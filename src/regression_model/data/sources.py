"""Placeholder data source generators.

Replace each function body with your own data retrieval logic before running.
Each function must ``yield`` one ``dict`` per record.  Required and optional
keys are documented in the comments inside each function.
"""

from __future__ import annotations

from typing import Iterator


def price_records() -> Iterator[dict]:
    # ── PLACEHOLDER ──────────────────────────────────────────────
    # TODO: yield one dict per price record (including ETF NAV rows)
    # Required keys:
    #   Isin       – security ISIN
    #   pricedate  – price date
    #   Price      – numeric price / NAV
    #   currency   – ISO currency code, e.g. "USD", "GBP"
    # Optional keys:
    #   proxy_id   – globally unique fallback ID for instruments with no FIGI
    #                (e.g. unlisted derivatives); caller must ensure uniqueness
    # ─────────────────────────────────────────────────────────────
    # KEVIN_CHECK_HERE — replace the line below with your generator logic
    raise NotImplementedError("price_records: implement before running")
    yield  # keeps this a generator function


def corp_action_records() -> Iterator[dict]:
    # ── PLACEHOLDER ──────────────────────────────────────────────
    # TODO: yield one dict per corporate action event
    # Required keys:
    #   Isin                  – security ISIN
    #   XdDate                – ex-date
    #   PriceAdjustmentFactor – float multiplier applied to prices before XdDate
    #                           e.g. 0.5 for a 2-for-1 split
    # Optional keys:
    #   proxy_id   – globally unique fallback ID for instruments with no FIGI
    # Present but not used:
    #   Bloomberg, MIC, Name, SecurityType, ShareAdjustmentFactor, ...
    # ─────────────────────────────────────────────────────────────
    # KEVIN_CHECK_HERE — replace the line below with your generator logic
    raise NotImplementedError("corp_action_records: implement before running")
    yield


def fx_rate_records() -> Iterator[dict]:
    # ── PLACEHOLDER ──────────────────────────────────────────────
    # TODO: yield one dict per FX rate observation
    # Required keys:
    #   pricedate        – rate date
    #   fromcurrencycode – source currency, e.g. "GBP"
    #   tocurrencycode   – target currency, e.g. "USD"
    #   value            – exchange rate
    # KEVIN_CHECK_HERE — replace the line below with your generator logic
    # ─────────────────────────────────────────────────────────────
    raise NotImplementedError("fx_rate_records: implement before running")
    yield


def dividend_records() -> Iterator[dict]:
    # ── PLACEHOLDER ──────────────────────────────────────────────
    # TODO: yield one dict per dividend event
    # Required keys:
    #   Isin           – security ISIN
    #   XdDate         – ex-dividend date
    #   NetAmount      – net dividend amount (used for price adjustment)
    #   GrossAmount    – gross dividend amount
    # Optional keys:
    #   proxy_id   – globally unique fallback ID for instruments with no FIGI
    #   PayDate, AnnounceDate, DividendType, Bloomberg
    # ─────────────────────────────────────────────────────────────
    # KEVIN_CHECK_HERE — replace the line below with your generator logic
    raise NotImplementedError("dividend_records: implement before running")
    yield
