from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from server.config import AudioTrainingSettings


@dataclass(slots=True)
class TranscriptResult:
    utterance_id: str
    text: str
    confidence: float
    backend: str
    source_audio_path: str


class WhisperAsrService:
    def __init__(self, settings: AudioTrainingSettings):
        self.settings = settings

    def load_whisper_model(self) -> dict[str, str]:
        return {
            "backend": self.settings.whisper_backend,
            "model": self.settings.whisper_model,
        }

    def transcribe_utterance(
        self,
        utterance_id: str,
        audio_path: Path,
        transcript_hint: str | None = None,
        asr_confidence_hint: float | None = None,
    ) -> TranscriptResult:
        if transcript_hint:
            return TranscriptResult(
                utterance_id=utterance_id,
                text=transcript_hint.strip(),
                confidence=asr_confidence_hint if asr_confidence_hint is not None else 0.97,
                backend="hint",
                source_audio_path=str(audio_path),
            )

        if self.settings.whisper_backend == "cli":
            return self._transcribe_via_cli(utterance_id, audio_path)

        fallback_text = audio_path.stem.replace("_", " ").strip() or "unintelligible speech"
        return TranscriptResult(
            utterance_id=utterance_id,
            text=fallback_text,
            confidence=0.2,
            backend="fallback",
            source_audio_path=str(audio_path),
        )

    def transcribe_conversation_window(self, utterances: Iterable[dict]) -> list[TranscriptResult]:
        results: list[TranscriptResult] = []
        for utterance in utterances:
            results.append(
                self.transcribe_utterance(
                    utterance_id=utterance["utterance_id"],
                    audio_path=Path(utterance["audio_path"]),
                    transcript_hint=utterance.get("transcript_hint"),
                    asr_confidence_hint=utterance.get("asr_confidence_hint"),
                )
            )
        return results

    def extract_asr_confidence_signals(self, transcripts: Iterable[TranscriptResult]) -> dict[str, float]:
        transcript_list = list(transcripts)
        if not transcript_list:
            return {"average_confidence": 0.0, "min_confidence": 0.0}
        confidences = [item.confidence for item in transcript_list]
        return {
            "average_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
        }

    def _transcribe_via_cli(self, utterance_id: str, audio_path: Path) -> TranscriptResult:
        cli_path = shutil.which(self.settings.whisper_cli) or self.settings.whisper_cli
        with tempfile.TemporaryDirectory() as tmpdir:
            command = [
                cli_path,
                str(audio_path),
                "--model",
                self.settings.whisper_model,
                "--language",
                "en",
                "--output_format",
                "json",
                "--output_dir",
                tmpdir,
                "--fp16",
                "False",
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            json_path = Path(tmpdir) / f"{audio_path.stem}.json"
            if completed.returncode != 0 or not json_path.exists():
                raise RuntimeError(
                    f"Whisper CLI failed for {audio_path.name}: {completed.stderr.strip() or completed.stdout.strip()}"
                )
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            text = str(payload.get("text", "")).strip()
            confidence = 0.75
            segments = payload.get("segments") or []
            if segments:
                probs = [float(seg.get("avg_logprob", -0.75)) for seg in segments]
                confidence = max(0.0, min(0.99, 1.0 + (sum(probs) / len(probs))))
            return TranscriptResult(
                utterance_id=utterance_id,
                text=text,
                confidence=confidence,
                backend="cli",
                source_audio_path=str(audio_path),
            )
