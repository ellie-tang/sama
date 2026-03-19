import unittest

from text_training.config import PromptConfig
from text_training.schema import ASRHypothesis, TrainingExample
from text_training.tokenization import collate_causal_lm_batch, tokenize_supervised_example


class FakeTokenizer:
    def __init__(self) -> None:
        self.pad_token_id = 0
        self.eos_token_id = 1
        self.pad_token = "<pad>"
        self.eos_token = "<eos>"

    def __call__(self, text, **kwargs):
        tokens = [index + 2 for index, _ in enumerate(text.split())]
        return {"input_ids": tokens}


class TokenizationTests(unittest.TestCase):
    def test_tokenize_supervised_example_masks_prompt_tokens(self) -> None:
        tokenizer = FakeTokenizer()
        example = TrainingExample(
            utterance_id="utt-1",
            nbest_hypotheses=[ASRHypothesis(text="hello world", rank=1)],
            reference_transcript="hello world",
        )

        feature = tokenize_supervised_example(
            example=example,
            prompt_config=PromptConfig(),
            tokenizer=tokenizer,
            max_length=128,
        )
        prompt_token_count = feature["prompt_token_count"]
        self.assertTrue(all(label == -100 for label in feature["labels"][:prompt_token_count]))
        self.assertTrue(any(label != -100 for label in feature["labels"][prompt_token_count:]))

    def test_collate_batch_pads_sequences(self) -> None:
        batch = collate_causal_lm_batch(
            [
                {"utterance_id": "a", "input_ids": [1, 2], "attention_mask": [1, 1], "labels": [-100, 2]},
                {"utterance_id": "b", "input_ids": [1], "attention_mask": [1], "labels": [-100]},
            ],
            pad_token_id=0,
        )
        input_ids = batch["input_ids"]
        if hasattr(input_ids, "shape"):
            self.assertEqual(tuple(input_ids.shape), (2, 2))
        else:
            self.assertEqual(input_ids, [[1, 2], [1, 0]])


if __name__ == "__main__":
    unittest.main()
