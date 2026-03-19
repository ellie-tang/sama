#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.cba_whisper_runner import CBAWhisperRunner
from server.config import load_settings
from server.retrain_scheduler import NightlyRetrainScheduler


def main() -> int:
    settings = load_settings()
    runner = CBAWhisperRunner(settings)
    scheduler = NightlyRetrainScheduler(runner)
    result = scheduler.schedule_retrain_job()
    scheduler.record_retrain_result(result)
    print(result["message"])
    print(f"job_id={result['job_id']}")
    print(f"manifest={result['manifest_path']}")
    print(f"checkpoint={result['checkpoint_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
