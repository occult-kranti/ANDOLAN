"""Diagnose actual GLB Mikk corner domains; write tangent-only candidates iff safe.

Input geometry, skin, native facial partition, morphs and JSON never change.
Unresolved/ambiguous corners reject candidate writing instead of being averaged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import numpy as np
from build_bridge import ROOT, sha
from mikk_frames import NativeMikk, diagnose, MAX_VERTICES, MAX_CORNERS

sys.path.insert(0,str(ROOT.parent/"hero-rama-lod"))
from glb_lod import GLB

def safe_outputs(source: Path,*outputs) -> None:
    source=source.resolve();seen=[]
    for value in outputs:
        if value is None:continue
        p=Path(value).resolve()
        if p==source or (p.exists() and os.path.samefile(p,source)):
            raise ValueError("Output aliases the source GLB; input must remain immutable")
        if p in seen:raise ValueError("Output paths alias each other")
        if p.exists():raise ValueError("Use fresh report/candidate/corner paths")
        seen.append(p)

def analyze_asset(native: NativeMikk,source_path: Path,report_path: Path,candidate_path: Path|None=None,corners_path: Path|None=None) -> dict:
    safe_outputs(source_path,report_path,candidate_path,corners_path)
    source=GLB(source_path)
    before=sha(source_path)
    json_length=struct.unpack_from("<I",source.raw,12)[0]
    binary_start=20+json_length+8
    patches={};domains=[];blocks=[];corner_archive={};processed=0
    for mi,pi,p in source.primitives():
        attrs=p["attributes"];material=source.doc["materials"][p["material"]]
        name=f"mesh{mi}-primitive{pi}"
        row={"mesh":mi,"primitive":pi,"material":material.get("name"),"meshName":source.doc["meshes"][mi].get("name"),"status":"diagnosed"}
        if p.get("mode",4)!=4 or not {"POSITION","NORMAL","TEXCOORD_0","TANGENT"}<=set(attrs):
            row["status"]="unsupported or missing source triangle/attribute domain"
            if "normalTexture" in material:blocks.append(name+": normal map lacks supported tangent domain")
            domains.append(row);continue
        try:
            # Check counts before expanding any sparse/zero-initialized accessor.
            for semantic in ("POSITION","NORMAL","TEXCOORD_0","TANGENT"):
                ai=attrs[semantic]
                if type(ai) is not int or not 0<=ai<len(source.doc["accessors"]):raise ValueError("Invalid source accessor index")
                count=source.doc["accessors"][ai]["count"]
                if type(count) is not int or not 0<count<=MAX_VERTICES:raise ValueError("Source vertex accessor exceeds bounded capacity")
            ii=p["indices"]
            if type(ii) is not int or not 0<=ii<len(source.doc["accessors"]):raise ValueError("Invalid source index accessor")
            count=source.doc["accessors"][ii]["count"]
            if type(count) is not int or not 0<count<=MAX_CORNERS or count%3:raise ValueError("Source corner accessor exceeds bounded complete triangles")
            pos=source.array(attrs["POSITION"],True);n=source.array(attrs["NORMAL"],True);uv=source.array(attrs["TEXCOORD_0"],True)
            indices=source.array(p["indices"]).reshape(-1)
            result=diagnose(native,pos,n,uv,indices)
        except (ValueError,KeyError,IndexError) as e:
            row.update(status="rejected input/native domain",error=str(e));blocks.append(name+": "+str(e));domains.append(row);continue
        processed+=1;row.update(result["summary"])
        old=source.array(attrs["TANGENT"],True)
        if old.shape!=(len(pos),4) or not np.isfinite(old).all():
            row.update(status="rejected malformed existing TANGENT",error="Source tangents must be finite matching Nx4")
            blocks.append(name+": source tangents are not finite matching Nx4");domains.append(row);continue
        old_dots=np.abs(np.einsum("ij,ij->i",old[:,:3].astype(np.float64),n.astype(np.float64)))
        old_bad=np.flatnonzero(old_dots>.01)
        unresolved=set(result["unresolved_vertices"].tolist());conflict=set(result["conflict_vertices"].tolist())
        row["before"]={"maximumAbsNormalTangentDot":float(old_dots.max(initial=0)),"aboveAbsDot0_01":len(old_bad),"aboveAbsDot0_5":int((old_dots>.5).sum()),"nonorthogonalVerticesWithUnresolvedCorners":sum(int(v) in unresolved for v in old_bad),"nonorthogonalVerticesWithCornerConflicts":sum(int(v) in conflict for v in old_bad)}
        corner_archive[name+"-source-indices"]=result["indices"]
        corner_archive[name+"-tangents"]=result["corner_tangents"]
        corner_archive[name+"-valid-mask"]=result["valid_corner_mask"]
        if not result["compatible"]:blocks.append(name+": unresolved/ambiguous existing indexed corners")
        ai=attrs["TANGENT"];accessor=source.doc["accessors"][ai]
        unsupported_storage=accessor["componentType"]!=5126 or accessor["type"]!="VEC4" or accessor.get("normalized",False) or "sparse" in accessor or "bufferView"not in accessor
        if unsupported_storage:
            blocks.append(name+": tangent storage is not dense float32 VEC4");row["candidateStorageCompatible"]=False
        else:
            row["candidateStorageCompatible"]=True
            frames=result["vertex_tangents"]
            if np.isfinite(frames).all():
                for key,actual in [("min",frames.min(axis=0)),("max",frames.max(axis=0))]:
                    if key in accessor and not np.array_equal(np.asarray(accessor[key],dtype=np.float32),actual):blocks.append(name+": tangent min/max JSON would require separate metadata rewrite")
            if any("TANGENT" in target for target in p.get("targets",[])):blocks.append(name+": existing tangent morph deltas require a separate posed rebake")
            if result["compatible"]:
                view=source.doc["bufferViews"][accessor["bufferView"]];stride=view.get("byteStride",16)
                if stride<16:raise ValueError("Invalid source tangent stride")
                offset=binary_start+view.get("byteOffset",0)+accessor.get("byteOffset",0)
                changed=[]
                for vertex,frame in enumerate(frames):
                    start=offset+vertex*stride;payload=frame.astype("<f4").tobytes()
                    if start in patches and patches[start]!=payload:blocks.append(name+": shared tangent storage has cross-primitive corner disagreement")
                    patches[start]=payload
                    if source.raw[start:start+16]!=payload:changed.append(vertex)
                row["compatibleChangedTangentRecords"]=len(changed)
                row["exampleChangedVertices"]=changed[:16]
        domains.append(row)
    if not processed:blocks.append("No supported source tangent domains were processed")
    compatible=processed>0 and not blocks
    report={"schema":1,"kind":"actual-source-mikktspace-diagnostic","diagnosticComplete":True,"source":str(source_path.resolve()),"sourceSha256":before,"sourceBytes":len(source.raw),"nativeBuild":native.receipt,
      "sources":{str(path.relative_to(ROOT)):sha(path) for path in [ROOT/"bridge.c",ROOT/"build_bridge.py",ROOT/"mikk_frames.py",ROOT/"regenerate.py",ROOT/"vendor/mikktspace.c",ROOT/"vendor/mikktspace.h",ROOT/"vendor/upstream.json"]},
      "reader":{"path":str(ROOT.parent/"hero-rama-lod/glb_lod.py"),"sha256":sha(ROOT.parent/"hero-rama-lod/glb_lod.py")},
      "domains":domains,"candidateCompatible":compatible,"candidateRequested":candidate_path is not None,"candidateWritten":False,"blockedReasons":blocks,
      "policy":{"cornerMapping":"Official output is per face/corner. Existing source-index collapse requires exact float32 direction/sign agreement; never average conflicting corners.","degenerate":"Geometry double-area or absolute UV determinant<=1e-12 after float32 conversion is unresolved. Diagnose clean faces only; strict candidate rejects any unresolved domains.","bounds":"Finite float32 coordinates/UVs within magnitude1000000;<=2000000vertices/6000000corners; supplied normals unit within0.002.","sourcePreservation":"Candidate, if written, changes dense base TANGENT records only. JSON/indices/position/normal/UV/skin/morph/image/face ownership remain byte-identical."},
      "limits":["Base geometry tangent calculation does not accept shading in morphed/deformed gameplay poses.","No UV seam splits, fallback recovery, normalization of source normals, Blender/import/render or runtime promotion performed.","Even a compatible tangent-only candidate needs source-matched native A/B material and animation review."]}
    if corners_path is not None:
        corners_path.parent.mkdir(parents=True,exist_ok=True)
        with corners_path.open("xb") as handle:np.savez_compressed(handle,**corner_archive)
        report["cornerArchive"]={"path":str(corners_path.resolve()),"sha256":sha(corners_path),"scope":"Per-corner outputs; NaNs explicitly mark unresolved corners, never candidate values"}
    if candidate_path is not None and compatible:
        raw=bytearray(source.raw);allowed=np.zeros(len(raw),dtype=bool)
        for offset,payload in patches.items():raw[offset:offset+16]=payload;allowed[offset:offset+16]=True
        old=np.frombuffer(source.raw,dtype=np.uint8);new=np.frombuffer(raw,dtype=np.uint8);changed=old!=new
        if bool(np.any(changed&~allowed)):raise ValueError("Non-tangent byte change rejected")
        # Reparse before publication, including accidental buffer-view aliasing:
        # identical JSON alone cannot prove that tangent storage did not overlap
        # position, skin, morph, mask, image or animation bytes.
        tangent_ids={p["attributes"]["TANGENT"] for _,_,p in source.primitives() if "TANGENT" in p["attributes"]}
        protected=set(range(len(source.doc["accessors"])))-tangent_ids
        for _,_,p in source.primitives():
            protected.add(p["indices"])
            protected.update(ai for semantic,ai in p["attributes"].items() if semantic!="TANGENT")
            protected.update(ai for target in p.get("targets",[]) for ai in target.values())
        for skin in source.doc.get("skins",[]):
            if "inverseBindMatrices" in skin:protected.add(skin["inverseBindMatrices"])
        for animation in source.doc.get("animations",[]):
            for sampler in animation["samplers"]:protected.update([sampler["input"],sampler["output"]])
        candidate_path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="yuga-tangent-proof-",dir=candidate_path.parent) as scratch:
            provisional=Path(scratch)/"candidate.glb";provisional.write_bytes(raw);candidate=GLB(provisional)
            if candidate.doc!=source.doc:raise ValueError("JSON/node/skin/animation/material ownership metadata changed")
            if any(source.array(ai).tobytes()!=candidate.array(ai).tobytes() for ai in protected):raise ValueError("Tangent storage aliases protected geometry/skin/morph/mask/animation accessor")
            if any(source.image(image)!=candidate.image(image) for image in source.doc.get("images",[])):raise ValueError("Tangent storage aliases protected image data")
        with candidate_path.open("xb") as handle:handle.write(raw)
        report.update(candidateWritten=True,candidate={"path":str(candidate_path.resolve()),"sha256":sha(candidate_path),"bytes":len(raw),"changedBytes":int(changed.sum()),"allowedTangentRecordBytes":int(allowed.sum()),"allOtherBytesIdentical":True,"geometrySkinMorphFaceMetadataIdentical":True})
    after=sha(source_path);report["sourceAfterSha256"]=after;report["sourceUnchanged"]=before==after
    if not report["sourceUnchanged"]:raise ValueError("Input changed during read-only diagnosis")
    report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",required=True,type=Path);parser.add_argument("--library",required=True,type=Path);parser.add_argument("--report",required=True,type=Path)
    parser.add_argument("--candidate",type=Path);parser.add_argument("--corners",type=Path)
    args=parser.parse_args();safe_outputs(args.source,args.report,args.candidate,args.corners)
    result=analyze_asset(NativeMikk(args.library),args.source,args.report,args.candidate,args.corners)
    print(json.dumps({"diagnosticComplete":True,"sourceSha256":result["sourceSha256"],"sourceUnchanged":result["sourceUnchanged"],"candidateCompatible":result["candidateCompatible"],"candidateWritten":result["candidateWritten"],"blockedDomains":len(result["blockedReasons"]),"report":str(args.report)},indent=2))
    raise SystemExit(2 if args.candidate is not None and not result["candidateWritten"] else 0)

if __name__=="__main__":main()
