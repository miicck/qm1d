import numpy as np
import math
from qm1d.functions import *
from qm1d.hilbert import Grid


def test_create_density():
    d = Density(Grid(-10, 10, 100))
    assert np.allclose(d.particles, 0)


def test_density_particles():
    d = Density(Grid(-10, 10, 1000))
    d.values = np.exp(-d.x.values ** 2)
    n = np.pi ** 0.5 * math.erf(10)
    assert np.allclose(d.particles, n)

    sqrt_d = Function(d.x)
    sqrt_d.values = d.values ** 0.5
    assert np.allclose(sqrt_d.inner_product(sqrt_d), n)


def test_potential_eigenstates():
    v = Potential(Grid(-20, 20, 1001))
    v.values = v.x.values ** 2
    eigs = v.diagonalize_hamiltonian()

    # Check eigenvalues are correct
    omega = 2 ** 0.5
    evals = [omega * (0.5 + i) for i in range(len(eigs.eigenvalues))]

    # Check the lowest-lying states are reproduced well
    assert_all_close(eigs.eigenvalues[:20], evals[:20], rtol=0.01)

    # Check first eigenstate is correct
    exp = np.exp(-(v.x.values * omega ** 0.5) ** 2 / 2)
    exp /= np.trapz(exp * exp, v.x.values) ** 0.5
    assert np.allclose(eigs.orbitals[0].values, exp, rtol=0.01)


def test_density_potential():
    for n in [0.1, 1, 1.5, 2]:
        # Setup a potential and get density
        v = Potential(Grid(-8, 8, 101))
        v.values = v.x.values ** 2
        s = v.diagonalize_hamiltonian()
        d = s.density(n)

        # Calculate potential from density
        vd = d.calculate_potential(n_elec_tol=0.1)

        # Re-calculate density
        svd = vd.diagonalize_hamiltonian()
        dvd = svd.density(n)

        # Check same to within n_elec_tol
        assert sum(d.values - dvd.values) * v.x.spacing < 0.1


def test_density_from_orbitals():
    d = Density(Grid(-10, 10, 100))
    d.values = np.exp(-(d.x.values - 1) ** 2) + np.exp(-(d.x.values + 1) ** 2)
    d.particles = 3
    v = d.calculate_potential(n_elec_tol=0.1)
    e = v.diagonalize_hamiltonian()
    delta_d = Density(d.x, abs(e.density(3).values - d.values))
    assert delta_d.particles < 0.1


def test_ke_from_orbitals(plot=False):
    grid = Grid(-8, 8, 101)
    v = Potential(grid, 0.5 * grid.values ** 2)
    spectrum = v.diagonalize_hamiltonian()

    if plot:
        import matplotlib.pyplot as plt
        from functionals import KELDA
        N = 2
        rho = spectrum.density(N)
        ke_dens = spectrum.kinetic_energy_density(N)

        print(KELDA(v).apply(rho, plot=plot), spectrum.kinetic_energy(N))

        plt.subplot(121)
        plt.plot(v.x.values, v.values, label="v")
        plt.plot(v.x.values, rho.values, label="rho")
        plt.plot(v.x.values, ke_dens.values, label="tau")
        plt.plot(v.x.values, v.values + ke_dens.values, label="v + tau")

        plt.subplot(122)
        from ladder import plot_orbitals
        plot_orbitals(plt, spectrum.orbitals[:N])

        plt.legend()
        plt.show()

    assert np.allclose(spectrum.kinetic_energy(5.5),
                       spectrum.kinetic_energy_density(5.5).inner_product(spectrum.density(5.5)))


def test_aufbau():
    assert np.allclose(OrbitalSpectrum.aufbau_weights(1.5), [1, 0.5])
    assert np.allclose(OrbitalSpectrum.aufbau_weights(1.0), [1])
    assert np.allclose(OrbitalSpectrum.aufbau_weights(1.00001), [1, 0.00001])
    assert np.allclose(OrbitalSpectrum.aufbau_weights(2.5), [1, 1, 0.5])
