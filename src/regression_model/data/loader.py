"""CSV data loading and delegation to the normalize pipeline."""

from __future__ import annotations

import csv
from pathlib import Path

from regression_model.data.normalize import normalize
from regression_model.models import AppConfig, PriceData


def _read_csv_dicts(path: str | Path) -> list[dict]:
    """Read a CSV file and return its rows as a list of dicts.

    Args:
        path: Filesystem path to the CSV file.

    Returns:
        A list of dicts, one per row, keyed by column header.
    """
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def load_all(config: AppConfig) -> PriceData:
    """Load CSV files and run the normalization pipeline.

    Args:
        config: Application configuration with data paths and identifier lists.

    Returns:
        A ``PriceData`` instance with normalized target and driver prices.
    """
    prices = _read_csv_dicts(config.data.prices_path)

    corp_actions: list[dict] = []
    if config.data.corp_actions_path:
        corp_actions = _read_csv_dicts(config.data.corp_actions_path)

    dividends: list[dict] = []
    if config.data.dividends_path:
        dividends = _read_csv_dicts(config.data.dividends_path)

    fx_rates: list[dict] = []
    if config.data.fx_rates_path:
        fx_rates = _read_csv_dicts(config.data.fx_rates_path)

    targets = config.targets
    drivers = config.drivers

    if config.resolution and config.resolution.enabled:
        from regression_model.data.resolve import resolve_identifiers, remap_price_records

        all_symbols = list(dict.fromkeys(
            targets + drivers + [r["identifier"] for r in prices]
        ))
        symbol_to_figi = resolve_identifiers(all_symbols, config.resolution)
        targets = [symbol_to_figi.get(t, t) for t in targets if symbol_to_figi.get(t) is not None]
        drivers = [symbol_to_figi.get(d, d) for d in drivers if symbol_to_figi.get(d) is not None]
        prices = remap_price_records(prices, symbol_to_figi)

    return normalize(
        prices=prices,
        corp_actions=corp_actions,
        dividends=dividends,
        fx_rates=fx_rates,
        targets=targets,
        drivers=drivers,
    )
