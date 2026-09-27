# Architecture and trade-offs

## A small support tool, not a monitoring platform

The CLI runs once, gathers evidence and exits. There is no daemon, database,
web server, automatic remediation or remote administration. Reports are the
only intended filesystem changes. A single dependency, `psutil`, provides
portable OS metrics; the rest uses the Python standard library.

## Data flow

1. `argparse` selects live or demo mode.
2. `config.py` validates JSON and applies documented defaults.
3. Each live check returns a `Check` with status, evidence and a next step.
4. `Report` derives severity counts, overall status and coverage.
5. The same report is serialized as JSON and rendered as escaped HTML.
6. The CLI applies an optional exit-code policy after reports are written.

Collectors and rendering are separate so report tests never need to query the
host. Demo scenarios use the same model and renderer as live checks.

## Why psutil?

CPU and memory interfaces differ between operating systems. psutil avoids
parsing localized command output. CPU sampling uses a nonzero interval rather
than the meaningless first nonblocking sample. Memory evidence uses available
RAM, not just the raw free-memory figure. The package is constrained to
`>=5.9.8,<8` to avoid unreviewed major-version API changes.

## Timeouts and process boundaries

Socket connection timeouts do not bound a separate blocking OS DNS lookup.
DNS and TCP work therefore runs in a child Python process. The parent uses
`subprocess.run(timeout=...)`, which kills and waits for that worker on expiry.
The child also shares a connection-time budget across resolved addresses.
All resolved addresses belong to a single explicitly configured destination.

The timeout includes normal worker execution, but OS process creation and
cleanup can add small overhead; it is not a hard real-time guarantee. Targets
run sequentially, so total duration increases with the number of targets.

## Services

- Windows: `psutil.win_service_get(name).status()` uses the Windows service API.
- Linux: `systemctl show` retrieves properties suitable for parsing. Commands
  are passed as argument arrays, without a shell. Exact `.service` names are
  required, and an active systemd manager must exist.
- Other platforms: `SKIP`; no attempt to infer a healthy service from a process name.

An inactive configured service fails because the configuration is an explicit
list of required running services. A transient start/stop/reload state warns.
An active service is not proof that its application is functioning correctly.

## Error handling

Unavailable metrics, permission failures and unsupported service managers are
unverified (`SKIP`). A missing configured path/service or failed destination
probe is a finding (`FAIL`). Invalid configuration is a usage error (exit 2).
This distinction prevents both false assurances and confusing tool failures
with proven outages. Partial coverage is surfaced even when completed checks
are OK.

## Report format

JSON contains `schema_version`, `tool_version`, `generated_at`, `mode`,
`inventory`, `checks`, `overall_status`, `counts` and `coverage`.
Each check has a stable-in-run ID, category, title, status, summary,
recommendation and evidence. Array-target IDs use their configuration index.

HTML has no CDN dependencies or external resources. All dynamic strings are
escaped, including JSON inside evidence panels. A small inline script filters
findings; all findings remain readable when JavaScript is disabled.
Each output file is written to a temporary sibling and renamed into place.
The two-file pair is not a filesystem transaction: a second-file write failure
can leave the first completed report. Unique report basenames prevent normal
successive runs from overwriting previous results.

## Intentional limits

This version does not check SMART, temperatures, gateway routes, HTTP bodies,
TLS certificates, cgroup resource limits or root causes automatically. These
would require separate evidence and platform-specific behavior. Recommendations
are investigation prompts, not a claim that the cause has been proven.
