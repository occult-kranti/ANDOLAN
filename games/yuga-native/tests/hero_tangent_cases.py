#!/usr/bin/env python3
"""Offline MikkTSpace authoring contract and immutable-GLB counterexamples."""
from __future__ import annotations
import argparse
import ctypes as ct
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import traceback
import numpy as np

ART=Path(__file__).resolve().parents[1]/"art/hero-rama-tangents"
sys.path.insert(0,str(ART))
from build_bridge import build,sha
from mikk_frames import NativeMikk,diagnose,prepare,strict_vertex_frames
from regenerate import analyze_asset,safe_outputs,GLB

def sheet():
    return (np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0]],dtype=np.float32),
            np.tile([0.,0.,1.],(4,1)).astype(np.float32),
            np.array([[0,0],[1,0],[1,1],[0,1]],dtype=np.float32),np.array([0,1,2,0,2,3],dtype=np.uint32))

def mirror(split=False):
    p=np.array([[0,0,0],[1,0,0],[0,1,0],[-1,0,0],[0,-1,0]],dtype=np.float32)
    uv=np.array([[0,0],[1,0],[0,1],[1,0],[0,-1]],dtype=np.float32)
    idx=[0,1,2,0,3,4]
    if split:p=np.vstack([p,p[0]]);uv=np.vstack([uv,uv[0]]);idx[3]=5
    return p,np.tile([0.,0.,1.],(len(p),1)).astype(np.float32),uv,np.array(idx,dtype=np.uint32)

