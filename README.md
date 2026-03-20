# Regression Model

A quantitative finance tool that fits regression models between target and driver securities using historically adjusted price data. Prices are backward-adjusted for corporate actions and dividends, converted to USD, and percent-change returns are fed into OLS, Lasso, Lars, or ElasticNet regression to estimate beta coefficients.

## !! BEFORE YOU RUN THIS — IMPLEMENT THESE FIRST !!

The pipeline will raise `NotImplementedError` immediately until these four functions are filled in.
Open `src/regression_model/data/sources.py` and search for `KEVIN_CHECK_HERE`.

| Function | File | What to implement |
|---|---|---|
| `price_records()` | `src/regression_model/data/sources.py` | Yield one dict per price / NAV observation |
| `corp_action_records()` | `src/regression_model/data/sources.py` | Yield one dict per corporate action event |
| `dividend_records()` | `src/regression_model/data/sources.py` | Yield one dict per dividend event |
| `fx_rate_records()` | `src/regression_model/data/sources.py` | Yield one dict per FX rate observation |

Also confirm before running:
- **FX rate direction** — `normalize.py → convert_to_usd`: is `value` fromcurrency-per-USD (divide) or USD-per-fromcurrency (multiply)? See `KEVIN_CHECK_HERE` comment on that line.

---

## Quick Start

1. **Install**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Implement data sources** — Fill in the four generator functions in
   `src/regression_model/data/sources.py`. Required keys are documented in
   the comments inside each function. Look for `KEVIN_CHECK_HERE` markers.

