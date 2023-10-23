"""
Simulation class for SLEDO.

Handles MOOSE simulations.

(c) Copyright UKAEA 2023.
"""
import subprocess
import pathlib
import csv
import yaml

CONFIG_PATH = "config.yaml"


class Simulation:
    """The SLEDO simulation base class.

    Handles running a MOOSE simulation for a given design point.

    Methods
    -------
    run_sim():
        Run a simulation.
    read_outputs():
        Read the results of the simulation.
    """

    def __init__(self, name, sim_dir, moose_path=None):
        """Initialise class instance.

        Parameters
        ----------
            filename : str
                Name of the simulation, used as the filename prefix.
            sim_dir : str or pathlib.Path
                Valid path to the input file to be used for the simulation.
            moose_path : str, optional (default = None)
                Valid path to the moose app to be used for the simulation.
                If left as `None` then the path with be taken from
                `config.yaml`.
        """
        self.name = name
        self.input_filename = f"{name}.i"
        self.output_filename = f"{name}_out.e"
        self.output_csv_filename = f"{name}_out.csv"
        if moose_path is None:
            with open(CONFIG_PATH) as config_file:
                config = yaml.safe_load(config_file)
                moose_path = config["MOOSE_PATH"]
        self.moose_path = pathlib.Path(moose_path).expanduser()
        self.sim_dir = pathlib.Path(sim_dir)

    def run_sim(self, extra_args=[]):
        """Run the simulation.

        Parameters
        ----------
        extra_args : str
            String containing all additional flags and arguments for the
            command line when initiating the simulation.
        """
        # Generate simulation command.
        input_path = self.sim_dir / self.input_filename
        command = [
            str(self.moose_path),
            "-i",
            str(input_path),
            f"name={str(self.name)}",
            f"outputDir={str(self.sim_dir)}",
        ]
        for arg in extra_args:
            command.append(arg)

        # Run simulation command as subprocess. Print stdout to the shell live.
        print(f"Running command: {' '.join(command)}")
        subprocess.run(command)

    def read_outputs(self):
        """Read the results of the simulation."""
        with open(self.sim_dir / self.output_csv_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            data = [row for row in csv_reader]
            return data


class ThermoMechSimulation(Simulation):
    """SLEDO simulation subclass for a thermomechanical MOOSE simulation."""

    def __init__(self, filename, sim_dir):
        super().__init__(filename, sim_dir)

    def get_results(self):
        """Return von Mises stress output."""
        data = self.read_outputs()
        result_dict = {"stress": (float(data[-1][-1]), 0.0)}
        return result_dict
