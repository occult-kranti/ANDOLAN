"""Measure one GLB without importing/rebuilding it or touching runtime assets."""
import argparse
import json
from pathlib import Path
from glb_lod import GLB, validate_pair

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--report", required=True, type=Path)
    args = ap.parse_args()
    source = GLB(args.source)
    report = {"measurement": source.measure(), "structuralSelfCheck": validate_pair(source, source)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report["measurement"].items() if k not in ("primitives", "textures")}, indent=2))

if __name__ == "__main__": main()
