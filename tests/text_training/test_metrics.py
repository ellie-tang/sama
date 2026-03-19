import unittest

from text_training.eval.metrics import compare_against_top1_baseline, compute_cer, compute_exact_match, compute_wer


class MetricsTests(unittest.TestCase):
    def test_wer_and_cer_are_zero_on_exact_match(self) -> None:
        predictions = ["hello world"]
        references = ["hello world"]
        self.assertEqual(compute_wer(predictions, references), 0.0)
        self.assertEqual(compute_cer(predictions, references), 0.0)
        self.assertEqual(compute_exact_match(predictions, references), 1.0)

    def test_compare_against_top1_baseline_reports_improvement(self) -> None:
        baseline = ["turn on delight"]
        regenerated = ["turn on the light"]
        references = ["turn on the light"]
        metrics = compare_against_top1_baseline(baseline, regenerated, references)
        self.assertGreater(metrics["baseline_wer"], metrics["regenerated_wer"])


if __name__ == "__main__":
    unittest.main()
