"""Per-corner MikkTSpace authoring data and fail-closed indexed compatibility.

No averaging of source-index corner frames is allowed. Degenerate faces are
explicit unresolved domains; diagnostics call the official algorithm only on
clean faces. Strict generation/candidate writing rejects unresolved domains.
"""
from __future__ import annotations
import ctypes as ct
import hashlib
import json
from pathlib import Path
import numpy as np
from build_bridge import PINS, ROOT, UPSTREAM, sha

MAX_VERTICES=2_000_000
MAX_CORNERS=6_000_000
AREA_EPSILON=1e-12
NORMAL_TOLERANCE=.002

class NativeMikk:
    def __init__(self,path: Path):
        self.path=Path(path).resolve()
        self.receipt=json.loads((self.path.parent/"build.json").read_text())
        if self.receipt["upstreamCommit"]!=UPSTREAM or self.receipt["upstreamFiles"]!=PINS or self.receipt["binarySha256"]!=sha(self.path) or self.receipt["adapterSha256"]!=sha(ROOT/"bridge.c"):
            raise ValueError("Native library/source receipt mismatch")
        self.library=ct.CDLL(str(self.path))
        self.function=self.library.yuga_mikk_generate
        self.function.restype=ct.c_int
        self.function.argtypes=[ct.POINTER(ct.c_float)]*3+[ct.c_uint32,ct.POINTER(ct.c_uint32),ct.c_uint32,ct.POINTER(ct.c_float),ct.c_size_t]

    def generate_validated(self,p: np.ndarray,n: np.ndarray,uv: np.ndarray,indices: np.ndarray) -> np.ndarray:
        output=np.full((len(indices),4),np.nan,dtype=np.float32)
        code=self.function(p.ctypes.data_as(ct.POINTER(ct.c_float)),n.ctypes.data_as(ct.POINTER(ct.c_float)),uv.ctypes.data_as(ct.POINTER(ct.c_float)),len(p),indices.ctypes.data_as(ct.POINTER(ct.c_uint32)),len(indices),output.ctypes.data_as(ct.POINTER(ct.c_float)),output.size)
        if code:raise ValueError("Native Mikk bridge rejected domain; return code="+str(code))
        return output

def prepare(positions,normals,uvs,indices):
    arrays=[]
    for value,width,label in [(positions,3,"POSITION"),(normals,3,"NORMAL"),(uvs,2,"TEXCOORD_0")]:
        original=np.asarray(value)
        if original.ndim!=2 or original.shape[1]!=width or original.dtype.kind not in "fiu" or original.dtype.kind=="b":
            raise ValueError(label+" must be a real numeric Nx"+str(width)+" array")
        with np.errstate(over="ignore",invalid="ignore"):
            a=np.ascontiguousarray(original,dtype=np.float32)
        if not np.isfinite(a).all() or float(np.abs(a).max(initial=0))>1_000_000:
            raise ValueError(label+" nonfinite/float32-overflow/unbounded authoring coordinates")
        arrays.append(a)
    p,n,uv=arrays
    if not 0<len(p)<=MAX_VERTICES or len(n)!=len(p) or len(uv)!=len(p):raise ValueError("Vertex array counts differ or exceed bounded capacity")
    normal_lengths=np.linalg.norm(n.astype(np.float64),axis=1)
    if np.any(np.abs(normal_lengths-1)>NORMAL_TOLERANCE):raise ValueError("Normals must be nonzero and unit; normalization is not silently invented")
    def contains_bool(value):
        if isinstance(value,(bool,np.bool_)):return True
        if isinstance(value,(list,tuple)):return any(contains_bool(item) for item in value)
        return False
    if contains_bool(indices):raise ValueError("Boolean indices are not numeric source indices")
    idx=np.asarray(indices)
    if idx.dtype.kind not in "iu" or idx.dtype.kind=="b" or idx.ndim not in (1,2) or (idx.ndim==2 and idx.shape[1]!=3):
        raise ValueError("Indices must be integer triangle/corner indices; bool/float indices are rejected")
    idx=idx.reshape(-1)
    if not 0<len(idx)<=MAX_CORNERS or len(idx)%3:raise ValueError("Require bounded complete nonempty triangles")
    if int(idx.min())<0 or int(idx.max())>=len(p):raise ValueError("Index outside source vertex domain")
    return p,n,uv,np.ascontiguousarray(idx,dtype=np.uint32)

def triangle_domains(p,uv,idx):
    faces=idx.reshape(-1,3)
    xyz=p.astype(np.float64)[faces];tex=uv.astype(np.float64)[faces]
    cross=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
    area=np.linalg.norm(cross,axis=1)
    a,b=tex[:,1]-tex[:,0],tex[:,2]-tex[:,0]
    determinant=a[:,0]*b[:,1]-a[:,1]*b[:,0]
    bad_geometry=area<=AREA_EPSILON
    bad_uv=np.abs(determinant)<=AREA_EPSILON
    return faces,bad_geometry,bad_uv

