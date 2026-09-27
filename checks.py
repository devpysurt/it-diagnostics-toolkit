"""Collectors and checks. Unsupported or inaccessible data is never called OK."""

import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

from . import __version__
from .config import Config, ServiceTarget, Threshold
from .models import Check, Report


def _skipped(check_id: str, category: str, title: str, reason: str) -> Check:
    return Check(check_id, category, title, "SKIP", reason,
                 "Review platform support, permissions and configuration; this check did not establish health.")


def _resource(check_id: str, title: str, value: float, threshold: Threshold,
              evidence: dict, action: str) -> Check:
    status = threshold.classify(value)
    return Check(check_id, "Resources", title, status, f"{value:.1f}% utilization",
                 action if status != "OK" else "No action required for this sample. Recheck if symptoms persist.",
                 {**evidence, "percent": round(value, 2), "warning_at": threshold.warning, "fail_at": threshold.fail})


def cpu_check(cfg: Config) -> Check:
    try:
        value = psutil.cpu_percent(interval=cfg.cpu_sample_seconds)
        return _resource("cpu", "CPU utilization", value, cfg.cpu,
                         {"sample_seconds": cfg.cpu_sample_seconds},
                         "Repeat the sample; inspect CPU-heavy processes in Task Manager or top before taking action.")
    except (OSError, psutil.Error, NotImplementedError) as exc:
        return _skipped("cpu", "Resources", "CPU utilization", f"CPU metrics unavailable ({type(exc).__name__}).")


def memory_check(cfg: Config) -> Check:
    try:
        memory = psutil.virtual_memory()
        return _resource("memory", "Memory utilization", memory.percent, cfg.memory,
                         {"total_bytes": memory.total, "available_bytes": memory.available},
                         "Inspect memory-heavy processes and available RAM. Save work before closing applications; "
                         "one sample does not prove a memory leak.")
    except (OSError, psutil.Error, NotImplementedError) as exc:
        return _skipped("memory", "Resources", "Memory utilization", f"Memory metrics unavailable ({type(exc).__name__}).")


def disk_check(path: str, cfg: Config, index: int) -> Check:
    check_id = f"disk.{index}"
    try:
        disk = psutil.disk_usage(path)
        return _resource(check_id, f"Disk space: {path}", disk.percent, cfg.disk,
                         {"path": path, "total_bytes": disk.total, "free_bytes": disk.free},
                         "Identify large files and review log retention or cleanup options. "
                         "Confirm ownership and backups before deleting anything; this check measures capacity, not disk health.")
    except FileNotFoundError:
        return Check(check_id, "Resources", f"Disk space: {path}", "FAIL", "Configured path does not exist.",
                     "Correct the disk path or confirm that the expected volume is mounted.", {"path": path})
    except (OSError, psutil.Error, NotImplementedError) as exc:
        return _skipped(check_id, "Resources", f"Disk space: {path}", f"Disk metrics unavailable ({type(exc).__name__}).")


def interface_check() -> Check:
    try:
        stats = psutil.net_if_stats()
        data = {name: {"is_up": value.isup, "speed_mbps": value.speed, "mtu": value.mtu}
                for name, value in sorted(stats.items())}
        if not data:
            return _skipped("interfaces", "Network", "Network interfaces", "No interface data returned.")
        up_count = sum(value["is_up"] for value in data.values())
        return Check("interfaces", "Network", "Network interfaces", "OK" if up_count else "WARNING",
                     f"{up_count} of {len(data)} interfaces are up (loopback may be included).",
                     "Link state alone does not establish Internet access. Use configured DNS and TCP checks "
                     "to test the required destination.", {"interfaces": data})
    except (OSError, psutil.Error, NotImplementedError) as exc:
        return _skipped("interfaces", "Network", "Network interfaces", f"Interface data unavailable ({type(exc).__name__}).")


