from sledo.optimiser import Optimiser
from sledo.simulation import ThermoMechSimulation

DATA_DIR = "./results/example_1"

search_space = (
    {
        "name": "Armour height",
        "type": "range",
        "hit_name": "monoBArmHeight",
        "hit_block": "",
        "bounds": [1e-3, 20e-3],
    },
    {
        "name": "Block width",
        "type": "range",
        "hit_name": "monoBWidth",
        "hit_block": "",
        "bounds": [17e-3, 34e-3],
    },
)

opt = Optimiser(
    name="simple_monoblock",
    search_space=search_space,
    simulation_class=ThermoMechSimulation,
    data_dir=DATA_DIR,
)

opt.load_input_file("./input_files/simple_monoblock.i")
opt.run_optimisation_loop(
    objective_name="stress",
    max_iter=20,
    minimise=True,
)

opt.pickle()
