from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(slots=True)
class AudioChunkContract:
    utterance_id: str
    source_file_name: str
    start_ms: int
    end_ms: int
    transcript_hint: Optional[str] = None
    speaker_tag: str = "wearer"
    asr_confidence_hint: Optional[float] = None


@dataclass(slots=True)
class ContextFrameContract:
    frame_id: str
    source_file_name: str
    timestamp_ms: int
    description: Optional[str] = None


@dataclass(slots=True)
class TranscriptContract:
    utterance_id: str
    text: str
    confidence: float
    backend: str
    source_audio_path: Optional[str] = None


@dataclass(slots=True)
class LabelDecisionContract:
    labelable: bool
    canonical_label: Optional[str]
    confidence: float
    reason: str
    needs_human_review: bool
    discard: bool
    evidence: list[str] = field(default_factory=list)
    raw_model_response: Optional[dict[str, Any]] = None
