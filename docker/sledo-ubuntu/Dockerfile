# Get base image
FROM idaholab/moose:latest

ARG WORKDIR="opt"

# Build Sledo
RUN cd /$WORKDIR && \
    git clone https://github.com/aurora-multiphysics/sledo.git && \
    cd sledo && \
    chmod +x install.sh && \
    ./install.sh

# Add MOOSE python packages to python path
RUN export PYTHONPATH=${PYTHONPATH}:/${WORKDIR}/moose/python/pyhit && \
    export PYTHONPATH=${PYTHONPATH}:/${WORKDIR}/moose/python/moosetree
