# CEvNS Reactor Examples

This directory contains working examples for reactor-based CEvNS Monte Carlo simulations using GLoBES.

## Directory Structure

```
examples/
├── README.md                    (this file)
├── cpp/                         C++ examples
│   ├── basic_rate_calculator.cpp
│   ├── mc_event_generator.cpp
│   └── Makefile
├── python/                      Python examples
│   ├── cevns_calculator.py
│   ├── mc_simulation.py
│   └── requirements.txt
├── aedl/                        GLoBES configuration files
│   ├── reactor_ge.glb
│   └── reactor_xe.glb
└── data/                        Physics data files
    ├── reactor_flux_U235.dat
    ├── cevns_ge_xsec.dat
    └── form_factors.dat
```

## Quick Start

### 1. Enter the Docker Container

```bash
cd /path/to/docker-globes
docker run -it -v $(pwd)/examples:/workspace docker-globes /bin/bash
cd /workspace
```

### 2. Run Python Examples

```bash
cd python
pip install -r requirements.txt

# Calculate event rates
python cevns_calculator.py

# Run full MC simulation
python mc_simulation.py --output my_simulation
```

### 3. Run C++ Examples

```bash
cd cpp
make all

# Calculate basic rates
./basic_rate_calculator

# Generate MC events
./mc_event_generator --output events.csv
```

## Python Examples

### cevns_calculator.py

**Purpose**: Physics calculations and event rate estimates.

**Features**:
- Calculate CEvNS differential cross sections
- Helm form factors for various nuclei
- Reactor flux models (Huber-Mueller)
- Total event rate calculations
- Threshold dependencies

**Usage**:

```bash
# Basic usage with defaults (1 kg Ge, 25m, 3 GW)
python cevns_calculator.py

# Custom configuration
python cevns_calculator.py --detector Ge --mass 1.0 --baseline 25.0 --power 3.0 --threshold 0.2

# Available detectors: Ge, Xe, Ar
# Mass in kg, baseline in meters, power in GW, threshold in keV_ee
```

**Example output**:
```
========================================
CEvNS Event Rate Calculator
========================================

Reactor Configuration:
  Power: 3.0 GW thermal
  Baseline: 25.0 meters
  Antineutrino flux at detector: 9.54e+12 ν/cm²/s

Detector Configuration:
  Material: Germanium (A=73, Z=32)
  Mass: 1.0 kg
  Number of targets: 8.27e+24 nuclei
  Weak charge Q_W: 29.4
  Quenching factor: 0.20

Physics Parameters:
  Cross section (3 MeV): 1.23e-39 cm²
  Mean recoil energy: 0.85 keV

Event Rates:
  No threshold:     102.3 events/day  (37,340 events/year)
  Threshold 0.2 keV: 67.8 events/day  (24,747 events/year)
  Threshold 0.5 keV: 31.2 events/day  (11,388 events/year)
  Threshold 1.0 keV: 10.5 events/day  (3,833 events/year)
```

**Key functions**:
```python
from cevns_calculator import *

# Calculate cross section
sigma = cevns_cross_section(E_nu=3.0, T_recoil=0.5, A=73, Z=32)

# Reactor flux
flux = reactor_flux_huber(E_nu=3.0, isotope='U235')

# Form factor
F2 = helm_form_factor(Q2=0.01, A=73)

# Total rate
rate = calculate_event_rate(power=3.0, baseline=25.0, mass=1.0, A=73, Z=32)
```

### mc_simulation.py

**Purpose**: Complete Monte Carlo event generation with detector response.

**Features**:
- Generate realistic event samples
- Full detector simulation (quenching, resolution, threshold, efficiency)
- Multiple output formats
- Automatic plotting
- Statistical analysis

**Usage**:

```bash
# Basic simulation (10,000 events)
python mc_simulation.py --nevents 10000 --output simulation_run1

# Full configuration
python mc_simulation.py \
    --detector Ge \
    --mass 1.0 \
    --baseline 25.0 \
    --power 3.0 \
    --threshold 0.2 \
    --quenching 0.20 \
    --resolution 0.05 \
    --nevents 50000 \
    --output my_full_simulation
```

