# Get base image
FROM idaholab/moose:latest

ARG WORKDIR="opt"

# By default, checkout the main branch
ARG build_git_sha="main"

# Build Sledo
RUN cd /$WORKDIR && \
    git clone https://github.com/aurora-multiphysics/sledo.git && \
    cd sledo && \
    git checkout "$build_git_sha" && \
    sudo apt update -y && \
    sudo apt install python3 -y && \
    sudo apt install python3.9-venv -y && \
    python3 -m pip install --upgrade pip && \
    chmod +x install.sh && \
    ./install.sh

# Add MOOSE python packages to python path
RUN export PYTHONPATH=${PYTHONPATH}:/${WORKDIR}/moose/python/pyhit && \
    export PYTHONPATH=${PYTHONPATH}:/${WORKDIR}/moose/python/moosetree
