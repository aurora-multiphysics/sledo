"""
Optimiser class for SLEDO.

(c) Copyright UKAEA 2023-2024.
"""

import os
from pathlib import Path
import dill

from ray import train, tune
from ray.tune.search import Searcher
from ray.tune.result_grid import ResultGrid

from sledo.design_evaluator import DesignEvaluator


class Optimiser:
    """The SLEDO optimiser class."""

    def __init__(
        self,
        design_evaluator: DesignEvaluator,
        search_alg: Searcher,
        search_space: dict,
        max_total_trials: int,
        max_concurrent_trials: int = 1,
        mode: str = "min",
        name: str = None,
        data_dir: str | Path = None,
    ) -> None:
        """Initialise class instance.

        Parameters
        ----------
        design_evaluator : DesignEvaluator
            The DesignEvaluator subclass used to evaluate each design.
        search_alg : Searcher
            The search algorithm to use. Must be an instance of a subclass of
            the Ray Tune Searcher base class.
        search_space : dict
            The search space for the optimisation, values must be set according
            to the Ray Tune Search Space API.
        max_total_trials : int
            The maximum number of total trials to run.
        max_concurrent_trials : int, optional
            The maximum number of concurrent trials, by default 1 (i.e.
            trials are sequential).
        mode : str
            Must be "min" or "max". Sets whether the optimisation metric is
            minimised or maximised, by default "min".
        name : str
            The name of the optimiser, will be passed to the Ray Tune tuner. By
            default, None, in which case a name is constructed by concatenating
            the metric names found in design_evaluator.
        data_dir : str | Path, optional
            Path to the data directory to store outputs, by default None (in
            which case a subdirectory is made in the current working directory
            with a name set by the name arg of this class).
        """
        self.design_evaluator = design_evaluator
        self.search_space = search_space

        # Get metrics from design evaluator.
        if len(design_evaluator.metrics) == 1:
            self.metrics = design_evaluator.metrics
        else:
            raise ValueError(
                """Multi-objective optimisation not yet implemented."""
            )

        # Set search algorithm and limit maximum number of concurrent trials.
        self.search_alg = tune.search.ConcurrencyLimiter(
            search_alg, max_concurrent=max_concurrent_trials
        )

        # Set name, construct from metrics if not passed.
        if name:
            self.name = name
        else:
            self.name = "_".join(self.metrics) + "_optimiser"

        # Set data directory and create the directory if it doesn't exist yet.
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(f"./{self.name}")
        if not self.data_dir.exists():
            self.data_dir.mkdir()

        # Workaround to a bug which causes ray to save to both the passed
        # storage directory and the default (~/ray-results).
        os.environ['TUNE_RESULT_DIR'] = str(self.data_dir)

        # Instantiate ray tune Tuner object.
        self.tuner = tune.Tuner(
            self.trial,
            tune_config=tune.TuneConfig(
                mode=mode,
                metric=self.metrics[0],
                search_alg=self.search_alg,
                num_samples=max_total_trials,
            ),
            run_config=train.RunConfig(
                storage_path=self.data_dir,
                name=self.name,
                log_to_file=True,
            ),
            param_space=search_space,
        )

    def trial(self, parameters: dict):
        """Trial evaluation function to be passed to the tuner object.

        Calls the evaluate_design method of the passed DesignEvaluator subclass
        with the parameters for a given trial and reports the result to
        the optimiser via train.report().

        Note: users should not need to call this method directly.

        Parameters
        ----------
        parameters : dict
            Dictionary of parameters describing the design to be evaluated.
        """
        train.report(self.design_evaluator.evaluate_design(parameters))

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
