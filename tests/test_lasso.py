"""Tests for Lasso regression strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd

from regression_model.regression.lasso import LassoStrategy


def test_lasso_fit_returns_correct_structure():
    """Lasso result contains expected fields and valid R-squared."""
    np.random.seed(42)
    n = 100
    x = pd.DataFrame({
        "D1": np.random.randn(n),
        "D2": np.random.randn(n),
    })
    y = pd.Series(0.5 * x["D1"] - 0.3 * x["D2"] + np.random.randn(n) * 0.1)

    strategy = LassoStrategy(alpha=0.01)
    result = strategy.fit("TARGET_1", y, x)

    assert result.target_figi == "TARGET_1"
    assert set(result.betas.keys()) == {"D1", "D2"}
    assert result.n_observations == 100
    assert 0 <= result.r_squared <= 1


def test_lasso_fit_recovers_known_betas():
    """Lasso recovers known betas with low regularization."""
    np.random.seed(0)
    n = 1000
    x = pd.DataFrame({
        "D1": np.random.randn(n),
        "D2": np.random.randn(n),
    })
    y = pd.Series(1.0 * x["D1"] + 2.0 * x["D2"] + 0.001)

    strategy = LassoStrategy(alpha=1e-6)
    result = strategy.fit("T", y, x)

    assert abs(result.betas["D1"] - 1.0) < 0.05
    assert abs(result.betas["D2"] - 2.0) < 0.05
    assert result.r_squared > 0.99


def test_lasso_sparsity():
    """High alpha drives some coefficients to zero."""
    np.random.seed(42)
    n = 200
    x = pd.DataFrame({
        "D1": np.random.randn(n),
        "D2": np.random.randn(n),
        "D3": np.random.randn(n),
    })
    # y depends only on D1
    y = pd.Series(1.0 * x["D1"] + np.random.randn(n) * 0.01)

    strategy = LassoStrategy(alpha=0.1)
    result = strategy.fit("T", y, x)

    # D1 should be nonzero, at least one of D2/D3 should be zero or near-zero
    assert abs(result.betas["D1"]) > 0.1
    assert abs(result.betas["D2"]) < 0.1 or abs(result.betas["D3"]) < 0.1
