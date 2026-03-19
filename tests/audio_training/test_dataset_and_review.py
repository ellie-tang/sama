from __future__ import annotations

import json
from pathlib import Path

from server.dataset_service import DatasetService
from server.review_queue import ReviewQueueService
from server.schemas import ReviewDecisionRequest
from server.storage import AudioTrainingStorage


def test_dataset_service_persists_sample(audio_training_settings, tmp_path: Path):
    source_audio = tmp_path / "example.wav"
    source_audio.write_bytes(b"RIFFxxxx")
    storage = AudioTrainingStorage(audio_training_settings)
    dataset = DatasetService(audio_training_settings, storage)

    result = dataset.persist_dataset_sample(
        {
            "sample_id": "sample123",
            "conversation_id": "conv1",
            "target_utterance_id": "u1",
            "target_audio_path": str(source_audio),
            "canonical_label": "turn off tv",
            "captured_at": "2026-03-18T12:00:00Z",
            "context_transcripts": ["wearer: tons of tv", "partner: do you mean turn off tv?", "wearer: yes"],
            "frame_descriptions": [],
        }
    )

    assert Path(result["audio_path"]).exists()
    assert Path(result["label_path"]).read_text(encoding="utf-8").strip() == "turn off tv"
    manifest = (audio_training_settings.manifest_dir / "dataset_manifest.csv").read_text(encoding="utf-8")
    assert "sample123" in manifest


def test_review_queue_enqueues_and_resolves(audio_training_settings):
    storage = AudioTrainingStorage(audio_training_settings)
    queue = ReviewQueueService(audio_training_settings, storage)

    review_item = queue.enqueue_review_task(
        {
            "conversation_id": "conv2",
            "target_utterance_id": "u1",
            "target_audio_path": "/tmp/u1.wav",
            "canonical_label": "turn off tv",
            "decision_confidence": 0.7,
            "decision_reason": "Needs review.",
            "context_transcripts": ["wearer: tons of tv", "partner: do you mean turn off tv?", "wearer: yes"],
            "frame_descriptions": ["living room tv"],
        }
    )

    pending = queue.list_pending_reviews()
    assert len(pending) == 1
    assert pending[0].review_task_id == review_item.review_task_id

    resolved_path = queue.resolve_review_task(
        review_item.review_task_id,
        ReviewDecisionRequest(decision="correct", corrected_label="turn off tv", reviewer="tester"),
    )
    resolved_payload = json.loads(resolved_path.read_text(encoding="utf-8"))

    assert resolved_payload["resolution"]["decision"] == "correct"
    assert not (audio_training_settings.review_pending_dir / f"{review_item.review_task_id}.json").exists()
