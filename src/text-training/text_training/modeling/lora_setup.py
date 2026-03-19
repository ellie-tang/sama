from __future__ import annotations

from typing import Any

from ..config import LoRAConfig


def _load_torch():
    try:
        import torch
    except ImportError as exc:
        raise ImportError("torch is required for model loading") from exc
    return torch


def _resolve_dtype(dtype_name: str):
    torch = _load_torch()
    mapping = {
        "float16": torch.float16,
        "fp16": torch.float16,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
        "float32": torch.float32,
        "fp32": torch.float32,
    }
    if dtype_name not in mapping:
        raise ValueError(f"Unsupported dtype: {dtype_name}")
    return mapping[dtype_name]


def load_base_model(
    model_name: str,
    dtype: str = "bfloat16",
    device_map: str = "auto",
    load_in_4bit: bool = False,
    trust_remote_code: bool = True,
):
    try:
        from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    except ImportError as exc:
        raise ImportError("transformers is required to load the base model") from exc

    torch_dtype = _resolve_dtype(dtype)
    quantization_config = None
    if load_in_4bit:
        quantization_config = BitsAndBytesConfig(load_in_4bit=True)

    return AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch_dtype,
        device_map=device_map,
        quantization_config=quantization_config,
        trust_remote_code=trust_remote_code,
    )


def prepare_model_for_kbit_training_if_needed(model: Any):
    try:
        from peft import prepare_model_for_kbit_training
    except ImportError as exc:
        raise ImportError("peft is required to prepare k-bit training") from exc

    is_quantized = getattr(model, "is_loaded_in_4bit", False) or getattr(model, "is_loaded_in_8bit", False)
    return prepare_model_for_kbit_training(model) if is_quantized else model


def build_lora_config(config: LoRAConfig):
    try:
        from peft import LoraConfig
    except ImportError as exc:
        raise ImportError("peft is required to build the LoRA config") from exc

    return LoraConfig(
        r=config.rank,
        lora_alpha=config.alpha,
        lora_dropout=config.dropout,
        bias=config.bias,
        task_type=config.task_type,
        target_modules=config.target_modules,
    )


def attach_lora_adapters(model: Any, lora_config: Any):
    try:
        from peft import get_peft_model
    except ImportError as exc:
        raise ImportError("peft is required to attach LoRA adapters") from exc
    return get_peft_model(model, lora_config)


def print_trainable_parameters(model: Any) -> None:
    trainable = 0
    total = 0
    for _, parameter in model.named_parameters():
        count = parameter.numel()
        total += count
        if parameter.requires_grad:
            trainable += count
    ratio = (trainable / total * 100.0) if total else 0.0
    print(f"Trainable parameters: {trainable:,} / {total:,} ({ratio:.2f}%)")