3. **Configure** — Edit `config.yaml` (see [Configuration](#configuration)):
   ```yaml
   drivers:
     - "IE00B4L5Y983"   # iShares Core MSCI World ETF — replace with actual ISINs
     - "IE00B3XXRP09"

   cache_path: "data/price_cache.parquet"

   regression:
     method: "ols"
     params: {}

   preprocessing:
     lookback_days: 0

   output:
     format: "json"
     path: "output/results.json"
   ```
   Omit `targets` to model every instrument in `price_records()` that is not a driver.

4. **Fetch and cache price data** *(slow — run once or on a schedule)*
   ```bash
   python -m regression_model prepare config.yaml
   ```

5. **Run regression** *(fast — run as often as needed)*
   ```bash
   python -m regression_model run config.yaml
   ```

6. **Read output** — Results written to `output.path` (see [Output Format](#output-format)).

The default config path is `C:\inav_data\regression_model\input\config.yaml` — you can omit the path argument if your config lives there.

---

## Two-Step Pipeline

The pipeline is intentionally split to isolate the slow data fetch from the fast regression calculation.

| Step | Command | What it does |
|---|---|---|
| `prepare` | `python -m regression_model prepare config.yaml` | Runs generators → normalises prices → saves Parquet cache |
| `run` | `python -m regression_model run config.yaml` | Loads Parquet cache → preprocesses returns → fits regression → writes output |

Re-run `prepare` whenever your price history needs refreshing. Re-run `run` whenever you want to update regression results, change drivers/targets, or adjust config parameters — no data fetch required.

---

## Input Data

Data is supplied via four generator functions in `src/regression_model/data/sources.py`. Implement each function to yield dicts with the keys described below.

All security records use `Isin` as the source identifier. ISINs flow through as column names in the Parquet cache and in the output.

### `price_records()`

| Key | Type | Description |
|---|---|---|
| `Isin` | string | Security ISIN |
| `pricedate` | string / date | Price date |
| `Price` | float | Closing price / NAV in local currency |
| `currency` | string | ISO 4217 currency code (e.g. `USD`, `GBP`) |
| `proxy_id` *(optional)* | string | Globally unique fallback identifier for instruments without an ISIN |

ETF NAV rows can be included here as ordinary price records.

### `corp_action_records()`

| Key | Type | Description |
|---|---|---|
| `Isin` | string | Security ISIN |
| `XdDate` | string / date | Ex-date of the event |
| `PriceAdjustmentFactor` | float | Multiplier applied to prices before `XdDate` (e.g. `0.5` for a 2-for-1 split) |
| `proxy_id` *(optional)* | string | Globally unique fallback identifier for instruments without an ISIN |

Additional fields present in the source payload (`Bloomberg`, `MIC`, `Name`, `SecurityType`, `ShareAdjustmentFactor`, …) are passed through and ignored.

### `dividend_records()`

| Key | Type | Description |
|---|---|---|
| `Isin` | string | Security ISIN |
| `XdDate` | string / date | Ex-dividend date |
| `NetAmount` | float | Net dividend per share (used for price adjustment) |
| `GrossAmount` | float | Gross dividend per share |
| `proxy_id` *(optional)* | string | Globally unique fallback identifier for instruments without an ISIN |
| `PayDate` *(optional)* | string / date | Payment date |
| `AnnounceDate` *(optional)* | string / date | Announcement date |
| `DividendType` *(optional)* | string | Dividend type classification |
| `Bloomberg` *(optional)* | string | Bloomberg identifier |

### `fx_rate_records()`

Required when any security's `currency` is not `USD`. Missing dates are forward-filled.

> **KEVIN_CHECK_HERE** — the pipeline assumes `value` is expressed as
> **fromcurrency units per 1 USD** (`price_usd = price_local / value`).
> If your feed expresses rates as USD per fromcurrency, flip the division
> to multiplication in `normalize.py → convert_to_usd`.

| Key | Type | Description |
|---|---|---|
| `pricedate` | string / date | Rate date |
| `fromcurrencycode` | string | Source currency (e.g. `GBP`) |
| `tocurrencycode` | string | Target currency (e.g. `USD`) |
| `value` | float | Exchange rate |

---

## Configuration

Full reference for `config.yaml`:

| Key | Type | Default | Description |
|---|---|---|---|
| `drivers` | list of strings | — | ISINs to use as regression X variables (required) |
| `targets` | list of strings | `null` | ISINs to model; omit to model all instruments except drivers |
| `cache_path` | string | `null` | Path to the Parquet price cache (required for `prepare` and `run`) |
| `regression.method` | string | `"ols"` | Regression method: `ols`, `lasso`, `lars`, `elastic_net` |
| `regression.params` | dict | `{}` | Extra kwargs forwarded to the sklearn estimator |
| `preprocessing.lookback_days` | int | `0` | Trim history to this many calendar days before the latest date; `0` = unlimited |
| `preprocessing.missing_data_handler` | string | `"drop"` | How to handle missing prices: `drop`, `forward_fill`, `interpolate` |
| `preprocessing.outlier_method` | string | `"none"` | Outlier treatment on returns: `none`, `winsorize`, `clip`, `drop` |
| `preprocessing.outlier_threshold` | float | `3.0` | Z-score threshold for outlier detection |
| `preprocessing.validate_prices` | bool | `true` | Enforce positive prices, no duplicate dates |
| `preprocessing.min_observations` | int | `10` | Minimum rows required after cleaning |
| `output.format` | string | `"json"` | Output format: `json` or `csv` |
| `output.path` | Path | `output/results.json` | Destination file path |

---

## Corporate Action Adjustments

Prices are backward-adjusted so that historical returns are comparable across split and dividend events.

**Stock split** — `PriceAdjustmentFactor` from `corp_action_records()` is multiplied into all prices strictly before `XdDate`. For a 2-for-1 split, `PriceAdjustmentFactor = 0.5`, halving all pre-split prices.

**Dividend** — `NetAmount` from `dividend_records()` is subtracted from all prices strictly before `XdDate`:
```
adjusted_price = price - NetAmount
```

Multiple events are processed **latest to earliest** so that earlier adjustments are not double-counted.

---

## Regression Methods

| Method | Key | Notes |
|---|---|---|
| Ordinary Least Squares | `ols` | No regularization; uses `sklearn.linear_model.LinearRegression` |
| Lasso (L1) | `lasso` | Sparse betas; use `params.alpha` to control regularization strength |
| LARS | `lars` | Least-angle regression; efficient for high-dimensional problems |
| Elastic Net | `elastic_net` | L1+L2 combination; use `params.alpha` and `params.l1_ratio` |

Extra kwargs in `regression.params` are forwarded directly to the underlying sklearn estimator.

---

## Output Format

Results are keyed by target ISIN. Load them back as typed objects in the proxy table step:

```python
from regression_model.output import load_results

results = load_results("output/results.json")
for r in results:
    print(r.target_figi, r.betas, r.r_squared)
```

### JSON (`output.format: "json"`)
```json
{
  "method": "ols",
  "results": {
    "IE00B4L5Y983": {
      "betas": {
        "IE00B3XXRP09": 0.175,
        "IE00BKM4GZ66": 0.176
      },
      "intercept": -0.0017,
      "r_squared": 0.098,
      "n_observations": 50
    }
  }
}
```

### CSV (`output.format: "csv"`)
```
target_figi,method,intercept,r_squared,n_observations,beta_IE00B3XXRP09,beta_IE00BKM4GZ66
IE00B4L5Y983,ols,-0.0017,0.098,50,0.175,0.176
```

Each run also writes a timestamped copy alongside the main file (e.g. `results_20260320_143022.json`) for audit purposes.

---

## Running Tests

```bash
pytest
```

To also run linting and type checks:
```bash
ruff check src tests
mypy src
```
