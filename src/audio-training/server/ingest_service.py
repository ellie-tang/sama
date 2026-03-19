from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from shared.constants import STATUS_DISCARDED, STATUS_REVIEW, STATUS_SAVED
from server.confidence_policy import is_dataset_ready, requires_human_review, should_discard_candidate
from server.config import AudioTrainingSettings
from server.context_builder import ConversationContextBuilder
from server.dataset_service import DatasetService
from server.qwen_labeler import QwenLabeler
from server.review_queue import ReviewQueueService
from server.schemas import IngestAudioPayload
from server.storage import AudioTrainingStorage
from server.whisper_asr import WhisperAsrService


class AudioTrainingIngestService:
    def __init__(
        self,
        settings: AudioTrainingSettings,
        storage: AudioTrainingStorage,
        whisper_asr: WhisperAsrService,
        qwen_labeler: QwenLabeler,
        dataset_service: DatasetService,
        review_queue: ReviewQueueService,
    ):
        self.settings = settings
        self.storage = storage
        self.whisper_asr = whisper_asr
        self.qwen_labeler = qwen_labeler
        self.dataset_service = dataset_service
        self.review_queue = review_queue
        self.context_builder = ConversationContextBuilder(settings.max_window_ms)

    def process_ingest_request(
        self,
        payload: IngestAudioPayload,
        audio_file_map: dict[str, Path],
        context_frame_map: dict[str, Path],
    ) -> dict:
        normalized_utterances = self.normalize_uploaded_audio(payload, audio_file_map)
        target_utterance_id = payload.preferred_target_utterance_id or payload.utterances[0].utterance_id
        transcripts = self.whisper_asr.transcribe_conversation_window(normalized_utterances)

        context = self.context_builder.merge_utterances_into_context(
            utterances=normalized_utterances,
            transcripts=transcripts,
            target_utterance_id=target_utterance_id,
        )
        context = self.context_builder.attach_frame_metadata(context, payload.context_frames)
        decision = self.qwen_labeler.decide_if_labelable(context)
        candidate = self.assemble_training_candidate(payload, context, decision)
        return self.route_decision_result(payload, transcripts, decision, candidate)

    def normalize_uploaded_audio(
        self,
        payload: IngestAudioPayload,
        audio_file_map: dict[str, Path],
    ) -> list[dict]:
        normalized: list[dict] = []
        for utterance in payload.utterances:
            audio_path = audio_file_map.get(utterance.source_file_name)
            if not audio_path:
                raise FileNotFoundError(f"Missing uploaded audio for {utterance.source_file_name}")
            normalized.append(
                {
                    "utterance_id": utterance.utterance_id,
                    "audio_path": str(audio_path),
                    "start_ms": utterance.start_ms,
                    "end_ms": utterance.end_ms,
                    "speaker_tag": utterance.speaker_tag,
                    "transcript_hint": utterance.transcript_hint,
                    "asr_confidence_hint": utterance.asr_confidence_hint,
                }
            )
        return normalized

    def assemble_training_candidate(self, payload: IngestAudioPayload, context, decision) -> dict:
        sample_id = uuid4().hex
        return {
            "sample_id": sample_id,
            "conversation_id": payload.conversation_id,
            "captured_at": payload.captured_at.isoformat(),
            "device_id": payload.device_id,
            "target_utterance_id": context.target_utterance_id,
            "target_audio_path": context.target_audio_path,
            "canonical_label": decision.canonical_label,
            "decision_confidence": decision.confidence,
            "decision_reason": decision.reason,
            "context_transcripts": context.conversation_lines,
            "frame_descriptions": context.frame_descriptions,
            "metadata": payload.metadata,
        }

    def route_decision_result(self, payload, transcripts, decision, candidate: dict) -> dict:
        if should_discard_candidate(decision):
            self.dataset_service.mark_sample_status(candidate["sample_id"], STATUS_DISCARDED, {"reason": decision.reason})
            return {
                "status": STATUS_DISCARDED,
                "dataset_sample_id": None,
                "review_task_id": None,
                "message": "Sample discarded because the label is not reliable enough.",
                "decision": decision,
                "transcripts": transcripts,
                "target_utterance_id": candidate["target_utterance_id"],
            }

        if is_dataset_ready(decision, self.settings):
            saved = self.dataset_service.persist_dataset_sample(candidate)
            self.dataset_service.mark_sample_status(candidate["sample_id"], STATUS_SAVED, saved)
            return {
                "status": STATUS_SAVED,
                "dataset_sample_id": saved["sample_id"],
                "review_task_id": None,
                "message": "Sample accepted and persisted into the training dataset.",
                "decision": decision,
                "transcripts": transcripts,
                "target_utterance_id": candidate["target_utterance_id"],
            }

        if requires_human_review(decision, self.settings):
            review_item = self.review_queue.enqueue_review_task(candidate)
            self.dataset_service.mark_sample_status(candidate["sample_id"], STATUS_REVIEW, {"review_task_id": review_item.review_task_id})
            return {
                "status": STATUS_REVIEW,
                "dataset_sample_id": None,
                "review_task_id": review_item.review_task_id,
                "message": "Sample requires human review before entering the dataset.",
                "decision": decision,
                "transcripts": transcripts,
                "target_utterance_id": candidate["target_utterance_id"],
            }

        self.dataset_service.mark_sample_status(candidate["sample_id"], STATUS_DISCARDED, {"reason": decision.reason})
        return {
            "status": STATUS_DISCARDED,
            "dataset_sample_id": None,
            "review_task_id": None,
            "message": "Sample did not meet dataset or review thresholds.",
            "decision": decision,
            "transcripts": transcripts,
            "target_utterance_id": candidate["target_utterance_id"],
        }
