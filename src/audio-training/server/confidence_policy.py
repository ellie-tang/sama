from __future__ import annotations

from shared.contracts import LabelDecisionContract
from server.config import AudioTrainingSettings


def is_dataset_ready(decision: LabelDecisionContract, settings: AudioTrainingSettings) -> bool:
    return (
        decision.labelable
        and not decision.discard
        and not decision.needs_human_review
        and decision.confidence >= settings.min_label_confidence
        and bool(decision.canonical_label)
    )


def requires_human_review(decision: LabelDecisionContract, settings: AudioTrainingSettings) -> bool:
    return (
        decision.labelable
        and not decision.discard
        and bool(decision.canonical_label)
        and (
            decision.needs_human_review
            or settings.review_confidence <= decision.confidence < settings.min_label_confidence
        )
    )


def should_discard_candidate(decision: LabelDecisionContract) -> bool:
    return decision.discard or not decision.labelable or not decision.canonical_label
