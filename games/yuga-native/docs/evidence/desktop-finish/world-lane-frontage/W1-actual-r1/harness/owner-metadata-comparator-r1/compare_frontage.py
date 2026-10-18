"""Finite strict three-view frontage control comparator. No pixel-quality claim."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

IDS = ['00-world-product', '01-frontage-contact', '02-overview-context']
GLOBAL_COUNTERS = {'process_frame', 'physics_frame', 'drawn_frame'}
# ONLY these root shot fields are handled separately below.
SEPARATE = GLOBAL_COUNTERS | {'file', 'sha256', 'frontage', 'meshes', 'collision_objects', 'pose_signal_counters'}
SELECTION = 'tools/visual-rounds/frontage-review.json'
MARKERS = {'.graphics-six-snapshot.json', 'res://.graphics-six-snapshot.json'}
IDENTITY = [[1,0,0],[0,1,0],[0,0,1],[0,0,0]]

OWNER_KEY = 'metadata/yuga_surface_finish_owner'
OWNER_NAMES = {
    'Worked warm gold · bounded secondary',
    'Swept black hair · bounded secondary',
    'Cobalt handwoven silk · bounded secondary',
    'Cobalt lotus brocade · bounded secondary',
}

def normalize_finish_owner(report, label, errors):
    # Resource metadata contains Node.get_instance_id(), not a renderer value.
    # Preserve the original report; admit exactly four named ShaderMaterials,
    # one positive process-local owner across all three views, and no other key.
    normalized = copy.deepcopy(report)
    owner_ids = set()
    audit = []
    for shot in normalized['shots']:
        remap = {}
        names = []
        rows = {}
        for raw_hash, row in shot['materials'].items():
            properties = row.get('properties', {})
            if OWNER_KEY not in properties:
                rows[raw_hash] = row
                continue
            owner = properties[OWNER_KEY]
            name = properties.get('resource_name')
            require(row.get('class') == 'ShaderMaterial' and name in OWNER_NAMES,
                    label+' only four named finish ShaderMaterials', errors)
            require(type(owner) is int and owner > 0,
                    label+' positive integer finish owner metadata', errors)
            if type(owner) is int:
                owner_ids.add(owner)
            names.append(name)
            properties[OWNER_KEY] = 'process-local RamaSurfaceFinish owner'
            normalized_hash = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
            require(normalized_hash not in rows, label+' unique normalized material row', errors)
            rows[normalized_hash] = row
            remap[raw_hash] = normalized_hash
            audit.append({'shot':shot['id'], 'name':name, 'raw_owner_id':owner,
                          'raw_material_sha256':raw_hash, 'normalized_material_sha256':normalized_hash})
        require(len(names) == 4 and set(names) == OWNER_NAMES,
                label+' exact four owned material rows per view', errors)
        shot['materials'] = rows
        references = {key:0 for key in remap}
        for mesh in shot['meshes']:
            for key in ('material_override', 'material_overlay'):
                value = mesh[key]
                if value in remap:
                    references[value] += 1
                    mesh[key] = remap[value]
            surfaces = []
            for value in mesh['surfaces']:
                if value in remap:
                    references[value] += 1
                surfaces.append(remap.get(value, value))
            mesh['surfaces'] = surfaces
        require(all(count > 0 for count in references.values()),
                label+' every normalized material referenced by retained mesh', errors)
    require(len(owner_ids) == 1, label+' one stable finish owner across all four materials/all views', errors)
    return normalized, audit

def differences(a, b, path=''):
    # JSON treats integral numeric values alike; still reject bool/number confusion.
    if isinstance(a, bool) != isinstance(b, bool) or type(a) is not type(b):
        if not (not isinstance(a, bool) and not isinstance(b, bool) and isinstance(a,(int,float)) and isinstance(b,(int,float))):
            return [{'path':path,'a':a,'b':b}]
    if isinstance(a,dict):
        out=[]
        for key in sorted(a.keys()|b.keys()):
            if key not in a or key not in b: out.append({'path':path+'/'+key,'missing':'baseline' if key not in a else 'candidate'})
            else: out.extend(differences(a[key],b[key],path+'/'+key))
        return out
    if isinstance(a,list):
        if len(a)!=len(b): return [{'path':path,'length_a':len(a),'length_b':len(b)}]
        return [row for i,(x,y) in enumerate(zip(a,b)) for row in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [{'path':path,'a':a,'b':b}]

def require(ok, label, errors):
    if not ok: errors.append(label)

def path_index(rows, errors, label):
    result={r['path']:r for r in rows}
    require(len(result)==len(rows),label+' unique paths',errors)
    return result

def finite(value):
    if isinstance(value,float): return math.isfinite(value)
    if isinstance(value,dict): return all(finite(v) for v in value.values())
    if isinstance(value,list): return all(finite(v) for v in value)
    return True

def compare_shot(x,y):
    errors=[]
    require(x['id']==y['id'],'shot ID',errors)
    controls=differences({k:v for k,v in x.items() if k not in SEPARATE}, {k:v for k,v in y.items() if k not in SEPARATE})
    require(not controls,'strict sampled controls equal',errors)
    for row in (x,y):
        require(row.get('serialization_errors')==[],'no serialization failures',errors)
        rig=row.get('hero_skeleton',{})
        require(len(rig.get('bone_names',[]))==len(rig.get('bone_global_poses',[]))==164 and rig.get('signals',0)>0,'full164final-modifier bones',errors)
        mods=rig.get('active_modifiers',[])
        require(bool(mods) and mods[-1]==rig.get('observer_modifier'),'observed last active modifier',errors)
        correlation=row.get('pose_correlation',{})
        require(correlation.get('source')=='RamaMotion.modification_processed' and correlation.get('process_age')==0 and correlation.get('physics_age')==0 and correlation.get('post_draw_age')==(0 if correlation.get('preflight_no_draw') else 1),'fresh final-modifier sample correlation',errors)
        require(set(row.get('pose_signal_counters',{}))==GLOBAL_COUNTERS,'raw pose callback counters recorded',errors)
        require(bool(row.get('nav_manifest_sha256')),'nav manifest recorded',errors)
        require(bool(row.get('environment')) and 'ssao_enabled' in row.get('ao',{}),'actual environment/AO recorded',errors)
        require(finite(row),'finite report',errors)
    a,b=x['frontage'],y['frontage']
    common=['target_path','target_transform','body_path','body_transform','body_metadata','material_ids','data_sha256','active_shape_count','shape_owner_count']
    declaration=differences({k:a.get(k) for k in common},{k:b.get(k) for k in common})
    require(not declaration,'frontage retained identity/metadata/material references',errors)
    require(a['branch']=='baseline' and b['branch']=='candidate','declared branches',errors)
    require(a['target_visible'] and not b['target_visible'] and not a['replacement_present'] and b['replacement_present'],'exact visibility replacement',errors)
    require(a['active_shape_count']==a['shape_owner_count']==b['active_shape_count']==b['shape_owner_count']==1,'sole active shape/owner',errors)
    require(a['shape_class']=='BoxShape3D' and a['box_size']==[18,15,18] and b['shape_class']=='ConcavePolygonShape3D','declared shape classes',errors)
    require(a['body_metadata'].get('authority_id')=='authority-solid-2' and a['body_metadata'].get('dimensions')==[18,15,18] and a['body_metadata'].get('position_base')==[20,0,-28],'real block2 metadata/bounds',errors)
    g=b['geometry']
    require(g['triangles']==2816 and g['surfaces']==3 and g['local_vertices_exact_raw'] and g['body_local_vertices_exact'] and g['world_vertices_equal_approx'] and g['vertex_count_matches'] and g['backface_collision'],'exact raw/body-local vertices and reviewed world transform',errors)
    require(g['bounds']==[[-9,0,-9],[18,15,18]] and g['body_bounds']==[[-9,-7.5,-9],[18,15,18]],'same exact broad bounds',errors)
    require(b['material_identity_reused'] and b['surface_material_ids']==a['material_ids'] and b['new_materials']==b['new_textures']==b['new_lights']==0,'no new material/texture/light resources',errors)
    # Every pre-existing collision object, path and shape-owner node stays present.
    ca=path_index(x['collision_objects'],errors,'baseline collision')
    cb=path_index(y['collision_objects'],errors,'candidate collision')
    require(ca.keys()==cb.keys(),'no added/lost collision object',errors)
    collider_diff=[]
    for path in ca.keys()&cb.keys():
        p,q=copy.deepcopy(ca[path]),copy.deepcopy(cb[path])
        if path==a['body_path']:
            require(len(p['shapes'])==len(q['shapes'])==1,'exactly one target child shape',errors)
            if len(p['shapes'])==len(q['shapes'])==1:
                u,v=p.pop('shapes')[0],q.pop('shapes')[0]
                require(u['class']=='BoxShape3D' and u['size']==[18,15,18] and v['class']=='ConcavePolygonShape3D' and v['faces']==2816 and v['backface_collision'] is True,'declared sole shape replacement',errors)
                require(len(v.get('faces_sha256',''))==64,'actual face hash recorded',errors)
                collider_diff.extend(differences({k:u[k] for k in ('path','disabled','transform')},{k:v[k] for k in ('path','disabled','transform')},path+'/holder'))
                require(u['disabled'] is False and v['disabled'] is False,'target collider enabled',errors)
                require(u['transform']==v['transform']==IDENTITY,'identity target local holder transform',errors)
        collider_diff.extend(differences(p,q,path))
    require(a['body_path'] in ca and a['body_path'] in cb,'target body present',errors)
    require(not collider_diff,'all retained collision controls exact',errors)
    ma=path_index(x['meshes'],errors,'baseline mesh')
    mb=path_index(y['meshes'],errors,'candidate mesh')
    added=set(mb)-set(ma)
    require(not (set(ma)-set(mb)),'old imported meshes retained for restoration',errors)
    require(len(added)==1 and next(iter(added),'').endswith('/ReviewBlock2Frontage/ClosedCivicFrontage'),'one declared candidate visible mesh',errors)
    mesh_diff=[]
    targets=0
    # Mesh paths are scene-relative; frontage target is absolute.
    suffix='/CityArt/block-2'
    for path in ma.keys()&mb.keys():
        p,q=copy.deepcopy(ma[path]),copy.deepcopy(mb[path])
        absolute_path='/'+path
        if suffix in absolute_path:
            tail=absolute_path.split(suffix,1)[1]
            if tail=='' or tail.startswith('/'):
                targets+=1
                require(p.pop('visible') is True and q.pop('visible') is False,'only target subtree hidden',errors)
        mesh_diff.extend(differences(p,q,path))
    require(targets>0,'actual imported target mesh recorded',errors)
    require(not mesh_diff,'all existing geometry/material/transform controls exact',errors)
    if len(added)==1:
        new=mb[next(iter(added))]
        require(new['visible'] is True and new['surfaces']==a['material_ids'] and len(new['surface_vertices'])==3 and sum(new['surface_vertices'])==2816*3,'candidate visible2816tri/3existing surfaces',errors)
        require(new['aabb']==g['bounds'] and new['material_override']=='none' and new['material_overlay']=='none' and new['mesh_path']=='','candidate no hidden new material/source resource',errors)
        require(new['global_transform']==b['candidate_transform']==[[1,0,0],[0,1,0],[0,0,1],[20,0,-28]],'independently known unscaled candidate global transform',errors)
    return {'id':x['id'],'passed':not errors,'errors':errors,'control_differences':controls,'frontage_common_differences':declaration,'retained_collision_differences':collider_diff,'retained_mesh_differences':mesh_diff,'global_frame_counters':{k:[x.get(k),y.get(k)] for k in sorted(GLOBAL_COUNTERS)}}

def compare(a,b):
    errors=[]
    a, owner_a = normalize_finish_owner(a, 'baseline', errors)
    b, owner_b = normalize_finish_owner(b, 'candidate', errors)
    for report,label,branch in [(a,'baseline','baseline'),(b,'candidate','candidate')]:
        require(report['complete'] is True and not report.get('failure') and report['case']=='lane-frontage-review',label+' successful correct case',errors)
        require(report['branch']==branch,label+' branch',errors)
        require(report['source_unchanged'] and report['source_sha256']==report['source_after_sha256'],label+' source unchanged',errors)
        require(bool(report['checks']) and all(r['passed'] is True for r in report['checks']),label+' all native checks pass',errors)
        require([s['id'] for s in report['shots']]==IDS,label+' exact3orderedviews',errors)
        require(isinstance(report['preflight'],bool) and all(s.get('pose_correlation',{}).get('preflight_no_draw') is report['preflight'] for s in report['shots']),label+' pose draw mode matches parent report',errors)
        cleanup=report['audio_cleanup']
        require(cleanup['observed_mixer_ticks']==2 and 0<=cleanup['wait_usec']<=cleanup['budget_usec']==250000 and cleanup['main_cleanup_frames']==8,label+' actual bounded mixer cleanup',errors)
        require(all(report['route_checks'].get(k) is True for k in ['hero_position_held','army_resumed','kit_resumed']),label+' genuine overview return',errors)
    for key in ['case','outer_transport_alias','preflight','renderer','adapter','route_checks']:
        require(not differences(a[key],b[key]),'same '+key,errors)
    sa,sb=a['source_sha256'],b['source_sha256']
    require(sa.keys()==sb.keys(),'same exact source inventory keys',errors)
    allowed=MARKERS|{SELECTION,'res://'+SELECTION}
    source_differences=[key for key in sa.keys()&sb.keys() if sa[key]!=sb[key]]
    require(set(source_differences)<=allowed,'only declared selection/derived manifest source bytes differ',errors)
    selection_keys=[key for key in sa if key.removeprefix('res://')==SELECTION]
    require(len(selection_keys)==1 and all(sa[k]==a['selection_sha256'] and sb[k]==b['selection_sha256'] and sa[k]!=sb[k] for k in selection_keys),'exact inventoried distinct selection JSON',errors)
    for path in ['art/world-finish/lane-frontage-r1/candidate.gd','art/world-finish/lane-frontage-r1/candidate-mesh.json','tools/graphics-six/capture_compact_screens.gd','tools/graphics-six/capture_scene_anchors.gd']:
        require(path in sa and path in sb and sa.get(path)==sb.get(path),'explicit same transitive source '+path,errors)
    rows=[compare_shot(x,y) for x,y in zip(a['shots'],b['shots'])]
    # Shape cannot mutate between reviewed shots without an independent declared variable.
    hashes=[s['shapes'][0]['faces_sha256'] for shot in b['shots'] for s in shot['collision_objects'] if s['path']==shot['frontage']['body_path'] and s['shapes'] and 'faces_sha256' in s['shapes'][0]]
    require(len(hashes)==3 and len(set(hashes))==1,'candidate local faces stable across all3views',errors)
    return {'passed':not errors and all(row['passed'] for row in rows),'finish_owner_metadata_normalization':{'baseline':owner_a,'candidate':owner_b,'scope':'Only exact process-local owner metadata; all other material values remain strict. Per-branch consistency, not direct Node-ID ownership observation.'},'errors':errors,'source_differences':source_differences,'shots':rows,'scope':'Strict full sampled164poses, units/joints, clocks, camera/UI, actual environment/AO/light/material settings, nav and all retained mesh/body controls. Sole block2 visible2816tri frontage and same-body Box-to-Concave localdetail are explicit exceptions. No pixel-quality/continuous-motion/online/GPU acceptance.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=compare(json.loads(args.baseline.read_text()),json.loads(args.candidate.read_text()))
    except (KeyError,TypeError,ValueError,IndexError) as error:
        result={'passed':False,'malformed_report':str(error)}
    result.update({key+'_report_sha256':hashlib.sha256(path.read_bytes()).hexdigest() for key,path in [('baseline',args.baseline),('candidate',args.candidate)]})
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'passed':result['passed'],'errors':result.get('errors',[]),'shots':[{'id':r['id'],'passed':r['passed'],'errors':r['errors']} for r in result.get('shots',[])]}))
    raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':main()
