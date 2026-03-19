from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar, get_args, get_origin, get_type_hints

from .utils import load_json

T = TypeVar("T")


@dataclass
class ModelConfig:
    base_model_name: str = ""
    tokenizer_name: str = ""
    dtype: str = "bfloat16"
    device_map: str = "auto"
    load_in_4bit: bool = False
    trust_remote_code: bool = True


@dataclass
class DataConfig:
    whisper_path: str = ""
    vlm_path: str = ""
    references_path: str = ""
    train_path: str = ""
    val_path: str = ""
    test_path: str = ""
    output_dir: str = "src/text-training/artifacts/dataset"
    top_k_hypotheses: int = 5
    include_confidence_scores: bool = True
    include_timestamps: bool = False
    include_visual_context: bool = True
    train_split: float = 0.8
    val_split: float = 0.1
    seed: int = 17


@dataclass
class PromptConfig:
    include_system_prompt: bool = True
    system_prompt: str = (
        "You are a second-pass transcription corrector. Use the n-best hypotheses "
        "and available scene context to produce the best final transcript. Return transcript only."
    )
    task_prompt: str = (
        "Resolve ASR ambiguity using the candidate transcripts and any useful environmental context."
    )
    answer_prefix: str = "Final transcript:"
    include_confidence_scores: bool = True
    include_visual_context: bool = True


@dataclass
class LoRAConfig:
    rank: int = 16
    alpha: int = 32
    dropout: float = 0.05
    bias: str = "none"
    task_type: str = "CAUSAL_LM"
    target_modules: list[str] = field(
        default_factory=lambda: ["k_proj", "v_proj", "gate_proj", "up_proj", "down_proj"]
    )


@dataclass
class TrainConfig:
    output_dir: str = "src/text-training/artifacts/checkpoints"
    max_seq_length: int = 2048
    learning_rate: float = 2e-4
    batch_size: int = 1
    gradient_accumulation_steps: int = 16
    num_train_epochs: int = 3
    warmup_ratio: float = 0.03
    weight_decay: float = 0.0
    logging_steps: int = 10
    eval_steps: int = 100
    save_steps: int = 100
    save_total_limit: int = 2
    fp16: bool = False
    bf16: bool = True
    gradient_checkpointing: bool = True
    resume_from_checkpoint: str = ""
    report_to: list[str] = field(default_factory=list)


@dataclass
class EvalConfig:
    output_dir: str = "src/text-training/artifacts/eval"
    prediction_input_path: str = ""
    metrics_output_path: str = "src/text-training/artifacts/eval/metrics.json"
    predictions_output_path: str = "src/text-training/artifacts/eval/predictions.jsonl"


@dataclass
class GenerationConfig:
    max_new_tokens: int = 128
    temperature: float = 0.0
    do_sample: bool = False
    num_beams: int = 1
    repetition_penalty: float = 1.05


@dataclass
class AppConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)
    lora: LoRAConfig = field(default_factory=LoRAConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ImportError("pyyaml is required to load YAML config files") from exc

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _coerce_value(field_type: Any, value: Any) -> Any:
    origin = get_origin(field_type)
    if is_dataclass(field_type):
        return _from_dict(field_type, value or {})

    if origin is list:
        item_type = get_args(field_type)[0] if get_args(field_type) else Any
        return [_coerce_value(item_type, item) for item in (value or [])]

    if origin is dict:
        return value or {}

    if origin is not None:
        args = [arg for arg in get_args(field_type) if arg is not type(None)]
        if len(args) == 1:
            return _coerce_value(args[0], value)

    return value


def _from_dict(cls: type[T], payload: dict[str, Any]) -> T:
    type_hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for item in fields(cls):
        if item.name not in payload:
            continue
        field_type = type_hints.get(item.name, item.type)
        kwargs[item.name] = _coerce_value(field_type, payload[item.name])
    return cls(**kwargs)


def load_config(path: str) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if config_path.suffix in {".yaml", ".yml"}:
        payload = _load_yaml(config_path)
    else:
        payload = load_json(config_path)

    config = _from_dict(AppConfig, payload or {})
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    if not config.model.base_model_name:
        raise ValueError("model.base_model_name must be set")
    if config.data.top_k_hypotheses < 1:
        raise ValueError("data.top_k_hypotheses must be >= 1")
    if config.train.max_seq_length < 32:
        raise ValueError("train.max_seq_length is unrealistically small")
    if config.data.train_split <= 0 or config.data.train_split >= 1:
        raise ValueError("data.train_split must be between 0 and 1")
    if config.data.val_split < 0 or config.data.val_split >= 1:
        raise ValueError("data.val_split must be between 0 and 1")
    if config.data.train_split + config.data.val_split >= 1:
        raise ValueError("data.train_split + data.val_split must be < 1")
