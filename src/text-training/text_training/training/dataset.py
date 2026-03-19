from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..config import AppConfig
from ..data.loaders import load_jsonl_dataset
from ..tokenization import tokenize_supervised_example


@dataclass
class TextTrainingDataset:
    features: list[dict[str, Any]]

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, index: int) -> dict[str, Any]:
        return self.features[index]


def build_hf_dataset(examples: list[dict[str, Any]]) -> TextTrainingDataset:
    return TextTrainingDataset(features=examples)


def map_tokenization(dataset: list[Any], tokenizer: Any, prompt_config: Any, max_length: int) -> TextTrainingDataset:
    features = [
        tokenize_supervised_example(
            example=example,
            prompt_config=prompt_config,
            tokenizer=tokenizer,
            max_length=max_length,
        )
        for example in dataset
    ]
    return TextTrainingDataset(features=features)


def create_train_val_datasets(config: AppConfig, tokenizer: Any) -> tuple[TextTrainingDataset, TextTrainingDataset | None]:
    train_examples = load_jsonl_dataset(config.data.train_path)
    train_dataset = map_tokenization(train_examples, tokenizer, config.prompt, config.train.max_seq_length)

    val_dataset = None
    if config.data.val_path:
        val_examples = load_jsonl_dataset(config.data.val_path)
        if val_examples:
            val_dataset = map_tokenization(val_examples, tokenizer, config.prompt, config.train.max_seq_length)

    return train_dataset, val_dataset
