"""
SLEDO DesignEvaluator abstract base class and library of subclasses.

Each subclass implements a specific design evaluation procedure.

(c) Copyright UKAEA 2024.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from catbird import MooseModel
from sledo.mooseherder_functions import (
    generate_modified_input_file,
    run_simulation,
    read_exodus,
)
from sledo.paths import MOOSE_CONFIG_FILE


class DesignEvaluator(ABC):
    """Abstract base class for evaluating a design. Must contain a method which
    takes in the parameters describing a design and returns the performance
    metrics for that design. Additional methods may be implemented by a given
    subclass to perform the design evaluation procedure as required.
    """

    @property
    @abstractmethod
    def metrics(self) -> list[str]:
        """Property: the list of metric names.

        List of metrics by which a given design's performance is evaluated.
        These names must match the keys of the dictionary returned by the
        evaluate_design method.
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


class TestFunctionDesignEvaluator(DesignEvaluator):
    """DesignEvaluator subclass which evaluates a test function."""

    def __init__(self, test_function: str = "three_hump_camel") -> None:
        self.test_function = getattr(self, test_function)
        metrics_dict = {
            "three_hump_camel": ["y1"]
        }
        self._metrics = metrics_dict[test_function]

    @property
    def metrics(self):
        return self._metrics

    def three_hump_camel(self, parameters: dict) -> dict:
        """Three-dimensional test function with three local minima.

        The single global minimum is at the origin.

        Parameters
        ----------
        parameters : dict[str, float | int]
            Dictionary of input parameters, must contain keys "x1" and "x2".

        Returns
        -------
        dict
            Dictionary of output metrics, contains a single key "y1".
        """
        x1, x2 = parameters["x1"], parameters["x2"]
        result = (
            (2 * x1**2)
            - (1.05 * x1**4)
            + (x1**6 / 6)
            + (x1 * x2)
            + (x2**2)
        )
        return {"y1": result}

    def evaluate_design(self, parameters: dict) -> dict:
        return self.test_function(parameters)


class MooseHerderDesignEvaluator(DesignEvaluator):
    """DesignEvaluator implemented with MooseHerder.

    This design evaluator requires a base input file to be modified per design
    iteration. It generates a modified input file in the working directory,
    runs a MOOSE simulation, and reads the appropriate output file(s).
    """

    def __init__(
        self,
        metrics: list[str],
        base_input_file: Path | str,
        config_path: Path | str = MOOSE_CONFIG_FILE,
        run_options: dict = {
            "n_tasks": 1,
            "n_threads": 4,
            "redirect_out": False,
        },
    ) -> None:
        """Initialise class instance with the metrics to output, the required
        paths, and the simulation run options.

        Parameters
        ----------
        metrics : list[str]
            List of metric names by which a given design's performance is
            evaluated. These names must exactly match how they appear in the
            MOOSE simulation postprocessors so they can be read successfully.
        base_input_file : Path | str
            Path to the base MOOSE input file (.i) to use as the basis for
            generating modified files. This file will not be modified.
        config_path : Path | str, optional
            Path to the config file containing the required paths to run MOOSE,
            by default 'moose_config.json' in the sledo root folder.
        run_options : dict, optional
            Dict of options for running the simulation, by default
            { "n_tasks": 1, "n_threads": 4, "redirect_out": False }.
        """
        self._metrics = metrics
        self.base_input_file = Path(base_input_file)
        self.config_path = Path(config_path)
        self.run_options = run_options

    @property
    def metrics(self):
        return self._metrics

    def evaluate_design(self, parameters: dict, timestep: int = -1) -> dict:
        """Evaluate a design and return performance metrics.

        Parameters
        ----------
        parameters : dict
            Dictionary of parameters describing the design to be evaluated.
            Keys must match top-level parameters in the MOOSE input file.
        timestep : int, optional
            The timestep of the simulation from which to read performance
            metrics, by default -1 (i.e. the final timestep will be read, in
            the case of steady-state solutions the solved model will be read).

        Returns
        -------
        metrics_dict : dict
            Dictionary of metrics describing the design's performance as
            evaluated. Key names will exactly match how they appear in the
            MOOSE simulation global variables.
        """
        # Generate input file.
        trial_filepath = generate_modified_input_file(
            self.base_input_file,
            Path.cwd() / "trial.i",
            parameters,
        )
        # Run simulation.
        result_filepath = run_simulation(
            trial_filepath,
            moose_config_file=self.config_path,
            run_options=self.run_options,
        )
        # Read simulation results and extract metrics.
        simdata = read_exodus(result_filepath)
        metrics_dict = {}
        for metric in self.metrics:
            metrics_dict[metric] = simdata.glob_vars[metric][timestep]

        return metrics_dict


