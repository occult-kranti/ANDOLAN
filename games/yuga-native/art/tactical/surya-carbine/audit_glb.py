"""Focused standard-library inspection of the actual exported SURYA bytes."""
import hashlib
import json
import math
from pathlib import Path
import struct

project = Path(__file__).resolve().parents[3]
asset = project / "assets/tactical/surya-carbine.glb"
raw = asset.read_bytes()
length, kind = struct.unpack_from("<II", raw, 12)
assert kind == 0x4E4F534A
document = json.loads(raw[20:20+length])
offset = 20 + length
binary_length, kind = struct.unpack_from("<II", raw, offset)
assert kind == 0x004E4942
binary = raw[offset+8:offset+8+binary_length]


def access(index):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    code = {5126:"f", 5125:"I", 5123:"H", 5121:"B"}[accessor["componentType"]]
    width = {"VEC3":3, "VEC2":2, "VEC4":4, "SCALAR":1}[accessor["type"]]
    fmt = "<" + code*width
    stride = view.get("byteStride", struct.calcsize(fmt))
    start = view.get("byteOffset",0) + accessor.get("byteOffset",0)
    return [struct.unpack_from(fmt,binary,start+i*stride) for i in range(accessor["count"])]


checks=[]
for mesh in document["meshes"]:
    count=zero=nonfinite=badnormals=0
    smallest=float("inf")
    for primitive in mesh["primitives"]:
        positions=access(primitive["attributes"]["POSITION"])
        normals=access(primitive["attributes"]["NORMAL"])
        indices=[item[0] for item in access(primitive["indices"])]
        nonfinite += sum(not math.isfinite(value) for vector in positions+normals for value in vector)
        badnormals += sum(abs(math.sqrt(sum(x*x for x in n))-1)>.001 for n in normals)
        for i in range(0,len(indices),3):
            a,b,c=[positions[j] for j in indices[i:i+3]]
            u=[b[j]-a[j] for j in range(3)]
            v=[c[j]-a[j] for j in range(3)]
            cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            area=math.sqrt(sum(x*x for x in cross))*.5
            count+=1
            zero+=area<=1e-14
            smallest=min(smallest,area)
    checks.append(dict(name=mesh.get("name"),triangles=count,zero_area_faces_at_1e_14=zero,minimum_area_m2=smallest,nonfinite_values=nonfinite,nonunit_normals=badnormals,primitives=len(mesh["primitives"])))
report={"kind":"actual exported GLB geometry and transform audit","asset_sha256":hashlib.sha256(raw).hexdigest(),"mesh_checks":checks,"nodes":document["nodes"],"materials":len(document.get("materials",[])),"embedded_images":len(document.get("images",[])),"animations":len(document.get("animations",[])),"command":"python games/yuga-native/art/tactical/surya-carbine/audit_glb.py","scope":"Read-only numerical audit of exported bytes; not visual quality or hardware performance proof."}
out=Path(__file__).with_name("glb-audit-r2.json")
if out.exists():
    raise RuntimeError("Preserve the earlier audit before writing a successor")
out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
