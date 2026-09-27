import json
import socket
import subprocess
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

from it_diagnostics import checks
from it_diagnostics.config import Config, ServiceTarget
from it_diagnostics.network_worker import probe


def test_memory_pressure_uses_available_memory(monkeypatch):
    monkeypatch.setattr(psutil, "virtual_memory", lambda: SimpleNamespace(percent=96, total=1000, available=40))
    result = checks.memory_check(Config())
    assert result.status == "FAIL"
    assert result.evidence["available_bytes"] == 40


def test_cpu_has_a_nonzero_sampling_interval(monkeypatch):
    seen = []
    monkeypatch.setattr(psutil, "cpu_percent", lambda interval: seen.append(interval) or 90)
    assert checks.cpu_check(Config()).status == "WARNING"
    assert seen == [0.5]


def test_missing_metrics_are_not_healthy(monkeypatch):
    def unavailable():
        raise PermissionError("not accessible")
    monkeypatch.setattr(psutil, "virtual_memory", unavailable)
    assert checks.memory_check(Config()).status == "SKIP"


def test_missing_disk_path_fails(tmp_path):
    assert checks.disk_check(str(tmp_path / "missing"), Config(), 0).status == "FAIL"


def test_disk_threshold(monkeypatch):
    monkeypatch.setattr(psutil, "disk_usage", lambda p: SimpleNamespace(percent=90, total=1000, free=100))
    assert checks.disk_check("/", Config(), 0).status == "FAIL"


def test_interfaces_no_addresses_collected(monkeypatch):
    monkeypatch.setattr(psutil, "net_if_stats", lambda: {"test0": SimpleNamespace(isup=False, speed=0, mtu=1500)})
    result = checks.interface_check()
    assert result.status == "WARNING"
    assert set(result.evidence["interfaces"]["test0"]) == {"is_up", "speed_mbps", "mtu"}


def test_dns_resolution_failure_is_explained(monkeypatch):
    def bad_name(*a, **kw):
        raise socket.gaierror("synthetic resolver error")
    monkeypatch.setattr(socket, "getaddrinfo", bad_name)
    result = probe("dns", "fictional.test", 0, 1)
    assert result["ok"] is False and result["stage"] == "dns"


def test_worker_deadline(monkeypatch):
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 0.2
        assert kwargs.get("shell", False) is False
        raise subprocess.TimeoutExpired(args[0], 0.2)
    monkeypatch.setattr(checks.subprocess, "run", timeout)
    result = checks.network_check("dns", "example.test", 0, 0.2, 0)
    assert result.status == "FAIL" and result.evidence["stage"] == "timeout"


def test_malformed_worker_output_is_unverified(monkeypatch):
    monkeypatch.setattr(checks.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout="{}"))
    assert checks.network_check("dns", "example.test", 0, 1, 0).status == "SKIP"


def test_dns_success_omits_resolved_ip_addresses(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **kw: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 0))])
    result = probe("dns", "example.test", 0, 1)
    assert result["address_count"] == 1
    assert "192.0.2.1" not in json.dumps(result)


def test_local_tcp_round_trip_via_real_worker():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        result = checks.network_check("tcp", "127.0.0.1", listener.getsockname()[1], 5, 0)
    assert result.status == "OK", result.summary


def test_tcp_refusal_in_worker():
    # A bound socket without listen() has no accepting TCP listener; no port-allocation race.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as target:
        target.bind(("127.0.0.1", 0))
        result = probe("tcp", "127.0.0.1", target.getsockname()[1], 1)
    assert result["ok"] is False and result["stage"] == "tcp"


@pytest.mark.parametrize("active, expected", [("active", "OK"), ("inactive", "FAIL"), ("activating", "WARNING")])
def test_systemd_states(monkeypatch, active, expected):
    monkeypatch.setattr(checks.platform, "system", lambda: "Linux")
    monkeypatch.setattr(checks.shutil, "which", lambda _: "/usr/bin/systemctl")
    monkeypatch.setattr(Path, "is_dir", lambda _: True)
    def fake_run(args, **kwargs):
        assert args[-2:] == ["--", "demo.service"]
        assert not kwargs.get("shell")
        return SimpleNamespace(returncode=0, stdout=f"LoadState=loaded\nActiveState={active}\nSubState=running\n")
    monkeypatch.setattr(checks.subprocess, "run", fake_run)
    assert checks.service_check(ServiceTarget("demo.service", "linux"), 1, 0).status == expected


def test_systemd_missing_unit(monkeypatch):
    monkeypatch.setattr(checks.platform, "system", lambda: "Linux")
    monkeypatch.setattr(checks.shutil, "which", lambda _: "/usr/bin/systemctl")
    monkeypatch.setattr(Path, "is_dir", lambda _: True)
    monkeypatch.setattr(checks.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout="LoadState=not-found\nActiveState=inactive\n"))
    result = checks.service_check(ServiceTarget("missing.service", "linux"), 1, 0)
    assert result.status == "FAIL" and "not found" in result.summary


def test_linux_without_systemd_skips(monkeypatch):
    monkeypatch.setattr(checks.platform, "system", lambda: "Linux")
    monkeypatch.setattr(checks.shutil, "which", lambda _: None)
    assert checks.service_check(ServiceTarget("demo.service", "linux"), 1, 0).status == "SKIP"


@pytest.mark.parametrize("state, expected", [("running", "OK"), ("stopped", "FAIL"), ("start_pending", "WARNING")])
def test_windows_service_adapter(monkeypatch, state, expected):
    monkeypatch.setattr(checks.platform, "system", lambda: "Windows")
    monkeypatch.setattr(psutil, "win_service_get", lambda name: SimpleNamespace(status=lambda: state), raising=False)
    assert checks.service_check(ServiceTarget("Spooler", "windows"), 1, 0).status == expected


def test_services_skip_on_wrong_platform(monkeypatch):
    monkeypatch.setattr(checks.platform, "system", lambda: "Darwin")
    assert checks.service_check(ServiceTarget("Spooler", "windows"), 1, 0).status == "SKIP"
