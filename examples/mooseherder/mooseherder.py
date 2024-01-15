"""
SLEDO MOOSEHerder class.

Class for handling parametric design evaluation using MOOSEHerder for model
instantiation.

(c) Copyright UKAEA 2024.
"""

import csv
from pathlib import Path
import subprocess

from mooseherder import InputModifier


class MooseHerder():
    """Class for handling parametric design evaluation.

    MOOSEHerder is used for model instantiation and a chosen MOOSE app is used
    for simulation.
    """

    def __init__(
        self,
        moose_exec_path: str | Path,
        base_input_file: str | Path,
        working_dir: str | Path,
    ) -> None:
        """Initialise class instance.

        Parameters
        ----------
        moose_exec_path (str | Path):
            Path to the MOOSE executable file to run, as you would type on the
            command line. If the executable directory has been exported to
            PATH, a string containing the command is also valid, as is a string
            containing a valid alias.
        base_input_file (str | Path):
            Path to the base MOOSE input file (.i) to use as the basis for
            generating modified files. This file will not be modified. Refer to
            MOOSEHerder documentation for instructions on how to prepare your
            input files to be compatible.
        working_dir (str | Path):
            Path to the working directory to use for storing modified MOOSE
            input files (.i), as well as run the MOOSE executable. This is
            also where MOOSE will store your simulation outputs by default,
            unless your input file specifies a different location.
        """
        self.moose_exec_path = Path(moose_exec_path)
        self.base_input_file = Path(base_input_file)
        self.working_dir = Path(working_dir)
        self.trial_num = 0

    def generate_modified_input_file(self, parameters: dict) -> Path:
        """Generate a modified MOOSE input file with specified parameters.

        Generate a modified MOOSE input file (.i) with specified parameters.
        Generated file will use the filename convention "trial_N" where N is
        the trial number starting at 1 and iterating by 1 each time this method
        is called.

        Parameters
        ----------
        parameters (dict):
            Dictionary of parameters to use in the modified file. Keys must
            match top-level parameters in the input file.

        Returns
        -------
        trial_filepath (Path):
            Path to the generated input file for the given trial.
        """
        moose_mod = InputModifier(
            str(self.base_input_file), comment_char='#', end_char=''
        )

        print(
            "Variables found the top of the MOOSE input file:\n"
            f"{moose_mod.get_vars()}\n"
        )

        moose_mod.update_vars(parameters)

        print(
            f"New variables inserted:\n{moose_mod.get_vars()}\n"
        )

        self.trial_num += 1
        trial_filename = f"trial_{self.trial_num}"
        trial_filepath = self.working_dir / f"{trial_filename}.i"
        moose_mod.write_file(str(trial_filepath))

        print(
            "Modified input script written to:\n"
            f"{str(trial_filepath)}\n"
        )

        return trial_filepath

    def run_simulation(self, moose_input_filepath: Path | str):
        """Run a simulation.

        Parameters
        ----------
        moose_input_filepath (Path | str):
            Path to the moose input file (.i) to run.
        """
        command = [
            str(self.moose_exec_path),
            "-i",
            str(moose_input_filepath),
        ]

        print(f"Running command:\n {' '.join(command)}\n")

        subprocess.run(
            command,
            cwd=str(self.working_dir)
        )

    def read_csv(self, trial_num: int = None):
        """Read an output csv file using the default suffix "_out.csv".

        Parameters
        ----------
        trial_num (int, optional):
            Number of the trial, as it appears in the filename. Defaults to
            None, in which case the latest trial is used.

        Returns
        -------
        data (list):
            Rowwise data as read from csv.
        """
        print("Reading results.\n")

        # If trial number unspecified, default to latest trial.
        if trial_num is None:
            trial_num = self.trial_num

        csv_filepath = self.working_dir / f"trial_{trial_num}_out.csv"
        with open(csv_filepath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            data = [row for row in csv_reader]

        return data

    def evaluate_design(self, parameters):
        """Convenience method for evaluating a given design: generate a
        modified input file, run a simulation, and read the results. Requires
        that the moose file outputs to csv using the default suffix "_out.csv".

        Parameters
        ----------
        parameters (dict):
            Dictionary of parameters to use for the design.

        Returns
        -------
        data (list):
            Rowwise data as read from csv.
        """
        trial_filepath = self.generate_modified_input_file(parameters)
        self.run_simulation(trial_filepath)
        data = self.read_csv()

        return data
