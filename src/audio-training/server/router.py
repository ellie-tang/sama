from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, FastAPI, File, Form, HTTPException, UploadFile

from shared.constants import STATUS_FAILED
from server.cba_whisper_runner import CBAWhisperRunner
from server.config import load_settings
from server.dataset_service import DatasetService
from server.ingest_service import AudioTrainingIngestService
from server.qwen_labeler import QwenLabeler
from server.review_queue import ReviewQueueService
from server.retrain_scheduler import NightlyRetrainScheduler
from server.schemas import (
    HealthView,
    IngestAudioPayload,
    IngestAudioResponse,
    LabelDecisionResponse,
    RetrainJobStatus,
    ReviewDecisionRequest,
    ReviewQueueItem,
    TranscriptView,
)
from server.storage import AudioTrainingStorage
from server.whisper_asr import WhisperAsrService

settings = load_settings()
storage = AudioTrainingStorage(settings)
whisper_asr = WhisperAsrService(settings)
qwen_labeler = QwenLabeler(settings)
dataset_service = DatasetService(settings, storage)
review_queue = ReviewQueueService(settings, storage)
ingest_service = AudioTrainingIngestService(
    settings=settings,
    storage=storage,
    whisper_asr=whisper_asr,
    qwen_labeler=qwen_labeler,
    dataset_service=dataset_service,
    review_queue=review_queue,
)
retrain_runner = CBAWhisperRunner(settings)
retrain_scheduler = NightlyRetrainScheduler(retrain_runner)

router = APIRouter(prefix="/audio-training", tags=["audio-training"])


async def _save_uploads(
    conversation_id: str,
    uploads: list[UploadFile],
    saver,
) -> dict[str, Path]:
    saved: dict[str, Path] = {}
    for upload in uploads:
        content = await upload.read()
        if not upload.filename:
            raise HTTPException(status_code=400, detail="Uploaded file is missing a filename.")
        saved[upload.filename] = saver(conversation_id, upload.filename, content)
    return saved


@router.post("/ingest", response_model=IngestAudioResponse)
async def post_ingest_audio(
    payload_json: str = Form(...),
    audio_files: list[UploadFile] = File(...),
    context_frames: list[UploadFile] = File(default=[]),
):
    try:
        payload = IngestAudioPayload(**json.loads(payload_json))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload_json: {exc}") from exc

    try:
        audio_file_map = await _save_uploads(payload.conversation_id, audio_files, storage.save_raw_audio)
        context_frame_map = await _save_uploads(payload.conversation_id, context_frames, storage.save_context_frame)
        result = ingest_service.process_ingest_request(payload, audio_file_map, context_frame_map)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return IngestAudioResponse(
        success=result["status"] != STATUS_FAILED,
        status=result["status"],
        conversation_id=payload.conversation_id,
        target_utterance_id=result["target_utterance_id"],
        transcripts=[
            TranscriptView(
                utterance_id=item.utterance_id,
                text=item.text,
                confidence=item.confidence,
                backend=item.backend,
            )
            for item in result["transcripts"]
        ],
        decision=LabelDecisionResponse(
            labelable=result["decision"].labelable,
            canonical_label=result["decision"].canonical_label,
            confidence=result["decision"].confidence,
            reason=result["decision"].reason,
            needs_human_review=result["decision"].needs_human_review,
            discard=result["decision"].discard,
            evidence=result["decision"].evidence,
        ),
        dataset_sample_id=result["dataset_sample_id"],
        review_task_id=result["review_task_id"],
        message=result["message"],
        timestamp=datetime.utcnow(),
    )


@router.get("/reviews", response_model=list[ReviewQueueItem])
async def get_pending_reviews():
    return review_queue.list_pending_reviews()


@router.post("/reviews/{review_task_id}")
async def post_review_decision(review_task_id: str, request: ReviewDecisionRequest):
    try:
        resolved_path = review_queue.resolve_review_task(review_task_id, request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "success": True,
        "review_task_id": review_task_id,
        "resolved_path": str(resolved_path),
        "timestamp": datetime.utcnow(),
    }


@router.post("/retrain", response_model=RetrainJobStatus)
async def post_trigger_retrain():
    started_at = datetime.utcnow()
    try:
        result = retrain_scheduler.schedule_retrain_job()
        retrain_scheduler.record_retrain_result(result)
        finished_at = datetime.utcnow()
        return RetrainJobStatus(
            success=True,
            started_at=started_at,
            finished_at=finished_at,
            job_id=result["job_id"],
            manifest_path=result.get("manifest_path"),
            checkpoint_path=result.get("checkpoint_path"),
            message=result["message"],
        )
    except Exception as exc:
        finished_at = datetime.utcnow()
        return RetrainJobStatus(
            success=False,
            started_at=started_at,
            finished_at=finished_at,
            job_id="failed",
            manifest_path=None,
            checkpoint_path=None,
            message=str(exc),
        )


@router.get("/health", response_model=HealthView)
async def get_audio_training_health():
    dataset_samples = len(list(settings.dataset_label_dir.glob("*.json")))
    return HealthView(
        status="healthy",
        whisper_backend=settings.whisper_backend,
        whisper_model=settings.whisper_model,
        qwen_backend=settings.qwen_backend,
        qwen_model=settings.qwen_model,
        pending_review_items=len(review_queue.list_pending_reviews()),
        dataset_samples=dataset_samples,
        timestamp=datetime.utcnow(),
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="SAMA Audio Training Server",
        description="Whisper + Qwen3.5 9B self-training pipeline for Vuzix Blade 2 audio collection.",
        version="1.0.0",
    )
    app.include_router(router)
    return app


app = create_app()
