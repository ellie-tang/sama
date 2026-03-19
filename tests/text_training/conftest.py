from __future__ import annotations

import sys
from pathlib import Path


TEXT_TRAINING_ROOT = Path(__file__).resolve().parents[2] / "src" / "text-training"
if str(TEXT_TRAINING_ROOT) not in sys.path:
    sys.path.insert(0, str(TEXT_TRAINING_ROOT))
