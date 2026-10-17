#!/usr/bin/env python3
"""Isolated real two-client native transport, interpolation/replay and negative controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
import urllib.request


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def run_case(engine: Path, project: Path, script: str, report: Path, extra: list[str] | None = None) -> dict:
    command = [str(engine), "--headless", "--path", str(project), "--script", f"res://tests/{script}", "--", f"--report={report}", *(extra or [])]
    run = subprocess.run(command, capture_output=True, text=True, timeout=25)
    report.with_suffix(".log").write_text(run.stdout + run.stderr)
    result = json.loads(report.read_text()) if report.exists() else {"passed": False, "missing_report": True}
    result["exit_code"] = run.returncode
    result["script_error"] = "SCRIPT ERROR" in run.stdout + run.stderr
    return result


def live_suite(repo: Path, engine: Path, project: Path, output: Path, reconnect: bool) -> dict:
    output.mkdir()
    ready = output / "server-ready.json"
    harness = output / "server.mts"
    harness.write_text(f'''import {{ createArenaServer }} from {json.dumps((repo / 'games/yuga/server/server.ts').as_uri())};
import {{ writeFile }} from 'node:fs/promises';
const server = await createArenaServer({{ port:0, host:'127.0.0.1', simulation:{{ duration:{6 if reconnect else 4}, botsPerTeam:0 }} }});
const address = server.address;
if (!address || typeof address === 'string') throw new Error('No TCP listener');
await writeFile({json.dumps(str(ready))}, JSON.stringify({{url:`ws://127.0.0.1:${{address.port}}/ws`,health:`http://127.0.0.1:${{address.port}}/health`}}));
let injected=0, maximumClients=0, closing=false;
const timer=setInterval(()=>{{for(const room of server.rooms.values()){{
 maximumClients=Math.max(maximumClients,room.clients.size);
 if(injected || room.clients.size!==2 || room.sim.time<3)continue;
 const snapshot=room.sim.snapshot();
 for(const socket of room.clients.values()){{
  socket.send(JSON.stringify({{type:'snapshot',snapshot:{{...snapshot,tick:Math.max(0,snapshot.tick-4)}}}}));
  socket.send('{{');
  socket.send(JSON.stringify({{type:'snapshot',snapshot:{{...snapshot,protocol:1}}}}));
  const extreme=structuredClone(snapshot);
  extreme.actors[0].yaw=1e308;
  if(extreme.actors.length>1)extreme.actors[1].yaw=-1e308;
  socket.send(JSON.stringify({{type:'snapshot',snapshot:extreme}}));
  socket.send(JSON.stringify({{type:'snapshot',snapshot:{{...snapshot,time:1e-50}}}}));
  injected++;
 }}
}}}},20);
process.on('SIGTERM',async()=>{{if(closing)return;closing=true;clearInterval(timer);
 const connectedBeforeClose=[...server.rooms.values()].reduce((n,r)=>n+r.clients.size,0);
 await server.close();
 await writeFile({json.dumps(str(output / 'server-report.json'))},JSON.stringify({{injectedClients:injected,maximumClients,connectedBeforeClose,roomsAfterClose:server.rooms.size}}));process.exit(0);
}});
''')
    processes: list[subprocess.Popen] = []
    handles = []
    result: dict = {"passed": False, "reconnect": reconnect, "clients": {}}
    try:
        log = (output / "server.log").open("w")
        handles.append(log)
        server = subprocess.Popen([str(repo / "node_modules/.bin/tsx"), str(harness)], cwd=repo, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        processes.append(server)
        deadline = time.monotonic() + 10
        connection = None
        while time.monotonic() < deadline:
            if ready.exists():
                try:
                    connection = json.loads(ready.read_text())
                    break
                except json.JSONDecodeError:
                    pass
            if server.poll() is not None:
                raise RuntimeError("Authority exited before listener readiness")
            time.sleep(.025)
        if not connection:
            raise TimeoutError("Authority listener did not start")
        clients = {}
        for role in ("host", "guest"):
            log = (output / f"{role}.log").open("w")
            handles.append(log)
            environment = os.environ.copy()
            environment.update({f"XDG_{key}_HOME": str(output / "xdg" / role / key.lower()) for key in ("DATA", "CONFIG", "CACHE")})
            command = [str(engine), "--headless", "--path", str(project), "--script", "res://tests/arena_client_cases.gd", "--",
                       f"--url={connection['url']}", f"--role={role}", f"--coordination={output / 'room.json'}", f"--report={output / (role + '-report.json')}", f"--recording={output / (role + '-snapshots.jsonl')}"]
            if not reconnect:
                command.append("--no-reconnect=true")
            process = subprocess.Popen(command, cwd=repo, env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            clients[role] = process
            processes.append(process)
        for role, process in clients.items():
            code = process.wait(timeout=25)
            path = output / f"{role}-report.json"
            data = json.loads(path.read_text()) if path.exists() else {"passed": False, "missing_report": True}
            data["exit_code"] = code
            result["clients"][role] = data
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(connection["health"], timeout=3) as response:
            result["health_after_clients"] = json.load(response)
        os.killpg(server.pid, signal.SIGTERM)
        server.wait(timeout=8)
        result["server_fixture"] = json.loads((output / "server-report.json").read_text())
        details = [next((case["details"] for case in data.get("checks", []) if case["name"] == "unique_shared_room_peers"), {}) for data in result["clients"].values()]
        result["checks"] = {
            "both_clients_passed": all(data.get("passed") and data["exit_code"] == 0 for data in result["clients"].values()),
            "mutual_identity_observation": len(details) == 2 and bool(details[0].get("identity")) and details[0].get("identity") != details[1].get("identity") and details[0].get("peer") == details[1].get("identity") and details[1].get("peer") == details[0].get("identity") and details[0].get("room") == details[1].get("room"),
            "transport_cleanup": result["health_after_clients"]["connected"] == 0,
            "two_native_transports_and_fault_fixtures": result["server_fixture"]["maximumClients"] == 2 and result["server_fixture"]["injectedClients"] == 2,
            "server_cleanup": result["server_fixture"]["roomsAfterClose"] == 0}
        if not reconnect:
            result["replay"] = {}
            for role in clients:
                recording = output / f"{role}-snapshots.jsonl"
                data = run_case(engine, project, "arena_interpolator_cases.gd", output / f"{role}-replay.json", [f"--replay={recording}"])
                data["recording_sha256"] = sha(recording)
                result["replay"][role] = data
            result["checks"]["both_recording_replays_passed"] = all(data["passed"] and data["exit_code"] == 0 and not data["script_error"] for data in result["replay"].values())
        result["passed"] = all(result["checks"].values())
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        for handle in handles:
            handle.close()
    return result


def negative_controls(engine: Path, project: Path, output: Path) -> dict:
    original = (project / "scripts/arena_interpolator.gd").read_text()
    start = original.index("func _set_pose(")
    end = original.index("func _reject_computation(")
    unsafe = "func _set_pose(actor: Dictionary, position: Vector3, yaw: float) -> bool:\n\tactor.x = position.x\n\tactor.y = position.y\n\tactor.z = position.z\n\tactor.yaw = wrapf(yaw, -PI, PI)\n\treturn true\n\n"
    variants = {
        "unbounded_projection": ("var projected_seconds := minf(lag, _extrapolation)", "var projected_seconds := lag", "extrapolation_is_bounded_then_held"),
        "long_yaw_arc": ("lerp_angle(float(actor.yaw), float(next.yaw), fraction)", "lerpf(float(actor.yaw), float(next.yaw), fraction)", "yaw_takes_shortest_arc"),
        "blended_teleport": ("if distance > _teleport_distance or distance / interval > _maximum_speed:", "if false:", "teleport_is_discrete"),
        "unbounded_yaw_input": ("if absf(float(actor.yaw)) > MAX_ABS_YAW: return false", "if false: return false", "literal_extreme_yaw_rejected_before_arithmetic"),
        "no_interval_epsilon": ("const MIN_INTERVAL_SECONDS := 0.000001", "const MIN_INTERVAL_SECONDS := 0.0", "literal_subnormal_interval_rejected_without_nan"),
        "nonfinite_output_commit": (original[start:end], unsafe, "computed_nonfinite_pose_is_atomic")}
    reports = {}
    for name, (old, new, expected) in variants.items():
        if original.count(old) != 1:
            raise RuntimeError(f"Negative-control target no longer unique: {name}")
        mutated = output / name
        shutil.copytree(project, mutated)
        (mutated / "scripts/arena_interpolator.gd").write_text(original.replace(old, new))
        data = run_case(engine, mutated, "arena_interpolator_cases.gd", output / f"{name}-report.json")
        failed = [case["name"] for case in data.get("checks", []) if not case["passed"]]
        reports[name] = {"detected": data["exit_code"] == 1 and not data["script_error"] and expected in failed,
                         "expected_failed_case": expected, "failed_cases": failed, "source_sha256": sha(mutated / "scripts/arena_interpolator.gd"), "replacement": {"from": old, "to": new}}
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, default=Path("/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64"))
    parser.add_argument("--output", type=Path, required=True, help="New output directory; existing evidence is never overwritten")
    args = parser.parse_args()
    native = Path(__file__).resolve().parents[1]
    repo = native.parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    project = output / "project"
    relative = ["scripts/arena_client.gd", "scripts/arena_interpolator.gd", "tests/arena_client_cases.gd", "tests/arena_interpolator_cases.gd"]
    source_paths = [*(native / path for path in relative), Path(__file__).resolve(), *(repo / path for path in ["games/yuga/server/server.ts", "games/yuga/server/clock.ts", "games/yuga/shared/types.ts", "games/yuga/shared/simulation.ts", "games/yuga/shared/map.ts", "games/yuga/shared/heroes.ts", "package-lock.json"])]
    before = {str(path.relative_to(repo)): sha(path) for path in source_paths}
    for path in relative:
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(native / path, project / path)
    (project / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Native network verification"\n[threading]\nworker_pool/max_threads=2\n')
    result: dict = {"passed": False, "source_sha256": before, "engine_sha256": sha(args.engine), "scope": "Fresh execution after workspace replacement. Actual two-client loopback authority, live headless actor sampling, recorded-data synthetic impairment and deliberately defective copies. Prior lost files are not used as evidence."}
    try:
        for script in ["arena_client_cases.gd", "arena_interpolator_cases.gd"]:
            run = subprocess.run([str(args.engine), "--headless", "--path", str(project), "--script", f"res://tests/{script}", "--check-only"], capture_output=True, text=True, timeout=15)
            (output / f"{script}.preflight.log").write_text(run.stdout + run.stderr)
            if run.returncode or "SCRIPT ERROR" in run.stdout + run.stderr:
                raise RuntimeError(f"Script compile failed: {script}")
        result["deterministic"] = run_case(args.engine, project, "arena_interpolator_cases.gd", output / "deterministic-report.json")
        result["transport"] = live_suite(repo, args.engine, project, output / "transport", True)
        result["interpolation"] = live_suite(repo, args.engine, project, output / "interpolation", False)
        result["negative_controls"] = negative_controls(args.engine, project, output)
        result["checks"] = {"deterministic_passed": result["deterministic"]["passed"] and result["deterministic"]["exit_code"] == 0,
                            "transport_passed": result["transport"]["passed"], "interpolation_and_replay_passed": result["interpolation"]["passed"],
                            "all_negative_controls_detected": all(data["detected"] for data in result["negative_controls"].values()),
                            "source_unchanged": before == {str(path.relative_to(repo)): sha(path) for path in source_paths}}
        result["passed"] = all(result["checks"].values())
    except Exception as error:
        result["failure"] = f"{type(error).__name__}: {error}"
    (output / "integration-report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "report": str(output / "integration-report.json"), "checks": result.get("checks"), "failure": result.get("failure")}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
