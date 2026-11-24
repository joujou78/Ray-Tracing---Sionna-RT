"""Consistency and sanity tests for the vectorised propagation engine."""
import numpy as np
import pytest

from rfcov.p1812 import P1812Params, free_space_loss, knife_edge_j, path_loss, path_loss_batch


@pytest.mark.parametrize("model", ["p1812", "delta_bullington", "knife_edge", "fspl"])
def test_batch_equals_single_paths(model):
    """Every endpoint j of a batched radial must equal a standalone 0..j path."""
    rng = np.random.default_rng(0)
    n = 120
    d = np.linspace(0, 25, n)
    h = np.maximum(80 + np.cumsum(rng.normal(0, 8, (3, n)), axis=1), 0)
    clutter = rng.uniform(0, 15, (3, n))
    prm = P1812Params(f_ghz=0.9, htg=30, hrg=1.5, p=10, dn=42, n0=326)
    j = np.arange(4, n)
    phi = np.full((3, len(j)), 52.3)
    batch = path_loss_batch(d, h, j, prm, phi=phi, clutter=clutter, model=model)
    for b in range(3):
        for k in (0, 7, 40, len(j) - 1):
            jj = j[k]
            single = path_loss(d[: jj + 1], h[b, : jj + 1], prm, phi=52.3,
                               clutter=clutter[b, : jj + 1], model=model)
            assert batch[b, k] == pytest.approx(single, abs=1e-9)


def test_flat_los_close_to_free_space():
    d = np.linspace(0, 2, 50)
    h = np.zeros(50)
    prm = P1812Params(f_ghz=2.0, htg=50, hrg=50)
    lb = path_loss(d, h, prm, model="p1812")
    assert lb == pytest.approx(free_space_loss(2.0, 2.0), abs=0.5)


def test_knife_edge_grazing_is_6db():
    # J(0) is ~6.0 dB for a grazing knife edge (P.526)
    assert knife_edge_j(0.0) == pytest.approx(6.0, abs=0.05)


def test_obstruction_increases_loss():
    d = np.linspace(0, 10, 101)
    flat = np.zeros(101)
    hill = flat.copy()
    hill[50] = 120
    prm = P1812Params(f_ghz=0.9, htg=20, hrg=2)
    assert path_loss(d, hill, prm) > path_loss(d, flat, prm) + 10
