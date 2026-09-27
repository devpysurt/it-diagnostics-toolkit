"""Strict configuration parsing: a misspelled setting must not silently pass."""

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(ValueError):
    """A configuration file is invalid."""


@dataclass(frozen=True)
class Threshold:
    warning: float
    fail: float

    def classify(self, value: float) -> str:
        return "FAIL" if value >= self.fail else "WARNING" if value >= self.warning else "OK"


@dataclass(frozen=True)
class TcpTarget:
    host: str
    port: int


@dataclass(frozen=True)
class ServiceTarget:
    name: str
    platform: str


@dataclass
class Config:
    cpu_sample_seconds: float = 0.5
    timeout_seconds: float = 3.0
    cpu: Threshold = field(default_factory=lambda: Threshold(85, 95))
    memory: Threshold = field(default_factory=lambda: Threshold(80, 95))
    disk: Threshold = field(default_factory=lambda: Threshold(80, 90))
    disk_paths: list[str] = field(default_factory=lambda: [Path.cwd().anchor])
    dns_hosts: list[str] = field(default_factory=list)
    tcp_targets: list[TcpTarget] = field(default_factory=list)
    services: list[ServiceTarget] = field(default_factory=list)


def _object(value: object, keys: set[str], label: str) -> dict:
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be an object")
    unknown = value.keys() - keys
    if unknown:
        raise ConfigError(f"Unknown {label} key(s): {', '.join(sorted(unknown))}")
    return value


def _number(value: object, low: float, high: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{label} must be a number")
    if not math.isfinite(value) or not low <= value <= high:
        raise ConfigError(f"{label} must be between {low} and {high}")
    return float(value)


def _list(value: object, label: str) -> list:
    if not isinstance(value, list) or len(value) > 32:
        raise ConfigError(f"{label} must be an array of at most 32 items")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 1024:
        raise ConfigError(f"{label} must be a nonempty string of at most 1024 characters")
    if any(ord(c) < 32 for c in value):
        raise ConfigError(f"{label} must not contain control characters")
    return value


def _host(value: object) -> str:
    value = _text(value, "host")
    if any(c.isspace() for c in value) or any(c in value for c in "/@?#\\"):
        raise ConfigError("host must be a hostname or IP address, not a URL")
    return value


def parse_config(data: object) -> Config:
    data = _object(data, {"cpu_sample_seconds", "timeout_seconds", "thresholds",
                          "disk_paths", "dns_hosts", "tcp_targets", "services"}, "config")
    cfg = Config()
    if "cpu_sample_seconds" in data:
        cfg.cpu_sample_seconds = _number(data["cpu_sample_seconds"], 0.1, 10, "cpu_sample_seconds")
    if "timeout_seconds" in data:
        cfg.timeout_seconds = _number(data["timeout_seconds"], 0.1, 30, "timeout_seconds")
    for key, value in _object(data.get("thresholds", {}), {"cpu", "memory", "disk"}, "thresholds").items():
        value = _object(value, {"warning", "fail"}, f"thresholds.{key}")
        if set(value) != {"warning", "fail"}:
            raise ConfigError(f"thresholds.{key} requires warning and fail")
        warning = _number(value["warning"], 0, 100, f"{key}.warning")
        fail = _number(value["fail"], 0, 100, f"{key}.fail")
        if warning >= fail:
            raise ConfigError(f"{key}.warning must be less than {key}.fail")
        setattr(cfg, key, Threshold(warning, fail))
    if "disk_paths" in data:
        cfg.disk_paths = [_text(v, "disk path") for v in _list(data["disk_paths"], "disk_paths")]
        if not cfg.disk_paths:
            raise ConfigError("disk_paths must contain at least one path")
    cfg.dns_hosts = [_host(v) for v in _list(data.get("dns_hosts", []), "dns_hosts")]
    for target in _list(data.get("tcp_targets", []), "tcp_targets"):
        target = _object(target, {"host", "port"}, "TCP target")
        if set(target) != {"host", "port"}:
            raise ConfigError("Each TCP target requires host and port")
        port = target["port"]
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ConfigError("TCP port must be an integer between 1 and 65535")
        cfg.tcp_targets.append(TcpTarget(_host(target["host"]), port))
    for target in _list(data.get("services", []), "services"):
        target = _object(target, {"name", "platform"}, "service")
        if set(target) != {"name", "platform"} or target["platform"] not in ("linux", "windows"):
            raise ConfigError("Each service requires name and platform (linux or windows)")
        name = _text(target["name"], "service name")
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.@-]{0,199}", name):
            raise ConfigError("Use an exact service name containing letters, digits, _, ., @ or -")
        if target["platform"] == "linux" and not name.endswith(".service"):
            raise ConfigError("Linux service names must end in .service")
        cfg.services.append(ServiceTarget(name, target["platform"]))
    return cfg


def load_config(path: Path | None) -> Config:
    if path is None:
        return Config()
    try:
        return parse_config(json.loads(path.read_text(encoding="utf-8-sig")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Cannot load configuration: {exc}") from exc
