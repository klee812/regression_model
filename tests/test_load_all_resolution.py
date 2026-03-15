"""Integration tests for load_all() with identifier resolution enabled."""

from __future__ import annotations

import sys
import textwrap
import types
from unittest.mock import MagicMock

import pytest

from regression_model.data.loader import load_all
from regression_model.models import AppConfig, DataConfig
from regression_model.models.resolution_config import IdentifierResolutionConfig


def _write_prices_csv(tmp_path, rows: str) -> str:
    p = tmp_path / "prices.csv"
    p.write_text(rows)
    return str(p)


def _mock_openfigi(batch_lookup_fn) -> types.ModuleType:
    mod = types.ModuleType("openfigi_cache")
    mod.batch_lookup = batch_lookup_fn
    return mod


_PRICES_CSV = textwrap.dedent("""\
    identifier,currency,date,price
    AAPL,USD,2024-01-02,150.0
    MSFT,USD,2024-01-02,300.0
    AAPL,USD,2024-01-03,152.0
    MSFT,USD,2024-01-03,302.0
    AAPL,USD,2024-01-04,151.0
    MSFT,USD,2024-01-04,301.0
    AAPL,USD,2024-01-05,153.0
    MSFT,USD,2024-01-05,303.0
    AAPL,USD,2024-01-08,154.0
    MSFT,USD,2024-01-08,304.0
    AAPL,USD,2024-01-09,155.0
    MSFT,USD,2024-01-09,305.0
    AAPL,USD,2024-01-10,156.0
    MSFT,USD,2024-01-10,306.0
    AAPL,USD,2024-01-11,157.0
    MSFT,USD,2024-01-11,307.0
    AAPL,USD,2024-01-12,158.0
    MSFT,USD,2024-01-12,308.0
    AAPL,USD,2024-01-15,159.0
    MSFT,USD,2024-01-15,309.0
""")

_AAPL_FIGI = "BBG000B9XRY4"
_MSFT_FIGI = "BBG000BPH459"


def test_load_all_with_resolution_returns_figi_columns(tmp_path):
    """load_all resolves tickers to FIGIs; PriceData columns are FIGIs."""
    prices_path = _write_prices_csv(tmp_path, _PRICES_CSV)

    resolution_cfg = IdentifierResolutionConfig(
        enabled=True,
        id_type="TICKER",
        on_failure="raise",
    )
    config = AppConfig(
        data=DataConfig(prices_path=prices_path),
        targets=["AAPL"],
        drivers=["MSFT"],
        resolution=resolution_cfg,
    )

    mock_bl = MagicMock(return_value={"AAPL": _AAPL_FIGI, "MSFT": _MSFT_FIGI})

    with patch_dict_sys_modules(_mock_openfigi(mock_bl)):
        price_data = load_all(config)

    assert _AAPL_FIGI in price_data.targets.columns
    assert _MSFT_FIGI in price_data.drivers.columns
    assert "AAPL" not in price_data.targets.columns
    assert "MSFT" not in price_data.drivers.columns


def test_load_all_without_resolution_unchanged(tmp_path):
    """load_all with resolution=None uses identifiers as-is (existing behavior)."""
    figi_prices = textwrap.dedent(f"""\
        identifier,currency,date,price
        {_AAPL_FIGI},USD,2024-01-02,150.0
        {_MSFT_FIGI},USD,2024-01-02,300.0
        {_AAPL_FIGI},USD,2024-01-03,152.0
        {_MSFT_FIGI},USD,2024-01-03,302.0
        {_AAPL_FIGI},USD,2024-01-04,151.0
        {_MSFT_FIGI},USD,2024-01-04,301.0
        {_AAPL_FIGI},USD,2024-01-05,153.0
        {_MSFT_FIGI},USD,2024-01-05,303.0
        {_AAPL_FIGI},USD,2024-01-08,154.0
        {_MSFT_FIGI},USD,2024-01-08,304.0
        {_AAPL_FIGI},USD,2024-01-09,155.0
        {_MSFT_FIGI},USD,2024-01-09,305.0
        {_AAPL_FIGI},USD,2024-01-10,156.0
        {_MSFT_FIGI},USD,2024-01-10,306.0
        {_AAPL_FIGI},USD,2024-01-11,157.0
        {_MSFT_FIGI},USD,2024-01-11,307.0
        {_AAPL_FIGI},USD,2024-01-12,158.0
        {_MSFT_FIGI},USD,2024-01-12,308.0
        {_AAPL_FIGI},USD,2024-01-15,159.0
        {_MSFT_FIGI},USD,2024-01-15,309.0
    """)
    prices_path = _write_prices_csv(tmp_path, figi_prices)

    config = AppConfig(
        data=DataConfig(prices_path=prices_path),
        targets=[_AAPL_FIGI],
        drivers=[_MSFT_FIGI],
        resolution=None,
    )

    # No mock needed — resolution is disabled; openfigi_cache is never imported.
    price_data = load_all(config)

    assert _AAPL_FIGI in price_data.targets.columns
    assert _MSFT_FIGI in price_data.drivers.columns


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def patch_dict_sys_modules(mock_mod: types.ModuleType):
    with patch.dict(sys.modules, {"openfigi_cache": mock_mod}):
        yield
