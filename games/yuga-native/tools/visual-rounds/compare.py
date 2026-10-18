#!/usr/bin/env python3
"""Compare exact scene controls and raw PNGs without changing either capture."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    base=json.loads((a.baseline/'capture.json').read_text())
    candidate=json.loads((a.candidate/'capture.json').read_text())
    assert base['complete'] and candidate['complete'] and base['source_unchanged'] and candidate['source_unchanged']
    index={s['id']:s for s in base['shots']}
    rows=[]
    for c in candidate['shots']:
        b=index[c['id']]
        controls={k:b[k]==c[k] for k in ['viewport','camera','player_transform','visual_yaw','night','pose_pin','face','motion','lod']}
        # R3 observes the final SkeletonModifier3D pose before Godot restores
        # public bone poses. Missing one side is a failed control, never equality.
        for key in ['rendered_pose_pin','body_velocity','ground_contact']:
            if key in b or key in c:
                controls[key] = key in b and key in c and b[key] == c[key]
        if 'secondary' in b or 'secondary' in c:
            # The authored groom intentionally changes vertex counts. Compare
            # the complete dynamics/ownership report separately from those counts.
            controls['secondary_dynamics'] = 'secondary' in b and 'secondary' in c and {
                k:v for k,v in b['secondary'].items() if k not in ['anchored_vertices','masked_vertices']
            } == {k:v for k,v in c['secondary'].items() if k not in ['anchored_vertices','masked_vertices']}
        if 'rendered_pose_pin' in b or 'rendered_pose_pin' in c:
            controls['actual_imported_bounds_passed'] = bool(b.get('bounds',{}).get('passed') and c.get('bounds',{}).get('passed'))
        controls['render_settings'] = b.get('render_settings') == c.get('render_settings')
        controls['ui_visible'] = b.get('ui_visible') == c.get('ui_visible')
        light_common={k:b['light'][k]==c['light'][k] for k in b['light'] if k in c['light']}
        bp,cp=a.baseline/b['file'],a.candidate/c['file']
        assert sha(bp)==b['sha256'] and sha(cp)==c['sha256']
        diff=ImageChops.difference(Image.open(bp).convert('RGB'),Image.open(cp).convert('RGB'))
        rows.append({'id':c['id'],'controls_equal':controls,'common_light_fields_equal':light_common,'light_fields_unobserved_in_baseline':{k:v for k,v in c['light'].items() if k not in b['light']},'baseline_render_settings':b.get('render_settings'),'candidate_render_settings':c.get('render_settings'),'baseline_sha256':b['sha256'],'candidate_sha256':c['sha256'],'baseline_frame':b['render_frame'],'candidate_frame':c['render_frame'],'mean_absolute_RGB_difference_0_to_255':ImageStat.Stat(diff).mean,'changed_bbox':diff.getbbox(),'scope':'Raw pixel difference is descriptive; it does not establish art improvement.'})
    common=base['source_sha256'].keys() & candidate['source_sha256'].keys()
    changed={k:{'before':base['source_sha256'][k],'after':candidate['source_sha256'][k]} for k in sorted(common) if base['source_sha256'][k]!=candidate['source_sha256'][k]}
    result={'complete':True,'baseline':str(a.baseline),'candidate':str(a.candidate),'baseline_report_sha256':sha(a.baseline/'capture.json'),'candidate_report_sha256':sha(a.candidate/'capture.json'),'compared_shots':rows,'changed_common_source_pins':changed,'new_source_metadata_pins':sorted(candidate['source_sha256'].keys()-base['source_sha256'].keys()),'all_pose_camera_controls_equal':all(all(r['controls_equal'].values()) for r in rows),'all_common_light_controls_equal':all(all(r['common_light_fields_equal'].values()) for r in rows)}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'complete':True,'shots':len(rows),'all_pose_camera_controls_equal':result['all_pose_camera_controls_equal'],'all_common_light_controls_equal':result['all_common_light_controls_equal']}))

if __name__=='__main__':main()
