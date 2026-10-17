"""Bounded central-drape skin correction; geometry and rig remain byte-exact.

Blender: --python rebind_dhoti.py -- --source-blend FILE --source-glb FILE --output DIR
The same bind function is imported by build_hero.py for future full builds.
"""
from pathlib import Path
import sys,json,math,hashlib,struct

def drape_weights(co):
    x,y,z=co
    v=max(0.,min(1.,(1.02-z)/.68))
    q=max(0.,min(1.,(v-.10)/.70));q=q*q*(3-2*q)
    thigh=.16*q
    left=.5+.5*math.tanh(x/.045)
    return {'spine05':1-thigh,'upperleg01.L':thigh*left,'upperleg01.R':thigh*(1-left)}

def apply_front_drape_binding(sheet,borders):
    # A continuous sheet bridges both legs. Pelvis dominance prevents the leg
    # nearest-neighbour ownership seam from turning it into two stretching flaps.
    for obj in [sheet,*borders]:
        obj.vertex_groups.clear()
        groups={name:obj.vertex_groups.new(name=name) for name in ('spine05','upperleg01.L','upperleg01.R')}
        for vertex in obj.data.vertices:
            for name,weight in drape_weights(vertex.co).items():
                if weight>0:groups[name].add([vertex.index],weight,'REPLACE')

def geometry_signature(obj):
    payload=dict(vertices=[list(v.co) for v in obj.data.vertices],polygons=[(list(p.vertices),p.material_index,p.use_smooth) for p in obj.data.polygons],uv=[list(x.uv) for x in obj.data.uv_layers.active.data] if obj.data.uv_layers.active else None,materials=[m.name if m else None for m in obj.data.materials],matrix=[list(r) for r in obj.matrix_local])
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()

def load_glb(path):
    raw=Path(path).read_bytes();size,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a;doc=json.loads(raw[20:20+size]);offset=20+size;ln,kind=struct.unpack_from('<II',raw,offset);assert kind==0x004e4942;return raw,doc,offset+8

def main():
    import bpy,numpy as np
    args=sys.argv[sys.argv.index('--')+1:]
    val=lambda key:Path(args[args.index(key)+1])
    source_blend=val('--source-blend');source_glb=val('--source-glb');out=val('--output');out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    sheet=bpy.data.objects['Layered ivory dhoti'];borders=[o for o in bpy.data.objects if o.name.startswith('Ivory embroidered edge')];assert len(borders)==2
    meshes=[o for o in bpy.data.objects if o.type=='MESH'];before_geometry={o.name:geometry_signature(o) for o in meshes}
    apply_front_drape_binding(sheet,borders)
    assert {o.name:geometry_signature(o) for o in meshes}==before_geometry,'Editable geometry/material/UV changed'
    target=[sheet,*borders]
    # Binary attributes use glTF Y-up while source Blender uses Z-up.
    key=lambda co:tuple(round(float(v),6) for v in co)
    target_positions={key((v.co.x,v.co.z,-v.co.y)):drape_weights(v.co) for o in target for v in o.data.vertices}
    original,doc,bin_start=load_glb(source_glb);modified=bytearray(original)
    nodes=[n for n in doc['nodes'] if n.get('name')=='RamaHero'];assert len(nodes)==1;node=nodes[0]
    joints={doc['nodes'][node_id]['name']:i for i,node_id in enumerate(doc['skins'][node['skin']]['joints'])}
    formats={5121:('B',1),5123:('H',2),5126:('f',4)}
    def info(index,width):
        ac=doc['accessors'][index];view=doc['bufferViews'][ac['bufferView']];fmt,size=formats[ac['componentType']]
        return bin_start+view.get('byteOffset',0)+ac.get('byteOffset',0),view.get('byteStride',width*size),fmt,size,ac['count']
    allowed=np.zeros(len(original),dtype=np.bool_);matched=set();patched=0;accessors=set()
    for primitive in doc['meshes'][node['mesh']]['primitives']:
        at=primitive['attributes'];po,ps,pf,pz,count=info(at['POSITION'],3);jo,js,jf,jz,jcount=info(at['JOINTS_0'],4);wo,ws,wf,wz,wcount=info(at['WEIGHTS_0'],4);assert pf==wf=='f' and count==jcount==wcount
        for i in range(count):
            position=struct.unpack_from('<3f',original,po+i*ps);k=key(position)
            if k not in target_positions:continue
            binding=target_positions[k];entries=[(joints[n],w) for n,w in binding.items() if w>0];entries+= [(0,0)]*(4-len(entries))
            struct.pack_into('<4'+jf,modified,jo+i*js,*[j for j,w in entries]);struct.pack_into('<4f',modified,wo+i*ws,*[w for j,w in entries])
            allowed[jo+i*js:jo+i*js+4*jz]=True;allowed[wo+i*ws:wo+i*ws+4*wz]=True
            matched.add(k);patched+=1;accessors.update([at['JOINTS_0'],at['WEIGHTS_0']])
    assert matched==set(target_positions),('Unmatched target positions',len(set(target_positions)-matched))
    changed=np.frombuffer(original,dtype=np.uint8)!=np.frombuffer(modified,dtype=np.uint8)
    assert not np.any(changed & ~allowed),'Bytes outside target joint/weight records changed'
    assert original[:bin_start]==modified[:bin_start],'GLB JSON/header changed'
    glb=out/'rama-hero.glb';glb.write_bytes(modified)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'rama-hero.blend'),compress=True)
    # Quantify the corrected vertex-to-neighbour continuity on the source sheet.
    def weights(v):return {sheet.vertex_groups[g.group].name:g.weight for g in v.groups}
    max_jump=0
    for edge in sheet.data.edges:
        a,b=[weights(sheet.data.vertices[i]) for i in edge.vertices];max_jump=max(max_jump,sum(abs(a.get(n,0)-b.get(n,0)) for n in set(a)|set(b)))
    assert max_jump<.08,max_jump
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    result=dict(schema=1,operation='Central dhoti and two matching gold borders: weights only',sourceGlbSha256=sha(source_glb),sourceBlendSha256=sha(source_blend),outputGlbSha256=sha(glb),outputBlendSha256=sha(out/'rama-hero.blend'),patchGeneratorSha256=sha(__file__),targetMeshes=[o.name for o in target],targetUniquePositions=len(target_positions),patchedExportedVertices=patched,changedBytes=int(changed.sum()),modifiedAccessors=sorted(accessors),allOtherGlbBytesIdentical=True,editableGeometryNormalsUVMaterialsPreserved=True,editableGeometryHashes=before_geometry,maximumDhotiAdjacentWeightL1=max_jump,pelvisWeightRange=[.84,1],maximumTotalThighWeight=.16,thighCrossfadeWidthMetres=.09,lowerLegInfluence=0,limitations=['Actual runtime strafe, forward run, draw/release and cloth clearances still require rendered review.'])
    (out/'weight-correction.json').write_text(json.dumps(result,indent=2)+'\n');print('WEIGHT_PATCH '+json.dumps({k:v for k,v in result.items() if k!='editableGeometryHashes'}),flush=True)

if __name__=='__main__':main()
