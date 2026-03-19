import unittest

from text_training.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_builds_nested_dataclasses(self) -> None:
        config = load_config("src/text-training/configs/example_config.json")
        self.assertEqual(config.model.base_model_name, "REPLACE_WITH_QWEN3_5_9B_MODEL_ID")
        self.assertEqual(config.data.top_k_hypotheses, 5)
        self.assertEqual(config.lora.target_modules[0], "k_proj")


if __name__ == "__main__":
    unittest.main()
