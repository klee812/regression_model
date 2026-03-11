"""Tests for data preprocessing (validation, missing data, outliers)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from regression_model.data.preprocess import (
    handle_missing,
    handle_outliers,
    trim_lookback,
    validate_prices,
)
from regression_model.models import PriceData, ReturnsData
from regression_model.models.preprocessing_config import PreprocessingConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prices(
    target_values: list[list[float]],
    driver_values: list[list[float]],
    periods: int | None = None,
) -> PriceData:
    if periods is None:
        periods = len(target_values[0])
    dates = pd.date_range("2024-01-02", periods=periods, freq="B")
    targets = pd.DataFrame(
        {f"T{i}": v for i, v in enumerate(target_values)}, index=dates
    )
    targets.index.name = "date"
    drivers = pd.DataFrame(
        {f"D{i}": v for i, v in enumerate(driver_values)}, index=dates
    )
    drivers.index.name = "date"
    return PriceData(targets=targets, drivers=drivers)


def _make_returns(
    target_values: list[list[float]],
    driver_values: list[list[float]],
    periods: int | None = None,
) -> ReturnsData:
    if periods is None:
        periods = len(target_values[0])
    dates = pd.date_range("2024-01-02", periods=periods, freq="B")
    targets = pd.DataFrame(
        {f"T{i}": v for i, v in enumerate(target_values)}, index=dates
    )
    drivers = pd.DataFrame(
        {f"D{i}": v for i, v in enumerate(driver_values)}, index=dates
    )
    return ReturnsData(targets=targets, drivers=drivers)


# ---------------------------------------------------------------------------
# trim_lookback
# ---------------------------------------------------------------------------


class TestTrimLookback:
    def test_trims_to_lookback_days(self):
        """Only dates within lookback_days of the latest date are kept."""
        dates = pd.date_range("2024-01-02", periods=100, freq="B")
        targets = pd.DataFrame({"T0": range(100)}, index=dates, dtype=float)
        drivers = pd.DataFrame({"D0": range(100)}, index=dates, dtype=float)
        prices = PriceData(targets=targets, drivers=drivers)

        config = PreprocessingConfig(lookback_days=30)
        result = trim_lookback(prices, config)

        max_date = dates[-1]
        cutoff = max_date - pd.Timedelta(days=30)
        assert result.targets.index.min() >= cutoff
        assert result.drivers.index.min() >= cutoff
        assert result.targets.index.max() == max_date
        assert len(result.targets) < 100

    def test_zero_means_no_trimming(self):
        """lookback_days=0 keeps all data."""
        prices = _make_prices(
            [[100, 101, 102, 103, 104]],
            [[200, 201, 202, 203, 204]],
        )
        config = PreprocessingConfig(lookback_days=0)
        result = trim_lookback(prices, config)
        pd.testing.assert_frame_equal(result.targets, prices.targets)
        pd.testing.assert_frame_equal(result.drivers, prices.drivers)


# ---------------------------------------------------------------------------
# validate_prices
# ---------------------------------------------------------------------------


class TestValidatePrices:
    def test_raises_on_negative_prices(self):
        prices = _make_prices([[100, -1, 102]], [[200, 201, 202]])
        config = PreprocessingConfig(min_observations=1)
        with pytest.raises(ValueError, match="Non-positive prices"):
            validate_prices(prices, config)

    def test_raises_on_zero_prices(self):
        prices = _make_prices([[100, 0, 102]], [[200, 201, 202]])
        config = PreprocessingConfig(min_observations=1)
        with pytest.raises(ValueError, match="Non-positive prices"):
            validate_prices(prices, config)

    def test_raises_on_duplicate_dates(self):
        dates = pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-03"])
        targets = pd.DataFrame({"T0": [100, 101, 102]}, index=dates)
        drivers = pd.DataFrame({"D0": [200, 201, 202]}, index=dates)
        prices = PriceData(targets=targets, drivers=drivers)
        config = PreprocessingConfig(min_observations=1)
        with pytest.raises(ValueError, match="Duplicate dates"):
            validate_prices(prices, config)

    def test_raises_on_insufficient_observations(self):
        prices = _make_prices([[100, 101]], [[200, 201]])
        config = PreprocessingConfig(min_observations=5)
        with pytest.raises(ValueError, match="Insufficient observations"):
            validate_prices(prices, config)

    def test_passes_clean_data(self):
        prices = _make_prices(
            [[100, 101, 102, 103, 104]],
            [[200, 201, 202, 203, 204]],
        )
        config = PreprocessingConfig(min_observations=3)
        result = validate_prices(prices, config)
        pd.testing.assert_frame_equal(result.targets, prices.targets)

    def test_skipped_when_disabled(self):
        prices = _make_prices([[100, -1, 102]], [[200, 201, 202]])
        config = PreprocessingConfig(validate_prices=False, min_observations=1)
        # Should not raise
        validate_prices(prices, config)


# ---------------------------------------------------------------------------
# handle_missing
# ---------------------------------------------------------------------------


class TestHandleMissing:
    def test_drop(self):
        prices = _make_prices(
            [[100, np.nan, 102, 103]],
            [[200, 201, 202, 203]],
        )
        config = PreprocessingConfig(missing_data_handler="drop")
        result = handle_missing(prices, config)
        assert len(result.targets) == 3
        assert not result.targets.isna().any().any()

    def test_forward_fill(self):
        prices = _make_prices(
            [[100, np.nan, 102, 103]],
            [[200, 201, 202, 203]],
        )
        config = PreprocessingConfig(missing_data_handler="forward_fill")
        result = handle_missing(prices, config)
        assert len(result.targets) == 4
        assert not result.targets.isna().any().any()
        # forward-filled value should equal the previous value
        assert result.targets["T0"].iloc[1] == 100.0

    def test_forward_fill_drops_leading_nans(self):
        prices = _make_prices(
            [[np.nan, 101, 102, 103]],
            [[200, 201, 202, 203]],
        )
        config = PreprocessingConfig(missing_data_handler="forward_fill")
        result = handle_missing(prices, config)
        assert len(result.targets) == 3
        assert not result.targets.isna().any().any()

    def test_interpolate(self):
        prices = _make_prices(
            [[100, np.nan, 102, 103]],
            [[200, 201, 202, 203]],
        )
        config = PreprocessingConfig(missing_data_handler="interpolate")
        result = handle_missing(prices, config)
        assert len(result.targets) == 4
        assert not result.targets.isna().any().any()
        # interpolated value should be midpoint of 100 and 102
        assert abs(result.targets["T0"].iloc[1] - 101.0) < 1e-10


# ---------------------------------------------------------------------------
# handle_outliers
# ---------------------------------------------------------------------------


class TestHandleOutliers:
    def test_none_passes_through(self):
        returns = _make_returns(
            [[0.01, 0.02, -0.01]], [[0.005, 0.01, -0.005]]
        )
        config = PreprocessingConfig(outlier_method="none")
        result = handle_outliers(returns, config)
        pd.testing.assert_frame_equal(result.targets, returns.targets)
        pd.testing.assert_frame_equal(result.drivers, returns.drivers)

    def test_winsorize_clips_extreme_returns(self):
        # Create returns with one extreme value
        normal = [0.01] * 20
        values = normal + [0.50]  # 0.50 is far from the mean
        driver_vals = [0.005] * 21
        returns = _make_returns([values], [driver_vals])
        config = PreprocessingConfig(outlier_method="winsorize", outlier_threshold=3.0)
        result = handle_outliers(returns, config)
        # The extreme value should be clipped
        assert result.targets["T0"].iloc[-1] < 0.50
        # Non-extreme values should be unchanged
        assert abs(result.targets["T0"].iloc[0] - 0.01) < 1e-10

    def test_clip_is_alias_for_winsorize(self):
        values = [0.01] * 20 + [0.50]
        driver_vals = [0.005] * 21
        returns = _make_returns([values], [driver_vals])
        config_w = PreprocessingConfig(outlier_method="winsorize", outlier_threshold=3.0)
        config_c = PreprocessingConfig(outlier_method="clip", outlier_threshold=3.0)
        result_w = handle_outliers(returns, config_w)
        result_c = handle_outliers(returns, config_c)
        pd.testing.assert_frame_equal(result_w.targets, result_c.targets)
        pd.testing.assert_frame_equal(result_w.drivers, result_c.drivers)

    def test_drop_removes_extreme_rows(self):
        normal = [0.01] * 20
        values = normal + [0.50]
        driver_vals = [0.005] * 21
        returns = _make_returns([values], [driver_vals])
        config = PreprocessingConfig(outlier_method="drop", outlier_threshold=3.0)
        result = handle_outliers(returns, config)
        # The row with the extreme value should be dropped
        assert len(result.targets) == 20
        assert len(result.drivers) == 20
