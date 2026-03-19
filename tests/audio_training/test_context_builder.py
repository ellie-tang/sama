from __future__ import annotations

from server.context_builder import ConversationContextBuilder
from server.schemas import ContextFrameInput
from server.whisper_asr import TranscriptResult


def test_merge_utterances_into_context_keeps_target_audio_path():
    builder = ConversationContextBuilder(max_window_ms=30000)
    utterances = [
        {"utterance_id": "u1", "start_ms": 0, "end_ms": 500, "speaker_tag": "wearer"},
        {"utterance_id": "u2", "start_ms": 1000, "end_ms": 1600, "speaker_tag": "partner"},
        {"utterance_id": "u3", "start_ms": 2000, "end_ms": 2400, "speaker_tag": "wearer"},
    ]
    transcripts = [
        TranscriptResult("u1", "tons of tv", 0.4, "hint", "/tmp/u1.wav"),
        TranscriptResult("u2", "do you mean turn off tv?", 0.99, "hint", "/tmp/u2.wav"),
        TranscriptResult("u3", "yes", 0.99, "hint", "/tmp/u3.wav"),
    ]

    context = builder.merge_utterances_into_context(utterances, transcripts, "u1")

    assert context.target_transcript == "tons of tv"
    assert context.target_audio_path == "/tmp/u1.wav"
    assert context.conversation_lines == [
        "wearer: tons of tv",
        "partner: do you mean turn off tv?",
        "wearer: yes",
    ]


def test_attach_frame_metadata_prefers_descriptions():
    builder = ConversationContextBuilder(max_window_ms=30000)
    utterances = [{"utterance_id": "u1", "start_ms": 0, "end_ms": 500, "speaker_tag": "wearer"}]
    transcripts = [TranscriptResult("u1", "call daughter", 0.9, "hint", "/tmp/u1.wav")]
    context = builder.merge_utterances_into_context(utterances, transcripts, "u1")
    frames = [
        ContextFrameInput(
            frame_id="f1",
            source_file_name="f1.jpg",
            timestamp_ms=1234,
            description="living room television in view",
        )
    ]

    updated = builder.attach_frame_metadata(context, frames)

    assert updated.frame_descriptions == ["living room television in view"]


def test_trim_context_window_drops_older_utterances():
    builder = ConversationContextBuilder(max_window_ms=1500)
    utterances = [
        {"utterance_id": "u1", "start_ms": 0, "end_ms": 400, "speaker_tag": "wearer"},
        {"utterance_id": "u2", "start_ms": 1000, "end_ms": 1400, "speaker_tag": "partner"},
        {"utterance_id": "u3", "start_ms": 2200, "end_ms": 2500, "speaker_tag": "wearer"},
    ]

    trimmed = builder.trim_context_window(utterances)

    assert [item["utterance_id"] for item in trimmed] == ["u2", "u3"]
