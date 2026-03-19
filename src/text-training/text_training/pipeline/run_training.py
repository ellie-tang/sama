from __future__ import annotations

import argparse

from ..config import load_config
from ..modeling.lora_setup import (
    attach_lora_adapters,
    build_lora_config,
    load_base_model,
    prepare_model_for_kbit_training_if_needed,
    print_trainable_parameters,
)
from ..tokenization import collate_causal_lm_batch, load_tokenizer
from ..training.dataset import create_train_val_datasets
from ..training.trainer import build_trainer, train_and_save


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LoRA fine-tuning for text second-pass correction")
    parser.add_argument("--config", required=True, help="Path to JSON or YAML config")
    args = parser.parse_args()

    config = load_config(args.config)
    tokenizer = load_tokenizer(config.model.base_model_name, config.model.tokenizer_name or None)
    train_dataset, val_dataset = create_train_val_datasets(config, tokenizer)

    model = load_base_model(
        model_name=config.model.base_model_name,
        dtype=config.model.dtype,
        device_map=config.model.device_map,
        load_in_4bit=config.model.load_in_4bit,
        trust_remote_code=config.model.trust_remote_code,
    )
    model = prepare_model_for_kbit_training_if_needed(model)
    lora_config = build_lora_config(config.lora)
    model = attach_lora_adapters(model, lora_config)
    print_trainable_parameters(model)

    collator = lambda batch: collate_causal_lm_batch(  # noqa: E731
        batch,
        pad_token_id=tokenizer.pad_token_id or 0,
    )
    trainer = build_trainer(model, tokenizer, train_dataset, val_dataset, collator, config.train)
    if config.train.resume_from_checkpoint:
        trainer.train(resume_from_checkpoint=config.train.resume_from_checkpoint)
        trainer.save_model(config.train.output_dir)
        tokenizer.save_pretrained(config.train.output_dir)
        return

    train_and_save(model, trainer, config.train.output_dir, tokenizer=tokenizer)


if __name__ == "__main__":
    main()
