from __future__ import annotations

from pathlib import Path
from typing import Any

from ..schema import ASRHypothesis, TrainingExample, VisionContext
from ..utils import load_json_or_jsonl


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if "records" in payload and isinstance(payload["records"], list):
            return [item for item in payload["records"] if isinstance(item, dict)]
        return [payload]
    raise ValueError("Unsupported payload format for dataset loading")


def _utterance_id(record: dict[str, Any]) -> str:
    for key in ("utterance_id", "id", "sample_id", "segment_id"):
        if record.get(key):
            return str(record[key])
    raise ValueError(f"Could not find utterance id in record: {record}")


def _parse_hypothesis(item: Any, fallback_rank: int) -> ASRHypothesis:
    if isinstance(item, str):
        return ASRHypothesis(text=item, rank=fallback_rank)
    if isinstance(item, dict):
        payload = dict(item)
        if "rank" not in payload:
            payload["rank"] = fallback_rank
        return ASRHypothesis.from_dict(payload)
    raise ValueError(f"Unsupported hypothesis format: {item!r}")


def load_whisper_nbest(path: str) -> dict[str, list[ASRHypothesis]]:
    payload = load_json_or_jsonl(path)
    records = _records_from_payload(payload)
    utterance_map: dict[str, list[ASRHypothesis]] = {}
    for record in records:
        utterance_id = _utterance_id(record)
        candidates = (
            record.get("nbest_hypotheses")
            or record.get("hypotheses")
            or record.get("candidates")
            or record.get("nbest")
        )
        if candidates is None:
            top_text = record.get("text") or record.get("transcript") or ""
            candidates = [top_text] if top_text else []
        hypotheses = [_parse_hypothesis(item, index + 1) for index, item in enumerate(candidates)]
        utterance_map[utterance_id] = hypotheses
    return utterance_map


def load_vlm_context(path: str) -> dict[str, VisionContext]:
    payload = load_json_or_jsonl(path)
    records = _records_from_payload(payload)
    context_map: dict[str, VisionContext] = {}
    for record in records:
        utterance_id = _utterance_id(record)
        context = VisionContext.from_dict(
            {
                "text": record.get("text")
                or record.get("visual_context_text")
                or record.get("context")
                or record.get("scene_description")
                or "",
                "entities": record.get("entities") or record.get("scene_entities") or [],
                "speaker_hint": record.get("speaker_hint"),
                "raw": record,
            }
        )
        if context:
            context_map[utterance_id] = context
    return context_map


def load_references(path: str) -> dict[str, str]:
    payload = load_json_or_jsonl(path)
    records = _records_from_payload(payload)
    references: dict[str, str] = {}
    for record in records:
        utterance_id = _utterance_id(record)
        text = record.get("reference_transcript") or record.get("reference") or record.get("text") or ""
        references[utterance_id] = str(text)
    return references


def merge_multimodal_records(
    whisper_nbest: dict[str, list[ASRHypothesis]],
    vlm_context: dict[str, VisionContext] | None = None,
    references: dict[str, str] | None = None,
    include_visual_context: bool = True,
) -> list[TrainingExample]:
    vlm_context = vlm_context or {}
    references = references or {}
    examples: list[TrainingExample] = []

    for utterance_id, hypotheses in whisper_nbest.items():
        examples.append(
            TrainingExample(
                utterance_id=utterance_id,
                nbest_hypotheses=hypotheses,
                visual_context=vlm_context.get(utterance_id) if include_visual_context else None,
                reference_transcript=references.get(utterance_id),
                metadata={},
            )
        )
    return examples


def load_jsonl_dataset(path: str) -> list[TrainingExample]:
    payload = load_json_or_jsonl(Path(path))
    records = _records_from_payload(payload)
    return [TrainingExample.from_dict(record) for record in records]
