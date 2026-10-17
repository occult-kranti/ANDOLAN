"""Hash-check unmodified vendored MikkTSpace and build an offline authoring ABI."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent
UPSTREAM="3e895b49d05ea07e4c2133156cfa94369e19e409"
PINS={"mikktspace.h":"17fc433894f24c73753d548086cc4d8c5c0379f4a6edfb98b5da243e4f0bc3d0",
      "mikktspace.c":"de87e74107df766ce68108801262bd8d53899414236b59810509a8fc2a51e288",
      "README.md":"295d4e37ac1980e1f811c340f618ffa68fc10bf906b34bc93a64c6960351bdfc"}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def build(output: Path,compiler: str="cc") -> dict:
    output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    for name,expected in PINS.items():
        path=ROOT/"vendor"/name
        if sha(path)!=expected:raise ValueError("Unmodified upstream source hash mismatch: "+name)
    binary=output/"libyuga_mikktspace.so"
    if binary.exists() or (output/"build.json").exists():raise ValueError("Choose a fresh build directory")
    executable=shutil.which(compiler)
    if not executable:raise ValueError("C99 compiler required")
    command=[executable,"-std=c99","-O2","-g","-fPIC","-shared","-Wl,--build-id=sha1","-I",str(ROOT/"vendor"),str(ROOT/"bridge.c"),str(ROOT/"vendor/mikktspace.c"),"-lm","-o",str(binary)]
    subprocess.run(command,check=True,capture_output=True,text=True)
    report={"schema":1,"upstreamRepository":"https://github.com/mmikk/MikkTSpace","upstreamCommit":UPSTREAM,
      "license":"Unmodified upstream zlib-style permissive notices retained in both C/header; original YUGA bridge CC0-1.0",
      "upstreamFiles":PINS,"adapter":str(ROOT/"bridge.c"),"adapterSha256":sha(ROOT/"bridge.c"),
      "builderSha256":sha(Path(__file__)),"compiler":subprocess.check_output([executable,"--version"],text=True).splitlines()[0],
      "command":command,"binary":str(binary),"binarySha256":sha(binary),"exportedBridge":"yuga_mikk_generate",
      "symbolVisibility":"Default ELF symbols, unstripped debug info; source/native analysis only, no game runtime dependency",
      "scope":"Offline per-corner authoring tool. Successful compilation does not establish tangent correctness or art acceptance."}
    (output/"build.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path);parser.add_argument("--compiler",default="cc")
    args=parser.parse_args();print(json.dumps(build(args.output,args.compiler),indent=2))
