#!/usr/bin/env python3
"""Independent bounded software/data checks; no engine, import or promotion."""
import argparse,copy,hashlib,json,os,struct,subprocess,sys,tempfile,time
from pathlib import Path
import numpy as np
PROJECT=Path(__file__).resolve().parents[4]
TOOLS=PROJECT/'art/hero-rama-repair'
sys.path.insert(0,str(TOOLS))
import repair_mesh as repair
import split_seams as seams
LIB=Path('/workspace/tooling/mikktspace-yuga-r1/libyuga_mikktspace.so')
PINS={'assets/heroes/rama-hero.glb':'de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5','assets/heroes/rama-hero-mid.glb':'40737faf61e660f74dbb97b7a5a507869fdedd1a27cd964bb15e27e445a2d3cd','assets/heroes/rama-hero-far.glb':'d5888a452c2a8b711a7a5d8542652762d73c2608047b0399a2486c9ed650f9aa','shaders/rama_secondary_cloth.gdshader':'c1712f075af34b0e57dd7f70e5494c2060703e7f1ee68ff87c8a645cff95c6d7'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encode(path,doc,binary):
    data=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();data+=b' '*(-len(data)%4);binary=bytes(binary)+b'\0'*(-len(binary)%4)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(data)+len(binary))+struct.pack('<II',len(data),0x4e4f534a)+data+struct.pack('<II',len(binary),0x004e4942)+binary)
