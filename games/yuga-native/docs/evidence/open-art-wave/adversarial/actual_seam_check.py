#!/usr/bin/env python3
"""Independent actual seam CLI and original-tangent/UV row preservation check."""
import argparse,hashlib,json,shutil,struct,subprocess,sys,time
from pathlib import Path
import numpy as np
PROJECT=Path(__file__).resolve().parents[4]
SOURCE=Path('/workspace/scratch/open-art-adversarial-r1/rama-repaired.glb')
EXPECTED_SOURCE='47cd393b975a9b505216a6051e0376a3020724a8c3400afc7422471dfbd9423d'
EXPECTED_CANDIDATE='5fc60979b7e258144e01a5ffb46752c263635e848c983cbd24aad52c5827c792'
LIB=Path('/workspace/tooling/mikktspace-yuga-r1/libyuga_mikktspace.so')
TOOL=PROJECT/'art/hero-rama-repair/split_seams.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parse(path):
    raw=Path(path).read_bytes();magic,version,length=struct.unpack_from('<4sII',raw);assert (magic,version,length)==(b'glTF',2,len(raw))
    length,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
    doc=json.loads(raw[20:20+length]);n,kind=struct.unpack_from('<II',raw,20+length);assert kind==0x004e4942
    binary=raw[28+length:];assert len(binary)==n
    return doc,binary
def rows(doc,binary,ai):
    a=doc['accessors'][ai];v=doc['bufferViews'][a['bufferView']]
    width={'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:np.dtype('<f4')}[a['componentType']]
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=offset,strides=(v.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    assert args.directory.is_absolute() and not args.directory.exists() and args.report.is_absolute() and not args.report.exists()
    args.directory.mkdir();candidate=args.directory/'rama-seams.glb';native_report=args.directory/'seams.json';identity=sha(SOURCE);assert identity==EXPECTED_SOURCE
    source_tool=sha(TOOL);command=[sys.executable,str(TOOL),'--source',str(SOURCE),'--library',str(LIB),'--output',str(candidate),'--report',str(native_report)]
    started=time.monotonic();proc=subprocess.run(command,capture_output=True,text=True,timeout=60);elapsed=time.monotonic()-started
    result={'schema':1,'command':command,'exit_code':proc.returncode,'elapsed_seconds':elapsed,'stdout':proc.stdout,'stderr':proc.stderr,'tool_before_sha256':source_tool,'tool_after_sha256':sha(TOOL),'source_before_sha256':identity,'source_after_sha256':sha(SOURCE),'native_library_sha256':sha(LIB),'checks':[],'scope':'One actual offline CLI execution plus independent decoding of original TANGENT and every UV channel. Not a deep pose, render, GPU or art approval.'}
    def check(name,yes,detail=None):result['checks'].append({'name':name,'passed':bool(yes),'detail':detail})
    check('Actual seam CLI succeeds',proc.returncode==0)
    check('Input and tool bytes stay frozen',sha(SOURCE)==identity and sha(TOOL)==source_tool)
    if candidate.exists() and native_report.exists():
        result['candidate_sha256']=sha(candidate);result['native_report_sha256']=sha(native_report)
        check('Candidate exactly reproduces independently specified 5fc609 source output',sha(candidate)==EXPECTED_CANDIDATE)
        d=json.loads(native_report.read_text());old,oldbin=parse(SOURCE);new,newbin=parse(candidate);per_domain=[]
        check('Every old binary byte remains a prefix',newbin.startswith(oldbin))
        for row in d['domains']:
            mi,pi=row['mesh'],row['primitive'];op=old['meshes'][mi]['primitives'][pi];np_=new['meshes'][mi]['primitives'][pi]
            count=old['accessors'][op['attributes']['POSITION']]['count'];clones=sorted(row['cloneMapping'],key=lambda r:r['newVertex'])
            mapping=np.concatenate([np.arange(count),np.array([x['sourceVertex'] for x in clones],dtype=np.int64)])
            target_indices=[x['newVertex'] for x in clones]
            check('Domain '+str((mi,pi))+' clone mapping contiguous',target_indices==list(range(count,count+len(clones))))
            channels={}
            for semantic,ai in op['attributes'].items():
                if semantic=='TANGENT' or semantic.startswith('TEXCOORD_'):
                    channels[semantic]=rows(old,oldbin,ai)[mapping].tobytes()==rows(new,newbin,np_['attributes'][semantic]).tobytes()
            check('Domain '+str((mi,pi))+' original tangent/UV rows copied exactly',bool(channels) and all(channels.values()),channels)
            per_domain.append({'mesh':mi,'primitive':pi,'original_vertices':count,'clones':len(clones),'channels':channels})
        result['per_domain']=per_domain
        remaining=d['remainingUnresolvedCorners'];check('UV/geometry remain unresolved rather than reported fixed',remaining==52971,{'remaining_unresolved_corners':remaining,'before_conflicts':d['beforeConflictVertices'],'after_conflicts':d['afterConflictVertices'],'clones':d['duplicatedVertices']})
        check('Face/rig/clip metadata remain unchanged',all(old.get(k)==new.get(k) for k in ['nodes','skins','animations','scenes','scene','materials','images','textures','samplers']))
        copied=args.report.parent/'actual-seam-report-r2.json';shutil.copyfile(native_report,copied);result['copied_native_report']={'path':str(copied.relative_to(PROJECT)),'sha256':sha(copied)}
    else:check('Actual output/report both exist',False)
    result['passed']=all(c['passed'] for c in result['checks']);result['count']=len(result['checks']);result['test_sha256']=sha(Path(__file__))
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':result['count'],'candidate_sha256':result.get('candidate_sha256'),'elapsed_seconds':elapsed},indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':sys.exit(main())
