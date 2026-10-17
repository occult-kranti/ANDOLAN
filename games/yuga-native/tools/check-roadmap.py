#!/usr/bin/env python3
"""Check the production dependency ledger; this is not game/visual acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
DEFAULT = ROOT / "games/yuga-native/docs/ROADMAP_BACKLOG.json"
STATUSES = {"planned", "in_progress", "blocked", "complete"}


def validate(data, root):
    errors = []
    evidence_paths = set()

    def require(condition, message):
        if not condition:
            errors.append(message)

    def strings(value):
        return isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)

    require(isinstance(data, dict), "root must be an object")
    if not isinstance(data, dict):
        return errors, evidence_paths
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(set(data.get("status_values", [])) == STATUSES, "status_values must declare all four states")
    groups = {}
    ids = set()
    for key in ("milestones", "tasks"):
        records = data.get(key)
        require(isinstance(records, list) and len(records) > 0, f"{key} must be a nonempty list")
        index = {}
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict):
                errors.append(f"{key}: entry must be an object")
                continue
            ident = record.get("id")
            if not isinstance(ident, str) or not ident.strip():
                errors.append(f"{key}: missing id")
                continue
            require(ident not in ids, f"duplicate id: {ident}")
            ids.add(ident)
            index[ident] = record
            require(record.get("status") in STATUSES, f"{ident}: invalid status")
            for field in ("title", "owner"):
                require(isinstance(record.get(field), str) and bool(record[field].strip()), f"{ident}: missing {field}")
            deps = record.get("depends_on")
            require(strings(deps), f"{ident}: depends_on must be a list of IDs")
            if strings(deps):
                require(len(set(deps)) == len(deps), f"{ident}: duplicate dependency")
        groups[key] = index

    for kind, index in groups.items():
        for ident, record in index.items():
            for dep in record.get("depends_on", []) if strings(record.get("depends_on")) else []:
                require(dep in index, f"{ident}: unknown {kind} dependency {dep}")
                if record.get("status") == "complete" and dep in index:
                    require(index[dep].get("status") == "complete", f"{ident}: complete before dependency {dep}")
        visiting, visited = set(), set()

        def visit(ident, path):
            if ident in visiting:
                errors.append("dependency cycle: " + " -> ".join(path + [ident]))
                return
            if ident in visited or ident not in index:
                return
            visiting.add(ident)
            deps = index[ident].get("depends_on", [])
            for dep in deps if strings(deps) else []:
                visit(dep, path + [ident])
            visiting.remove(ident)
            visited.add(ident)

        for ident in index:
            visit(ident, [])

    for ident, task in groups["tasks"].items():
        require(task.get("milestone") in groups["milestones"], f"{ident}: unknown milestone")
        require(task.get("priority") in {"P0", "P1", "P2"}, f"{ident}: invalid priority")
        for field in ("deliverables", "acceptance"):
            require(strings(task.get(field)) and bool(task.get(field)), f"{ident}: missing {field}")
        require(isinstance(task.get("next_action"), str) and bool(task["next_action"].strip()), f"{ident}: missing next_action")
        evidence = task.get("evidence")
        require(isinstance(evidence, list), f"{ident}: evidence must be a list")
        if task.get("status") == "complete":
            require(bool(evidence), f"{ident}: complete without evidence")
        for item in evidence if isinstance(evidence, list) else []:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                errors.append(f"{ident}: invalid evidence entry")
                continue
            path = Path(item["path"])
            if task.get("status") == "complete":
                digest = item.get("sha256")
                require(isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), f"{ident}: complete evidence needs SHA-256: {path}")
            target = (root / path).resolve()
            inside = not path.is_absolute() and target.is_relative_to(root.resolve())
            require(inside, f"{ident}: evidence must stay inside repository: {path}")
            require(inside and target.is_file(), f"{ident}: evidence file missing: {path}")
            require(isinstance(item.get("scope"), str) and bool(item["scope"].strip()), f"{ident}: evidence needs scope")
            if inside and target.is_file():
                evidence_paths.add(str(path))
                if "sha256" in item:
                    require(hashlib.sha256(target.read_bytes()).hexdigest() == item["sha256"], f"{ident}: evidence hash mismatch: {path}")

    for ident, milestone in groups["milestones"].items():
        owned = {task_id for task_id, task in groups["tasks"].items() if task.get("milestone") == ident}
        declared = milestone.get("task_ids")
        require(strings(declared) and len(declared) > 0, f"{ident}: missing task_ids")
        require(strings(declared) and set(declared) == owned, f"{ident}: task_ids disagree with ownership")
        if strings(declared):
            require(len(declared) == len(set(declared)), f"{ident}: duplicate task_id")
        require(isinstance(milestone.get("completion_rule"), str) and bool(milestone["completion_rule"].strip()), f"{ident}: missing completion_rule")
        if milestone.get("status") == "complete":
            require(bool(owned) and all(groups["tasks"][x].get("status") == "complete" for x in owned), f"{ident}: complete before all tasks")

    packets = data.get("next_packets")
    require(strings(packets), "next_packets must be a list of task IDs")
    for ident in packets if strings(packets) else []:
        require(ident in groups["tasks"], f"next packet missing: {ident}")
        if ident in groups["tasks"]:
            require(groups["tasks"][ident].get("status") != "complete", f"next packet already complete: {ident}")
            task = groups["tasks"][ident]
            require(task.get("status") != "blocked", f"next packet blocked: {ident}")
            for dep in task.get("depends_on", []) if strings(task.get("depends_on")) else []:
                require(dep in groups["tasks"] and groups["tasks"][dep].get("status") == "complete", f"next packet {ident}: prerequisite {dep} incomplete")
    return errors, evidence_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", type=Path, default=DEFAULT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        raw = args.backlog.read_bytes()
        data = json.loads(raw)
        errors, evidence = validate(data, ROOT)
    except (OSError, ValueError, TypeError) as exc:
        raw, data, evidence = b"", {}, set()
        errors = [str(exc)]
    report = {
        "passed": not errors,
        "scope": "Dependency structure, status consistency and evidence file existence/hash only; not content, visual or game acceptance",
        "backlog_sha256": hashlib.sha256(raw).hexdigest(),
        "milestones": len(data.get("milestones", [])) if isinstance(data, dict) else 0,
        "tasks": len(data.get("tasks", [])) if isinstance(data, dict) else 0,
        "evidence_files": len(evidence),
        "errors": errors,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
