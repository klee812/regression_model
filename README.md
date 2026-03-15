# Regression Model

A quantitative finance tool that fits regression models between target and driver securities using historically adjusted price data. Prices are backward-adjusted for corporate actions and dividends, converted to USD, and percent-change returns are fed into OLS, Lasso, Lars, or ElasticNet regression to estimate beta coefficients.

## Quick Start

1. **Install**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Prepare data** — Place CSVs in a data directory (see [Input Data](#input-data)):
   ```
   data/sample/prices.csv
   data/sample/corp_actions.csv   # optional
   data/sample/dividends.csv      # optional
   data/sample/fx_rates.csv       # optional, required for non-USD securities
   ```

3. **Configure** — Edit `config.yaml` (see [Configuration](#configuration)):
   ```yaml
   data:
     prices_path: "data/sample/prices.csv"
     corp_actions_path: "data/sample/corp_actions.csv"
     dividends_path: "data/sample/dividends.csv"
   targets:
     - "BBG000BVPV84"
   drivers:
     - "BBG0000DYRK6"
     - "BBG000BB2N45"
   regression:
     method: "ols"
     params: {}
   preprocessing:
     lookback_days: 70
   output:
     format: "json"
     path: "output/results.json"
   ```

4. **Run**
   ```bash
   python -m regression_model config.yaml
   ```

5. **Read output** — Results are written to the path in `output.path` (see [Output Format](#output-format)).

---

## Input Data

All input files are CSV. Only `prices.csv` is required; the others are optional but must be provided if the data contains non-USD securities or corporate events.

See [`docs/data-format.md`](docs/data-format.md) for full specs and example rows.

### prices.csv

| Column | Type | Format | Description |
|---|---|---|---|
| `identifier` | string | Bloomberg FIGI or similar | Security identifier |
| `currency` | string | ISO 4217 (e.g. `USD`, `EUR`) | Currency of the price |
| `date` | string | `YYYY-MM-DD` | Price date |
| `price` | float | positive number | Closing price in local currency |

Example row: `BBG000BVPV84,USD,2023-01-03,185.0`

### corp_actions.csv

| Column | Type | Format | Description |
|---|---|---|---|
| `identifier` | string | same as prices | Security identifier |
| `ex_date` | string | `YYYY-MM-DD` | First ex-date of the event |
| `ratio_shares_adjustment` | float | e.g. `1.0` | Shares ratio (reserved; see below) |
| `ratio_price_adjustment` | float | e.g. `0.5` for 2-for-1 split | Multiplier applied to pre-event prices |

Example row: `BBG000BVPV84,2023-06-15,2.0,0.5`

### dividends.csv

| Column | Type | Format | Description |
|---|---|---|---|
| `identifier` | string | same as prices | Security identifier |
| `ex_date` | string | `YYYY-MM-DD` | Ex-dividend date |
| `ratio_shares_adjustment` | float | e.g. `1.0` | Shares ratio applied after dividend subtraction |
| `div_amount` | float | same currency as price | Dividend amount per share |

Example row: `BBG000BVPV84,2023-03-15,1.0,0.50`

### fx_rates.csv

Required when any security's `currency` is not `USD`. Rates are expressed as **foreign currency units per 1 USD** (`price_usd = price_local / rate`). Missing dates are forward-filled.

| Column | Type | Format | Description |
|---|---|---|---|
| `date` | string | `YYYY-MM-DD` | Rate date |
| `fxsymbol` | string | ISO 4217 currency code | Currency being quoted (e.g. `EUR`) |
| `rate` | float | positive number | Units of `fxsymbol` per 1 USD |

Example row: `2023-01-03,EUR,0.9350`

---

## Identifier Resolution

By default, targets and drivers in `config.yaml` must be FIGIs. Optionally, you can supply tickers, ISINs, CUSIPs, or any identifier type supported by OpenFIGI and have them resolved automatically before the pipeline runs. FIGIs are passed through unchanged — zero API calls for pure-FIGI configs.

### Install with resolution support

```bash
pip install -e ".[resolution]"
pip install openfigi-cache   # provides batch_lookup + local caching
export OPENFIGI_API_KEY=your-key
```

### Quick start with tickers

```yaml
resolution:
  enabled: true
  id_type: "TICKER"
  exch_code: "US"
  on_failure: "raise"        # or "warn" / "skip"
  cache_path: ".figi_cache.json"
  # optional per-symbol overrides:
  overrides:
    US0378331005:
      id_type: "ID_ISIN"

targets:
  - AAPL                     # ticker — resolved to FIGI automatically
drivers:
  - MSFT
  - BBG000BPH459             # already a FIGI — passed through, no API call
```

### Resolution config reference

| Key | Type | Default | Description |
|---|---|---|---|
| `resolution.enabled` | bool | `false` | Must be `true` to activate resolution |
| `resolution.id_type` | string | `"TICKER"` | Default OpenFIGI `idType` for all symbols |
| `resolution.exch_code` | string | `null` | OpenFIGI exchange code filter (e.g. `"US"`) |
| `resolution.mic_code` | string | `null` | MIC filter (e.g. `"XNAS"`) |
| `resolution.currency` | string | `null` | Currency filter (e.g. `"USD"`) |
| `resolution.cache_path` | string | `".figi_cache.json"` | Path for the local lookup cache |
| `resolution.on_failure` | string | `"raise"` | What to do when a symbol can't be resolved: `raise`, `warn`, or `skip` |
| `resolution.overrides` | dict | `{}` | Per-symbol overrides for any of the above fields |

---

## Configuration

Full reference for `config.yaml`:

| Key | Type | Default | Description |
|---|---|---|---|
| `data.prices_path` | string | — | Path to `prices.csv` (required) |
| `data.corp_actions_path` | string | `null` | Path to `corp_actions.csv` (optional) |
| `data.dividends_path` | string | `null` | Path to `dividends.csv` (optional) |
| `data.fx_rates_path` | string | `null` | Path to `fx_rates.csv` (optional) |
| `targets` | list of strings | — | FIGIs (or resolvable identifiers) to use as regression Y variables (required) |
| `drivers` | list of strings | — | FIGIs (or resolvable identifiers) to use as regression X variables (required) |
| `regression.method` | string | `"ols"` | Regression method: `ols`, `lasso`, `lars`, `elastic_net` |
| `regression.params` | dict | `{}` | Extra kwargs forwarded to the sklearn estimator |
| `preprocessing.lookback_days` | int | `0` | Trim history to this many calendar days before the latest date; `0` = unlimited |
| `preprocessing.missing_data_handler` | string | `"drop"` | How to handle missing prices: `drop`, `forward_fill`, `interpolate` |
| `preprocessing.outlier_method` | string | `"none"` | Outlier treatment on returns: `none`, `winsorize`, `clip`, `drop` |
| `preprocessing.outlier_threshold` | float | `3.0` | Z-score threshold for outlier detection |
| `preprocessing.validate_prices` | bool | `true` | Enforce positive prices, no duplicate dates |
| `preprocessing.min_observations` | int | `10` | Minimum rows required after cleaning |
| `output.format` | string | `"json"` | Output format: `json` or `csv` |
| `output.path` | string | — | Destination file path (required) |

---

## Corporate Action Adjustments

Prices are backward-adjusted so that historical returns are comparable across split and dividend events. See [`docs/corporate-actions.md`](docs/corporate-actions.md) for the full explanation and worked examples.

**Stock split** — the `ratio_price_adjustment` from `corp_actions.csv` is multiplied into all prices strictly before `ex_date`. For a 2-for-1 split, `ratio_price_adjustment = 0.5`, halving all pre-split prices.

**Dividend** — for each record in `dividends.csv`, prices strictly before `ex_date` are adjusted as:
```
adjusted_price = (price - div_amount) / ratio_shares_adjustment
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

### JSON (`output.format: "json"`)
```json
{
  "method": "ols",
  "results": {
    "BBG000BVPV84": {
      "betas": {
        "BBG0000DYRK6": 0.175,
        "BBG000BB2N45": 0.176
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
target_figi,method,intercept,r_squared,n_observations,beta_BBG0000DYRK6,beta_BBG000BB2N45
BBG000BVPV84,ols,-0.0017,0.098,50,0.175,0.176
```

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
