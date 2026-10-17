#!/usr/bin/env python3
"""Offline exact-corner topology and complete-row preservation checks."""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import traceback
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'art/hero-rama-repair'))
from split_seams import plan_split,split_asset,GLB,NativeMikk,sha
from hero_tangent_cases import fixture,mirror,sheet
from build_bridge import build

def rewrite(path,mutate):
    g=GLB(path);doc=copy.deepcopy(g.doc);mutate(doc);j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*(-len(j)%4)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(j)+len(g.binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(g.binary),0x004e4942)+g.binary)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path,required=True);parser.add_argument('--build-dir',type=Path);args=parser.parse_args()
    if not args.report.is_absolute() or args.report.exists():parser.error('--report must be fresh absolute path')
    if args.build_dir is not None and not args.build_dir.is_absolute():parser.error('--build-dir must be absolute')
    checks=[]
    def yes(value,message='assertion failed'):
        if not value:raise AssertionError(message)
    def check(name,fn):
        try:fn();checks.append({'name':name,'passed':True})
        except Exception as error:checks.append({'name':name,'passed':False,'error':str(error),'traceback':traceback.format_exc()})
    def reject(fn):
        try:fn()
        except (ValueError,TypeError,IndexError):return
        raise AssertionError('Expected explicit rejection')
    idx=np.array([0,1,2,0,2,3],dtype=np.uint32);frames=np.tile([1,0,0,1],(6,1)).astype(np.float32);frames[3]=[-1,0,0,-1];valid=np.ones(6,dtype=bool)
    check('valid distinct corner signs and directions split exactly once',lambda:yes(plan_split(idx,frames,valid,4)['duplicates'].tolist()==[0]))
    check('cloned group changes only required corner',lambda:yes(plan_split(idx,frames,valid,4)['indices'].tolist()==[0,1,2,4,2,3]))
    def unresolved():
        mask=valid.copy();mask[3]=False;t=frames.copy();t[3]=np.nan;result=plan_split(idx,t,mask,4)
        yes(result['indices'][3]==idx[3]);yes(len(result['duplicates'])==0)
    check('unresolved corner remains original and NaN is never copied as a frame',unresolved)
    def signed_zero():
        t=frames.copy();t[3]=[1,-0.,0.,1];yes(len(plan_split(idx,t,valid,4)['duplicates'])==0)
    check('numeric signed-zero identity does not invent a seam',signed_zero)
    for label,bad in [('negative',np.array([-1,1,2])),('out-of-range',np.array([0,1,4])),('fractional',np.array([0.,1.,2.])),('bool',np.array([False,True,True])),('partial',np.array([0,1])),('rank2',np.array([[0,1,2]]))]:
        check('reject '+label+' index plan',lambda bad=bad:reject(lambda:plan_split(bad,frames,valid,4)))
    check('reject float64 output frame contract',lambda:reject(lambda:plan_split(idx,frames.astype(float),valid,4)))
    check('reject nonboolean valid mask',lambda:reject(lambda:plan_split(idx,frames,valid.astype(int),4)))
    bad=frames.copy();bad[0]=np.nan
    check('reject NaN labelled valid',lambda:reject(lambda:plan_split(idx,bad,valid,4)))
    bad2=frames.copy();bad2[0]=[2,0,0,1]
    check('reject nonunit labelled valid frame',lambda:reject(lambda:plan_split(idx,bad2,valid,4)))
    check('reject oversized vertex domain before output allocation',lambda:reject(lambda:plan_split(idx,frames,valid,2_000_001)))
    with tempfile.TemporaryDirectory(prefix='yuga-seam-tests-') as scratch:
        tmp=Path(scratch);build_dir=args.build_dir or tmp/'build';receipt=build(build_dir);native=NativeMikk(build_dir/'libyuga_mikktspace.so')
        source=tmp/'mirror.glb';fixture(source,mirror(),tangent_morph=True);identity=sha(source)
        output=tmp/'split.glb';result=split_asset(native,source,output,tmp/'split.json')
        check('actual official mirrored corner conflict resolves 1 to 0',lambda:yes(result['beforeConflictVertices']==1 and result['afterConflictVertices']==0 and result['duplicatedVertices']==1))
        original=GLB(source);candidate=GLB(output);oldp=original.doc['meshes'][0]['primitives'][0];newp=candidate.doc['meshes'][0]['primitives'][0]
        check('original binary prefix and metadata receipt preserved',lambda:yes(candidate.binary[:len(original.binary)]==original.binary and result['candidate']['originalAccessorViewMetadataIdentical']))
        check('original tangent rows copied without generated-frame writes',lambda:yes(np.array_equal(candidate.array(newp['attributes']['TANGENT']),np.tile([0,0,1,1],(6,1)))))
        check('every target channel including tangent morph is duplicated exactly',lambda:yes(all(np.array_equal(candidate.array(newp['targets'][0][key])[-1],original.array(ai)[0]) for key,ai in oldp['targets'][0].items())))
        check('one original face node and one original skin remain unchanged',lambda:yes(candidate.doc['nodes']==original.doc['nodes'] and candidate.doc['skins']==original.doc['skins']))
        check('source immutable after candidate generation',lambda:yes(sha(source)==identity and result['sourceUnchanged']))
        def noop():
            path=tmp/'clean.glb';fixture(path);out=tmp/'noop.glb';r=split_asset(native,path,out,tmp/'noop.json');yes(r['noOp'] and not r['candidateWritten'] and not out.exists())
        check('clean source explicitly returns no-op without meaningless candidate',noop)
        check('output cannot alias source',lambda:reject(lambda:split_asset(native,source,source,tmp/'source-alias.json')))
        check('report cannot alias source',lambda:reject(lambda:split_asset(native,source,tmp/'report-alias.glb',source)))
        linked=tmp/'hardlink.glb';os.link(source,linked)
        check('hardlinked output cannot alias source',lambda:reject(lambda:split_asset(native,source,linked,tmp/'hardlink.json')))
        check('existing candidate is never overwritten',lambda:reject(lambda:split_asset(native,source,output,tmp/'overwrite.json')))
        def shared():
            path=tmp/'shared.glb';fixture(path,mirror())
            def mutate(d):
                primitive=d['meshes'][0]['primitives'][0];primitive['attributes']['TEXCOORD_1']=primitive['attributes']['TEXCOORD_0'];d['meshes'][0]['primitives'].append(copy.deepcopy(primitive))
            rewrite(path,mutate);out=tmp/'shared-output.glb';r=split_asset(native,path,out,tmp/'shared.json');g=GLB(out);prims=g.doc['meshes'][0]['primitives']
            yes(r['duplicatedVertices']==2 and r['afterConflictVertices']==0);yes(prims[0]['attributes']['POSITION']!=prims[1]['attributes']['POSITION'])
            yes(np.array_equal(g.array(prims[0]['attributes']['TEXCOORD_0']),g.array(prims[0]['attributes']['TEXCOORD_1'])))
        check('shared accessors across primitives and extra UV channels copy safely',shared)
        def sparse():
            path=tmp/'sparse.glb';fixture(path,mirror())
            def mutate(d):
                p=d['meshes'][0]['primitives'][0];target=d['accessors'][p['targets'][0]['POSITION']];target.pop('bufferView')
                target['sparse']={'count':1,'indices':{'bufferView':d['accessors'][p['indices']]['bufferView'],'componentType':5125},'values':{'bufferView':d['accessors'][p['attributes']['POSITION']]['bufferView'],'byteOffset':12}}
            rewrite(path,mutate);g=GLB(path);p=g.doc['meshes'][0]['primitives'][0];before=g.array(p['targets'][0]['POSITION']);out=tmp/'sparse-output.glb';split_asset(native,path,out,tmp/'sparse.json');after=GLB(out);p=after.doc['meshes'][0]['primitives'][0];a=after.array(p['targets'][0]['POSITION']);yes(a.tobytes()==np.concatenate([before,before[[0]]]).tobytes())
        check('sparse morph expands exact original and cloned row values',sparse)
        def oversized():
            path=tmp/'oversized.glb';fixture(path,mirror(),oversized=True);reject(lambda:split_asset(native,path,tmp/'oversized-out.glb',tmp/'oversized.json'));yes(not (tmp/'oversized-out.glb').exists())
        check('enormous zero-filled source accessor rejected before expansion',oversized)
        def bad_morph():
            path=tmp/'bad-morph.glb';fixture(path,mirror());rewrite(path,lambda d:d['accessors'][d['meshes'][0]['primitives'][0]['targets'][0]['POSITION']].update(count=4))
            reject(lambda:split_asset(native,path,tmp/'bad-morph-out.glb',tmp/'bad-morph.json'))
        check('mismatched morph count rejects before candidate publication',bad_morph)
        report={'schema':1,'kind':'exact-corner-seam-contract','passed':all(c['passed'] for c in checks),'checks':checks,'count':len(checks),'testSourceSha256':sha(Path(__file__)),'splitterSha256':sha(ROOT/'art/hero-rama-repair/split_seams.py'),'build':receipt,'limits':['Offline synthetic authoring proof only; actual source candidate and native visual review are separate.','No UV/tangent rewrite, commercial quality or GPU performance claim.']}
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':report['count'],'failed':[c['name'] for c in checks if not c['passed']],'report':str(args.report)},indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
