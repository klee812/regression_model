"""End-to-end pipeline integration test."""

from __future__ import annotations

import json
import textwrap

from regression_model.__main__ import main


def test_full_pipeline_json(tmp_path):
    """Full pipeline from CSV files through regression to JSON output."""
    # create target prices
    targets_csv = textwrap.dedent("""\
        date,figi,close
        2024-01-02,T1,100.0
        2024-01-03,T1,102.0
        2024-01-04,T1,101.0
        2024-01-05,T1,103.0
        2024-01-08,T1,105.0
        2024-01-09,T1,104.0
        2024-01-10,T1,106.0
        2024-01-11,T1,108.0
        2024-01-12,T1,107.0
        2024-01-15,T1,109.0
    """)
    (tmp_path / "targets.csv").write_text(targets_csv)

    # create driver prices
    drivers_csv = textwrap.dedent("""\
        date,figi,close
        2024-01-02,D1,200.0
        2024-01-02,D2,50.0
        2024-01-03,D1,204.0
        2024-01-03,D2,49.0
        2024-01-04,D1,202.0
        2024-01-04,D2,51.0
        2024-01-05,D1,206.0
        2024-01-05,D2,50.0
        2024-01-08,D1,210.0
        2024-01-08,D2,52.0
        2024-01-09,D1,208.0
        2024-01-09,D2,51.0
        2024-01-10,D1,212.0
        2024-01-10,D2,53.0
        2024-01-11,D1,216.0
        2024-01-11,D2,52.0
        2024-01-12,D1,214.0
        2024-01-12,D2,54.0
        2024-01-15,D1,218.0
        2024-01-15,D2,53.0
    """)
    (tmp_path / "drivers.csv").write_text(drivers_csv)

    # create config
    output_path = tmp_path / "output" / "results.json"
    config_content = textwrap.dedent(f"""\
        data:
          targets_path: "{tmp_path / 'targets.csv'}"
          drivers_path: "{tmp_path / 'drivers.csv'}"
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
