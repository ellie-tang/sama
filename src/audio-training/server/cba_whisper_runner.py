from __future__ import annotations

import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from server.config import AudioTrainingSettings


class CBAWhisperRunner:
    def __init__(self, settings: AudioTrainingSettings):
        self.settings = settings

    def prepare_cba_whisper_inputs(self) -> Path:
        manifest_path = self.settings.manifest_dir / "dataset_manifest.csv"
        if not manifest_path.exists():
            manifest_path.write_text("sample_id,audio_path,text\n", encoding="utf-8")
        return manifest_path

    def launch_training_job(self) -> dict[str, str]:
        manifest_path = self.prepare_cba_whisper_inputs()
        job_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "_" + uuid4().hex[:8]
        run_dir = self.settings.runs_dir / job_id
        run_dir.mkdir(parents=True, exist_ok=True)

        if not self.settings.cba_command:
            checkpoint = run_dir / "mock-checkpoint"
            checkpoint.mkdir(exist_ok=True)
            return {
                "job_id": job_id,
                "manifest_path": str(manifest_path),
                "checkpoint_path": str(checkpoint),
                "message": "No CBA command configured; created placeholder checkpoint.",
            }

        command = shlex.split(self.settings.cba_command) + ["--manifest", str(manifest_path), "--output-dir", str(run_dir)]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "CBA-Whisper job failed")
        return {
            "job_id": job_id,
            "manifest_path": str(manifest_path),
            "checkpoint_path": str(run_dir),
            "message": completed.stdout.strip() or "CBA-Whisper training completed.",
        }

    def promote_latest_checkpoint(self, checkpoint_path: str) -> Path:
        latest = self.settings.runs_dir / "latest"
        latest.write_text(checkpoint_path, encoding="utf-8")
        return latest

    def rollback_on_failure(self) -> None:
        return None
