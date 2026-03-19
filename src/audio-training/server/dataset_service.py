from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from server.config import AudioTrainingSettings
from server.storage import AudioTrainingStorage


class DatasetService:
    def __init__(self, settings: AudioTrainingSettings, storage: AudioTrainingStorage):
        self.settings = settings
        self.storage = storage

    def persist_dataset_sample(self, candidate: dict[str, Any]) -> dict[str, str]:
        sample_id = candidate.get("sample_id") or uuid4().hex
        audio_source = Path(candidate["target_audio_path"])
        copied_audio = self.storage.copy_into_dataset(audio_source, sample_id)
        label_path = self.settings.dataset_label_dir / f"{sample_id}.txt"
        label_path.write_text(candidate["canonical_label"].strip() + "\n", encoding="utf-8")

        metadata_path = self.settings.dataset_label_dir / f"{sample_id}.json"
        self.storage.write_json_record(
            metadata_path,
            {
                "sample_id": sample_id,
                "conversation_id": candidate["conversation_id"],
                "target_utterance_id": candidate["target_utterance_id"],
                "canonical_label": candidate["canonical_label"],
                "captured_at": candidate["captured_at"],
                "created_at": datetime.utcnow().isoformat(),
                "context_transcripts": candidate["context_transcripts"],
                "frame_descriptions": candidate.get("frame_descriptions", []),
                "source_audio_path": str(audio_source),
                "dataset_audio_path": str(copied_audio),
            },
        )
        manifest_row = self.build_cba_whisper_manifest_row(sample_id, copied_audio, candidate["canonical_label"])
        self.append_training_index(manifest_row)
        return {
            "sample_id": sample_id,
            "audio_path": str(copied_audio),
            "label_path": str(label_path),
            "metadata_path": str(metadata_path),
        }

    def build_cba_whisper_manifest_row(self, sample_id: str, audio_path: Path, text: str) -> str:
        escaped = text.replace('"', '""')
        return f'{sample_id},"{audio_path}","{escaped}"'

    def append_training_index(self, row: str) -> Path:
        manifest_path = self.settings.manifest_dir / "dataset_manifest.csv"
        if not manifest_path.exists():
            manifest_path.write_text("sample_id,audio_path,text\n", encoding="utf-8")
        with manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(row + "\n")
        return manifest_path

    def mark_sample_status(self, sample_id: str, status: str, extra: dict[str, Any] | None = None) -> Path:
        status_path = self.settings.candidate_dir / f"{sample_id}.status.json"
        payload = {
            "sample_id": sample_id,
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if extra:
            payload.update(extra)
        return self.storage.write_json_record(status_path, payload)
