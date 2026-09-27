# Troubleshooting the toolkit

## Python or pip is not found

On Windows try `py -3 --version`. On Linux/macOS try `python3 --version`.
Install Python from its official distribution or your OS package manager, then
reopen the terminal. Use the virtual-environment Python for both installation
and execution so packages are installed into the correct interpreter.

## PowerShell blocks script activation

Activation is optional. Use `.\.venv\Scripts\python.exe` directly as shown in
the README. No execution-policy change is needed.

## `No module named it_diagnostics` or `psutil`

From the folder containing `pyproject.toml`, run your virtual-environment Python
with `-m pip install ".[dev]"`. Do not run a file from `src/` directly.

## CPU, memory or service check says SKIP

Read the finding. A restricted container may not expose `/proc`, Windows may
restrict a service query, or Linux may not be running systemd. The tool does
not elevate privileges automatically. Try the same command on the workstation
you actually want to inspect using your normal account.

## CPU is unexpectedly high

One short sample may catch a transient spike. Repeat the run or increase
`cpu_sample_seconds` (0.1 to 10 seconds). Correlate with the user's symptom and
an OS process view before concluding that CPU usage is the cause.

## TCP succeeds but the website still fails

A connection to a port establishes transport reachability only. TLS negotiation,
HTTP responses, authentication and application workflows need separate checks.

## DNS or TCP probe times out

Check the destination and network context. The timeout is configurable from
0.1 to 30 seconds. Very small limits may expire during worker startup. OS
process startup/cleanup can add overhead beyond the requested worker deadline.

## Disk path does not exist

Change `disk_paths` for your computer. Windows backslashes need JSON escaping:
`"C:\\"`. Relative paths are relative to your terminal's current directory.

## Reports are not appearing

Check the paths printed by the CLI and verify the output directory is writable.
Each run creates unique filenames. If you request only JSON, no HTML is created.

## GitHub shows HTML source instead of a report

Download the HTML file and open it locally. The README includes an SVG overview.
GitHub Pages is not required to use this project.

## How do I share evidence safely?

Prefer `examples/reports/` for the public repository. Review live reports before
sharing because paths, interface names, configured destinations and service names
can reveal environment details. `.gitignore` is a convenience, not anonymization.
