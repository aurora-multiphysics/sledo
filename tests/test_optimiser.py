"""
Tests for the SLEDO Optimiser class.

(c) Copyright UKAEA 2023-2024.
"""

import pytest

from sledo.optimiser import Optimiser
from sledo.design_evaluator import TestFunctionDesignEvaluator

from ray import tune
from ray.tune.result_grid import ResultGrid
from ray.tune.search import ConcurrencyLimiter

NAME = "three_hump_camel_optimiser"
DESIGN_EVALUATOR = TestFunctionDesignEvaluator(
    test_function="three_hump_camel"
)
SEARCH_SPACE = {
    "x1": tune.uniform(-5.0, +5.0),
    "x2": tune.uniform(-5.0, +5.0),
}


@pytest.fixture(scope="session")
def tmp_data_dir(tmp_path_factory):
    tmp_data_dir = tmp_path_factory.mktemp("tmp_data_dir")
    return tmp_data_dir


class TestOptimiser:
    """
    Tests for the SLEDO Optimiser class.
    """

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_data_dir):
        self.opt = Optimiser(
            NAME,
            DESIGN_EVALUATOR,
            SEARCH_SPACE,
            max_total_trials=5,
            data_dir=tmp_data_dir,
        )

    def test_init(self):
        """Test Optimiser class initiates correctly."""
        assert self.opt.name == NAME
        assert self.opt.design_evaluator == DESIGN_EVALUATOR
        assert self.opt.search_space == SEARCH_SPACE
        assert isinstance(self.opt.search_alg, ConcurrencyLimiter)
        assert self.opt.data_dir.is_dir()
        assert isinstance(self.opt.tuner, tune.Tuner)

    def test_run_optimisation(self):
        """Test that the run_optimisation method returns results."""
        results = self.opt.run_optimisation()
        assert isinstance(results, ResultGrid)

    def test_get_results(self):
        """Tests that the get_results method returns existing results."""
        self.opt.run_optimisation()
        results = self.opt.get_results()
        assert isinstance(results, ResultGrid)

    def test_get_results_without_results(self):
        """Tests that get_results raises error when there are no results."""
        with pytest.raises(RuntimeError):
            self.opt.get_results()
