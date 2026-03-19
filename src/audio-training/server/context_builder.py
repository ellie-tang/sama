from __future__ import annotations

from dataclasses import dataclass

from server.schemas import ContextFrameInput
from server.whisper_asr import TranscriptResult


@dataclass(slots=True)
class ConversationContext:
    conversation_lines: list[str]
    frame_descriptions: list[str]
    target_utterance_id: str
    target_transcript: str
    target_audio_path: str


class ConversationContextBuilder:
    def __init__(self, max_window_ms: int):
        self.max_window_ms = max_window_ms

    def merge_utterances_into_context(
        self,
        utterances: list[dict],
        transcripts: list[TranscriptResult],
        target_utterance_id: str,
    ) -> ConversationContext:
        transcript_map = {item.utterance_id: item for item in transcripts}
        filtered = self.trim_context_window(utterances)
        conversation_lines: list[str] = []
        target_transcript = ""
        target_audio_path = ""

        for utterance in filtered:
            transcript = transcript_map[utterance["utterance_id"]]
            speaker = utterance.get("speaker_tag", "wearer")
            line = f"{speaker}: {transcript.text}"
            conversation_lines.append(line)
            if utterance["utterance_id"] == target_utterance_id:
                target_transcript = transcript.text
                target_audio_path = transcript.source_audio_path

        if not target_transcript and transcripts:
            fallback = transcript_map[target_utterance_id]
            target_transcript = fallback.text
            target_audio_path = fallback.source_audio_path

        return ConversationContext(
            conversation_lines=conversation_lines,
            frame_descriptions=[],
            target_utterance_id=target_utterance_id,
            target_transcript=target_transcript,
            target_audio_path=target_audio_path,
        )

    def format_conversation_prompt(self, context: ConversationContext) -> list[str]:
        return context.conversation_lines

    def attach_frame_metadata(
        self,
        context: ConversationContext,
        frames: list[ContextFrameInput],
    ) -> ConversationContext:
        descriptions = [
            frame.description or f"frame:{frame.frame_id}@{frame.timestamp_ms}"
            for frame in frames
        ]
        context.frame_descriptions.extend(descriptions)
        return context

    def trim_context_window(self, utterances: list[dict]) -> list[dict]:
        if not utterances:
            return []
        end_ms = max(item["end_ms"] for item in utterances)
        start_cutoff = max(0, end_ms - self.max_window_ms)
        return [item for item in utterances if item["end_ms"] >= start_cutoff]
