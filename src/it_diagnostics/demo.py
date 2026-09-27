"""Deterministic fictional fixtures. Demo mode never inspects or changes the host."""

from dataclasses import replace

from . import __version__
from .models import Check, Report

SCENARIOS = ("healthy", "memory-pressure", "disk-full", "dns-failure", "service-down")


def demo_report(scenario: str) -> Report:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    checks = [
        Check("cpu", "Resources", "CPU utilization", "OK", "18.4% utilization",
              "No action required for this sample.", {"percent": 18.4, "sample_seconds": 0.5, "warning_at": 85, "fail_at": 95}),
        Check("memory", "Resources", "Memory utilization", "OK", "42.0% utilization",
              "No action required for this sample.", {"percent": 42.0, "total_bytes": 17179869184,
                                                     "available_bytes": 9964324127, "warning_at": 80, "fail_at": 95}),
        Check("disk.0", "Resources", "Disk space: /", "OK", "36.0% utilization",
              "No action required for this sample.", {"path": "/", "percent": 36.0, "total_bytes": 536870912000,
                                                     "free_bytes": 343597383680, "warning_at": 80, "fail_at": 90}),
        Check("interfaces", "Network", "Network interfaces", "OK", "1 of 1 interfaces is up.",
              "Link state alone does not establish Internet access.",
              {"interfaces": {"eth0": {"is_up": True, "speed_mbps": 1000, "mtu": 1500}}}),
        Check("dns.0", "Network", "DNS: support.example.test", "OK", "Name resolution succeeded (simulated).",
              "Resolution success does not prove application availability.", {"host": "support.example.test", "elapsed_ms": 12.1}),
        Check("tcp.0", "Network", "TCP: support.example.test:443", "OK", "TCP connection established (simulated).",
              "TCP success does not validate HTTP or TLS.", {"host": "support.example.test", "port": 443, "elapsed_ms": 23.8}),
        Check("service.0", "Services", "Service: demo-agent.service", "OK", "Current state: active (simulated).",
              "Service state does not establish application health.", {"name": "demo-agent.service", "state": "active"}),
    ]
    if scenario == "memory-pressure":
        checks[1] = replace(checks[1], status="WARNING", summary="88.0% utilization",
                            recommendation="Inspect memory-heavy processes and repeat the measurement. "
                            "A single snapshot cannot establish a memory leak.",
                            evidence={**checks[1].evidence, "percent": 88.0, "available_bytes": 2061584302})
    elif scenario == "disk-full":
        checks[2] = replace(checks[2], status="FAIL", summary="96.0% utilization",
                            recommendation="Identify large files and review log retention. Confirm ownership and backups "
                            "before cleanup, then rerun diagnostics to verify free space.",
                            evidence={**checks[2].evidence, "percent": 96.0, "free_bytes": 21474836480})
    elif scenario == "dns-failure":
        checks[4] = replace(checks[4], status="FAIL", summary="Name resolution failed (simulated).",
                            recommendation="Verify the hostname, resolver configuration and VPN. Compare with a "
                            "known-good hostname before attributing the failure to DNS infrastructure.",
                            evidence={"host": "support.example.test", "stage": "dns", "error": "gaierror"})
        checks[5] = replace(checks[5], status="FAIL", summary="TCP probe could not resolve the destination (simulated).",
                            recommendation="Resolve the name lookup issue, then repeat the TCP probe. "
                            "No TCP connection was attempted in this scenario.",
                            evidence={"host": "support.example.test", "port": 443, "stage": "dns", "error": "gaierror"})
    elif scenario == "service-down":
        checks[6] = replace(checks[6], status="FAIL", summary="Current state: inactive (simulated).",
                            recommendation="Confirm the service should be running. Inspect service logs and dependencies "
                            "before an authorized restart, then check application behavior.",
                            evidence={"name": "demo-agent.service", "state": "inactive"})
    return Report("2026-09-27T09:00:00+00:00", f"demo:{scenario}",
                  {"os": "Linux (fictional demo)", "os_release": "demo", "architecture": "x86_64",
                   "logical_cpus": 8, "physical_cpus": 4, "uptime_seconds": 86400,
                   "hostname_collected": False, "ip_addresses_collected": False}, checks, __version__)
