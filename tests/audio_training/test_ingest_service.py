from __future__ import annotations

from server.dataset_service import DatasetService
from server.ingest_service import AudioTrainingIngestService
from server.qwen_labeler import QwenLabeler
from server.review_queue import ReviewQueueService
from server.schemas import IngestAudioPayload
from server.storage import AudioTrainingStorage
from server.whisper_asr import WhisperAsrService


def _build_ingest_service(audio_training_settings):
    storage = AudioTrainingStorage(audio_training_settings)
    return (
        storage,
        AudioTrainingIngestService(
            settings=audio_training_settings,
            storage=storage,
            whisper_asr=WhisperAsrService(audio_training_settings),
            qwen_labeler=QwenLabeler(audio_training_settings),
            dataset_service=DatasetService(audio_training_settings, storage),
            review_queue=ReviewQueueService(audio_training_settings, storage),
        ),
    )


def test_ingest_service_saves_labelable_sample(audio_training_settings):
    storage, service = _build_ingest_service(audio_training_settings)
    conversation_id = "conv-direct"
    a1 = storage.save_raw_audio(conversation_id, "u1.wav", b"RIFFu1")
    a2 = storage.save_raw_audio(conversation_id, "u2.wav", b"RIFFu2")
    a3 = storage.save_raw_audio(conversation_id, "u3.wav", b"RIFFu3")
    payload = IngestAudioPayload(
        conversation_id=conversation_id,
        device_id="blade2",
        captured_at="2026-03-18T10:30:00Z",
        utterances=[
            {"utterance_id": "u1", "source_file_name": "u1.wav", "start_ms": 0, "end_ms": 600, "transcript_hint": "tons of tv", "speaker_tag": "wearer"},
            {"utterance_id": "u2", "source_file_name": "u2.wav", "start_ms": 700, "end_ms": 1600, "transcript_hint": "do you mean turn off tv?", "speaker_tag": "partner"},
            {"utterance_id": "u3", "source_file_name": "u3.wav", "start_ms": 1700, "end_ms": 2100, "transcript_hint": "yes", "speaker_tag": "wearer"},
        ],
        context_frames=[],
        preferred_target_utterance_id="u1",
        metadata={"device": "blade2"},
    )

    result = service.process_ingest_request(payload, {"u1.wav": a1, "u2.wav": a2, "u3.wav": a3}, {})

    assert result["status"] == "saved"
    assert result["decision"].canonical_label == "turn off tv"
    assert result["dataset_sample_id"] is not None


def test_ingest_service_routes_ambiguous_sample_to_discard(audio_training_settings):
    storage, service = _build_ingest_service(audio_training_settings)
    conversation_id = "conv-ambiguous"
    a1 = storage.save_raw_audio(conversation_id, "u1.wav", b"RIFFu1")
    payload = IngestAudioPayload(
        conversation_id=conversation_id,
        device_id="blade2",
        captured_at="2026-03-18T10:30:00Z",
        utterances=[
            {"utterance_id": "u1", "source_file_name": "u1.wav", "start_ms": 0, "end_ms": 600, "transcript_hint": "mumble", "speaker_tag": "wearer"},
        ],
        context_frames=[],
        preferred_target_utterance_id="u1",
        metadata={},
    )

    result = service.process_ingest_request(payload, {"u1.wav": a1}, {})

    assert result["status"] == "discarded"
    assert result["decision"].canonical_label == "mumble"
    assert result["decision"].confidence < audio_training_settings.review_confidence
