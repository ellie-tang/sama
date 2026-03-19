from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ASRHypothesis:
    text: str
    score: float | None = None
    rank: int | None = None
    source: str = "whisper"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ASRHypothesis":
        return cls(
            text=str(payload.get("text", "")),
            score=payload.get("score"),
            rank=payload.get("rank"),
            source=str(payload.get("source", "whisper")),
        )


@dataclass
class VisionContext:
    text: str = ""
    entities: list[str] = field(default_factory=list)
    speaker_hint: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "VisionContext | None":
        if payload is None:
            return None
        return cls(
            text=str(payload.get("text", payload.get("visual_context_text", ""))),
            entities=list(payload.get("entities", payload.get("scene_entities", [])) or []),
            speaker_hint=payload.get("speaker_hint"),
            raw=dict(payload.get("raw", {})),
        )


@dataclass
class TrainingExample:
    utterance_id: str
    nbest_hypotheses: list[ASRHypothesis]
    visual_context: VisionContext | None = None
    reference_transcript: str | None = None
    audio_path: str | None = None
    segment_timestamps: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def top_hypothesis(self) -> str:
        if not self.nbest_hypotheses:
            return ""
        return self.nbest_hypotheses[0].text

    def to_dict(self) -> dict[str, Any]:
        return {
            "utterance_id": self.utterance_id,
            "audio_path": self.audio_path,
            "nbest_hypotheses": [item.to_dict() for item in self.nbest_hypotheses],
            "visual_context": self.visual_context.to_dict() if self.visual_context else None,
            "reference_transcript": self.reference_transcript,
            "segment_timestamps": self.segment_timestamps,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TrainingExample":
        hypotheses = [
            item if isinstance(item, ASRHypothesis) else ASRHypothesis.from_dict(item)
            for item in payload.get("nbest_hypotheses", [])
        ]
        if not hypotheses and payload.get("text"):
            hypotheses = [ASRHypothesis(text=str(payload["text"]), rank=1)]
        return cls(
            utterance_id=str(payload.get("utterance_id", payload.get("id", ""))),
            nbest_hypotheses=hypotheses,
            visual_context=VisionContext.from_dict(payload.get("visual_context")),
            reference_transcript=payload.get("reference_transcript"),
            audio_path=payload.get("audio_path"),
            segment_timestamps=list(payload.get("segment_timestamps", []) or []),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass
class InferenceExample:
    utterance_id: str
    nbest_hypotheses: list[ASRHypothesis]
    visual_context: VisionContext | None = None
    audio_path: str | None = None
    segment_timestamps: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "utterance_id": self.utterance_id,
            "audio_path": self.audio_path,
            "nbest_hypotheses": [item.to_dict() for item in self.nbest_hypotheses],
            "visual_context": self.visual_context.to_dict() if self.visual_context else None,
            "segment_timestamps": self.segment_timestamps,
            "metadata": self.metadata,
        }

    @classmethod
    def from_training_example(cls, example: TrainingExample) -> "InferenceExample":
        return cls(
            utterance_id=example.utterance_id,
            nbest_hypotheses=example.nbest_hypotheses,
            visual_context=example.visual_context,
            audio_path=example.audio_path,
            segment_timestamps=example.segment_timestamps,
            metadata=example.metadata,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InferenceExample":
        training_example = TrainingExample.from_dict(payload)
        return cls.from_training_example(training_example)


@dataclass
class BatchFeatures:
    input_ids: list[int]
    attention_mask: list[int]
    labels: list[int]
