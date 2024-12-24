import re
from pathlib import Path
from typing import Any, Callable, Literal
import json
import string

from moonshot.src.metrics.metric_interface import MetricInterface
from moonshot.src.utils.timeit import timeit


class MyExactStrMatch(MetricInterface):
    def __init__(self):
        self.id = Path(__file__).stem
        self.name = "MyExactStrMatch"
        self.description = (
            "ExactStrMatch will compare the output from language model with a single target"
            " or multiple expected target."
        )
        self.metric_config = self.get_metrics_configuration(self.id)
        self.endpoints = self.metric_config.get("endpoints", [])
        self.configurations = self.metric_config.get("configurations", {})

    def get_metadata(self) -> dict | None:
        """
        Retrieves and returns the metadata of the ExactStrMatch class.

        Returns:
            dict | None: A dictionary containing the 'id', 'name', 'description', 'endpoints' and 'configurations'
            of the ExactStrMatch class, or None if not applicable.
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

        correct = 0
        wrong = 0
        total = len(predicted_results)
        results = []

        for idx, (result, target) in enumerate(zip(predicted_results, targets)):
            # Check if the target is a single or multiple targets
            result = self.extract(result.response)
            if not isinstance(target, str):
                target = str(target)
            _, matched = inspect_match_str(
                result,
                target,
                numeric=True
            )
            correct += int(matched)
            results.append(int(matched))

        return {
            "accuracy": float(correct / total) * 100,
            "results": results,
            "grading_criteria": {"accuracy": float(correct / total) * 100},
        }

    @staticmethod
    def extract(result: str) -> str:
        """
        Extracts a numerical value from a string if present.

        Args:
            result (str): The string to extract the value from.

        Returns:
            str: The extracted numerical value as a string, or 'NA' if no value is found.
        """
        matches = re.findall(r"The answer is \$?(\-?[\d,\.]+)", result)
        if len(matches) == 0:
            return 'NA'
        model_answer = matches[-1].replace(',', '')
        if model_answer[-1] == '.':
            model_answer = model_answer[:-1]
        return model_answer


def first_number_normalized(words: list[str]) -> str:
    """
    Retrieves and normalizes the first numeric word in a list of words.

    Args:
        words (list[str]): A list of words to search.

    Returns:
        str: The normalized numeric value as a string, or the first word if no numeric value is found.
    """
    number = next(
        (word for word in words if word.replace(".", "").isnumeric()), words[0]
    )
    return normalize_number(number)


def strip_punctuation(s: str) -> str:
    """
    Removes punctuation and surrounding whitespace from a string.

    Args:
        s (str): The string to clean.

    Returns:
        str: The cleaned string.
    """
    return s.strip(string.whitespace + string.punctuation)


def normalize_number(number: str, precision: int = 5) -> str:
    """
    Normalizes a number to a specified precision.

    Args:
        number (str): The number to normalize.
        precision (int, optional): The number of significant figures to keep. Defaults to 5.

    Returns:
        str: The normalized number as a string.
    """
    if number.replace(".", "").isnumeric():
        num = float(number)
        return format(num, f".{precision}g")
    else:
        return number


def strip_numeric_punctuation(s: str) -> str:
    """
    Removes numeric-related punctuation (e.g., $, €, £) and commas from a string.

    Args:
        s (str): The string to clean.

    Returns:
        str: The cleaned string.
    """
    stripped = re.sub(r"[$,£,€]", "", s)
    # strip . if it's followed by a space, the end of the string,
    # or a non-digit character
    stripped = re.sub(r"\.(?=\s|$|\D)", "", stripped)
    return stripped


def inspect_match_str(
    value: str,
    target: str,
    location: Literal["begin", "end", "any", "exact"] = "end",
    ignore_case: bool = True,
    ignore_punctuation: bool = True,
    numeric: bool = False,
) -> tuple[str, bool]:
    """
    Compares a value and a target string with various matching criteria.

    Args:
        value (str): The value to compare.
        target (str): The target string.
        location (Literal["begin", "end", "any", "exact"], optional): The match location criteria. Defaults to "end".
        ignore_case (bool, optional): Whether to ignore case in the comparison. Defaults to True.
        ignore_punctuation (bool, optional): Whether to ignore punctuation in the comparison. Defaults to True.
        numeric (bool, optional): Whether to treat the strings as numeric values. Defaults to False.

    Returns:
        tuple[str, bool]: A tuple containing the processed value and a boolean indicating whether the match criteria are met.
    """

    v = value.strip()
    t = target.strip()

    # baseline answer (will only change for numeric)
    answer = v

    # further cleanup
    if ignore_case:
        v = v.casefold()
        t = t.casefold()
    if numeric:
        # remove punctuation
        v = strip_numeric_punctuation(v)
        t = strip_numeric_punctuation(t)
        # normalize as required
        t = normalize_number(t)
        if location == "begin":
            words = v.split(" ")
            v = first_number_normalized(words)
        elif location == "end":
            words = v.split(" ")
            words.reverse()
            v = first_number_normalized(words)
        elif location == "exact":
            v = normalize_number(v)
        answer = v
    elif ignore_punctuation:
        v = strip_punctuation(v)
        t = strip_punctuation(t)

    # comparisons
    if location == "begin":
        return answer, v.startswith(t)
    elif location == "end":
        return answer, v.endswith(t)
    elif location == "exact":
        return answer, v == t
    else:
        return answer, t in v