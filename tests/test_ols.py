"""Tests for OLS regression strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd

from regression_model.regression.ols import OLSStrategy


def test_ols_fit_returns_correct_structure():
    """OLS result contains expected fields and valid R-squared."""
    np.random.seed(42)
    n = 100
    x = pd.DataFrame({
        "D1": np.random.randn(n),
        "D2": np.random.randn(n),
    })
    y = pd.Series(0.5 * x["D1"] - 0.3 * x["D2"] + np.random.randn(n) * 0.1)

    strategy = OLSStrategy()
    result = strategy.fit("TARGET_1", y, x)

    assert result.target_figi == "TARGET_1"
    assert set(result.betas.keys()) == {"D1", "D2"}
    assert result.n_observations == 100
    assert 0 <= result.r_squared <= 1


def test_ols_fit_recovers_known_betas():
    """OLS accurately recovers known beta coefficients from noiseless data."""
    np.random.seed(0)
    n = 1000
    x = pd.DataFrame({
        "D1": np.random.randn(n),
        "D2": np.random.randn(n),
    })
    y = pd.Series(1.0 * x["D1"] + 2.0 * x["D2"] + 0.001)  # no noise

    strategy = OLSStrategy()
    result = strategy.fit("T", y, x)

    assert abs(result.betas["D1"] - 1.0) < 0.01
    assert abs(result.betas["D2"] - 2.0) < 0.01
    assert result.r_squared > 0.99