def fixture(path:Path,data=None,*,tangent_morph=False,unsupported=False,alias_mask=False,oversized=False):
    """Tiny named-face+skin+morph+mask fixture, never the production source."""
    p,n,uv,idx=data or sheet();count=len(p);binary=bytearray();views=[];accessors=[]
    def add(a,kind,component=5126):
        while len(binary)%4:binary.append(0)
        raw=np.ascontiguousarray(a).tobytes();views.append({"buffer":0,"byteOffset":len(binary),"byteLength":len(raw)})
        binary.extend(raw);accessors.append({"bufferView":len(views)-1,"componentType":component,"count":len(a),"type":kind})
        return len(accessors)-1
    attrs={"POSITION":add(p,"VEC3"),"NORMAL":add(n,"VEC3"),"TEXCOORD_0":add(uv,"VEC2"),
           "TANGENT":add(np.tile([0.,0.,1.,1.],(count,1)).astype('<f4'),"VEC4"),
           "COLOR_0":add(np.tile([1.,1.,1.,.5],(count,1)).astype('<f4'),"VEC4"),
           "JOINTS_0":add(np.zeros((count,4),dtype='<u2'),"VEC4",5123),
           "WEIGHTS_0":add(np.tile([1.,0.,0.,0.],(count,1)).astype('<f4'),"VEC4")}
    if unsupported:del attrs["TANGENT"]
    if alias_mask:attrs["COLOR_0"]=attrs["TANGENT"]
    if oversized:
        accessors[attrs['POSITION']].pop('bufferView');accessors[attrs['POSITION']]['count']=2**40
    target={"POSITION":add(np.zeros((count,3),dtype='<f4'),"VEC3")}
    if tangent_morph:target["TANGENT"]=add(np.zeros((count,3),dtype='<f4'),"VEC3")
    prim={"attributes":attrs,"indices":add(idx.reshape(-1,1),"SCALAR",5125),"material":0,"targets":[target]}
    inverse=add(np.eye(4,dtype='<f4').reshape(1,16),"MAT4")
    doc={"asset":{"version":"2.0","generator":"YUGA test fixture only"},"buffers":[{"byteLength":len(binary)}],"bufferViews":views,"accessors":accessors,
         "materials":[{"name":"fixture-gold"}],"meshes":[{"name":"RamaFace","primitives":[prim],"weights":[0.],"extras":{"targetNames":["Blink"]}}],
         "nodes":[{"name":"RamaHero","children":[1,2]},{"name":"RootBone"},{"name":"RamaFace","mesh":0,"skin":0}],
         "skins":[{"name":"one-shared-rig","joints":[1],"inverseBindMatrices":inverse}],"scenes":[{"nodes":[0]}],"scene":0}
    raw_json=json.dumps(doc,separators=(',',':')).encode();raw_json+=b' '*(-len(raw_json)%4);binary+=b'\0'*(-len(binary)%4)
    raw=struct.pack('<4sII',b'glTF',2,28+len(raw_json)+len(binary))+struct.pack('<II',len(raw_json),0x4e4f534a)+raw_json+struct.pack('<II',len(binary),0x004e4942)+binary
    path.write_bytes(raw);return doc

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',required=True,type=Path);parser.add_argument('--build-dir',type=Path)
    args=parser.parse_args()
    if not args.report.is_absolute() or args.report.exists():parser.error('--report must be a fresh absolute path')
    if args.build_dir is not None and not args.build_dir.is_absolute():parser.error('--build-dir must be absolute')
    checks=[]
    def check(name,fn):
        try:
            detail=fn();checks.append({"name":name,"passed":True,**({"detail":detail} if detail is not None else {})})
        except Exception as error:checks.append({"name":name,"passed":False,"error":str(error),"traceback":traceback.format_exc()})
    def reject(fn):
        try:fn()
        except (ValueError,TypeError,IndexError):return
        raise AssertionError('Expected explicit rejection')
    def yes(value,message='assertion failed'):
        if not value:raise AssertionError(message)
    with tempfile.TemporaryDirectory(prefix='yuga-mikk-tests-') as scratch:
        tmp=Path(scratch);build_dir=args.build_dir or tmp/'build';receipt=build(build_dir);native=NativeMikk(build_dir/'libyuga_mikktspace.so')
        p,n,uv,idx=sheet()
        check('official vendor hashes verified during offline build',lambda:yes(len(receipt['upstreamFiles'])==3))
        check('planar analytic tangent and handedness',lambda:yes(np.allclose(strict_vertex_frames(native,p,n,uv,idx),[1,0,0,1],atol=1e-6)))
        def rotated():
            t=np.array([1.,2.,3.]);t/=np.linalg.norm(t);normal=np.array([-2.,1.,0.]);normal/=np.linalg.norm(normal);b=np.cross(normal,t)
            pos=uv[:,0,None]*t+uv[:,1,None]*b
            out=strict_vertex_frames(native,pos,np.tile(normal,(4,1)),uv,idx)
            yes(np.allclose(out[:,:3],t,atol=2e-6));yes(np.all(out[:,3]==1));return {'independentTangent':t.tolist(),'normal':normal.tolist()}
        check('rotated 3D analytic derivative oracle',rotated)
        check('face permutation preserves planar per-vertex result',lambda:yes(np.array_equal(strict_vertex_frames(native,p,n,uv,idx),strict_vertex_frames(native,p,n,uv,idx.reshape(-1,3)[::-1]))))
        def mirror_conflict():
            result=diagnose(native,*mirror());yes(result['summary']['handednessConflictVertices']==1)
            yes(result['corner_tangents'][0,3]==1 and result['corner_tangents'][3,3]==-1)
            reject(lambda:strict_vertex_frames(native,*mirror()));return result['summary']
        check('mirrored shared index retains opposite corner signs and rejects collapse',mirror_conflict)
        check('authored mirrored split preserves distinct valid frames',lambda:yes(diagnose(native,*mirror(True))['compatible']))
        for label,bad in [('negative',[-1,1,2]),('out of bounds',[0,1,4]),('fractional',[0.,1.,2.]),('bool',[False,True,True]),('mixed bool',[0,True,2]),('partial',[0,1]),('empty',[]),('object',np.array([0,1,2],dtype=object)),('three-dimensional',np.array([[[0,1,2]]]))]:
            check('reject '+label+' indices',lambda bad=bad:reject(lambda:prepare(p,n,uv,bad)))
        for label,array_index,value in [('NaN position',0,np.nan),('Inf normal',1,np.inf),('Inf UV',2,np.inf),('float32 overflow',0,1e39),('finite beyond bound',2,1000001.)]:
            def bad_array(array_index=array_index,value=value):
                arrays=[p.astype(np.float64),n.astype(np.float64),uv.astype(np.float64)];arrays[array_index][0,0]=value
                reject(lambda:prepare(*arrays,idx))
            check('reject '+label,bad_array)
        check('reject zero normal',lambda:reject(lambda:prepare(p,np.zeros_like(n),uv,idx)))
        check('reject nonunit normal',lambda:reject(lambda:prepare(p,n*2,uv,idx)))
        check('reject mismatched vertex domains',lambda:reject(lambda:prepare(p,n[:-1],uv,idx)))
        check('reject complex geometry',lambda:reject(lambda:prepare(p.astype(complex),n,uv,idx)))
        check('reject boolean UV',lambda:reject(lambda:prepare(p,n,uv.astype(bool),idx)))
        def degenerate(data,kind):
            result=diagnose(native,*data);yes(result['summary'][kind]>0);yes(not result['compatible']);yes(result['summary']['unresolvedCorners']>0)
            reject(lambda:strict_vertex_frames(native,*data));return result['summary']
        check('zero UV explicitly unresolved',lambda:degenerate((p,n,np.zeros_like(uv),idx),'degenerateUVFaces'))
        check('zero geometry explicitly unresolved',lambda:degenerate((np.zeros_like(p),n,uv,idx),'degenerateGeometryFaces'))
        check('float32-collapsed UV explicitly unresolved',lambda:degenerate((p,n,uv.astype(float)*1e-46,idx),'degenerateUVFaces'))
        check('tiny finite geometry below policy area explicitly unresolved',lambda:degenerate((p*1e-8,n,uv,idx),'degenerateGeometryFaces'))
        check('unused source vertex disallows invented tangent',lambda:yes(not diagnose(native,np.vstack([p,p[0]]),np.vstack([n,n[0]]),np.vstack([uv,uv[0]]),idx)['compatible']))
        def direct(code,*,position=None,normal=None,tex=None,index=None,output_count=24,corners=6):
            a=np.ascontiguousarray(p if position is None else position,dtype=np.float32);b=np.ascontiguousarray(n if normal is None else normal,dtype=np.float32)
            c=np.ascontiguousarray(uv if tex is None else tex,dtype=np.float32);d=np.ascontiguousarray(idx if index is None else index,dtype=np.uint32);out=np.zeros((6,4),dtype=np.float32)
            got=native.function(a.ctypes.data_as(ct.POINTER(ct.c_float)),b.ctypes.data_as(ct.POINTER(ct.c_float)),c.ctypes.data_as(ct.POINTER(ct.c_float)),4,d.ctypes.data_as(ct.POINTER(ct.c_uint32)),corners,out.ctypes.data_as(ct.POINTER(ct.c_float)),output_count)
            yes(got==code,f'Expected return {code}, got {got}');return {'nativeReturn':got}
        check('native valid direct ABI',lambda:direct(0))
        check('native rejects wrong output capacity before callback',lambda:direct(1,output_count=23))
        check('native rejects partial face before callback',lambda:direct(1,corners=5,output_count=20))
        for label,val in [('NaN',np.nan),('Inf',np.inf),('negative Inf',-np.inf)]:
            a=p.copy();a[0,0]=val;check('native rejects '+label+' position before callback',lambda a=a:direct(2,position=a))
        bad=idx.copy();bad[0]=4;check('native rejects out-of-bounds index before callback',lambda:direct(3,index=bad))
        check('native rejects zero normals before callback',lambda:direct(4,normal=np.zeros_like(n)))
        check('native rejects degenerate UV before callback',lambda:direct(7,tex=np.zeros_like(uv)))
        def tamper():
            folder=tmp/'tamper';folder.mkdir();shutil.copy2(build_dir/'build.json',folder/'build.json');data=bytearray((build_dir/'libyuga_mikktspace.so').read_bytes());data[-1]^=1
            (folder/'libyuga_mikktspace.so').write_bytes(data);reject(lambda:NativeMikk(folder/'libyuga_mikktspace.so'))
        check('binary receipt tamper rejected before native load',tamper)
        source=tmp/'source.glb';fixture(source);before=sha(source)
        def candidate():
            report=analyze_asset(native,source,tmp/'positive.json',tmp/'candidate.glb',tmp/'corners.npz')
            yes(report['candidateWritten']);yes(report['candidate']['changedBytes']>0);yes(sha(source)==before)
            original=GLB(source);changed=GLB(tmp/'candidate.glb');yes(original.doc==changed.doc)
            tangent=original.doc['meshes'][0]['primitives'][0]['attributes']['TANGENT']
            allowed=np.zeros(len(original.raw),dtype=bool);a=original.doc['accessors'][tangent];v=original.doc['bufferViews'][a['bufferView']]
            start=28+struct.unpack_from('<I',original.raw,12)[0]+v['byteOffset'];allowed[start:start+a['count']*16]=True
            delta=np.frombuffer(original.raw,dtype=np.uint8)!=np.frombuffer(changed.raw,dtype=np.uint8)
            yes(not np.any(delta&~allowed));yes(np.allclose(changed.array(tangent),[1,0,0,1]));return report['candidate']
        check('tangent-only GLB candidate preserves JSON skin morph mask geometry and source',candidate)
        check('report cannot equal source',lambda:reject(lambda:analyze_asset(native,source,source)))
        check('candidate cannot equal source',lambda:reject(lambda:analyze_asset(native,source,tmp/'alias-report.json',source)))
        hard=tmp/'hardlink.glb';os.link(source,hard)
        check('hardlinked output source alias rejected',lambda:reject(lambda:safe_outputs(source,hard)))
        sym=tmp/'symlink.glb';sym.symlink_to(source)
        check('symlink output source alias rejected',lambda:reject(lambda:safe_outputs(source,sym)))
        check('report and candidate cannot alias each other',lambda:reject(lambda:safe_outputs(source,tmp/'same',tmp/'same')))
        check('existing output never overwritten',lambda:reject(lambda:safe_outputs(source,tmp/'positive.json')))
        def blocked(label,data=None,**kwargs):
            path=tmp/(label+'.glb');fixture(path,data,**kwargs);identity=sha(path);out=tmp/(label+'-candidate.glb')
            report=analyze_asset(native,path,tmp/(label+'-report.json'),out)
            yes(not report['candidateWritten']);yes(not report['candidateCompatible']);yes(not out.exists());yes(sha(path)==identity);return report['blockedReasons']
        check('ambiguous GLB corner domain never writes candidate',lambda:blocked('ambiguous',mirror()))
        check('degenerate GLB domain never writes candidate',lambda:blocked('degenerate',(p,n,np.zeros_like(uv),idx)))
        check('existing tangent morph blocks unposed overwrite',lambda:blocked('morphed',tangent_morph=True))
        check('no supported tangent domain cannot write empty candidate',lambda:blocked('unsupported',unsupported=True))
        check('oversized zero-filled source accessor rejects before allocation',lambda:blocked('oversized',oversized=True))
        def aliased_attribute():
            path=tmp/'attribute-alias.glb';fixture(path,alias_mask=True);identity=sha(path);out=tmp/'attribute-alias-candidate.glb'
            reject(lambda:analyze_asset(native,path,tmp/'attribute-alias-report.json',out))
            yes(not out.exists());yes(sha(path)==identity)
        check('tangent storage aliasing protected COLOR mask rejects before publication',aliased_attribute)
        check('source identity retained after all alias counterexamples',lambda:yes(sha(source)==before))
        report={"schema":1,"kind":"offline-mikktspace-authoring-contract","passed":all(c['passed'] for c in checks),"checks":checks,"count":len(checks),"build":receipt,
                "testSourceSha256":sha(Path(__file__)),"toolSources":{p.name:sha(p) for p in ART.glob('*.py')},
                "limits":["Synthetic tool/ABI and source immutability evidence; no native render, hardware FPS, final-art or runtime promotion acceptance.","Actual indexed authoring domains are diagnosed separately; synthetic success does not make an ambiguous production mesh compatible."]}
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print(json.dumps({"passed":report['passed'],"checks":len(checks),"failed":[c['name'] for c in checks if not c['passed']],"report":str(args.report)},indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
