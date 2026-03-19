import unittest

from text_training.config import PromptConfig
from text_training.prompting.templates import build_training_prompt
from text_training.schema import ASRHypothesis, TrainingExample, VisionContext


class PromptTemplateTests(unittest.TestCase):
    def test_build_training_prompt_includes_hypotheses_and_context(self) -> None:
        config = PromptConfig()
        example = TrainingExample(
            utterance_id="utt-1",
            nbest_hypotheses=[
                ASRHypothesis(text="turn on the light", score=0.9),
                ASRHypothesis(text="turn on delight", score=0.7),
            ],
            visual_context=VisionContext(text="A lamp is visible on a bedside table."),
            reference_transcript="turn on the light",
        )

        prompt = build_training_prompt(example, config)
        self.assertIn("### N-best hypotheses", prompt)
        self.assertIn("turn on the light", prompt)
        self.assertIn("A lamp is visible on a bedside table.", prompt)
        self.assertIn(config.answer_prefix, prompt)


if __name__ == "__main__":
    unittest.main()
