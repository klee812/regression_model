"""Shared test fixtures."""

from __future__ import annotations

import pandas as pd
import pytest

from regression_model.models import PriceData


@pytest.fixture
def sample_prices() -> PriceData:
    """Small price DataFrames for testing."""
    dates = pd.date_range("2024-01-02", periods=10, freq="B")

    targets = pd.DataFrame(
        {"BBG000BVPV84": [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]},
        index=dates,
    )
    targets.index.name = "date"

    drivers = pd.DataFrame(
        {
            "BBG0000DYRK6": [200, 204, 202, 206, 210, 208, 212, 216, 214, 218],
            "BBG000BB2N45": [50, 49, 51, 50, 52, 51, 53, 52, 54, 53],
        },
        index=dates,
    )
    drivers.index.name = "date"

    return PriceData(targets=targets, drivers=drivers)
