"""
SLEDO Monoblock Example

Example input file for running Bayesian optimisation of a divertor monoblock.

(c) Copyright UKAEA 2023.
"""

from sledo.optimiser import Optimiser
from sledo.simulation import Simulation
from ray import train, tune
from ray.tune.search.ax import AxSearch
from mooseherder import InputModifier
import pathlib


DATA_DIR = pathlib.Path("./results/example_monoblock")

if __name__ == '__main__':

    counter = 0

    def design_evaluator(input_parameters):
        # Generate modified input file.
        moose_input = "/home/luke/code/sledo/examples/input_files/monoblock.i"
        # moose_mod = InputModifier(moose_input, comment_char='#', end_char='')
        # moose_mod.update_vars(input_parameters)
        # counter += 1
        # moose_filename = f"monoblock_{counter}"
        # moose_filepath = DATA_DIR / f"{moose_filename}.i"
        # moose_mod.write_file(str(moose_filepath))

        # Run simulation.
        moose_path = "proteus-opt"
        simulation = Simulation(
            "monoblock", DATA_DIR, moose_path=moose_path
        )
        extra_args = [f"{i}={input_parameters[i]}" for i in input_parameters]
        simulation.run_sim(extra_args=extra_args)

        # Read results and return.
        data = simulation.read_outputs()
        stress = float(data[-1][-1])
        return stress

    # Define an objective function.
    def objective(input_parameters):
        stress = design_evaluator(input_parameters)
        train.report(
            {"stress": stress}
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

    # Define the search algorithm.
    # Input/output constraints may be specified at this stage by uncommenting
    # the lines below.
    search_alg = AxSearch(
        # parameter_constraints = [],
        # outcome_constraints = [],
    )

    # Set the maximum number of concurrent trials.
    search_alg = tune.search.ConcurrencyLimiter(search_alg, max_concurrent=4)

    # Set the number of component designs to trial.
    num_samples = 20

    tuner = tune.Tuner(
        objective,
        tune_config=tune.TuneConfig(
            metric="stress",
            mode="min",
            search_alg=search_alg,
            num_samples=num_samples,
        ),
        run_config=train.RunConfig(
            name="ax",
        ),
        param_space=search_space,
    )
    results = tuner.fit()

    # # Instantiate the Sledo Optimiser class.
    # opt = Optimiser(
    #     name="monoblock",
    #     search_space=search_space,
    #     search_algorithm=search_algo,
    #     data_dir=DATA_DIR,
    # )

    # opt.run_optimisation_loop(
    #     objective_name="stress",
    #     max_iter=20,
    #     minimise=True,
    # )

    # opt.pickle()
