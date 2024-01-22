"""
Optimiser base class for SLEDO.

(c) Copyright UKAEA 2023-2024.
"""

import dill
import pathlib
from ray import train, tune
from ray.tune.result_grid import ResultGrid


class Optimiser:
    """The SLEDO optimiser class."""

    def __init__(
        self,
        name: str,
        evaluation_function: callable,
        search_space: dict,
        metric: str,
        search_alg: type(tune.search.Searcher),
        max_total_trials: int,
        max_concurrent_trials: int = 1,
        data_dir: str | pathlib.Path = None,
    ) -> None:
        """Initialise class instance.

        Parameters
        ----------
        name (str):
            The name of the instance.
        evaluation_function (callable):
            The function used to evaluate each design iteration. Must accept a
            dict of parameters and their values for a given design and return
            a dict of metrics for that design.
        search_space (dict):
            The search space for the optimisation, values must be set according
            to the Ray Tune Search Space API.
        metric (str):
            The metric of interest, must match one of the keys used in the
            output of the evaluation function.
        search_alg (tune.search.Searcher):
            The search algorithm to use, must be an instance of a subclass of
            the Ray Tune Searcher base class.
        max_total_trials(int):
            The maximum number of total trials to run.
        max_concurrent_trials (int, optional):
            The maximum number of concurrent trials. Defaults to 1, in which
            case the optimisation is entirely sequential.
        data_dir (str | pathlib.Path):
            Path to the data directory to store outputs. Defaults to None, in
            which case a subdirectory is made in the current working directory
            with a name set by the name arg of this class.
        """
        self.name = name

        # Add tune report step to output of design evaluation function.
        self.evaluation_function = lambda x: train.report(
            evaluation_function(x)
        )

        self.search_space = search_space

        # Set search algorithm and limit maximum number of concurrent trials.
        self.search_alg = tune.search.ConcurrencyLimiter(
            search_alg, max_concurrent=max_concurrent_trials
        )

        # Set data directory and create the directory if it doesn't exist yet.
        if data_dir:
            self.data_dir = pathlib.Path(data_dir)
        else:
            self.data_dir = pathlib.Path(f"./{self.name}")
        if not self.data_dir.exists():
            self.data_dir.mkdir()

        # Instantiate Tuner object.
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
        """Run the optimisation loop.

        Returns
        -------
        results (ResultGrid):
            Ray tune ResultGrid instance containing the results of the
            optimisation.
        """
        self.results = self.tuner.fit()
        return self.results

    def get_results(self) -> ResultGrid:
        """Get results of a previous optimisation.

        Returns
        -------
        results (ResultGrid):
            Ray tune ResultGrid instance containing the results of the
            optimisation.
        """
        self.results = self.tuner.get_results()
        return self.results


    def pickle(self, filepath=None):
        """Save instance to file."""
        if not filepath:
            filepath = self.data_dir / f"{self.name}.pickle"
        with open(filepath, "wb") as file:
            dill.dump(self, file)

    @classmethod
    def unpickle(cls, filepath):
        """Load instance from file."""
        with open(filepath, "rb") as f:
            obj = dill.load(f)
        if isinstance(obj, cls):
            return obj
        raise TypeError(
            f"Unpickled object is not an instance of {cls.__name__}."
        )
