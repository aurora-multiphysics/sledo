"""
SLEDO MooseHerder/Proteus Simple Monoblock Example

Example input file for running Bayesian optimisation of a simplified divertor
monoblock using MooseHerder as the model instantiation tool and Proteus as the
simulation tool.

(c) Copyright UKAEA 2023-2024.
"""

from pathlib import Path
from ray import tune
from ray.tune.search.ax import AxSearch

from sledo.optimiser import Optimiser
from examples.mooseherder.design_evaluator import DesignEvaluator

MOOSE_OPT = "proteus-opt"
EXAMPLES_DIR = Path(__file__).parent.absolute()
BASE_INPUT_FILE = EXAMPLES_DIR / "input_files" / "simple_monoblock.i"
WORKING_DIR = EXAMPLES_DIR / "results" / "simple_monoblock"

if __name__ == '__main__':

    # Instantiate moose herder class.
    design_evaluator = DesignEvaluator(
        MOOSE_OPT,
        BASE_INPUT_FILE,
        WORKING_DIR,
    )

    # Define design evaluation function.
    def evaluate(parameters):
        data = design_evaluator.evaluate_design(parameters)
        stress = float(data[-1][-1])
        return {"stress": stress}

    # Define a search space according to the Ray Tune API.
    # Documentation here:
    # https://docs.ray.io/en/latest/tune/api/search_space.html
    search_space = {
        "monoBArmHeight": tune.uniform(1e-3, 20e-3),
        "monoBThick": tune.uniform(0.5e-3, 9e-3),
    }

    # Instantiate SLEDO optimiser.
    opt = Optimiser(
        "simple-monoblock-optimiser",
        evaluate,
        search_space,
        "stress",
        AxSearch(),
        20,
        data_dir=WORKING_DIR,
    )

    results = opt.run_optimisation()

    # Save the optimiser class instance to file.
    opt.pickle()
