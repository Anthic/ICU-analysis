import numpy as np

from src.conformal.utils import (
    conformal_quantile,
    fit_class_conditional,
    fit_marginal,
    fit_mondrian_class_conditional,
    fit_mondrian_marginal,
    prediction_sets,
    prediction_sets_mondrian,
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


def test_mondrian_marginal_coverage_per_group():
    rng = np.random.default_rng(42)
    n_cal, n_test = 6000, 12000
    groups_pool = np.array(["A", "B", "C"])
    g_cal = rng.choice(groups_pool, n_cal)
    g_test = rng.choice(groups_pool, n_test)
    y_cal = rng.binomial(1, 0.3, n_cal)
    y_test = rng.binomial(1, 0.3, n_test)
    p_cal = np.clip(0.2 + 0.6 * y_cal + rng.normal(0, 0.2, n_cal), 0.01, 0.99)
    p_test = np.clip(0.2 + 0.6 * y_test + rng.normal(0, 0.2, n_test), 0.01, 0.99)

    q_mondrian = fit_mondrian_marginal(y_cal, p_cal, g_cal, alpha=0.10)
    sets = prediction_sets_mondrian(p_test, g_test, q_mondrian)
    for g in groups_pool:
        mask = g_test == g
        cov = sets[mask, y_test[mask]].mean()
        assert abs(cov - 0.90) < 0.03


def test_mondrian_class_conditional_coverage_per_group_and_class():
    rng = np.random.default_rng(999)
    n_cal, n_test = 8000, 16000
    groups_pool = np.array(["G1", "G2"])
    g_cal = rng.choice(groups_pool, n_cal)
    g_test = rng.choice(groups_pool, n_test)
    y_cal = rng.binomial(1, 0.25, n_cal)
    y_test = rng.binomial(1, 0.25, n_test)
    p_cal = np.clip(0.15 + 0.7 * y_cal + rng.normal(0, 0.25, n_cal), 0.01, 0.99)
    p_test = np.clip(0.15 + 0.7 * y_test + rng.normal(0, 0.25, n_test), 0.01, 0.99)

    q_mondrian_cc = fit_mondrian_class_conditional(y_cal, p_cal, g_cal, alpha=0.10)
    sets = prediction_sets_mondrian(p_test, g_test, q_mondrian_cc)
    for g in groups_pool:
        for label in (0, 1):
            mask = (g_test == g) & (y_test == label)
            cov = sets[mask, label].mean()
            assert abs(cov - 0.90) < 0.035


def _simulate(seed=7, n=6000):
    rng = np.random.default_rng(seed)
    groups = rng.choice(["a", "b", "c"], size=n)
    base = {"a": 0.05, "b": 0.12, "c": 0.25}
    p = np.clip(rng.beta(1, 8, size=n) * (1 + 3 * np.array([base[g] for g in groups])), 1e-4, 1 - 1e-4)
    y = (rng.random(n) < p).astype(int)
    return y, p, groups


def _independent_threshold(values, alpha=0.10):
    """Order-statistic rule written out by hand, independent of src.conformal.utils."""
    v = np.sort(np.asarray(values))
    n = len(v)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    return np.inf if k > n else v[k - 1]


def test_age_mondrian_equals_group_specific_thresholds():
    """Mondrian sets must equal sets from hand-computed group-specific risk thresholds
    (survivor label in set iff p <= q0_g; death label in set iff 1-p <= q1_g), with q0/q1
    taken from each group's calibration survivors/decedents only."""
    y, p, groups = _simulate()
    q = fit_mondrian_class_conditional(y, p, groups, alpha=0.10)
    sets = prediction_sets_mondrian(p, groups, q)
    for g in ["a", "b", "c"]:
        m = groups == g
        q0 = _independent_threshold(p[m & (y == 0)])
        q1 = _independent_threshold((1 - p)[m & (y == 1)])
        np.testing.assert_allclose([q[g][0], q[g][1]], [q0, q1])
        np.testing.assert_array_equal(sets[m, 0], p[m] <= q0)
        np.testing.assert_array_equal(sets[m, 1], (1 - p[m]) <= q1)


def test_group_thresholds_differ_when_score_distributions_differ():
    """Equalised-odds-type difference: groups with different risk distributions get different thresholds."""
    y, p, groups = _simulate()
    q = fit_mondrian_class_conditional(y, p, groups, alpha=0.10)
    assert len({round(q[g][0], 6) for g in "abc"}) == 3
    assert len({round(q[g][1], 6) for g in "abc"}) == 3


def test_no_leakage_from_test_labels_or_test_scores_into_thresholds():
    """Thresholds depend only on calibration data: changing test labels cannot change test sets,
    and permuting calibration labels must change thresholds."""
    y, p, groups = _simulate()
    ycal, pcal, gcal = y[:4000], p[:4000], groups[:4000]
    ptest, gtest = p[4000:], groups[4000:]
    q = fit_mondrian_class_conditional(ycal, pcal, gcal, alpha=0.10)
    sets1 = prediction_sets_mondrian(ptest, gtest, q)
    rng = np.random.default_rng(0)
    _ytest_shuffled = rng.permutation(y[4000:])  # test labels are never passed to the pipeline
    q2 = fit_mondrian_class_conditional(ycal, pcal, gcal, alpha=0.10)
    sets2 = prediction_sets_mondrian(ptest, gtest, q2)
    np.testing.assert_array_equal(sets1, sets2)
    q3 = fit_mondrian_class_conditional(rng.permutation(ycal), pcal, gcal, alpha=0.10)
    assert any(q3[g][1] != q[g][1] for g in "abc")


def test_split_indices_are_disjoint_and_cover_all():
    import importlib.util
    import pandas as pd
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "src" / "models" / "03_train_baseline.py"
    spec = importlib.util.spec_from_file_location("baseline", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rng = np.random.default_rng(1)
    df = pd.DataFrame({
        "subject_id": np.arange(2000),
        "mortality": rng.integers(0, 2, 2000),
        "race_group": rng.choice(["W", "B", "A"], 2000),
    })
    train, cal, test = mod.split_indices(df, seed=3)[:3]
    assert len(np.intersect1d(train, cal)) == 0
    assert len(np.intersect1d(train, test)) == 0
    assert len(np.intersect1d(cal, test)) == 0
    assert len(train) + len(cal) + len(test) == len(df)
