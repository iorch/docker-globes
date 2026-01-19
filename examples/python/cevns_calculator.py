#!/usr/bin/env python3
"""
CEvNS Event Rate Calculator

Calculate Coherent Elastic Neutrino-Nucleus Scattering event rates
for reactor-based experiments.

Usage:
    python cevns_calculator.py
    python cevns_calculator.py --detector Ge --mass 1.0 --baseline 25.0 --power 3.0
"""

import numpy as np
from scipy.integrate import quad
from scipy.interpolate import interp1d
import argparse

# Physical constants
GF = 1.1663787e-5  # GeV^-2, Fermi constant
SIN2TW = 0.23121   # sin^2(theta_W), weak mixing angle
HBARC = 0.1973     # GeV fm, conversion factor
MEV_TO_GEV = 0.001
CM2_TO_GEV2 = 2.568e-31  # Conversion from GeV^-2 to cm^2

# Detector properties database
DETECTORS = {
    'Ge': {'A': 73, 'Z': 32, 'quenching': 0.20, 'name': 'Germanium'},
    'Xe': {'A': 131, 'Z': 54, 'quenching': 0.15, 'name': 'Xenon'},
    'Ar': {'A': 40, 'Z': 18, 'quenching': 0.23, 'name': 'Argon'},
}


def weak_charge(A, Z):
    """
    Calculate weak nuclear charge Q_W.

    Parameters:
        A: Mass number
        Z: Atomic number (protons)

    Returns:
        Q_W: Weak nuclear charge
    """
    N = A - Z  # Number of neutrons
    return N - Z * (1.0 - 4.0 * SIN2TW)


def helm_form_factor(Q2_GeV2, A):
    """
    Calculate Helm form factor F^2(Q^2) for nuclear recoils.

    The Helm form factor accounts for loss of coherence at
    high momentum transfer due to finite nuclear size.

    Parameters:
        Q2_GeV2: Momentum transfer squared in GeV^2
        A: Mass number

    Returns:
        F^2(Q^2): Form factor squared (dimensionless, 0 to 1)
    """
    # Nuclear size parameters
    R0 = 1.2 * A**(1.0/3.0)  # fm, nuclear radius
    s = 0.9  # fm, nuclear skin thickness
    RA = np.sqrt(R0**2 - 5.0*s**2)  # Effective radius

    # Momentum transfer
    q = np.sqrt(Q2_GeV2) / HBARC  # fm^-1
    qRA = q * RA
    qs = q * s

    # Spherical Bessel function j1(x)/x
    # Use Taylor expansion for small x to avoid numerical issues
    if np.isscalar(qRA):
        if qRA < 0.01:
            j1_over_qRA = 1.0/3.0 - qRA**2/30.0
        else:
            j1_over_qRA = (np.sin(qRA)/qRA - np.cos(qRA)) / qRA
    else:
        j1_over_qRA = np.where(
            qRA < 0.01,
            1.0/3.0 - qRA**2/30.0,  # Taylor expansion
            (np.sin(qRA)/qRA - np.cos(qRA)) / qRA
        )

    # Helm form factor
    F = 3.0 * j1_over_qRA * np.exp(-qs**2/2.0)
    return F**2


def cevns_dsigma_dT(E_nu_MeV, T_recoil_MeV, A, Z):
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
    # Nuclear mass
    MA_GeV = A * 0.9315  # GeV (using atomic mass unit ≈ 0.9315 GeV)

    # Weak charge
    QW = weak_charge(A, Z)

    # Convert to GeV
    E_nu_GeV = E_nu_MeV * MEV_TO_GEV
    T_GeV = T_recoil_MeV * MEV_TO_GEV

    # Momentum transfer squared
    Q2 = 2.0 * MA_GeV * T_GeV  # GeV^2

    # Form factor
    F2 = helm_form_factor(Q2, A)

    # Kinematic factor
    kinematic = 1.0 - (MA_GeV * T_GeV) / (2.0 * E_nu_GeV**2)

    if kinematic < 0:
        return 0.0  # Kinematically forbidden

    # Differential cross section (in natural units)
    dsigma = (GF**2 * MA_GeV) / (4.0 * np.pi)
    dsigma *= QW**2 * F2 * kinematic

    # Convert to cm^2/MeV
    dsigma /= CM2_TO_GEV2  # GeV^-2 to cm^2
    dsigma /= MEV_TO_GEV   # per GeV to per MeV

    return dsigma


