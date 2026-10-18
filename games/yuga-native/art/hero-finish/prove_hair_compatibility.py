"""Read-only upper-hair compatibility ledger for accepted original asset stages.

This does not alter runtime source, guide schema/authorship or helper activation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / 'art/hero-rama-lod'))
from glb_lod import GLB
STAGES = {
    'original-r7': ('art/visual-rounds/groom/principal-groom-v1', ['8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c','d95a061e2243477afc0227bf52564252fbcb20cb039d303ad10292ea5d85beed','ee2e35278ce49efdda6751850fddbb8f1b4de99ad019e6992c10e7702dc6317c']),
    'smooth-crown-r2': ('art/hero-finish/s4-diadem-smooth/candidate-r2', ['e98c9110161e49b653e98b6f4ca1dda997ad891cf73b737abd18f319bb3c2b82','dfa9a41adab7cfd5c60416a66d2b95c4d1ab06d081b64ee7a9f5ff5c7744474b','8b74504c07d38416032ea22e37061d69061baaf0b86e78dec27417c8927e39f9']),
    'sash-uv-r2': ('art/hero-finish/sash-texel-r1/candidate-r2', ['db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e','b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005','aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a'])}
FILES = ['rama-hero.glb', 'rama-hero-mid.glb', 'rama-hero-far.glb']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--import-proof',type=Path,action='append',default=[]);a=ap.parse_args()
    assert not a.output.exists()
    rows=[]
    for i,filename in enumerate(FILES):
        original=GLB(PROJECT/STAGES['original-r7'][0]/filename)
        assert sha(original.path)==STAGES['original-r7'][1][i]
        hp=original.doc['meshes'][2]['primitives'][0]
        accessors=set(hp['attributes'].values())|{hp['indices']}
        for target in hp.get('targets',[]): accessors.update(target.values())
        for stage,(directory,pins) in STAGES.items():
            model=GLB(PROJECT/directory/filename);assert sha(model.path)==pins[i]
            assert model.doc['meshes'][2]['primitives'][0]==hp
            for key in ['skins','nodes','animations']: assert model.doc.get(key)==original.doc.get(key)
            assert model.doc['materials'][hp['material']]==original.doc['materials'][hp['material']]
            records=[]
            for index in sorted(accessors):
                before,after=original.array(index).tobytes(),model.array(index).tobytes()
                assert before==after, ('Hair changed',stage,filename,index)
                records.append({'accessor':index,'bytes':len(before),'sha256':hashlib.sha256(before).hexdigest()})
            rows.append({'stage':stage,'source':str(model.path.relative_to(PROJECT)),'sha256':pins[i],
                'hair_primitive_rig_animation_material_json_exact':True,'hair_accessors':records})
    proofs=[]
    for p in a.import_proof:
        data=json.loads(p.read_text());assert data['passed'];proofs.append({'path':str(p.resolve().relative_to(PROJECT)),'sha256':sha(p)})
    guide=PROJECT/'assets/hero-finish/upper-hair-layers.json';data=json.loads(guide.read_text())
    assert data['schema']==1 and data['source_sha256']==STAGES['original-r7'][1][0]
    result={'passed':True,'scope':'Offline accepted-stage compatibility ledger only. Runtime helper/guide remain original schema1, with existing rig/rest/material admission. No raw-file runtime hashing, new guide geometry, activation or new principal-hair acceptance.',
        'tool_sha256':sha(__file__),'guides_sha256':sha(guide),'original_generator_sha256':sha(PROJECT/'art/hero-finish/build_g2_hair_layers.py'),'actual_import_proofs':proofs,'levels_and_stages':rows}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(rows),'stage/LOD rows; unchanged hair accessors per row',[len(r['hair_accessors']) for r in rows])
if __name__=='__main__':main()
