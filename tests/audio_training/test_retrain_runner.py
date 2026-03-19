from __future__ import annotations

from pathlib import Path

from server.cba_whisper_runner import CBAWhisperRunner
from server.retrain_scheduler import NightlyRetrainScheduler


def test_cba_runner_creates_placeholder_checkpoint_when_command_missing(audio_training_settings):
    runner = CBAWhisperRunner(audio_training_settings)

    result = runner.launch_training_job()

    assert result["job_id"]
    assert Path(result["checkpoint_path"]).exists()
    assert "placeholder checkpoint" in result["message"].lower()


def test_scheduler_records_latest_checkpoint_pointer(audio_training_settings):
    runner = CBAWhisperRunner(audio_training_settings)
    scheduler = NightlyRetrainScheduler(runner)

    result = scheduler.schedule_retrain_job()
    job_id = scheduler.record_retrain_result(result)

    latest = (audio_training_settings.runs_dir / "latest").read_text(encoding="utf-8")
    assert job_id == result["job_id"]
    assert latest == result["checkpoint_path"]