def reactor_flux_huber(E_nu_MeV, isotope='U235'):
    """
    Huber-Mueller reactor antineutrino spectrum.

    Parameterization from:
    Huber, Phys. Rev. C 84, 024617 (2011)

    Parameters:
        E_nu_MeV: Neutrino energy in MeV
        isotope: 'U235', 'U238', 'Pu239', or 'Pu241'

    Returns:
        dN/dE in antineutrinos per MeV per fission
    """
    # Polynomial coefficients for different isotopes
    # Format: log(flux) = a0 + a1*E + a2*E^2 + a3*E^3 + a4*E^4 + a5*E^5
    params = {
        'U235':  [3.217, -3.111, 1.395, -0.369, 0.0445, -0.00202],
        'U238':  [2.990, -2.882, 1.278, -0.328, 0.0391, -0.00178],
        'Pu239': [3.251, -3.204, 1.428, -0.386, 0.0467, -0.00213],
        'Pu241': [3.297, -3.288, 1.472, -0.399, 0.0481, -0.00220],
    }

    if isotope not in params:
        raise ValueError(f"Unknown isotope: {isotope}. Choose from {list(params.keys())}")

    a = params[isotope]
    E = E_nu_MeV

    # Valid energy range
    if E < 1.8 or E > 8.0:
        return 0.0

    # Exponential parameterization
    log_flux = a[0] + a[1]*E + a[2]*E**2 + a[3]*E**3 + a[4]*E**4 + a[5]*E**5
    return np.exp(log_flux)


def reactor_total_flux(power_GW, baseline_m):
    """
    Calculate total reactor antineutrino flux at detector.

    Parameters:
        power_GW: Reactor thermal power in GW
        baseline_m: Distance from reactor core in meters

    Returns:
        Total flux in ν/cm²/s
    """
    # Fission rate
    energy_per_fission_J = 200.0 * 1.6e-13  # 200 MeV in Joules
    power_W = power_GW * 1e9  # Convert to Watts
    fissions_per_sec = power_W / energy_per_fission_J

    # Antineutrinos per fission (average)
    nu_per_fission = 6.0

    # Total production rate
    nu_per_sec = fissions_per_sec * nu_per_fission

    # Flux at distance (inverse square law)
    L_cm = baseline_m * 100.0  # Convert to cm
    flux = nu_per_sec / (4.0 * np.pi * L_cm**2)

    return flux


def calculate_total_cross_section(E_nu_MeV, A, Z):
    """
    Calculate total CEvNS cross section (integrated over recoil energy).

    Parameters:
        E_nu_MeV: Neutrino energy in MeV
        A, Z: Target nucleus

    Returns:
        Total cross section in cm^2
    """
    # Maximum recoil energy
    MA_MeV = A * 931.5  # Nuclear mass in MeV
    T_max = 2.0 * E_nu_MeV**2 / (MA_MeV + 2.0 * E_nu_MeV)

    if T_max <= 0:
        return 0.0

    # Integrate differential cross section
    sigma_total, _ = quad(
        lambda T: cevns_dsigma_dT(E_nu_MeV, T, A, Z),
        0.0, T_max,
        limit=100
    )

    return sigma_total


