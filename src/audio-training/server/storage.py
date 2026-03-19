from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from server.config import AudioTrainingSettings


class AudioTrainingStorage:
    def __init__(self, settings: AudioTrainingSettings):
        self.settings = settings

    def save_raw_audio(self, conversation_id: str, file_name: str, content: bytes) -> Path:
        destination = self.settings.raw_audio_dir / conversation_id / file_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return destination

    def save_context_frame(self, conversation_id: str, file_name: str, content: bytes) -> Path:
        destination = self.settings.context_frame_dir / conversation_id / file_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return destination

    def write_json_record(self, destination: Path, payload: dict[str, Any]) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return destination

    def load_json_record(self, source: Path) -> dict[str, Any]:
        return json.loads(source.read_text(encoding="utf-8"))

    def copy_into_dataset(self, source: Path, sample_id: str) -> Path:
        extension = source.suffix or ".wav"
        destination = self.settings.dataset_audio_dir / f"{sample_id}{extension}"
        shutil.copy2(source, destination)
        return destination

    def count_json_records(self, directory: Path) -> int:
        if not directory.exists():
            return 0
        return len(list(directory.glob("*.json")))
