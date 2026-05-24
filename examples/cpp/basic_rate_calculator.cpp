/*
 * Basic CEvNS Rate Calculator
 *
 * Calculate total event rate for reactor-based CEvNS experiments.
 *
 * Compilation:
 *   g++ -o basic_rate_calculator basic_rate_calculator.cpp \
 *       -lglobes -lgsl -lgslcblas -lm -O2
 *
 * Usage:
 *   ./basic_rate_calculator [baseline_m] [power_GW] [mass_kg] [A] [Z]
 */

#include <iostream>
#include <cmath>
#include <iomanip>
#include <gsl/gsl_integration.h>

// Physical constants
const double GF = 1.1663787e-5;  // GeV^-2, Fermi constant
const double SIN2TW = 0.23121;   // sin^2(theta_W)
const double HBARC = 0.1973;     // GeV·fm
const double MEV_TO_GEV = 0.001;
const double CM2_TO_GEV2 = 2.568e+27;  // 1 cm^2 in GeV^-2 via (hbar*c)^2
const double NA = 6.022e23;      // Avogadro's number
const double AMU_TO_KG = 1.66054e-27;  // Atomic mass unit to kg

// Calculate weak nuclear charge
double weak_charge(int A, int Z) {
    int N = A - Z;
    return static_cast<double>(N) - static_cast<double>(Z) * (1.0 - 4.0 * SIN2TW);
}

// Helm form factor
double helm_form_factor(double Q2_GeV2, double A) {
    double R0 = 1.2 * std::pow(static_cast<double>(A), 1.0/3.0);  // fm
    double s = 0.9;  // fm
    double RA = std::sqrt(R0*R0 - 5.0*s*s);

    double q = std::sqrt(Q2_GeV2) / HBARC;  // fm^-1
    double qRA = q * RA;
    double qs = q * s;

    // Spherical Bessel function j1(x)/x = (sin x - x cos x)/x^3
    double j1_over_qRA;
    if (qRA < 0.01) {
        j1_over_qRA = 1.0/3.0 - qRA*qRA/30.0;
    } else {
        j1_over_qRA = (std::sin(qRA) - qRA*std::cos(qRA)) / (qRA*qRA*qRA);
    }

    double F = 3.0 * j1_over_qRA * std::exp(-qs*qs/2.0);
    return F * F;
}

// CEvNS differential cross section dσ/dT [cm^2/GeV]
double cevns_dsigma_dT(double E_nu_GeV, double T_GeV, int A, int Z) {
    double MA = static_cast<double>(A) * 0.9315;  // GeV
    double QW = weak_charge(A, Z);
    double Q2 = 2.0 * MA * T_GeV;  // GeV^2

    // Form factor
    double F2 = helm_form_factor(Q2, A);

    // Kinematic factor
    double kinematic = 1.0 - (MA * T_GeV) / (2.0 * E_nu_GeV * E_nu_GeV);

    if (kinematic < 0.0) return 0.0;

    // Differential cross section
    double dsigma = (GF * GF * MA) / (4.0 * M_PI);
    dsigma *= QW * QW * F2 * kinematic;
    dsigma /= CM2_TO_GEV2;  // Convert to cm^2

    return dsigma;
}

// Simplified reactor flux (U-235, Huber parameterization)
double reactor_flux_U235(double E_MeV) {
    if (E_MeV < 1.8 || E_MeV > 8.0) return 0.0;

    // Huber parameterization coefficients for U-235
    double a0 = 3.217, a1 = -3.111, a2 = 1.395;
    double a3 = -0.369, a4 = 0.0445, a5 = -0.00202;

    double E = E_MeV;
    double log_flux = a0 + a1*E + a2*E*E + a3*E*E*E + a4*E*E*E*E + a5*E*E*E*E*E;

    return std::exp(log_flux);
}

// Structure for integration parameters
struct integration_params {
    int A;
    int Z;
    double E_nu_GeV;
};

// Integrand for total cross section
double xsec_integrand(double T_GeV, void *params) {
    integration_params *p = static_cast<integration_params*>(params);
    return cevns_dsigma_dT(p->E_nu_GeV, T_GeV, p->A, p->Z);
}

// Calculate total cross section for given neutrino energy
double calculate_total_xsec(double E_nu_MeV, int A, int Z) {
    double E_nu_GeV = E_nu_MeV * MEV_TO_GEV;
    double MA_GeV = static_cast<double>(A) * 0.9315;

    // Maximum recoil energy
    double T_max_GeV = 2.0 * E_nu_GeV * E_nu_GeV / (MA_GeV + 2.0 * E_nu_GeV);

    if (T_max_GeV <= 0.0) return 0.0;

    // Setup GSL integration
    integration_params params = {A, Z, E_nu_GeV};
    gsl_integration_workspace *w = gsl_integration_workspace_alloc(1000);

    gsl_function F;
    F.function = &xsec_integrand;
    F.params = &params;

    double result, error;
    gsl_integration_qag(&F, 0.0, T_max_GeV, 0, 1e-7, 1000,
                       GSL_INTEG_GAUSS61, w, &result, &error);

    gsl_integration_workspace_free(w);

    return result;
}

