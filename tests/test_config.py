import json

import pytest

from it_diagnostics.config import ConfigError, Threshold, load_config, parse_config


@pytest.mark.parametrize("value, expected", [(0, "OK"), (79.99, "OK"), (80, "WARNING"), (89.99, "WARNING"), (90, "FAIL"), (100, "FAIL")])
def test_threshold_boundaries(value, expected):
    assert Threshold(80, 90).classify(value) == expected


@pytest.mark.parametrize("data", [
    [], {"typo": 1}, {"timeout_seconds": True}, {"timeout_seconds": 0},
    {"timeout_seconds": float("nan")}, {"cpu_sample_seconds": 0},
    {"thresholds": {"disk": {"warning": 90, "fail": 80}}},
    {"thresholds": {"memory": {"warning": 50}}},
    {"thresholds": {"cpu": {"warning": 20, "fail": 101}}},
    {"disk_paths": []}, {"disk_paths": [""]}, {"dns_hosts": "example.com"},
    {"dns_hosts": ["https://example.com"]}, {"dns_hosts": ["example.com\n"]},
    {"dns_hosts": ["example.test"] * 33}, {"tcp_targets": [{"host": "x", "port": True}]},
    {"tcp_targets": [{"host": "x", "port": 65536}]}, {"tcp_targets": [{"host": "x"}]},
    {"services": [{"name": "--help", "platform": "linux"}]},
    {"services": [{"name": "ssh;restart", "platform": "linux"}]},
    {"services": [{"name": "ssh", "platform": "linux"}]},
    {"services": [{"name": "anything", "platform": "macos"}]},
])
def test_invalid_configuration_is_rejected(data):
    with pytest.raises(ConfigError):
        parse_config(data)


def test_defaults_do_not_send_remote_probes():
    cfg = parse_config({})
    assert not cfg.dns_hosts and not cfg.tcp_targets and not cfg.services
    assert cfg.disk_paths


def test_valid_configuration_and_bom(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"dns_hosts": ["::1"], "tcp_targets": [{"host": "localhost", "port": 8000}],
                                "services": [{"name": "Spooler", "platform": "windows"}]}), encoding="utf-8-sig")
    cfg = load_config(path)
    assert cfg.tcp_targets[0].port == 8000
    assert cfg.services[0].name == "Spooler"


def test_bad_json_has_useful_error(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ConfigError, match="Cannot load"):
        load_config(path)
