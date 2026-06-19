import os
import json
from typing import List, Dict, Any, Tuple


class DataProcessor:
    """
    Processor for handling data preprocessing, evaluation and accuracy computation.
    """

    def answer_is_correct(self, predicted: str, ground_truth: str) -> bool:
        """
        Answer correctness check.

        Args:
            predicted: Model's answer
            ground_truth: Ground truth answer

        Returns:
            bool: True if answer is correct, False otherwise
        """
        if not predicted or not ground_truth:
            return False

        pred = predicted.strip().lower()
        truth = ground_truth.strip().lower()

        if pred == truth:
            return True

        pred_parts = [p.strip() for p in pred.split("/") if p.strip()]
        truth_parts = [t.strip() for t in truth.split("/") if t.strip()]

        for p in pred_parts:
            for t in truth_parts:
                if p == t or p in t or t in p:
                    return True

        return False

    def evaluate_accuracy(self, out: List[str], target: List[str]) -> tuple:
        """
        Accuracy evaluation.

        Args:
            out: List of model predictions
            target: List of ground truth targets

        Returns:
            tuple: (accuracy, response_list)
        """
        if len(out) != len(target):
            raise ValueError(
                "Input lists 'out' and 'target' must have the same length."
            )

        correct_count = 0

        for predicted, ground_truth in zip(out, target):
            if self.answer_is_correct(predicted, ground_truth):
                correct_count += 1

        accuracy = 0.0
        if len(out) > 0:
            accuracy = correct_count / len(out)

        return accuracy
