"""
ProteusHerder class.

Class for handling parametric design evaluation using MOOSEHerder for model
instantiation and Proteus for simulation.

(c) Copyright UKAEA 2024.
"""

import csv
from pathlib import Path
import subprocess

from mooseherder import InputModifier


class ProteusHerder():
    """Class for handling parametric design evaluation.

    MOOSEHerder is used for model instantiation and Proteus is used for
    simulation.
    """

    def __init__(
        self,
        moose_opt_path: str | Path,
        base_input_file: str | Path,
        working_dir: str | Path,
    ) -> None:
        """_summary_

        Args:
            moose_opt_path (str | Path): _description_
            base_input_file (str | Path): _description_
            working_dir (str | Path): _description_
        """
        self.moose_opt_path = Path(moose_opt_path)
        self.base_input_file = Path(base_input_file)
        self.working_dir = Path(working_dir)
        self.trial_num = 0

    def generate_modified_input_file(self, parameters: dict) -> None:
        """_summary_

        Args:
            parameters (dict): _description_

        Returns:
            _type_: _description_
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

    def evaluate_design(self, parameters: dict):
        """_summary_

        Args:
            parameters (_type_): _description_

        Returns:
            _type_: _description_
        """
        trial_filepath = self.generate_modified_input_file(parameters)

        command = [
            str(self.moose_opt_path),
            "-i",
            str(trial_filepath),
        ]

        print(f"Running command:\n {' '.join(command)}\n")

        subprocess.run(
            command,
            cwd=str(self.working_dir)
        )

        print("Reading results.\n")

        csv_filepath = self.working_dir / f"trial_{self.trial_num}_out.csv"
        with open(csv_filepath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            data = [row for row in csv_reader]

        return data
