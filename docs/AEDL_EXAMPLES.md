# AEDL Configuration Reference for Reactor CEvNS

## Table of Contents
1. [AEDL Basics](#aedl-basics)
2. [Reactor Flux Configuration](#reactor-flux-configuration)
3. [Cross Section Definition](#cross-section-definition)
4. [Detector Configuration](#detector-configuration)
5. [Energy Settings and Smearing](#energy-settings-and-smearing)
6. [Channel Definitions](#channel-definitions)
7. [Rule Definitions](#rule-definitions)
8. [Complete Working Examples](#complete-working-examples)
9. [Common Patterns](#common-patterns)

## AEDL Basics

### What is AEDL?

AEDL (Abstract Experiment Definition Language) is GLoBES' configuration file format. It defines:
- Neutrino fluxes
- Cross sections
- Detector properties
- Energy resolution and efficiencies
- Analysis channels and rules

### File Structure

A typical AEDL file consists of blocks with this syntax:

```
block_type(#block_name)<
  @parameter1 = value1
  @parameter2 = value2
  /* Comments */
>
```

### Comments and Includes

```
/* Multi-line comment
   using C-style syntax */

// Single-line comment (C++ style also works)

/* Include other AEDL files */
%include "common_definitions.glb"
```

### Variable Definitions

Define variables for reuse:

```
$baseline = 25.0      /* meters */
$detector_mass = 1.0  /* kg */
$reactor_power = 3.0  /* GW thermal */
```

## Reactor Flux Configuration

### Basic Flux Definition

```
nuflux(#reactor_flux)<
  @flux_file = "data/reactor_flux_U235.dat"
  @time = YEARS
  @power = 3.0
  @norm = 1.0
>
```

**Parameters**:
- **@flux_file**: Path to flux data file (relative to AEDL file)
- **@time**: Time unit (YEARS, DAYS, SECONDS)
- **@power**: Normalization factor (typically reactor power in GW)
- **@norm**: Additional normalization multiplier

### Flux File Format

The flux file should contain energy (MeV) and flux values:

```
# reactor_flux_U235.dat
# E_nu [MeV]    dN/dE [1/MeV/fission]
1.800           3.654
1.850           3.423
1.900           3.207
...
7.950           0.00345
8.000           0.00287
```

### Built-in Flux

GLoBES has some built-in fluxes, but they're designed for long-baseline experiments:

```
nuflux(#builtin_reactor)<
  @builtin = 2          /* Reactor neutrinos (may not be accurate) */
  @time = YEARS
  @power = $reactor_power
  @norm = 1.0
>
```

**Note**: For reactor CEvNS, always use custom flux files with Huber-Mueller spectra.

### Distance Scaling

Flux automatically scales with distance (inverse square law):

```
$baseline = 25.0  /* meters */

nuflux(#reactor_flux)<
  @flux_file = "reactor_flux.dat"
  @time = YEARS
  @power = 3.0
  @norm = 1.0
  @distance = $baseline  /* Flux ∝ 1/distance² */
>
```

## Cross Section Definition

### Custom Cross Section File

CEvNS requires custom cross sections (not built into GLoBES):

```
cross(#cevns_ge)<
  @cross_file = "data/cevns_ge_xsec.dat"
>
```

### Cross Section File Format

Energy-dependent cross section:

```
# cevns_ge_xsec.dat
# E_nu [GeV]    sigma [cm^2]
0.001800        8.234e-40
0.001900        9.123e-40
0.002000        1.012e-39
...
0.007900        5.678e-39
0.008000        5.234e-39
```

**Units**:
- Energy: GeV (even though reactor neutrinos are MeV-scale!)
- Cross section: cm²

### Generating Cross Section Files

Use the Python or C++ examples to generate these files:

```python
import numpy as np

E_nu_array = np.linspace(1.8, 8.0, 100) / 1000  # Convert MeV to GeV
sigma_array = np.array([
    integrate_dsigma_dT(E_nu, A=73, Z=32) for E_nu in E_nu_array
])

np.savetxt('cevns_ge_xsec.dat',
           np.column_stack([E_nu_array, sigma_array]),
           header='E_nu[GeV] sigma[cm^2]',
           fmt='%.6e')
```

## Detector Configuration

### Energy Binning

Define the observable energy range and binning:

```
$emin =  0.0001   /* GeV = 0.1 keV (after quenching) */
$emax =  0.010    /* GeV = 10 keV */
$bins =  100      /* Number of energy bins */
```

**Important**: These energies are in GeV and represent the observable (quenched) energies, not nuclear recoil energies.

### Sampling Settings

For accurate cross section integration:

```
$sampling_min =  0.0018  /* GeV = 1.8 MeV (neutrino energy) */
$sampling_max =  0.008   /* GeV = 8 MeV */
$sampling_points = 1000  /* Number of points for integration */
```

These define the neutrino energy range for flux × cross section integration.

### Detector Mass and Geometry

```
detector(#reactor_detector)<
  @target_mass = 1.0          /* kg */
  @target_power = 1.0          /* Unused for CEvNS */
  @target_norm = 1.0           /* Additional normalization */
  @energy_window = {$emin, $emax}
>
```

### Detection Efficiency

Energy-dependent efficiency can be defined:

```
detector(#reactor_detector)<
  @target_mass = 1.0
  @pre_smearing_efficiencies = {1.0}     /* Before energy resolution */
  @post_smearing_efficiencies = #eff     /* After energy resolution */
  @energy_window = {$emin, $emax}
>

/* Efficiency function */
energy(#eff)<
  @energy = {0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.010}  /* GeV */
  @pre_smearing_efficiency = {0.0, 0.3, 0.7, 0.9, 0.95, 1.0}
>
```

This creates a step function for efficiency vs energy (e.g., threshold turn-on).

## Energy Settings and Smearing

### Gaussian Energy Resolution

```
energy(#ERES)<
  @type = 1                     /* 1 = Gaussian */
  @sigma_function = #sigma_expr
>

energy(#sigma_expr)<
  @expression = 0.05*sqrt(E)    /* 5% at 1 keV, improves with √E */
>
```

**Expression syntax**:
- `E`: Energy variable (in GeV)
- `sqrt(E)`: Square root
- Standard operators: `+`, `-`, `*`, `/`, `^`

### Energy-Dependent Resolution Examples

**Constant absolute resolution**:
```
@expression = 0.0001  /* 0.1 keV constant */
```

**Constant fractional resolution**:
```
@expression = 0.05*E  /* 5% at all energies */
```

**Combined resolution**:
```
@expression = sqrt((0.0001)^2 + (0.05*sqrt(E))^2)
```
This combines electronic noise (constant) with statistical fluctuations (√E).

### No Smearing

```
energy(#NO_SMEARING)<
  @type = 0  /* No energy smearing */
>
```

## Channel Definitions

### Basic Channel

A channel connects flux, cross section, and detector:

```
channel(#cevns_signal)<
  @channel = #reactor_flux : + : e : e : #cevns_ge : #reactor_detector
  @pre_smearing_efficiencies = {1.0}
  @post_smearing_efficiencies = {0.8}  /* Overall detection efficiency */
>
```

**Channel syntax breakdown**:
```
@channel = #flux : sign : initial_flavor : final_flavor : #xsec : #detector
```

- **#flux**: Flux definition name
- **sign**: `+` for neutrinos, `-` for antineutrinos
- **initial_flavor**: `e`, `m`, or `t` (electron, muon, tau)
- **final_flavor**: Same for CEvNS (no flavor change)
- **#xsec**: Cross section name
- **#detector**: Detector name

### Important for CEvNS

Since CEvNS is flavor-blind, you might want to sum over initial flavors if your reactor has multiple components:

```
/* Electron antineutrinos (dominant from reactor) */
channel(#cevns_nue)<
  @channel = #reactor_flux : + : e : e : #cevns_ge : #reactor_detector
>

/* If reactor had other flavors (oscillations, etc.) */
channel(#cevns_numu)<
  @channel = #reactor_flux : + : m : m : #cevns_ge : #reactor_detector
>
```

### Background Channels

Define backgrounds similarly:

```
nuflux(#flat_background)<
  @builtin = 5  /* Flat spectrum */
  @power = 0.1  /* events/day/keV */
  @norm = 1.0
>

channel(#background)<
  @channel = #flat_background : + : e : e : #cevns_ge : #reactor_detector
  @pre_smearing_efficiencies = {1.0}
  @post_smearing_efficiencies = {1.0}
>
```

## Rule Definitions

### Basic Rule

Rules define how channels combine for analysis:

```
rule(#CEvNS_Rule)<
  @signal = 1.0@#cevns_signal
  @signalerror = 0.02 : 0.0  /* 2% normalization error, no tilt */

  @background = 0.1@#background
  @backgrounderror = 0.10 : 0.0  /* 10% background error */

  @sys_on_function = "chiSpectrumTilt"
  @sys_off_function = "chiNoSysSpectrum"

  @energy_window = {$emin, $emax}
>
```

**Parameters**:
- **@signal**: Signal channel(s) with coefficients
- **@signalerror**: Normalization : spectral tilt error
- **@background**: Background channel(s)
- **@backgrounderror**: Background uncertainties
- **@sys_on_function**: Chi-squared function with systematics
- **@sys_off_function**: Chi-squared function without systematics

### Multiple Channels in a Rule

```
rule(#CEvNS_Total)<
  @signal = 1.0@#cevns_nue + 0.05@#cevns_numu  /* νe dominant */
  @background = 1.0@#ambient_bg + 0.5@#reactor_correlated_bg
  @signalerror = 0.02 : 0.0
  @backgrounderror = 0.15 : 0.0
  @sys_on_function = "chiSpectrumTilt"
  @sys_off_function = "chiNoSysSpectrum"
  @energy_window = {$emin, $emax}
>
```

### Chi-Squared Functions

GLoBES provides built-in chi-squared functions:

- **chiNoSysSpectrum**: No systematics, Poisson statistics only
- **chiSpectrumTilt**: Allows normalization and spectral tilt errors
- **chiSpectrumCalib**: Includes energy calibration uncertainty
- **chiTotalRatesTilt**: Adds rate-only information

For most reactor CEvNS:
```
@sys_on_function = "chiSpectrumTilt"  /* Include flux uncertainties */
@sys_off_function = "chiNoSysSpectrum"  /* For comparison */
```

## Complete Working Examples

### Example 1: Minimal Germanium Detector

```
/* ================================================================
   Reactor CEvNS on Germanium Detector - Minimal Configuration
   ================================================================ */

/* Energy ranges */
$emin = 0.0002  /* 0.2 keV electron equivalent */
$emax = 0.010   /* 10 keV */
$bins = 50

$sampling_min = 0.0018  /* 1.8 MeV neutrino energy */
$sampling_max = 0.008   /* 8 MeV */
$sampling_points = 500

/* Detector parameters */
$baseline = 25.0    /* meters */
$mass = 1.0         /* kg */
$power = 3.0        /* GW thermal */

/* Reactor flux */
nuflux(#reactor_flux_U235)<
  @flux_file = "../data/reactor_flux_U235.dat"
  @time = YEARS
  @power = $power
  @norm = 1.0
  @distance = $baseline
>

/* CEvNS cross section on Ge-73 */
cross(#cevns_ge73)<
  @cross_file = "../data/cevns_ge_xsec.dat"
>

/* Detector */
detector(#ge_detector)<
  @target_mass = $mass
  @energy_window = {$emin, $emax}
>

/* Energy resolution: 5% at 1 keV, scales with √E */
energy(#ge_resolution)<
  @type = 1
  @sigma_function = #sigma_ge
>

energy(#sigma_ge)<
  @expression = 0.05*sqrt(E*1000)*0.001  /* Convert to GeV */
>

/* Signal channel */
channel(#signal_cevns)<
  @channel = #reactor_flux_U235 : + : e : e : #cevns_ge73 : #ge_detector
  @pre_smearing_efficiencies = {1.0}
  @post_smearing_efficiencies = {0.9}  /* 90% efficiency */
>

/* Analysis rule */
rule(#CEvNS_Simple)<
  @signal = 1.0@#signal_cevns
  @signalerror = 0.025 : 0.0  /* 2.5% flux uncertainty */
  @background = 0.0@#signal_cevns  /* No background for now */
  @sys_on_function = "chiSpectrumTilt"
  @sys_off_function = "chiNoSysSpectrum"
  @energy_window = {$emin, $emax}
>
```

### Example 2: Ge Detector with Background

```
/* ================================================================
   Reactor CEvNS with Background
   ================================================================ */

$emin = 0.0002
$emax = 0.010
$bins = 50

$sampling_min = 0.0018
$sampling_max = 0.008
$sampling_points = 500

$baseline = 25.0
$mass = 1.0
$power = 3.0

/* Reactor flux */
nuflux(#reactor_flux)<
  @flux_file = "../data/reactor_flux_U235.dat"
  @time = YEARS
  @power = $power
  @norm = 1.0
  @distance = $baseline
>

/* Flat background (simplified) */
nuflux(#flat_bg_flux)<
  @builtin = 5  /* Flat spectrum */
  @power = 0.05  /* Arbitrary normalization */
  @norm = 1.0
>

/* Cross sections */
cross(#cevns_ge73)<
  @cross_file = "../data/cevns_ge_xsec.dat"
>

/* Use dummy cross section for background */
cross(#background_xsec)<
  @cross_file = "../data/cevns_ge_xsec.dat"  /* Reuse, shape doesn't matter much */
>

/* Detector */
detector(#ge_detector)<
  @target_mass = $mass
  @energy_window = {$emin, $emax}
>

/* Energy resolution */
energy(#ge_resolution)<
  @type = 1
  @sigma_function = #sigma_ge
>

energy(#sigma_ge)<
  @expression = 0.05*sqrt(E*1000)*0.001
>

/* Signal channel */
channel(#signal)<
  @channel = #reactor_flux : + : e : e : #cevns_ge73 : #ge_detector
  @pre_smearing_efficiencies = {1.0}
  @post_smearing_efficiencies = {0.9}
>

/* Background channel */
channel(#background)<
  @channel = #flat_bg_flux : + : e : e : #background_xsec : #ge_detector
  @pre_smearing_efficiencies = {1.0}
  @post_smearing_efficiencies = {1.0}
>

/* Analysis rule with background */
rule(#CEvNS_WithBG)<
  @signal = 1.0@#signal
  @signalerror = 0.025 : 0.0  /* 2.5% signal systematic */

  @background = 1.0@#background
  @backgrounderror = 0.15 : 0.0  /* 15% background uncertainty */

  @sys_on_function = "chiSpectrumTilt"
  @sys_off_function = "chiNoSysSpectrum"
  @energy_window = {$emin, $emax}
>
```

### Example 3: Xenon Detector with Threshold Turn-On

```
/* ================================================================
   Reactor CEvNS on Xenon with Realistic Efficiency
   ================================================================ */

$emin = 0.0001  /* 0.1 keV */
$emax = 0.005   /* 5 keV */
$bins = 50

$sampling_min = 0.0018
$sampling_max = 0.008
$sampling_points = 500

$baseline = 10.0  /* Closer to reactor */
$mass = 0.010     /* 10 g fiducial */
$power = 4.0      /* 4 GW reactor */

/* Reactor flux */
nuflux(#reactor_flux)<
  @flux_file = "../data/reactor_flux_U235.dat"
  @time = YEARS
  @power = $power
  @norm = 1.0
  @distance = $baseline
>

/* CEvNS on Xe-131 */
cross(#cevns_xe131)<
  @cross_file = "../data/cevns_xe_xsec.dat"
>

/* Detector with efficiency function */
detector(#xe_detector)<
  @target_mass = $mass
  @post_smearing_efficiencies = #xe_efficiency
  @energy_window = {$emin, $emax}
>

/* Energy-dependent efficiency (threshold turn-on) */
energy(#xe_efficiency)<
  @energy = {0.0000, 0.0001, 0.00015, 0.0002, 0.0003, 0.005}  /* GeV */
  @post_smearing_efficiency = {0.0, 0.1, 0.5, 0.8, 0.95, 0.95}
>

/* Energy resolution */
energy(#xe_resolution)<
  @type = 1
  @sigma_function = #sigma_xe
>

energy(#sigma_xe)<
  @expression = 0.10*sqrt(E*1000)*0.001  /* 10% resolution at 1 keV */
>

/* Signal channel */
channel(#signal_xe)<
  @channel = #reactor_flux : + : e : e : #cevns_xe131 : #xe_detector
  @pre_smearing_efficiencies = {1.0}
>

/* Analysis rule */
rule(#CEvNS_Xe)<
  @signal = 1.0@#signal_xe
  @signalerror = 0.03 : 0.0  /* 3% flux uncertainty */
  @background = 0.0@#signal_xe
  @sys_on_function = "chiSpectrumTilt"
  @sys_off_function = "chiNoSysSpectrum"
  @energy_window = {$emin, $emax}
>
```

## Common Patterns

### Multi-Isotope Flux

Combine fluxes from different fission isotopes:

```
nuflux(#flux_U235)<
  @flux_file = "../data/reactor_flux_U235.dat"
  @time = YEARS
  @power = 3.0
  @norm = 0.56  /* U-235 fraction */
  @distance = 25.0
>

nuflux(#flux_Pu239)<
  @flux_file = "../data/reactor_flux_Pu239.dat"
  @time = YEARS
  @power = 3.0
  @norm = 0.30  /* Pu-239 fraction */
  @distance = 25.0
>

/* Combined in channel */
channel(#signal_combined)<
  @channel = #flux_U235 : + : e : e : #cevns_ge : #detector
  ...
>

channel(#signal_combined_Pu)<
  @channel = #flux_Pu239 : + : e : e : #cevns_ge : #detector
  ...
>

rule(#Combined)<
  @signal = 1.0@#signal_combined + 1.0@#signal_combined_Pu
  ...
>
```

### Near/Far Detector Setup

```
$baseline_near = 10.0
$baseline_far = 100.0

detector(#near_detector)<
  @target_mass = 0.1
  @energy_window = {$emin, $emax}
>

detector(#far_detector)<
  @target_mass = 1.0
  @energy_window = {$emin, $emax}
>

nuflux(#flux_near)<
  @flux_file = "../data/reactor_flux.dat"
  @distance = $baseline_near
  ...
>

nuflux(#flux_far)<
  @flux_file = "../data/reactor_flux.dat"
  @distance = $baseline_far
  ...
>

channel(#near_signal)<
  @channel = #flux_near : + : e : e : #cevns_xsec : #near_detector
>

channel(#far_signal)<
  @channel = #flux_far : + : e : e : #cevns_xsec : #far_detector
>

/* Separate rules or combined analysis */
rule(#Near_Analysis)<
  @signal = 1.0@#near_signal
  ...
>

rule(#Far_Analysis)<
  @signal = 1.0@#far_signal
  ...
>
```

### Varying Threshold

To study sensitivity vs threshold, create multiple configurations:

```
/* Low threshold */
$emin_low = 0.0001
rule(#Low_Threshold)<
  @signal = 1.0@#signal
  @energy_window = {$emin_low, $emax}
  ...
>

/* Medium threshold */
$emin_med = 0.0005
rule(#Med_Threshold)<
  @signal = 1.0@#signal
  @energy_window = {$emin_med, $emax}
  ...
>

/* High threshold */
$emin_high = 0.001
rule(#High_Threshold)<
  @signal = 1.0@#signal
  @energy_window = {$emin_high, $emax}
  ...
>
```

Then in your C++ code, loop over rules to compute rates for each threshold.

### Time-Varying Flux (Reactor On/Off)

```
/* Reactor on */
nuflux(#reactor_on)<
  @flux_file = "../data/reactor_flux.dat"
  @time = DAYS
  @power = 3.0
  @norm = 1.0  /* Full flux */
  @distance = 25.0
>

/* Reactor off (background only) */
nuflux(#reactor_off)<
  @flux_file = "../data/reactor_flux.dat"
  @time = DAYS
  @power = 3.0
  @norm = 0.0  /* Zero flux */
  @distance = 25.0
>

/* Or use separate experiments */
/* reactor_on.glb and reactor_off.glb */
```

In analysis, subtract reactor-off spectrum from reactor-on to isolate CEvNS signal.

## Tips and Troubleshooting

### Common Mistakes

1. **Wrong units**: Energies must be in GeV in AEDL files, even though reactor neutrinos are MeV-scale
2. **Missing files**: Flux and cross section files must exist at specified paths
3. **Sampling range**: `sampling_min/max` should cover neutrino energies, not recoil energies
4. **Flavor matching**: For CEvNS, initial and final flavors are the same

### Validation

After writing an AEDL file:

1. **Syntax check**:
   ```bash
   globes your_file.glb
   ```
   GLoBES will report parsing errors.

2. **Physical reasonableness**:
   - Check event rates match expectations (~10-100/day for kg-scale Ge)
   - Verify energy spectrum peaks at ~0.5-1 keV
   - Ensure form factor suppression at high energies

3. **Compare implementations**:
   - Cross-check with standalone Python/C++ calculations
   - Verify against published experimental results

### Debugging

If GLoBES gives unexpected results:

- Print intermediate values in your C++ code using `glbGetRuleRatePtr()`
- Check flux normalization with `glbFlux()` function
- Verify cross section loading with `glbCrossSection()` function
- Compare energy bins: `glbGetBinCenters()` and `glbGetBinSizes()`

## Further Reading

- **GLoBES Manual**: Complete AEDL syntax reference
  - https://www.mpi-hd.mpg.de/personalhomes/globes/documentation/globes-manual-3.0.8.pdf
- **Example AEDL files**: Check GLoBES distribution for oscillation experiment examples
- **Custom functions**: GLoBES allows user-defined systematic functions in C

---

For complete working AEDL files, see `examples/aedl/reactor_ge.glb` and `reactor_xe.glb`.

For questions about implementing specific features, consult the GLoBES manual or ask on the GLoBES mailing list.
