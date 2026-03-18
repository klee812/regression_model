"""Data loading and delegation to the normalize pipeline."""

from __future__ import annotations

from regression_model.data.normalize import normalize
from regression_model.data.sources import corp_action_records, dividend_records, fx_rate_records, price_records
from regression_model.models import AppConfig, PriceData



def load_all(config: AppConfig) -> PriceData:
    """Load data and run the normalization pipeline.

    Args:
        config: Application configuration with data paths and identifier lists.

    Returns:
        A ``PriceData`` instance with normalized target and driver prices.
    """
    prices = list(price_records())
    corp_actions = list(corp_action_records())
    dividends = list(dividend_records())

    fx_rates = list(fx_rate_records())

    targets = config.targets
    drivers = config.drivers

    if config.resolution:
        from regression_model.data.resolve import resolve_identifiers, remap_records

        all_symbols = list(dict.fromkeys(
            targets + drivers + [r["Isin"] for r in prices]
        ))
        symbol_to_figi = resolve_identifiers(all_symbols, config.resolution)
        targets = [symbol_to_figi.get(t, t) for t in (targets or []) if symbol_to_figi.get(t) is not None] or None
        drivers = [symbol_to_figi.get(d, d) for d in drivers if symbol_to_figi.get(d) is not None]
        prices = remap_records(prices, symbol_to_figi)
        corp_actions = remap_records(corp_actions, symbol_to_figi)
        dividends = remap_records(dividends, symbol_to_figi)
    else:
        # No resolution configured — treat Isin values as-is but normalise the key to figi.
        prices = [{**{k: v for k, v in r.items() if k != "Isin"}, "figi": r["Isin"]} for r in prices]
        corp_actions = [{**{k: v for k, v in r.items() if k != "Isin"}, "figi": r["Isin"]} for r in corp_actions]
        dividends = [{**{k: v for k, v in r.items() if k != "Isin"}, "figi": r["Isin"]} for r in dividends]

    return normalize(
        prices=prices,
        corp_actions=corp_actions,
        dividends=dividends,
        fx_rates=fx_rates,
        targets=targets,
        drivers=drivers,
    )
