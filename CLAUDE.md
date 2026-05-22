# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository provides a Docker container for GLoBES (General Long Baseline Experiment Simulator), a scientific computing tool for neutrino physics simulations. The project includes:

1. GLoBES 3.2.18 installation in a containerized environment
2. Complete framework for reactor-based CEvNS (Coherent Elastic Neutrino-Nucleus Scattering) Monte Carlo simulations
3. Python and C++ example codes with full documentation

## Architecture

### Core Components

1. **download_globes.sh**: Downloads the GLoBES 3.2.18 tarball from the official MPI-HD server if not already present locally. Includes existence check to avoid re-downloading.

2. **Dockerfile**: Multi-stage build process that:
   - Starts from gcc:12.1.0-bullseye base image
   - Installs libgsl-dev (GNU Scientific Library) dependency
   - Downloads GLoBES tarball via the download script
   - Extracts, configures, builds, and installs GLoBES using standard autotools pattern (./configure && make && make install)

3. The built container has GLoBES installed system-wide and ready to use.

### CEvNS Simulation Support

The repository includes comprehensive tools for reactor-based CEvNS simulations:

**Documentation** (in `docs/`):
- `CEVNS_REACTOR_QUICKSTART.md`: Main tutorial covering physics, setup, and implementation
- `AEDL_EXAMPLES.md`: GLoBES AEDL configuration file reference

**Python Examples** (in `examples/python/`):
- `cevns_calculator.py`: Physics calculations (cross sections, form factors, event rates)
- `mc_simulation.py`: Complete Monte Carlo event generator with detector response
- `requirements.txt`: Dependencies (numpy, scipy, matplotlib)

**C++ Examples** (in `examples/cpp/`):
- `basic_rate_calculator.cpp`: Event rate calculations using GLoBES and GSL
- `mc_event_generator.cpp`: MC event generation with detector response
- `Makefile`: Build system (compile with `-lglobes -lgsl -lgslcblas -lm`)

**AEDL Configurations** (in `examples/aedl/`):
- `reactor_ge.glb`: Germanium detector configuration (CONUS+-style, 1 kg @ 25m)
- `reactor_xe.glb`: Xenon detector configuration (NUCLEUS-style, 10g-1kg @ 10m)

**Physics Data** (in `examples/data/`):
- `reactor_flux_U235.dat`: Huber-Mueller reactor antineutrino spectrum
- `cevns_ge_xsec.dat`: CEvNS cross sections for Germanium-73
- `cevns_xe_xsec.dat`: CEvNS cross sections for Xenon-131
- `form_factors.dat`: Helm form factors for Ge, Xe, Ar

## Building and Running

### Build the Docker image
```bash
docker build -t docker-globes .
```

### Run container with examples mounted
```bash
docker run -it -v $(pwd)/examples:/workspace docker-globes /bin/bash
cd /workspace
```

Once inside the container:
- GLoBES tools available system-wide (e.g., `globes`, library files)
- Use Python examples: `cd python && python cevns_calculator.py`
- Compile C++ examples: `cd cpp && make all`

## Key CEvNS Implementation Details

### Physics Parameters

**CEvNS Cross Section**:
```
dσ/dT = (G_F² M_A)/(4π) · Q_W² · F²(Q²) · [1 - (M_A T)/(2 E_ν²)]
```
- G_F = 1.1663787×10⁻⁵ GeV⁻² (Fermi constant)
- Q_W = N - Z(1 - 4sin²θ_W) (weak nuclear charge)
- F(Q²) = Helm form factor

**Detector-Specific Values**:
- Germanium-73: A=73, Z=32, Q_W≈38.6, quenching=0.20
- Xenon-131: A=131, Z=54, Q_W≈72.9, quenching=0.15
- Argon-40: A=40, Z=18, Q_W≈20.6, quenching=0.23
- Cesium-133: A=133, Z=55, Q_W≈73.9, quenching=0.08

(Q_W = N − Z(1 − 4·sin²θ_W) with sin²θ_W = 0.23121.)

**Typical Event Rates** (1 kg Ge, 25m, 3 GW reactor):
- No threshold: ~100 events/day
- 0.2 keV_ee threshold: ~70 events/day
- 1.0 keV_ee threshold: ~10 events/day

### GLoBES-CEvNS Integration Notes

**Important Limitations**:
- GLoBES designed for neutrino oscillation experiments (flavor change)
- CEvNS is neutral-current process (no flavor change)
- Requires custom cross sections (not built into GLoBES)
- AEDL files use workarounds to leverage GLoBES infrastructure

**Energy Units in AEDL**:
- All energies must be in GeV (GLoBES convention)
- Observable energies: 0.0002-0.010 GeV (0.2-10 keV_ee after quenching)
- Neutrino energies: 0.0018-0.008 GeV (1.8-8 MeV)

**File Paths in AEDL**:
- Use relative paths from AEDL file location
- Example: `@flux_file = "../data/reactor_flux_U235.dat"`

## Development Workflow

### Modifying Examples

1. **Python**: Edit files in `examples/python/`, run directly in container
2. **C++**: Edit files in `examples/cpp/`, rebuild with `make`, run executables
3. **AEDL**: Edit `.glb` files in `examples/aedl/`, test with `globes` command

### Adding New Detectors

To add a new detector configuration:
1. Calculate CEvNS cross section for your target nucleus (use Python calculator as template)
2. Generate cross section data file in `examples/data/`
3. Create new AEDL file in `examples/aedl/` (use `reactor_ge.glb` as template)
4. Update detector parameters: mass, baseline, threshold, quenching, resolution

### Generating New Physics Data

Data files were generated using Python script with numpy. To regenerate:
```python
cd examples
python3 << EOF
# (Physics calculation code to generate .dat files)
EOF
```

## Common Commands

### Python Examples
```bash
cd /workspace/python
python3 cevns_calculator.py --help
python3 mc_simulation.py --nevents 10000 --output sim1
```

Python and the scientific stack (numpy, scipy, matplotlib) are installed in the image, so no `pip install` step is needed.

### C++ Examples
```bash
cd /workspace/cpp
make clean && make all
./basic_rate_calculator 25.0 3.0 1.0 73 32
./mc_event_generator --nevents 50000 --output events.csv
```

### GLoBES Commands
```bash
globes --version
globes examples/aedl/reactor_ge.glb  # Parse AEDL file
```

## Key Details

- GLoBES source: https://www.mpi-hd.mpg.de/personalhomes/globes/download/globes-3.2.18.tar.gz
- Build uses standard autotools workflow (configure/make/make install)
- Working directory in container: `/globes-3.2.18` (GLoBES source)
- Workspace directory: `/workspace` (mount examples here)
- Required dependencies: libgsl-dev for GNU Scientific Library support
- License: MIT

## References

- GLoBES Manual: https://www.mpi-hd.mpg.de/personalhomes/globes/
- Huber et al., "GLoBES," Comput. Phys. Commun. 167 (2005) 195
- CEvNS physics references in `docs/CEVNS_REACTOR_QUICKSTART.md`
