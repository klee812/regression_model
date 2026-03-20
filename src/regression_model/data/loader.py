"""Data loading and delegation to the normalize pipeline."""

from __future__ import annotations

import pandas as pd

from regression_model.data.normalize import build_adjusted_prices
from regression_model.data.sources import corp_action_records, dividend_records, fx_rate_records, price_records
from regression_model.models import AppConfig


def load_all(config: AppConfig) -> pd.DataFrame:
    """Fetch data from all sources, normalise, and return a wide price DataFrame.

    ISINs are used as column identifiers throughout — they become the column
    names in the Parquet cache and must match the drivers list in config.

    Args:
        config: Application configuration.

    Returns:
        Wide adjusted, USD-denominated DataFrame (date index, ISIN columns).
    """
    prices = list(price_records())
    corp_actions = list(corp_action_records())
    dividends = list(dividend_records())
    fx_rates = list(fx_rate_records())

    # Rename Isin → figi so normalize sees a consistent field name.
    prices = [{**{k: v for k, v in r.items() if k != "Isin"}, "figi": r["Isin"]} for r in prices]
    corp_actions = [{**{k: v for k, v in r.items() if k != "Isin"}, "figi": r["Isin"]} for r in corp_actions]
    dividends = [{**{k: v for k, v in r.items() if k != "Isin"}, "figi": r["Isin"]} for r in dividends]

    return build_adjusted_prices(prices, corp_actions, dividends, fx_rates)


if __name__ == "__main__":
    # ── PyCharm debug entry point ─────────────────────────────────
    # Run this file directly to step through the data loading pipeline.
    from regression_model.config import load_config
    from regression_model.settings import DEFAULT_CONFIG_PATH
    _config = load_config(DEFAULT_CONFIG_PATH)
    _result = load_all(_config)
    print(_result)
