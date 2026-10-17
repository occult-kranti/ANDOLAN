"""Proper small native orbital partition and actual eyelid quad morphs.

Named R4 correction for rejected layered-shell candidate. No overlay shell/rim.
Preserves exact original partition positions, corner normals, UVs and weights.
"""
from pathlib import Path
import argparse,hashlib,json,math,re,struct,sys,time
import numpy as np
import bpy
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_face import hero,sha,rig_signature,fingerprint
from validate_face import read,accessor
POSE_GAINS={'upper':.75,'lower':.15}
MEDIAL_GAINS={'upper':1.,'lower':1.}
MEDIAL_FALLOFF=(-.009,-.002)

def smooth(a,b,v):
    t=max(0,min(1,(v-a)/(b-a)))
    return t*t*(3-2*t)

def capture_body(body):
    m=body.data
    return {'vertices':[v.co.copy()for v in m.vertices],
            'weights':[[(body.vertex_groups[g.group].name,g.weight)for g in v.groups]for v in m.vertices],
            'groups':[g.name for g in body.vertex_groups],
            'faces':[{'vertices':tuple(p.vertices),'material':p.material_index,'normals':[m.corner_normals[i].vector.copy()for i in p.loop_indices],'uvs':{uv.name:[tuple(uv.data[i].uv)for i in p.loop_indices]for uv in m.uv_layers}}for p in m.polygons],
            'materials':list(m.materials),'uv_names':[uv.name for uv in m.uv_layers]}

def partition_mesh(name,data,face_ids,rig):
    used=sorted({i for f in face_ids for i in data['faces'][f]['vertices']})
    remap={old:i for i,old in enumerate(used)}
    mesh=bpy.data.meshes.new(name+' exact original quads')
    mesh.from_pydata([data['vertices'][i]for i in used],[],[[remap[i]for i in data['faces'][f]['vertices']]for f in face_ids])
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    for material in data['materials']:mesh.materials.append(material)
    for name_ in data['uv_names']:mesh.uv_layers.new(name=name_)
    color=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
    for entry in color.data:entry.color=(1,1,1,0)
    custom=[]
    for p,old in zip(mesh.polygons,face_ids):
        source=data['faces'][old]
        p.material_index=source['material'];p.use_smooth=True
        for local,li in enumerate(p.loop_indices):
            custom.append(source['normals'][local])
            for name_ in data['uv_names']:mesh.uv_layers[name_].data[li].uv=source['uvs'][name_][local]
    mesh.normals_split_custom_set(custom)
    for name_ in data['groups']:obj.vertex_groups.new(name=name_)
    for local,old in enumerate(used):
        for bone,weight in data['weights'][old]:obj.vertex_groups[bone].add([local],weight,'REPLACE')
    mod=obj.modifiers.new('Same original skeleton','ARMATURE');mod.object=rig;obj.parent=rig
    return obj,used,remap

def source_pose_units():
    metadata=json.loads((HERE/'sources/face-poseunits.json').read_text())
    assert metadata['license']=='CC0'
    hierarchy,motion=(HERE/'sources/face-poseunits.bvh').read_text().split('MOTION')
    channels=[];name=''
    for root,joint,count,values in re.findall(r'ROOT\s+(\S+)|JOINT\s+(\S+)|CHANNELS\s+(\d+)([^\n]*)',hierarchy):
        if root or joint:name=root or joint
        if count:channels.extend((name,channel)for channel in values.split())
    rows=[[float(v)for v in line.split()]for line in motion.strip().splitlines()[2:]if line.strip()]
    units={}
    for side,label in [('L','Left'),('R','Right')]:
        units[side]=[]
        for suffix in ['UpperLidClosed','LowerLidUp']:
            frame=metadata['framemapping'].index(label+suffix)
            nonzero=[(bone,axis,value)for(bone,axis),value in zip(channels,rows[frame])if abs(value)>.00001]
            assert len(nonzero)==1 and nonzero[0][1]=='Xrotation',nonzero
            bone,axis,value=nonzero[0]
            assert bone in ['orbicularis03.'+side,'orbicularis04.'+side]
            units[side].append((bone,value))
    return units

