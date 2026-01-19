/*
 * CEvNS Monte Carlo Event Generator
 *
 * Generate Monte Carlo events for reactor-based CEvNS with detector response.
 *
 * Compilation:
 *   g++ -o mc_event_generator mc_event_generator.cpp \
 *       -lglobes -lgsl -lgslcblas -lm -O2
 *
 * Usage:
 *   ./mc_event_generator --nevents 10000 --output events.csv
 */

#include <iostream>
#include <fstream>
#include <cmath>
#include <cstring>
#include <ctime>
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

// Physical constants (same as basic calculator)
const double GF = 1.1663787e-5;
const double SIN2TW = 0.23121;
const double HBARC = 0.1973;
const double MEV_TO_GEV = 0.001;
const double CM2_TO_GEV2 = 2.568e-31;

// Default parameters
struct SimConfig {
    int nevents = 10000;
    double power_GW = 3.0;
    double baseline_m = 25.0;
    double mass_kg = 1.0;
    int A = 73;  // Ge
    int Z = 32;
    double threshold_keV = 0.2;
    double quenching = 0.20;
    double resolution = 0.05;
    std::string output_file = "cevns_events.csv";
    unsigned long seed = 0;
};

// Physics functions (same as before)
double weak_charge(int A, int Z) {
    int N = A - Z;
    return static_cast<double>(N) - static_cast<double>(Z) * (1.0 - 4.0 * SIN2TW);
}

double helm_form_factor(double Q2_GeV2, double A) {
    double R0 = 1.2 * std::pow(static_cast<double>(A), 1.0/3.0);
    double s = 0.9;
    double RA = std::sqrt(R0*R0 - 5.0*s*s);

    double q = std::sqrt(Q2_GeV2) / HBARC;
    double qRA = q * RA;
    double qs = q * s;

    double j1_over_qRA;
    if (qRA < 0.01) {
        j1_over_qRA = 1.0/3.0 - qRA*qRA/30.0;
    } else {
        j1_over_qRA = (std::sin(qRA)/qRA - std::cos(qRA)) / qRA;
    }

    double F = 3.0 * j1_over_qRA * std::exp(-qs*qs/2.0);
    return F * F;
}

double cevns_dsigma_dT(double E_nu_GeV, double T_GeV, int A, int Z) {
    double MA = static_cast<double>(A) * 0.9315;
    double QW = weak_charge(A, Z);
    double Q2 = 2.0 * MA * T_GeV;

    double F2 = helm_form_factor(Q2, A);
    double kinematic = 1.0 - (MA * T_GeV) / (2.0 * E_nu_GeV * E_nu_GeV);

    if (kinematic < 0.0) return 0.0;

    double dsigma = (GF * GF * MA) / (4.0 * M_PI);
    dsigma *= QW * QW * F2 * kinematic;
    dsigma /= CM2_TO_GEV2;

    return dsigma;
}

double reactor_flux_U235(double E_MeV) {
    if (E_MeV < 1.8 || E_MeV > 8.0) return 0.0;

    double a0 = 3.217, a1 = -3.111, a2 = 1.395;
    double a3 = -0.369, a4 = 0.0445, a5 = -0.00202;

    double E = E_MeV;
    double log_flux = a0 + a1*E + a2*E*E + a3*E*E*E + a4*E*E*E*E + a5*E*E*E*E*E;

    return std::exp(log_flux);
}

// Sample neutrino energy from reactor spectrum
double sample_neutrino_energy(gsl_rng *rng) {
    // Simple rejection sampling
    while (true) {
        double E = gsl_rng_uniform(rng) * 6.2 + 1.8;  // 1.8 to 8.0 MeV
        double flux = reactor_flux_U235(E);
        double flux_max = 4.0;  // Approximate maximum

        if (gsl_rng_uniform(rng) * flux_max < flux) {
            return E;
        }
    }
}

// Sample recoil energy for given neutrino energy
double sample_recoil_energy(double E_nu_MeV, int A, int Z, gsl_rng *rng) {
    double MA_MeV = static_cast<double>(A) * 931.5;
    double T_max_MeV = 2.0 * E_nu_MeV * E_nu_MeV / (MA_MeV + 2.0 * E_nu_MeV);

    if (T_max_MeV <= 0.0) return 0.0;

    double E_nu_GeV = E_nu_MeV * MEV_TO_GEV;

    // Find approximate maximum of differential cross section
    double dsigma_max = 0.0;
    for (int i = 0; i < 100; ++i) {
        double T_test = T_max_MeV * static_cast<double>(i) / 100.0;
        double ds = cevns_dsigma_dT(E_nu_GeV, T_test * MEV_TO_GEV, A, Z);
        if (ds > dsigma_max) dsigma_max = ds;
    }
    dsigma_max *= 1.2;  // Safety factor

    // Rejection sampling
    for (int iter = 0; iter < 10000; ++iter) {
        double T_sample_MeV = gsl_rng_uniform(rng) * T_max_MeV;
        double prob = cevns_dsigma_dT(E_nu_GeV, T_sample_MeV * MEV_TO_GEV, A, Z);

        if (gsl_rng_uniform(rng) * dsigma_max < prob) {
            return T_sample_MeV;
        }
    }

    // Fallback
    return gsl_rng_uniform(rng) * T_max_MeV;
}

