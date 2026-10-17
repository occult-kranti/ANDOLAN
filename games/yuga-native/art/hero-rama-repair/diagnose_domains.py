#!/usr/bin/env python3
"""Read-only Rama UV/geometry/corner diagnosis; never rewrite UVs or assets.

Reports rest-pose geometric facts separately from source-authoring hypotheses
and native screen visibility, which requires a subsequent controlled render.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'hero-rama-lod'))
from glb_lod import GLB
ABS_EPS=1e-12
REL_EPS=1e-10

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def classify(p,uv,idx,skin_arrays=(),morph_positions=(),color=None,all_attributes=(),all_morph_channels=()):
    """Exact pair proof covers skeletal/morph position only, not shaders."""
    p=np.asarray(p,dtype=np.float64);uv=np.asarray(uv,dtype=np.float64);idx=np.asarray(idx)
    if p.ndim!=2 or p.shape[1]!=3 or uv.shape!=(len(p),2) or idx.dtype.kind not in 'iu' or idx.ndim!=1 or len(idx)%3:raise ValueError('Malformed position/UV/index domain')
    if not np.isfinite(p).all() or not np.isfinite(uv).all() or int(idx.min(initial=0))<0 or int(idx.max(initial=0))>=len(p):raise ValueError('Nonfinite or out-of-range source domain')
    faces=idx.reshape(-1,3);xyz=p[faces];tex=uv[faces]
    e1=xyz[:,1]-xyz[:,0];e2=xyz[:,2]-xyz[:,0];area=np.linalg.norm(np.cross(e1,e2),axis=1)
    a=tex[:,1]-tex[:,0];b=tex[:,2]-tex[:,0];det=a[:,0]*b[:,1]-a[:,1]*b[:,0]
    max_edge_sq=np.maximum.reduce([np.einsum('ij,ij->i',e1,e1),np.einsum('ij,ij->i',e2,e2),np.sum((xyz[:,2]-xyz[:,1])**2,axis=1)])
    uv_scale_sq=np.maximum(np.max(np.abs(a),axis=1),np.max(np.abs(b),axis=1))**2
    geom=area<=ABS_EPS;uv_bad=np.abs(det)<=ABS_EPS
    relative_area=np.divide(area,max_edge_sq,out=np.zeros_like(area),where=max_edge_sq>0)
    relative_uv=np.divide(np.abs(det),uv_scale_sq,out=np.zeros_like(det),where=uv_scale_sq>0)
    repeated=np.zeros(len(faces),bool);coincident=np.zeros(len(faces),bool);proof=np.zeros(len(faces),bool);coincident_color_diff=np.zeros(len(faces),bool)
    strict=np.zeros(len(faces),bool);core_color=np.zeros(len(faces),bool)
    attributes=[np.asarray(value) for value in skin_arrays]+[np.asarray(value) for value in morph_positions]
    byte_records=[]
    for value in (*all_attributes,*all_morph_channels):
        value=np.ascontiguousarray(value)
        if len(value)!=len(p):raise ValueError('Malformed complete-record proof domain')
        byte_records.append(value.view(np.uint8).reshape(len(p),-1))
    if any(len(value)!=len(p) or not np.isfinite(value).all() for value in attributes):raise ValueError('Malformed skin/morph proof domain')
    for left,right in ((0,1),(1,2),(2,0)):
        ia,ib=faces[:,left],faces[:,right]
        repeated|=ia==ib
        pair=np.all(p[ia]==p[ib],axis=1);coincident|=pair;exact=pair.copy()
        for value in attributes:exact&=np.all(value[ia]==value[ib],axis=1)
        proof|=exact
        if color is not None:coincident_color_diff|=pair&np.any(color[ia]!=color[ib],axis=1)
        if color is not None:core_color|=exact&np.all(color[ia]==color[ib],axis=1)
        all_equal=pair.copy()
        for value in byte_records:all_equal&=np.all(value[ia]==value[ib],axis=1)
        if byte_records:strict|=all_equal
    onepoint=np.all(tex[:,0]==tex[:,1],axis=1)&np.all(tex[:,0]==tex[:,2],axis=1)
    constant_u=np.all(tex[:,:,0]==tex[:,0:1,0],axis=1);constant_v=np.all(tex[:,:,1]==tex[:,0:1,1],axis=1)
    candidates=uv_bad&~geom
    masks={'geometryAbsoluteDegenerate':geom,'geometryExactlyZero':area==0,'geometryEpsilonOnly':geom&(area>0),
           'geometryScaleRelativeSliver':relative_area<=REL_EPS,'uvAbsoluteDegenerate':uv_bad,'uvExactlyZeroDeterminant':det==0,'uvEpsilonOnly':uv_bad&(det!=0),
           'uvScaleRelativeSliver':relative_uv<=REL_EPS,'geometryUVUnion':geom|uv_bad,'repeatedSourceIndex':repeated,'identicalPositionPair':coincident,
           'skeletalMorphCoincidentPair':proof,'restDegenerateNotSkeletalMorphProven':geom&~proof,
           'skeletalMorphColor0CoincidentPair':core_color,'allAttributeMorphByteIdenticalPair':strict,
           'uvPointCollapsed':uv_bad&onepoint,'uvCollinearNonpoint':uv_bad&~onepoint,'uvConstantU':uv_bad&constant_u,'uvConstantV':uv_bad&constant_v,
           'uvDegenerateWithNondegenerateGeometry':candidates,'uvDegenerateNonzeroSurfaceNotRemovableByPairProof':candidates&~proof,
           'coincidentPairDifferentColorMask':coincident_color_diff}
    surface=area*.5;total=float(surface.sum())
    def subset(mask):
        ids=np.flatnonzero(mask);bounds=None
        if len(ids):
            vertices=xyz[mask].reshape(-1,3);bounds={'minimum':vertices.min(axis=0).tolist(),'maximum':vertices.max(axis=0).tolist()}
        area_sum=float(surface[mask].sum())
        return {'faces':len(ids),'restSurfaceArea':area_sum,'shareOfPrimitiveRestArea':area_sum/total if total else 0.,'boundsLocal':bounds,'exampleFaceIds':ids[:12].tolist()}
    summary={'triangles':len(faces),'vertices':len(p),'totalRestSurfaceArea':total,'counts':{key:int(mask.sum()) for key,mask in masks.items()},
             'surfaceDomains':{key:subset(masks[key]) for key in ['geometryUVUnion','uvDegenerateWithNondegenerateGeometry','uvDegenerateNonzeroSurfaceNotRemovableByPairProof','restDegenerateNotSkeletalMorphProven']}}
    return {'summary':summary,'masks':masks,'faces':faces,'double_area':area,'uv_determinant':det,'uvs':uv,'positions':p}

def corner_detail(domain,normals,corner,tangent=None):
    face=int(corner)//3;ids=domain['faces'][face];vertex=int(ids[int(corner)%3]);p=domain['positions'][ids];uv=domain['uvs'][ids]
    determinant=float(domain['uv_determinant'][face]);normal=np.asarray(normals[vertex],dtype=float)
    derivative=None
    if abs(determinant)>ABS_EPS:
        a,b=uv[1]-uv[0],uv[2]-uv[0];t=((p[1]-p[0])*b[1]-(p[2]-p[0])*a[1])/determinant
        # Normal is not modified. This projection is diagnostic only, not a
        # substitute for the official corner-averaged Mikk algorithm.
        nn=float(np.dot(normal,normal));projected=t-normal*(float(np.dot(normal,t))/nn)
        derivative={'faceDerivative':t.tolist(),'derivativeLength':float(np.linalg.norm(t)),
                    'normalProjectedDerivativeLength':float(np.linalg.norm(projected)),
                    'projectionRatio':float(np.linalg.norm(projected)/np.linalg.norm(t)) if np.linalg.norm(t)>0 else 0.}
    # Same explicit float32 dot, reciprocal-then-multiply normalization and
    # projected edge-angle formula as pinned Mikk EvalTspace (1390-1425).
    # This records conditioning; it does not replace a native algorithm trace.
    p32=p.astype(np.float32);n32=normal.astype(np.float32);k=int(corner)%3
    dot32=lambda a,b:np.float32(np.float32(a[0]*b[0]+a[1]*b[1])+a[2]*b[2])
    v1=p32[(k+2)%3]-p32[k];v2=p32[(k+1)%3]-p32[k]
    v1=v1-n32*dot32(n32,v1);v2=v2-n32*dot32(n32,v2)
    for value in (v1,v2):
        length=np.sqrt(dot32(value,value))
        if length>0:value*=np.float32(1)/length
    cosine=dot32(v1,v2);angle=float(np.arccos(np.clip(float(cosine),-1.,1.)))
    face_cross=np.cross(p[1]-p[0],p[2]-p[0]);face_length=np.linalg.norm(face_cross)
    frame_condition={'float32ProjectedEdgeCosine':float(cosine),'float32ClampedCornerWeightRadians':angle,
                     'normalDotGeometricFaceNormal':float(np.dot(normal,face_cross/face_length)/np.linalg.norm(normal)) if face_length>0 else None,
                     'formulaSource':'Pinned MikkTSpace EvalTspace projected edge angle; float32 dot/reciprocal normalization reproduced, not runtime instrumentation.'}
    return {'corner':int(corner),'face':face,'sourceVertex':vertex,'sourceIndices':ids.tolist(),'positionsLocal':p.tolist(),'uvs':uv.tolist(),'normal':normal.tolist(),
            'geometryDoubleArea':float(domain['double_area'][face]),'uvDeterminant':determinant,'mikkTangent':None if tangent is None else np.asarray(tangent).tolist(),'analyticDerivativeDiagnostic':derivative,'cornerWeightConditioning':frame_condition}

def author_ledger(paths):
    """Read text only; no bpy imports or claimed editable-mesh object mapping."""
    result=[]
    terms=('def tube','def ellipsoid','def cloth','def solid','def lock','def join_group','faces.extend','fs.extend','uv.append','uvs.append','uv[index]','modifier_apply')
    for path in paths:
        lines=path.read_text().splitlines();evidence=[{'line':i+1,'text':line.strip()} for i,line in enumerate(lines) if any(term in line for term in terms)]
        result.append({'path':str(path.resolve()),'sha256':sha(path),'textEvidence':evidence,'executed':False})
    return result

def probe_zero(native,domain,normals,corner):
    """Bounded actual-library contrast, not an invented replacement tangent."""
    p=np.ascontiguousarray(domain['positions'],dtype=np.float32);uv=np.ascontiguousarray(domain['uvs'],dtype=np.float32);n=np.ascontiguousarray(normals,dtype=np.float32)
    faces=domain['faces'];face=corner//3;vertex=int(faces[face,corner%3]);one=np.ascontiguousarray(faces[face],dtype=np.uint32)
    isolated=native.generate_validated(p,n,uv,one)[corner%3]
    equivalent=np.flatnonzero(np.all(p==p[vertex],axis=1)&np.all(n==n[vertex],axis=1)&np.all(uv==uv[vertex],axis=1))
    clean=~domain['masks']['geometryUVUnion'];near=np.flatnonzero(np.isin(faces,equivalent).any(axis=1)&clean)
    subset=np.ascontiguousarray(faces[near].reshape(-1),dtype=np.uint32);outputs=native.generate_validated(p,n,uv,subset)
    picked=np.flatnonzero(np.isin(subset,equivalent))
    return {'nativeBinarySha256':native.receipt['binarySha256'],'isolatedFaceCorner':isolated.tolist(),'isolatedFaceTangentLength':float(np.linalg.norm(isolated[:3])),
            'matchingPositionNormalUVVertices':equivalent.tolist(),'cleanIncidentFaceCount':len(near),'cleanIncidentFaceIds':near.tolist(),
            'incidentTupleCornerOutputs':[{'face':int(near[c//3]),'vertex':int(subset[c]),'tangent':outputs[c].tolist(),'tangentLength':float(np.linalg.norm(outputs[c,:3]))} for c in picked],
            'interpretation':'Isolated and incident-subset outputs are actual native calls. Zero already on an isolated face rules out a requirement for large-mesh cancellation; compare the source-matched float32 projected corner-weight conditioning. This does not instrument an internal branch or authorize replacement.'}

def analyze(source_path,report_path,mikk_report=None,corners_path=None,author_sources=(),library_path=None):
    source_path=Path(source_path);report_path=Path(report_path)
    if report_path.resolve()==source_path.resolve() or (report_path.exists() and os.path.samefile(report_path,source_path)):raise ValueError('Report aliases immutable input')
    if report_path.exists():raise ValueError('Use fresh report path')
    g=GLB(source_path);identity=sha(source_path);mikk=None;archive=None
    if mikk_report is not None:
        mikk=json.loads(Path(mikk_report).read_text())
        if mikk['sourceSha256']!=identity:raise ValueError('Mikk report is for another asset')
    if corners_path is not None:
        if mikk is None or sha(corners_path)!=mikk['cornerArchive']['sha256']:raise ValueError('Corner archive identity mismatch')
        archive=np.load(corners_path,allow_pickle=False)
    native=None
    if library_path is not None:
        sys.path.insert(0,str(HERE.parent/'hero-rama-tangents'))
        from mikk_frames import NativeMikk
        native=NativeMikk(library_path)
    output=[]
    for mi,pi,primitive in g.primitives():
        attrs=primitive['attributes'];material=g.doc.get('materials',[])[primitive['material']];name=f'mesh{mi}-primitive{pi}'
        if primitive.get('mode',4)!=4 or not {'POSITION','NORMAL','TEXCOORD_0'}<=attrs.keys():raise ValueError('Unsupported source domain '+name)
        if any(g.doc['accessors'][attrs[key]]['count']>2_000_000 for key in ('POSITION','NORMAL','TEXCOORD_0')) or g.doc['accessors'][primitive['indices']]['count']>6_000_000:raise ValueError('Oversized source domain')
        p=g.array(attrs['POSITION']);uv=g.array(attrs['TEXCOORD_0']);normals=g.array(attrs['NORMAL']);idx=g.array(primitive['indices']).reshape(-1)
        skin_keys=sorted(key for key in attrs if key.startswith(('JOINTS_','WEIGHTS_')))
        if any(('WEIGHTS_'+key[7:]) not in attrs for key in skin_keys if key.startswith('JOINTS_')) or any(('JOINTS_'+key[8:]) not in attrs for key in skin_keys if key.startswith('WEIGHTS_')):raise ValueError('Unpaired skin set')
        morphs=[g.array(target['POSITION']) for target in primitive.get('targets',[]) if 'POSITION'in target]
        domain=classify(p,uv,idx,[g.array(attrs[key]) for key in skin_keys],morphs,g.array(attrs['COLOR_0']) if 'COLOR_0'in attrs else None,
                        [g.array(ai) for ai in attrs.values()],[g.array(ai) for target in primitive.get('targets',[]) for ai in target.values()])
        row={'mesh':mi,'primitive':pi,'meshName':g.doc['meshes'][mi].get('name'),'material':material.get('name'),'hasNormalTexture':'normalTexture'in material,
             'skinAttributeSets':skin_keys,'positionMorphTargets':len(morphs),**domain['summary'],'mikkCornerConflicts':[],'invalidCleanOutputCorners':[]}
        if mikk is not None:
            prior=next(value for value in mikk['domains'] if value['mesh']==mi and value['primitive']==pi)
            if row['counts']['geometryUVUnion']!=prior.get('degenerateUnionFaces'):raise ValueError('Independent domain union disagrees with pinned Mikk diagnostic')
            row['mikkSummary']={key:prior.get(key) for key in ['ambiguousSourceVertices','invalidOutputOnCleanCorners','unresolvedCorners','degenerateUnionFaces']}
            if archive is not None:
                ai=archive[name+'-source-indices'];t=archive[name+'-tangents'];valid=archive[name+'-valid-mask']
                if not np.array_equal(ai,idx) or t.shape!=(len(idx),4) or valid.shape!=(len(idx),):raise ValueError('Corner archive domain mismatch')
                for example in prior.get('exampleCornerConflicts',[]):
                    vertex=example['vertex'];ids=np.flatnonzero((idx==vertex)&valid)
                    vectors=t[ids,:3].astype(np.float64);lengths=np.linalg.norm(vectors,axis=1);units=vectors/lengths[:,None]
                    cosine=np.clip(units@units.T,-1.,1.)
                    angular=float(np.degrees(np.arccos(cosine)).max(initial=0))
                    max_component=float(np.abs(vectors[:,None,:]-vectors[None,:,:]).max(initial=0))
                    row['mikkCornerConflicts'].append({**example,'maximumPairwiseAngleDegrees':angular,'maximumPairwiseFloat32ComponentDelta':max_component,
                                                     'corners':[corner_detail(domain,normals,int(c),t[c]) for c in ids]})
                extra=np.flatnonzero(np.isfinite(t).all(axis=1)&~valid)
                row['invalidCleanOutputCorners']=[corner_detail(domain,normals,int(c),t[c]) for c in extra]
                if native is not None:
                    for detail in row['invalidCleanOutputCorners']:detail['boundedNativeContrast']=probe_zero(native,domain,normals,detail['corner'])
        output.append(row)
    keys=next(iter(output))['counts'].keys() if output else ()
    totals={key:sum(row['counts'][key] for row in output) for key in keys}
    report={'schema':1,'kind':'read-only-uv-and-deformation-domain-diagnosis','source':str(source_path.resolve()),'sourceSha256':identity,'sourceAfterSha256':sha(source_path),'sourceUnchanged':identity==sha(source_path),
            'diagnosticSourceSha256':sha(Path(__file__)),'readerSha256':sha(HERE.parent/'hero-rama-lod/glb_lod.py'),'totals':totals,'domains':output,
            'mikkEvidence':None if mikk_report is None else {'path':str(Path(mikk_report).resolve()),'sha256':sha(mikk_report),'cornerArchiveSha256':None if corners_path is None else sha(corners_path)},
            'authorSourceText':author_ledger(author_sources),
            'policies':{'absoluteEpsilon':ABS_EPS,'scaleRelativeSliverEpsilon':REL_EPS,'coincidenceProof':'skeletalMorphCoincidentPair is the weaker exact POSITION+all JOINTS/WEIGHTS+all POSITION morph proof, not universal removal permission. allAttributeMorphByteIdenticalPair independently requires every base attribute and every morph channel byte-identical. Color0-equal core pairs are separately counted; any shader-specific acceptance needs the exact shader pin and separate contract.','UVPreservation':'No UV values, geometry, indices, skin, morphs, metadata or runtime files changed.'},
            'interpretation':{'measured':'UV-degenerate triangles with nonzero rest area are material-frame risk on real surface; measured area/bounds do not prove screen visibility.','sourceMechanisms':['Tube and lock cap vertices reuse same longitudinal V; cap polygons therefore have collinear UVs despite nonzero 3D cap area.','Ellipsoid parameter grids duplicate pole coordinates; some pole triangles have zero geometric area.','Solidify can create side walls with copied front/back UVs; this is a source hypothesis until exact editable face mapping is inspected.'],
                              'limits':['Joined GLB nodes retain mesh/material identity but not original Blender object-to-face ranges. Source text mechanisms cannot uniquely label an exported face as an intentional cap.','No Blender, render, occlusion, backface/shadow visibility or posed animation execution. Rest area and bounds are not screen coverage.','Analytic per-face derivative is not the official averaged Mikk frame and is never written as a replacement.','No arbitrary UV rewrite, unsafe rest-area triangle deletion, tangent averaging or asset promotion.']}}
    if not report['sourceUnchanged']:raise ValueError('Source changed during read-only diagnosis')
    report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    if archive is not None:archive.close()
    return report

def self_test():
    checks=[]
    def check(name,ok):
        checks.append({'name':name,'passed':bool(ok)})
    p=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
    uv=np.array([[0.,0.],[1.,0.],[0.,1.]])
    idx=np.array([0,1,2],dtype=np.uint32)
    a=classify(p,uv,idx);check('clean triangle',a['summary']['counts']['geometryUVUnion']==0)
    cap=classify(p,np.array([[0.,0.],[.5,0.],[1.,0.]]),idx)
    check('cap UV line has nonzero surface area',cap['summary']['counts']['uvDegenerateWithNondegenerateGeometry']==1)
    check('UV cap not removable by rest-pair proof',cap['summary']['counts']['skeletalMorphCoincidentPair']==0)
    p2=p.copy();p2[1]=p2[0]
    same=np.tile([1.,0.,0.,0.],(3,1));different=same.copy();different[1]=[0,1,0,0]
    check('coincident weights prove skeletal coincidence',classify(p2,uv,idx,[same])['summary']['counts']['skeletalMorphCoincidentPair']==1)
    check('different weights prevent any-pose proof',classify(p2,uv,idx,[different])['summary']['counts']['skeletalMorphCoincidentPair']==0)
    morph=np.zeros_like(p);morph[1]=[1,0,0]
    check('different position morph prevents proof',classify(p2,uv,idx,[same],[morph])['summary']['counts']['skeletalMorphCoincidentPair']==0)
    check('UV seam blocks strict complete-record coincidence',classify(p2,uv,idx,[same],all_attributes=[p2,uv,same])['summary']['counts']['allAttributeMorphByteIdenticalPair']==0)
    check('core and equal mask coincidence explicitly weaker than strict',classify(p2,uv,idx,[same],color=same,all_attributes=[p2,uv,same])['summary']['counts']['skeletalMorphColor0CoincidentPair']==1)
    line=np.array([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]])
    check('collinear rest shape without duplicate not removable',classify(line,uv,idx)['summary']['counts']['restDegenerateNotSkeletalMorphProven']==1)
    tiny=classify(p*1e-8,uv,idx)
    check('epsilon-only geometry distinguished from exact zero',tiny['summary']['counts']['geometryEpsilonOnly']==1 and tiny['summary']['counts']['geometryExactlyZero']==0)
    check('relative sliver metric independent of global scale',tiny['summary']['counts']['geometryScaleRelativeSliver']==0)
    detail=corner_detail(a,np.tile([0.,0.,1.],(3,1)),0)
    check('analytic derivative oracle',np.allclose(detail['analyticDerivativeDiagnostic']['faceDerivative'],[1,0,0]))
    check('repeated source index proves coincidence',classify(p,uv,np.array([0,0,2],dtype=np.uint32))['summary']['counts']['skeletalMorphCoincidentPair']==1)
    return {'schema':1,'kind':'uv-domain-diagnostic-self-test','passed':all(row['passed'] for row in checks),'checks':checks,'count':len(checks),'sourceSha256':sha(Path(__file__))}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path);parser.add_argument('--report',required=True,type=Path);parser.add_argument('--mikk-report',type=Path);parser.add_argument('--corners',type=Path);parser.add_argument('--library',type=Path);parser.add_argument('--author-source',action='append',default=[],type=Path);parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if not args.report.is_absolute() or args.report.exists():parser.error('--report must be a fresh absolute path')
    if args.self_test:
        report=self_test();args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':report['count'],'report':str(args.report)}));raise SystemExit(0 if report['passed'] else 1)
    if args.source is None:parser.error('--source required unless --self-test')
    report=analyze(args.source,args.report,args.mikk_report,args.corners,args.author_source,args.library);print(json.dumps({'sourceUnchanged':report['sourceUnchanged'],'totals':report['totals'],'report':str(args.report)},indent=2))

if __name__=='__main__':main()
