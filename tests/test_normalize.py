"""Tests for the market data normalization pipeline."""

from __future__ import annotations

import pandas as pd
import pytest

from regression_model.data.normalize import (
    adjust_for_corp_actions,
    adjust_for_dividends,
    build_price_table,
    convert_to_usd,
    normalize,
)


def test_build_price_table():
    """Price dicts produce a wide DataFrame and currency mapping."""
    records = [
        {"identifier": "A", "currency": "USD", "date": "2024-01-02", "price": 100},
        {"identifier": "B", "currency": "EUR", "date": "2024-01-02", "price": 200},
        {"identifier": "A", "currency": "USD", "date": "2024-01-03", "price": 101},
        {"identifier": "B", "currency": "EUR", "date": "2024-01-03", "price": 202},
    ]
    df, currencies = build_price_table(records)

    assert list(sorted(df.columns)) == ["A", "B"]
    assert len(df) == 2
    assert df.loc[df.index[0], "A"] == 100.0
    assert df.loc[df.index[1], "B"] == 202.0
    assert currencies == {"A": "USD", "B": "EUR"}


def test_adjust_corp_actions():
    """Prices before ex_date are multiplied by ratio_price_adjustment."""
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    prices = pd.DataFrame({"X": [100.0, 102.0, 104.0]}, index=dates)

    events = [
        {
            "identifier": "X",
            "ex_date": "2024-01-04",
            "ratio_shares_adjustment": "1",
            "ratio_price_adjustment": "0.5",
        }
    ]
    result = adjust_for_corp_actions(prices, events)

    # Dates before 2024-01-04 should be multiplied by 0.5
    assert result.loc[dates[0], "X"] == pytest.approx(50.0)
    assert result.loc[dates[1], "X"] == pytest.approx(51.0)
    # On ex_date, no adjustment
    assert result.loc[dates[2], "X"] == pytest.approx(104.0)


def test_adjust_corp_actions_empty():
    """No events means prices are unchanged."""
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    prices = pd.DataFrame({"X": [100.0, 102.0]}, index=dates)

    result = adjust_for_corp_actions(prices, [])

    pd.testing.assert_frame_equal(result, prices)


def test_adjust_dividends_cash():
    """div_amount is subtracted for dates before ex_date."""
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    prices = pd.DataFrame({"X": [100.0, 102.0, 104.0]}, index=dates)

    events = [
        {
            "identifier": "X",
            "ex_date": "2024-01-04",
            "ratio_shares_adjustment": "1",
            "div_amount": "2.0",
        }
    ]
    result = adjust_for_dividends(prices, events)

    # (price - 2.0) / 1 for dates before ex_date
    assert result.loc[dates[0], "X"] == pytest.approx(98.0)
    assert result.loc[dates[1], "X"] == pytest.approx(100.0)
    # On ex_date, no adjustment
    assert result.loc[dates[2], "X"] == pytest.approx(104.0)


def test_adjust_dividends_stock():
    """ratio_shares_adjustment is applied when != 1."""
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    prices = pd.DataFrame({"X": [100.0, 102.0, 104.0]}, index=dates)

    events = [
        {
            "identifier": "X",
            "ex_date": "2024-01-04",
            "ratio_shares_adjustment": "2",
            "div_amount": "0",
        }
    ]
    result = adjust_for_dividends(prices, events)

    # (price - 0) / 2 for dates before ex_date
    assert result.loc[dates[0], "X"] == pytest.approx(50.0)
    assert result.loc[dates[1], "X"] == pytest.approx(51.0)
    # On ex_date, no adjustment
    assert result.loc[dates[2], "X"] == pytest.approx(104.0)


def test_adjust_dividends_empty():
    """No events means prices are unchanged."""
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    prices = pd.DataFrame({"X": [100.0, 102.0]}, index=dates)

    result = adjust_for_dividends(prices, [])

    pd.testing.assert_frame_equal(result, prices)


def test_convert_to_usd():
    """Non-USD prices are divided by the FX rate."""
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    prices = pd.DataFrame(
        {"A": [100.0, 102.0], "B": [150.0, 153.0]}, index=dates
    )
    currencies = {"A": "USD", "B": "EUR"}

    fx_records = [
        {"date": "2024-01-02", "currency": "EUR", "rate": "0.9"},
        {"date": "2024-01-03", "currency": "EUR", "rate": "0.9"},
    ]
    result = convert_to_usd(prices, currencies, fx_records)

    # USD prices unchanged
    assert result.loc[dates[0], "A"] == pytest.approx(100.0)
    # EUR prices divided by rate
    assert result.loc[dates[0], "B"] == pytest.approx(150.0 / 0.9)
    assert result.loc[dates[1], "B"] == pytest.approx(153.0 / 0.9)


def test_convert_to_usd_all_usd():
    """All-USD prices are returned unchanged."""
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    prices = pd.DataFrame({"A": [100.0, 102.0]}, index=dates)
    currencies = {"A": "USD"}

    result = convert_to_usd(prices, currencies, [])

    pd.testing.assert_frame_equal(result, prices)


def test_convert_to_usd_missing_currency_raises():
    """ValueError raised when a required currency has no FX data."""
    dates = pd.to_datetime(["2024-01-02"])
    prices = pd.DataFrame({"A": [100.0]}, index=dates)
    currencies = {"A": "JPY"}

    with pytest.raises(ValueError, match="JPY"):
        convert_to_usd(prices, currencies, [])


def test_normalize_end_to_end():
    """Full normalize pipeline from dicts to PriceData."""
    price_records = [
        {"identifier": "T1", "currency": "USD", "date": "2024-01-02", "price": 100},
        {"identifier": "T1", "currency": "USD", "date": "2024-01-03", "price": 102},
        {"identifier": "D1", "currency": "USD", "date": "2024-01-02", "price": 200},
        {"identifier": "D1", "currency": "USD", "date": "2024-01-03", "price": 204},
    ]

    result = normalize(
        prices=price_records,
        corp_actions=[],
        dividends=[],
        fx_rates=[],
        targets=["T1"],
        drivers=["D1"],
    )

    assert list(result.targets.columns) == ["T1"]
    assert list(result.drivers.columns) == ["D1"]
    assert len(result.targets) == 2
    assert result.targets.iloc[0]["T1"] == 100.0
    assert result.drivers.iloc[1]["D1"] == 204.0
