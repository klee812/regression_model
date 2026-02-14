"""Tests for CSV data loading."""

from __future__ import annotations

import textwrap

from regression_model.data.loader import _read_csv_dicts


def test_read_csv_dicts(tmp_path):
    """CSV file is read into a list of dicts."""
    csv_content = textwrap.dedent("""\
        identifier,currency,date,price
        FIGI_A,USD,2024-01-02,100.0
        FIGI_B,USD,2024-01-02,200.0
    """)
    p = tmp_path / "prices.csv"
    p.write_text(csv_content)

    rows = _read_csv_dicts(p)

    assert len(rows) == 2
    assert rows[0]["identifier"] == "FIGI_A"
    assert rows[0]["currency"] == "USD"
    assert rows[0]["date"] == "2024-01-02"
    assert rows[0]["price"] == "100.0"


def test_read_csv_dicts_empty(tmp_path):
    """Header-only CSV returns an empty list."""
    csv_content = "identifier,currency,date,price\n"
    p = tmp_path / "empty.csv"
    p.write_text(csv_content)

    rows = _read_csv_dicts(p)

    assert rows == []