def calculate_event_rate(power_GW, baseline_m, mass_kg, A, Z,
                        threshold_keV=0.0, quenching=1.0):
    """
    Calculate total CEvNS event rate.

    Parameters:
        power_GW: Reactor thermal power in GW
        baseline_m: Distance from reactor in meters
        mass_kg: Detector mass in kg
        A, Z: Target nucleus
        threshold_keV: Energy threshold in keV (electron equivalent)
        quenching: Quenching factor (keV_ee / keV_nr)

    Returns:
        Event rate in events/day
    """
    # Number of target nuclei
    NA = 6.022e23  # Avogadro's number
    M_nucleus_kg = A * 1.66e-27  # kg
    N_targets = mass_kg / M_nucleus_kg

    # Reactor flux normalization
    energy_per_fission_J = 200.0 * 1.6e-13
    power_W = power_GW * 1e9
    fissions_per_sec = power_W / energy_per_fission_J
    nu_per_fission = 6.0
    L_cm = baseline_m * 100.0
    flux_norm = fissions_per_sec * nu_per_fission / (4.0 * np.pi * L_cm**2)

    # Convert threshold to nuclear recoil energy
    threshold_nr_MeV = (threshold_keV / 1000.0) / quenching if quenching > 0 else 0.0

    # Integrate over neutrino energy
    def integrand(E_nu):
        flux = reactor_flux_huber(E_nu, 'U235')

        # Maximum recoil energy for this neutrino
        MA_MeV = A * 931.5
        T_max = 2.0 * E_nu**2 / (MA_MeV + 2.0 * E_nu)

        if T_max <= threshold_nr_MeV:
            return 0.0

        # Integrate cross section above threshold
        sigma, _ = quad(
            lambda T: cevns_dsigma_dT(E_nu, T, A, Z),
            threshold_nr_MeV, T_max,
            limit=50
        )

        return flux * sigma

    # Integrate over neutrino energy
    rate_per_target, _ = quad(integrand, 1.8, 8.0, limit=100)

    # Total rate
    rate = flux_norm * N_targets * rate_per_target
    rate *= 86400.0  # Convert per second to per day

    return rate


def print_results(detector_name, power, baseline, mass, A, Z, quenching):
    """Print formatted results."""
    print("=" * 60)
    print("CEvNS Event Rate Calculator")
    print("=" * 60)
    print()

    # Reactor configuration
    print("Reactor Configuration:")
    print(f"  Power: {power} GW thermal")
    print(f"  Baseline: {baseline} meters")
    flux = reactor_total_flux(power, baseline)
    print(f"  Antineutrino flux at detector: {flux:.2e} ν/cm²/s")
    print()

    # Detector configuration
    print("Detector Configuration:")
    print(f"  Material: {detector_name} (A={A}, Z={Z})")
    print(f"  Mass: {mass} kg")
    N_targets = mass / (A * 1.66e-27)
    print(f"  Number of targets: {N_targets:.2e} nuclei")
    QW = weak_charge(A, Z)
    print(f"  Weak charge Q_W: {QW:.1f}")
    print(f"  Quenching factor: {quenching:.2f}")
    print()

    # Physics parameters
    print("Physics Parameters:")
    E_test = 3.0  # MeV
    sigma_test = calculate_total_cross_section(E_test, A, Z)
    print(f"  Cross section ({E_test} MeV): {sigma_test:.2e} cm²")

    # Form factor check
    Q2_test = 0.01  # GeV^2
    F2_test = helm_form_factor(Q2_test, A)
    print(f"  Form factor F²(Q²=0.01 GeV²): {F2_test:.3f}")
    print()

    # Event rates
    print("Event Rates:")

    thresholds = [0.0, 0.2, 0.5, 1.0]
    for thresh in thresholds:
        rate_day = calculate_event_rate(power, baseline, mass, A, Z,
                                       threshold_keV=thresh,
                                       quenching=quenching)
        rate_year = rate_day * 365.25

        if thresh == 0.0:
            print(f"  No threshold:      {rate_day:6.1f} events/day  ({rate_year:,.0f} events/year)")
        else:
            print(f"  Threshold {thresh:3.1f} keV: {rate_day:6.1f} events/day  ({rate_year:,.0f} events/year)")
    print()


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description='Calculate CEvNS event rates for reactor-based experiments'
    )
    parser.add_argument('--detector', type=str, default='Ge',
                       choices=['Ge', 'Xe', 'Ar'],
                       help='Detector material (default: Ge)')
    parser.add_argument('--mass', type=float, default=1.0,
                       help='Detector mass in kg (default: 1.0)')
    parser.add_argument('--baseline', type=float, default=25.0,
                       help='Baseline distance in meters (default: 25.0)')
    parser.add_argument('--power', type=float, default=3.0,
                       help='Reactor power in GW thermal (default: 3.0)')
    parser.add_argument('--threshold', type=float, default=0.2,
                       help='Energy threshold in keV_ee (default: 0.2)')

    args = parser.parse_args()

    # Get detector properties
    det = DETECTORS[args.detector]

    # Print results
    print_results(
        det['name'],
        args.power,
        args.baseline,
        args.mass,
        det['A'],
        det['Z'],
        det['quenching']
    )


if __name__ == '__main__':
    main()
