from __future__ import annotations

import sys
from pathlib import Path


WEBSERVER_ROOT = Path(__file__).resolve().parents[2] / "src" / "aiserver" / "webserver"
if str(WEBSERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(WEBSERVER_ROOT))
