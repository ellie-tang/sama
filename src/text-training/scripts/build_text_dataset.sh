#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}" \
python3 -m text_training.pipeline.build_dataset --config "${ROOT_DIR}/configs/example_config.json" "$@"
