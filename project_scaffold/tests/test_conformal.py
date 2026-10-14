import numpy as np

from src.conformal.utils import (
    conformal_quantile,
    fit_class_conditional,
    fit_marginal,
    prediction_sets,
)


def test_marginal_coverage_within_sampling_error():
    rng = np.random.default_rng(2026)
    n_cal, n_test = 4000, 12000
    y_cal = rng.binomial(1, 0.35, n_cal)
    y_test = rng.binomial(1, 0.35, n_test)
    p_cal = np.clip(0.15 + 0.7 * y_cal + rng.normal(0, 0.25, n_cal), 0.01, 0.99)
    p_test = np.clip(0.15 + 0.7 * y_test + rng.normal(0, 0.25, n_test), 0.01, 0.99)
    sets = prediction_sets(p_test, fit_marginal(y_cal, p_cal))
    coverage = sets[np.arange(n_test), y_test].mean()
    assert abs(coverage - 0.90) < 0.025


def test_class_conditional_coverage_per_class_within_sampling_error():
    rng = np.random.default_rng(1337)
    n_cal, n_test = 6000, 16000
    y_cal = rng.binomial(1, 0.3, n_cal)
    y_test = rng.binomial(1, 0.3, n_test)
    p_cal = np.clip(0.1 + 0.75 * y_cal + rng.normal(0, 0.28, n_cal), 0.01, 0.99)
    p_test = np.clip(0.1 + 0.75 * y_test + rng.normal(0, 0.28, n_test), 0.01, 0.99)
    sets = prediction_sets(p_test, fit_class_conditional(y_cal, p_cal))
    for label in (0, 1):
        covered = sets[y_test == label, label].mean()
        assert abs(covered - 0.90) < 0.04


def test_level_above_one_returns_infinity_and_full_sets():
    qhat = conformal_quantile([0.1, 0.2, 0.3], alpha=0.1)
    assert np.isinf(qhat)
    assert prediction_sets([0, 0.5, 1], qhat).all()


def test_empty_prediction_sets_are_representable():
    sets = prediction_sets([0.5], 0.1)
    assert sets.shape == (1, 2)
    assert not sets.any()


def test_conformal_quantile_exact_order_statistic_ranks():
    assert conformal_quantile(np.arange(1, 20), alpha=0.10) == 18
    assert conformal_quantile(np.arange(1, 10), alpha=0.10) == 9
    assert np.isinf(conformal_quantile(np.arange(1, 9), alpha=0.10))
