"""
Tests for the SLEDO DesignEvaluator abstract base class and its subclasses.

(c) Copyright UKAEA 2024.
"""
import pytest

from sledo.design_evaluator import (
    TestFunctionDesignEvaluator,
    MooseHerderDesignEvaluator,
)
from sledo.paths import SLEDO_ROOT

TEST_INPUT_FILE = SLEDO_ROOT / "tests" / "test_data" / "input.i"


@pytest.fixture(scope="session")
def tmp_data_dir(tmp_path_factory):
    tmp_data_dir = tmp_path_factory.mktemp("tmp_data_dir")
    return tmp_data_dir


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


class TestMooseHerderDesignEvaluator:
    """Tests for MooseHerderDesignEvaluator."""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_data_dir):
        metrics = ["temperature"]
        self.design_evaluator = MooseHerderDesignEvaluator(
            metrics,
            base_input_file=TEST_INPUT_FILE,
            working_dir=tmp_data_dir,
        )

    def test_has_required_methods(self):
        assert hasattr(self.design_evaluator, "metrics")
        assert hasattr(self.design_evaluator, "evaluate_design")

    def test_evaluate_design(self):
        pass
