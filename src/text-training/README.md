Text Training

This package implements a text-based second-pass regeneration pipeline for ASR correction using Qwen-style causal language models with LoRA adapters.

Scope
- ingest Whisper n-best hypotheses
- ingest optional vision-language environmental context
- build structured prompts for second-pass correction
- fine-tune a frozen base model with LoRA
- evaluate against Whisper top-1 using WER and CER
- run offline inference with trained adapters

Layout
- `text_training/`: Python package
- `configs/`: example configuration files
- `scripts/`: shell wrappers for common workflows
- `tests/`: lightweight unit tests
- `artifacts/`: checkpoints and metrics output

Quick start

```bash
cd /Users/ellietang/sama
PYTHONPATH=src/text-training python3 -m unittest discover -s src/text-training/tests
```

Example workflow

```bash
cd /Users/ellietang/sama
PYTHONPATH=src/text-training python3 -m text_training.pipeline.build_dataset \
  --config src/text-training/configs/example_config.json

PYTHONPATH=src/text-training python3 -m text_training.pipeline.run_training \
  --config src/text-training/configs/example_config.json

PYTHONPATH=src/text-training python3 -m text_training.pipeline.run_eval \
  --config src/text-training/configs/example_config.json
```

Dependencies
- `torch`
- `transformers`
- `peft`
- `accelerate`
- `pyyaml` for YAML configs

The package is written so that most modules can be imported without those heavy dependencies. They are loaded only when training or generation functions are called.

Before training, replace `model.base_model_name` in `configs/example_config.json` with the exact model identifier you want to use for your Qwen3.5 9B checkpoint.
