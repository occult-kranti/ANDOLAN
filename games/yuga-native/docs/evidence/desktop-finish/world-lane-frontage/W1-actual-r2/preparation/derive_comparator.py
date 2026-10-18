from pathlib import Path
import hashlib,difflib,json
W=Path(__file__).parent;parent=Path('/workspace/scratch/yuga-frontage-review-r1/harness/owner-metadata-comparator-r1/compare_frontage.py');old=parent.read_text();new=old
new=new.replace("'material_ids','data_sha256','active_shape_count'","'material_ids','active_shape_count'")
new=new.replace("require(not declaration,'frontage retained identity/metadata/material references',errors)","require(not declaration,'frontage retained identity/metadata/material references',errors)\n    require(a['data_sha256']=='117123f32c232dc2c2693bbf0180578feb85396fcddaf1518b7c6d653698f141' and b['data_sha256']=='67950a68d7b6384b8b114987a27efff1f113d44f8fb1b7df8632f3e9217406a2','exact baseline/r2 declared geometry data',errors)")
new=new.replace('2816','4824')
new=new.replace("require(sa.keys()==sb.keys(),'same exact source inventory keys',errors)","r2_inputs={'art/world-finish/lane-frontage-r2/candidate.gd':'b0b6027d551835ffe5f7f99898ec80511426e51de77c6a6016e888f13de98f79','art/world-finish/lane-frontage-r2/candidate-mesh.json':'67950a68d7b6384b8b114987a27efff1f113d44f8fb1b7df8632f3e9217406a2'}\n    helper='tools/graphics-six/capture_scene_anchors.gd'\n    require(set(sb)==set(sa)|set(r2_inputs) and not (set(sa)&set(r2_inputs)),'only two exact declared candidate source additions',errors)\n    require(all(sb.get(k)==v for k,v in r2_inputs.items()),'exact r2 code/data pins',errors)\n    require(sa.get(helper)=='6282cb7e794509c412a38cc66ef2abd0b06c98a1c4ddba72abb301c2adbdc9a9' and sb.get(helper)=='a052a33ed086ec713546021b2a9a3b77ee75ee7fa1e560685b465ec1b92cd43d','exact two-line preload/assertion-only helper successor',errors)")
new=new.replace("allowed=MARKERS|{SELECTION,'res://'+SELECTION}","allowed=MARKERS|{SELECTION,'res://'+SELECTION,helper}")
new=new.replace("'only declared selection/derived manifest source bytes differ'","'only declared selection/manifest/assertion-only helper source bytes differ'")
new=new.replace(",'tools/graphics-six/capture_scene_anchors.gd']:","]:")
(W/'compare_frontage_r2.py').write_text(new);(W/'comparator-r1-r2.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(parent),tofile='compare_frontage_r2.py')))
print(hashlib.sha256(new.encode()).hexdigest())
