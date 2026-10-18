"""Compose the qualified hair geometry with accepted crown+sash-UV source bytes.

Refuses emission until every required current-parent geometry gate is complete.
No canonical asset or import cache is written.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
from build_candidate import PROJECT, GLB, PINS, sha

UV = {
 'near':'db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e',
 'mid':'b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005',
 'far':'aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a'}


def eligibility(manifest_path, evidence):
    manifest=json.loads(manifest_path.read_text());digest=sha(manifest_path);proofs={}
    def read(name):
        path=evidence/name;data=json.loads(path.read_text());assert data['passed'], ('Failed gate',name)
        if 'complete' in data:assert data['complete'], ('Partial gate',name)
        if 'manifest_sha256' in data:assert data['manifest_sha256']==digest
        proofs[name]=sha(path);return data
    source=read('source-validation-r4.json');assert source['count']==56
    tape=read('smooth-parent-draw-r3.json');assert len(tape['samples'])==348
    assert tape['source_before']==tape['source_after'] and tape['source_before']['res://assets/heroes/rama-hero.glb']==PINS['near']
    ids=[s['id'] for s in tape['samples']];assert len(set(ids))==348
    khronos=read('khronos-r4.json')
    for level,row in manifest['levels'].items():
        assert sha(row['output'])==row['output_sha256']
        assert khronos['levels'][Path(row['output']).name]['sha256']==row['output_sha256']
        assert khronos['levels'][Path(row['output']).name]['report']['issues']['numErrors']==0
        rest=read('rest-'+level+'-r4.json');assert len(rest['rows'])==1
        poses=read('poses-'+level+'-r4.json');assert len(poses['rows'])==37
        stress=read('stress-runtime-'+level+'-r4.json');assert len(stress['rows'])==32
        assert stress['stress_contract']=='runtime' and not stress['neck_secondary_offset_applied']
        collected=[]
        for start in [0,87,174,261]:
            name=f'draw-{level}-{start:03d}-{start+86:03d}-r4.json';data=read(name)
            assert data['level']==level and data['start']==start and data['count']==87
            assert len(data['rows'])==87 and data['native_sha256']==sha(evidence/'smooth-parent-draw-r3.json')
            assert [r['id'] for r in data['rows']]==ids[start:start+87]
            assert all(r['passed'] for r in data['rows']);collected.extend(r['id'] for r in data['rows'])
        assert collected==ids
    return manifest,proofs


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--evidence',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists(), 'Use a fresh review-only output'
    manifest,proofs=eligibility(a.manifest,a.evidence)
    staged=[]
    for level,row in manifest['levels'].items():
        parent=GLB(row['source']);hair=GLB(row['output']);uv=GLB(PROJECT/'art/hero-finish/sash-texel-r1/candidate-r2'/hair.path.name)
        assert sha(parent.path)==PINS[level] and sha(uv.path)==UV[level]
        assert hair.binary[:len(parent.binary)]==parent.binary and len(parent.binary)==len(uv.binary)
        # The accepted UV stage may alter only attribute data and accessor bounds,
        # not geometry, topology, rig, material, or appended-array addressing.
        assert len(parent.doc['accessors'])==len(uv.doc['accessors'])
        assert parent.doc['bufferViews']==uv.doc['bufferViews']
        for mi,pi,p in parent.primitives():
            q=uv.doc['meshes'][mi]['primitives'][pi];assert p==q
            for key in ['POSITION','NORMAL','JOINTS_0','WEIGHTS_0']:
                assert parent.array(p['attributes'][key]).tobytes()==uv.array(q['attributes'][key]).tobytes()
            assert parent.array(p['indices']).tobytes()==uv.array(q['indices']).tobytes()
        for key in ['skins','nodes','animations','materials']:assert parent.doc.get(key)==uv.doc.get(key)
        doc=copy.deepcopy(uv.doc)
        doc['accessors']+=copy.deepcopy(hair.doc['accessors'][len(parent.doc['accessors']):])
        doc['bufferViews']+=copy.deepcopy(hair.doc['bufferViews'][len(parent.doc['bufferViews']):])
        doc['meshes'][2]['primitives'][0]=copy.deepcopy(hair.doc['meshes'][2]['primitives'][0])
        doc['buffers']=copy.deepcopy(hair.doc['buffers'])
        binary=uv.binary+hair.binary[len(parent.binary):]
        encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
        raw=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+struct.pack('<II',len(binary),0x004E4942)+binary
        staged.append((level,row,uv,hair,raw))
    a.output.mkdir(parents=True)
    result={'schema':1,'inactive':True,'recipe':'Exact accepted UV binary prefix + exact qualified R4 appended hair arrays; accepted UV JSON with only existing hair append references.',
        'composer_sha256':sha(__file__),'qualified_geometry_manifest_sha256':sha(a.manifest),'qualification_proofs':proofs,'levels':{}}
    for level,row,uv,hair,raw in staged:
        path=a.output/hair.path.name;path.write_bytes(raw);composed=GLB(path)
        assert composed.binary[:len(uv.binary)]==uv.binary
        hp=hair.doc['meshes'][2]['primitives'][0];accessors=set(hp['attributes'].values())|{hp['indices']}
        for target in hp.get('targets',[]):accessors.update(target.values())
        assert all(hair.array(i).tobytes()==composed.array(i).tobytes() for i in accessors)
        result['levels'][level]={**row,'source':str(uv.path),'source_sha256':UV[level],'output':str(path),'output_sha256':sha(path),
            'qualified_r4_sha256':sha(hair.path),'accepted_uv_prefix_exact':True,'complete_r4_hair_accessors_exact':True}
    (a.output/'groom-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({level:row['output_sha256'] for level,row in result['levels'].items()},indent=2))

if __name__=='__main__':main()
