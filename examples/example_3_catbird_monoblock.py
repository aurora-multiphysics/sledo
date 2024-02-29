"""
SLEDO Monoblock Example

Example input file for running Bayesian optimisation of a divertor monoblock
to minimise the peak temperature predicted by a thermal MOOSE simulation.

In this example, catbird is used to generate input files without the need for
a user-supplied input file to use as a base.

(c) Copyright UKAEA 2023-2024.
"""

from ray import tune

from pathlib import Path
from mooseherder import MooseConfig

from sledo import Optimiser, CatBirdMooseHerderDesignEvaluator
from sledo import SLEDO_ROOT, MOOSE_CONFIG_FILE

from input_files.catbird_monoblock import (
    MonoblockFactory,
    MonoblockGeometry,
    MonoblockModel,
)

EXAMPLES_DIR = SLEDO_ROOT / "examples"
WORKING_DIR = EXAMPLES_DIR / "results" / "example_3"
FACTORY_CONFIG_PATH = WORKING_DIR / "factory_config.json"
INPUT_FILE_PATH = WORKING_DIR / "trial.i"
PICKLE_FILEPATH = WORKING_DIR / "catbird-monoblock-optimiser.pickle"

METRICS = ["max_temp"]

if __name__ == "__main__":

    # Only run if optimiser not already pickled.
    if not PICKLE_FILEPATH.exists():

        # Create factory, loading from config if available, else generating
        # from the objects available in the MOOSE app.
        moose_config = MooseConfig().read_config(
            MOOSE_CONFIG_FILE
        ).get_config()
        app_exe = Path(moose_config["app_path"]) / moose_config["app_name"]

        if FACTORY_CONFIG_PATH.is_file():
            factory = MonoblockFactory(app_exe, str(FACTORY_CONFIG_PATH))
        else:
            factory = MonoblockFactory(app_exe)
            factory.write_config(str(FACTORY_CONFIG_PATH))

        # geom
        # modify geom
        # pass to monoblock model
        model = MonoblockModel(factory)

        # Write out our input file
        input_name = WORKING_DIR / "monoblock_thermal.i"
        model.write(input_name)

        # Instantiate design evaluator.
        design_evaluator = CatBirdMooseHerderDesignEvaluator(
            METRICS,
            model,
            working_dir=WORKING_DIR,
            config_path=MOOSE_CONFIG_FILE,
        )

        # Define a search space according to the ray tune API.
        # Documentation here:
        # https://docs.ray.io/en/latest/tune/api/search_space.html
        search_space = {
            "pipeThick": tune.uniform(1e-3, 6e-3),
            "intLayerThick": tune.uniform(1e-3, 6e-3),
            "monoBThick": tune.uniform(1e-3, 6e-3),
            "monoBArmHeight": tune.uniform(1e-3, 16e-3),
        }

        # Instantiate SLEDO optimiser.
        opt = Optimiser(
            "catbird-monoblock-optimiser",
            design_evaluator,
            search_space,
            20,
            data_dir=WORKING_DIR,
        )

        # Save the optimiser class instance to file.
        opt.pickle(PICKLE_FILEPATH)

    # If there's a pickle from a previous run, unpickle that instead.
    else:
        opt = Optimiser.unpickle(PICKLE_FILEPATH)

    # Run optimisation.
    results = opt.run_optimisation()
    print(results)

    # Save the optimiser class instance to file.
    opt.pickle(PICKLE_FILEPATH)
