"""
DesignEvaluator abstract base class for SLEDO.

(c) Copyright UKAEA 2024.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from mooseherder import (
    MooseConfig,
    InputModifier,
    MooseRunner,
    ExodusReader,
    SimData,
)

from sledo.paths import MOOSE_CONFIG_FILE


class DesignEvaluator(ABC):
    """Abstract base class for evaluating a design. Must contain a method which
    takes in the parameters describing a design and returns the performance
    metrics for that design. Additional methods may be implemented by a given
    subclass to perform the design evaluation procedure as required.
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

    @property
    @abstractmethod
    def metrics(self):
        """List of metric names.

        List of metrics by which a given design's performance is evaluated.
        These names must match the keys of the dictionary returned by the
        evaluate_design method.
        """


class TestFunctionDesignEvaluator(DesignEvaluator):
    """DesignEvaluator subclass which evaluates a test function."""

    def __init__(self, test_function: str = "three_hump_camel") -> None:
        self.test_function = getattr(self, test_function)
        metrics_dict = {
            "three_hump_camel": "y1"
        }
        self.metrics = metrics_dict[test_function]

    def three_hump_camel(x1, x2):
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
    """DesignEvaluator subclass which evaluates a design via MooseHerder."""

    def __init__(
        self,
        metrics: list[str],
        base_input_file: Path | str,
        working_dir: Path | str = Path.cwd(),
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
            MOOSE simulation global variables so they can be read successfully.
        base_input_file : Path | str
            Path to the base MOOSE input file (.i) to use as the basis for
            generating modified files. This file will not be modified.
        working_dir : Path | str, optional
            Path to the working directory to use for storing modified MOOSE
            input files (.i) and running MOOSE, by default Path.cwd().
        config_path : Path | str, optional
            Path to the config file containing the required paths to run MOOSE,
            by default 'moose_config.json' in the sledo root folder.
        run_options : dict, optional
            Dict of options for running the simulation, by default
            { "n_tasks": 1, "n_threads": 4, "redirect_out": False }.
        """
        self.metrics = metrics
        self.base_input_file = Path(base_input_file)
        self.working_dir = Path(working_dir)
        self.moose_config = MooseConfig().read_config(config_path)
        self.run_options = run_options

    def generate_modified_input_file(
        self,
        parameters: dict,
    ) -> Path:
        """Generate a modified MOOSE input file (.i) with specified parameters.
        Generated file will use the filename "trial.i".

        Parameters
        ----------
        parameters : dict
            Dictionary of parameters to use in the modified file. Keys must
            match top-level parameters in the input file.

        Returns
        -------
        Path
            Path to the generated input file for the given trial.
        """
        moose_mod = InputModifier(
            str(self.base_input_file), comment_char="#", end_char=""
        )
        moose_mod.update_vars(parameters)
        new_input_file = self.working_dir / "trial.i"
        moose_mod.write_file(new_input_file)

        return new_input_file

    def run_simulation(
        self,
        input_filepath: Path | str,
        run_options: dict = None,
    ) -> None:
        """Run a MOOSE simulation.

        Parameters
        ----------
        input_filepath : Path | str
            Path to the moose input file (.i) to run.
        run_options : dict, optional
            Dictionary of options for running the simulation, overrides those
            set during __init__, by default None.
        """
        moose_runner = MooseRunner(self.moose_config)
        moose_runner.set_input_file(Path(input_filepath))
        if not run_options:
            run_options = self.run_options
        moose_runner.set_run_opts(**run_options)
        moose_runner.run()

    def read_exodus(self, filepath: Path | str = None) -> SimData:
        """Read the simulation results from exodus file.

        Parameters
        ----------
        filepath : Path | str, optional
            Path to the exodus file to read, by default "trial_out.e" in the
            set working directory (self.working_dir) is used.

        Returns
        -------
        SimData
            SimData object containing the simulation results read from file.
        """
        if not filepath:
            filepath = self.working_dir / "trial_out.e"
        exodus_reader = ExodusReader(filepath)
        simdata = exodus_reader.read_all_sim_data()

        return simdata

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
        trial_filepath = self.generate_modified_input_file(parameters)
        self.run_simulation(trial_filepath)
        simdata = self.read_exodus()

        metrics_dict = {}
        for metric in self.metrics:
            metrics_dict[metric] = simdata.glob_vars[metric][timestep]

        return metrics_dict
