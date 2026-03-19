from __future__ import annotations

from ..config import PromptConfig
from ..schema import ASRHypothesis, InferenceExample, TrainingExample, VisionContext


def build_system_prompt(config: PromptConfig) -> str:
    if not config.include_system_prompt:
        return ""
    return config.system_prompt.strip()


def render_nbest_block(
    hypotheses: list[ASRHypothesis],
    include_confidence_scores: bool = True,
) -> str:
    lines = ["### N-best hypotheses"]
    for index, hypothesis in enumerate(hypotheses, start=1):
        score_suffix = ""
        if include_confidence_scores and hypothesis.score is not None:
            score_suffix = f" (score={hypothesis.score:.4f})"
        lines.append(f"{index}. {hypothesis.text}{score_suffix}")
    return "\n".join(lines)


def render_context_block(context: VisionContext | None) -> str:
    lines = ["### Environmental context"]
    if not context or not context.text:
        lines.append("None")
        return "\n".join(lines)

    lines.append(context.text)
    if context.entities:
        lines.append(f"Entities: {', '.join(context.entities)}")
    if context.speaker_hint:
        lines.append(f"Speaker hint: {context.speaker_hint}")
    return "\n".join(lines)


def _build_shared_prompt(
    utterance_id: str,
    hypotheses: list[ASRHypothesis],
    context: VisionContext | None,
    config: PromptConfig,
) -> str:
    sections: list[str] = []
    system_prompt = build_system_prompt(config)
    if system_prompt:
        sections.append("### System\n" + system_prompt)
    sections.append("### Task\n" + config.task_prompt.strip())
    sections.append(f"### Utterance ID\n{utterance_id}")
    sections.append(render_nbest_block(hypotheses, config.include_confidence_scores))
    if config.include_visual_context:
        sections.append(render_context_block(context))
    sections.append("### Response rules\nReturn transcript only. Do not explain your reasoning.")
    sections.append(config.answer_prefix)
    return "\n\n".join(sections)


def build_training_prompt(example: TrainingExample, config: PromptConfig) -> str:
    return _build_shared_prompt(
        utterance_id=example.utterance_id,
        hypotheses=example.nbest_hypotheses,
        context=example.visual_context,
        config=config,
    )


def build_inference_prompt(example: InferenceExample, config: PromptConfig) -> str:
    return _build_shared_prompt(
        utterance_id=example.utterance_id,
        hypotheses=example.nbest_hypotheses,
        context=example.visual_context,
        config=config,
    )
