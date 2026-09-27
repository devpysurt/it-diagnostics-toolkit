"""Command-line entry point with explicit automation exit codes."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .checks import collect_report
from .config import ConfigError, load_config
from .demo import SCENARIOS, demo_report
from .reporting import write_reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only IT diagnostics with HTML and JSON reports.")
    parser.add_argument("--version", action="version", version=f"itdiag {__version__}")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--config", type=Path, help="JSON configuration (default: local checks only)")
    mode.add_argument("--demo", choices=SCENARIOS, help="Generate a synthetic report without running probes")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--format", choices=("both", "html", "json"), default="both")
    parser.add_argument("--fail-on", choices=("none", "warning", "fail"), default="none",
                        help="Exit 1 on selected finding severity; default always 0 after successful report writing")
    args = parser.parse_args(argv)
    try:
        report = demo_report(args.demo) if args.demo else collect_report(load_config(args.config))
        paths = write_reports(report, args.output_dir, args.format)
    except (ConfigError, OSError, UnicodeError) as exc:
        print(f"itdiag: {exc}", file=sys.stderr)
        return 2
    print(f"IT Diagnostics Toolkit {__version__} | {report.mode} | Overall: {report.overall_status}")
    print(" | ".join(f"{status}: {count}" for status, count in report.counts.items()))
    if report.counts["SKIP"]:
        print("PARTIAL COVERAGE: skipped checks are unverified, not healthy.")
    for check in report.checks:
        print(f"[{check.status:7}] {check.title}: {check.summary}")
    for path in paths:
        print(f"Report: {path.resolve()}")
    if args.fail_on == "warning" and (report.counts["WARNING"] or report.counts["FAIL"]):
        return 1
    if args.fail_on == "fail" and report.counts["FAIL"]:
        return 1
    return 0
