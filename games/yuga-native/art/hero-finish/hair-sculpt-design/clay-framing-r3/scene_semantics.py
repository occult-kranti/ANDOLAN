"""Read-only semantic census for a saved authoring clay scene."""
import array, hashlib, json
import bpy

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def array_sha(collection, name, width, kind='f'):
    data=array.array(kind,[0])*(len(collection)*width)
    collection.foreach_get(name,data)
    return dict(count=len(collection),width=width,scalar_type=kind,sha256=hashlib.sha256(data.tobytes()).hexdigest())
def simple(value):
    if value is None or isinstance(value,(str,bool,int,float)):return value
    if isinstance(value,bpy.types.ID):return dict(id_type=value.bl_rna.identifier,name=value.name)
    try:return [simple(x)for x in value]
    except TypeError:return str(value)
def properties(value):
    result={}
    for prop in value.bl_rna.properties:
        key=prop.identifier
        if key in ['rna_type','id_data']or prop.type not in ['BOOLEAN','INT','FLOAT','STRING','ENUM']:continue
        try:result[key]=simple(getattr(value,key))
        except (AttributeError,TypeError):continue
    return result
def node_tree(tree):
    if tree is None:return None
    return dict(nodes={node.name:dict(type=node.bl_idname,properties=properties(node),
                   inputs={socket.identifier:simple(socket.default_value)for socket in node.inputs if hasattr(socket,'default_value')},
                   outputs={socket.identifier:simple(socket.default_value)for socket in node.outputs if hasattr(socket,'default_value')})for node in tree.nodes},
                links=sorted((link.from_node.name,link.from_socket.identifier,link.to_node.name,link.to_socket.identifier)for link in tree.links))
def snapshot():
    meshes={}
    for mesh in bpy.data.meshes:
        meshes[mesh.name]=dict(vertices=array_sha(mesh.vertices,'co',3),edges=array_sha(mesh.edges,'vertices',2,'i'),
            loops=array_sha(mesh.loops,'vertex_index',1,'i'),polygon_starts=array_sha(mesh.polygons,'loop_start',1,'i'),
            polygon_counts=array_sha(mesh.polygons,'loop_total',1,'i'),material_indices=array_sha(mesh.polygons,'material_index',1,'i'),
            smooth_faces=[p.use_smooth for p in mesh.polygons],materials=[m.name if m else None for m in mesh.materials],
            vertex_weights=[[(g.group,g.weight)for g in v.groups]for v in mesh.vertices],
            uv_layer_names=list(mesh.uv_layers.keys()),attribute_names=list(mesh.attributes.keys()),shape_keys=None if mesh.shape_keys is None else mesh.shape_keys.name)
    objects={}
    for obj in bpy.data.objects:
        objects[obj.name]=dict(type=obj.type,data=None if obj.data is None else obj.data.name,
            matrix_world=[list(row)for row in obj.matrix_world],matrix_basis=[list(row)for row in obj.matrix_basis],
            parent=None if obj.parent is None else obj.parent.name,hide_render=obj.hide_render,hide_viewport=obj.hide_viewport,hide_select=obj.hide_select,
            vertex_groups=[(g.name,g.index,g.lock_weight)for g in obj.vertex_groups],modifiers=[properties(m)for m in obj.modifiers],
            custom_properties={k:simple(v)for k,v in obj.items()})
    cameras={cam.name:{key:simple(getattr(cam,key))for key in ['type','lens','lens_unit','sensor_width','sensor_height','sensor_fit','clip_start','clip_end','shift_x','shift_y','ortho_scale','display_size','passepartout_alpha']}for cam in bpy.data.cameras}
    for cam in bpy.data.cameras:cameras[cam.name]['depth_of_field']=properties(cam.dof)
    return dict(meshes=meshes,objects=objects,cameras=cameras,
       materials={m.name:dict(properties=properties(m),nodes=node_tree(m.node_tree))for m in bpy.data.materials},
       lights={l.name:dict(properties=properties(l),nodes=node_tree(l.node_tree))for l in bpy.data.lights},
       worlds={w.name:dict(properties=properties(w),nodes=node_tree(w.node_tree))for w in bpy.data.worlds},
       scene=dict(active_camera=bpy.context.scene.camera.name,frame=bpy.context.scene.frame_current,render=properties(bpy.context.scene.render),
                  color_management=properties(bpy.context.scene.view_settings),cycles=properties(bpy.context.scene.cycles),
                  units=properties(bpy.context.scene.unit_settings),custom_properties={k:simple(v)for k,v in bpy.context.scene.items()}))
def differences(a,b,path=''):
    if type(a)!=type(b):return [(path,a,b)]
    if isinstance(a,dict):
        rows=[]
        for key in sorted(set(a)|set(b)):
            if key not in a or key not in b:rows.append((path+'.'+key,a.get(key),b.get(key)))
            else:rows.extend(differences(a[key],b[key],path+'.'+key))
        return rows
    return []if a==b else [(path,a,b)]
