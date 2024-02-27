"""
Tests for the SLEDO DesignEvaluator abstract base class and its subclasses.

(c) Copyright UKAEA 2024.
"""
from sledo.design_evaluator import (
    TestFunctionDesignEvaluator,
    MooseHerderDesignEvaluator,
)

import pytest


class TestTestFunctionDesignEvaluator:
    """Tests for TestFunctionDesignEvaluator."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.design_evaluator = TestFunctionDesignEvaluator(
            test_function="three_hump_camel"
        )

    def test_has_required_methods(self):
        assert hasattr(self.design_evaluator, "metrics")
        assert hasattr(self.design_evaluator, "evaluate_design")

    def test_evaluate_design(self):
        test_parameters = {"x1": 0.0, "x2": 0.0}
        expected_result = {"y1": 0.0}
        result = self.design_evaluator.evaluate_design(test_parameters)
        assert result == expected_result