// Structure for rate integration
struct rate_params {
    int A;
    int Z;
    double flux_norm;
};

// Integrand for event rate (flux × cross section)
double rate_integrand(double E_nu_MeV, void *params) {
    rate_params *p = static_cast<rate_params*>(params);

    double flux = reactor_flux_U235(E_nu_MeV);
    double xsec = calculate_total_xsec(E_nu_MeV, p->A, p->Z);

    return flux * xsec;
}

// Calculate total event rate
double calculate_event_rate(double power_GW, double baseline_m,
                           double mass_kg, int A, int Z) {
    // Number of target nuclei
    double M_nucleus_kg = static_cast<double>(A) * AMU_TO_KG;
    double N_targets = mass_kg / M_nucleus_kg;

    // Reactor flux normalization
    double energy_per_fission_J = 200.0 * 1.6e-13;  // 200 MeV in Joules
    double power_W = power_GW * 1e9;
    double fissions_per_sec = power_W / energy_per_fission_J;
    double nu_per_fission = 6.0;
    double L_cm = baseline_m * 100.0;
    double flux_norm = fissions_per_sec * nu_per_fission / (4.0 * M_PI * L_cm * L_cm);

    // Setup integration over neutrino energy
    rate_params params = {A, Z, flux_norm};
    gsl_integration_workspace *w = gsl_integration_workspace_alloc(1000);

    gsl_function F;
    F.function = &rate_integrand;
    F.params = &params;

    double result, error;
    gsl_integration_qag(&F, 1.8, 8.0, 0, 1e-5, 1000,
                       GSL_INTEG_GAUSS61, w, &result, &error);

    gsl_integration_workspace_free(w);

    // Total rate
    double rate = flux_norm * N_targets * result;
    rate *= 86400.0;  // Convert to per day

    return rate;
}

int main(int argc, char *argv[]) {
    // Default parameters (1 kg Ge at 25m from 3 GW reactor)
    double baseline_m = 25.0;
    double power_GW = 3.0;
    double mass_kg = 1.0;
    int A = 73;  // Germanium-73
    int Z = 32;

    // Parse command line arguments
    if (argc >= 6) {
        baseline_m = std::atof(argv[1]);
        power_GW = std::atof(argv[2]);
        mass_kg = std::atof(argv[3]);
        A = std::atoi(argv[4]);
        Z = std::atoi(argv[5]);
    } else if (argc > 1 && argc < 6) {
        std::cerr << "Usage: " << argv[0] << " [baseline_m] [power_GW] [mass_kg] [A] [Z]" << std::endl;
        std::cerr << "Using default parameters..." << std::endl;
    }

    // Print configuration
    std::cout << std::string(60, '=') << std::endl;
    std::cout << "CEvNS Event Rate Calculation" << std::endl;
    std::cout << std::string(60, '=') << std::endl;
    std::cout << std::endl;

    std::cout << "Configuration:" << std::endl;
    std::cout << "  Reactor: " << power_GW << " GW thermal at "
              << baseline_m << " m baseline" << std::endl;
    std::cout << "  Detector: " << mass_kg << " kg (A=" << A << ", Z=" << Z << ")" << std::endl;
    std::cout << std::endl;

    // Calculate physics parameters
    double QW = weak_charge(A, Z);
    double M_nucleus_kg = static_cast<double>(A) * AMU_TO_KG;
    double N_targets = mass_kg / M_nucleus_kg;

    std::cout << "Physics:" << std::endl;
    std::cout << "  Weak charge Q_W: " << std::fixed << std::setprecision(2) << QW << std::endl;
    std::cout << "  Number of targets: " << std::scientific << std::setprecision(3)
              << N_targets << std::endl;
    std::cout << std::endl;

    // Calculate cross section at reference energy
    std::cout << "Calculating event rate..." << std::endl;
    double xsec_3MeV = calculate_total_xsec(3.0, A, Z);

    // Calculate event rate
    double rate_per_day = calculate_event_rate(power_GW, baseline_m, mass_kg, A, Z);
    double rate_per_year = rate_per_day * 365.25;
    double rate_per_ton_year = rate_per_year * (1000.0 / mass_kg);

    // Print results
    std::cout << std::endl;
    std::cout << "Results:" << std::endl;
    std::cout << "  Event rate: " << std::fixed << std::setprecision(2)
              << rate_per_day << " events/day" << std::endl;
    std::cout << "              " << std::fixed << std::setprecision(0)
              << rate_per_year << " events/year" << std::endl;
    std::cout << "              " << std::scientific << std::setprecision(3)
              << rate_per_ton_year << " events/ton/year" << std::endl;
    std::cout << std::endl;

    std::cout << "Cross section check (3 MeV): " << std::scientific
              << std::setprecision(3) << xsec_3MeV << " cm²" << std::endl;

    double F2_test = helm_form_factor(0.01, A);  // Q² = 0.01 GeV²
    std::cout << "Form factor F²(Q²=0.01 GeV²): " << std::fixed
              << std::setprecision(3) << F2_test << std::endl;

    return 0;
}
