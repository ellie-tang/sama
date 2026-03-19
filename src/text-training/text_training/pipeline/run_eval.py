from __future__ import annotations

import argparse

from ..config import load_config
from ..data.loaders import load_jsonl_dataset
from ..eval.inference import batch_generate, load_adapter_for_inference, save_predictions
from ..eval.metrics import compare_against_top1_baseline
from ..schema import InferenceExample
from ..tokenization import load_tokenizer
from ..utils import save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate second-pass regeneration with a LoRA adapter")
    parser.add_argument("--config", required=True, help="Path to JSON or YAML config")
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

    eval_path = config.eval.prediction_input_path or config.data.test_path
    examples = load_jsonl_dataset(eval_path)
    inference_examples = [InferenceExample.from_training_example(example) for example in examples]
    predictions = batch_generate(inference_examples, model, tokenizer, config.prompt, config.generation)

    references = [example.reference_transcript or "" for example in examples]
    top1 = [example.top_hypothesis for example in examples]
    metrics = compare_against_top1_baseline(top1, predictions, references)

    prediction_rows = []
    for example, prediction in zip(examples, predictions):
        prediction_rows.append(
            {
                "utterance_id": example.utterance_id,
                "top1_hypothesis": example.top_hypothesis,
                "prediction": prediction,
                "reference_transcript": example.reference_transcript,
            }
        )

    save_predictions(prediction_rows, config.eval.predictions_output_path)
    save_json(config.eval.metrics_output_path, metrics)


if __name__ == "__main__":
    main()
