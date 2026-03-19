from __future__ import annotations

from shared.contracts import LabelDecisionContract
from server.confidence_policy import is_dataset_ready, requires_human_review, should_discard_candidate


def test_confidence_policy_routes_high_confidence_to_dataset(audio_training_settings):
    decision = LabelDecisionContract(
        labelable=True,
        canonical_label="turn off tv",
        confidence=0.9,
        reason="Resolved from confirmation turn.",
        needs_human_review=False,
        discard=False,
    )

    assert is_dataset_ready(decision, audio_training_settings) is True
    assert requires_human_review(decision, audio_training_settings) is False
    assert should_discard_candidate(decision) is False


def test_confidence_policy_routes_mid_confidence_to_review(audio_training_settings):
    decision = LabelDecisionContract(
        labelable=True,
        canonical_label="turn off tv",
        confidence=0.7,
        reason="Context helps but confidence is moderate.",
        needs_human_review=True,
        discard=False,
    )

    assert is_dataset_ready(decision, audio_training_settings) is False
    assert requires_human_review(decision, audio_training_settings) is True
    assert should_discard_candidate(decision) is False


def test_confidence_policy_discards_unresolved_label(audio_training_settings):
    decision = LabelDecisionContract(
        labelable=False,
        canonical_label=None,
        confidence=0.2,
        reason="Context does not resolve a canonical label.",
        needs_human_review=False,
        discard=True,
    )

    assert is_dataset_ready(decision, audio_training_settings) is False
    assert requires_human_review(decision, audio_training_settings) is False
    assert should_discard_candidate(decision) is True
