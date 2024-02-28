"""
SLEDO functions wrapping mooseherder for design evaluation.

Contains functions for modifying MOOSE input files, initiating MOOSE
simulations, and reading MOOSE simulation results.

(c) Copyright UKAEA 2024.
"""

from pathlib import Path

from mooseherder import (
    MooseConfig,
    InputModifier,
    MooseRunner,
    ExodusReader,
    SimData,
)

from sledo.paths import MOOSE_CONFIG_FILE


def generate_modified_input_file(
    base_input_file: Path | str,
    new_input_filepath: Path | str,
    parameters: dict,
) -> Path:
    """Generate a modified MOOSE input file (.i) with specified parameters.

    Parameters
    ----------
    base_input_file : Path | str
        Path to the base MOOSE input file (.i) to use as the basis for
        generating modified files. This file will not be modified.
    new_input_filepath : Path | str
        Path to input file to be generated. The .i extension will be added if
        not passed.
    parameters : dict
        Dictionary of parameters to use in the modified file. Keys must
        match top-level parameters in the input file.

    Returns
    -------
    new_input_filepath : Path
        Path to the generated input file for the given trial.
    """
    # Read base input file, modify parameters.
    moose_mod = InputModifier(
        str(base_input_file), comment_char="#", end_char=""
    )
    moose_mod.update_vars(parameters)

    # Write new input file, ensuring .i extension is used.
    new_input_filepath = Path(new_input_filepath)
    if new_input_filepath.suffix != ".i":
        new_input_filepath = new_input_filepath.parent / Path(
            new_input_filepath.name + ".i"
        )
    moose_mod.write_file(new_input_filepath)

    return new_input_filepath


def run_simulation(
    input_filepath: Path | str,
    moose_config_file: Path | str = MOOSE_CONFIG_FILE,
    run_options: dict = {
        "n_tasks": 1,
        "n_threads": 4,
        "redirect_out": False,
    },
) -> None:
    """Run a MOOSE simulation.

    Parameters
    ----------
    input_filepath : Path | str
        Path to the moose input file (.i) to run.
    config_path : Path | str, optional
        Path to the config file containing the required paths to run MOOSE,
        by default 'moose_config.json' in the sledo root folder is used.
    run_options : dict, optional
        Dict of options for running the simulation, by default
        { "n_tasks": 1, "n_threads": 4, "redirect_out": False }.

    Returns
    -------
    exodus_filepath : Path
        Expected path to the exodus file using the "_out.e" suffix convention.
    """
    moose_config = MooseConfig().read_config(moose_config_file)
    moose_runner = MooseRunner(moose_config)
    moose_runner.set_input_file(Path(input_filepath))
    moose_runner.set_run_opts(**run_options)
    moose_runner.run()

    exodus_filepath = input_filepath.parent / (input_filepath.stem + "_out.e")

    return exodus_filepath


def read_exodus(filepath: Path | str) -> SimData:
    """Read an exodus file and return simulation data.

    Parameters
    ----------
    filepath : Path | str
        Filepath to exodus file to read.

    Returns
    -------
    SimData
        SimData object containing the simulation results read from file.
    """
    exodus_reader = ExodusReader(filepath)
    simdata = exodus_reader.read_all_sim_data()

    return simdata
