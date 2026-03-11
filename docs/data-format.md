# Data Format Specifications

All input files are CSV with a header row. Dates must use `YYYY-MM-DD` format. Numeric columns must not contain commas or currency symbols.

---

## prices.csv

The only required input file. Contains one row per (identifier, date) pair. All identifiers referenced in `targets` and `drivers` in `config.yaml` must appear here.

**Columns**

| Column | Type | Required | Description |
|---|---|---|---|
| `identifier` | string | yes | Security identifier (e.g. Bloomberg FIGI) |
| `currency` | string | yes | ISO 4217 currency code for the price (e.g. `USD`, `EUR`, `GBP`) |
| `date` | string | yes | Trading date in `YYYY-MM-DD` format |
| `price` | float | yes | Closing price in local currency; must be positive |

**Constraints**
- No duplicate `(identifier, date)` pairs.
- Prices must be positive (enforced when `preprocessing.validate_prices: true`).
- Non-USD prices require a corresponding entry in `fx_rates.csv`.

**Full example**

```csv
identifier,currency,date,price
BBG000BVPV84,USD,2023-01-03,185.0
BBG000BVPV84,USD,2023-01-04,184.66
BBG000BVPV84,USD,2023-01-05,184.24
BBG0000DYRK6,USD,2023-01-03,420.0
BBG0000DYRK6,USD,2023-01-04,420.93
BBG0000DYRK6,USD,2023-01-05,419.78
BBG000BB2N45,USD,2023-01-03,55.0
BBG000BB2N45,USD,2023-01-04,56.25
BBG000BB2N45,USD,2023-01-05,55.86
```

---

## corp_actions.csv

Optional. Records corporate actions (stock splits, mergers, spin-offs) that require backward price adjustment. If the file is omitted or the path is not set in config, no corporate action adjustment is applied.

**Columns**

| Column | Type | Required | Description |
|---|---|---|---|
| `identifier` | string | yes | Security identifier matching `prices.csv` |
| `ex_date` | string | yes | First ex-date of the event in `YYYY-MM-DD` format |
| `ratio_shares_adjustment` | float | yes | Shares ratio for the event (reserved for future use; set to `1.0` if not applicable) |
| `ratio_price_adjustment` | float | yes | Multiplier applied to all prices strictly before `ex_date`. For a 2-for-1 split use `0.5`; for a 1-for-3 reverse split use `3.0`. |

**How it works**: for each record, `price * ratio_price_adjustment` is applied to all dates before `ex_date`. Multiple events are processed latest-to-earliest. See [`corporate-actions.md`](corporate-actions.md) for details.

**Full example** (2-for-1 split on 2023-06-15)

```csv
identifier,ex_date,ratio_shares_adjustment,ratio_price_adjustment
BBG000BVPV84,2023-06-15,2.0,0.5
```

An empty file (header only) is valid and results in no adjustment.

---

## dividends.csv

Optional. Records dividend payments that require backward price adjustment. If omitted or path not set, no dividend adjustment is applied.

**Columns**

| Column | Type | Required | Description |
|---|---|---|---|
| `identifier` | string | yes | Security identifier matching `prices.csv` |
| `ex_date` | string | yes | Ex-dividend date in `YYYY-MM-DD` format |
| `ratio_shares_adjustment` | float | yes | Divisor applied after subtracting the dividend amount. Typically `1.0` for cash dividends; use a different value for stock dividends that change share count. |
| `div_amount` | float | yes | Dividend amount per share in the same currency as the price |

**How it works**: for each record, prices strictly before `ex_date` are adjusted as `(price - div_amount) / ratio_shares_adjustment`. Multiple events are processed latest-to-earliest. See [`corporate-actions.md`](corporate-actions.md) for details.

**Full example** ($0.50 cash dividend on 2023-03-15)

```csv
identifier,ex_date,ratio_shares_adjustment,div_amount
BBG000BVPV84,2023-03-15,1.0,0.50
```

An empty file (header only) is valid and results in no adjustment.

---

## fx_rates.csv

Optional, but **required** if any security in `prices.csv` has a `currency` other than `USD`. Rates must cover at least the date range in `prices.csv`; missing intermediate dates are forward-filled.

**Columns**

| Column | Type | Required | Description |
|---|---|---|---|
| `date` | string | yes | Rate date in `YYYY-MM-DD` format |
| `fxsymbol` | string | yes | ISO 4217 currency code being quoted (e.g. `EUR`, `GBP`) |
| `rate` | float | yes | Number of `fxsymbol` units per 1 USD. Conversion: `price_usd = price_local / rate` |

**Constraints**
- One row per `(date, fxsymbol)`.
- Only non-USD currencies need entries; USD itself must not appear.
- If `fxsymbol` data is missing for a required currency the pipeline raises a `ValueError`.

**Full example** (EUR/USD and GBP/USD rates)

```csv
date,fxsymbol,rate
2023-01-03,EUR,0.9350
2023-01-04,EUR,0.9372
2023-01-05,EUR,0.9341
2023-01-03,GBP,0.8105
2023-01-04,GBP,0.8120
2023-01-05,GBP,0.8098
```

> **Note**: `rate = 0.9350` means 1 USD buys 0.9350 EUR, so a EUR-denominated price of 93.50 converts to USD as `93.50 / 0.9350 = 100.00`.
