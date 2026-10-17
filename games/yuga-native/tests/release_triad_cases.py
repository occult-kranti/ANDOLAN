#!/usr/bin/env python3
"""Synthetic Triad publication counterexamples; no render, network or Git writes.

Fixtures describe a single hero reaching a neutral Lotus relay after 7.5 seconds,
then capturing it and receiving one three-arrow supply during the six-second take.
They are deliberately not recorded gameplay. Actual media decoding is a separate gate.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import struct
import subprocess
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve()
PROJECT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("triad_siege_fixture", HERE.with_name("release_siege_cases.py"))
siege = importlib.util.module_from_spec(spec)
spec.loader.exec_module(siege)
base, release = siege.base, siege.release
write = base.write
TAG = "yuga-traversal-armies-review-fixture-triad-siege"
SIGNATURE = {"width":1280,"height":720,"frames":180,"fps":30,"duration_seconds":6.0}
CHECKS = []


def session_snapshot(steps):
    owned, supplied = steps >= 80, steps >= 130
    sites = [{"id":i,"label":label,"position":[(i-1)*40,0,0],"radius":5.0,
              "owner":"sun" if i == 1 and owned else "neutral", "contested":False,
              "progress":min(8.0,steps*.1) if i == 1 else 0.0,
              "supply_clock":((steps-80) % 50)*.1 if i == 1 and owned else 0.0}
             for i,label in enumerate(("Reed Relay","Lotus Relay","Sky Relay"))]
    return {"rules":{"epoch":2,"steps":steps,"elapsed":steps*.1,"last_support_id":int(supplied),"sites":sites},
            "arrows_total":3 if supplied else 0}


def fixture(path):
    repo, project, film, args, siege_capture, _ = siege.fixture(path)
    args.tag = TAG
    for name in ("scripts/relay_control.gd","scripts/relay_session.gd","scripts/relay_art.gd",
                 "tools/capture-triad.gd","tools/run-triad-capture.py"):
        write(project/name,"Synthetic Triad fixture source: "+name)
    paths = set(release.CAPTURE_FIXED_SOURCES)
    for folder in ("scripts","scenes","assets"):
        paths.update(p.relative_to(project).as_posix() for p in (project/folder).rglob("*") if p.is_file())
    exported = {"git":{"head":base.COMMIT},"source":{"files":{name:release.record(project/name) for name in paths
                if name == "project.godot" or name.split("/")[0] in ("scripts","scenes","assets")}}}
    write(args.build/"native-export-manifest.json",exported)
    base.mutate_capture(project/release.TRAVERSAL_CAPTURE_DIRECTORY,
                        lambda r:r.update(source_sha256={"res://"+name:release.digest(project/name) for name in paths}))
    siege.render_mutation(siege_capture,lambda r:r.update(source_sha256={"res://"+name:release.digest(project/name)
                          for name in paths | {"tools/capture-siege.gd","tools/run-siege-capture.py"}}))
    capture = project/release.TRIAD_CAPTURE_DIRECTORY
    capture.mkdir(parents=True)

    def image(name, retained=None):
        # Minimal synthetic IHDR; no PNG decoding or visual acceptance is claimed.
        data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"+struct.pack(">II",1280,720)+name.encode()
        if retained: (capture/retained).write_bytes(data)
        return {"file":name,"sha256":hashlib.sha256(data).hexdigest(),"width":1280,"height":720,
                "draw_calls":23,"rendered_objects":42,"rendered_primitives":987}

    frames = []
    for index in range(180):
        steps = 75+(index+1)//3
        snapshot = session_snapshot(steps)
        retained = f"triad-frame-{index:05d}.png" if index in (15,90,175) else None
        frames.append({"index":index,"physics_tick":1000+2*(index+1),"physics_tick_delta":2,
                       "render_frame":300+index,"finite":True,"image":image(f"frame-{index:05d}.png",retained),
                       "relays":snapshot,"ammo":3+snapshot["arrows_total"]})
    imports = json.loads((siege_capture/"siege-render-review.json").read_text())["imports"]
    render = {"schema":1,"complete":True,"failure":"","renderer":"forward_plus","display":"X11",
              "fps":30,"physics_hz":60,"time_scale":1.0,"width":1280,"height":720,
              "take_start_tick":1000,"take_physics_ticks":360,"frames":frames,
              "before":session_snapshot(75),"after":session_snapshot(135),
              "outcomes":{"captured":True,"supplied":True,"finite":True},"imports":imports,
              "source_sha256":{"res://"+name:release.digest(project/name) for name in paths | release.TRIAD_FIXED_SOURCES},
              "stills":[{"image":image(name,name),"scope":"Synthetic separate frozen view"} for name in sorted(release.TRIAD_STILLS)]}
    write(capture/"triad-render-review.json",render)
    write(capture/"TRIAD-RENDER-REVIEW.md","Synthetic review fixture; no real visual review claim.\n")
    write(capture/"yuga-triad-preview.mp4","Synthetic Triad movie bytes; external decoder mocked in these tests.")
    write(capture/"triad-video.json",{"complete":True,"file":"yuga-triad-preview.mp4",
          **release.record(capture/"yuga-triad-preview.mp4"),"capture_report_sha256":release.digest(capture/"triad-render-review.json"),
          "probe":{"streams":[{"codec_type":"video","codec_name":"h264","width":1280,"height":720,
                                 "nb_read_frames":"180","avg_frame_rate":"30/1"}],"format":{"duration":"6.000000"}}})
    return repo, project, film, args, capture, exported


def mutate_render(capture, change):
    path = capture/"triad-render-review.json"
    report = json.loads(path.read_text())
    change(report)
    write(path,report)
    mutate_video(capture,lambda video:video.update(capture_report_sha256=release.digest(path)))


def mutate_video(capture, change):
    path = capture/"triad-video.json"
    video = json.loads(path.read_text())
    change(video)
    write(path,video)


def record(name, expected, error, **evidence):
    CHECKS.append({"case":name,"passed":(error is None) == expected,"expected_success":expected,
                   "rejection":error,"evidence":evidence})


def direct_case(name, mutation=None, expected=False, decode=False, decoder_failure=False):
    with tempfile.TemporaryDirectory(prefix="yuga-triad-release-case-") as temporary:
        _, project, _, _, capture, exported = fixture(Path(temporary))
        if mutation: mutation(capture,project,exported)
        error = None
        with patch.object(release,"PROJECT",project), patch.object(release,"probe_traversal_movie",return_value=SIGNATURE,
             side_effect=ValueError("Synthetic decoder rejects bytes") if decoder_failure else None) as decoder:
            try: release.validate_triad_capture(capture,exported,decode=decode)
            except (ValueError,KeyError,TypeError,OSError,IndexError) as caught: error = str(caught)
        record(name,expected,error,decoder_calls=decoder.call_count)
        if expected and decode and decoder.call_count != 1: CHECKS[-1]["passed"] = False


def staged_case(name, mutation=None, expected=False, resealed_mutation=None, git_failure=None):
    with tempfile.TemporaryDirectory(prefix="yuga-triad-staging-case-") as temporary:
        repo, project, film, args, capture, _ = fixture(Path(temporary))
        if mutation: mutation(capture,project,args)
        observed_git = []
        def fake_git(*arguments):
            observed_git.append(arguments)
            if git_failure:
                value = git_failure(arguments)
                if value is not None: return value
            return base.COMMIT if arguments[0] == "rev-parse" else ""
        error = None
        with patch.object(release,"REPO",repo), patch.object(release,"PROJECT",project), patch.object(release,"FILM",film), \
             patch.object(release,"git",side_effect=fake_git), patch.object(release,"validate_evidence",return_value={"passed":True}), \
             patch.object(release,"probe_traversal_movie",return_value=SIGNATURE) as decoder:
            try:
                release.stage(args)
                if resealed_mutation:
                    resealed_mutation(args.output)
                    base.update_inventory(args.output)
                    release.verify(args.output,TAG,base.COMMIT)
            except (ValueError,KeyError,TypeError,OSError,IndexError,subprocess.CalledProcessError) as caught: error = str(caught)
        record(name,expected,error,decoder_calls=decoder.call_count)
        if expected and error is None:
            tracked = [row for row in observed_git if row[0] == "ls-files" and any(release.TRIAD_CAPTURE_DIRECTORY in value for value in row)]
            exact = {str((capture/name).relative_to(repo)) for name in release.TRIAD_CAPTURE_ASSETS}
            exact |= {str((project/name).relative_to(repo)) for name in release.TRIAD_FIXED_SOURCES | release.TRIAD_REQUIRED_RUNTIME}
            CHECKS[-1]["passed"] = decoder.call_count == 3 and bool(tracked) and exact <= set(tracked[-1])
            CHECKS[-1]["evidence"].update(three_movies_decoded=decoder.call_count==3,triad_archive_and_sources_checked_as_tracked=bool(tracked) and exact<=set(tracked[-1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report",type=Path)
    args = parser.parse_args()
    source_before = release.record(PROJECT/"tools/release-native.py")
    record("tag selection requires exact bounded Triad suffix",True,None if release.triad_release(TAG) and
           not any(release.triad_release(tag) for tag in ("yuga-confluence-duel-x-triad-siege","yuga-traversal-armies-x-siege",
                    "yuga-traversal-armies-x-triad-siege-other","yuga-traversal-armies-x-triad-siege\n")) else "Incorrect tag selection")
    direct_case("valid continuous capture control",expected=True)
    direct_case("valid fresh decoder control",expected=True,decode=True)
    direct_case("fresh decoder rejection blocks capture",decode=True,decoder_failure=True)
    staged_case("valid Triad stage and verification binds all three movies and sources",expected=True)
    mutations = {
        "incomplete capture":lambda r:r.update(complete=False),
        "preview capture":lambda r:r.update(preview=True),
        "reported capture failure":lambda r:r.update(failure="Failed during take"),
        "headless display":lambda r:r.update(display="headless"),
        "wrong renderer":lambda r:r.update(renderer="gl_compatibility"),
        "zero timescale":lambda r:r.update(time_scale=0),
        "boolean timescale":lambda r:r.update(time_scale=True),
        "nonfinite timescale":lambda r:r.update(time_scale=float("nan")),
        "wrong dimensions":lambda r:r.update(width=960),
        "missing frame":lambda r:r["frames"].pop(),
        "wrong total ticks":lambda r:r.update(take_physics_ticks=359),
        "negative start tick":lambda r:r.update(take_start_tick=-1),
        "physics sequence gap":lambda r:r["frames"][40].update(physics_tick=9999),
        "one physics tick per frame":lambda r:r["frames"][40].update(physics_tick_delta=1),
        "nonadvancing render counter":lambda r:r["frames"][40].update(render_frame=1),
        "nonfinite frame flag":lambda r:r["frames"][40].update(finite=False),
        "numeric finite flag":lambda r:r["frames"][40].update(finite=1),
        "unsafe frame image name":lambda r:r["frames"][40]["image"].update(file="../frame.png"),
        "missing image hash":lambda r:r["frames"][40]["image"].pop("sha256"),
        "no actual draw calls":lambda r:r["frames"][40]["image"].update(draw_calls=0),
        "capture outcome absent":lambda r:r["outcomes"].update(captured=False),
        "numeric supply outcome":lambda r:r["outcomes"].update(supplied=1),
        "already owned before take":lambda r:r["before"]["rules"]["sites"][1].update(owner="sun"),
        "already supplied before take":lambda r:r["before"].update(arrows_total=3),
        "outcome flag cannot substitute for actual ownership":lambda r:r["after"]["rules"]["sites"][1].update(owner="moon"),
        "outcome flag cannot substitute for applied arrows":lambda r:r["after"].update(arrows_total=0),
        "rule reset during take":lambda r:r["frames"][40]["relays"]["rules"].update(epoch=3),
        "rule clock discontinuity":lambda r:r["frames"][40]["relays"]["rules"].update(elapsed=999),
        "capture progress nonfinite":lambda r:r["frames"][40]["relays"]["rules"]["sites"][1].update(progress=float("nan")),
        "capture progress out of bounds":lambda r:r["frames"][40]["relays"]["rules"]["sites"][1].update(progress=9),
        "unbounded supply clock":lambda r:r["frames"][40]["relays"]["rules"]["sites"][1].update(supply_clock=5),
        "missing relay site":lambda r:r["frames"][40]["relays"]["rules"]["sites"].pop(),
        "wrong relay position":lambda r:r["frames"][40]["relays"]["rules"]["sites"][1].update(position=[1,0,0]),
        "boolean relay position":lambda r:r["frames"][40]["relays"]["rules"]["sites"][1].update(position=[False,False,False]),
        "wrong relay label":lambda r:r["frames"][40]["relays"]["rules"]["sites"][1].update(label="Other"),
        "owner contradicts signed progress":lambda r:r["frames"][40]["relays"]["rules"]["sites"][1].update(owner="moon"),
        "supply receipt counter regresses":lambda r:r["frames"][170]["relays"]["rules"].update(last_support_id=0),
        "unbounded per-frame receipt jump":lambda r:r["frames"][170]["relays"]["rules"].update(last_support_id=100),
        "applied arrows regress":lambda r:r["frames"][170]["relays"].update(arrows_total=0),
        "negative ammo":lambda r:r["frames"][40].update(ammo=-1),
        "floating ammo":lambda r:r["frames"][40].update(ammo=3.0),
        "ammo differs from applied supply":lambda r:r["frames"][170].update(ammo=9),
        "ending snapshot does not match last frame":lambda r:r["after"]["rules"].update(last_support_id=2),
        "missing still":lambda r:r["stills"].pop(),
        "duplicate still name":lambda r:r["stills"].__setitem__(1,copy.deepcopy(r["stills"][0])),
        "missing source inventory":lambda r:r.update(source_sha256={}),
        "wrong captured source hash":lambda r:r["source_sha256"].update({"res://scripts/relay_control.gd":"0"*64}),
        "unsafe source path":lambda r:r["source_sha256"].update({"res://../outside":"0"*64}),
        "missing import proof":lambda r:r.update(imports={}),
        "stale imported hero":lambda r:r["imports"]["res://assets/heroes/rama-production.glb"].update(fresh=False),
        "unsafe imported path":lambda r:r["imports"]["res://assets/heroes/rama-production.glb"].update(imported="res://../outside.scn"),
        "invalid import hash":lambda r:r["imports"]["res://assets/heroes/rama-production.glb"].update(sha256="invalid"),
    }
    for name, change in mutations.items():
        direct_case(name,lambda c,p,e,change=change:mutate_render(c,change))
    for name in sorted(release.TRIAD_CAPTURE_ASSETS):
        direct_case("required capture file: "+name,lambda c,p,e,name=name:(c/name).unlink())
        staged_case("self-consistent release cannot omit "+name,resealed_mutation=lambda d,name=name:(d/name).unlink())
    for gate in ("relay-control","relay-art","relay-integration","triad-release-gates"):
        staged_case("failed stage check: "+gate,mutation=lambda c,p,a,gate=gate:write(a.checks/(gate+".json"),{"passed":False}))
        staged_case("published check cannot be removed: "+gate,resealed_mutation=lambda d,gate=gate:(d/("ci-"+gate+".json")).unlink())
    direct_case("retained frame substitution",lambda c,p,e:write(c/"triad-frame-00015.png","replacement"))
    direct_case("retained still substitution",lambda c,p,e:write(c/"still-lotus-night.png","replacement"))
    direct_case("changed actual relay source",lambda c,p,e:write(p/"scripts/relay_control.gd","changed after capture"))
    direct_case("changed capture helper source",lambda c,p,e:write(p/"tools/capture-triad.gd","changed after capture"))
    direct_case("missing required relay runtime",lambda c,p,e:(p/"scripts/relay_art.gd").unlink())
    direct_case("exported source hash differs",lambda c,p,e:e["source"]["files"]["scripts/relay_control.gd"].update(sha256="0"*64))
    direct_case("export omits relay runtime",lambda c,p,e:e["source"]["files"].pop("scripts/relay_session.gd"))
    direct_case("export adds unrecorded runtime",lambda c,p,e:e["source"]["files"].update({"scripts/extra.gd":{"sha256":"0"*64,"bytes":1}}))
    direct_case("movie bytes changed",lambda c,p,e:write(c/"yuga-triad-preview.mp4","substitute"))
    direct_case("movie report links other capture",lambda c,p,e:mutate_video(c,lambda v:v.update(capture_report_sha256="0"*64)))
    for field,value in (("nb_read_frames","179"),("width",960),("avg_frame_rate","24/1"),("codec_name","vp9")):
        direct_case("decoded metadata rejects "+field,lambda c,p,e,field=field,value=value:mutate_video(c,lambda v:v["probe"]["streams"][0].update({field:value})))
    direct_case("nonfinite movie duration",lambda c,p,e:mutate_video(c,lambda v:v["probe"]["format"].update(duration="nan")))
    def untracked(arguments):
        if arguments[0] == "ls-files" and any(release.TRIAD_CAPTURE_DIRECTORY in value for value in arguments):
            raise subprocess.CalledProcessError(1,["git",*arguments])
    staged_case("untracked Triad archive blocks staging",git_failure=untracked)
    staged_case("changed committed Triad archive blocks staging",git_failure=lambda a:"changed archive" if a[0]=="diff" and any(release.TRIAD_CAPTURE_DIRECTORY in value for value in a) else None)
    staged_case("wrong tag commit blocks staging",git_failure=lambda a:"b"*40 if a[0]=="rev-parse" and a[1].startswith("refs/tags/") else None)
    record("validator source remains unchanged throughout fixtures",True,None if release.record(PROJECT/"tools/release-native.py")==source_before else "Source changed during run")
    report = {"passed":all(row["passed"] for row in CHECKS),"checks":CHECKS,
              "source_sha256":{str(path.relative_to(PROJECT)):release.digest(path) for path in
                               (HERE,PROJECT/"tools/release-native.py",HERE.with_name("release_siege_cases.py"),HERE.with_name("release_traversal_cases.py"))},
              "scope":"Synthetic bounded fixtures exercise source/archive/export, checksums, playback evidence and staged-publication rejection. Decoder and Git queries mocked; no network, actual render, package, Git mutation or real release claim."}
    if args.report: write(args.report,report)
    print(json.dumps({"passed":report["passed"],"checks":len(CHECKS),"failures":[row for row in CHECKS if not row["passed"]]},indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
