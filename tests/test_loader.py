"""Tests for CSV data loading and pivoting."""

from __future__ import annotations

import textwrap

import pandas as pd

from regression_model.data.loader import _load_csv


def test_load_csv_pivots_to_wide(tmp_path):
    """Long-format CSV is pivoted to wide format with correct values."""
    csv_content = textwrap.dedent("""\
        date,figi,close
        2024-01-02,FIGI_A,100.0
        2024-01-02,FIGI_B,200.0
        2024-01-03,FIGI_A,101.0
        2024-01-03,FIGI_B,202.0
    """)
    p = tmp_path / "prices.csv"
    p.write_text(csv_content)

    df = _load_csv(p, ["FIGI_A", "FIGI_B"])

    assert list(df.columns) == ["FIGI_A", "FIGI_B"]
    assert len(df) == 2
    assert df.iloc[0]["FIGI_A"] == 100.0
    assert df.iloc[1]["FIGI_B"] == 202.0


def test_load_csv_filters_figis(tmp_path):
    """Only requested FIGIs are included in the result."""
    csv_content = textwrap.dedent("""\
        date,figi,close
        2024-01-02,FIGI_A,100.0
        2024-01-02,FIGI_B,200.0
        2024-01-02,FIGI_C,300.0
    """)
    p = tmp_path / "prices.csv"
    p.write_text(csv_content)

    df = _load_csv(p, ["FIGI_A"])

    assert list(df.columns) == ["FIGI_A"]
    assert len(df) == 1
