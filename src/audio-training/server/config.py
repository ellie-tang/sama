from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from shared.constants import (
    DEFAULT_CONVERSATION_GAP_MS,
    DEFAULT_MAX_REVIEW_ITEMS,
    DEFAULT_MAX_WINDOW_MS,
    DEFAULT_MIN_LABEL_CONFIDENCE,
    DEFAULT_MODEL_QWEN,
    DEFAULT_MODEL_WHISPER,
    DEFAULT_REVIEW_CONFIDENCE,
    ROOT_ENV_VAR,
    default_root,
)


@dataclass(slots=True)
class AudioTrainingSettings:
    root_dir: Path
    data_dir: Path
    raw_audio_dir: Path
    context_frame_dir: Path
    candidate_dir: Path
    dataset_audio_dir: Path
    dataset_label_dir: Path
    manifest_dir: Path
    review_pending_dir: Path
    review_resolved_dir: Path
    runs_dir: Path
    whisper_backend: str
    whisper_cli: str
    whisper_model: str
    qwen_backend: str
    qwen_model: str
    qwen_api_base: str
    qwen_api_key: str
    min_label_confidence: float
    review_confidence: float
    conversation_gap_ms: int
    max_window_ms: int
    max_review_items: int
    cba_command: str


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value).expanduser().resolve() if value else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def load_settings() -> AudioTrainingSettings:
    root_dir = _env_path(ROOT_ENV_VAR, default_root())
    data_dir = _env_path("AUDIO_TRAINING_DATA_DIR", root_dir / "data")
    runs_dir = _env_path("AUDIO_TRAINING_RUNS_DIR", root_dir / "runs")

    settings = AudioTrainingSettings(
        root_dir=root_dir,
        data_dir=data_dir,
        raw_audio_dir=data_dir / "raw_audio",
        context_frame_dir=data_dir / "context_frames",
        candidate_dir=data_dir / "candidates",
        dataset_audio_dir=data_dir / "dataset" / "audio",
        dataset_label_dir=data_dir / "dataset" / "labels",
        manifest_dir=data_dir / "manifests",
        review_pending_dir=data_dir / "review_queue" / "pending",
        review_resolved_dir=data_dir / "review_queue" / "resolved",
        runs_dir=runs_dir,
        whisper_backend=os.getenv("AUDIO_TRAINING_WHISPER_BACKEND", "hint"),
        whisper_cli=os.getenv("AUDIO_TRAINING_WHISPER_CLI", "whisper"),
        whisper_model=os.getenv("AUDIO_TRAINING_WHISPER_MODEL", DEFAULT_MODEL_WHISPER),
        qwen_backend=os.getenv("AUDIO_TRAINING_QWEN_BACKEND", "heuristic"),
        qwen_model=os.getenv("AUDIO_TRAINING_QWEN_MODEL", DEFAULT_MODEL_QWEN),
        qwen_api_base=os.getenv("AUDIO_TRAINING_QWEN_API_BASE", "http://127.0.0.1:8001/v1"),
        qwen_api_key=os.getenv("AUDIO_TRAINING_QWEN_API_KEY", ""),
        min_label_confidence=_env_float("AUDIO_TRAINING_MIN_LABEL_CONFIDENCE", DEFAULT_MIN_LABEL_CONFIDENCE),
        review_confidence=_env_float("AUDIO_TRAINING_REVIEW_CONFIDENCE", DEFAULT_REVIEW_CONFIDENCE),
        conversation_gap_ms=_env_int("AUDIO_TRAINING_CONVERSATION_GAP_MS", DEFAULT_CONVERSATION_GAP_MS),
        max_window_ms=_env_int("AUDIO_TRAINING_MAX_WINDOW_MS", DEFAULT_MAX_WINDOW_MS),
        max_review_items=_env_int("AUDIO_TRAINING_MAX_REVIEW_ITEMS", DEFAULT_MAX_REVIEW_ITEMS),
        cba_command=os.getenv("AUDIO_TRAINING_CBA_COMMAND", ""),
    )
    ensure_directories(settings)
    return settings


def ensure_directories(settings: AudioTrainingSettings) -> None:
    for path in (
        settings.data_dir,
        settings.raw_audio_dir,
        settings.context_frame_dir,
        settings.candidate_dir,
        settings.dataset_audio_dir,
        settings.dataset_label_dir,
        settings.manifest_dir,
        settings.review_pending_dir,
        settings.review_resolved_dir,
        settings.runs_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def get_whisper_model_config(settings: AudioTrainingSettings) -> dict[str, str]:
    return {
        "backend": settings.whisper_backend,
        "cli": settings.whisper_cli,
        "model": settings.whisper_model,
    }


def get_qwen_model_config(settings: AudioTrainingSettings) -> dict[str, str]:
    return {
        "backend": settings.qwen_backend,
        "model": settings.qwen_model,
        "api_base": settings.qwen_api_base,
    }


def get_dataset_paths(settings: AudioTrainingSettings) -> dict[str, str]:
    return {
        "audio_dir": str(settings.dataset_audio_dir),
        "label_dir": str(settings.dataset_label_dir),
        "manifest_dir": str(settings.manifest_dir),
    }
