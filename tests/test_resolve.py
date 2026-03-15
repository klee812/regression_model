"""Unit tests for regression_model.data.resolve."""

from __future__ import annotations

import sys
import types
import warnings
from unittest.mock import MagicMock, patch

import pytest

from regression_model.data.resolve import remap_price_records, resolve_identifiers
from regression_model.models.resolution_config import IdentifierResolutionConfig


def _cfg(**kwargs) -> IdentifierResolutionConfig:
    return IdentifierResolutionConfig(enabled=True, **kwargs)


def _mock_openfigi(batch_lookup_fn) -> types.ModuleType:
    """Return a fake openfigi_cache module with the given batch_lookup."""
    mod = types.ModuleType("openfigi_cache")
    mod.batch_lookup = batch_lookup_fn
    return mod


# ---------------------------------------------------------------------------
# resolve_identifiers
# ---------------------------------------------------------------------------


def test_all_tickers_resolved():
    cfg = _cfg(id_type="TICKER")
    mock_bl = MagicMock(return_value={"AAPL": "BBG000B9XRY4", "MSFT": "BBG000BPH459"})

    with patch.dict(sys.modules, {"openfigi_cache": _mock_openfigi(mock_bl)}):
        result = resolve_identifiers(["AAPL", "MSFT"], cfg)

    assert result == {"AAPL": "BBG000B9XRY4", "MSFT": "BBG000BPH459"}


def test_figi_passthrough_no_api_call():
    cfg = _cfg(id_type="TICKER")
    figi = "BBG000B9XRY4"
    mock_bl = MagicMock()

    with patch.dict(sys.modules, {"openfigi_cache": _mock_openfigi(mock_bl)}):
        result = resolve_identifiers([figi], cfg)

    mock_bl.assert_not_called()
    assert result == {figi: figi}


def test_on_failure_raise():
    cfg = _cfg(id_type="TICKER", on_failure="raise")
    mock_bl = MagicMock(return_value={"UNKNOWN": None})

    with patch.dict(sys.modules, {"openfigi_cache": _mock_openfigi(mock_bl)}):
        with pytest.raises(ValueError, match="UNKNOWN"):
            resolve_identifiers(["UNKNOWN"], cfg)


def test_on_failure_warn():
    cfg = _cfg(id_type="TICKER", on_failure="warn")
    mock_bl = MagicMock(return_value={"UNKNOWN": None})

    with patch.dict(sys.modules, {"openfigi_cache": _mock_openfigi(mock_bl)}):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = resolve_identifiers(["UNKNOWN"], cfg)

    assert result == {"UNKNOWN": None}
    assert any("UNKNOWN" in str(warning.message) for warning in w)


def test_on_failure_skip_silent():
    cfg = _cfg(id_type="TICKER", on_failure="skip")
    mock_bl = MagicMock(return_value={"UNKNOWN": None})

    with patch.dict(sys.modules, {"openfigi_cache": _mock_openfigi(mock_bl)}):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = resolve_identifiers(["UNKNOWN"], cfg)

    assert result == {"UNKNOWN": None}
    assert not w


def test_per_symbol_override_uses_correct_id_type():
    cfg = _cfg(
        id_type="TICKER",
        overrides={"US0378331005": {"id_type": "ID_ISIN"}},
    )

    captured_calls: list[dict] = []

    def fake_batch_lookup(symbols, **kwargs):
        captured_calls.append({"symbols": list(symbols), "kwargs": kwargs})
        return {s: f"BBG{'X' * 9}" for s in symbols}

    with patch.dict(sys.modules, {"openfigi_cache": _mock_openfigi(fake_batch_lookup)}):
        resolve_identifiers(["AAPL", "US0378331005"], cfg)

    id_types = {call["kwargs"]["id_type"]: call["symbols"] for call in captured_calls}
    assert "ID_ISIN" in id_types
    assert "US0378331005" in id_types["ID_ISIN"]
    assert "TICKER" in id_types
    assert "AAPL" in id_types["TICKER"]


def test_import_error_when_openfigi_cache_missing():
    cfg = _cfg()
    with patch.dict(sys.modules, {"openfigi_cache": None}):
        with pytest.raises(ImportError, match="openfigi_cache"):
            resolve_identifiers(["AAPL"], cfg)


# ---------------------------------------------------------------------------
# remap_price_records
# ---------------------------------------------------------------------------

_RECORDS = [
    {"identifier": "AAPL", "date": "2024-01-02", "price": "150.0"},
    {"identifier": "BBG000B9XRY4", "date": "2024-01-02", "price": "200.0"},
    {"identifier": "MSFT", "date": "2024-01-02", "price": "300.0"},
]


def test_remap_rewrites_identifier():
    sym_map = {"AAPL": "BBG000B9XRY4AAPL", "MSFT": "BBG000BPH459MSFT"}
    out = remap_price_records(_RECORDS, sym_map)
    ids = [r["identifier"] for r in out]
    assert "BBG000B9XRY4AAPL" in ids
    assert "BBG000BPH459MSFT" in ids


def test_remap_passthrough_for_unknown_symbol():
    sym_map = {}  # no entries → all rows pass through unchanged
    out = remap_price_records(_RECORDS, sym_map)
    assert len(out) == len(_RECORDS)
    assert out[1]["identifier"] == "BBG000B9XRY4"


def test_remap_drops_rows_with_none_figi():
    sym_map = {"AAPL": None, "MSFT": "BBG000BPH459MSFT"}
    out = remap_price_records(_RECORDS, sym_map)
    ids = [r["identifier"] for r in out]
    assert "AAPL" not in ids
    assert "BBG000BPH459MSFT" in ids
    assert "BBG000B9XRY4" in ids  # already-FIGI row passes through
