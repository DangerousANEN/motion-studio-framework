"""MSF Base Agent Framework.

Provides BaseAgent abstract class defining the contract for all MSF production agents
with validation gates and auto-retry execution loops.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from msf.agents.llm_client import LLMClient
from msf.config import MSFConfig
from msf.contracts.models import ReviewResult, ReviewVerdict
from msf.utils.logger import StageLogger

InT = TypeVar("InT")
OutT = TypeVar("OutT")


class BaseAgent(ABC, Generic[InT, OutT]):
    """Abstract base class for domain agents in MSF pipeline."""

    def __init__(self, config: MSFConfig, logger: StageLogger | logging.Logger):
        self.config = config
        self.logger = logger
        self.llm = LLMClient(config.llm)

    @abstractmethod
    def execute(self, input_data: InT) -> OutT:
        """Execute agent core logic on input_data to produce output_data."""
        pass

    @abstractmethod
    def validate(self, output_data: OutT) -> ReviewResult:
        """Validate agent output against domain constraints to produce a ReviewResult."""
        pass

    def run(self, input_data: InT, max_attempts: int = 3) -> OutT:
        """Execute agent workflow with validation and retry loop up to max_attempts.

        Args:
            input_data: Domain input data for the agent.
            max_attempts: Maximum execution + validation attempts allowed.

        Returns:
            The validated output_data.

        Raises:
            RuntimeError: If output fails validation after max_attempts.
        """
        last_review: ReviewResult | None = None
        last_output: OutT | None = None

        for attempt in range(1, max_attempts + 1):
            self.logger.info(
                f"Running agent {self.__class__.__name__} (attempt {attempt}/{max_attempts})"
            )
            try:
                output_data = self.execute(input_data)
                last_output = output_data
            except Exception as e:
                self.logger.error(
                    f"Agent {self.__class__.__name__} execution error on attempt {attempt}: {e}"
                )
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"Agent {self.__class__.__name__} failed execution on final attempt: {e}"
                    ) from e
                continue

            review = self.validate(output_data)
            review.attempt = attempt
            review.max_attempts = max_attempts
            last_review = review

            if review.verdict == ReviewVerdict.PASS:
                self.logger.info(
                    f"Agent {self.__class__.__name__} validation PASSED on attempt {attempt} (score: {review.score:.2f})"
                )
                return output_data
            else:
                self.logger.warning(
                    f"Agent {self.__class__.__name__} validation FAILED on attempt {attempt}: {review.issues}"
                )

        issues_str = "; ".join(last_review.issues) if last_review else "Unknown error"
        raise RuntimeError(
            f"Agent {self.__class__.__name__} failed quality validation after {max_attempts} attempts. Issues: {issues_str}"
        )
