"""Validate actual GLB skin, image identity and animation data without rendering."""
import argparse, hashlib, json, math, struct
from pathlib import Path

SIZES={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
COMP={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}
class GLB:
    def __init__(self,path):
        self.path=Path(path);raw=self.path.read_bytes();assert raw[:4]==b'glTF';size,kind=struct.unpack_from('<II',raw,12);self.doc=json.loads(raw[20:20+size]);self.blob=raw[28+size:]
    def array(self,index):
        a=self.doc['accessors'][index];v=self.doc['bufferViews'][a['bufferView']];fmt,width=COMP[a['componentType']];n=SIZES[a['type']];stride=v.get('byteStride',n*width);start=v.get('byteOffset',0)+a.get('byteOffset',0)
        rows=[struct.unpack_from('<'+fmt*n,self.blob,start+i*stride) for i in range(a['count'])]
        if a.get('normalized'):
            maximum={5120:127,5121:255,5122:32767,5123:65535}[a['componentType']];rows=[tuple(max(-1,x/maximum) for x in row) for row in rows]
        return rows
    def image_hashes(self):
        out=[]
        for image in self.doc.get('images',[]):
            view=self.doc['bufferViews'][image['bufferView']];start=view.get('byteOffset',0);out.append(hashlib.sha256(self.blob[start:start+view['byteLength']]).hexdigest())
        return out
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    g=GLB(a.candidate);s=GLB(a.source);d=GLB(a.donor);assert len(g.doc['skins'])==1;skin=g.doc['skins'][0]
    names=[g.doc['nodes'][i]['name'] for i in skin['joints']];donor_names=[d.doc['nodes'][i]['name'] for i in d.doc['skins'][0]['joints']];assert set(names)==set(donor_names) and len(names)==164
    influence_rows=[];geometry_vertices=0
    for mesh in g.doc['meshes']:
        for primitive in mesh['primitives']:
            attrs=primitive['attributes'];assert 'JOINTS_0' in attrs and 'WEIGHTS_0' in attrs;assert 'JOINTS_1' not in attrs
            j=g.array(attrs['JOINTS_0']);w=g.array(attrs['WEIGHTS_0']);pos=g.array(attrs['POSITION']);assert len(j)==len(w)==len(pos);geometry_vertices+=len(pos)
            assert all(math.isfinite(c) for v in pos for c in v)
            for joints,weights in zip(j,w):
                assert all(0<=i<len(names) for i in joints);assert all(math.isfinite(v) and 0<=v<=1 for v in weights);assert abs(sum(weights)-1)<1e-5
            influence_rows.extend(w)
    actions=g.doc['animations'];expected={x['name'] for x in d.doc['animations']};assert {x['name'] for x in actions}==expected and len(actions)==9
    for animation in actions:
        assert animation['channels'] and animation['samplers']
        for sample in animation['samplers']:
            times=g.array(sample['input']);values=g.array(sample['output']);assert all(math.isfinite(x) for row in times+values for x in row);assert all(times[i][0]<times[i+1][0] for i in range(len(times)-1))
    binds=g.array(skin['inverseBindMatrices']);assert len(binds)==164 and all(math.isfinite(x) for row in binds for x in row)
    assert sorted(g.image_hashes())==sorted(s.image_hashes())
    report={'schema_version':1,'scope':'GLB container/skinning/animation/image integrity only; cannot accept anatomy, deformation, contacts or visual quality.','candidate':{'path':str(a.candidate),'bytes':a.candidate.stat().st_size,'sha256':sha(a.candidate)},'script_sha256':sha(__file__),'skin_joints':len(names),'donor_bone_names_preserved':True,'actions':[x['name'] for x in actions],'geometry_vertices':geometry_vertices,'unweighted_vertices':sum(sum(v)==0 for v in influence_rows),'max_influences':max(sum(x>0 for x in row) for row in influence_rows),'max_weight_sum_error':max(abs(sum(row)-1) for row in influence_rows),'finite_positions_inverse_binds_animations':True,'source_embedded_image_bytes_preserved':True,'image_sha256':g.image_hashes(),'runtime_promoted':False,'quality_accepted':False}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('RIG_GLB_INTEGRITY_PASS',json.dumps(report))
if __name__=='__main__':main()
