"""Tests for ElasticNet regression strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd

from regression_model.regression.elastic_net import ElasticNetStrategy


def test_elastic_net_fit_returns_correct_structure():
    """ElasticNet result contains expected fields and valid R-squared."""
    np.random.seed(42)
    n = 100
    x = pd.DataFrame({
        "D1": np.random.randn(n),
        "D2": np.random.randn(n),
    })
    y = pd.Series(0.5 * x["D1"] - 0.3 * x["D2"] + np.random.randn(n) * 0.1)

    strategy = ElasticNetStrategy(alpha=0.01)
    result = strategy.fit("TARGET_1", y, x)

    assert result.target_figi == "TARGET_1"
    assert set(result.betas.keys()) == {"D1", "D2"}
    assert result.n_observations == 100
    assert 0 <= result.r_squared <= 1


def test_elastic_net_fit_recovers_known_betas():
    """ElasticNet recovers known betas with low regularization."""
    np.random.seed(0)
    n = 1000
    x = pd.DataFrame({
        "D1": np.random.randn(n),
        "D2": np.random.randn(n),
    })
    y = pd.Series(1.0 * x["D1"] + 2.0 * x["D2"] + 0.001)

    strategy = ElasticNetStrategy(alpha=1e-6)
    result = strategy.fit("T", y, x)

    assert abs(result.betas["D1"] - 1.0) < 0.05
    assert abs(result.betas["D2"] - 2.0) < 0.05
    assert result.r_squared > 0.99
