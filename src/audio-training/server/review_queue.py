from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from server.config import AudioTrainingSettings
from server.schemas import ReviewDecisionRequest, ReviewQueueItem
from server.storage import AudioTrainingStorage


class ReviewQueueService:
    def __init__(self, settings: AudioTrainingSettings, storage: AudioTrainingStorage):
        self.settings = settings
        self.storage = storage

    def enqueue_review_task(self, candidate: dict) -> ReviewQueueItem:
        review_task_id = uuid4().hex
        item = ReviewQueueItem(
            review_task_id=review_task_id,
            conversation_id=candidate["conversation_id"],
            target_utterance_id=candidate["target_utterance_id"],
            target_audio_path=candidate["target_audio_path"],
            proposed_label=candidate.get("canonical_label"),
            decision_confidence=float(candidate["decision_confidence"]),
            reason=candidate["decision_reason"],
            created_at=datetime.utcnow(),
            metadata={
                "context_transcripts": candidate.get("context_transcripts", []),
                "frame_descriptions": candidate.get("frame_descriptions", []),
            },
        )
        self.storage.write_json_record(
            self.settings.review_pending_dir / f"{review_task_id}.json",
            item.model_dump(mode="json"),
        )
        return item

    def list_pending_reviews(self) -> list[ReviewQueueItem]:
        items: list[ReviewQueueItem] = []
        for path in sorted(self.settings.review_pending_dir.glob("*.json"))[: self.settings.max_review_items]:
            items.append(ReviewQueueItem(**self.storage.load_json_record(path)))
        return items

    def resolve_review_task(self, review_task_id: str, request: ReviewDecisionRequest) -> Path:
        source = self.settings.review_pending_dir / f"{review_task_id}.json"
        if not source.exists():
            raise FileNotFoundError(f"Unknown review task: {review_task_id}")
        payload = self.storage.load_json_record(source)
        payload["resolution"] = request.model_dump(mode="json")
        payload["resolved_at"] = datetime.utcnow().isoformat()
        destination = self.settings.review_resolved_dir / f"{review_task_id}.json"
        self.storage.write_json_record(destination, payload)
        source.unlink()
        return destination
