import unittest

from text_training.data.preprocess import align_modalities, deduplicate_hypotheses, normalize_transcript_text
from text_training.schema import ASRHypothesis, TrainingExample, VisionContext


class PreprocessTests(unittest.TestCase):
    def test_normalize_transcript_text_collapses_whitespace(self) -> None:
        self.assertEqual(normalize_transcript_text(" hello   world \n"), "hello world")

    def test_deduplicate_hypotheses_removes_case_duplicates(self) -> None:
        hypotheses = [
            ASRHypothesis(text="Hello world", rank=1),
            ASRHypothesis(text=" hello   world ", rank=2),
            ASRHypothesis(text="Different", rank=3),
        ]
        result = deduplicate_hypotheses(hypotheses)
        self.assertEqual([item.text for item in result], ["Hello world", "Different"])

    def test_align_modalities_keeps_visual_context_optional(self) -> None:
        example = TrainingExample(
            utterance_id="utt-1",
            nbest_hypotheses=[ASRHypothesis(text="  hello   there ")],
            visual_context=VisionContext(text=" kitchen   table "),
            reference_transcript=" hello there ",
        )
        aligned = align_modalities([example], top_k=3, require_reference=True)
        self.assertEqual(len(aligned), 1)
        self.assertEqual(aligned[0].nbest_hypotheses[0].text, "hello there")
        self.assertEqual(aligned[0].visual_context.text, "kitchen table")


if __name__ == "__main__":
    unittest.main()
