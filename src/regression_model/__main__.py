"""Entry point for ``python -m regression_model <config.yaml>``."""

from __future__ import annotations

import sys

from regression_model.config import load_config
from regression_model.data.loader import load_all
from regression_model.data.preprocess import prepare_prices, prepare_returns
from regression_model.data.transforms import prices_to_returns
from regression_model.output.writer import write_results
from regression_model.regression import registry


def main(config_path: str) -> None:
    """Run the full regression pipeline from config to output.

    Args:
        config_path: Path to the YAML configuration file.
    """
    config = load_config(config_path)
    prices = load_all(config)
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m regression_model <config.yaml>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
