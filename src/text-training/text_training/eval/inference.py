from __future__ import annotations

from typing import Any

from ..config import GenerationConfig, PromptConfig
from ..modeling.lora_setup import load_base_model
from ..prompting.templates import build_inference_prompt
from ..schema import InferenceExample
from ..utils import save_jsonl


def load_adapter_for_inference(
    base_model_name: str,
    adapter_path: str,
    dtype: str = "bfloat16",
    device_map: str = "auto",
    load_in_4bit: bool = False,
):
    try:
        from peft import PeftModel
    except ImportError as exc:
        raise ImportError("peft is required to load LoRA adapters") from exc

    model = load_base_model(
        model_name=base_model_name,
        dtype=dtype,
        device_map=device_map,
        load_in_4bit=load_in_4bit,
    )
    return PeftModel.from_pretrained(model, adapter_path)


def _extract_answer(decoded_text: str, answer_prefix: str) -> str:
    if answer_prefix in decoded_text:
        return decoded_text.split(answer_prefix, 1)[-1].strip()
    return decoded_text.strip()


def generate_refined_transcript(
    example: InferenceExample,
    model: Any,
    tokenizer: Any,
    prompt_config: PromptConfig,
    generation_config: GenerationConfig,
) -> str:
    prompt = build_inference_prompt(example, prompt_config)
    encoded = tokenizer(prompt, return_tensors="pt")
    encoded = {key: value.to(model.device) for key, value in encoded.items()}

    generated = model.generate(
        **encoded,
        max_new_tokens=generation_config.max_new_tokens,
        temperature=generation_config.temperature,
        do_sample=generation_config.do_sample,
        num_beams=generation_config.num_beams,
        repetition_penalty=generation_config.repetition_penalty,
    )
    prompt_length = encoded["input_ids"].shape[-1]
    completion_ids = generated[0][prompt_length:]
    decoded = tokenizer.decode(completion_ids, skip_special_tokens=True)
    return _extract_answer(decoded, prompt_config.answer_prefix)


def batch_generate(
    examples: list[InferenceExample],
    model: Any,
    tokenizer: Any,
    prompt_config: PromptConfig,
    generation_config: GenerationConfig,
) -> list[str]:
    return [
        generate_refined_transcript(example, model, tokenizer, prompt_config, generation_config)
        for example in examples
    ]


def save_predictions(predictions: list[dict[str, Any]], output_path: str) -> None:
    save_jsonl(output_path, predictions)
