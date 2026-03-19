from __future__ import annotations

import sys
from pathlib import Path

import pytest


AUDIO_TRAINING_ROOT = Path(__file__).resolve().parents[2] / "src" / "audio-training"
if str(AUDIO_TRAINING_ROOT) not in sys.path:
    sys.path.insert(0, str(AUDIO_TRAINING_ROOT))

from server.config import AudioTrainingSettings


@pytest.fixture
def audio_training_settings(tmp_path: Path) -> AudioTrainingSettings:
    settings = AudioTrainingSettings(
        root_dir=tmp_path,
        data_dir=tmp_path / "data",
        raw_audio_dir=tmp_path / "data" / "raw_audio",
        context_frame_dir=tmp_path / "data" / "context_frames",
        candidate_dir=tmp_path / "data" / "candidates",
        dataset_audio_dir=tmp_path / "data" / "dataset" / "audio",
        dataset_label_dir=tmp_path / "data" / "dataset" / "labels",
        manifest_dir=tmp_path / "data" / "manifests",
        review_pending_dir=tmp_path / "data" / "review_queue" / "pending",
        review_resolved_dir=tmp_path / "data" / "review_queue" / "resolved",
        runs_dir=tmp_path / "runs",
        whisper_backend="hint",
        whisper_cli="whisper",
        whisper_model="whisper-large-v3",
        qwen_backend="heuristic",
        qwen_model="qwen3.5-9b",
        qwen_api_base="http://127.0.0.1:8001/v1",
        qwen_api_key="",
        min_label_confidence=0.82,
        review_confidence=0.55,
        conversation_gap_ms=4000,
        max_window_ms=30000,
        max_review_items=500,
        cba_command="",
    )
    for path in (
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
    return settings
