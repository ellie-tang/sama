from __future__ import annotations

from server.context_builder import ConversationContext
from server.qwen_labeler import QwenLabeler


def test_qwen_labeler_uses_confirmation_turn(audio_training_settings):
    labeler = QwenLabeler(audio_training_settings)
    context = ConversationContext(
        conversation_lines=[
            "wearer: tons of tv",
            "partner: do you mean turn off tv?",
            "wearer: yes",
        ],
        frame_descriptions=[],
        target_utterance_id="u1",
        target_transcript="tons of tv",
        target_audio_path="/tmp/u1.wav",
    )

    decision = labeler.decide_if_labelable(context)

    assert decision.labelable is True
    assert decision.canonical_label == "turn off tv"
    assert decision.confidence >= 0.82


def test_qwen_labeler_returns_none_for_negative_confirmation(audio_training_settings):
    labeler = QwenLabeler(audio_training_settings)
    context = ConversationContext(
        conversation_lines=[
            "wearer: tons of tv",
            "partner: do you mean turn off tv?",
            "wearer: no",
        ],
        frame_descriptions=[],
        target_utterance_id="u1",
        target_transcript="tons of tv",
        target_audio_path="/tmp/u1.wav",
    )

    decision = labeler.decide_if_labelable(context)

    assert decision.discard is True
    assert decision.canonical_label is None


def test_qwen_labeler_uses_frame_context_to_boost_confidence(audio_training_settings):
    labeler = QwenLabeler(audio_training_settings)
    context = ConversationContext(
        conversation_lines=[
            "wearer: turn off tv",
        ],
        frame_descriptions=["television visible in front of wearer"],
        target_utterance_id="u1",
        target_transcript="turn off tv",
        target_audio_path="/tmp/u1.wav",
    )

    decision = labeler.decide_if_labelable(context)

    assert decision.labelable is True
    assert decision.canonical_label == "turn off tv"
    assert decision.confidence > 0.76
