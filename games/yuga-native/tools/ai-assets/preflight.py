#!/usr/bin/env python3
"""Capacity checks for a declared AI job; never downloads or runs a model."""

import argparse
import csv
from datetime import datetime, timezone
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

GIB = 1024 ** 3
MIB = 1024 ** 2


def positive_finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("must be a positive finite number") from exc
    if not math.isfinite(number) or number <= 0 or number > (2 ** 63 - 1) / GIB:
        raise argparse.ArgumentTypeError("must be positive, finite and fit a 64-bit byte count")
    return number


def parse_gpus(text):
    """Reject unknown, contradictory or partial metrics instead of inventing capacity."""
    devices = []
    seen = set()
    for row in csv.reader(io.StringIO(text)):
        if len(row) != 4:
            raise ValueError("expected GPU index, total MiB, free MiB, name")
        index, total, free, name = (part.strip() for part in row)
        if not index.isdecimal() or index in seen or not name:
            raise ValueError("invalid or duplicate GPU identity")
        if not total.isdecimal() or not free.isdecimal():
            raise ValueError("unavailable GPU memory metrics")
        total, free = int(total), int(free)
        if total <= 0 or free < 0 or free > total:
            raise ValueError("contradictory GPU memory metrics")
        devices.append({"index": int(index), "name": name,
                        "total_bytes": total * MIB, "free_bytes": free * MIB})
        seen.add(index)
    if not devices:
        raise ValueError("empty GPU inventory")
    return devices


def probe_gpus():
    executable = shutil.which("nvidia-smi")
    if not executable:
        return {"status": "unavailable", "devices": [], "reason": "nvidia-smi not found"}
    try:
        result = subprocess.run(
            [executable, "--query-gpu=index,memory.total,memory.free,name",
             "--format=csv,noheader,nounits"],
            check=True, capture_output=True, text=True, timeout=10)
        return {"status": "observed", "devices": parse_gpus(result.stdout)}
    except (OSError, subprocess.SubprocessError, ValueError):
        # Do not dump subprocess output, which is not needed to qualify capacity.
        return {"status": "unknown", "devices": [],
                "reason": "GPU query failed, timed out, or returned invalid metrics"}


def read_cgroup():
    result = {"version": "v2", "memory_limit_bytes": None, "cpu_quota_cores": None,
              "memory_status": "unknown", "cpu_status": "unknown"}
    try:
        value = Path("/sys/fs/cgroup/memory.max").read_text().strip()
        if value == "max":
            result["memory_status"] = "unlimited_by_cgroup"
        elif value.isdecimal() and int(value) > 0:
            result.update(memory_limit_bytes=int(value), memory_status="observed")
    except OSError:
        pass
    try:
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if quota == "max":
            result["cpu_status"] = "unlimited_by_cgroup"
        elif quota.isdecimal() and period.isdecimal() and int(quota) > 0 and int(period) > 0:
            result.update(cpu_quota_cores=int(quota) / int(period), cpu_status="observed")
    except (OSError, ValueError):
        pass
    return result


def assess(observed, requirements):
    failures = []
    disk_required = requirements["new_disk_bytes"] + requirements["reserve_disk_bytes"]
    disk = observed["disk"]
    if disk["status"] != "observed":
        failures.append("disk_capacity_unknown")
    elif disk["free_bytes"] < disk_required:
        failures.append("insufficient_free_disk_including_reserve")
    selected = None
    if requirements["execution"] == "cuda":
        gpu = observed["gpu"]
        if gpu["status"] != "observed":
            failures.append("nvidia_capacity_unavailable_or_unknown")
        else:
            eligible = [device for device in gpu["devices"]
                        if device["free_bytes"] >= requirements["vram_bytes"]]
            if not eligible:
                failures.append("no_single_gpu_has_required_free_vram")
            else:
                selected = max(eligible, key=lambda device: device["free_bytes"])["index"]
    return {"ready": not failures, "scope": "declared_capacity_only",
            "selected_gpu_index": selected, "failures": failures,
            "not_verified": ["model_or_dependency_download", "license_acceptance",
                             "CUDA_and_custom_kernel_compatibility", "model_inference",
                             "peak_system_RAM", "performance", "asset_quality"]}


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--required-vram-gib", type=positive_finite,
                      help="Declared single-GPU peak requirement including headroom")
    mode.add_argument("--cpu-only", action="store_true",
                      help="Only for a model with independently verified CPU support")
    result.add_argument("--required-free-disk-gib", required=True, type=positive_finite,
                        help="New weights + dependencies + extraction/cache/scratch estimate")
    result.add_argument("--reserve-disk-gib", type=positive_finite, default=1.0)
    result.add_argument("--path", type=Path, default=Path("/workspace"))
    result.add_argument("--output", type=Path, help="Write a new receipt; refuse to overwrite")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    path = args.path.resolve()
    try:
        usage = shutil.disk_usage(path)
        disk = {"status": "observed", "path": str(path), "total_bytes": usage.total,
                "free_bytes": usage.free}
    except OSError:
        disk = {"status": "unknown", "path": str(path)}
    observed = {"disk": disk, "gpu": probe_gpus(), "cgroup": read_cgroup(),
                "logical_cpus": os.cpu_count()}
    requirements = {"execution": "cpu" if args.cpu_only else "cuda",
                    "vram_bytes": 0 if args.cpu_only else math.ceil(args.required_vram_gib * GIB),
                    "new_disk_bytes": math.ceil(args.required_free_disk_gib * GIB),
                    "reserve_disk_bytes": math.ceil(args.reserve_disk_gib * GIB)}
    report = {"schema_version": 1, "checked_at": datetime.now(timezone.utc).isoformat(),
              "observed": observed, "requirements": requirements,
              "assessment": assess(observed, requirements)}
    serialized = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(serialized)
    print(serialized, end="")
    return 0 if report["assessment"]["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
