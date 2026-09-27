# Troubleshooting walkthroughs

All cases below are fictional exercises. Demo mode generates evidence without
creating real failures. The listed investigations are proposed next steps, not
actions automatically performed by the toolkit.

## 1. Workstation running out of disk space

**Generate:** `python -m it_diagnostics --demo disk-full`

**Observed evidence:** filesystem utilization is 96%; the configured failure
threshold is 90%. CPU and memory are within their demo thresholds.

**Interpretation:** low capacity is established for the sampled filesystem.
Physical disk damage and the owner of the used space are not established.

**Next steps:**

1. Identify large directories using the OS storage view or a disk-usage tool.
2. Check application logs, caches and retention settings.
3. Confirm ownership, retention requirements and backups before cleanup.
4. Rerun live diagnostics after an authorized change and compare free space.
5. Verify the user's original operation, such as saving a file, works again.

**Interview discussion:** explain why capacity and hardware health are different,
and why an automatic delete operation would be inappropriate for this tool.

## 2. Application endpoint cannot be resolved

**Generate:** `python -m it_diagnostics --demo dns-failure`

**Observed evidence:** name resolution fails. The TCP probe fails at its DNS
stage, so it never establishes whether the destination port accepts connections.

**Interpretation:** the immediate blocker is name resolution for that target.
A mistyped name, missing VPN, resolver configuration issue or missing DNS record
remain possible explanations. A global DNS outage is not proven.

**Next steps:**

1. Verify the exact hostname and the expected network/VPN context.
2. Compare with a known-good hostname in the same environment.
3. Inspect OS resolver settings and query results.
4. After name resolution recovers, rerun TCP and then an application-level test.

**Interview discussion:** explain how correlating failure stages avoids treating
two failed checks as two unrelated incidents.

## 3. Required service is stopped

**Generate:** `python -m it_diagnostics --demo service-down`

**Observed evidence:** the fictional `demo-agent.service` is inactive, while the
other demo checks complete successfully.

**Interpretation:** the required service is not active. This does not establish
why it stopped, whether dependencies failed or whether a restart would fix it.

**Next steps:**

1. Confirm the machine is supposed to run this service.
2. Inspect service logs, recent configuration changes and dependencies.
3. Follow the normal approval/runbook process for remediation.
4. Check service state after the authorized change.
5. Verify application behavior; `active` alone is insufficient.

**Interview discussion:** explain what should be included in an L3 escalation:
time, exact service, state, related logs, recent changes and reproduction steps.
