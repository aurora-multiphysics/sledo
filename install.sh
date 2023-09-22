#!/usr/bin/env bash
#
# SLEDO installation script.
#
# (c) Copyright UKAEA 2023.

# Setup python virtual environment.
echo "Setting up python venv..."
python -m venv venv
source venv/bin/activate

# Build and install sledo package.
echo "Building sledo package..."
pip install build --upgrade
python -m build
echo "Installing sledo package..."
pip install ./dist/*.whl

# Notify user.
echo "Install complete."
echo ""
echo "Please ensure you add pyhit and moosetree to your python path by adding the following lines to your bashrc file:"
echo "export PYTHONPATH=\${PYTHONPATH}:/path/to/moose/python/pyhit"
echo "export PYTHONPATH=\${PYTHONPATH}:/path/to/moose/python/moosetree"
