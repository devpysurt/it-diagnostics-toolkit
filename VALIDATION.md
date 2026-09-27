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

## Live-environment limitations

The live collector ran successfully, but this workspace does not expose several
OS counters needed by psutil. CPU, memory and interface measurements returned
`SKIP`. A filesystem capacity check completed. The output explicitly reported
partial coverage. This run is **not** evidence of full hardware validation.

No public Internet endpoint was probed as part of local validation. Network
integration testing used the loopback interface; DNS errors and edge cases
used controlled test doubles.

## Checks still to perform after publication

- Run the included GitHub Actions matrix on Ubuntu, Windows and macOS.
- Run live diagnostics on an ordinary Windows or Linux workstation.
- Exercise actual installed-service queries on Windows and a systemd host.
- Open an HTML report in desktop/mobile browsers and check filters, evidence
  panels and print output. Browser-based visual validation could not be
  completed in the preparation environment because a browser process could
  not start. The README overview is an SVG illustration, not a screenshot.

The repository includes CI configuration, but no successful remote CI run is
claimed before the repository is published. Keep this distinction when describing
the project in a portfolio.
