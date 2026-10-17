#!/usr/bin/env python3
"""Run bounded actual-world LOD comparisons on one owned render display.

This is a renderer owner, not a synthetic image generator or performance test.
Use only after root grants the heavy slot. --dry-run starts no processes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

PROJECT = Path(__file__).resolve().parents[2]
SIZE = (1280,960)
HERO_IMPORTS = ["res://assets/heroes/rama-hero.glb", "res://assets/heroes/rama-hero-mid.glb", "res://assets/heroes/rama-hero-far.glb"]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def local(project: Path, resource: str) -> Path:
    if not resource.startswith("res://"):
        raise ValueError("Expected pinned res:// path")
    path = (project/resource.removeprefix("res://")).resolve()
    if not path.is_relative_to(project):
        raise ValueError("Resource escapes project")
    return path

def validate(report: dict, output: Path, project: Path, pairs_only: bool) -> None:
    if not report.get("complete") or report.get("failure") or report.get("kind") != "actual-rama-lod-comparison":
        raise ValueError("LOD capture failed: "+str(report.get("failure")))
    if report.get("renderer") != "forward_plus" or str(report.get("display", "")).lower() != "x11":
        raise ValueError("Actual Forward+ X11 capture required")
    if (report.get("width"),report.get("height")) != SIZE or report.get("fps") != 15 or bool(report.get("pairs_only")) != pairs_only:
        raise ValueError("Unexpected capture dimensions/mode")
    if not report.get("source_unchanged") or report["source_sha256"] != report["source_after_sha256"]:
        raise ValueError("Runtime source changed during take")
    for path, sha in report["source_sha256"].items():
        if digest(local(project,path)) != sha:
            raise ValueError("Pinned source changed: "+path)
    for path, entry in report["imports"].items():
        if not entry["fresh"] or digest(local(project,path)) != entry["source_sha256"]:
            raise ValueError("Stale source import: "+path)
        for key, sha_key in [("metadata","metadata_sha256"),("imported","sha256"),("stamp","stamp_sha256")]:
            if digest(local(project,entry[key])) != entry[sha_key]:
                raise ValueError("Imported data changed: "+entry[key])
    for path in HERO_IMPORTS:
        if path not in report["imports"] or report["imports"][path]["generate_lods"]:
            raise ValueError("All three authored candidates need fresh import with generated LOD disabled")
    for path, sha in report.get("material_texture_pins",{}).items():
        if digest(local(project,path)) != sha:
            raise ValueError("Material texture resource changed")
    from PIL import Image
    def verify_image(shot: dict) -> None:
        filename = Path(shot["file"])
        if filename.name != str(filename) or filename.suffix != ".png":
            raise ValueError("Unsafe framebuffer name")
        path = output/filename
        if digest(path) != shot["sha256"]:
            raise ValueError("Framebuffer hash changed")
        with Image.open(path) as image:
            if image.size != SIZE: raise ValueError("Framebuffer dimensions differ")
            image.verify()
        state = shot["lod"]
        if (state["live_rigs"],state["live_bones"],state["levels"],state["owned_mesh_instances"],state["owned_skins"]) != (1,164,3,4,2) or state["errors"]:
            raise ValueError("One-rig LOD ownership invariant failed")
        if state["visible_levels"] != [state["level"]] or not shot["tree_paused"]:
            raise ValueError("Frozen comparison shows wrong mesh levels")
    poses = report.get("poses",[])
    if [pose["id"] for pose in poses] != ["idle","draw"]:
        raise ValueError("Exact idle and actual draw poses required")
    for pose in poses:
        state = pose["state"]
        if state["live_rigs"] != 1 or len(state["bones"]) != 164 or state["face_meshes"] != 1 or state["hero_time_shaders"]:
            raise ValueError("Native face/rig or hero clock invariant failed")
        if not state["controllers"]["motion"]["finite"] or not state["controllers"]["secondary"]["finite"]:
            raise ValueError("Nonfinite frozen controller")
    if not poses[1]["actual_cast"].get("accepted") or poses[1]["state"]["controllers"]["motion"]["stage"] not in ("windup","hold"):
        raise ValueError("Draw must come from actual accepted runtime windup")
    expected = [(pose,pixels,level) for pose in ("idle","draw") for level,pixels in enumerate((780,350,120))]
    if len(report.get("pairs",[])) != len(expected):
        raise ValueError("Six exact matched LOD pairs required")
    previous = -1
    for pair,(pose,pixels,level) in zip(report["pairs"],expected):
        if (pair["pose"],pair["target_hero_pixels"],pair["selected_level"]) != (pose,pixels,level) or not pair["same_camera"] or not pair["same_frozen_state"]:
            raise ValueError("Unexpected matched pair contract")
        a,b = pair["reference"],pair["candidate"]
        if a["camera"] != b["camera"] or a["state_sha256"] != b["state_sha256"] or a["state_sha256"] != next(p["state_sha256"] for p in poses if p["id"] == pose):
            raise ValueError("Pair changed camera/pose/morph/material/controller state")
        if a["lod"]["level"] != 0 or b["lod"]["level"] != level:
            raise ValueError("Wrong reference/selected geometry")
        for shot in (a,b):
            verify_image(shot)
            if shot["render_frame"] <= previous:
                raise ValueError("Frame chronology not increasing")
            previous = shot["render_frame"]
    frames = report.get("frames",[])
    if len(frames) != (0 if pairs_only else 30):
        raise ValueError("Expected bounded30-frame camera take")
    levels = []
    for index, frame in enumerate(frames):
        shot=frame["image"]
        if frame["index"] != index or abs(frame["sample_time_s"]-index/15) > 1e-7 or shot["state_sha256"] != poses[1]["state_sha256"]:
            raise ValueError("Camera take changed frozen draw or frame chronology")
        if index > 0 and (frame["physics_tick_delta"] != 4 or frame["render_frame_delta"] <= 0):
            raise ValueError("Camera take skipped a fixed15Hz sample")
        verify_image(shot)
        if shot["render_frame"] <= previous:
            raise ValueError("Camera frames must render consecutively in order")
        previous=shot["render_frame"]
        levels.append(shot["lod"]["level"])
    if frames and (levels[0] != 0 or levels[-1] != 0 or set(levels) != {0,1,2}):
        raise ValueError("Camera take must show near→mid→far→mid→near selection")

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--project",type=Path,default=PROJECT)
    parser.add_argument("--runtime",type=Path,default=Path("/workspace/tooling/native-render/runtime"))
    parser.add_argument("--godot",default=shutil.which("godot"))
    parser.add_argument("--display",type=int,default=143)
    parser.add_argument("--shader-cache-seed",type=Path)
    parser.add_argument("--pairs-only",action="store_true")
    parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args()
    if not args.output.is_absolute(): parser.error("Output must be absolute")
    project=args.project.resolve();output=args.output.resolve();runtime=args.runtime.resolve()
    user=output.with_name(output.name+"-user")
    log_path=output.with_name(output.name+".godot.log")
    xlog_path=output.with_name(output.name+".xvfb.log")
    if any(p.exists() for p in (output,user,log_path,xlog_path)) or not 90<=args.display<=199 or Path(f"/tmp/.X11-unix/X{args.display}").exists():
        parser.error("Choose a fresh output and unused display90–199")
    command=[args.godot,"--path",str(project),"--display-driver","x11","--rendering-method","forward_plus","--audio-driver","Dummy","--disable-vsync","--fixed-fps","15","--max-threads","2","--script","res://art/hero-rama-lod/capture_lods.gd","--","--output="+str(output)]
    if args.pairs_only: command.append("--pairs-only")
    if args.dry_run:
        print(json.dumps({"starts_renderer":False,"command":command,"expected_pairs":6,"expected_camera_frames":0 if args.pairs_only else 30},indent=2));return
    xvfb=runtime/"usr/bin/Xvfb";icd=runtime/"usr/share/vulkan/icd.d/lvp_icd.json"
    if not args.godot or not xvfb.is_file() or not icd.is_file():parser.error("Prepared Godot/render runtime required")
    ffmpeg=shutil.which("ffmpeg");ffprobe=shutil.which("ffprobe")
    if not args.pairs_only and (not ffmpeg or not ffprobe):parser.error("FFmpeg and ffprobe required for camera take")
    output.parent.mkdir(parents=True,exist_ok=True);user.mkdir()
    env=os.environ.copy()
    env.update(DISPLAY=f":{args.display}",LP_NUM_THREADS="2",VK_ICD_FILENAMES=str(icd),LD_LIBRARY_PATH=str(runtime/"usr/lib/x86_64-linux-gnu")+(":"+env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else ""))
    for key,name in [("XDG_DATA_HOME","data"),("XDG_CONFIG_HOME","config"),("XDG_CACHE_HOME","cache")]:
        p=user/name;p.mkdir();env[key]=str(p)
    env["MESA_SHADER_CACHE_DIR"]=str(user/"cache/mesa")
    cache=None
    if args.shader_cache_seed:
        if not args.shader_cache_seed.is_dir():parser.error("Shader cache seed must be an existing directory")
        shutil.copytree(args.shader_cache_seed,env["MESA_SHADER_CACHE_DIR"])
        cache={"path":str(args.shader_cache_seed),"scope":"Driver cache speed only; not image/quality acceptance"}
    with log_path.open("x") as log,xlog_path.open("x") as xlog:
        server=subprocess.Popen([str(xvfb),env["DISPLAY"],"-screen","0",f"{SIZE[0]}x{SIZE[1]}x24","-nolisten","tcp","-extension","MIT-SHM","-ac"],env=env,stdout=xlog,stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if server.poll() is not None:raise RuntimeError("Owned display stopped")
                if Path(f"/tmp/.X11-unix/X{args.display}").exists():break
                time.sleep(.1)
            else:raise RuntimeError("Owned display did not start")
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1100)
        finally:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait()
    text=log_path.read_text()
    if result.returncode or "SCRIPT ERROR:" in text or "\nERROR:" in text:
        raise RuntimeError("Actual capture failed; preserve "+str(log_path))
    report_path=output/"lod-capture.json"
    report=json.loads(report_path.read_text());validate(report,output,project,args.pairs_only)
    snapshots=output/"source";snapshots.mkdir()
    for resource,sha in report["source_sha256"].items():
        path=local(project,resource)
        if path.suffix in (".gd",".gdshader",".gdshaderinc",".py",".tres",".tscn",".json",".godot",".import"):
            target=snapshots/path.relative_to(project);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    video=None
    if not args.pairs_only:
        video=output/"rama-lod-camera.mp4"
        subprocess.run([ffmpeg,"-hide_banner","-loglevel","error","-nostdin","-n","-framerate","15","-i",str(output/"frame-%05d.png"),"-an","-c:v","libx264","-threads","2","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(video)],check=True,timeout=180)
        probe=json.loads(subprocess.check_output([ffprobe,"-v","error","-count_frames","-show_streams","-show_format","-of","json",str(video)],timeout=30))
        if len(probe["streams"])!=1 or int(probe["streams"][0]["nb_read_frames"])!=30:raise ValueError("Camera video frame count mismatch")
        subprocess.run([ffmpeg,"-hide_banner","-loglevel","error","-xerror","-nostdin","-i",str(video),"-f","null","-"],check=True,timeout=60)
        (output/"camera-video.json").write_text(json.dumps({"complete":True,"file":video.name,"sha256":digest(video),"probe":probe,"scope":"Actual camera movement around frozen real windup pose;15Hz capture is not achieved frame rate or advancing gameplay."},indent=2)+"\n")
    receipt={"complete":True,"command":command,"runner_sha256":digest(Path(__file__)),"report_sha256":digest(report_path),"log_sha256":digest(log_path),"pairs":6,"camera_frames":len(report["frames"]),"video_sha256":digest(video) if video else None,"shader_cache_seed":cache,"scope":"Source/import/state-bound actual one-rig native LOD appearance; image review and physicalGPU acceptance remain independent."}
    (output/"capture-run.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"complete":True,"output":str(output),"pairs":6,"camera_frames":len(report["frames"]),"video":str(video) if video else None}))

if __name__ == "__main__":main()
