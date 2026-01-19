# docker-globes
GLoBES, General Long Baseline Experiment Simulator in a Docker container

## Overview

This repository provides a Docker container with GLoBES 3.2.18 for neutrino physics simulations, including comprehensive support for **reactor-based CEvNS** (Coherent Elastic Neutrino-Nucleus Scattering) Monte Carlo simulations.

## Features

- **GLoBES 3.2.18** with GNU Scientific Library (GSL) support
- **CEvNS simulation framework** with Python and C++ examples
- Pre-computed physics data (reactor flux, cross sections, form factors)
- Complete documentation and tutorials
- Ready-to-use detector configurations (Germanium, Xenon)

## Quick Start

### Build and Run

```bash
# Build the Docker image
docker build -t docker-globes .

# Run container with workspace
docker run -it -v $(pwd)/examples:/workspace docker-globes /bin/bash
```

### CEvNS Simulations

This container includes complete tools for reactor-based CEvNS simulations:

#### Documentation
- **[CEvNS Reactor Quick-Start Guide](docs/CEVNS_REACTOR_QUICKSTART.md)** - Comprehensive tutorial
- **[AEDL Reference](docs/AEDL_EXAMPLES.md)** - GLoBES configuration syntax
- **[Examples Guide](examples/README.md)** - Running the example code

#### Quick Example (Python)
```bash
cd /workspace/python
apt update
apt install pip
pip install -r requirements.txt

# Calculate event rates
python cevns_calculator.py --detector Ge --mass 1.0 --baseline 25.0 --power 3.0

# Run Monte Carlo simulation
python mc_simulation.py --nevents 10000 --output my_simulation
```

#### Quick Example (C++)
```bash
cd /workspace/cpp
make all

# Calculate event rate
./basic_rate_calculator 25.0 3.0 1.0 73 32

# Generate MC events
./mc_event_generator --nevents 10000 --output events.csv
```

## What is CEvNS?

Coherent Elastic Neutrino-Nucleus Scattering (CEvNS) is a Standard Model process where neutrinos scatter coherently off entire nuclei. Nuclear reactors provide intense antineutrino sources ideal for CEvNS detection.

**Key features:**
- Cross section scales as N² (coherent enhancement)
- Sub-keV nuclear recoils (challenging detection threshold)
- Flavor-blind process (sensitive to all neutrino flavors equally)
- Applications: reactor monitoring, dark matter searches, neutrino properties

## Repository Structure

```
docker-globes/
├── Dockerfile                          # Container setup
├── download_globes.sh                  # GLoBES download script
├── docs/                               # Documentation
│   ├── CEVNS_REACTOR_QUICKSTART.md    # Main tutorial
│   └── AEDL_EXAMPLES.md                # AEDL reference
└── examples/                           # Code examples and data
    ├── python/                         # Python scripts
    ├── cpp/                            # C++ programs
    ├── aedl/                           # GLoBES configurations
    └── data/                           # Physics data files
```

## License

MIT License - see LICENSE file for details
