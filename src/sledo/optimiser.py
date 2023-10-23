"""
Optimiser classes for SLEDO.

Handles Bayesian Optimisation.

(c) Copyright UKAEA 2023.
"""
import ax.service.ax_client
import pathlib
import dill

# Import pyhit and moosetree from your local moose installation.
import pyhit
import moosetree


class Optimiser:
    """The SLEDO optimiser base class.

    Methods
    -------
    load_input_file(path_to_input_file):
        Load a MOOSE input file to serve as a base for optimisation. Save a
        copy to the data directory.
    generate_modified_file(filename, parameters)):
        Generate a MOOSE input file by modifying the parameters specified. Save
        the new file to the data directory.
    """

    def __init__(
        self,
        name,
        simulation_class,
        search_space,
        data_dir=None,
        input_file=None,
    ):
        """
        Initialise class instance.

        Attributes
        ----------
        simulation_class : sledo.Simulation
            The simulation class to use for the optimisation.
        search_space : list[dict]
            The search space for the optimisation.
        data_dir : str | pathlib.Path
            Path to the data directory for the optimisation.
        input_file: str | pathlib.Path
            Path to the simulation input file for the optimisation.
        """
        self.name = name
        self.simulation_class = simulation_class

        # Get location of each param in the moose input file (HIT format).
        self.hit_blocks = {}
        self.hit_names = {}
        for param in search_space:
            self.hit_blocks[param["name"]] = param["hit_block"]
            param.pop("hit_block")
            self.hit_names[param["name"]] = param["hit_name"]
            param.pop("hit_name")
        self.search_space = search_space

        # Set data directory.
        if data_dir:
            self.data_dir = pathlib.Path(data_dir)
        else:
            self.data_dir = pathlib.Path(f"./{self.name}")
        if not self.data_dir.exists():
            self.data_dir.mkdir()

        # Load input file, if one was passed.
        if input_file:
            self.load_input_file(path_to_input_file=input_file)

    def load_input_file(self, path_to_input_file):
        """Load a MOOSE input file to serve as a base for optimisation. Save a
        copy to the data directory.
        """
        # Load input file.
        filename_to_load = str(path_to_input_file)
        moose_file = pyhit.load(filename_to_load)

        # Save a copy.
        filename_to_save = str(self.data_dir / "input_unmodified.i")
        pyhit.write(filename_to_save, moose_file)

    def generate_modified_file(self, filename, new_params):
        """Generate a MOOSE input file by modifying the new_params specified in
        new_params. Save the new file to the data directory.

        Parameters
        ----------
        filename (str):
            filename for the modified input file
        new_params (list of dicts):
            list of dictionaries containing information on which new_params to
            modify
        """
        # Load unmodified input file from data directory.
        path_to_base_input_file = self.data_dir / "input_unmodified.i"
        if not path_to_base_input_file.is_file():
            print("Base input file not found. Use load_input_file() first.")
        root = pyhit.load(str(path_to_base_input_file))

        # Locate and modify each parameter.
        for param, value in zip(new_params.keys(), new_params.values()):
            hit_block = self.hit_blocks[param]
            hit_name = self.hit_names[param]
            if hit_block:
                block = moosetree.find(
                    root, func=lambda n: n.fullpath == hit_block
                )
            else:
                block = root
            block[hit_name] = value
            block.setComment(hit_name, "Modified by SLEDO")

        # Write modified input file to data directory.
        path_to_modified_file = self.data_dir / f"{filename}.i"
        pyhit.write(path_to_modified_file, root)

        return path_to_modified_file

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
        """Save object to file."""
        if not filepath:
            filepath = self.data_dir / f"{self.name}.pickle"
        with open(filepath, "wb") as file:
            dill.dump(self, file)

    @classmethod
    def unpickle(cls, filepath):
        with open(filepath, "rb") as f:
            obj = dill.load(f)
        if isinstance(obj, cls):
            return obj
        raise TypeError(
            f"Unpickled object is not an instance of {cls.__name__}."
        )
