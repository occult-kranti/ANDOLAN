"""Independent exported face/body seam attributes and held-morph boundary."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from validate_face import read,accessor

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('asset',type=Path);p.add_argument('--partition',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();_,d,b=read(a.asset);partition=json.loads(a.partition.read_text());checks=[]
    def check(name,passed,**details):checks.append({'name':name,'passed':bool(passed),'details':details});print(('PASS 'if passed else'FAIL ')+name,details)
    nodes={n.get('name'):n for n in d['nodes']}
    def gather(name):
        node=nodes[name];skin=d['skins'][node['skin']];names=[d['nodes'][i]['name']for i in skin['joints']];blocks=[]
        for primitive in d['meshes'][node['mesh']]['primitives']:
            if d['materials'][primitive['material']]['name']!='Rama warm skin':continue
            at=primitive['attributes'];block={k:accessor(d,b,at[k])for k in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']};block['names']=names
            block['targets']=[{k:accessor(d,b,v)for k,v in t.items()}for t in primitive.get('targets',[])];blocks.append(block)
        return blocks
    face=gather('RamaFace');body=gather('RamaHero');missing=[];bad=[];maximum={'position_m':0.,'normal':0.,'uv':0.,'skin_weight':0.,'target_position_m':0.,'target_normal':0.}
    for boundary in partition['boundary']:
        x,y,z=boundary['position'];position=np.array([x,z,-y]);found=[]
        for blocks in [face,body]:
            matches=[]
            for block in blocks:
                indices=np.flatnonzero(np.max(abs(block['POSITION']-position),axis=1)<1e-7)
                matches.extend((block,index)for index in indices)
            found.append(matches)
        if not all(found):missing.append(boundary['source_vertex']);continue
        expected=dict(boundary['weights'])
        for fb,fi in found[0]:
            candidates=[(bb,bi)for bb,bi in found[1]if np.max(abs(fb['TEXCOORD_0'][fi]-bb['TEXCOORD_0'][bi]))<1e-6]
            if not candidates:bad.append([boundary['source_vertex'],'UV']);continue
            bb,bi=min(candidates,key=lambda pair:np.linalg.norm(fb['NORMAL'][fi]-pair[0]['NORMAL'][pair[1]]))
            maximum['position_m']=max(maximum['position_m'],float(np.max(abs(fb['POSITION'][fi]-bb['POSITION'][bi]))))
            maximum['normal']=max(maximum['normal'],float(np.max(abs(fb['NORMAL'][fi]-bb['NORMAL'][bi]))))
            maximum['uv']=max(maximum['uv'],float(np.max(abs(fb['TEXCOORD_0'][fi]-bb['TEXCOORD_0'][bi]))))
            for block,index in [(fb,fi),(bb,bi)]:
                actual={block['names'][int(j)]:float(w)for j,w in zip(block['JOINTS_0'][index],block['WEIGHTS_0'][index])if w>1e-7}
                for bone in set(expected)|set(actual):maximum['skin_weight']=max(maximum['skin_weight'],abs(expected.get(bone,0)-actual.get(bone,0)))
            for target in fb['targets']:
                maximum['target_position_m']=max(maximum['target_position_m'],float(np.max(abs(target['POSITION'][fi]))))
                maximum['target_normal']=max(maximum['target_normal'],float(np.max(abs(target['NORMAL'][fi]))))
    check('Every original partition boundary exists in both exported meshes',not missing,vertices=len(partition['boundary']),missing=missing)
    check('Boundary UV, normal, position and original skin are continuous',not bad and maximum['position_m']<1e-7 and maximum['normal']<.0002 and maximum['uv']<1e-6 and maximum['skin_weight']<1e-6,bad=bad,measured=maximum)
    check('Both blink targets hold boundary position and normal exactly',maximum['target_position_m']<1e-7 and maximum['target_normal']<1e-6,maximum_position_delta_m=maximum['target_position_m'],maximum_normal_delta=maximum['target_normal'])
    check('Source body partition proof retained all faces and attributes',partition['originalBodyCoveredExactlyOnce']and all(partition['sourcePartitionChecks'].values())and partition['overlayShells']==0 and partition['bones']==164)
    result={'passed':all(c['passed']for c in checks),'count':len(checks),'checks':checks,'asset_sha256':digest(a.asset),'partition_sha256':digest(a.partition),'validator_sha256':digest(__file__),'scope':'Exported actual face/body attachment and fixed target boundary only. Visual eyelid-fold, continuous pose and game integration acceptance remain separate.'}
    a.report.write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed']else 1

if __name__=='__main__':sys.exit(main())
