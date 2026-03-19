from __future__ import annotations

from typing import Any, Protocol

from .config import PromptConfig
from .prompting.templates import build_training_prompt
from .schema import TrainingExample


class TokenizerLike(Protocol):
    pad_token_id: int | None
    eos_token_id: int | None
    eos_token: str | None
    pad_token: str | None

    def __call__(self, text: str, **kwargs: Any) -> Any:
        ...


def load_tokenizer(model_name: str, tokenizer_name: str | None = None):
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ImportError("transformers is required to load the tokenizer") from exc

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name or model_name, trust_remote_code=True)
    if tokenizer.pad_token is None and tokenizer.eos_token is not None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def _tokenizer_output_to_ids(output: Any) -> list[int]:
    if isinstance(output, dict):
        return list(output["input_ids"])
    if hasattr(output, "input_ids"):
        return list(output.input_ids)
    return list(output)


def _encode_text(tokenizer: TokenizerLike, text: str) -> list[int]:
    output = tokenizer(text, add_special_tokens=False, truncation=False)
    return _tokenizer_output_to_ids(output)


def build_labels(input_ids: list[int], prompt_token_count: int, ignore_index: int = -100) -> list[int]:
    return [ignore_index] * prompt_token_count + input_ids[prompt_token_count:]


def tokenize_supervised_example(
    example: TrainingExample,
    prompt_config: PromptConfig,
    tokenizer: TokenizerLike,
    max_length: int,
) -> dict[str, Any]:
    if not example.reference_transcript:
        raise ValueError("Training example is missing reference_transcript")

    prompt_text = build_training_prompt(example, prompt_config)
    target_text = " " + example.reference_transcript.strip()

    prompt_ids = _encode_text(tokenizer, prompt_text)
    target_ids = _encode_text(tokenizer, target_text)
    eos_token_id = getattr(tokenizer, "eos_token_id", None)
    if eos_token_id is not None:
        target_ids = target_ids + [eos_token_id]

    max_prompt_tokens = max(max_length - len(target_ids), 0)
    if len(prompt_ids) > max_prompt_tokens:
        prompt_ids = prompt_ids[:max_prompt_tokens]

    remaining = max_length - len(prompt_ids)
    target_ids = target_ids[:remaining]
    input_ids = prompt_ids + target_ids
    attention_mask = [1] * len(input_ids)
    labels = build_labels(input_ids, len(prompt_ids))

    return {
        "utterance_id": example.utterance_id,
        "prompt_text": prompt_text,
        "target_text": example.reference_transcript,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
        "prompt_token_count": len(prompt_ids),
    }


def collate_causal_lm_batch(
    features: list[dict[str, Any]],
    pad_token_id: int = 0,
    label_pad_token_id: int = -100,
) -> dict[str, Any]:
    max_length = max(len(feature["input_ids"]) for feature in features)

    input_ids: list[list[int]] = []
    attention_mask: list[list[int]] = []
    labels: list[list[int]] = []
    utterance_ids: list[str] = []

    for feature in features:
        pad_count = max_length - len(feature["input_ids"])
        input_ids.append(feature["input_ids"] + [pad_token_id] * pad_count)
        attention_mask.append(feature["attention_mask"] + [0] * pad_count)
        labels.append(feature["labels"] + [label_pad_token_id] * pad_count)
        utterance_ids.append(feature.get("utterance_id", ""))

    try:
        import torch

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "utterance_ids": utterance_ids,
        }
    except ImportError:
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "utterance_ids": utterance_ids,
        }
