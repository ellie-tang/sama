from __future__ import annotations

import argparse
from pathlib import Path

from ..config import load_config
from ..data.loaders import load_references, load_vlm_context, load_whisper_nbest, merge_multimodal_records
from ..data.preprocess import align_modalities, split_dataset
from ..utils import ensure_dir, save_json, save_jsonl


def build_training_corpus(config_path: str) -> None:
    config = load_config(config_path)

    whisper_nbest = load_whisper_nbest(config.data.whisper_path)
    vlm_context = load_vlm_context(config.data.vlm_path) if config.data.vlm_path else {}
    references = load_references(config.data.references_path) if config.data.references_path else {}

    examples = merge_multimodal_records(
        whisper_nbest=whisper_nbest,
        vlm_context=vlm_context,
        references=references,
        include_visual_context=config.data.include_visual_context,
    )
    examples = align_modalities(
        examples,
        top_k=config.data.top_k_hypotheses,
        require_reference=bool(config.data.references_path),
    )

    splits = split_dataset(
        examples=examples,
        train_ratio=config.data.train_split,
        val_ratio=config.data.val_split,
        seed=config.data.seed,
    )

    output_dir = ensure_dir(config.data.output_dir)
    train_path = config.data.train_path or str(output_dir / "train.jsonl")
    val_path = config.data.val_path or str(output_dir / "val.jsonl")
    test_path = config.data.test_path or str(output_dir / "test.jsonl")

    save_jsonl(train_path, [example.to_dict() for example in splits.train])
    save_jsonl(val_path, [example.to_dict() for example in splits.val])
    save_jsonl(test_path, [example.to_dict() for example in splits.test])

    metadata = {
        "total_examples": len(examples),
        "train_examples": len(splits.train),
        "val_examples": len(splits.val),
        "test_examples": len(splits.test),
        "top_k_hypotheses": config.data.top_k_hypotheses,
        "include_visual_context": config.data.include_visual_context,
    }
    save_json(Path(output_dir) / "metadata.json", metadata)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build text-training dataset splits")
    parser.add_argument("--config", required=True, help="Path to JSON or YAML config")
    args = parser.parse_args()
    build_training_corpus(args.config)


if __name__ == "__main__":
    main()