class CatBirdMooseHerderDesignEvaluator(DesignEvaluator):
    """DesignEvaluator subclass implemented with CatBird and MooseHerder.

    This design evaluator generates an input file in the working directory,
    runs a MOOSE simulation, and reads the appropriate output file(s).
    """

    def __init__(
        self,
        metrics: list[str],
        model: MooseModel,
        config_path: Path | str = MOOSE_CONFIG_FILE,
        run_options: dict = {
            "n_tasks": 1,
            "n_threads": 4,
            "redirect_out": False,
        },
    ) -> None:
        """Initialise class instance with the metrics to output, the required
        paths, and the simulation run options.

        Parameters
        ----------
        metrics : list[str]
            List of metric names by which a given design's performance is
            evaluated. These names must exactly match how they appear in the
            MOOSE simulation postprocessors so they can be read successfully.
        model : MooseModel
            A catbird MooseModel capable of updating parameters and writing a
            MOOSE input file.
        config_path : Path | str, optional
            Path to the config file containing the required paths to run MOOSE,
            by default 'moose_config.json' in the sledo root folder.
        run_options : dict, optional
            Dict of options for running the simulation, by default
            { "n_tasks": 1, "n_threads": 4, "redirect_out": False }.
        """
        self._metrics = metrics
        self._model = model
        self.config_path = Path(config_path)
        self.run_options = run_options

    @property
    def metrics(self):
        return self._metrics

    def add_metric_postprocessor(
        self,
        metric: str,
        variable_name: str,
        postprocessor_type: str = "ElementExtremeValue",
        **postprocessor_kwargs,
    ):
        """Add a Postprocessor object to the MOOSE input file with a name
        matching an optimisation metric. Available postprocessors here:
        https://mooseframework.inl.gov/syntax/Postprocessors/index.html

        Parameters
        ----------
        metric : str
            Name of metric to add a postprocessor for, must match exactly the
            name of an optimisation metric so that it may be reported to the
            optimiser.
        variable_name : str
            Name of variable upon which the postprocessor will act.
        postprocessor_type : str, optional
            Type of postprocessor to use, by default "ElementExtremeValue".
        """
        if metric not in self._metrics:
            msg = (
                "Warning: Metric not found in optimisation metrics."
                "Nothing has been added."
            )
            raise ValueError(msg)
        if metric in self._model.postprocessors.objects.keys():
            msg = (
                "Warning: Postprocessor already exists for this metric."
                "Nothing has been added."
            )
            raise ValueError(msg)
        self._model.add_postprocessor(
            metric,
            postprocessor_type,
            variable_name,
            **postprocessor_kwargs,
        )

    def generate_input_file(
        self, input_filepath: Path | str, parameters: dict
    ):
        """Generate a MOOSE input file (.i) with specified parameters.

        Parameters
        ----------
        input_filepath : Path | str
            Path to input file to be generated. The .i extension will be added
            if not passed.
        parameters : dict
            Dictionary of parameters to use in the modified file. Keys must
            match top-level parameters in the input file.

        Returns
        -------
        input_filepath : Path
            Path to the generated input file for the given trial.
        """
        self._model.modify_parameters(parameters)

        # Write input file, ensuring .i extension is used.
        input_filepath = Path(input_filepath)
        if input_filepath.suffix != ".i":
            input_filepath = input_filepath.parent / Path(
                input_filepath.name + ".i"
            )
        self._model.write(input_filepath)

        return input_filepath

    def evaluate_design(self, parameters: dict, timestep: int = -1) -> dict:
        """Evaluate a design and return performance metrics.

        Parameters
        ----------
        parameters : dict
            Dictionary of parameters describing the design to be evaluated.
            Keys must match top-level parameters in the MOOSE input file.
        timestep : int, optional
            The timestep of the simulation from which to read performance
            metrics, by default -1 (i.e. the final timestep will be read, in
            the case of steady-state solutions the solved model will be read).

        Returns
        -------
        metrics_dict : dict
            Dictionary of metrics describing the design's performance as
            evaluated. Key names will exactly match how they appear in the
            MOOSE simulation global variables.
        """
        # Generate input file.
        trial_filepath = self.generate_input_file(
            Path.cwd() / "trial.i",
            parameters,
        )
        # Run simulation.
        result_filepath = run_simulation(
            trial_filepath,
            moose_config_file=self.config_path,
            run_options=self.run_options,
        )
        # Read simulation results and extract metrics.
        simdata = read_exodus(result_filepath)
        metrics_dict = {}
        for metric in self.metrics:
            metrics_dict[metric] = simdata.glob_vars[metric][timestep]

        return metrics_dict