def bake_native_pose(face,rig,units,progress):
    # Source BVH X is the same anatomical left/right axis as Blender X.
    # Conjugate that joint-frame rotation into each bone's local rest basis.
    for bone in rig.pose.bones:bone.matrix_basis.identity()
    rig.data.pose_position='POSE'
    for name,degrees in units:
        rest=rig.data.bones[name].matrix_local.to_3x3()
        rotation=rest.inverted()@Matrix.Rotation(math.radians(degrees*progress),3,'X')@rest
        bone=rig.pose.bones[name];bone.rotation_mode='QUATERNION';bone.rotation_quaternion=rotation.to_quaternion()
    bpy.context.view_layer.update()
    evaluated=face.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    positions=[v.co.copy()for v in mesh.vertices]
    evaluated.to_mesh_clear()
    for bone in rig.pose.bones:bone.matrix_basis.identity()
    rig.data.pose_position='REST'
    bpy.context.view_layer.update()
    return positions

def join_custom(objects,name):
    hero.activate(objects[0])
    for obj in objects:obj.select_set(True)
    bpy.ops.object.join()
    obj=bpy.context.object;obj.name=name
    for modifier in list(obj.modifiers)[1:]:obj.modifiers.remove(modifier)
    tri=obj.modifiers.new('Runtime triangulation','TRIANGULATE')
    tri.keep_custom_normals=True
    bpy.ops.object.modifier_apply(modifier=tri.name)
    return obj

def seal_exported_boundary(path,boundaries):
    # Blender custom-normal storage quantizes in each mesh's local loop basis.
    # Copy the body's exported attachment shading attributes bit-for-bit onto
    # the duplicate facial attachment. Positions, UVs and weights are untouched.
    raw,doc,_=read(path);raw=bytearray(raw);json_length=struct.unpack_from('<I',raw,12)[0];start=20+json_length+8
    binary=memoryview(raw)[start:]
    def view(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];assert a['componentType']==5126
        width={'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        return np.ndarray((a['count'],width),dtype=np.float32,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',4*width),4))
    nodes={n.get('name'):n for n in doc['nodes']};body=[]
    for p in doc['meshes'][nodes['RamaHero']['mesh']]['primitives']:
        if doc['materials'][p['material']]['name']=='Rama warm skin':body.append({k:accessor(doc,binary,v)for k,v in p['attributes'].items()})
    copied=0
    for p in doc['meshes'][nodes['RamaFace']['mesh']]['primitives']:
        attrs=p['attributes'];positions=view(attrs['POSITION']);normals=view(attrs['NORMAL']);uv=view(attrs['TEXCOORD_0']);tangents=view(attrs['TANGENT'])
        indices=set()
        for entry in boundaries:
            x,y,z=entry['position'];point=np.array([x,z,-y])
            for i in np.flatnonzero(np.max(abs(positions-point),axis=1)<1e-7):
                candidates=[]
                for b in body:
                    for j in np.flatnonzero((np.max(abs(b['POSITION']-point),axis=1)<1e-7)&(np.max(abs(b['TEXCOORD_0']-uv[i]),axis=1)<1e-6)):
                        candidates.append((b,int(j)))
                assert candidates,entry
                b,j=min(candidates,key=lambda item:np.linalg.norm(item[0]['NORMAL'][item[1]]-normals[i]))
                normals[i]=b['NORMAL'][j];tangents[i]=b['TANGENT'][j];indices.add(int(i));copied+=1
        for target in p['targets']:
            a=doc['accessors'][target['NORMAL']]
            if 'bufferView'in a:
                values=view(target['NORMAL'])
                for i in indices:values[i]=0
            if 'sparse'in a:
                s=a['sparse'];si=s['indices'];sv=s['values'];iv=doc['bufferViews'][si['bufferView']];vv=doc['bufferViews'][sv['bufferView']]
                ids=np.frombuffer(binary,dtype={5121:np.uint8,5123:np.uint16,5125:np.uint32}[si['componentType']],count=s['count'],offset=iv.get('byteOffset',0)+si.get('byteOffset',0))
                values=np.frombuffer(binary,dtype=np.float32,count=s['count']*3,offset=vv.get('byteOffset',0)+sv.get('byteOffset',0)).reshape(-1,3)
                for row,i in enumerate(ids):
                    if int(i)in indices:values[row]=0
    Path(path).write_bytes(raw)
    return {'faceBoundaryCopies':copied,'normalAndTangent':'Exact exported body values','targetBoundaryNormalDeltas':'Zero','positionsUVsWeightsChanged':False}

