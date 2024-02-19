"""
DesignEvaluator abstract base class for SLEDO.

(c) Copyright UKAEA 2024.
"""

from abc import ABC, abstractmethod


class DesignEvaluator(ABC):
    """Abstract base class for evaluating a design. Must contain a method which
    takes in the parameters describing a design and returns the
    performance metrics for that design. Additional methods may be implemented
    by a given subclass to perform the design evaluation procedure as required.
    """

    @abstractmethod
    def evaluate_design(self, parameters: dict) -> dict:
        """Evaluate a design and return performance metrics.

        Parameters
        ----------
        parameters : dict
            Dictionary of parameters describing the design to be evaluated.

        Returns
        -------
        dict
            Dictionary of metrics describing the design's performance as
            evaluated.
        """
