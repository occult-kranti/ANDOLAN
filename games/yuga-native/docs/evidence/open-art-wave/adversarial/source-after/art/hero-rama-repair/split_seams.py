#!/usr/bin/env python3
"""Candidate-only exact Mikk corner partition; copy all rows, write no tangents.

UV/geometry-degenerate corners retain their original source index. This step
separates conflicting VALID corner groups so a later, separately accepted
authoring rebake can represent them. It does not repair UVs or shading.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'hero-rama-tangents'))
from build_bridge import sha
from mikk_frames import NativeMikk,diagnose,MAX_VERTICES,MAX_CORNERS
from regenerate import GLB
from repair_mesh import read_checked

PROJECT=HERE.parents[1].resolve()

def safe_outputs(source,output,report,library=None):
    """Public admission guard, before native calls, directories or file writes.

    Resolve parent symlinks to enforce the entire native-project boundary;
    lexists also refuses a dangling final symlink. All writes later use these
    resolved paths plus exclusive creation, never a following write_text.
    """
    originals=[Path(source),Path(output),Path(report)]
    if library is not None:originals.append(Path(library))
    try:resolved=[path.resolve() for path in originals]
    except (RuntimeError,OSError) as error:raise ValueError('Unresolvable source/output/library path') from error
    if len(set(resolved))!=len(resolved):raise ValueError('Source/library/candidate/report paths alias')
    for path in originals[1:3]:
        if os.path.lexists(path):raise ValueError('Outputs must be fresh, including no dangling symlinks')
    if resolved[1]==PROJECT or PROJECT in resolved[1].parents:raise ValueError('Candidate must remain outside the entire native project')
    return tuple(resolved[:3])

def admitted_source(path):
    """Reuse the bounded logical-BIN/sparse/layout validator, then finite-check
    all accessors, including protected, animation and unreferenced records.
    """
    source=read_checked(path)
    for ai in range(len(source.doc['accessors'])):
        if not np.isfinite(source.array(ai)).all():raise ValueError('Nonfinite protected/source accessor data')
    return source

def plan_split(indices,tangents,valid,vertex_count):
    idx=np.asarray(indices);t=np.asarray(tangents);valid=np.asarray(valid)
    if type(vertex_count) is not int or not 0<vertex_count<=MAX_VERTICES:raise ValueError('Invalid bounded source vertex count')
    if idx.dtype.kind not in 'iu' or idx.ndim!=1 or not 0<len(idx)<=MAX_CORNERS or len(idx)%3 or int(idx.min())<0 or int(idx.max())>=vertex_count:raise ValueError('Invalid bounded complete index domain')
    if t.dtype!=np.dtype(np.float32) or t.shape!=(len(idx),4) or valid.dtype!=np.dtype(bool) or valid.shape!=(len(idx),):raise ValueError('Malformed corner frame/mask domain')
    if not np.isfinite(t[valid]).all() or not np.all(np.abs(t[valid,3])==1):raise ValueError('Invalid valid-corner frame')
    lengths=np.linalg.norm(t[valid,:3].astype(np.float64),axis=1)
    if np.any(np.abs(lengths-1)>=.002):raise ValueError('Valid tangent direction is not unit')
    # Official output groups are exact numeric float32 tuples, including sign.
    # +0/-0 compare equal; nothing is rounded, averaged or written to TANGENT.
    groups={};result=idx.astype(np.uint32,copy=True);duplicates=[];changes=[]
    for corner in np.flatnonzero(valid):
        source_vertex=int(idx[corner]);frame=tuple(float(x) for x in t[corner]);mapping=groups.setdefault(source_vertex,{})
        if frame not in mapping:
            target=source_vertex if not mapping else vertex_count+len(duplicates)
            if mapping:
                if target>=MAX_VERTICES:raise ValueError('Split exceeds bounded vertex capacity')
                duplicates.append(source_vertex)
                changes.append({'sourceVertex':source_vertex,'newVertex':target,'groupFrame':list(frame),'firstCorner':int(corner)})
            mapping[frame]=target
        result[corner]=mapping[frame]
    if not np.array_equal(result[~valid],idx[~valid]):raise AssertionError('Unresolved corner changed')
    return {'indices':result,'duplicates':np.array(duplicates,dtype=np.uint32),'changes':changes,'conflictVertices':sum(len(value)>1 for value in groups.values())}

def read_domain(source,primitive):
    attrs=primitive['attributes']
    if primitive.get('mode',4)!=4 or not {'POSITION','NORMAL','TEXCOORD_0','TANGENT'}<=attrs.keys():raise ValueError('Only complete triangle tangent domains supported')
    arrays={}
    for semantic,ai in attrs.items():
        if type(ai) is not int or not 0<=ai<len(source.doc['accessors']):raise ValueError('Invalid attribute accessor index')
        spec=source.doc['accessors'][ai]
        if type(spec['count']) is not int or not 0<spec['count']<=MAX_VERTICES:raise ValueError('Attribute exceeds bounded capacity before expansion')
        arrays[semantic]=source.array(ai)
    count=len(arrays['POSITION'])
    if any(len(value)!=count for value in arrays.values()):raise ValueError('Attribute vertex counts disagree')
    ii=primitive['indices']
    if type(ii) is not int or not 0<=ii<len(source.doc['accessors']):raise ValueError('Invalid index accessor')
    spec=source.doc['accessors'][ii]
    if type(spec['count']) is not int or not 0<spec['count']<=MAX_CORNERS or spec['count']%3:raise ValueError('Index exceeds bounded complete triangles')
    idx=source.array(ii).reshape(-1)
    targets=[]
    for target in primitive.get('targets',[]):
        values={}
        for semantic,ai in target.items():
            if type(ai) is not int or not 0<=ai<len(source.doc['accessors']) or source.doc['accessors'][ai]['count']!=count:raise ValueError('Morph count/index does not match source vertices')
            values[semantic]=source.array(ai)
        targets.append(values)
    return arrays,idx,targets

def stable_metadata(doc):
    data=copy.deepcopy(doc)
    for key in ('buffers','bufferViews','accessors'):data.pop(key,None)
    for mesh in data.get('meshes',[]):
        for primitive in mesh['primitives']:
            primitive['indices']='preserved-corner-source-lineage'
            primitive['attributes']={key:'copied-row' for key in primitive['attributes']}
            primitive['targets']=[{key:'copied-morph-row' for key in target} for target in primitive.get('targets',[])]
    return data

def split_asset(native,source_path:Path,output_path:Path,report_path:Path):
    source_path,output_path,report_path=safe_outputs(source_path,output_path,report_path,getattr(native,'path',None))
    source=admitted_source(source_path);identity=sha(source_path);doc=copy.deepcopy(source.doc);binary=bytearray(source.binary)
    rows=[];plans={};new_vertex_total=0
    def append(spec,array):
        while len(binary)%4:binary.append(0)
        view={'buffer':0,'byteOffset':len(binary),'byteLength':array.nbytes};doc['bufferViews'].append(view);binary.extend(np.ascontiguousarray(array).tobytes())
        metadata=copy.deepcopy(spec)
        for field in ('sparse','byteOffset'):metadata.pop(field,None)
        metadata['bufferView']=len(doc['bufferViews'])-1;metadata['count']=len(array)
        doc['accessors'].append(metadata);return len(doc['accessors'])-1
    for mi,pi,primitive in source.primitives():
        arrays,idx,targets=read_domain(source,primitive)
        result=diagnose(native,arrays['POSITION'],source.array(primitive['attributes']['NORMAL'],True),source.array(primitive['attributes']['TEXCOORD_0'],True),idx)
        plan=plan_split(result['indices'],result['corner_tangents'],result['valid_corner_mask'],len(arrays['POSITION']))
        row={'mesh':mi,'primitive':pi,'material':source.doc['materials'][primitive['material']].get('name'),'before':result['summary'],
             'duplicates':len(plan['duplicates']),'cloneMapping':plan['changes'],'sourceVertices':len(arrays['POSITION']),'afterVertices':len(arrays['POSITION'])+len(plan['duplicates'])}
        plans[(mi,pi)]=(plan,arrays,targets,result);rows.append(row)
        if not len(plan['duplicates']):continue
        new_vertex_total+=len(plan['duplicates']);p=doc['meshes'][mi]['primitives'][pi];duplicates=plan['duplicates']
        for semantic,ai in primitive['attributes'].items():
            value=np.concatenate([arrays[semantic],arrays[semantic][duplicates]],axis=0)
            p['attributes'][semantic]=append(source.doc['accessors'][ai],value)
        for ti,target in enumerate(primitive.get('targets',[])):
            for semantic,ai in target.items():
                value=np.concatenate([targets[ti][semantic],targets[ti][semantic][duplicates]],axis=0)
                p['targets'][ti][semantic]=append(source.doc['accessors'][ai],value)
        spec=copy.deepcopy(source.doc['accessors'][primitive['indices']]);spec['componentType']=5125;spec.pop('normalized',None)
        if 'min'in spec:spec['min']=[int(plan['indices'].min())]
        if 'max'in spec:spec['max']=[int(plan['indices'].max())]
        p['indices']=append(spec,plan['indices'].astype('<u4').reshape(-1,1))
    report={'schema':1,'kind':'exact-valid-corner-topology-split','source':str(source_path.resolve()),'sourceSha256':identity,'nativeBuild':native.receipt,'generatorSha256':sha(Path(__file__)),
            'admission':{'validator':'repair_mesh.read_checked plus all-accessor finite validation','validatorSourceSha256':sha(HERE/'repair_mesh.py'),'candidateOutsideNativeProject':True,'resolvedFreshExclusiveOutputs':True},
            'candidateWritten':False,'noOp':not new_vertex_total,'duplicatedVertices':new_vertex_total,'domains':rows,
            'scope':'Topology preparation only. Every base attribute including original TANGENT, COLOR masks, skin and every morph row is copied byte-for-byte. No generated Mikk frame is written to the asset. Unresolved corners retain their source indices.',
            'limits':['UV/geometry degenerates and invalid clean Mikk outputs remain unresolved.','No shader/material/render or runtime promotion acceptance. A later tangent rebake requires separate preserved-morph/frame and native A/B acceptance.','Append-only authoring candidate retains unused original buffer data; file size is not an optimized delivery budget.']}
    if new_vertex_total:
        doc['buffers'][0]['byteLength']=len(binary)
        raw_json=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();raw_json+=b' '*(-len(raw_json)%4);binary+=b'\0'*(-len(binary)%4)
        raw=struct.pack('<4sII',b'glTF',2,28+len(raw_json)+len(binary))+struct.pack('<II',len(raw_json),0x4e4f534a)+raw_json+struct.pack('<II',len(binary),0x004e4942)+binary
        output_path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='yuga-seam-proof-',dir=output_path.parent) as scratch:
            provisional=Path(scratch)/'candidate.glb';provisional.write_bytes(raw);candidate=admitted_source(provisional)
            if candidate.binary[:len(source.binary)]!=source.binary or candidate.doc['accessors'][:len(source.doc['accessors'])]!=source.doc['accessors'] or candidate.doc['bufferViews'][:len(source.doc['bufferViews'])]!=source.doc['bufferViews']:raise ValueError('Original binary/accessor/view prefix changed')
            if stable_metadata(source.doc)!=stable_metadata(candidate.doc):raise ValueError('Non-topology metadata changed')
            for row in rows:
                key=(row['mesh'],row['primitive']);plan,old_arrays,old_targets,before=plans[key];p=candidate.doc['meshes'][key[0]]['primitives'][key[1]]
                arrays,new_idx,targets=read_domain(candidate,p);mapping=np.concatenate([np.arange(len(old_arrays['POSITION']),dtype=np.uint32),plan['duplicates']])
                if not np.array_equal(mapping[new_idx],before['indices']):raise ValueError('Corner source lineage changed')
                for semantic,value in old_arrays.items():
                    if arrays[semantic].tobytes()!=value[mapping].tobytes():raise ValueError('Attribute row copy mismatch: '+semantic)
                for ti,target in enumerate(old_targets):
                    for semantic,value in target.items():
                        if targets[ti][semantic].tobytes()!=value[mapping].tobytes():raise ValueError('Morph row copy mismatch: '+semantic)
                after=diagnose(native,arrays['POSITION'],candidate.array(p['attributes']['NORMAL'],True),candidate.array(p['attributes']['TEXCOORD_0'],True),new_idx)
                if after['summary']['ambiguousSourceVertices']:raise ValueError('Indexed corner conflict remains after exact split')
                if not np.array_equal(before['valid_corner_mask'],after['valid_corner_mask']) or not np.array_equal(before['corner_tangents'],after['corner_tangents'],equal_nan=True):raise ValueError('Per-corner native result/classification changed despite copied inputs')
                row['after']=after['summary'];row['allAttributeMorphRowsExact']=True;row['originalTangentsPreserved']=True;row['unresolvedCornerIndicesUnchanged']=bool(np.array_equal(new_idx[~before['valid_corner_mask']],before['indices'][~before['valid_corner_mask']]))
            for image in source.doc.get('images',[]):
                if source.image(image)!=candidate.image(image):raise ValueError('Embedded image changed')
        with output_path.open('xb') as handle:handle.write(raw)
        report.update(candidateWritten=True,candidate={'path':str(output_path.resolve()),'sha256':sha(output_path),'bytes':len(raw),'sourceBytes':len(source.raw),'growthBytes':len(raw)-len(source.raw),
                       'sourceBinaryPrefixIdentical':True,'originalAccessorViewMetadataIdentical':True,'rigClipsMaterialsImagesFaceOwnershipIdentical':True})
    else:
        for row in rows:row['after']=row['before']
    report['sourceAfterSha256']=sha(source_path);report['sourceUnchanged']=identity==report['sourceAfterSha256']
    if not report['sourceUnchanged']:raise ValueError('Source changed during candidate operation')
    report['beforeConflictVertices']=sum(row['before']['ambiguousSourceVertices'] for row in rows);report['afterConflictVertices']=sum(row['after']['ambiguousSourceVertices'] for row in rows)
    report['remainingUnresolvedCorners']=sum(row['after']['unresolvedCorners'] for row in rows)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    with report_path.open('x') as handle:handle.write(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--library',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if not args.output.is_absolute() or not args.report.is_absolute():parser.error('--output/--report must be absolute fresh paths')
    result=split_asset(NativeMikk(args.library),args.source,args.output,args.report)
    print(json.dumps({key:result[key] for key in ['candidateWritten','noOp','duplicatedVertices','beforeConflictVertices','afterConflictVertices','remainingUnresolvedCorners','sourceUnchanged']},indent=2))

if __name__=='__main__':main()