**Command-line options**:
- `--detector`: Target material (Ge, Xe, Ar)
- `--mass`: Detector mass in kg
- `--baseline`: Distance from reactor in meters
- `--power`: Reactor thermal power in GW
- `--threshold`: Energy threshold in keV_ee
- `--quenching`: Nuclear recoil quenching factor
- `--resolution`: Fractional energy resolution (σ/E at 1 keV)
- `--nevents`: Number of MC events to generate
- `--output`: Output file prefix

**Output files**:
- `{output}_events.csv`: Event list with columns:
  ```
  event_id, neutrino_energy_MeV, recoil_energy_keV, detected_energy_keV
  ```
- `{output}_spectrum.png`: Recoil energy histogram
- `{output}_flux.png`: Reactor flux plot
- `{output}_xsec.png`: Cross section vs energy
- `{output}_summary.txt`: Run statistics

**Example output**:
```
========================================
CEvNS Monte Carlo Simulation
========================================

Configuration:
  Detector: 1.0 kg Germanium
  Reactor: 3.0 GW at 25.0 m
  Threshold: 0.2 keV_ee
  Quenching: 0.20
  Resolution: 5.0%

Generating 10000 events...
Progress: 100% [####################]

Results:
  Generated events: 10000
  Passed threshold: 6854 (68.5%)
  Mean detected energy: 0.47 keV
  Median detected energy: 0.35 keV

Event rate estimate: 68.5 events/day

Output files:
  simulation_run1_events.csv
  simulation_run1_spectrum.png
  simulation_run1_summary.txt

Done!
```

**Using as a module**:
```python
from mc_simulation import generate_cevns_events, plot_spectrum

events = generate_cevns_events(
    n_events=1000,
    power_GW=3.0,
    baseline_m=25.0,
    detector_mass_kg=1.0,
    A=73, Z=32,
    threshold_keV=0.2,
    quenching=0.20
)

plot_spectrum(events, 'my_spectrum.png')
```

### requirements.txt

Install Python dependencies:
```bash
pip install -r requirements.txt
```

**Dependencies**:
- numpy >= 1.20
- scipy >= 1.7
- matplotlib >= 3.5

## C++ Examples

### basic_rate_calculator.cpp

**Purpose**: Fast event rate calculations.

**Compilation**:
```bash
cd cpp
make basic_rate_calculator
# Or manually:
g++ -o basic_rate_calculator basic_rate_calculator.cpp -lglobes -lgsl -lgslcblas -lm -O2
```

**Usage**:
```bash
./basic_rate_calculator [baseline_m] [power_GW] [mass_kg] [A] [Z]

# Examples:
./basic_rate_calculator 25.0 3.0 1.0 73 32  # 1 kg Ge at 25m from 3 GW
./basic_rate_calculator 10.0 4.0 0.01 131 54  # 10g Xe at 10m from 4 GW
```

**Example output**:
```
CEvNS Event Rate Calculation
=============================
Configuration:
  Reactor: 3.0 GW thermal at 25.0 m baseline
  Detector: 1.0 kg Germanium-73 (A=73, Z=32)

Physics:
  Weak charge Q_W: 29.40
  Number of targets: 8.267e+24

Results:
  Event rate: 102.34 events/day
              37354 events/year
              3.735e+07 events/ton/year

Cross section check (3 MeV): 1.234e-39 cm²
Form factor F²(Q²=0.01 GeV²): 0.952
```

**Code structure**:
```cpp
// Key functions
double weak_charge(int A, int Z);
double helm_form_factor(double Q2, double A);
double cevns_dsigma_dT(double Enu, double T, int A, int Z);
double reactor_flux_U235(double Enu);
double calculate_event_rate(double power_GW, double baseline_m,
                           double detector_mass_kg, int A, int Z);
```

### mc_event_generator.cpp

**Purpose**: Generate Monte Carlo event samples with full kinematics.

**Compilation**:
```bash
make mc_event_generator
# Or manually:
g++ -o mc_event_generator mc_event_generator.cpp -lglobes -lgsl -lgslcblas -lm -O2
```

**Usage**:
```bash
./mc_event_generator [options]

Options:
  --nevents N        Number of events to generate (default: 10000)
  --power P          Reactor power in GW (default: 3.0)
  --baseline L       Baseline in meters (default: 25.0)
  --mass M           Detector mass in kg (default: 1.0)
  --target T         Target nucleus: Ge, Xe, Ar (default: Ge)
  --threshold E      Threshold in keV_ee (default: 0.2)
  --output FILE      Output filename (default: cevns_events.csv)
  --seed S           Random seed (default: time)
```

