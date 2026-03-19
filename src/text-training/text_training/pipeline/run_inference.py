from __future__ import annotations

import argparse

from ..config import load_config
from ..data.loaders import load_jsonl_dataset
from ..eval.inference import batch_generate, load_adapter_for_inference, save_predictions
from ..schema import InferenceExample
from ..tokenization import load_tokenizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Run second-pass text regeneration inference")
    parser.add_argument("--config", required=True, help="Path to JSON or YAML config")
    parser.add_argument("--input", required=True, help="Input JSONL file of inference examples")
    parser.add_argument("--output", required=True, help="Output JSONL predictions path")
    parser.add_argument("--adapter-path", default="", help="Path to trained LoRA adapter directory")
    args = parser.parse_args()

    config = load_config(args.config)
    adapter_path = args.adapter_path or config.train.output_dir
    tokenizer = load_tokenizer(config.model.base_model_name, config.model.tokenizer_name or None)
    model = load_adapter_for_inference(
        base_model_name=config.model.base_model_name,
        adapter_path=adapter_path,
        dtype=config.model.dtype,
        device_map=config.model.device_map,
        load_in_4bit=config.model.load_in_4bit,
    )

    raw_examples = load_jsonl_dataset(args.input)
    examples = [InferenceExample.from_training_example(example) for example in raw_examples]
    predictions = batch_generate(examples, model, tokenizer, config.prompt, config.generation)

    rows = []
    for example, prediction in zip(examples, predictions):
        rows.append({"utterance_id": example.utterance_id, "prediction": prediction})
    save_predictions(rows, args.output)


if __name__ == "__main__":
    main()
