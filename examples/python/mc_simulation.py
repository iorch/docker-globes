#!/usr/bin/env python3
"""
CEvNS Monte Carlo Simulation

Generate Monte Carlo events for reactor-based CEvNS experiments
with full detector response simulation.

Usage:
    python mc_simulation.py --nevents 10000 --output simulation
    python mc_simulation.py --detector Xe --mass 0.01 --baseline 10.0 --power 4.0
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import argparse
import csv
from datetime import datetime

# Import physics functions from cevns_calculator
try:
    from cevns_calculator import (
        weak_charge, helm_form_factor, cevns_dsigma_dT,
        reactor_flux_huber, DETECTORS
    )
except ImportError:
    print("Error: Could not import cevns_calculator.py")
    print("Make sure cevns_calculator.py is in the same directory.")
    exit(1)


class ReactorCEvNSSimulation:
    """Monte Carlo simulation for reactor CEvNS events."""

    def __init__(self, power_GW, baseline_m, mass_kg, A, Z,
                 threshold_keV=0.2, quenching=0.20, resolution=0.05):
        """
        Initialize simulation parameters.

        Parameters:
            power_GW: Reactor thermal power in GW
            baseline_m: Distance from reactor in meters
            mass_kg: Detector mass in kg
            A, Z: Target nucleus
            threshold_keV: Detection threshold in keV_ee
            quenching: Quenching factor (E_ee / E_nr)
            resolution: Fractional energy resolution (σ/E at 1 keV)
        """
        self.power_GW = power_GW
        self.baseline_m = baseline_m
        self.mass_kg = mass_kg
        self.A = A
        self.Z = Z
        self.threshold_keV = threshold_keV
        self.quenching = quenching
        self.resolution = resolution

        self.MA_MeV = A * 931.5  # Nuclear mass in MeV
        self.QW = weak_charge(A, Z)

        # Pre-compute flux and cross section grids for efficiency
        self._setup_grids()

    def _setup_grids(self):
        """Setup energy grids for sampling."""
        # Neutrino energy grid
        self.E_nu_grid = np.linspace(1.8, 8.0, 1000)

        # Flux on grid (U-235 spectrum)
        self.flux_grid = np.array([
            reactor_flux_huber(E, 'U235') for E in self.E_nu_grid
        ])

        # Flux normalization
        energy_per_fission_J = 200.0 * 1.6e-13
        power_W = self.power_GW * 1e9
        fissions_per_sec = power_W / energy_per_fission_J
        nu_per_fission = 6.0
        L_cm = self.baseline_m * 100.0
        self.flux_norm = fissions_per_sec * nu_per_fission / (4.0 * np.pi * L_cm**2)

        # Total cross sections on grid
        self.sigma_total_grid = np.array([
            self._integrate_cross_section(E) for E in self.E_nu_grid
        ])

        # Sampling probability (flux × cross section)
        sampling_weights = self.flux_grid * self.sigma_total_grid
        self.sampling_prob = sampling_weights / sampling_weights.sum()

    def _integrate_cross_section(self, E_nu_MeV):
        """Integrate differential cross section for given neutrino energy."""
        T_max = 2.0 * E_nu_MeV**2 / (self.MA_MeV + 2.0 * E_nu_MeV)

        if T_max <= 0:
            return 0.0

        # Simple trapezoidal integration
        T_grid = np.linspace(0, T_max, 100)
        dsigma_grid = np.array([
            cevns_dsigma_dT(E_nu_MeV, T, self.A, self.Z) for T in T_grid
        ])

        return np.trapz(dsigma_grid, T_grid)

    def sample_neutrino_energy(self, n_samples=1):
        """
        Sample neutrino energies from reactor spectrum weighted by cross section.

        Parameters:
            n_samples: Number of energies to sample

        Returns:
            Array of neutrino energies in MeV
        """
        indices = np.random.choice(
            len(self.E_nu_grid),
            size=n_samples,
            p=self.sampling_prob
        )
        return self.E_nu_grid[indices]

    def sample_recoil_energy(self, E_nu_MeV):
        """
        Sample nuclear recoil energy for given neutrino energy.

        Uses acceptance-rejection method.

        Parameters:
            E_nu_MeV: Neutrino energy in MeV

        Returns:
            Recoil energy in MeV
        """
        T_max = 2.0 * E_nu_MeV**2 / (self.MA_MeV + 2.0 * E_nu_MeV)

        if T_max <= 0:
            return 0.0

        # Find approximate maximum of differential cross section
        T_test = np.linspace(0.0001, T_max, 100)
        dsigma_test = np.array([
            cevns_dsigma_dT(E_nu_MeV, T, self.A, self.Z) for T in T_test
        ])
        dsigma_max = dsigma_test.max() * 1.2  # Add safety factor

        # Acceptance-rejection sampling
        max_iterations = 10000
        for _ in range(max_iterations):
            T_sample = np.random.uniform(0, T_max)
            prob = cevns_dsigma_dT(E_nu_MeV, T_sample, self.A, self.Z)

            if np.random.uniform(0, dsigma_max) < prob:
                return T_sample

        # Fallback: uniform sampling if rejection fails
        return np.random.uniform(0, T_max)

    def apply_detector_response(self, T_recoil_keV):
        """
        Apply detector response: quenching, resolution, threshold.

        Parameters:
            T_recoil_keV: Nuclear recoil energy in keV

        Returns:
            detected_energy_keV: Detected energy in keV_ee (or None if below threshold)
        """
        # Quenching: nuclear recoil to electron equivalent
        E_observed = T_recoil_keV * self.quenching

        # Energy resolution (Gaussian smearing)
        # σ(E) = resolution * √E for statistical term
        sigma = self.resolution * np.sqrt(E_observed)
        E_detected = E_observed + np.random.normal(0, sigma)

        # Threshold cut
        if E_detected < self.threshold_keV:
            return None

        return E_detected

    def generate_events(self, n_events, verbose=True):
        """
        Generate Monte Carlo events.

        Parameters:
            n_events: Number of events to generate (pre-threshold)
            verbose: Print progress

        Returns:
            events: List of dictionaries with event information
        """
        events = []

        if verbose:
            print(f"Generating {n_events} events...")
            print_interval = max(n_events // 20, 1)

        for i in range(n_events):
            if verbose and (i % print_interval == 0 or i == n_events - 1):
                progress = (i + 1) / n_events * 100
                bar_length = 40
                filled = int(bar_length * (i + 1) / n_events)
                bar = '=' * filled + '-' * (bar_length - filled)
                print(f'\rProgress: [{bar}] {progress:.1f}%', end='', flush=True)

            # 1. Sample neutrino energy
            E_nu = self.sample_neutrino_energy(1)[0]

            # 2. Sample recoil energy
            T_recoil_MeV = self.sample_recoil_energy(E_nu)
            T_recoil_keV = T_recoil_MeV * 1000.0

            # 3. Apply detector response
            E_detected = self.apply_detector_response(T_recoil_keV)

            # Store event
            event = {
                'event_id': i + 1,
                'neutrino_energy_MeV': E_nu,
                'recoil_energy_keV': T_recoil_keV,
                'detected_energy_keV': E_detected,
                'passed_threshold': E_detected is not None
            }
            events.append(event)

        if verbose:
            print()  # New line after progress bar

        return events


def save_events(events, filename):
    """Save events to CSV file."""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'event_id', 'neutrino_energy_MeV',
            'recoil_energy_keV_nr', 'detected_energy_keV_ee'
        ])

        for event in events:
            writer.writerow([
                event['event_id'],
                f"{event['neutrino_energy_MeV']:.4f}",
                f"{event['recoil_energy_keV']:.4f}",
                f"{event['detected_energy_keV']:.4f}" if event['detected_energy_keV'] else 'None'
            ])


def plot_spectrum(events, output_file, title):
    """Plot detected energy spectrum."""
    # Filter events that passed threshold
    detected_energies = [
        e['detected_energy_keV'] for e in events if e['passed_threshold']
    ]

    if len(detected_energies) == 0:
        print("Warning: No events passed threshold. Skipping spectrum plot.")
        return

    plt.figure(figsize=(10, 6))
    plt.hist(detected_energies, bins=50, alpha=0.7, edgecolor='black', color='steelblue')
    plt.xlabel('Detected Energy (keV_ee)', fontsize=12)
    plt.ylabel('Events', fontsize=12)
    plt.title(title, fontsize=14)
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved spectrum plot: {output_file}")


def plot_flux(output_file):
    """Plot reactor flux spectrum."""
    E_grid = np.linspace(1.8, 8.0, 200)
    flux_grid = np.array([reactor_flux_huber(E, 'U235') for E in E_grid])

    plt.figure(figsize=(10, 6))
    plt.plot(E_grid, flux_grid, linewidth=2, color='darkred')
    plt.xlabel('Neutrino Energy (MeV)', fontsize=12)
    plt.ylabel('dN/dE (1/MeV/fission)', fontsize=12)
    plt.title('Reactor Antineutrino Flux (U-235)', fontsize=14)
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved flux plot: {output_file}")


def plot_cross_section(A, Z, output_file):
    """Plot CEvNS cross section vs neutrino energy."""
    E_grid = np.linspace(1.8, 8.0, 100)
    sigma_grid = []

    for E in E_grid:
        MA_MeV = A * 931.5
        T_max = 2.0 * E**2 / (MA_MeV + 2.0 * E)
        # Integrate cross section
        T_test = np.linspace(0, T_max, 50)
        dsigma = np.array([cevns_dsigma_dT(E, T, A, Z) for T in T_test])
        sigma_total = np.trapz(dsigma, T_test)
        sigma_grid.append(sigma_total)

    plt.figure(figsize=(10, 6))
    plt.plot(E_grid, sigma_grid, linewidth=2, color='darkgreen')
    plt.xlabel('Neutrino Energy (MeV)', fontsize=12)
    plt.ylabel('Total Cross Section (cm²)', fontsize=12)
    plt.title(f'CEvNS Cross Section (A={A}, Z={Z})', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved cross section plot: {output_file}")


def save_summary(events, sim, output_file):
    """Save simulation summary."""
    detected = [e for e in events if e['passed_threshold']]

    with open(output_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("CEvNS Monte Carlo Simulation Summary\n")
        f.write("=" * 60 + "\n")
        f.write(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("Configuration:\n")
        f.write(f"  Reactor power: {sim.power_GW} GW thermal\n")
        f.write(f"  Baseline: {sim.baseline_m} m\n")
        f.write(f"  Detector mass: {sim.mass_kg} kg\n")
        f.write(f"  Target nucleus: A={sim.A}, Z={sim.Z}\n")
        f.write(f"  Weak charge Q_W: {sim.QW:.2f}\n")
        f.write(f"  Threshold: {sim.threshold_keV} keV_ee\n")
        f.write(f"  Quenching factor: {sim.quenching}\n")
        f.write(f"  Energy resolution: {sim.resolution*100:.1f}%\n\n")

        f.write("Results:\n")
        f.write(f"  Generated events: {len(events)}\n")
        f.write(f"  Passed threshold: {len(detected)} ({len(detected)/len(events)*100:.1f}%)\n")

        if len(detected) > 0:
            detected_energies = [e['detected_energy_keV'] for e in detected]
            f.write(f"  Mean detected energy: {np.mean(detected_energies):.3f} keV\n")
            f.write(f"  Median detected energy: {np.median(detected_energies):.3f} keV\n")
            f.write(f"  Min/Max: {np.min(detected_energies):.3f} / {np.max(detected_energies):.3f} keV\n")

            # Estimate event rate
            efficiency = len(detected) / len(events)
            # This is approximate - real rate calculation needs proper normalization
            f.write(f"\n  Detection efficiency: {efficiency*100:.1f}%\n")

    print(f"Saved summary: {output_file}")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description='Monte Carlo simulation for reactor CEvNS'
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
    parser.add_argument('--quenching', type=float, default=None,
                       help='Quenching factor (default: detector-specific)')
    parser.add_argument('--resolution', type=float, default=0.05,
                       help='Fractional energy resolution (default: 0.05 = 5%%)')
    parser.add_argument('--nevents', type=int, default=10000,
                       help='Number of events to generate (default: 10000)')
    parser.add_argument('--output', type=str, default='cevns_simulation',
                       help='Output file prefix (default: cevns_simulation)')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed (default: None)')

    args = parser.parse_args()

    # Set random seed
    if args.seed is not None:
        np.random.seed(args.seed)

    # Get detector properties
    det = DETECTORS[args.detector]
    quenching = args.quenching if args.quenching is not None else det['quenching']

    # Print configuration
    print("=" * 60)
    print("CEvNS Monte Carlo Simulation")
    print("=" * 60)
    print()
    print("Configuration:")
    print(f"  Detector: {args.mass} kg {det['name']} (A={det['A']}, Z={det['Z']})")
    print(f"  Reactor: {args.power} GW at {args.baseline} m")
    print(f"  Threshold: {args.threshold} keV_ee")
    print(f"  Quenching: {quenching:.2f}")
    print(f"  Resolution: {args.resolution*100:.1f}%")
    print(f"  Events to generate: {args.nevents}")
    print()

    # Initialize simulation
    sim = ReactorCEvNSSimulation(
        power_GW=args.power,
        baseline_m=args.baseline,
        mass_kg=args.mass,
        A=det['A'],
        Z=det['Z'],
        threshold_keV=args.threshold,
        quenching=quenching,
        resolution=args.resolution
    )

    # Generate events
    events = sim.generate_events(args.nevents, verbose=True)

    # Count detected events
    detected = [e for e in events if e['passed_threshold']]
    print()
    print(f"Results:")
    print(f"  Generated events: {len(events)}")
    print(f"  Passed threshold: {len(detected)} ({len(detected)/len(events)*100:.1f}%)")

    if len(detected) > 0:
        detected_energies = [e['detected_energy_keV'] for e in detected]
        print(f"  Mean detected energy: {np.mean(detected_energies):.3f} keV")
        print(f"  Median detected energy: {np.median(detected_energies):.3f} keV")
    print()

    # Save outputs
    print("Saving outputs...")
    save_events(events, f"{args.output}_events.csv")
    save_summary(events, sim, f"{args.output}_summary.txt")

    # Generate plots
    plot_spectrum(events, f"{args.output}_spectrum.png",
                 f"CEvNS Recoil Spectrum - {det['name']}")
    plot_flux(f"{args.output}_flux.png")
    plot_cross_section(det['A'], det['Z'], f"{args.output}_xsec.png")

    print()
    print("Done!")


if __name__ == '__main__':
    main()
