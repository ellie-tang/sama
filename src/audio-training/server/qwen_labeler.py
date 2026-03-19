from __future__ import annotations

import json
import re
from urllib import error, request

from shared.contracts import LabelDecisionContract
from shared.prompts import SYSTEM_PROMPT, build_qwen_labeling_prompt
from server.config import AudioTrainingSettings
from server.context_builder import ConversationContext


YES_WORDS = {"yes", "yeah", "yep", "correct", "right", "uh huh"}
NO_WORDS = {"no", "nope", "wrong", "incorrect"}


class QwenLabeler:
    def __init__(self, settings: AudioTrainingSettings):
        self.settings = settings

    def load_qwen_client(self) -> dict[str, str]:
        return {
            "backend": self.settings.qwen_backend,
            "model": self.settings.qwen_model,
            "api_base": self.settings.qwen_api_base,
        }

    def decide_if_labelable(self, context: ConversationContext) -> LabelDecisionContract:
        if self.settings.qwen_backend == "openai_compatible":
            try:
                return self._call_openai_compatible(context)
            except Exception:
                return self._heuristic_decision(context, degraded=True)
        return self._heuristic_decision(context, degraded=False)

    def infer_canonical_label(self, context: ConversationContext) -> str | None:
        lines = context.conversation_lines
        if not lines:
            return None

        for index in range(1, len(lines)):
            current = self._normalize(self._line_to_text(lines[index]))
            previous = lines[index - 1]
            if current in YES_WORDS:
                candidate = self._extract_previous_candidate(previous)
                if candidate:
                    return candidate
            if current in NO_WORDS:
                return None

        target_text = self._normalize(context.target_transcript)
        if target_text in NO_WORDS:
            return None

        longest = max((self._line_to_text(item) for item in lines), key=len, default="")
        longest = re.sub(r"^(do you mean|did you say)\s+", "", longest, flags=re.IGNORECASE).strip().rstrip("?")
        return longest or None

    def score_label_confidence(self, context: ConversationContext, canonical_label: str | None) -> float:
        if not canonical_label:
            return 0.2

        confidence = 0.65
        if self._conversation_has_confirmation(context.conversation_lines):
            confidence = 0.9
        elif canonical_label.lower() == context.target_transcript.lower().strip():
            confidence = 0.76

        if len(context.conversation_lines) >= 3:
            confidence += 0.04
        if context.frame_descriptions:
            confidence += 0.02
        return min(confidence, 0.98)

    def build_json_prompt(self, context: ConversationContext) -> str:
        return build_qwen_labeling_prompt(
            conversation_lines=context.conversation_lines,
            target_utterance_id=context.target_utterance_id,
            target_transcript=context.target_transcript,
            frame_descriptions=context.frame_descriptions,
        )

    def _heuristic_decision(self, context: ConversationContext, degraded: bool) -> LabelDecisionContract:
        canonical_label = self.infer_canonical_label(context)
        confidence = self.score_label_confidence(context, canonical_label)

        if not canonical_label:
            return LabelDecisionContract(
                labelable=False,
                canonical_label=None,
                confidence=0.2 if not degraded else 0.15,
                reason="Context does not resolve a canonical label.",
                needs_human_review=False,
                discard=True,
                evidence=context.conversation_lines,
                raw_model_response={"backend": "heuristic", "degraded": degraded},
            )

        needs_review = confidence < 0.82
        discard = confidence < 0.55
        reason = "Resolved from confirmation turn." if self._normalize(context.target_transcript) in YES_WORDS else "Best effort canonicalization from context."
        return LabelDecisionContract(
            labelable=not discard,
            canonical_label=canonical_label,
            confidence=confidence,
            reason=reason if not degraded else f"{reason} Fallbacked from API error.",
            needs_human_review=needs_review and not discard,
            discard=discard,
            evidence=context.conversation_lines,
            raw_model_response={"backend": "heuristic", "degraded": degraded},
        )

    def _call_openai_compatible(self, context: ConversationContext) -> LabelDecisionContract:
        url = f"{self.settings.qwen_api_base.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.qwen_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self.build_json_prompt(context)},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.qwen_api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            raise RuntimeError(f"Qwen API request failed: {exc}") from exc

        content = raw["choices"][0]["message"]["content"]
        decision_payload = json.loads(content)
        return LabelDecisionContract(
            labelable=bool(decision_payload.get("labelable")),
            canonical_label=decision_payload.get("canonical_label"),
            confidence=float(decision_payload.get("confidence", 0.0)),
            reason=str(decision_payload.get("reason", "")),
            needs_human_review=bool(decision_payload.get("needs_human_review", False)),
            discard=bool(decision_payload.get("discard", False)),
            evidence=list(decision_payload.get("evidence", [])),
            raw_model_response=raw,
        )

    def _extract_previous_candidate(self, line: str) -> str | None:
        text = self._line_to_text(line)
        match = re.search(r"do you mean (.+?)(?:\?|$)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip("?")
        return text.strip() or None

    def _conversation_has_confirmation(self, lines: list[str]) -> bool:
        for index in range(1, len(lines)):
            current = self._normalize(self._line_to_text(lines[index]))
            previous = self._line_to_text(lines[index - 1])
            if current in YES_WORDS and re.search(r"do you mean", previous, flags=re.IGNORECASE):
                return True
        return False

    def _line_to_text(self, line: str) -> str:
        return line.split(":", 1)[1].strip() if ":" in line else line.strip()

    def _normalize(self, value: str) -> str:
        return re.sub(r"[^a-z0-9 ]+", "", value.lower()).strip()
