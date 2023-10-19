# sledo

SLEDO (Sequential Learning Engineering Design Optimiser) is a tool for optimising parametric component designs, developed for fusion engineering.

Sledo uses Bayesian Optimisation to intelligently select candidate designs from a parametric search space and MOOSE to evaluate the design performance via scalable multiphysics simulation.

# Installation

## Linux

Create a virtual environment and activate it. (Skip this step if you intend to install `sledo` into an existing python environment.)
```
python -m venv venv
source venv/bin/activate
```

### Standard install
To install `sledo`, run the following:
```
# Ensure `build` package is installed.
pip install build --upgrade

# Build the distribution package.
python -m build

# Install the built distribution.
pip install ./dist/*.whl
```

If you intend to use the jupyter notebook tutorials, also run the following line:
```
# Enable virtual environment in the tutorial notebooks.
python -m ipykernel install --user --name=venv
```

Sledo can now be imported into python as:
```
import sledo
```

To test the installation, run `python -c "import sledo"`. If the installation was unsuccessful, an error will be raised.



### Editable install (developer mode)
Developers may wish to create an editable installation. This allows changes to the source code to immediately take effect without the need to re-package and re-install sledo. This can be useful when running tests and other scripts.

To install `sledo` this way, run the following:
```
# Install as an editable installation.
pip install --editable .
```

# Getting started

To start using sledo, please refer to the `tutorials` and `examples` folders for example usage.

# Contributors

Luke Humphrey, UK Atomic Energy Authority

Aleksander Dubas, UK Atomic Energy Authority

Andrew Davis, UK Atomic Energy Authority

Lloyd Fletcher, UK Atomic Energy Authority

# Citing Sledo

If using Sledo in your research, please cite the following:

> Citation TBC

Please also cite Sledo's dependencies as indicated on their individual websites:

- MOOSE (https://mooseframework.inl.gov/citing.html)
- BoTorch (https://botorch.org/docs/papers)
- NumPy (https://numpy.org/citing-numpy/)
- SciPy (https://scipy.org/citing-scipy/)
- Matplotlib (https://matplotlib.org/stable/users/project/citing.html)
