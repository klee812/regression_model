"""Identifier resolution: tickers/ISINs/CUSIPs → FIGIs via openfigi_cache."""

from __future__ import annotations

import logging
import re
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from regression_model.models.resolution_config import IdentifierResolutionConfig

log = logging.getLogger(__name__)

_FIGI_RE = re.compile(r"^BBG[A-Z0-9]{9}$")


def _is_figi(symbol: str) -> bool:
    return bool(_FIGI_RE.match(symbol))


def _qualifier(symbol: str, config: IdentifierResolutionConfig) -> tuple:
    """Return the (id_type, exch_code, mic_code, currency) tuple for a symbol."""
    ov = config.overrides.get(symbol, {})
    return (
        ov.get("id_type", config.id_type),
        ov.get("exch_code", config.exch_code),
        ov.get("mic_code", config.mic_code),
        ov.get("currency", config.currency),
    )


def resolve_identifiers(
    identifiers: list[str],
    config: IdentifierResolutionConfig,
) -> dict[str, str | None]:
    """Resolve a list of identifiers to FIGIs.

    FIGIs (12-char ``BBG…`` strings) are passed through without any API call.
    Non-FIGI identifiers are grouped by their effective qualifier tuple and
    sent to ``openfigi_cache.batch_lookup`` per group.

    Args:
        identifiers: Symbols to resolve (tickers, ISINs, FIGIs, …).
        config: Resolution settings including ``id_type``, filter fields, and
            per-symbol overrides.

    Returns:
        Mapping of input symbol → FIGI string, or ``None`` when unresolvable.
    """
    try:
        from openfigi_cache import batch_lookup
    except ImportError as exc:
        raise ImportError(
            "openfigi_cache is required for identifier resolution. "
            "Install it with: pip install regression-model[resolution]"
        ) from exc

    result: dict[str, str | None] = {}

    # Pass FIGIs through unchanged; group non-FIGIs by qualifier.
    groups: dict[tuple, list[str]] = {}
    for sym in identifiers:
        if _is_figi(sym):
            result[sym] = sym
        else:
            key = _qualifier(sym, config)
            groups.setdefault(key, []).append(sym)

    for (id_type, exch_code, mic_code, currency), symbols in groups.items():
        kwargs: dict = {"id_type": id_type, "cache_path": Path(config.cache_path)}
        if exch_code is not None:
            kwargs["exch_code"] = exch_code
        if mic_code is not None:
            kwargs["mic_code"] = mic_code
        if currency is not None:
            kwargs["currency"] = currency

        resolved: dict[str, str | None] = batch_lookup(symbols, **kwargs)

        for sym in symbols:
            figi = resolved.get(sym)
            if figi is not None:
                result[sym] = figi
            else:
                _handle_failure(sym, config)
                result[sym] = None

    return result


def _handle_failure(symbol: str, config: IdentifierResolutionConfig) -> None:
    msg = f"Could not resolve identifier to FIGI: {symbol!r}"
    if config.on_failure == "raise":
        raise ValueError(msg)
    elif config.on_failure == "warn":
        warnings.warn(msg, stacklevel=4)
    # "skip" → silent


def remap_records(
    records: list[dict],
    symbol_to_figi: dict[str, str | None],
) -> list[dict]:
    """Resolve ``Isin`` → FIGI and rename the key to ``figi``.

    - Records whose ``Isin`` is not in the map (already FIGIs) pass through
      with the key renamed to ``figi``.
    - Records that resolved to ``None`` fall back to ``proxy_id`` if present
      (caller must guarantee global uniqueness of proxy IDs).
    - Records with no FIGI and no ``proxy_id`` are dropped with a warning.

    Args:
        records: Source rows (prices, corp actions, or dividends).
        symbol_to_figi: Map returned by ``resolve_identifiers``.

    Returns:
        Records with ``Isin`` key removed and ``figi`` key added.
    """
    out: list[dict] = []
    for row in records:
        sym = row["Isin"]
        base = {k: v for k, v in row.items() if k != "Isin"}
        if sym not in symbol_to_figi:
            out.append({**base, "figi": sym})
            continue
        figi = symbol_to_figi[sym]
        if figi is None:
            proxy = row.get("proxy_id")
            if proxy:
                log.warning("No FIGI for %r — using proxy_id %r", sym, proxy)
                out.append({**base, "figi": proxy})
            else:
                log.warning("Dropping record: no FIGI and no proxy_id for %r", sym)
        else:
            out.append({**base, "figi": figi})
    return out
