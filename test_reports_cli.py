import json
from dataclasses import replace

import pytest

from it_diagnostics import cli
from it_diagnostics.demo import SCENARIOS, demo_report
from it_diagnostics.models import Check, Report
from it_diagnostics.reporting import render_html, write_reports


@pytest.mark.parametrize("scenario, overall", [("healthy", "OK"), ("memory-pressure", "WARNING"), ("disk-full", "FAIL"), ("dns-failure", "FAIL"), ("service-down", "FAIL")])
def test_demo_scenarios_are_consistent(scenario, overall):
    report = demo_report(scenario)
    assert report.overall_status == overall
    assert sum(report.counts.values()) == len(report.checks)
    assert "SYNTHETIC DATA" in render_html(report)


def test_all_skipped_is_not_ok():
    report = Report("now", "live", {}, [Check("x", "test", "test", "SKIP", "unavailable", "review")], "0.1.0")
    assert report.overall_status == "SKIP"
    assert report.to_dict()["coverage"] == "partial"
    assert "PARTIAL COVERAGE" in render_html(report)


def test_html_escapes_external_text():
    report = demo_report("healthy")
    attack = '<img src=x onerror="alert(1)">'
    report.checks[0] = replace(report.checks[0], title=attack, summary=attack, recommendation=attack, evidence={"payload": "</script>"})
    report.inventory["os"] = attack
    rendered = render_html(report)
    assert attack not in rendered
    assert "&lt;img" in rendered and "&lt;/script&gt;" in rendered


def test_reports_are_parseable_and_do_not_overwrite(tmp_path):
    report = demo_report("disk-full")
    first = write_reports(report, tmp_path)
    second = write_reports(report, tmp_path)
    assert set(first).isdisjoint(second)
    assert json.loads(first[0].read_text(encoding="utf-8"))["overall_status"] == "FAIL"
    assert first[1].read_text(encoding="utf-8").startswith("<!doctype html>")


def test_demo_does_not_collect_live_metrics(tmp_path, monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("Demo invoked the live collector")
    monkeypatch.setattr(cli, "collect_report", forbidden)
    assert cli.main(["--demo", "healthy", "--output-dir", str(tmp_path)]) == 0


@pytest.mark.parametrize("scenario, policy, code", [
    ("healthy", "fail", 0), ("disk-full", "none", 0), ("disk-full", "fail", 1),
    ("memory-pressure", "fail", 0), ("memory-pressure", "warning", 1),
])
def test_exit_codes(tmp_path, scenario, policy, code):
    assert cli.main(["--demo", scenario, "--fail-on", policy, "--format", "json", "--output-dir", str(tmp_path)]) == code


def test_bad_config_returns_two(tmp_path):
    assert cli.main(["--config", str(tmp_path / "missing.json")]) == 2


def test_unwritable_output_returns_two(tmp_path):
    output = tmp_path / "file"
    output.write_text("not a directory", encoding="utf-8")
    assert cli.main(["--demo", "healthy", "--output-dir", str(output)]) == 2


def test_demo_and_config_are_mutually_exclusive():
    with pytest.raises(SystemExit) as exc:
        cli.main(["--demo", "healthy", "--config", "config.json"])
    assert exc.value.code == 2
