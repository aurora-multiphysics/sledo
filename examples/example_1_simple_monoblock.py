"""
SLEDO Simple Monoblock Example

Example input file for running Bayesian optimisation of a simplified divertor
monoblock to minimise the peak von misses stress predicted by a
thermomechanical MOOSE simulation.

(c) Copyright UKAEA 2023-2025.
"""
from pathlib import Path
from ray import tune

from sledo import Optimiser, MooseHerderDesignEvaluator
from ray.tune.search.bayesopt import BayesOptSearch

# Set the paths required for this example, starting with the directory
# containing this file. In general usage, the user will set their own paths.
# If you haven't already, you should update the moose_config.json file in the
# examples folder with the paths to your MOOSE installation.
EXAMPLES_DIR = Path(__file__).parent.absolute()
MOOSE_CONFIG_FILE = EXAMPLES_DIR / "moose_config.json"
INPUT_FILE = EXAMPLES_DIR / "input_files" / "simple_monoblock_thermomech.i"
WORKING_DIR = EXAMPLES_DIR / "results"
PICKLE_FILEPATH = WORKING_DIR / "example_1_optimiser.pickle"

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

    # Instantiate search algorithm.
    bayesopt_search_alg = BayesOptSearch(
        utility_kwargs={"kind": "ucb", "kappa": 2.5, "xi": 0.0}
    )

    # Define a search space according to the Ray Tune API.
    # Documentation here:
    # https://docs.ray.io/en/latest/tune/api/search_space.html
    # The variable names must exactly match how they appear in the MOOSE input
    # file so that they can be updated for each design iteration.
    search_space = {
        "monoBArmHeight": tune.uniform(1e-3, 20e-3),
        "monoBThick": tune.uniform(0.5e-3, 9e-3),
    }

    # Instantiate SLEDO optimiser.
    opt = Optimiser(
        design_evaluator,
        bayesopt_search_alg,
        search_space,
        max_total_trials=20,
        name="example_1",
        data_dir=WORKING_DIR,
    )

    # Run optimisation.
    results = opt.run_optimisation()
    print(results)

    # Save the optimiser class instance to file.
    opt.pickle(PICKLE_FILEPATH)

    # To load the optimiser class from file, you can then run.
    opt = Optimiser.unpickle(PICKLE_FILEPATH)
