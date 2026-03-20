"""Entry point for the regression_model pipeline.

Commands:
    prepare  — fetch and normalise price data, save to Parquet cache
    run      — load cached prices and run regression
"""

from __future__ import annotations

import sys

from regression_model.config import load_config
from regression_model.settings import DEFAULT_CONFIG_PATH


def prepare(config_path: str) -> None:
    """Fetch data from sources, normalise, and save to the Parquet cache.

    This is the slow step — run it ahead of time.

    Args:
        config_path: Path to the YAML configuration file.
    """
    from regression_model.data.loader import load_all
    from regression_model.data.cache import save_price_cache

    config = load_config(config_path)

    if not config.cache_path:
        print("Error: 'cache_path' must be set in config.yaml for the prepare step.", file=sys.stderr)
        sys.exit(1)

    print("Fetching and normalising price data...")
    prices = load_all(config)
    save_price_cache(prices, config.cache_path)


def run(config_path: str) -> None:
    """Load cached prices and run regression.

    This is the fast step — requires prepare to have been run first.

    Args:
        config_path: Path to the YAML configuration file.
    """
    from regression_model.data.cache import load_price_cache
    from regression_model.data.preprocess import prepare_prices, prepare_returns
    from regression_model.data.transforms import prices_to_returns
    from regression_model.output.writer import write_results
    from regression_model.regression import registry

    config = load_config(config_path)

    if not config.cache_path:
        print("Error: 'cache_path' must be set in config.yaml for the run step.", file=sys.stderr)
        sys.exit(1)

    prices = load_price_cache(config.cache_path, config.drivers, config.targets)
    prices = prepare_prices(prices, config.preprocessing)
    returns = prices_to_returns(prices)
    returns = prepare_returns(returns, config.preprocessing)

    strategy = registry.create(config.regression.method, **config.regression.params)

    results = []
    for figi in returns.targets.columns:
        y = returns.targets[figi]
        x = returns.drivers
        result = strategy.fit(figi, y, x)
        results.append(result)

    write_results(results, config.regression.method, config.output.format, config.output.path)
    print(f"Results written to {config.output.path}")


DEFAULT_CONFIG = DEFAULT_CONFIG_PATH


def debug_prepare() -> None:
    """PyCharm debug entry point — run prepare with no arguments."""
    prepare(DEFAULT_CONFIG)


def debug_run() -> None:
    """PyCharm debug entry point — run regression with no arguments."""
    run(DEFAULT_CONFIG)


if __name__ == "__main__":
    commands = {"prepare": prepare, "run": run}

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print(f"Usage: python -m regression_model <prepare|run> [config.yaml]", file=sys.stderr)
        print(f"       config.yaml defaults to: {DEFAULT_CONFIG}", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_CONFIG
    commands[sys.argv[1]](config_path)