// Apply detector response
double apply_detector_response(double T_recoil_keV, double quenching,
                               double resolution, gsl_rng *rng) {
    // Quenching
    double E_observed = T_recoil_keV * quenching;

    // Energy resolution
    double sigma = resolution * std::sqrt(E_observed);
    double E_detected = E_observed + gsl_ran_gaussian(rng, sigma);

    return E_detected;
}

// Parse command line arguments
void parse_args(int argc, char *argv[], SimConfig &config) {
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--nevents") == 0 && i + 1 < argc) {
            config.nevents = std::atoi(argv[++i]);
        } else if (std::strcmp(argv[i], "--power") == 0 && i + 1 < argc) {
            config.power_GW = std::atof(argv[++i]);
        } else if (std::strcmp(argv[i], "--baseline") == 0 && i + 1 < argc) {
            config.baseline_m = std::atof(argv[++i]);
        } else if (std::strcmp(argv[i], "--mass") == 0 && i + 1 < argc) {
            config.mass_kg = std::atof(argv[++i]);
        } else if (std::strcmp(argv[i], "--threshold") == 0 && i + 1 < argc) {
            config.threshold_keV = std::atof(argv[++i]);
        } else if (std::strcmp(argv[i], "--output") == 0 && i + 1 < argc) {
            config.output_file = argv[++i];
        } else if (std::strcmp(argv[i], "--seed") == 0 && i + 1 < argc) {
            config.seed = std::atol(argv[++i]);
        }
    }
}

int main(int argc, char *argv[]) {
    SimConfig config;
    parse_args(argc, argv, config);

    // Initialize random number generator
    gsl_rng *rng = gsl_rng_alloc(gsl_rng_mt19937);
    if (config.seed == 0) {
        config.seed = static_cast<unsigned long>(std::time(nullptr));
    }
    gsl_rng_set(rng, config.seed);

    // Print configuration
    std::cout << std::string(60, '=') << std::endl;
    std::cout << "CEvNS Monte Carlo Event Generator" << std::endl;
    std::cout << std::string(60, '=') << std::endl;
    std::cout << std::endl;

    std::cout << "Configuration:" << std::endl;
    std::cout << "  Reactor: " << config.power_GW << " GW at "
              << config.baseline_m << " m" << std::endl;
    std::cout << "  Detector: " << config.mass_kg << " kg (A="
              << config.A << ", Z=" << config.Z << ")" << std::endl;
    std::cout << "  Threshold: " << config.threshold_keV << " keV_ee" << std::endl;
    std::cout << "  Quenching: " << config.quenching << std::endl;
    std::cout << "  Resolution: " << config.resolution * 100.0 << "%" << std::endl;
    std::cout << "  Events: " << config.nevents << std::endl;
    std::cout << "  Output: " << config.output_file << std::endl;
    std::cout << "  Seed: " << config.seed << std::endl;
    std::cout << std::endl;

    // Open output file
    std::ofstream outfile(config.output_file);
    if (!outfile.is_open()) {
        std::cerr << "Error: Could not open output file!" << std::endl;
        return 1;
    }

    // Write CSV header
    outfile << "event_id,neutrino_energy_MeV,recoil_energy_keV_nr,detected_energy_keV_ee"
            << std::endl;

    // Generate events
    std::cout << "Generating events..." << std::endl;
    int n_detected = 0;
    int progress_interval = std::max(config.nevents / 20, 1);

    for (int i = 0; i < config.nevents; ++i) {
        // Progress bar
        if (i % progress_interval == 0 || i == config.nevents - 1) {
            double progress = static_cast<double>(i + 1) / config.nevents * 100.0;
            int bar_length = 40;
            int filled = static_cast<int>(bar_length * (i + 1) / config.nevents);
            std::cout << "\rProgress: [" << std::string(filled, '=')
                      << std::string(bar_length - filled, '-') << "] "
                      << std::fixed << std::setprecision(1) << progress << "% "
                      << std::flush;
        }

        // 1. Sample neutrino energy
        double E_nu = sample_neutrino_energy(rng);

        // 2. Sample recoil energy
        double T_recoil_MeV = sample_recoil_energy(E_nu, config.A, config.Z, rng);
        double T_recoil_keV = T_recoil_MeV * 1000.0;

        // 3. Apply detector response
        double E_detected_keV = apply_detector_response(T_recoil_keV, config.quenching,
                                                        config.resolution, rng);

        // 4. Write event to file
        outfile << (i + 1) << ","
                << E_nu << ","
                << T_recoil_keV << ","
                << E_detected_keV << std::endl;

        // Count detected events
        if (E_detected_keV >= config.threshold_keV) {
            n_detected++;
        }
    }

    std::cout << std::endl << std::endl;

    // Print results
    std::cout << "Results:" << std::endl;
    std::cout << "  Generated events: " << config.nevents << std::endl;
    std::cout << "  Passed threshold: " << n_detected
              << " (" << std::fixed << std::setprecision(1)
              << static_cast<double>(n_detected) / config.nevents * 100.0 << "%)" << std::endl;
    std::cout << std::endl;

    std::cout << "Output saved to: " << config.output_file << std::endl;

    outfile.close();
    gsl_rng_free(rng);

    return 0;
}
