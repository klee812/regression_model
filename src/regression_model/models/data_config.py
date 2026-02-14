"""Data configuration for specifying input file paths."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DataConfig:
    """Paths to price, corporate action, dividend, and FX rate CSV files."""

    prices_path: str = ""
    corp_actions_path: str = ""
    dividends_path: str = ""
    fx_rates_path: str = ""
