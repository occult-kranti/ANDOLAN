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
from split_seams import plan_split,split_asset,GLB,NativeMikk,sha,safe_outputs,PROJECT
from hero_tangent_cases import fixture,mirror,sheet
from build_bridge import build

def rewrite(path,mutate):
    g=GLB(path);doc=copy.deepcopy(g.doc);mutate(doc);j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*(-len(j)%4)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(j)+len(g.binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(g.binary),0x004e4942)+g.binary)

def write_binary(path,doc,binary):
    j=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();j+=b' '*(-len(j)%4);binary=bytes(binary)+b'\0'*(-len(binary)%4)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)

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
        # R2 admission regressions: use real malformed storage and public calls,
        # and assert refusal precedes every candidate/report/target write.
        def boundary(use_parent_alias=False,nonasset=False):
            parent=PROJECT
            if use_parent_alias:
                parent=tmp/'native-parent-alias';parent.symlink_to(PROJECT,target_is_directory=True)
            destination=parent/('docs/UNWRITTEN-seam-regression.glb' if nonasset else 'assets/heroes/UNWRITTEN-seam-regression.glb')
            report=tmp/('boundary-'+str(use_parent_alias)+'-'+str(nonasset)+'.json')
            yes(not os.path.lexists(destination));reject(lambda:split_asset(None,source,destination,report));yes(not os.path.lexists(destination) and not report.exists())
        check('public API refuses candidate inside native assets before native use',boundary)
        check('public API refuses candidate anywhere inside native project',lambda:boundary(nonasset=True))
        check('resolved symlink parent cannot bypass native-project boundary',lambda:boundary(True))
        def dangling(which):
            out=tmp/('dangling-'+which+'.glb');report=tmp/('dangling-'+which+'.json');target=tmp/('UNCREATED-'+which);link=out if which=='output' else report;link.symlink_to(target)
            reject(lambda:split_asset(native,source,out,report));yes(not target.exists());yes(link.is_symlink())
            yes(not (report if which=='output' else out).exists())
        check('dangling candidate symlink refused without following target',lambda:dangling('output'))
        check('dangling report symlink refused before candidate publication',lambda:dangling('report'))
        check('fresh report and candidate aliases refused',lambda:reject(lambda:safe_outputs(source,tmp/'same-new',tmp/'same-new',native.path)))
        check('native library cannot alias candidate',lambda:reject(lambda:safe_outputs(source,native.path,tmp/'library-output.json',native.path)))
        check('native library cannot alias report',lambda:reject(lambda:safe_outputs(source,tmp/'library-report.glb',native.path,native.path)))
        check('source and native library aliases refused',lambda:reject(lambda:safe_outputs(native.path,tmp/'library-source.glb',tmp/'library-source.json',native.path)))
        def logical(label,value):
            path=tmp/('logical-'+label+'.glb');fixture(path,mirror());rewrite(path,lambda d:d['buffers'][0].update(byteLength=value));identity=sha(path);out=tmp/('logical-'+label+'-out.glb');report=tmp/('logical-'+label+'.json')
            reject(lambda:split_asset(native,path,out,report));yes(not out.exists() and not report.exists() and sha(path)==identity)
        check('short declared logical BIN length refuses before publication',lambda:logical('short',16))
        check('logical BIN length beyond actual payload refuses before publication',lambda:logical('long',1_000_000))
        def nonfinite(label,accessor_selector):
            path=tmp/('nonfinite-'+label+'.glb');fixture(path,mirror(),tangent_morph=True);g=GLB(path);ai=accessor_selector(g.doc);a=g.doc['accessors'][ai];view=g.doc['bufferViews'][a['bufferView']];binary=bytearray(g.binary)
            struct.pack_into('<f',binary,view.get('byteOffset',0)+a.get('byteOffset',0),float('nan'));write_binary(path,g.doc,binary)
            identity=sha(path);out=tmp/('nonfinite-'+label+'-out.glb');report=tmp/('nonfinite-'+label+'.json');reject(lambda:split_asset(native,path,out,report));yes(not out.exists() and not report.exists() and sha(path)==identity)
        for semantic in ['TANGENT','COLOR_0','WEIGHTS_0']:
            check('nonfinite protected '+semantic+' refuses before publication',lambda semantic=semantic:nonfinite(semantic,lambda d:d['meshes'][0]['primitives'][0]['attributes'][semantic]))
        check('nonfinite morph channel refuses before publication',lambda:nonfinite('morph',lambda d:d['meshes'][0]['primitives'][0]['targets'][0]['TANGENT']))
        check('nonfinite protected inverse bind matrix refuses before publication',lambda:nonfinite('skin',lambda d:d['skins'][0]['inverseBindMatrices']))
        def unused_nan():
            path=tmp/'unused-nan.glb';fixture(path,mirror());g=GLB(path);doc=copy.deepcopy(g.doc);binary=bytearray(g.binary)
            doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':4});binary.extend(struct.pack('<f',float('nan')))
            doc['accessors'].append({'bufferView':len(doc['bufferViews'])-1,'componentType':5126,'type':'SCALAR','count':1});doc['buffers'][0]['byteLength']=len(binary);write_binary(path,doc,binary)
            out=tmp/'unused-nan-out.glb';report=tmp/'unused-nan.json';reject(lambda:split_asset(native,path,out,report));yes(not out.exists() and not report.exists())
        check('nonfinite unreferenced accessor also refuses publication',unused_nan)
        def interleaved_sparse():
            path=tmp/'interleaved.glb';fixture(path,mirror(),tangent_morph=True);g=GLB(path);doc=copy.deepcopy(g.doc);binary=bytearray(g.binary);p=doc['meshes'][0]['primitives'][0]
            def view(payload,stride=None):
                while len(binary)%4:binary.append(0)
                meta={'buffer':0,'byteOffset':len(binary),'byteLength':len(payload)}
                if stride is not None:meta['byteStride']=stride
                doc['bufferViews'].append(meta);binary.extend(payload);return len(doc['bufferViews'])-1
            inter=np.concatenate([g.array(p['attributes'][semantic]) for semantic in ['POSITION','NORMAL','TANGENT']],axis=1).astype('<f4');vi=view(inter.tobytes(),40)
            for semantic,offset in [('POSITION',0),('NORMAL',12),('TANGENT',24)]:doc['accessors'][p['attributes'][semantic]].update(bufferView=vi,byteOffset=offset)
            p['attributes']['TEXCOORD_1']=p['attributes']['TEXCOORD_0']
            color=view(np.tile([255,255,255,128],(5,1)).astype('u1').tobytes());doc['accessors'][p['attributes']['COLOR_0']].update(bufferView=color,componentType=5121,normalized=True)
            sparse_i=view(np.array([0,4],dtype='u1').tobytes());sparse_v=view(np.array([[.125,0,0],[0,.25,0]],dtype='<f4').tobytes());morph=doc['accessors'][p['targets'][0]['POSITION']];morph.pop('bufferView');morph['sparse']={'count':2,'indices':{'bufferView':sparse_i,'componentType':5121},'values':{'bufferView':sparse_v}}
            doc['buffers'][0]['byteLength']=len(binary);write_binary(path,doc,binary);original=GLB(path);out=tmp/'interleaved-output.glb';r=split_asset(native,path,out,tmp/'interleaved.json');after=GLB(out);op=original.doc['meshes'][0]['primitives'][0];np_=after.doc['meshes'][0]['primitives'][0];mapping=np.array([0,1,2,3,4,0])
            yes(r['afterConflictVertices']==0 and r['duplicatedVertices']==1)
            for key,ai in op['attributes'].items():yes(original.array(ai)[mapping].tobytes()==after.array(np_['attributes'][key]).tobytes(),key)
            for key,ai in op['targets'][0].items():yes(original.array(ai)[mapping].tobytes()==after.array(np_['targets'][0][key]).tobytes(),key)
        check('valid interleaved sparse reflected-chart shared-UV normalized-COLOR fixture still passes',interleaved_sparse)
        report={'schema':1,'kind':'exact-corner-seam-contract','passed':all(c['passed'] for c in checks),'checks':checks,'count':len(checks),'testSourceSha256':sha(Path(__file__)),'splitterSha256':sha(ROOT/'art/hero-rama-repair/split_seams.py'),'build':receipt,'limits':['Offline synthetic authoring proof only; actual source candidate and native visual review are separate.','No UV/tangent rewrite, commercial quality or GPU performance claim.']}
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':report['count'],'failed':[c['name'] for c in checks if not c['passed']],'report':str(args.report)},indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
