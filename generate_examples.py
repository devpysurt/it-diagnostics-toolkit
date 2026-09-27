"""Regenerate fictional examples after installing the project in editable mode."""

import json
from pathlib import Path

from it_diagnostics.demo import SCENARIOS, demo_report
from it_diagnostics.reporting import render_html

root = Path(__file__).resolve().parents[1]
destination = root / "examples" / "reports"
destination.mkdir(parents=True, exist_ok=True)
for scenario in SCENARIOS:
    report = demo_report(scenario)
    (destination / f"{scenario}.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    (destination / f"{scenario}.html").write_text(render_html(report), encoding="utf-8")
print(f"Generated {len(SCENARIOS)} synthetic report pairs in {destination}")
