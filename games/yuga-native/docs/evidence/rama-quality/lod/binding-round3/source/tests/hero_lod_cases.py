"""LOD interchange failure cases, including mask/morph/skin pairing damage."""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "art/hero-rama-lod"))
from glb_lod import GLB, validate_pair, write_compacted

def save(path, doc, binary):
    doc = copy.deepcopy(doc)
    doc["buffers"] = [{"byteLength": len(binary)}]
    raw = json.dumps(doc, separators=(",", ":")).encode()
    raw += b" " * (-len(raw) % 4)
    binary = bytes(binary) + b"\0" * (-len(binary) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 28+len(raw)+len(binary)) +
        struct.pack("<II", len(raw), 0x4E4F534A) + raw + struct.pack("<II", len(binary), 0x004E4942) + binary)

def fixture(path):
    doc = {"asset":{"version":"2.0"}, "scene":0, "scenes":[{"nodes":[0]}],
        "nodes":[{"name":"rig", "children":[1,2]}, {"name":"wrist.R"}, {"name":"hero", "mesh":0, "skin":0}],
        "skins":[{"joints":[1], "skeleton":0}], "materials":[{"name":"skin", "normalTexture":{"index":0}}],
        "textures":[], "samplers":[], "accessors":[], "bufferViews":[]}
    binary = bytearray()
    def add(a, kind, ctype):
        a = np.asarray(a)
        while len(binary)%4:binary.append(0)
        vi=len(doc["bufferViews"]);doc["bufferViews"].append({"buffer":0,"byteOffset":len(binary),"byteLength":a.nbytes})
        binary.extend(a.tobytes())
        ai=len(doc["accessors"]);doc["accessors"].append({"bufferView":vi,"componentType":ctype,"count":len(a),"type":kind})
        return ai
    attrs = {"POSITION":add(np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[.5,.5,0]],dtype='<f4'),"VEC3",5126),
        "NORMAL":add(np.tile(np.array([0,0,1],dtype='<f4'),(5,1)),"VEC3",5126),
        "TANGENT":add(np.tile(np.array([1,0,0,1],dtype='<f4'),(5,1)),"VEC4",5126),
        "TEXCOORD_0":add(np.array([[0,0],[1,0],[1,1],[0,1],[.5,.5]],dtype='<f4'),"VEC2",5126),
        "COLOR_0":add(np.array([[0,0,0,1],[1,0,0,1],[0,1,0,1],[0,0,0,1],[.5,.5,0,1]],dtype='<f4'),"VEC4",5126),
        "JOINTS_0":add(np.zeros((5,4),dtype='<u2'),"VEC4",5123),
        "WEIGHTS_0":add(np.tile(np.array([1,0,0,0],dtype='<f4'),(5,1)),"VEC4",5126)}
    idx=add(np.array([0,1,4,1,2,4,2,3,4,3,0,4],dtype='<u4').reshape(-1,1),"SCALAR",5125)
    delta=add(np.array([[0,0,.1]]*5,dtype='<f4'),"VEC3",5126)
    doc["meshes"]=[{"name":"hero", "weights":[0.0],"primitives":[{"attributes":attrs,"indices":idx,"material":0,"targets":[{"POSITION":delta}]}]}]
    doc["skins"][0]["inverseBindMatrices"]=add(np.eye(4,dtype='<f4').reshape(1,16),"MAT4",5126)
    time=add(np.array([0,1],dtype='<f4').reshape(-1,1),"SCALAR",5126)
    values=add(np.array([[0,0,0],[0,.1,0]],dtype='<f4'),"VEC3",5126)
    doc["animations"]=[{"name":"idle","channels":[{"sampler":0,"target":{"node":1,"path":"translation"}}],"samplers":[{"input":time,"output":values}]}]
    save(path,doc,binary)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path);args=ap.parse_args()
    checks=[]
    def check(name,fn):
        try:fn();checks.append({"name":name,"passed":True})
        except Exception as e:checks.append({"name":name,"passed":False,"error":str(e)})
    def reject(fn):
        try:fn()
        except (ValueError,KeyError,IndexError):return
        raise AssertionError('Malformed candidate was accepted')
    with tempfile.TemporaryDirectory(prefix='yuga-hero-lod-') as temp:
        d=Path(temp);fixture(d/'source.glb');source=GLB(d/'source.glb')
        selected={(0,0):np.array([0,1,2,0,2,3],dtype=np.uint32)}
        write_compacted(source,selected,d/'candidate.glb',{"status":"test"});candidate=GLB(d/'candidate.glb')
        check('Compaction retains normalized skin, tangent,UV,color and morph records',lambda:validate_pair(source,candidate))
        check('Actual vertex/triangle buffers are compacted',lambda: (_ for _ in ()).throw(AssertionError()) if not (candidate.measure()['vertices']==4 and candidate.measure()['triangles']==2 and candidate.measure()['vertexBytes']<source.measure()['vertexBytes']) else None)
        def mutate(name,change):
            doc=copy.deepcopy(candidate.doc);binary=bytearray(candidate.binary);change(doc,binary);p=d/(name+'.glb');save(p,doc,binary);validate_pair(source,GLB(p))
        check('Dropped secondary-motion COLOR_0 rejected',lambda:reject(lambda:mutate('mask',lambda doc,b:doc['meshes'][0]['primitives'][0]['attributes'].pop('COLOR_0'))))
        check('Dropped UV rejected',lambda:reject(lambda:mutate('uv',lambda doc,b:doc['meshes'][0]['primitives'][0]['attributes'].pop('TEXCOORD_0'))))
        check('Dropped morph target rejected',lambda:reject(lambda:mutate('morph',lambda doc,b:doc['meshes'][0]['primitives'][0].pop('targets'))))
        check('Changed skeleton rest/contact node rejected',lambda:reject(lambda:mutate('rest',lambda doc,b:doc['nodes'][1].update(translation=[.1,0,0]))))
        check('Changed joint order rejected',lambda:reject(lambda:mutate('joint',lambda doc,b:doc['skins'][0].update(joints=[0]))))
        check('Changed material contract rejected',lambda:reject(lambda:mutate('mat',lambda doc,b:doc['materials'][0].update(name='other'))))
        def alter(doc,b,semantic,value):
            ai=doc['meshes'][0]['primitives'][0]['attributes'][semantic];a=doc['accessors'][ai];v=doc['bufferViews'][a['bufferView']]
            struct.pack_into('<f',b,v['byteOffset'],value)
        for semantic,value,label in [('WEIGHTS_0',.5,'Unnormalized weights rejected'),('TANGENT',-1.,'Changed tangent rejected'),('COLOR_0',.2,'Changed mask/vertex pairing rejected'),('POSITION',float('nan'),'Nonfinite geometry rejected')]:
            check(label,lambda semantic=semantic,value=value:reject(lambda:mutate(semantic,lambda doc,b:alter(doc,b,semantic,value))))
        check('Unknown output vertex index rejected',lambda:reject(lambda:write_compacted(source,{(0,0):np.array([0,1,99])},d/'bad-index.glb',{})))
        check('Partial triangle rejected',lambda:reject(lambda:write_compacted(source,{(0,0):np.array([0,1])},d/'partial.glb',{})))
        (d/'truncated.glb').write_bytes(source.raw[:-4]);check('Truncated GLB / declared length mismatch rejected',lambda:reject(lambda:GLB(d/'truncated.glb')))
        # Blender exports morphs as sparse arrays. Expand explicitly, retaining
        # exact evaluated values rather than dropping their zero-filled base.
        sparse_doc=copy.deepcopy(source.doc);sparse_binary=bytearray(source.binary)
        target=sparse_doc['meshes'][0]['primitives'][0]['targets'][0]['POSITION']
        spec=sparse_doc['accessors'][target];values_view=spec.pop('bufferView')
        while len(sparse_binary)%4:sparse_binary.append(0)
        index_offset=len(sparse_binary);sparse_binary.extend(bytes(range(5)))
        index_view=len(sparse_doc['bufferViews']);sparse_doc['bufferViews'].append({'buffer':0,'byteOffset':index_offset,'byteLength':5})
        spec['sparse']={'count':5,'indices':{'bufferView':index_view,'componentType':5121},'values':{'bufferView':values_view}}
        save(d/'sparse.glb',sparse_doc,sparse_binary);sparse=GLB(d/'sparse.glb')
        check('Sparse Blender morph expands to exact original array',lambda:np.testing.assert_array_equal(sparse.array(target),source.array(target)))
        write_compacted(sparse,selected,d/'sparse-candidate.glb',{'status':'test'})
        check('Sparse source morph survives compact dense candidate',lambda:validate_pair(sparse,GLB(d/'sparse-candidate.glb')))
        def bad_sparse(label,values):
            b=bytearray(sparse_binary);b[index_offset:index_offset+5]=bytes(values);p=d/(label+'.glb');save(p,sparse_doc,b);GLB(p).array(target)
        check('Duplicate sparse indices rejected',lambda:reject(lambda:bad_sparse('sparse-duplicate',[0,1,1,3,4])))
        check('Out-of-range sparse indices rejected',lambda:reject(lambda:bad_sparse('sparse-bound',[0,1,2,3,9])))
    result={'passed':all(x['passed'] for x in checks),'passedCount':sum(x['passed'] for x in checks),'total':len(checks),'checks':checks}
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':main()