def network_check(kind: str, host: str, port: int, timeout: float, index: int) -> Check:
    check_id = f"{kind}.{index}"
    title = f"DNS: {host}" if kind == "dns" else f"TCP: {host}:{port}"
    evidence = {"host": host, "timeout_seconds": timeout}
    if kind == "tcp":
        evidence["port"] = port
    # subprocess.run kills and waits for the worker on timeout, including a stuck resolver.
    try:
        result = subprocess.run(
            [sys.executable, "-m", "it_diagnostics.network_worker", kind, host, str(port), str(timeout)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
        if result.returncode:
            return _skipped(check_id, "Network", title, "Network worker could not complete.")
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict) or type(payload.get("ok")) is not bool:
            raise ValueError("Invalid worker result")
    except subprocess.TimeoutExpired:
        payload = {"ok": False, "stage": "timeout", "error": "Timeout", "message": "Probe exceeded its deadline."}
    except (OSError, ValueError) as exc:
        return _skipped(check_id, "Network", title, f"Network probe unavailable ({type(exc).__name__}).")
    if payload["ok"]:
        summary = "Name resolution succeeded." if kind == "dns" else "TCP connection established."
        action = ("Resolution success does not prove that the application is available." if kind == "dns" else
                  "TCP success does not validate HTTP responses, TLS certificates or application health.")
    else:
        summary = f"Probe failed during {payload.get('stage', 'unknown')}: {payload.get('message', 'unknown error')}"
        action = ("Verify the hostname, configured resolver and VPN/network connection. Compare with a known-good name; "
                  "failure alone does not prove a DNS server outage." if payload.get("stage") == "dns" else
                  "Check name resolution, routing, firewall rules and the target listener. "
                  "A failed connection does not by itself identify which component is at fault.")
    return Check(check_id, "Network", title, "OK" if payload["ok"] else "FAIL", summary, action,
                 {**evidence, **payload})


def service_check(target: ServiceTarget, timeout: float, index: int) -> Check:
    check_id, title = f"service.{index}", f"Service: {target.name}"
    evidence = {"name": target.name, "platform": target.platform}
    if platform.system().lower() != target.platform:
        return _skipped(check_id, "Services", title, f"Check only applies to {target.platform}.")
    try:
        if target.platform == "windows":
            state = psutil.win_service_get(target.name).status()
            healthy = state == "running"
        else:
            executable = shutil.which("systemctl")
            if not executable or not Path("/run/systemd/system").is_dir():
                return _skipped(check_id, "Services", title, "An active systemd manager is not available.")
            result = subprocess.run(
                [executable, "show", "--no-pager", "--property=LoadState,ActiveState,SubState", "--", target.name],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
            )
            properties = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
            evidence.update(properties)
            if properties.get("LoadState") == "not-found":
                return Check(check_id, "Services", title, "FAIL", "Configured service was not found.",
                             "Check the exact unit name and whether the required service is installed.", evidence)
            if result.returncode or not properties.get("ActiveState"):
                return _skipped(check_id, "Services", title, "systemd service state could not be read.")
            state = properties["ActiveState"]
            healthy = state == "active"
        transitional = state in ("activating", "deactivating", "reloading", "start_pending", "stop_pending",
                                "continue_pending", "pause_pending")
        return Check(check_id, "Services", title, "OK" if healthy else "WARNING" if transitional else "FAIL",
                     f"Current state: {state}.",
                     "Service state does not establish application health." if healthy else
                     "Confirm that this service is expected to be running. Review its logs and dependencies before restarting.",
                     {**evidence, "state": state})
    except psutil.NoSuchProcess:
        return Check(check_id, "Services", title, "FAIL", "Configured service was not found.",
                     "Check the service name and installation.", evidence)
    except (OSError, psutil.Error, subprocess.TimeoutExpired, NotImplementedError) as exc:
        return _skipped(check_id, "Services", title, f"Service state unavailable ({type(exc).__name__}).")


def collect_report(cfg: Config) -> Report:
    inventory = {"os": platform.system(), "os_release": platform.release(),
                 "architecture": platform.machine(), "python_version": platform.python_version(),
                 "logical_cpus": None, "physical_cpus": None, "uptime_seconds": None,
                 "hostname_collected": False, "ip_addresses_collected": False}
    for key, reader in (
        ("logical_cpus", lambda: psutil.cpu_count(logical=True)),
        ("physical_cpus", lambda: psutil.cpu_count(logical=False)),
        ("uptime_seconds", lambda: max(0, round(time.time() - psutil.boot_time()))),
    ):
        try:
            inventory[key] = reader()
        except (OSError, psutil.Error, NotImplementedError):
            pass  # null explicitly represents unavailable inventory, never a zero measurement.
    checks = [cpu_check(cfg), memory_check(cfg)]
    checks.extend(disk_check(path, cfg, i) for i, path in enumerate(cfg.disk_paths))
    checks.append(interface_check())
    checks.extend(network_check("dns", host, 0, cfg.timeout_seconds, i) for i, host in enumerate(cfg.dns_hosts))
    checks.extend(network_check("tcp", target.host, target.port, cfg.timeout_seconds, i)
                  for i, target in enumerate(cfg.tcp_targets))
    checks.extend(service_check(target, cfg.timeout_seconds, i) for i, target in enumerate(cfg.services))
    if not cfg.dns_hosts and not cfg.tcp_targets:
        checks.append(Check("network.not-configured", "Network", "Remote connectivity", "SKIP",
                            "No DNS or TCP targets configured; no remote probes were sent.",
                            "Add only the destinations you need to test to a configuration file."))
    if not cfg.services:
        checks.append(Check("services.not-configured", "Services", "Service checks", "SKIP",
                            "No required services configured.", "Add service names expected to be running on this machine."))
    return Report(datetime.now(timezone.utc).isoformat(timespec="seconds"), "live", inventory, checks, __version__)
