# Corporate Action Adjustments

## Why adjustments are needed

Raw price series contain discontinuities caused by corporate events. A 2-for-1 stock split causes the price to drop by roughly 50% overnight, even though the holder's economic value is unchanged. Fitting a regression on raw prices would treat this as a large negative return for the security, distorting beta estimates.

Backward price adjustment removes these discontinuities by rescaling all historical prices so that the adjusted series is economically continuous up to the most recent observation. The most recent price is never modified; only prices before each event's ex-date are changed.

---

## Stock Split Adjustment

A stock split is recorded in `corp_actions.csv` with a `ratio_price_adjustment`. For a 2-for-1 split this ratio is `0.5`; for a 3-for-1 split it is `0.333`.

**Formula**: for all dates strictly before `ex_date`:
```
adjusted_price = raw_price * ratio_price_adjustment
```

**Example**: 2-for-1 split with `ex_date = 2023-06-15`, `ratio_price_adjustment = 0.5`

| Date | Raw Price | Adjusted Price |
|---|---|---|
| 2023-06-12 | 200.00 | 100.00 |
| 2023-06-13 | 202.00 | 101.00 |
| 2023-06-14 | 198.00 | 99.00 |
| **2023-06-15** (ex-date) | **101.00** | **101.00** |
| 2023-06-16 | 102.00 | 102.00 |

The post-split prices are unchanged. The percent-change return from 2023-06-14 to 2023-06-15 using the adjusted series is `(101 - 99) / 99 ≈ +2.0%`, which correctly reflects the actual price movement rather than an artificial 50% gap.

---

## Dividend Adjustment

A dividend payment is recorded in `dividends.csv` with `div_amount` and `ratio_shares_adjustment`. For a plain cash dividend, `ratio_shares_adjustment` is `1.0`.

**Formula**: for all dates strictly before `ex_date`:
```
adjusted_price = (raw_price - div_amount) / ratio_shares_adjustment
```

**Example**: $0.50 dividend with `ex_date = 2023-03-15`, `div_amount = 0.50`, `ratio_shares_adjustment = 1.0`

| Date | Raw Price | Adjusted Price |
|---|---|---|
| 2023-03-12 | 100.00 | 99.50 |
| 2023-03-13 | 101.00 | 100.50 |
| 2023-03-14 | 99.50 | 99.00 |
| **2023-03-15** (ex-date) | **99.00** | **99.00** |
| 2023-03-16 | 99.50 | 99.50 |

Without adjustment, the price drop from 99.50 to 99.00 on the ex-date would appear as a small negative return, obscuring the actual no-change from the investor's perspective (they received the $0.50 as cash).

---

## Multiple Events and Ordering

When there are multiple corporate events for a single security, they are always processed **from latest to earliest**. This prevents double-counting: if an earlier event's adjustment were applied first, a later event would then compound on already-adjusted values, producing incorrect results.

**Example**: two events for the same security

| Event | ex_date | Type |
|---|---|---|
| B | 2023-09-01 | Dividend ($1.00) |
| A | 2023-03-15 | Dividend ($0.50) |

Processing order: B first (2023-09-01), then A (2023-03-15).

1. Apply event B: adjust all prices before 2023-09-01 by subtracting $1.00.
2. Apply event A: adjust all prices before 2023-03-15 by subtracting $0.50 (from the already B-adjusted values).

Prices between 2023-03-15 and 2023-09-01 are adjusted only by event B. Prices before 2023-03-15 are adjusted by both events, in that order.

---

## Implementation Notes

- Adjustments are applied to a copy of the price DataFrame; the original data is not mutated.
- The `prices strictly before ex_date` condition means the ex-date itself and all subsequent dates are left unchanged.
- Corporate action and dividend adjustments are applied before FX conversion, so the adjustment arithmetic is always in the security's local currency.
- Source: `src/regression_model/data/normalize.py` — `adjust_for_corp_actions` and `adjust_for_dividends`.
