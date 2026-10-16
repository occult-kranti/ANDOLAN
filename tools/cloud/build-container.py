#!/usr/bin/env python3
"""Build with the current managed proxy, without copying its trust into the image."""
import os
from pathlib import Path
import socket
import subprocess
from urllib.parse import urlsplit

root = Path(__file__).resolve().parents[2]
args = ["docker", "build"]
proxy_hosts = set()
for name in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy"):
    if os.environ.get(name):
        args += ["--build-arg", name]
        if name.lower() != "no_proxy":
            host = urlsplit(os.environ[name]).hostname
            if host:
                proxy_hosts.add(host)
# BuildKit can have different DNS from the caller in managed cloud containers.
# Resolve only the existing proxy endpoint; traffic still uses the same proxy.
for host in sorted(proxy_hosts):
    args += ["--add-host", f"{host}:{socket.gethostbyname(host)}"]
ca_path = os.environ.get("NODE_EXTRA_CA_CERTS")
if ca_path:
    contents = Path(ca_path).read_text()
    if "PRIVATE KEY" in contents or "BEGIN CERTIFICATE" not in contents:
        raise ValueError("Registry trust must be a public certificate bundle")
    args += ["--secret", f"id=registry_ca,src={ca_path}"]
args += ["--tag", os.environ.get("ANDOLAN_CONTAINER_TAG", "andolan:0.3"), str(root)]
subprocess.run(args, check=True)
