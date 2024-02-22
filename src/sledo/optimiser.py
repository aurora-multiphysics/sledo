"""
Optimiser base class for SLEDO.

(c) Copyright UKAEA 2023-2024.
"""

from pathlib import Path
import dill

from ray import train, tune
from ray.tune.search import Searcher
from ray.tune.search.ax import AxSearch
from ray.tune.result_grid import ResultGrid

from sledo.design_evaluator import DesignEvaluator


class Optimiser:
    """The SLEDO optimiser class."""

    def __init__(
        self,
        name: str,
        design_evaluator: DesignEvaluator,
        search_space: dict,
        metric: str,
        max_total_trials: int,
        max_concurrent_trials: int = 1,
        search_alg: Searcher = AxSearch(),
        data_dir: str | Path = None,
    ) -> None:
        """Initialise class instance.

        Parameters
        ----------
        name : str
            The name of the instance.
        design_evaluator : DesignEvaluator
            The DesignEvaluator subclass used to evaluate each design.
        search_space : dict
            The search space for the optimisation, values must be set according
            to the Ray Tune Search Space API.
        max_total_trials : int
            The maximum number of total trials to run.
        max_concurrent_trials : int, optional
            The maximum number of concurrent trials, by default 1 (i.e.
            trials are sequential).
        search_alg : Searcher, optional
            The search algorithm to use, by default AxSearch(). Must be an
            instance of a subclass of the Ray Tune Searcher base class.
        data_dir : str | Path, optional
            Path to the data directory to store outputs, by default None (in
            which case a subdirectory is made in the current working directory
            with a name set by the name arg of this class).
        """
        self.name = name
        self.design_evaluator = design_evaluator
        self.search_space = search_space

        # Get metrics from design evaluator.
        self.metrics = design_evaluator.metrics

        # Set search algorithm and limit maximum number of concurrent trials.
        self.search_alg = tune.search.ConcurrencyLimiter(
            search_alg, max_concurrent=max_concurrent_trials
        )

        # Set data directory and create the directory if it doesn't exist yet.
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(f"./{self.name}")
        if not self.data_dir.exists():
            self.data_dir.mkdir()

        # Add a step to the evaluation function reporting the results of each
        # design evaluation to the ray tune optimiser.
        self.evaluation_function = lambda results_dict: train.report(
            self.design_evaluator.evaluate_design(results_dict)
        )

        # Instantiate ray tune Tuner object.
        self.tuner = tune.Tuner(
            self.evaluation_function,
            tune_config=tune.TuneConfig(
                mode="min",
                metric=metric,
                search_alg=self.search_alg,
                num_samples=max_total_trials,
            ),
            run_config=train.RunConfig(
                name=self.name,
            ),
            param_space=search_space,
        )

    def run_optimisation(self) -> ResultGrid:
        """Run the optimisation loop and return the results.

        Returns
        -------
        results : ResultGrid
            Ray tune ResultGrid instance containing the results of the
            optimisation.
        """
        self.results = self.tuner.fit()
        return self.results

    def get_results(self) -> ResultGrid:
        """Get results of the optimisation.

        Returns
        -------
        results : ResultGrid
            Ray tune ResultGrid instance containing the results of the
            optimisation.
        """
        self.results = self.tuner.get_results()
        return self.results

    def pickle(self, filepath=None):
        """Save class instance to file."""
        if not filepath:
            filepath = self.data_dir / f"{self.name}.pickle"
        with open(filepath, "wb") as file:
            dill.dump(self, file)

    @classmethod
    def unpickle(cls, filepath):
        """Load class instance from file."""
        with open(filepath, "rb") as f:
            obj = dill.load(f)
        if isinstance(obj, cls):
            return obj
        raise TypeError(
            f"Unpickled object is not an instance of {cls.__name__}."
        )
