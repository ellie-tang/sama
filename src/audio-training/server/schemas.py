from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UtteranceInput(BaseModel):
    utterance_id: str
    source_file_name: str
    start_ms: int
    end_ms: int
    transcript_hint: Optional[str] = None
    speaker_tag: str = "wearer"
    asr_confidence_hint: Optional[float] = None


class ContextFrameInput(BaseModel):
    frame_id: str
    source_file_name: str
    timestamp_ms: int
    description: Optional[str] = None


class IngestAudioPayload(BaseModel):
    conversation_id: str
    device_id: str
    captured_at: datetime
    utterances: list[UtteranceInput]
    context_frames: list[ContextFrameInput] = Field(default_factory=list)
    preferred_target_utterance_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class TranscriptView(BaseModel):
    utterance_id: str
    text: str
    confidence: float
    backend: str


class LabelDecisionResponse(BaseModel):
    labelable: bool
    canonical_label: Optional[str] = None
    confidence: float
    reason: str
    needs_human_review: bool = False
    discard: bool = False
    evidence: list[str] = Field(default_factory=list)


class IngestAudioResponse(BaseModel):
    success: bool
    status: str
    conversation_id: str
    target_utterance_id: Optional[str] = None
    transcripts: list[TranscriptView] = Field(default_factory=list)
    decision: LabelDecisionResponse
    dataset_sample_id: Optional[str] = None
    review_task_id: Optional[str] = None
    message: str
    timestamp: datetime


class ReviewQueueItem(BaseModel):
    review_task_id: str
    conversation_id: str
    target_utterance_id: str
    target_audio_path: str
    proposed_label: Optional[str] = None
    decision_confidence: float
    reason: str
    created_at: datetime
    metadata: dict = Field(default_factory=dict)


class ReviewDecisionRequest(BaseModel):
    decision: str
    corrected_label: Optional[str] = None
    reviewer: str = "human"
    notes: Optional[str] = None


class RetrainJobStatus(BaseModel):
    success: bool
    started_at: datetime
    finished_at: datetime
    job_id: str
    manifest_path: Optional[str] = None
    checkpoint_path: Optional[str] = None
    message: str


class HealthView(BaseModel):
    status: str
    whisper_backend: str
    whisper_model: str
    qwen_backend: str
    qwen_model: str
    pending_review_items: int
    dataset_samples: int
    timestamp: datetime
