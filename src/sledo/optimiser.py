"""
Optimiser classes for SLEDO.

Handles Bayesian Optimisation.

(c) Copyright UKAEA 2023.
"""
import ax.service.ax_client
import pathlib
import dill


class Optimiser:
    """The SLEDO optimiser base class."""

    def __init__(
        self,
        name: str,
        search_space: dict,
        trainable,
        search_algorithm,
        scheduler,
        evaluation_function,
        data_dir: str | pathlib.Path = None,
    ) -> None:
        """Initialise class instance.

        Parameters
        ----------
        name : str
            The name of the instance.
        search_space : dict
            The search space for the optimisation, values must be set according
            to the Ray Tune Search Space API.
        data_dir : str | pathlib.Path
            Path to the data directory to store outputs.
        """
        self.name = name
        self.search_space = search_space

        # Set data directory and create the directory if it doesn't exist yet.
        if data_dir:
            self.data_dir = pathlib.Path(data_dir)
        else:
            self.data_dir = pathlib.Path(f"./{self.name}")
        if not self.data_dir.exists():
            self.data_dir.mkdir()

    def run_optimisation_loop(
        self,
        objective_name="",
        force=False,
        minimise=False,
        parameter_constraints=None,
        outcome_constraints=None,
        max_iter=25,
        min_acqf=None,
    ):
        """Run the optimisation loop.

        Parameters
        ----------
        max_iter : int
            The maximum number of optimisation iterations. The optimisation
            will complete when this number of iterations is reached.
        min_acqf : float (optional, default = None)
            The minimum value of the acquisition function required to proceed
            with the optimisation loop. The optimisation will complete when
            the max of the acquisition function is below this value. If None,
            the optimisation loop will continue to max_iter regardless of the
            acquisition function values.
        """

        self.ax_client = ax.service.ax_client.AxClient()
        self.ax_client.create_experiment(
            overwrite_existing_experiment=force,
            name=self.name,
            parameters=self.search_space,
            objective_name=objective_name,
            minimize=minimise,
            parameter_constraints=parameter_constraints,
            outcome_constraints=outcome_constraints,
        )

        def evaluate(filename, parameters):
            self.generate_modified_file(filename, parameters)
            sim = self.simulation_class(filename, self.data_dir)
            sim.run_sim()
            result_dict = sim.get_results()
            return result_dict

        for i in range(max_iter):
            filename = f"trial_{i}"
            parameters, trial_index = self.ax_client.get_next_trial()
            self.ax_client.complete_trial(
                trial_index=trial_index,
                raw_data=evaluate(filename, parameters),
            )

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
