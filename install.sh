#!/usr/bin/env bash
#
# SLEDO installation script.
#
# (c) Copyright UKAEA 2023.

# Build and install sledo package.
echo "Building sledo package..."
pip3 install build --upgrade
python3 -m build
echo "Installing sledo package..."
pip3 install ./dist/*.whl

# Allow jupyter notebooks to use the virtual environment.
python3 -m ipykernel install --user --name=venv

# Notify user.
echo "Install complete."
echo ""
echo "Please ensure you add pyhit and moosetree to your python path by adding the following lines to your bashrc file:"
echo "export PYTHONPATH=\${PYTHONPATH}:/path/to/moose/python/pyhit"
echo "export PYTHONPATH=\${PYTHONPATH}:/path/to/moose/python/moosetree"
