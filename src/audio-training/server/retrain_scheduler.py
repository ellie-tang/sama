from __future__ import annotations

from datetime import datetime, time

from server.cba_whisper_runner import CBAWhisperRunner


class NightlyRetrainScheduler:
    def __init__(self, runner: CBAWhisperRunner):
        self.runner = runner

    def should_run_nightly_retrain(self, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        return now.time() >= time(1, 0)

    def schedule_retrain_job(self) -> dict[str, str]:
        return self.runner.launch_training_job()

    def record_retrain_result(self, result: dict[str, str]) -> str:
        self.runner.promote_latest_checkpoint(result["checkpoint_path"])
        return result["job_id"]
