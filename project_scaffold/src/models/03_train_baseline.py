"""Phase 3 XGBoost baseline configuration, predictor allow-list, and splits."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "features.parquet"

# Fixed before Phase 3 results are examined; no class reweighting or imputation.
MODEL_CONFIG = {
    "learning_rate": 0.05,
    "max_depth": 4,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 5,
    "reg_lambda": 1.0,
    "n_estimators": 1000,
    "early_stopping_rounds": 50,
    "eval_metric": "logloss",
    "tree_method": "hist",
}

VITALS = ("heart_rate", "sbp", "dbp", "map", "resp_rate", "spo2", "temperature")
LABS = (
    "lactate", "creatinine", "wbc", "platelets", "bun", "glucose",
    "potassium", "sodium", "bicarbonate",
)
FORBIDDEN = {
    "subject_id", "hadm_id", "stay_id", "intime", "outtime", "los",
    "age_group", "anchor_year_group", "race_group", "insurance_group", "mortality",
}


def predictor_columns(
    df: pd.DataFrame, use_measured_flags: bool, drop_lactate: bool = False
) -> list[str]:
    columns = ["anchor_age", "sex"]
    columns += [f"{name}_{stat}" for name in VITALS for stat in ("min", "max", "mean")]
    columns += ["gcs_min", "intubated"]
    labs = [name for name in LABS if not (drop_lactate and name == "lactate")]
    columns += [f"{name}_{stat}" for name in labs for stat in ("min", "max", "mean")]
    if use_measured_flags:
        columns += [f"{name}_measured" for name in labs]
    missing = [name for name in columns if name not in df.columns]
    if missing:
        raise ValueError(f"Required allow-listed feature columns missing: {missing}")
    if set(columns) & FORBIDDEN:
        raise AssertionError(f"Forbidden predictors selected: {set(columns) & FORBIDDEN}")
    return columns


def split_indices(df: pd.DataFrame, seed: int):
    """50/25/25 split stratified on mortality x race_group; no fitting occurs here."""
    if not df["subject_id"].is_unique:
        raise AssertionError("subject_id must be unique")
    strata = df["mortality"].astype(str) + "_" + df["race_group"].astype(str)
    indices = np.arange(len(df))
    train, remainder = train_test_split(
        indices, test_size=0.5, random_state=seed, stratify=strata
    )
    cal, test = train_test_split(
        remainder, test_size=0.5, random_state=seed, stratify=strata.iloc[remainder]
    )
    parts = (train, cal, test)
    if sum(map(len, parts)) != len(df):
        raise AssertionError("split sizes do not add up")
    if any(np.intersect1d(parts[i], parts[j]).size for i in range(3) for j in range(i + 1, 3)):
        raise AssertionError("train, calibration, and test must be disjoint")
    races = set(df["race_group"])
    for name, ix in zip(("train", "calibration", "test"), parts):
        if set(df.iloc[ix]["race_group"]) != races:
            raise AssertionError(f"every race_group must occur in {name}")
    return train, cal, test


def fit_baseline(X_train, y_train, seed: int):
    """Fit only on train, using a 15% early-stopping slice drawn from train."""
    fit_ix, es_ix = train_test_split(
        np.arange(len(y_train)), test_size=0.15, random_state=seed, stratify=y_train
    )
    cfg = {k: v for k, v in MODEL_CONFIG.items() if k != "early_stopping_rounds"}
    cfg.update(random_state=seed, n_jobs=-1)
    model = XGBClassifier(**cfg, early_stopping_rounds=MODEL_CONFIG["early_stopping_rounds"])
    model.fit(
        X_train.iloc[fit_ix], y_train[fit_ix],
        eval_set=[(X_train.iloc[es_ix], y_train[es_ix])],
        verbose=False,
    )
    return model


def main():
    """Convenience entry point: the paired conformal script orchestrates runs."""
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing input: {FEATURES_PATH}")
    print(f"Phase 3 model configuration: {MODEL_CONFIG}")
    print(f"Input available: {FEATURES_PATH}")
    print("Run src/conformal/03b_split_conformal.py to execute both variants.")


if __name__ == "__main__":
    main()
