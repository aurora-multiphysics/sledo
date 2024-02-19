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


class DesignEvaluator(ABC):
    """Abstract base class for evaluating a design. Must contain a method which
    takes in the parameters describing a design and returns the
    performance metrics for that design. Additional methods may be implemented
    by a given subclass to perform the design evaluation procedure as required.
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


class MooseHerderDesignEvaluator(DesignEvaluator):
    """DesignEvaluator subclass implemented using MooseHerder.
    """
    def __init__(
        self,
        metrics: list[str],
        base_input_file: Path | str,
        working_dir: Path | str = Path.cwd(),
        config_path: Path | str = Path.cwd() / 'moose_config.json',
        run_options: dict = {
            "n_tasks": 1,
            "n_threads": 4,
            "redirect_out": False
        }
    ) -> None:
        """_summary_

        Parameters
        ----------
        metrics : list[str]
            _description_
        base_input_file : Path | str
            _description_
        working_dir : Path | str, optional
            _description_, by default Path.cwd()
        config_path : Path | str, optional
            _description_, by default Path.cwd()/'moose_config.json'
        run_options : _type_, optional
            _description_, by default { "n_tasks": 1, "n_threads": 4, "redirect_out": False }
        """
        self.metrics = metrics
        self.base_input_file = Path(base_input_file)
        self.working_dir = Path(working_dir)
        self.moose_config = MooseConfig().read_config(config_path)
        self.run_options - run_options

    def generate_modified_input_file(
        self, parameters: dict,
    ) -> Path:
        """_summary_

        Parameters
        ----------
        parameters : dict
            _description_

        Returns
        -------
        Path
            _description_
        """
        moose_mod = InputModifier(
            str(self.base_input_file), comment_char="#", end_char=""
        )
        moose_mod.update_vars(parameters)
        new_input_file = self.working_dir / "trial.i"
        moose_mod.write_file(new_input_file)

        return new_input_file

    def run_simulation(
        self, input_filepath: Path | str, run_options: dict = None,
    ) -> None:
        """_summary_

        Parameters
        ----------
        input_filepath : Path | str
            _description_
        run_options : dict, optional
            _description_, by default None
        """
        moose_runner = MooseRunner(self.moose_config)
        moose_runner.set_input_file(Path(input_filepath))
        if not run_options:
            run_options = self.run_options
        moose_runner.set_run_opts(**run_options)
        moose_runner.run()

    def read_exodus(self, filepath: Path | str = None) -> SimData:
        """_summary_

        Parameters
        ----------
        filepath : Path | str, optional
            _description_, by default None

        Returns
        -------
        SimData
            _description_
        """
        if not filepath:
            filepath = self.working_dir / "trial_out.e"
        exodus_reader = ExodusReader(filepath)
        simdata = exodus_reader.read_all_sim_data()

        return simdata

    def evaluate_design(self, parameters: dict) -> dict:
        """_summary_

        Parameters
        ----------
        parameters : dict
            _description_

        Returns
        -------
        dict
            _description_
        """
        trial_filepath = self.generate_modified_input_file(parameters)
        self.run_simulation(trial_filepath)
        simdata = self.read_exodus()

        metrics_dict = {}
        for metric in self.metrics:
            metrics_dict[metric] = simdata.glob_vars[metric]

        return metrics_dict
