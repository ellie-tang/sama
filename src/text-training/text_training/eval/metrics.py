from __future__ import annotations


def _levenshtein_distance(source: list[str], target: list[str]) -> int:
    if not source:
        return len(target)
    if not target:
        return len(source)

    previous = list(range(len(target) + 1))
    for i, source_item in enumerate(source, start=1):
        current = [i]
        for j, target_item in enumerate(target, start=1):
            cost = 0 if source_item == target_item else 1
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + cost,
                )
            )
        previous = current
    return previous[-1]


def compute_wer(predictions: list[str], references: list[str]) -> float:
    if len(predictions) != len(references):
        raise ValueError("predictions and references must have the same length")
    total_words = 0
    total_edits = 0
    for prediction, reference in zip(predictions, references):
        prediction_words = prediction.split()
        reference_words = reference.split()
        total_words += len(reference_words)
        total_edits += _levenshtein_distance(prediction_words, reference_words)
    return total_edits / total_words if total_words else 0.0


def compute_cer(predictions: list[str], references: list[str]) -> float:
    if len(predictions) != len(references):
        raise ValueError("predictions and references must have the same length")
    total_chars = 0
    total_edits = 0
    for prediction, reference in zip(predictions, references):
        prediction_chars = list(prediction)
        reference_chars = list(reference)
        total_chars += len(reference_chars)
        total_edits += _levenshtein_distance(prediction_chars, reference_chars)
    return total_edits / total_chars if total_chars else 0.0


def compute_exact_match(predictions: list[str], references: list[str]) -> float:
    if len(predictions) != len(references):
        raise ValueError("predictions and references must have the same length")
    if not references:
        return 0.0
    matches = sum(int(prediction == reference) for prediction, reference in zip(predictions, references))
    return matches / len(references)


def compare_against_top1_baseline(
    nbest_top1: list[str],
    regenerated: list[str],
    references: list[str],
) -> dict[str, float]:
    baseline_wer = compute_wer(nbest_top1, references)
    regenerated_wer = compute_wer(regenerated, references)
    baseline_cer = compute_cer(nbest_top1, references)
    regenerated_cer = compute_cer(regenerated, references)

    wer_reduction = 0.0
    cer_reduction = 0.0
    if baseline_wer > 0:
        wer_reduction = (baseline_wer - regenerated_wer) / baseline_wer
    if baseline_cer > 0:
        cer_reduction = (baseline_cer - regenerated_cer) / baseline_cer

    return {
        "baseline_wer": baseline_wer,
        "regenerated_wer": regenerated_wer,
        "baseline_cer": baseline_cer,
        "regenerated_cer": regenerated_cer,
        "wer_relative_reduction": wer_reduction,
        "cer_relative_reduction": cer_reduction,
        "exact_match": compute_exact_match(regenerated, references),
    }
