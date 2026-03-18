"""Write and read regression results (JSON or CSV)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from regression_model.models import RegressionResult


def load_results(path: str | Path) -> list[RegressionResult]:
    """Load regression results from a JSON file written by ``write_results``.

    Args:
        path: Path to the JSON output file.

    Returns:
        List of ``RegressionResult`` instances, one per target.
    """
    with open(path) as f:
        raw = json.load(f)
    return [
        RegressionResult.from_dict(figi, data)
        for figi, data in raw["results"].items()
    ]


def write_results(
    results: list[RegressionResult],
    method: str,
    fmt: str,
    path: str | Path,
) -> None:
    """Dispatch results to the appropriate writer based on format.

    Args:
        results: List of regression results to write.
        method: Name of the regression method used.
        fmt: Output format (``"json"`` or ``"csv"``).
        path: Destination file path.

    Raises:
        ValueError: If *fmt* is not a supported format.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        _write_json(results, method, path)
    elif fmt == "csv":
        _write_csv(results, method, path)
    else:
        raise ValueError(f"Unknown output format {fmt!r}. Available: json, csv")


def _write_json(results: list[RegressionResult], method: str, path: Path) -> None:
    """Serialize results to a JSON file.

    Args:
        results: Regression results to serialize.
        method: Name of the regression method.
        path: Output file path.
    """
    out = {
        "method": method,
        "results": {
            r.target_figi: {
                "betas": r.betas,
                "intercept": r.intercept,
                "r_squared": r.r_squared,
                "n_observations": r.n_observations,
            }
            for r in results
        },
    }
    with open(path, "w") as f:
        json.dump(out, f, indent=2)


def _write_csv(results: list[RegressionResult], method: str, path: Path) -> None:
    """Write results to a CSV file with one row per target.

    Args:
        results: Regression results to write.
        method: Name of the regression method.
        path: Output file path.
    """
    if not results:
        return

    # collect all driver FIGIs across results
    all_drivers = list(dict.fromkeys(d for r in results for d in r.betas))

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        header = ["target_figi", "method", "intercept", "r_squared", "n_observations"] + [
            f"beta_{d}" for d in all_drivers
        ]
        writer.writerow(header)
        for r in results:
            row = [r.target_figi, method, r.intercept, r.r_squared, r.n_observations] + [
                r.betas.get(d, "") for d in all_drivers
            ]
            writer.writerow(row)