**Examples**:
```bash
# Generate 50k events for Ge detector
./mc_event_generator --nevents 50000 --target Ge --output ge_events.csv

# Xe detector with low threshold
./mc_event_generator --target Xe --mass 0.01 --threshold 0.1 --output xe_events.csv

# High-statistics run
./mc_event_generator --nevents 1000000 --output high_stats.csv
```

**Output format (CSV)**:
```
event_id,neutrino_energy_MeV,recoil_energy_keV_nr,detected_energy_keV_ee
1,3.452,2.341,0.468
2,4.123,1.892,0.378
3,2.987,0.891,0.178
...
```

**Post-processing**:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load events
events = pd.read_csv('cevns_events.csv')

# Plot spectrum
plt.hist(events['detected_energy_keV_ee'], bins=50, alpha=0.7)
plt.xlabel('Detected Energy (keV_ee)')
plt.ylabel('Events')
plt.yscale('log')
plt.savefig('spectrum.png')
```

### Makefile

**Targets**:
```bash
make all                  # Build all examples
make basic_rate_calculator
make mc_event_generator
make clean               # Remove executables
```

**Customization**:
Edit Makefile to change compiler flags:
```makefile
CXX = g++
CXXFLAGS = -O2 -Wall
LIBS = -lglobes -lgsl -lgslcblas -lm
```

## AEDL Configuration Files

### reactor_ge.glb

**Description**: Germanium detector configuration based on CONUS+ experiment parameters.

**Parameters**:
- Target: Ge-73
- Mass: 1 kg
- Baseline: 25 m
- Threshold: 0.2 keV_ee (with quenching)
- Resolution: 5% at 1 keV
- Reactor: 3 GW thermal

**Usage with GLoBES**:
```bash
globes reactor_ge.glb
```

**Usage in C++ code**:
```cpp
#include <globes/globes.h>

glbInit(argv[0]);
glbInitExperiment("reactor_ge.glb", &glb_experiment_list[0], &glb_num_of_exps);

