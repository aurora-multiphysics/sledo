"""
SLEDO Monoblock Example

Example input file for running Bayesian optimisation of a divertor monoblock
to minimise the peak temperature predicted by a thermal MOOSE simulation.
Note that this thermal problem has a flat cost function, so nothing is
optimised, however this example demonstrates how to interface between sledo and
catbird.

In this example, catbird is used to generate input files without the need for
a user-supplied input file to use as a base.

(c) Copyright UKAEA 2023-2024.
"""

from ray import tune

from pathlib import Path
from mooseherder import MooseConfig

from sledo import Optimiser, CatBirdMooseHerderDesignEvaluator
from sledo import SLEDO_ROOT

# This points to the file 'moose_config.json' in sledo root folder.
# If you haven't already, please make sure you've entered the required paths
# for your chosen MOOSE app.
# In general, you don't need to import this as it will be used by default,
# however you may point to a config file in a different location if you wish
# to use something else for a given optimisation run.
from sledo import MOOSE_CONFIG_FILE

# Import the required catbird MooseFactory and MooseModel classes.
from input_files.catbird_monoblock import (
    MonoblockFactory,
    MonoblockModel,
)

# Set the paths required for this example.
# In general, the user will set their own paths and pass them where required.
EXAMPLES_DIR = SLEDO_ROOT / "examples"
WORKING_DIR = EXAMPLES_DIR / "results"
FACTORY_CONFIG_PATH = WORKING_DIR / "factory_config.json"
INPUT_FILE_PATH = WORKING_DIR / "trial.i"
PICKLE_FILEPATH = WORKING_DIR / "example_3_optimiser.pickle"

if __name__ == "__main__":

    # Set metrics for optimisation. These must exactly match how they appear
    # in your MOOSE postprocessor. In this case, we are only optimising a
    # single objective, but the list convention is still used.
    metrics = ["max_temp"]

    # To save time when rerunning this example, only run if optimiser is not
    # already saved as pickle. If there's a pickle from a previous run,
    # unpickle that instead.
    if PICKLE_FILEPATH.exists():
        opt = Optimiser.unpickle(PICKLE_FILEPATH)
    else:
        # Create factory, loading from config if available, else generating
        # from the objects available in the MOOSE app.
        moose_config = (
            MooseConfig().read_config(MOOSE_CONFIG_FILE).get_config()
        )
        app_exe = Path(moose_config["app_path"]) / moose_config["app_name"]

        if FACTORY_CONFIG_PATH.is_file():
            factory = MonoblockFactory(app_exe, str(FACTORY_CONFIG_PATH))
        else:
            factory = MonoblockFactory(app_exe)
            factory.write_config(str(FACTORY_CONFIG_PATH))

        # Instantiate Monoblock catbird model.
        model = MonoblockModel(factory)

        # Instantiate design evaluator.
        design_evaluator = CatBirdMooseHerderDesignEvaluator(
            metrics,
            model,
            config_path=MOOSE_CONFIG_FILE,  # Contains required MOOSE paths.
        )

        # Define a search space according to the Ray Tune API.
        # Documentation here:
        # https://docs.ray.io/en/latest/tune/api/search_space.html
        # The variable names must exactly match how they appear in the catbird
        # model so that they can be updated for each design iteration.
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
            name="example_3",
            data_dir=WORKING_DIR,
        )

        # Save the optimiser class instance to file, if something goes wrong in
        # the optimisation step, this will be reloaded to save time rerunning.
        opt.pickle(PICKLE_FILEPATH)

    # Run optimisation.
    results = opt.run_optimisation()
    print(results)

    # Save the optimiser class instance to file.
    opt.pickle(PICKLE_FILEPATH)

    # To load the optimiser class from file, you can then run.
    opt = Optimiser.unpickle(PICKLE_FILEPATH)
