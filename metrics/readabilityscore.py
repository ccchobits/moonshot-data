from pathlib import Path
from typing import Any

from moonshot.src.metrics.metric_interface import MetricInterface
from moonshot.src.utils.timeit import timeit
from readability import Readability


class ReadabilityScore(MetricInterface):
    def __init__(self):
        self.id = Path(__file__).stem
        self.name = "ReadabilityScore"
        self.description = "ReadabilityScore uses Flesch Reading Ease to compute the complexity of the output"
        self.metric_config = self.get_metrics_configuration(self.id)
        self.endpoints = self.metric_config.get("endpoints", [])
        self.configurations = self.metric_config.get("configurations", {})

    def get_metadata(self) -> dict | None:
        """
        Retrieves and returns the metadata of the ReadabilityScore class.

        Returns:
            dict | None: A dictionary containing the 'id', 'name', 'description', 'endpoints' and 'configurations'
            of the ReadabilityScore class, or None if not applicable.
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
        Calculates the readability score and the number of valid and invalid responses based on the predicted results.

        Args:
            prompts (Any): The prompts used for generating the predicted results.
            predicted_results (Any): The predicted results.
            targets (Any): The target results.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            dict: A dictionary containing the readability score, the number of valid responses,
            and the list of invalid responses.
        """
        predicted_values = [result.response for result in predicted_results]

        results = 0
        temp_scores = {}
        num_of_output_more_than_100 = 0
        response_less_than_100 = []

        for result in predicted_values:
            if len(result.split()) < 100:
                temp_scores[result] = -1
                response_less_than_100.append(result)
            else:
                r = Readability(result)
                this_score = r.flesch_kincaid()
                temp_scores[result] = this_score.score
                results += this_score.score
                num_of_output_more_than_100 += 1

        if num_of_output_more_than_100 > 0:
            temp_score = results / num_of_output_more_than_100
        else:
            temp_score = 0

        return {
            "readabilityscore": temp_score,
            "valid_response": len(predicted_results) - len(response_less_than_100),
            "invalid_response": response_less_than_100,
            "grading_criteria": {},
        }
