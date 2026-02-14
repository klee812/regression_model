"""End-to-end pipeline integration test."""

from __future__ import annotations

import json
import textwrap

from regression_model.__main__ import main


def test_full_pipeline_json(tmp_path):
    """Full pipeline from CSV files through regression to JSON output."""
    # create combined prices file
    prices_csv = textwrap.dedent("""\
        identifier,currency,date,price
        T1,USD,2024-01-02,100.0
        D1,USD,2024-01-02,200.0
        D2,USD,2024-01-02,50.0
        T1,USD,2024-01-03,102.0
        D1,USD,2024-01-03,204.0
        D2,USD,2024-01-03,49.0
        T1,USD,2024-01-04,101.0
        D1,USD,2024-01-04,202.0
        D2,USD,2024-01-04,51.0
        T1,USD,2024-01-05,103.0
        D1,USD,2024-01-05,206.0
        D2,USD,2024-01-05,50.0
        T1,USD,2024-01-08,105.0
        D1,USD,2024-01-08,210.0
        D2,USD,2024-01-08,52.0
        T1,USD,2024-01-09,104.0
        D1,USD,2024-01-09,208.0
        D2,USD,2024-01-09,51.0
        T1,USD,2024-01-10,106.0
        D1,USD,2024-01-10,212.0
        D2,USD,2024-01-10,53.0
        T1,USD,2024-01-11,108.0
        D1,USD,2024-01-11,216.0
        D2,USD,2024-01-11,52.0
        T1,USD,2024-01-12,107.0
        D1,USD,2024-01-12,214.0
        D2,USD,2024-01-12,54.0
        T1,USD,2024-01-15,109.0
        D1,USD,2024-01-15,218.0
        D2,USD,2024-01-15,53.0
    """)
    (tmp_path / "prices.csv").write_text(prices_csv)

    # create empty corp_actions and dividends
    (tmp_path / "corp_actions.csv").write_text(
        "identifier,ex_date,ratio_shares_adjustment,ratio_price_adjustment\n"
    )
    (tmp_path / "dividends.csv").write_text(
        "identifier,ex_date,ratio_shares_adjustment,div_amount\n"
    )

    # create config
    output_path = tmp_path / "output" / "results.json"
    config_content = textwrap.dedent(f"""\
        data:
          prices_path: "{tmp_path / 'prices.csv'}"
          corp_actions_path: "{tmp_path / 'corp_actions.csv'}"
          dividends_path: "{tmp_path / 'dividends.csv'}"
        targets:
          - "T1"
        drivers:
          - "D1"
          - "D2"
        regression:
          method: "ols"
          params: {{}}
        output:
          format: "json"
          path: "{output_path}"
    """)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)

    main(str(config_path))

    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)

    assert data["method"] == "ols"
    assert "T1" in data["results"]
    result = data["results"]["T1"]
    assert "betas" in result
    assert "D1" in result["betas"]
    assert "D2" in result["betas"]
    assert "intercept" in result
    assert "r_squared" in result
    assert result["n_observations"] == 9
