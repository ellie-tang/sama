#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.config import load_settings
from server.dataset_service import DatasetService
from server.storage import AudioTrainingStorage


def main() -> int:
    settings = load_settings()
    storage = AudioTrainingStorage(settings)
    dataset = DatasetService(settings, storage)
    manifest_path = settings.manifest_dir / "dataset_manifest.csv"
    manifest_path.write_text("sample_id,audio_path,text\n", encoding="utf-8")

    for metadata_path in sorted(settings.dataset_label_dir.glob("*.json")):
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        row = dataset.build_cba_whisper_manifest_row(
            payload["sample_id"],
            Path(payload["dataset_audio_path"]),
            payload["canonical_label"],
        )
        dataset.append_training_index(row)

    print(f"rebuilt_manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
