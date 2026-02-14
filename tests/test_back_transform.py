"""Tests that pipeline back-transformed OLS betas match plain OLS."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from regression_model.regression.ols import OLSStrategy


def test_pipeline_betas_match_plain_ols():
    """Back-transformed pipeline coefficients match direct OLS fit."""
    np.random.seed(99)
    n = 500
    x = pd.DataFrame({
        "D1": np.random.randn(n) * 10 + 5,   # non-zero mean, large scale
        "D2": np.random.randn(n) * 0.01 - 2,  # different scale
    })
    y = pd.Series(0.7 * x["D1"] - 1.5 * x["D2"] + 3.0 + np.random.randn(n) * 0.001)

    # Pipeline-based OLS
    strategy = OLSStrategy()
    result = strategy.fit("T", y, x)

    # Direct (plain) OLS for reference
    plain = LinearRegression()
    plain.fit(x, y)

    assert abs(result.betas["D1"] - plain.coef_[0]) < 1e-6
    assert abs(result.betas["D2"] - plain.coef_[1]) < 1e-6
    assert abs(result.intercept - plain.intercept_) < 1e-6
    assert abs(result.r_squared - plain.score(x, y)) < 1e-10
