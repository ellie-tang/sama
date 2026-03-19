from __future__ import annotations

import json
from typing import Iterable


SYSTEM_PROMPT = (
    "You are a labeling engine for disordered speech audio collected from Vuzix Blade 2 smart glasses. "
    "You receive Whisper ASR utterances, context metadata, and a target utterance. "
    "Return strict JSON only. Decide whether the target utterance can be assigned a clean canonical intent label."
)


def build_qwen_labeling_prompt(
    conversation_lines: Iterable[str],
    target_utterance_id: str,
    target_transcript: str,
    frame_descriptions: Iterable[str],
) -> str:
    payload = {
        "task": "Decide if the target utterance is labelable for supervised ASR finetuning.",
        "rules": [
            "Labelable means the canonical text label is clear enough for training.",
            "Use surrounding utterances as context.",
            "If the context is insufficient, mark labelable false.",
            "If context helps but confidence is moderate, request human review.",
            "Return JSON keys: labelable, canonical_label, confidence, reason, needs_human_review, discard, evidence.",
        ],
        "target_utterance_id": target_utterance_id,
        "target_transcript": target_transcript,
        "conversation": list(conversation_lines),
        "frame_descriptions": list(frame_descriptions),
    }
    return json.dumps(payload, ensure_ascii=True, indent=2)
