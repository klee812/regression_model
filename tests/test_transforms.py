"""Tests for price-to-returns transformation."""

from __future__ import annotations

import pandas as pd

from regression_model.data.transforms import prices_to_returns
from regression_model.models import PriceData


def test_prices_to_returns_computes_pct_change(sample_prices):
    """Percent-change returns are computed correctly from prices."""
    returns = prices_to_returns(sample_prices)

    # first row of prices is dropped (pct_change produces NaN)
    assert len(returns.targets) == 9
    assert len(returns.drivers) == 9

    # check a specific return: 102/100 - 1 = 0.02
    first_return = returns.targets["BBG000BVPV84"].iloc[0]
    assert abs(first_return - 0.02) < 1e-10


def test_prices_to_returns_aligns_dates():
    """Targets and drivers are aligned to overlapping dates only."""
    dates_t = pd.date_range("2024-01-02", periods=5, freq="B")
    dates_d = pd.date_range("2024-01-03", periods=5, freq="B")  # offset by 1 day

    targets = pd.DataFrame({"T1": [100, 101, 102, 103, 104]}, index=dates_t)
    drivers = pd.DataFrame({"D1": [200, 201, 202, 203, 204]}, index=dates_d)

    prices = PriceData(targets=targets, drivers=drivers)
    returns = prices_to_returns(prices)

    # only overlapping dates should remain
    assert (returns.targets.index == returns.drivers.index).all()


def test_prices_to_returns_no_nans(sample_prices):
    """Returned DataFrames contain no NaN values."""
    returns = prices_to_returns(sample_prices)

    assert not returns.targets.isna().any().any()
    assert not returns.drivers.isna().any().any()
