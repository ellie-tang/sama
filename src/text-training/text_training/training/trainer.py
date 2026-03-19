from __future__ import annotations

from typing import Any

from ..config import TrainConfig


def build_training_arguments(config: TrainConfig):
    try:
        from transformers import TrainingArguments
    except ImportError as exc:
        raise ImportError("transformers is required to build training arguments") from exc

    evaluation_strategy = "steps" if config.eval_steps > 0 else "no"
    return TrainingArguments(
        output_dir=config.output_dir,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_train_epochs,
        warmup_ratio=config.warmup_ratio,
        weight_decay=config.weight_decay,
        logging_steps=config.logging_steps,
        evaluation_strategy=evaluation_strategy,
        eval_steps=config.eval_steps if config.eval_steps > 0 else None,
        save_steps=config.save_steps,
        save_total_limit=config.save_total_limit,
        fp16=config.fp16,
        bf16=config.bf16,
        gradient_checkpointing=config.gradient_checkpointing,
        report_to=config.report_to,
        remove_unused_columns=False,
    )


def build_trainer(
    model: Any,
    tokenizer: Any,
    train_dataset: Any,
    eval_dataset: Any,
    collator: Any,
    config: TrainConfig,
):
    try:
        from transformers import Trainer
    except ImportError as exc:
        raise ImportError("transformers is required to build the trainer") from exc

    training_args = build_training_arguments(config)
    return Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        data_collator=collator,
    )


def resume_from_checkpoint_if_available(trainer: Any, checkpoint_dir: str | None):
    return trainer.train(resume_from_checkpoint=checkpoint_dir or None)


def train_and_save(model: Any, trainer: Any, output_dir: str, tokenizer: Any | None = None) -> None:
    trainer.train()
    trainer.save_model(output_dir)
    if tokenizer is not None:
        tokenizer.save_pretrained(output_dir)
