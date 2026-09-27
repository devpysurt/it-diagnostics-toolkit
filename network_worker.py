"""Isolate blocking OS DNS resolution so the parent can enforce a deadline.

No shell, ICMP, subnet scan, application payload or credentials are used.
"""

import json
import socket
import sys
import time


def probe(kind: str, host: str, port: int, timeout: float) -> dict:
    started = time.monotonic()
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        return {"ok": False, "stage": "dns", "error": type(exc).__name__, "message": str(exc)}
    if not addresses:
        return {"ok": False, "stage": "dns", "error": "EmptyResolution", "message": "No addresses returned"}
    if kind == "dns":
        return {"ok": True, "stage": "dns", "address_count": len({a[4][0] for a in addresses}),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 2)}
    last_error = "No connection attempted"
    seen = set()
    for family, socktype, proto, _, address in addresses:
        if (family, address) in seen:
            continue
        seen.add((family, address))
        remaining = timeout - (time.monotonic() - started)
        if remaining <= 0:
            break
        try:
            with socket.socket(family, socktype, proto) as connection:
                connection.settimeout(remaining)
                connection.connect(address)
            return {"ok": True, "stage": "tcp", "elapsed_ms": round((time.monotonic() - started) * 1000, 2)}
        except OSError as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    return {"ok": False, "stage": "tcp", "error": "ConnectionFailed", "message": last_error}


def main() -> None:
    kind, host, port, timeout = sys.argv[1:]
    print(json.dumps(probe(kind, host, int(port), float(timeout))))


if __name__ == "__main__":
    main()
