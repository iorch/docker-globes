# CEvNS Reactor Monte Carlo Quick-Start Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Quick Physics Overview](#quick-physics-overview)
3. [Docker Setup](#docker-setup)
4. [CEvNS Monte Carlo Workflow](#cevns-monte-carlo-workflow)
5. [C++ Implementation](#c-implementation)
6. [Python Implementation](#python-implementation)
7. [Key Parameters for Reactor CEvNS](#key-parameters-for-reactor-cevns)
8. [Running the Examples](#running-the-examples)
9. [Next Steps and Resources](#next-steps-and-resources)

## Introduction

### What is CEvNS?

Coherent Elastic Neutrino-Nucleus Scattering (CEvNS) is a Standard Model process where neutrinos scatter coherently off entire atomic nuclei rather than individual nucleons. First observed by the COHERENT collaboration in 2017, CEvNS has important implications for:

- Neutrino physics and detector technology
- Supernova detection
- Dark matter searches
- Nuclear reactor monitoring

### Reactor-Based CEvNS Detection

Nuclear reactors are intense sources of electron antineutrinos from fission, producing:
- ~6 antineutrinos per fission
- Typical flux: ~10²¹ ν/s per GW thermal power
- Energy spectrum: 1-10 MeV (peak at 3-4 MeV)
- Baseline: typically 10-100 meters from reactor core

Reactor-based CEvNS experiments (CONUS+, NUCLEUS, CONNIE) offer advantages:
- High neutrino flux
- Well-understood source
- Reactor on/off cycles for background discrimination
- Opportunity to test detector technologies at low threshold

### Why GLoBES?

GLoBES (General Long Baseline Experiment Simulator) is a powerful framework for neutrino physics simulations. While originally designed for oscillation experiments, it provides useful infrastructure for CEvNS:

**Advantages**:
- Systematic flux and cross section handling
- Built-in statistical analysis tools
- Flexible detector configuration
- Community-tested code base

**Limitations**:
- Designed for flavor-change processes (oscillations)
- CEvNS is neutral-current (no flavor change)
- Requires custom cross sections and workarounds

This guide shows practical approaches to leverage GLoBES for reactor CEvNS simulations while addressing its limitations.

### Prerequisites

- Basic understanding of neutrino physics
- Familiarity with C++ or Python programming
- Docker installed on your system
- Background in Monte Carlo methods helpful but not required

## Quick Physics Overview

### CEvNS Cross Section

The CEvNS differential cross section for a neutrino of energy E_ν producing nuclear recoil energy T is:

```
dσ/dT = (G_F² M_A)/(4π) · Q_W² · F²(Q²) · [1 - (M_A T)/(2 E_ν²)]
```

Where:
- **G_F = 1.1663787 × 10⁻⁵ GeV⁻²**: Fermi constant
- **M_A**: Nuclear mass
- **Q_W = N - Z(1 - 4sin²θ_W)**: Weak nuclear charge
  - N = number of neutrons
  - Z = atomic number
  - sin²θ_W ≈ 0.231: weak mixing angle
- **F(Q²)**: Nuclear form factor (accounts for finite nuclear size)
- **Q² = 2M_A T**: Momentum transfer squared
- **T**: Nuclear recoil energy

**Key feature**: The cross section scales as Q_W² ∝ N², providing coherent enhancement for heavy nuclei.

### Coherent Enhancement

For typical nuclei (Q_W = N − Z(1 − 4·sin²θ_W), sin²θ_W = 0.23121):
- **Germanium-73** (A=73, Z=32): Q_W ≈ 38.6, σ ∝ 1490
- **Xenon-131** (A=131, Z=54): Q_W ≈ 72.9, σ ∝ 5320
- **Argon-40** (A=40, Z=18): Q_W ≈ 20.6, σ ∝ 426
- **Cesium-133** (A=133, Z=55): Q_W ≈ 73.9, σ ∝ 5457

This N² scaling makes CEvNS favorable for heavy target materials.

### Nuclear Form Factors

The form factor F(Q²) accounts for loss of coherence at high momentum transfer. The Helm parameterization is commonly used:

```
F(Q²) = 3 j₁(qR_A)/(qR_A) · exp(-(qs)²/2)
```

Where:
- **j₁**: Spherical Bessel function of order 1
- **q = √(2M_A T)**: Momentum transfer
- **R_A = √(R₀² - 5s²)**: Effective nuclear radius
- **R₀ = 1.2 A^(1/3) fm**: Nuclear size parameter
- **s ≈ 0.9 fm**: Nuclear skin thickness

Form factor suppression becomes important when Q² > 1/(R_A)², corresponding to recoil energies T > few keV for heavy nuclei.

### Reactor Antineutrino Flux

Nuclear reactor cores produce electron antineutrinos from fission of four main isotopes:

| Isotope | Energy/fission | ν per fission | Typical fraction |
|---------|---------------|---------------|-----------------|
| ²³⁵U | 202.36 MeV | 6.17 | 0.56 |
| ²³⁸U | 205.99 MeV | 6.69 | 0.08 |
| ²³⁹Pu | 211.12 MeV | 5.98 | 0.30 |
| ²⁴¹Pu | 214.26 MeV | 6.22 | 0.06 |

**Flux calculation**:
1. Fission rate: F = P_thermal / (200 MeV per fission) ≈ 3.12×10¹⁹ fissions/s/GW
2. Antineutrino production: N_ν = F × 6 ≈ 1.87×10²⁰ ν/s/GW
3. Flux at distance L: φ(L) = N_ν / (4πL²)

**Energy spectrum**: The Huber-Mueller model provides parameterized fission spectra for each isotope. The combined spectrum is:

```
Φ(E_ν) = Σᵢ fᵢ · Φᵢ(E_ν)
```

where fᵢ are the fission fractions and Φᵢ(E_ν) are individual isotope spectra.

### Nuclear Recoil Energy Range

For reactor antineutrinos (E_ν ~ 1-10 MeV) scattering on typical nuclei:

- **Maximum recoil energy**: T_max = 2E_ν² / (M_A + 2E_ν) ≈ few keV
- **Typical range**: 0.1 - 10 keV nuclear recoil
- **After quenching**: 0.02 - 2 keV electron equivalent (detector-dependent)

This requires ultra-low threshold detectors, which is a major experimental challenge.

### Detector Response

Converting nuclear recoils to observable signals involves several effects:

1. **Quenching factor** (q): Not all recoil energy produces detectable signal
   - Germanium: q ≈ 0.20
   - Xenon (liquid): q ≈ 0.15
   - Argon (liquid): q ≈ 0.23
   - Observable energy: E_obs = q × T_recoil

2. **Energy threshold** (E_th): Minimum detectable energy
   - Current best: ~0.2 keV electron equivalent
   - Future goal: <0.1 keV

3. **Energy resolution** (σ_E): Gaussian smearing
   - Typical: σ_E/E ~ 5-10% at 1 keV
   - Can be energy-dependent: σ(E) = a√E + bE

4. **Detection efficiency** (ε(E)): Energy-dependent acceptance
   - Turn-on curve near threshold
   - Analysis cuts and triggers

## Docker Setup

### Building the Container

From the `docker-globes` repository root:

```bash
# Build the Docker image
docker build -t docker-globes .

# This will:
# - Start from gcc:12.1.0-bullseye base
# - Install libgsl-dev (GNU Scientific Library)
# - Download GLoBES 3.2.18 source
# - Compile and install GLoBES
```

Build time: ~5-10 minutes depending on your system.

### Running the Container

Create a workspace directory for your simulations:

```bash
# Create local workspace
mkdir -p workspace
cd workspace

# Run container with workspace mounted
docker run -it -v $(pwd):/workspace docker-globes /bin/bash

# Inside container, you'll have:
# - GLoBES installed (/usr/local/bin/globes, /usr/local/lib/libglobes.*)
# - GCC compiler
# - GSL libraries
# - All standard build tools
```

### Verifying Installation

Inside the container:

```bash
# Check GLoBES installation
globes --version
# Expected: globes 3.2.18

# Check libraries
ldconfig -p | grep globes
# Should show libglobes.so entries

# Check GSL
pkg-config --modversion gsl
# Expected: 2.6 or similar
```

### Working with Files

The `/workspace` directory in the container is mounted to your local `workspace/` directory:
- Files created in the container appear on your host system
- Edit files on host with your favorite editor
- Run simulations in container
- Results automatically available on host

## CEvNS Monte Carlo Workflow

A complete CEvNS Monte Carlo simulation follows these steps:

### Step 1: Define Reactor Source

**Inputs**:
- Reactor thermal power (P_th in GW)
- Fission isotope composition (f_U235, f_U238, f_Pu239, f_Pu241)
- Baseline distance (L in meters)
- Reactor operation time (T in days/years)

**Outputs**:
- Antineutrino flux at detector: φ(E_ν, L)
- Total integrated flux

### Step 2: Calculate CEvNS Cross Sections

**Inputs**:
- Target nucleus (A, Z)
- Neutrino energy grid (E_ν from 1-10 MeV)
- Form factor parameterization

**Computation**:
- Weak nuclear charge: Q_W(A, Z)
- Form factor: F(Q²) for each (E_ν, T_recoil) pair
- Differential cross section: dσ/dT(E_ν, T)
- Total cross section: σ_total(E_ν) = ∫ (dσ/dT) dT

**Outputs**:
- Cross section table: σ(E_ν)
- Differential cross section: dσ/dT(E_ν, T)

### Step 3: Calculate Event Rate

**Formula**:
```
R = N_targets · ∫ φ(E_ν) · σ(E_ν) · ε(E_ν) dE_ν
```

Where:
- **N_targets** = (m_detector / M_A) × N_A
  - m_detector: detector mass
  - M_A: nuclear mass
  - N_A: Avogadro's number
- **ε(E_ν)**: Detection efficiency

**Outputs**:
- Total event rate (events/day or events/kg/day)
- Rate as function of threshold

### Step 4: Generate Recoil Spectrum

**Monte Carlo sampling**:

For each event i = 1, ..., N_events:

1. **Sample neutrino energy**: E_ν ~ φ(E_ν)
   - Use inverse transform sampling or acceptance-rejection
   - Weight by flux × cross section

2. **Sample recoil energy**: T ~ dσ/dT(E_ν, T)
   - For given E_ν, sample from recoil distribution
   - Include form factor suppression

3. **Apply detector response**:
   - Quenching: E_obs = q × T
   - Resolution: E_det ~ Gaussian(E_obs, σ(E_obs))
   - Threshold cut: accept if E_det > E_th
   - Efficiency: accept with probability ε(E_det)

**Outputs**:
- List of detected recoil energies
- Histogram: dN/dE_recoil

### Step 5: Statistical Analysis

**Signal and background**:
- Signal: S = N_CEvNS (from Step 4)
- Background: B = known background rate × exposure
- Statistical significance: σ = S / √(S + B)

**Systematic uncertainties**:
- Flux normalization: δφ/φ ~ 2-5%
- Cross section: δσ/σ ~ 1%
- Detector response: detector-specific
- Quenching factor: δq/q ~ 5-10%

**Sensitivity projections**:
- Vary parameters (mass, threshold, baseline)
- Calculate required exposure for N-sigma detection
- Optimize detector configuration

## C++ Implementation

### Basic Structure

A minimal C++ program using GLoBES:

```cpp
#include <iostream>
#include <cmath>
#include <globes/globes.h>
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

int main(int argc, char *argv[]) {
    // Initialize GLoBES
    glbInit(argv[0]);

    // Load experiment definition (if using AEDL)
    // glbInitExperiment("reactor_cevns.glb", &glb_experiment_list[0], &glb_num_of_exps);

    // Your simulation code here

    // Cleanup
    glbFreeParams(true_values);
    glbFreeParams(test_values);

    return 0;
}
```

### Event Rate Calculation Example

Calculate total CEvNS event rate for a detector:

```cpp
#include <iostream>
#include <cmath>
#include <gsl/gsl_integration.h>

// Physical constants
const double GF = 1.1663787e-5;  // GeV^-2, Fermi constant
const double SIN2TW = 0.23121;   // sin^2(theta_W)
const double HBARC = 0.1973;     // GeV fm
const double MEV_TO_GEV = 0.001;
const double CM2_TO_GEV2 = 2.568e-31;

// Calculate weak nuclear charge
double weak_charge(int A, int Z) {
    int N = A - Z;
    return N - Z * (1.0 - 4.0 * SIN2TW);
}

// Helm form factor
double helm_form_factor(double Q2, double A) {
    double R0 = 1.2 * std::pow(A, 1.0/3.0);  // fm
    double s = 0.9;  // fm
    double RA = std::sqrt(R0*R0 - 5.0*s*s);

    double q = std::sqrt(Q2) / HBARC;  // Convert to fm^-1
    double qRA = q * RA;
    double qs = q * s;

    // j1(x)/x = (sin(x)/x - cos(x))/x for spherical Bessel function
    double j1_over_qRA;
    if (qRA < 0.01) {
        j1_over_qRA = 1.0/3.0 - qRA*qRA/30.0;  // Taylor expansion
    } else {
        j1_over_qRA = (std::sin(qRA)/qRA - std::cos(qRA)) / qRA;
    }

    double F = 3.0 * j1_over_qRA * std::exp(-qs*qs/2.0);
    return F * F;
}

// CEvNS differential cross section dσ/dT [cm^2/GeV]
double cevns_dsigma_dT(double Enu, double T, int A, int Z) {
    double MA = A * 0.9315;  // Nuclear mass in GeV (approximate)
    double QW = weak_charge(A, Z);
    double Q2 = 2.0 * MA * T;  // Momentum transfer squared (GeV^2)

    double F2 = helm_form_factor(Q2, A);
    double kinematic_factor = 1.0 - (MA * T) / (2.0 * Enu * Enu);

    double dsigma = (GF * GF * MA) / (4.0 * M_PI);
    dsigma *= QW * QW * F2 * kinematic_factor;
    dsigma /= CM2_TO_GEV2;  // Convert to cm^2

    return dsigma;
}

// Reactor flux (simplified - use data file for real calculation)
double reactor_flux_U235(double Enu) {
    // Simplified parameterization (use Huber-Mueller for accuracy)
    // Returns dN/dE in antineutrinos per MeV per fission
    if (Enu < 1.8 || Enu > 8.0) return 0.0;

    double a0 = 3.217, a1 = -3.111, a2 = 1.395;
    double a3 = -0.369, a4 = 0.0445, a5 = -0.00202;

    double E = Enu;
    double flux = std::exp(a0 + a1*E + a2*E*E + a3*E*E*E + a4*E*E*E*E + a5*E*E*E*E*E);
    return flux;
}

// Calculate total event rate
double calculate_event_rate(double power_GW, double baseline_m,
                           double detector_mass_kg, int A, int Z) {
    // Number of target nuclei
    double NA = 6.022e23;  // Avogadro's number
    double M_nucleus = A * 1.66e-27;  // kg
    double N_targets = (detector_mass_kg / M_nucleus);

    // Reactor flux normalization
    double fissions_per_sec = power_GW * 1e9 * 1e6 / (200.0 * 1.6e-19);  // J to eV
    double nu_per_fission = 6.0;  // Average for U-235
    double L_cm = baseline_m * 100.0;
    double flux_norm = fissions_per_sec * nu_per_fission / (4.0 * M_PI * L_cm * L_cm);

    // Integrate over neutrino energy
    double rate = 0.0;
    double E_min = 1.8;  // MeV
    double E_max = 8.0;   // MeV
    int n_steps = 1000;
    double dE = (E_max - E_min) / n_steps;

    for (int i = 0; i < n_steps; ++i) {
        double Enu = E_min + (i + 0.5) * dE;  // MeV
        double flux = reactor_flux_U235(Enu);

        // Integrate over recoil energy
        double T_min = 0.0;
        double MA = A * 0.9315;  // GeV
        double T_max = 2.0 * Enu * Enu / (MA * 1000.0 + 2.0 * Enu);  // GeV

        int n_T_steps = 100;
        double dT = (T_max - T_min) / n_T_steps;
        double sigma = 0.0;

        for (int j = 0; j < n_T_steps; ++j) {
            double T = T_min + (j + 0.5) * dT;
            sigma += cevns_dsigma_dT(Enu * MEV_TO_GEV, T, A, Z) * dT;
        }

        rate += flux * sigma * dE;
    }

    rate *= flux_norm * N_targets;
    rate *= 86400.0;  // Convert to events per day

    return rate;
}

int main() {
    // Example: 1 kg Ge detector at 25m from 3 GW reactor
    double rate = calculate_event_rate(3.0, 25.0, 1.0, 73, 32);

    std::cout << "CEvNS Event Rate Calculation" << std::endl;
    std::cout << "=============================" << std::endl;
    std::cout << "Detector: 1 kg Germanium-73" << std::endl;
    std::cout << "Reactor: 3 GW thermal at 25 m baseline" << std::endl;
    std::cout << "Event rate: " << rate << " events/day" << std::endl;
    std::cout << "           " << rate * 365.25 << " events/year" << std::endl;
    std::cout << "           " << rate * 365.25 * 1000.0 << " events/ton/year" << std::endl;

    return 0;
}
```

**Compilation**:
```bash
g++ -o rate_calculator rate_calculator.cpp -lglobes -lgsl -lgslcblas -lm -O2
./rate_calculator
```

### Monte Carlo Event Generator Pattern

```cpp
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <vector>
#include <fstream>

std::vector<double> generate_cevns_events(int n_events, double power_GW,
                                          double baseline_m, int A, int Z,
                                          double threshold_keV) {
    gsl_rng *rng = gsl_rng_alloc(gsl_rng_mt19937);
    gsl_rng_set(rng, time(NULL));

    std::vector<double> recoil_energies;

    for (int i = 0; i < n_events; ++i) {
        // 1. Sample neutrino energy from reactor spectrum
        double Enu = sample_reactor_spectrum(rng);

        // 2. Sample recoil energy from differential cross section
        double T_recoil = sample_recoil_energy(Enu, A, Z, rng);

        // 3. Apply quenching (Ge: q = 0.2)
        double E_observed = T_recoil * 0.2;

        // 4. Apply energy resolution
        double sigma = 0.05 * std::sqrt(E_observed);  // Example resolution
        double E_detected = E_observed + gsl_ran_gaussian(rng, sigma);

        // 5. Apply threshold
        if (E_detected > threshold_keV) {
            recoil_energies.push_back(E_detected);
        }
    }

    gsl_rng_free(rng);
    return recoil_energies;
}
```

Full working examples are provided in `examples/cpp/`.

## Python Implementation

Python offers easier development and better visualization capabilities compared to C++, at the cost of some performance.

### Physics Calculations with NumPy

```python
import numpy as np
from scipy.integrate import quad
from scipy.interpolate import interp1d

# Physical constants
GF = 1.1663787e-5  # GeV^-2
SIN2TW = 0.23121
HBARC = 0.1973  # GeV fm
MEV_TO_GEV = 0.001

def weak_charge(A, Z):
    """Calculate weak nuclear charge Q_W."""
    N = A - Z
    return N - Z * (1 - 4 * SIN2TW)

def helm_form_factor(Q2_GeV2, A):
    """
    Calculate Helm form factor F^2(Q^2).

    Parameters:
        Q2_GeV2: Momentum transfer squared in GeV^2
        A: Mass number

    Returns:
        F^2(Q^2): Form factor squared
    """
    R0 = 1.2 * A**(1/3)  # fm
    s = 0.9  # fm
    RA = np.sqrt(R0**2 - 5*s**2)

    q = np.sqrt(Q2_GeV2) / HBARC  # fm^-1
    qRA = q * RA
    qs = q * s

    # Spherical Bessel function j1(x)/x
    j1_over_qRA = np.where(
        qRA < 0.01,
        1/3 - qRA**2/30,  # Taylor expansion for small x
        (np.sin(qRA)/qRA - np.cos(qRA)) / qRA
    )

    F = 3.0 * j1_over_qRA * np.exp(-qs**2/2)
    return F**2

def cevns_cross_section(E_nu_MeV, T_recoil_MeV, A, Z):
    """
    CEvNS differential cross section dσ/dT.

    Parameters:
        E_nu_MeV: Neutrino energy in MeV
        T_recoil_MeV: Nuclear recoil energy in MeV
        A: Mass number
        Z: Atomic number

    Returns:
        dσ/dT in cm^2/MeV
    """
    MA_GeV = A * 0.9315  # Nuclear mass in GeV
    QW = weak_charge(A, Z)

    E_nu_GeV = E_nu_MeV * MEV_TO_GEV
    T_GeV = T_recoil_MeV * MEV_TO_GEV

    Q2 = 2 * MA_GeV * T_GeV  # GeV^2
    F2 = helm_form_factor(Q2, A)

    kinematic = 1 - (MA_GeV * T_GeV) / (2 * E_nu_GeV**2)

    dsigma = (GF**2 * MA_GeV) / (4 * np.pi)
    dsigma *= QW**2 * F2 * kinematic
    dsigma /= 2.568e-31  # Convert GeV^-2 to cm^2
    dsigma /= MEV_TO_GEV  # Convert to per MeV

    return dsigma

def reactor_flux_huber(E_nu_MeV, isotope='U235'):
    """
    Huber-Mueller reactor antineutrino spectrum.

    Parameters:
        E_nu_MeV: Neutrino energy in MeV
        isotope: 'U235', 'U238', 'Pu239', or 'Pu241'

    Returns:
        dN/dE in antineutrinos per MeV per fission
    """
    # Simplified parameterization (see Huber, Phys. Rev. C 84, 024617)
    params = {
        'U235':  [3.217, -3.111, 1.395, -0.369, 0.0445, -0.00202],
        'Pu239': [3.251, -3.204, 1.428, -0.386, 0.0467, -0.00213],
    }

    if isotope not in params:
        raise ValueError(f"Unknown isotope: {isotope}")

    a = params[isotope]
    E = E_nu_MeV

    if E < 1.8 or E > 8.0:
        return 0.0

    log_flux = a[0] + a[1]*E + a[2]*E**2 + a[3]*E**3 + a[4]*E**4 + a[5]*E**5
    return np.exp(log_flux)

def calculate_event_rate(power_GW, baseline_m, mass_kg, A, Z, threshold_keV=0):
    """
    Calculate total CEvNS event rate.

    Parameters:
        power_GW: Reactor thermal power in GW
        baseline_m: Distance from reactor core in meters
        mass_kg: Detector mass in kg
        A, Z: Target nucleus
        threshold_keV: Energy threshold in keV recoil energy

    Returns:
        Event rate in events/day
    """
    # Number of targets
    NA = 6.022e23
    M_nucleus_kg = A * 1.66e-27
    N_targets = mass_kg / M_nucleus_kg

    # Reactor flux normalization
    fissions_per_sec = power_GW * 1e9 * 1e6 / (200 * 1.6e-19)
    nu_per_fission = 6.0
    L_cm = baseline_m * 100
    flux_norm = fissions_per_sec * nu_per_fission / (4 * np.pi * L_cm**2)

    # Integrate over neutrino energy
    def integrand(E_nu):
        flux = reactor_flux_huber(E_nu, 'U235')

        # Maximum recoil energy for this neutrino
        MA_MeV = A * 931.5
        T_max = 2 * E_nu**2 / (MA_MeV + 2 * E_nu)
        T_min = threshold_keV / 1000  # Convert to MeV

        if T_max <= T_min:
            return 0

        # Integrate differential cross section
        sigma_total = quad(
            lambda T: cevns_cross_section(E_nu, T, A, Z),
            T_min, T_max
        )[0]

        return flux * sigma_total

    rate_per_target, _ = quad(integrand, 1.8, 8.0)
    rate = flux_norm * N_targets * rate_per_target
    rate *= 86400  # Convert to per day

    return rate
```

### Monte Carlo Simulation

```python
import matplotlib.pyplot as plt

def monte_carlo_cevns(n_events, power_GW, baseline_m, mass_kg,
                     A, Z, threshold_keV=0.2, quenching=0.2):
    """
    Generate CEvNS events with full detector response.

    Parameters:
        n_events: Number of events to generate
        power_GW: Reactor power
        baseline_m: Baseline distance
        mass_kg: Detector mass
        A, Z: Target nucleus
        threshold_keV: Detection threshold in keV_ee
        quenching: Quenching factor

    Returns:
        detected_energies: Array of detected recoil energies in keV_ee
    """
    detected = []

    # Create energy grid for sampling
    E_nu_grid = np.linspace(1.8, 8.0, 1000)
    flux_grid = np.array([reactor_flux_huber(E) for E in E_nu_grid])
    flux_grid /= flux_grid.sum()  # Normalize to probability

    for _ in range(n_events):
        # 1. Sample neutrino energy
        E_nu = np.random.choice(E_nu_grid, p=flux_grid)

        # 2. Sample recoil energy
        MA_MeV = A * 931.5
        T_max = 2 * E_nu**2 / (MA_MeV + 2 * E_nu)

        # Use rejection sampling for recoil distribution
        T_recoil = 0
        accepted = False
        while not accepted:
            T_test = np.random.uniform(0, T_max)
            prob = cevns_cross_section(E_nu, T_test, A, Z)
            prob_max = cevns_cross_section(E_nu, 0.01, A, Z)  # Approximate max
            if np.random.uniform(0, prob_max) < prob:
                T_recoil = T_test
                accepted = True

        # 3. Apply quenching
        T_recoil_keV = T_recoil * 1000
        E_observed = T_recoil_keV * quenching

        # 4. Apply energy resolution
        sigma = 0.05 * np.sqrt(E_observed)  # Example: 5% at 1 keV
        E_detected = E_observed + np.random.normal(0, sigma)

        # 5. Apply threshold
        if E_detected > threshold_keV:
            detected.append(E_detected)

    return np.array(detected)

# Example usage
events = monte_carlo_cevns(10000, 3.0, 25.0, 1.0, 73, 32)

plt.figure(figsize=(10, 6))
plt.hist(events, bins=50, alpha=0.7, edgecolor='black')
plt.xlabel('Detected Energy (keV_ee)')
plt.ylabel('Events')
plt.title('CEvNS Recoil Spectrum - 1 kg Ge at 25m from 3 GW Reactor')
plt.yscale('log')
plt.grid(True, alpha=0.3)
plt.savefig('cevns_spectrum.png', dpi=300, bbox_inches='tight')
plt.show()
```

Complete, production-ready Python examples are in `examples/python/`.

## Key Parameters for Reactor CEvNS

### Detector Parameters

| Experiment | Target | Mass | Threshold (keV_ee) | Quenching | Baseline (m) |
|------------|--------|------|-------------------|-----------|--------------|
| CONUS+ | Ge | 1 kg | 0.2 | 0.20 | 25 |
| NUCLEUS | Xe/Ar | 10g-1kg | <1 | 0.15/0.23 | 10-30 |
| CONNIE | Si | 8.15 kg | 0.8 | 0.25 | 30 |
| MINER | Ge | 10 kg | 0.1 | 0.20 | 15 |

### Reactor Parameters

**Typical Commercial Reactor**:
- Thermal power: 1-4 GW_th
- Fuel composition (initial):
  - U-235: 56%
  - U-238: 8%
  - Pu-239: 30%
  - Pu-241: 6%
- Antineutrino flux at 25m: ~10¹³ ν/cm²/s
- Energy spectrum: 1.8-8 MeV (effective range for CEvNS)

### Physics Parameters

**Fundamental Constants**:
```python
GF = 1.1663787e-5  # GeV^-2
SIN2TW = 0.23121
HBARC = 0.1973  # GeV fm
```

**Weak Charges** (Q_W):
| Nucleus | A | Z | Q_W | Enhancement (Q_W²) |
|---------|---|---|-----|-------------------|
| ²³Na | 23 | 11 | 11.2 | 125 |
| ⁴⁰Ar | 40 | 18 | 20.6 | 426 |
| ⁷³Ge | 73 | 32 | 38.6 | 1490 |
| ¹²⁷I | 127 | 53 | 70.0 | 4900 |
| ¹³¹Xe | 131 | 54 | 72.9 | 5320 |
| ¹³³Cs | 133 | 55 | 73.9 | 5457 |

**Quenching Factors** (nuclear recoil to electron equivalent):
- Germanium: q = 0.20 ± 0.02
- Liquid Xenon: q = 0.15 ± 0.02
- Liquid Argon: q = 0.23 ± 0.03
- Silicon: q = 0.25 ± 0.03

### Expected Event Rates

**1 kg Germanium detector at 25m from 3 GW reactor**:
- No threshold: ~100 events/day
- 0.5 keV_ee threshold: ~30 events/day
- 1.0 keV_ee threshold: ~10 events/day

**Scaling**:
- Rate ∝ power (linear)
- Rate ∝ 1/distance² (inverse square law)
- Rate ∝ mass (linear)
- Rate strongly dependent on threshold (exponential-like)

## Running the Examples

### C++ Examples

Navigate to the examples directory:

```bash
cd /workspace/examples/cpp

# Build all examples
make all

# Run basic rate calculator
./basic_rate_calculator 25.0 3.0 1.0 73 32
# Args: baseline_m power_GW mass_kg A Z

# Run Monte Carlo generator
./mc_event_generator --config ../aedl/reactor_ge.glb --nevents 10000 --output cevns_events.csv

# Check output
head cevns_events.csv
```

Expected output format (CSV):
```
event_id,neutrino_energy_MeV,recoil_energy_keV,detected_energy_keV
1,3.45,2.34,0.468
2,4.12,1.89,0.378
...
```

### Python Examples

Install dependencies:

```bash
cd /workspace/examples/python
pip install -r requirements.txt
```

Run physics calculator:

```python
python cevns_calculator.py --detector Ge --mass 1.0 --baseline 25.0 --power 3.0

# Output:
# Reactor: 3.0 GW at 25.0 m
# Detector: 1.0 kg Germanium-73
# Weak charge Q_W: 38.6
# Event rate (no threshold): 102.3 events/day
# Event rate (0.2 keV_ee): 67.8 events/day
# Event rate (0.5 keV_ee): 31.2 events/day
```

Run full Monte Carlo simulation:

```bash
python mc_simulation.py --detector Ge --mass 1.0 --baseline 25.0 --power 3.0 \
                       --threshold 0.2 --nevents 10000 --output cevns_simulation

# Generates:
# - cevns_simulation_events.csv: Event list
# - cevns_simulation_spectrum.png: Recoil spectrum plot
# - cevns_simulation_flux.png: Reactor flux plot
# - cevns_simulation_xsec.png: Cross section plot
```

### Using AEDL Configurations

GLoBES AEDL files define complete experiment configurations:

```bash
# With GLoBES directly (if available)
globes reactor_ge.glb

# Or use in your custom C++ program
glbInitExperiment("../aedl/reactor_ge.glb", &glb_experiment_list[0], &glb_num_of_exps);
```

See `docs/AEDL_EXAMPLES.md` for detailed AEDL syntax and examples.

### Validation Checks

Compare your results with known values:

**1. Total cross section** (E_ν = 3 MeV, Ge-73):
- Expected: σ ≈ 1.2 × 10⁻³⁹ cm²
- Check: Integrate dσ/dT over all recoil energies

**2. Event rate** (1 kg Ge, 25m, 3 GW, no threshold):
- Expected: ~100 events/day
- Tolerance: ±20% (depends on flux model)

**3. Form factor suppression**:
- At Q² = 0.01 GeV²: F² ≈ 0.95 (minimal suppression)
- At Q² = 0.1 GeV²: F² ≈ 0.7 (moderate suppression)

**4. Spectrum shape**:
- Peak recoil energy: ~0.5-1 keV
- Exponentially decreasing at higher energies
- Sharp cutoff at maximum kinematic recoil

## Next Steps and Resources

### Advanced Topics

Once you're comfortable with the basics, explore:

1. **Multi-detector configurations**: Near/far detector setups for background subtraction
2. **Time-dependent analysis**: Reactor on/off cycles, fuel burnup effects
3. **Systematic uncertainties**: Proper treatment in GLoBES framework
4. **Background modeling**: Reactor-correlated and ambient backgrounds
5. **Sensitivity optimization**: Baseline, threshold, and mass trade-offs
6. **Geant4 integration**: Detailed detector simulation beyond simplified response
7. **Non-standard physics**: NSI, sterile neutrinos, electromagnetic properties

### Recommended Reading

**GLoBES**:
- Huber et al., "GLoBES: General Long Baseline Experiment Simulator," Comput. Phys. Commun. 167 (2005) 195 [hep-ph/0407333]
- Kopp et al., "Efficient numerical diagonalization of hermitian 3x3 matrices," Int. J. Mod. Phys. C 19 (2008) 523 [physics/0610206]

**CEvNS Theory**:
- Freedman, "Coherent effects of a weak neutral current," Phys. Rev. D 9 (1974) 1389
- Scholberg, "Prospects for measuring coherent neutrino-nucleus elastic scattering at a stopped-pion neutrino source," Phys. Rev. D 73 (2006) 033005 [hep-ex/0511042]

**Experimental Results**:
- COHERENT Collaboration, "Observation of Coherent Elastic Neutrino-Nucleus Scattering," Science 357 (2017) 1123 [arXiv:1708.01294]
- CONUS Collaboration, "Novel constraints on neutrino physics beyond the standard model from the CONUS experiment," JHEP 05 (2022) 085 [arXiv:2110.02174]

**Reactor Flux**:
- Huber, "Determination of antineutrino spectra from nuclear reactors," Phys. Rev. C 84 (2011) 024617 [arXiv:1106.0687]
- Mueller et al., "Improved predictions of reactor antineutrino spectra," Phys. Rev. C 83 (2011) 054615 [arXiv:1101.2663]

### External Tools

**CEvNS Calculator** (Python):
- GitHub: https://github.com/bradkav/CEvNS
- Standalone CEvNS event rate calculator
- Includes nuclear response functions

**GENIE** (C++):
- Comprehensive neutrino event generator
- Includes CEvNS processes
- Full nuclear modeling
- Website: http://www.genie-mc.org/

**Geant4**:
- Detailed detector simulation
- Particle tracking and energy deposition
- Essential for realistic detector response
- Website: https://geant4.web.cern.ch/

**ROOT**:
- Data analysis framework
- Histogramming and fitting
- Widely used in particle physics
- Website: https://root.cern.ch/

### Online Resources

- **GLoBES website**: https://www.mpi-hd.mpg.de/personalhomes/globes/
- **Neutrino oscillation parameters** (NuFit): http://www.nu-fit.org/
- **Particle Data Group**: https://pdg.lbl.gov/ (Review of Particle Physics)
- **COHERENT experiment**: https://www.ornl.gov/division/pd/coherent
- **NUCLEUS experiment**: https://nucleus-experiment.org/
- **ArXiv hep-ph**: https://arxiv.org/archive/hep-ph (latest preprints)

### Community and Support

- **GLoBES mailing list**: Subscribe via GLoBES website
- **Neutrino physics forums**: Various online communities
- **GitHub issues**: Report bugs or request features for this repository

### Contributing

Found an error or have an improvement? Contributions welcome:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

### Citation

If you use this guide or examples in your research, please cite:
- This repository: [Add DOI if/when published]
- GLoBES: Huber et al., Comput. Phys. Commun. 167 (2005) 195
- Relevant experimental papers for detector parameters

---

**Questions or Issues?**

Open an issue on GitHub or consult the references above. Happy simulating!