def repair_exported_zero_tangents(path):
    before=Path(path).read_bytes();raw=bytearray(before);_,doc,_=read(path)
    json_length=struct.unpack_from('<I',raw,12)[0];start=20+json_length+8;binary=memoryview(raw)[start:];repairs=[];allowed=[]
    def dense(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];assert a['componentType']==5126
        count={'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',4*count)
        return np.ndarray((a['count'],count),dtype=np.float32,buffer=binary,offset=offset,strides=(stride,4)),offset,stride
    for mesh_index,mesh in enumerate(doc['meshes']):
        for primitive_index,p in enumerate(mesh['primitives']):
            attrs=p['attributes']
            if 'TANGENT'not in attrs:continue
            tangents,offset,stride=dense(attrs['TANGENT']);bad=np.flatnonzero(np.linalg.norm(tangents[:,:3],axis=1)<1e-8)
            if not len(bad):continue
            assert (mesh_index,primitive_index)==(2,1)and set(map(int,bad))=={8160,8188,8875},(mesh_index,primitive_index,bad)
            assert doc['materials'][p['material']]['name']=='Ivory silk'
            positions=accessor(doc,binary,attrs['POSITION']).astype(np.float64);normals=accessor(doc,binary,attrs['NORMAL']).astype(np.float64);uvs=accessor(doc,binary,attrs['TEXCOORD_0']).astype(np.float64);indices=accessor(doc,binary,p['indices']).reshape(-1,3)
            for vertex in map(int,bad):
                frames=[]
                for triangle in indices[np.any(indices==vertex,axis=1)]:
                    p0,p1,p2=positions[triangle];uv0,uv1,uv2=uvs[triangle];e1=p1-p0;e2=p2-p0;d1=uv1-uv0;d2=uv2-uv0;det=d1[0]*d2[1]-d1[1]*d2[0]
                    if abs(det)<1e-12 or np.linalg.norm(np.cross(e1,e2))<1e-12:continue
                    tangent=(e1*d2[1]-e2*d1[1])/det;bitangent=(e2*d1[0]-e1*d2[0])/det;normal=normals[vertex]/np.linalg.norm(normals[vertex]);tangent-=normal*np.dot(normal,tangent)
                    if np.linalg.norm(tangent)<1e-10:continue
                    tangent/=np.linalg.norm(tangent);w=1. if np.dot(np.cross(normal,tangent),bitangent)>=0 else -1.
                    frames.append((list(map(int,triangle)),np.array([*tangent,w],dtype=np.float32)))
                assert len(frames)==1,(vertex,len(frames))
                triangle,value=frames[0];tangents[vertex]=value;absolute=start+offset+stride*vertex;allowed.append((absolute,absolute+16))
                repairs.append({'mesh':mesh_index,'primitive':primitive_index,'material':'Ivory silk','vertex':vertex,'triangle':triangle,'tangent':list(map(float,value)),'absoluteByteOffset':absolute,'bytes':16,'unitLengthError':abs(float(np.linalg.norm(value[:3]))-1),'normalDot':float(np.dot(value[:3],normals[vertex]))})
    assert len(repairs)==3
    changes=[i for i,(a,b)in enumerate(zip(before,raw))if a!=b]
    assert len(before)==len(raw)and all(any(low<=i<high for low,high in allowed)for i in changes)
    Path(path).write_bytes(raw)
    return {'sourceSha256':hashlib.sha256(before).hexdigest(),'resultSha256':sha(path),'repairs':repairs,'changedBytes':len(changes),'allowedRecords':len(allowed),'allOtherBytesIdentical':True,'positionsNormalsUVsSkinMorphsFaceUnchanged':True,'method':'Only zero tangent records: derive adjacent nondegenerate UV triangle T/B, Gram-Schmidt against the existing normal, normalize, derive signed handedness.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repair-reviewed-input',type=Path);p.add_argument('--reviewed-sha256');p.add_argument('--reviewed-metadata',type=Path);p.add_argument('--reviewed-editable',type=Path)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    if a.repair_reviewed_input:
        import shutil
        assert a.reviewed_sha256 and a.reviewed_metadata and a.reviewed_editable
        assert sha(a.repair_reviewed_input)==a.reviewed_sha256
        metadata=json.loads(a.reviewed_metadata.read_text())
        assert metadata['outputSha256']==a.reviewed_sha256
        assert metadata['inputBlendSha256']==sha(a.input)
        assert metadata['editableSha256']==sha(a.reviewed_editable)
        output=a.output/'rama-hero-face.glb';editable=a.output/'rama-hero-face.blend'
        assert not output.exists()and not editable.exists(),'Repair requires fresh output paths'
        shutil.copy2(a.repair_reviewed_input,output);shutil.copy2(a.reviewed_editable,editable)
        repair=repair_exported_zero_tangents(output)
        metadata.update(nativeGeometryGeneratorSha256=metadata['generatorSha256'],generatorSha256=sha(__file__),postExportProcessorSha256=sha(__file__),generationMode='Exact reviewed native GLB plus three derived cloth tangent records; reviewed editable unchanged',zeroTangentRepair=repair,outputSha256=sha(output),editableSha256=sha(editable))
        (a.output/'candidate.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print('RAMA_REVIEWED_TANGENT_REPAIR '+json.dumps(repair),flush=True)
        return
    bpy.ops.wm.open_mainfile(filepath=str(a.input))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    rig.data.pose_position='REST';rig.animation_data.action=None
    for bone in rig.pose.bones:bone.matrix_basis.identity()
    body=bpy.data.objects['RamaAnatomy'];data=capture_body(body);before_rig=rig_signature(rig)
    eyes=[o for o in bpy.data.objects if o.name.startswith(('Seated sclera','Brown iris','Dark pupil'))]
    eye_hashes={o.name:fingerprint(o)for o in eyes}
    centers={}
    for side in ('L','R'):
        c=rig.data.bones['eye.'+side].head_local.copy();c.y-=.003;centers[side]=c
    selected=[]
    for index,face in enumerate(data['faces']):
        c=sum((data['vertices'][i]for i in face['vertices']),Vector())/len(face['vertices'])
        if c.y<-.106 and any(((c.x-eye.x)/.033)**2+((c.z-eye.z)/.031)**2<1 for eye in centers.values()):selected.append(index)
    unselected=sorted(set(range(len(data['faces'])))-set(selected))
    face,used,remap=partition_mesh('RamaFace',data,selected,rig)
    retained,retained_used,_=partition_mesh('RamaAnatomy remainder',data,unselected,rig)
    boundary=set(used)&set(retained_used)
    # Hold the entire shared boundary and its immediate selected neighbor ring;
    # positions and target normal deltas stay stationary at the attachment.
    held=set(boundary)
    for f in selected:
        ids=set(data['faces'][f]['vertices'])
        if ids&boundary:held|=ids
    neutral={old:data['vertices'][old].copy()for old in used}
    source_units=source_pose_units()
    units={side:[(bone,degrees*POSE_GAINS['upper'if'03.'in bone else'lower'])for bone,degrees in values]for side,values in source_units.items()}
    evaluated_rest=bake_native_pose(face,rig,[],0.)
    baked={(side,progress):bake_native_pose(face,rig,units[side],progress)for side in ('L','R')for progress in (.5,1.)}
    medial_units={side:[(bone,degrees*MEDIAL_GAINS['upper'if'03.'in bone else'lower'])for bone,degrees in values]for side,values in source_units.items()}
    medial_baked={(side,progress):bake_native_pose(face,rig,medial_units[side],progress)for side in ('L','R')for progress in (.5,1.)}
    affected={side:{b.name for b in rig.data.bones if b.name in dict(units[side])or any(parent.name in dict(units[side])for parent in b.parent_recursive)}for side in ('L','R')}
    basis=face.shape_key_add(name='Basis')
    for side,name,progress in [('L','rama_blink_left',1.),('R','rama_blink_right',1.),('L','rama_blink_half_left',.5),('R','rama_blink_half_right',.5)]:
        key=face.shape_key_add(name=name)
        c=centers[side]
        for local,old in enumerate(used):
            point=neutral[old]
            weighted=any(name in affected[side]and weight>1e-7 for name,weight in data['weights'][old])
            if old not in held and weighted and (point.x>0)==(side=='L'):
                outward=(point.x-c.x)*(1 if side=='L'else -1)
                medial=1-smooth(*MEDIAL_FALLOFF,outward)
                posed=baked[(side,progress)][local].lerp(medial_baked[(side,progress)][local],medial)
                key.data[local].co=point+(posed-evaluated_rest[local])
        key.value=0;key.slider_min=0;key.slider_max=1
    # No overlay skin and no residual static or moving artificial rim tubes.
    removed_rims=[o.name for o in bpy.data.objects if o.type=='MESH'and o.name.startswith(('Integrated upper eyelid','Integrated lower eyelid'))]
    assert len(removed_rims)==4
    for name in removed_rims:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
    bpy.data.objects.remove(body,do_unlink=True)
    retained.name='RamaAnatomy'
    assert before_rig==rig_signature(rig)
    assert eye_hashes=={o.name:fingerprint(o)for o in eyes}
    assert len(face.data.vertices)<8000 and len(rig.data.bones)==164
    # Source-to-partition proof includes exact seam corner data and weights;
    # original face IDs cover the body once, with duplication only at its seam.
    assertions={'positions':True,'normals':True,'uvs':True,'weights':True,'color':True,'shape_boundary':True}
    boundary_records=[]
    for obj,ids,source_faces in [(face,used,selected),(retained,retained_used,unselected)]:
        for local,old in enumerate(ids):
            assertions['positions'] &= obj.data.vertices[local].co==(neutral[old]if obj==face else data['vertices'][old])
            copied=[(obj.vertex_groups[g.group].name,g.weight)for g in obj.data.vertices[local].groups]
            assertions['weights'] &= copied==data['weights'][old]
        for poly,source_index in zip(obj.data.polygons,source_faces):
            source=data['faces'][source_index]
            for local,li in enumerate(poly.loop_indices):
                normal=obj.data.corner_normals[li].vector
                assertions['normals'] &= (normal-source['normals'][local]).length<.0002
                for name in data['uv_names']:assertions['uvs'] &= tuple(obj.data.uv_layers[name].data[li].uv)==source['uvs'][name][local]
    for old in boundary:
        local=remap[old]
        assertions['shape_boundary'] &= all(key.data[local].co==data['vertices'][old]for key in face.data.shape_keys.key_blocks)
        boundary_records.append({'source_vertex':old,'position':list(data['vertices'][old]),'weights':data['weights'][old]})
    assert all(assertions.values()),assertions
    stats={'schema':1,'task':'Rama R4 actual native eyelid quad partition','inputBlendSha256':sha(a.input),'generatorSha256':sha(__file__),'originalBodyPolygons':len(data['faces']),'selectedPolygons':len(selected),'retainedPolygons':len(unselected),'selectedSourceVertices':len(used),'retainedSourceVertices':len(retained_used),'sharedBoundaryVertices':len(boundary),'heldBoundaryAndRingVertices':len(held),'originalBodyCoveredExactlyOnce':set(selected).isdisjoint(unselected)and len(selected)+len(unselected)==len(data['faces']),'sourcePartitionChecks':assertions,'removedArtificialRims':removed_rims,'originalEyesUnchanged':True,'rigRestPreserved':True,'bones':len(rig.data.bones),'overlayShells':0,'morphNames':['rama_blink_left','rama_blink_right','rama_blink_half_left','rama_blink_half_right'],'sourcePoseUnits':{'license':'CC0','revision':'a8bc2d54ff0ac92e78ff71431b1023eda42bf482','originalAnglesDegrees':source_units,'gains':{'central':POSE_GAINS,'medial':MEDIAL_GAINS,'medialFalloffOutwardXM':MEDIAL_FALLOFF},'bakedCentralAnglesDegrees':units,'bakedMedialAnglesDegrees':medial_units,'jsonSha256':sha(HERE/'sources/face-poseunits.json'),'bvhSha256':sha(HERE/'sources/face-poseunits.bvh'),'method':'Authoring-only native bone-weighted full/half poses with smooth medial gain blend baked to small morphs; all original bones restored before export.'},'neutralRefinement':{'kind':'None; all original anatomical neutral positions retained','maximumDisplacementM':0.,'heldBoundary':True},'boundary':boundary_records,'eyeOriginsBlender':{s:list(v)for s,v in centers.items()},'status':'CANDIDATE_UNREVIEWED'}
    rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions.get('idle');bpy.context.scene.frame_set(1)
    editable=a.output/'rama-hero-face.blend';bpy.ops.wm.save_as_mainfile(filepath=str(editable),compress=True)
    objects=[o for o in bpy.data.objects if o.type=='MESH']
    terms=['Forged recurved bow limbs','Cobalt bow inset','Bow pierced leaf scroll','Bow sapphire setting','Swept bow tip flourish','Leather bound grip','Grip chased wire','Skinned bowstring']
    bows=[o for o in objects if any(o.name.startswith(t)for t in terms)];assert len(bows)>15
    hero_mesh=join_custom([o for o in objects if o not in bows and o!=face],'RamaHero');bow=hero.join_group(bows,'RamaBow')
    hero.activate(rig)
    for obj in (hero_mesh,bow,face):obj.select_set(True)
    output=a.output/'rama-hero-face.glb'
    bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_skins=True,export_all_influences=False,export_yup=True,export_tangents=True,export_image_format='AUTO',export_vertex_color='ACTIVE',export_morph=True,export_morph_normal=True)
    stats['boundaryAttributeSeal']=seal_exported_boundary(output,boundary_records)
    stats['zeroTangentRepair']=repair_exported_zero_tangents(output)
    stats.update(outputSha256=sha(output),editableSha256=sha(editable),elapsedSeconds=round(time.monotonic()-started,2),limitations=['Requires imported open/half/closed, continuous blink and partition-seam visual acceptance.','No authored brow/gaze/jaw expression or physical GPU/gameplay acceptance.'])
    (a.output/'candidate.json').write_text(json.dumps(stats,indent=2)+'\n')
    print('RAMA_NATIVE_FACE '+json.dumps({k:v for k,v in stats.items()if k!='boundary'}),flush=True)

if __name__=='__main__':main()
