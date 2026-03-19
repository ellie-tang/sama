from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass

from ..schema import ASRHypothesis, TrainingExample, VisionContext


_WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class DatasetSplits:
    train: list[TrainingExample]
    val: list[TrainingExample]
    test: list[TrainingExample]


def normalize_transcript_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = normalized.replace("\u00a0", " ")
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()


def clean_visual_context(text: str) -> str:
    return normalize_transcript_text(text)


def sort_and_trim_hypotheses(hypotheses: list[ASRHypothesis], top_k: int) -> list[ASRHypothesis]:
    def sort_key(item: ASRHypothesis) -> tuple[float, int]:
        score = item.score if item.score is not None else float("-inf")
        rank = item.rank if item.rank is not None else 10**6
        return (-score, rank)

    ranked = sorted(hypotheses, key=sort_key)
    trimmed = ranked[:top_k]
    for index, hypothesis in enumerate(trimmed, start=1):
        hypothesis.rank = index
    return trimmed


def deduplicate_hypotheses(hypotheses: list[ASRHypothesis]) -> list[ASRHypothesis]:
    seen: set[str] = set()
    deduplicated: list[ASRHypothesis] = []
    for hypothesis in hypotheses:
        key = normalize_transcript_text(hypothesis.text).casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        deduplicated.append(hypothesis)
    return deduplicated


def align_modalities(
    examples: list[TrainingExample],
    top_k: int | None = None,
    require_reference: bool = False,
) -> list[TrainingExample]:
    aligned: list[TrainingExample] = []
    for example in examples:
        normalized_hypotheses = [
            ASRHypothesis(
                text=normalize_transcript_text(item.text),
                score=item.score,
                rank=item.rank,
                source=item.source,
            )
            for item in example.nbest_hypotheses
        ]
        normalized_hypotheses = deduplicate_hypotheses(normalized_hypotheses)
        if top_k is not None:
            normalized_hypotheses = sort_and_trim_hypotheses(normalized_hypotheses, top_k)
        if not normalized_hypotheses:
            continue

        visual_context = example.visual_context
        if visual_context:
            visual_context = VisionContext(
                text=clean_visual_context(visual_context.text),
                entities=visual_context.entities,
                speaker_hint=visual_context.speaker_hint,
                raw=visual_context.raw,
            )

        reference = normalize_transcript_text(example.reference_transcript or "")
        if require_reference and not reference:
            continue

        aligned.append(
            TrainingExample(
                utterance_id=example.utterance_id,
                nbest_hypotheses=normalized_hypotheses,
                visual_context=visual_context,
                reference_transcript=reference or None,
                audio_path=example.audio_path,
                segment_timestamps=example.segment_timestamps,
                metadata=example.metadata,
            )
        )
    return aligned


def split_dataset(
    examples: list[TrainingExample],
    train_ratio: float,
    val_ratio: float,
    seed: int,
) -> DatasetSplits:
    records = list(examples)
    random.Random(seed).shuffle(records)
    total = len(records)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    return DatasetSplits(
        train=records[:train_end],
        val=records[train_end:val_end],
        test=records[val_end:],
    )
