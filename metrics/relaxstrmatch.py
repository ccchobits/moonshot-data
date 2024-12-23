import re
from pathlib import Path
from typing import Any

from moonshot.src.metrics.metric_interface import MetricInterface
from moonshot.src.utils.timeit import timeit


class RelaxStrMatch(MetricInterface):
    """
    RelaxStrMatch will remove symbols and spaces before comparing the output from language model with the expected
    target.
    """

    def __init__(self):
        self.id = Path(__file__).stem
        self.name = "RelaxStrMatch"
        self.description = (
            "RelaxStrMatch will remove symbols and spaces before comparing the output from language "
            "model with the expected target."
        )
        self.metric_config = self.get_metrics_configuration(self.id)
        self.endpoints = self.metric_config.get("endpoints", [])
        self.configurations = self.metric_config.get("configurations", {})

    def get_metadata(self) -> dict | None:
        """
        Retrieves and returns the metadata of the RelaxStrMatch class.

        Returns:
            dict | None: A dictionary containing the 'id', 'name', 'description', 'endpoints' and 'configurations'
            of the RelaxStrMatch class, or None if not applicable.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "endpoints": self.endpoints,
            "configurations": self.configurations,
        }

    @timeit
    async def get_results(
        self, prompts: Any, predicted_results: Any, targets: Any, *args, **kwargs
    ) -> dict:
        """
        Calculates the accuracy of the predicted results by comparing them to the target results.

        Args:
            prompts (Any): The prompts used for prediction.
            predicted_results (Any): The predicted results.
            targets (Any): The target results.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing the accuracy of the predicted results.
        """
        predicted_values = [result.response for result in predicted_results]

        correct = 0
        total = len(predicted_values)

        for result, target in zip(predicted_values, targets):
            # remove symbols and space
            result = re.sub(r"[^\w]", "", str(result).rstrip()).replace(" ", "")
            result = result.lower()

            # To support benchmarks with multiple possible answers
            if type(target) is list:
                for each_item in target:
                    each_item = re.sub(r"[^\w]", "", str(each_item).rstrip()).replace(
                        " ", ""
                    )
                    each_item = each_item.lower()

                    if result == each_item:
                        correct += 1
                        break
            else:
                target = re.sub(r"[^\w\s]", "", str(target).rstrip()).replace(" ", "")
                target = target.lower()

                if result == target:
                    correct += 1

        return {
            "relax_str_match": float(correct / total) * 100,
            "grading_criteria": {"relax_str_match": float(correct / total) * 100},
        }
