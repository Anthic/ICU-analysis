"""Manual split-conformal prediction sets for binary classification."""

from __future__ import annotations

import numpy as np


def conformal_quantile(scores, alpha: float = 0.10) -> float:
    """Finite-sample higher quantile, or +inf when the requested level exceeds 1."""
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or scores.size == 0:
        raise ValueError("scores must be a non-empty one-dimensional array")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    k = int(np.ceil((scores.size + 1) * (1 - alpha)))
    if k > scores.size:
        return float("inf")
    return float(np.sort(scores)[k - 1])


def true_label_scores(y_true, p_hat) -> np.ndarray:
    y_true = np.asarray(y_true, dtype=int)
    p_hat = np.asarray(p_hat, dtype=float)
    if y_true.ndim != 1 or p_hat.shape != y_true.shape:
        raise ValueError("y_true and p_hat must be equal-length one-dimensional arrays")
    if not np.isin(y_true, [0, 1]).all() or not np.isfinite(p_hat).all():
        raise ValueError("labels must be binary and probabilities finite")
    if ((p_hat < 0) | (p_hat > 1)).any():
        raise ValueError("probabilities must be in [0, 1]")
    return np.where(y_true == 1, 1 - p_hat, p_hat)


def prediction_sets(p_hat, qhat) -> np.ndarray:
    """Return boolean (n, 2) membership for labels 0 and 1; empty sets are allowed."""
    p_hat = np.asarray(p_hat, dtype=float)
    if p_hat.ndim != 1 or not np.isfinite(p_hat).all() or ((p_hat < 0) | (p_hat > 1)).any():
        raise ValueError("p_hat must be a finite one-dimensional probability array")
    q = np.asarray(qhat, dtype=float)
    if q.ndim == 0:
        q = np.repeat(q, 2)
    if q.shape != (2,):
        raise ValueError("qhat must be a scalar or two class-specific quantiles")
    return np.column_stack((p_hat <= q[0], (1 - p_hat) <= q[1]))


def fit_marginal(y_cal, p_cal, alpha: float = 0.10) -> float:
    return conformal_quantile(true_label_scores(y_cal, p_cal), alpha)


def fit_class_conditional(y_cal, p_cal, alpha: float = 0.10) -> np.ndarray:
    y_cal = np.asarray(y_cal, dtype=int)
    scores = true_label_scores(y_cal, p_cal)
    quantiles = []
    for label in (0, 1):
        class_scores = scores[y_cal == label]
        if class_scores.size == 0:
            raise ValueError(f"calibration data contain no examples of class {label}")
        quantiles.append(conformal_quantile(class_scores, alpha))
    return np.asarray(quantiles)