def fixture(path,repeat=False):
    # Non-uniform geometry and a reflected UV chart give opposite handedness
    # at shared source vertex 0. Tangents intentionally carry an old sentinel.
    p=np.array([[0,0,0],[2,0,0],[0,3,0],[-2,0,0],[0,-3,0]],dtype='<f4')
    n=np.tile([0,0,1],(5,1)).astype('<f4');t=np.tile([0,1,0,-1],(5,1)).astype('<f4')
    inter=np.concatenate([p,n,t],axis=1);uv=np.array([[0,0],[1,0],[0,1],[1,0],[0,-1]],dtype='<f4')
    binary=bytearray();views=[];acc=[]
    def view(a,stride=None):
        while len(binary)%4:binary.append(0)
        v={'buffer':0,'byteOffset':len(binary),'byteLength':a.nbytes}
        if stride:v['byteStride']=stride
        views.append(v);binary.extend(a.tobytes());return len(views)-1
    def a(value,kind,ct=5126):
        vi=view(np.ascontiguousarray(value));acc.append({'bufferView':vi,'componentType':ct,'type':kind,'count':len(value)});return len(acc)-1
    vi=view(inter,40);attrs={}
    for semantic,offset,kind in [('POSITION',0,'VEC3'),('NORMAL',12,'VEC3'),('TANGENT',24,'VEC4')]:
        attrs[semantic]=len(acc);acc.append({'bufferView':vi,'byteOffset':offset,'componentType':5126,'type':kind,'count':5})
    attrs['TEXCOORD_0']=a(uv,'VEC2');attrs['TEXCOORD_1']=attrs['TEXCOORD_0']
    attrs['COLOR_0']=a(np.tile([255,255,255,128],(5,1)).astype('u1'),'VEC4',5121);acc[-1]['normalized']=True
    attrs['JOINTS_0']=a(np.zeros((5,4),dtype='<u2'),'VEC4',5123)
    attrs['WEIGHTS_0']=a(np.tile([1,0,0,0],(5,1)).astype('<f4'),'VEC4')
    sparse_i=view(np.array([0,4],dtype='u1'));sparse_v=view(np.array([[.125,0,0],[0,.25,0]],dtype='<f4'))
    morph=len(acc);acc.append({'componentType':5126,'type':'VEC3','count':5,'sparse':{'count':2,'indices':{'bufferView':sparse_i,'componentType':5121},'values':{'bufferView':sparse_v}}})
    index=[0,1,2,0,3,4]+([0,0,1] if repeat else []);ii=a(np.array(index,dtype='<u2').reshape(-1,1),'SCALAR',5123)
    inv=a(np.eye(4,dtype='<f4').reshape(1,16),'MAT4')
    prim={'attributes':attrs,'indices':ii,'material':0,'targets':[{'POSITION':morph}]}
    doc={'asset':{'version':'2.0','generator':'Independent QA reflected-chart + interleaved sparse fixture'},'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':acc,'materials':[{'name':'QA cloth'}],'meshes':[{'name':'RamaFace','primitives':[prim],'weights':[0],'extras':{'targetNames':['QA morph']}}],'nodes':[{'name':'Root'},{'name':'QA face','mesh':0,'skin':0}],'skins':[{'joints':[0],'inverseBindMatrices':inv}],'scenes':[{'nodes':[0,1]}],'scene':0}
    encode(path,doc,binary);return doc,bytes(binary)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    if not args.report.is_absolute() or args.report.exists():ap.error('fresh absolute report required')
    checks=[];sources={str(p.relative_to(PROJECT)):sha(p) for p in [TOOLS/'repair_mesh.py',TOOLS/'split_seams.py',PROJECT/'art/hero-rama-tangents/regenerate.py',PROJECT/'art/hero-rama-lod/glb_lod.py']};runtime_before={p:sha(PROJECT/p) for p in PINS}
    def yes(x,msg='independent contract failed'):
        if not x:raise AssertionError(msg)
    def run(cmd):
        r=subprocess.run([sys.executable,*map(str,cmd)],capture_output=True,text=True,timeout=30)
        return {'command':[sys.executable,*map(str,cmd)],'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    def check(name,fn):
        try:detail=fn();checks.append({'name':name,'passed':True,'detail':detail})
        except Exception as e:checks.append({'name':name,'passed':False,'error':type(e).__name__+': '+str(e)})
    with tempfile.TemporaryDirectory(prefix='qa-art-adversarial-') as temporary:
        tmp=Path(temporary);source=tmp/'independent-source.glb';doc,binary=fixture(source,True)
        repaired=tmp/'repaired.glb';repair_report=tmp/'repair.json'
        def positive_repair():
            r=run([TOOLS/'repair_mesh.py',source,'--candidate',repaired,'--report',repair_report]);yes(r['exit_code']==0,r['stderr']);d=json.loads(repair_report.read_text());yes(d['removedPairProven']==1 and d['trianglesBefore']==3 and d['trianglesAfter']==2);yes(d['preservation']['oldBinaryPrefixExact']);return r
        check('CLI strict removes only repeated-index face in independent interleaved+sparse fixture',positive_repair)
        split=tmp/'split.glb';split_report=tmp/'split.json'
        def positive_seam():
            old=seams.GLB(repaired);r=run([TOOLS/'split_seams.py','--source',repaired,'--library',LIB,'--output',split,'--report',split_report]);yes(r['exit_code']==0,r['stderr']);d=json.loads(split_report.read_text());yes(d['duplicatedVertices']==1 and d['beforeConflictVertices']==1 and d['afterConflictVertices']==0)
            new=seams.GLB(split);op=old.doc['meshes'][0]['primitives'][0];np_=new.doc['meshes'][0]['primitives'][0];mapping=np.array([0,1,2,3,4,0]);yes(new.array(np_['indices']).reshape(-1).tolist()==[0,1,2,5,3,4]);yes(new.binary[:len(old.binary)]==old.binary)
            for semantic,ai in op['attributes'].items():yes(old.array(ai)[mapping].tobytes()==new.array(np_['attributes'][semantic]).tobytes(),semantic)
            for semantic,ai in op['targets'][0].items():yes(old.array(ai)[mapping].tobytes()==new.array(np_['targets'][0][semantic]).tobytes(),'morph '+semantic)
            yes(new.doc['nodes']==old.doc['nodes'] and new.doc['skins']==old.doc['skins']);return {'process':r,'asserted':'All attrs and sparse morph independently equal old[[0,1,2,3,4,0]], TANGENT sentinel exact, interleaved/shared UV storage handled; source face/skin same.'}
        check('CLI seam splits reflected handedness while preserving all interleaved/sparse/shared rows',positive_seam)
        # Real malformed storage, not source-string inspection. Each must refuse
        # before publication; input byte identity is independently checked.
        mutations=[('short-logical-buffer',lambda d:d['buffers'][0].update(byteLength=16)),('external-buffer-URI',lambda d:d['buffers'][0].update(uri='https://invalid.example/no-fetch.bin')),('accessor-stride-too-short',lambda d:d['bufferViews'][0].update(byteStride=8)),('sparse-index-out-of-bounds',None),('nonfinite-source-tangent',None)]
        for label,mutation in mutations:
            for tool in ['repair','seam']:
                def malformed(label=label,mutation=mutation,tool=tool):
                    src=tmp/(label+'-'+tool+'.glb');d,b=fixture(src)
                    if mutation:mutation(d)
                    elif label=='sparse-index-out-of-bounds':
                        sa=d['accessors'][d['meshes'][0]['primitives'][0]['targets'][0]['POSITION']]['sparse'];v=d['bufferViews'][sa['indices']['bufferView']];b=bytearray(b);b[v['byteOffset']+1]=5
                    elif label=='nonfinite-source-tangent':
                        b=bytearray(b);struct.pack_into('<f',b,24,float('nan'))
                    encode(src,d,b);identity=sha(src);out=tmp/(label+'-'+tool+'-out.glb');rep=tmp/(label+'-'+tool+'.json')
                    cmd=[TOOLS/'repair_mesh.py',src,'--candidate',out,'--report',rep] if tool=='repair' else [TOOLS/'split_seams.py','--source',src,'--library',LIB,'--output',out,'--report',rep]
                    r=run(cmd);detail={'process':r,'candidate_written':out.exists(),'source_unchanged':sha(src)==identity}
                    if not (r['exit_code']!=0 and not out.exists() and sha(src)==identity):
                        failure=Path(args.report.parent)/(label+'-'+tool+'-failure.json');failure.parent.mkdir(parents=True,exist_ok=True);failure.write_text(json.dumps(detail,indent=2)+'\n')
                        raise AssertionError('Malformed input was accepted or candidate published; raw outcome '+str(failure))
                    return detail
                check(tool+' refuses '+label+' before candidate publication',malformed)
        def refuse_project_candidate(use_alias=False):
            src=tmp/'project-boundary-source.glb'
            if not src.exists():fixture(src)
            parent=PROJECT
            if use_alias:
                parent=tmp/'native-project-alias';parent.symlink_to(PROJECT,target_is_directory=True)
            destination=parent/'assets/heroes/UNWRITTEN-adversarial.glb'
            try:seams.split_asset(None,src,destination,tmp/('project-alias.json' if use_alias else 'project.json'))
            except ValueError:return {'destination_exists':destination.exists(),'scope':'Public function rejected before any NativeMikk call or candidate write.'}
            except Exception as error:raise AssertionError('Candidate admitted until native use: '+type(error).__name__)
            raise AssertionError('In-project candidate admitted')
        check('Public seam function refuses native-project candidate before native work',refuse_project_candidate)
        check('Public seam function refuses symlink-parent native-project candidate',lambda:refuse_project_candidate(True))
        def dangling_report():
            src=tmp/'dangling-source.glb';fixture(src);out=tmp/'dangling-out.glb';target=tmp/'UNCREATED-dangling-report.json';link=tmp/'dangling-report.json';link.symlink_to(target);identity=sha(src)
            r=run([TOOLS/'split_seams.py','--source',src,'--library',LIB,'--output',out,'--report',link]);detail={'process':r,'symlink_target_written':target.exists(),'candidate_written':out.exists(),'source_unchanged':sha(src)==identity}
            if not(r['exit_code']!=0 and not target.exists() and not out.exists()):
                (args.report.parent/'dangling-report-symlink-failure.json').write_text(json.dumps(detail,indent=2)+'\n');raise AssertionError('Dangling report symlink followed; see retained failure')
            return detail
        check('Seam CLI refuses dangling report symlink before any output',dangling_report)
        check('Accepted runtime byte pins remain unchanged',lambda:yes(runtime_before==PINS and {p:sha(PROJECT/p) for p in PINS}==PINS))
    after={str(p.relative_to(PROJECT)):sha(p) for p in [TOOLS/'repair_mesh.py',TOOLS/'split_seams.py',PROJECT/'art/hero-rama-tangents/regenerate.py',PROJECT/'art/hero-rama-lod/glb_lod.py']}
    report={'schema':1,'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL_WITH_PRESERVED_COUNTEREXAMPLES','passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'sources_before':sources,'sources_after':after,'source_changed_during_run':sources!=after,'test_sha256':sha(Path(__file__)),'native_library':{'path':str(LIB),'sha256':sha(LIB)},'runtime_pins':PINS,'scope':'Independent synthetic CLI data/path tests. No engine/import/render, full deformation or art acceptance.'}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'count':len(checks),'failed':[c['name'] for c in checks if not c['passed']]},indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
