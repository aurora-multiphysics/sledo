from sledo.optimiser import Optimiser

from ray import tune
from ray.tune.search.ax import AxSearch
from ray.tune.result_grid import ResultGrid
from ray.tune.search import ConcurrencyLimiter

import pytest


def three_hump_camel(x1, x2):
    return (2 * x1**2) - (1.05 * x1**4) + (x1**6 / 6) + (x1 * x2) + (x2**2)


NAME = "three_hump_camel_optimiser"
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
            lambda X: {"y": three_hump_camel(X["x1"], X["x2"])},
            SEARCH_SPACE,
            "y",
            AxSearch(),
            5,
            data_dir=tmp_data_dir,
        )

    def test_init(self):
        """Test Optimiser class initiates correctly."""
        assert self.opt.name == NAME
        assert self.opt.search_space == SEARCH_SPACE
        assert isinstance(self.opt.search_alg, ConcurrencyLimiter)
        assert self.opt.data_dir.is_dir()
        assert isinstance(self.opt.tuner, tune.Tuner)

    def test_run_optimisation(self):
        """Test that the run_optimisation method returns results.
        """
        results = self.opt.run_optimisation()
        assert isinstance(results, ResultGrid)

    def test_get_results(self):
        """Tests that the get_results method returns existing results."""
        self.opt.run_optimisation()
        results = self.opt.get_results()
        assert isinstance(results, ResultGrid)

    def test_get_results_without_results(self):
        """Tests that the get_results method returns existing results."""
        with pytest.raises(RuntimeError):
            self.opt.get_results()