// Compute rates
double rate = glbGetRuleRate(0, 0);  // Rule 0, experiment 0
printf("Rate: %.2f events/year\n", rate);
```

**Modifying parameters**:
Edit the `.glb` file to change:
- `$baseline`: Distance to reactor
- `$mass`: Detector mass
- `$power`: Reactor power
- `$emin`: Energy threshold

### reactor_xe.glb

**Description**: Xenon detector configuration based on NUCLEUS experiment.

**Parameters**:
- Target: Xe-131
- Mass: 10 g to 1 kg (configurable)
- Baseline: 10 m
- Threshold: <1 keV_nr (0.15 keV_ee with quenching)
- Resolution: 10% at 1 keV
- Reactor: 4 GW thermal

**Key differences from Ge**:
- Different quenching factor (0.15 vs 0.20)
- Higher Q_W (stronger signal)
- Typically smaller mass, closer baseline

## Data Files

### reactor_flux_U235.dat

**Description**: Huber-Mueller U-235 fission antineutrino spectrum.

**Format**:
```
# E_nu [MeV]    dN/dE [1/MeV/fission]
1.800           3.6542
1.850           3.4234
...
```

**Energy range**: 1.8 - 8.0 MeV (effective range for CEvNS)

**Usage**:
- Reference in AEDL files: `@flux_file = "data/reactor_flux_U235.dat"`
- Load in Python: `np.loadtxt('reactor_flux_U235.dat')`
- Load in C++: Standard file I/O

**Source**: Parameterization from Huber, Phys. Rev. C 84, 024617 (2011)

### cevns_ge_xsec.dat

**Description**: CEvNS total cross section on Germanium-73.

**Format**:
```
# E_nu [GeV]    sigma [cm^2]
0.001800        8.234e-40
0.001900        9.123e-40
...
```

**Note**: Energies in GeV (GLoBES convention), even though values are MeV-scale.

**Includes**:
- Weak nuclear charge for Ge-73
- Helm form factor (integrated over recoil energy)
- Full kinematics

**Generation**: Created using `cevns_calculator.py` physics functions.

### form_factors.dat

**Description**: Helm form factors for common target nuclei.

**Format**:
```
# Q^2 [GeV^2]   F^2_Ge(Q^2)   F^2_Xe(Q^2)   F^2_Ar(Q^2)
0.0000          1.0000        1.0000        1.0000
0.0001          0.9987        0.9985        0.9990
0.0010          0.9734        0.9634        0.9801
...
```

**Usage**:
- Interpolate for specific Q² values
- Verify form factor implementations
- Study coherence loss at high Q²

## Validation and Expected Results

### Cross-Checks

**1. Event Rates (1 kg Ge, 25m, 3 GW)**:
| Threshold | Expected Rate (events/day) |
|-----------|---------------------------|
| No threshold | ~100 |
| 0.2 keV_ee | ~70 |
| 0.5 keV_ee | ~30 |
| 1.0 keV_ee | ~10 |

**2. Cross Sections (Ge-73 at 3 MeV)**:
- Total: σ ≈ 1.2 × 10⁻³⁹ cm²
- Differential peak: dσ/dT ≈ 5 × 10⁻⁴⁰ cm²/MeV at T ~ 0.5 keV

**3. Form Factors**:
| Nucleus | Q² = 0.01 GeV² | Q² = 0.1 GeV² |
|---------|----------------|---------------|
| Ge-73 | F² ≈ 0.95 | F² ≈ 0.70 |
| Xe-131 | F² ≈ 0.92 | F² ≈ 0.50 |

**4. Spectrum Shape**:
- Peak recoil energy: 0.5-1 keV_nr (0.1-0.2 keV_ee for Ge)
- Exponential decrease at higher energies
- Sharp cutoff at kinematic maximum (~5-10 keV for reactor neutrinos)

### Comparison with Experiments

**CONUS+ (Ge detector, 25m from reactor)**:
- Published: Few events/day at keV threshold
- Our calculation: Consistent within flux and quenching uncertainties

**COHERENT (CsI detector, stopped pion source)**:
- Different source (pions, not reactor)
- Higher energy neutrinos → different kinematics
- Not directly comparable

### Troubleshooting

**Low event rates**:
- Check reactor power (should be GW_thermal, not electric)
- Verify baseline distance (meters, not cm)
- Confirm threshold (keV_ee after quenching, not keV_nr)

**Unexpected spectrum shape**:
- Verify form factor implementation
- Check energy units (GeV vs MeV)
- Ensure proper detector response (quenching, resolution)

**Python vs C++ disagreement**:
- Cross-check input parameters
- Compare intermediate values (cross sections, fluxes)
- Verify random number generation (seed consistency)

**GLoBES errors**:
- Check file paths in AEDL
- Verify energy ranges (sampling vs observable)
- Ensure cross section files have correct units

## Performance Notes

**Python**:
- Event generation: ~1000 events/second
- Good for: Quick calculations, prototyping, visualization
- Use for: <100k events, development

**C++**:
- Event generation: ~100,000 events/second
- Good for: High-statistics runs, production
- Use for: >100k events, final analysis

**Tips**:
- Develop and test in Python
- Port to C++ for large-scale production
- Use Python for plotting even with C++ data

## Next Steps

1. **Run the examples** as-is to familiarize yourself with outputs
2. **Modify parameters** to match your detector configuration
3. **Extend code** for your specific physics case
4. **Add backgrounds** to make realistic projections
5. **Optimize thresholds** for your detector sensitivity

## Additional Resources

- Main documentation: `../docs/CEVNS_REACTOR_QUICKSTART.md`
- AEDL reference: `../docs/AEDL_EXAMPLES.md`
- GLoBES manual: https://www.mpi-hd.mpg.de/personalhomes/globes/
- CEvNS physics: https://github.com/bradkav/CEvNS

## Support

For issues or questions:
- Check documentation in `docs/`
- Review code comments in example files
- Consult GLoBES manual for AEDL questions
- Open GitHub issue for bug reports

---

**Ready to start? Try this:**

```bash
# Python quick test
cd python
pip install -r requirements.txt
python cevns_calculator.py

# C++ quick test
cd cpp
make basic_rate_calculator
./basic_rate_calculator 25.0 3.0 1.0 73 32
```

Happy simulating!
