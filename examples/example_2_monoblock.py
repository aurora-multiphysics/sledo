"""
SLEDO Monoblock Example

Example input file for running Bayesian optimisation of a divertor monoblock
to minimise the peak von misses stress predicted by a thermomechanical
MOOSE simulation.

(c) Copyright UKAEA 2023-2024.
"""

from ray import tune

from sledo import Optimiser, MooseHerderDesignEvaluator
from sledo import SLEDO_ROOT

# This points to the file 'moose_config.json' in sledo root folder.
# If you haven't already, please make sure you've entered the required paths
# for your chosen MOOSE app.
# In general, you don't need to import this as it will be used by default,
# however you may point to a config file in a different location if you wish
# to use something else for a given optimisation run.
from sledo import MOOSE_CONFIG_FILE

# Set the paths required for this example.
# In general, the user will set their own paths and pass them where required.
EXAMPLES_DIR = SLEDO_ROOT / "examples"
INPUT_FILE = EXAMPLES_DIR / "input_files" / "monoblock_thermomech.i"
WORKING_DIR = EXAMPLES_DIR / "results"
PICKLE_FILEPATH = WORKING_DIR / "example_2_optimiser.pickle"

if __name__ == "__main__":

    # Set metrics for optimisation. These must exactly match how they appear
    # in your MOOSE postprocessor. In this case, we are only optimising a
    # single objective, but the list convention is still used.
    metrics = ["max_stress"]

    # Instantiate design evaluator.
    design_evaluator = MooseHerderDesignEvaluator(
        metrics,
        INPUT_FILE,  # The base input file to be modified per design iteration.
        config_path=MOOSE_CONFIG_FILE,  # Contains required MOOSE paths.
    )

    # Define a search space according to the Ray Tune API.
    # Documentation here:
    # https://docs.ray.io/en/latest/tune/api/search_space.html
    # The variable names must exactly match how they appear in the MOOSE input
    # file so that they can be updated for each design iteration.
    search_space = {
        "pipeThick": tune.uniform(1e-3, 6e-3),
        "intLayerThick": tune.uniform(1e-3, 6e-3),
        "monoBThick": tune.uniform(1e-3, 6e-3),
        "monoBArmHeight": tune.uniform(1e-3, 16e-3),
    }

    # Instantiate SLEDO optimiser.
    opt = Optimiser(
        design_evaluator,
        search_space,
        max_total_trials=20,
        name="example_2",
        data_dir=WORKING_DIR,
    )

    # Run optimisation.
    results = opt.run_optimisation()
    print(results)

    # Save the optimiser class instance to file.
    opt.pickle(PICKLE_FILEPATH)

    # To load the optimiser class from file, you can then run.
    opt = Optimiser.unpickle(PICKLE_FILEPATH)