def diagnose(native: NativeMikk,positions,normals,uvs,indices) -> dict:
    p,n,uv,idx=prepare(positions,normals,uvs,indices)
    faces,bad_geometry,bad_uv=triangle_domains(p,uv,idx)
    clean=~(bad_geometry|bad_uv)
    all_corners=np.full((len(idx),4),np.nan,dtype=np.float32)
    clean_corner_ids=np.flatnonzero(np.repeat(clean,3))
    native_error=""
    if len(clean_corner_ids):
        try:all_corners[clean_corner_ids]=native.generate_validated(p,n,uv,np.ascontiguousarray(idx[clean_corner_ids]))
        except ValueError as e:native_error=str(e)
    finite=np.isfinite(all_corners).all(axis=1)
    lengths=np.linalg.norm(all_corners[:,:3].astype(np.float64),axis=1)
    dot=np.abs(np.einsum("ij,ij->i",all_corners[:,:3].astype(np.float64),n[idx].astype(np.float64)))
    valid=finite&(np.abs(lengths-1)<.002)&(dot<.002)&(np.abs(all_corners[:,3])==1)
    used=np.unique(idx)
    first_frames=np.full((len(p),4),np.nan,dtype=np.float32)
    valid_ids=np.flatnonzero(valid)
    valid_used,first_valid=np.unique(idx[valid_ids],return_index=True)
    first_frames[valid_used]=all_corners[valid_ids[first_valid]]
    direction_diff=np.any(all_corners[:,:3]!=first_frames[idx,:3],axis=1)&valid
    sign_diff=(all_corners[:,3]!=first_frames[idx,3])&valid
    conflict_vertices=np.unique(idx[direction_diff|sign_diff])
    direction_delta=np.linalg.norm(all_corners[:,:3].astype(np.float64)-first_frames[idx,:3].astype(np.float64),axis=1)
    conflict_examples=[]
    for vertex in conflict_vertices[:16]:
        corners=np.flatnonzero((idx==vertex)&valid)
        conflict_examples.append({"vertex":int(vertex),"validCornerCount":len(corners),"maximumDirectionDeltaFromFirst":float(direction_delta[corners].max(initial=0)),"handedness":np.unique(all_corners[corners,3]).tolist()})
    unresolved_vertices=np.unique(idx[~valid])
    unused=np.setdiff1d(np.arange(len(p),dtype=np.uint32),used)
    compatible=not native_error and bool(valid.all()) and not len(conflict_vertices) and not len(unused)
    valid_dots=dot[valid]
    return {"positions":p,"normals":n,"uvs":uv,"indices":idx,"corner_tangents":all_corners,"valid_corner_mask":valid,"vertex_tangents":first_frames,
      "compatible":compatible,"summary":{"vertices":len(p),"triangles":len(faces),"corners":len(idx),"cleanFacesSentToMikk":int(clean.sum()),
        "degenerateGeometryFaces":int(bad_geometry.sum()),"degenerateUVFaces":int(bad_uv.sum()),"unresolvedCorners":int((~valid).sum()),
        "degenerateUnionFaces":int((bad_geometry|bad_uv).sum()),
        "invalidOutputOnCleanCorners":int((~valid[clean_corner_ids]).sum()),"ambiguousSourceVertices":len(conflict_vertices),
        "directionConflictVertices":len(np.unique(idx[direction_diff])),"handednessConflictVertices":len(np.unique(idx[sign_diff])),
        "unresolvedSourceVertices":len(unresolved_vertices),"unusedSourceVertices":len(unused),"candidateCompatible":compatible,"nativeError":native_error,
        "maximumAbsNormalTangentDotOnValidCorners":float(valid_dots.max(initial=0)),"cornerOutputSha256":hashlib.sha256(all_corners.tobytes()).hexdigest(),
        "maximumValidCornerDirectionDeltaFromFirst":float(direction_delta[valid].max(initial=0)),"exampleCornerConflicts":conflict_examples,
        "exampleDegenerateGeometryFaces":np.flatnonzero(bad_geometry)[:16].tolist(),"exampleDegenerateUVFaces":np.flatnonzero(bad_uv)[:16].tolist(),
        "exampleAmbiguousVertices":conflict_vertices[:16].tolist(),"exampleUnresolvedVertices":unresolved_vertices[:16].tolist()},
      "conflict_vertices":conflict_vertices,"unresolved_vertices":unresolved_vertices}

def strict_vertex_frames(native: NativeMikk,positions,normals,uvs,indices) -> np.ndarray:
    result=diagnose(native,positions,normals,uvs,indices)
    if not result["compatible"]:raise ValueError("Existing index domain needs authoring/seam/degenerate repair; per-corner frames must not be averaged: "+json.dumps(result["summary"],sort_keys=True))
    return result["vertex_tangents"]
