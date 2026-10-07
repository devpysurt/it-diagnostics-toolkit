# Validation record

Version: **0.1.0**. Prepared on **2026-09-27**.

## Completed locally

Environment: a restricted Linux execution workspace, CPython **3.12.14**,
psutil **7.2.2**, pytest **9.1.1**.

| Check | Result |
| --- | --- |
| Unit and local integration suite | **69 passed** |
| Validating both example configurations | Passed |
| Editable package installation | Passed |
| Building a distributable Python wheel | Passed |
| Installing that wheel into a second clean virtual environment | Passed |
| Running the installed package outside the source directory | Passed |
| Real TCP handshake against a loopback listener, including the subprocess worker | Passed |
| Connection refusal against a bound, non-listening local socket | Passed |
| Generating five synthetic HTML/JSON report pairs | Passed |
| CLI error codes, HTML escaping, threshold boundaries and report serialization | Passed |
| Service adapters | Simulated Windows and systemd states passed |

## Completed remotely

On **2026-09-27**, the GitHub Actions **Tests** workflow
(`.github/workflows/ci.yml`) completed with **success** on commit
`36ca209e71b79e57f7c9325ecf5abbe3b05fbb05` (push to `main`).
[Run 36320849589](https://github.com/devpysurt/it-diagnostics-toolkit/actions/runs/36320849589)
passed all **9 matrix jobs**: Ubuntu, Windows and macOS with Python **3.10,
3.12 and 3.14**. Each job passed unit and local integration tests, installed
CLI checks and a local-collector smoke test.

This remote CI evidence is separate from the local validation above and does
not remove the live-environment limitations below.

## Live-environment limitations

The live collector ran successfully, but this workspace does not expose several
OS counters needed by psutil. CPU, memory and interface measurements returned
`SKIP`. A filesystem capacity check completed. The output explicitly reported
partial coverage. This run is **not** evidence of full hardware validation.

No public Internet endpoint was probed as part of local validation. Network
integration testing used the loopback interface; DNS errors and edge cases
used controlled test doubles.

## Checks still to perform after publication

- Run live diagnostics on an ordinary Windows or Linux workstation.
- Exercise actual installed-service queries on Windows and a systemd host.
- Open an HTML report in desktop/mobile browsers and check filters, evidence
  panels and print output. Browser-based visual validation could not be
  completed in the preparation environment because a browser process could
  not start. The README overview is an SVG illustration, not a screenshot.

Keep local validation, confirmed remote CI results and the remaining
live-environment limitations distinct when describing the project in a portfolio.
