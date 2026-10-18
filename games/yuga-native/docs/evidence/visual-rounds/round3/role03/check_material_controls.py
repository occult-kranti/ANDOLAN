"""Read-only material/roughness control audit; no engine import or rendering."""
from pathlib import Path
import json,sys,hashlib,re
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'art/hero-rama-lod'));from glb_lod import GLB
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths={'woven_baseline':ROOT/'assets/materials/rama-finish/woven-roughness.png','woven_candidate':ROOT/'art/visual-rounds/cloth/textures/woven-roughness-r3.png','hair_unchanged':ROOT/'assets/materials/rama-finish/hair-roughness.png'}
rows={}
for name,path in paths.items():
 im=Image.open(path);a=np.asarray(im.convert('RGB'),float)/255
 rows[name]={'path':str(path),'sha256':sha(path),'mode':im.mode,'size':list(im.size),'red_min':float(a[:,:,0].min()),'red_max':float(a[:,:,0].max()),'red_mean':float(a[:,:,0].mean()),'red_std':float(a[:,:,0].std()),'rgb_channels_equal':bool(np.array_equal(a[:,:,0],a[:,:,1])and np.array_equal(a[:,:,0],a[:,:,2]))}
base=GLB('/workspace/scratch/visual-round2/role-08/face-form-candidate-r6/candidate.glb');groom=GLB('/workspace/scratch/visual-round3/role-08/groom-r6/rama-hero.glb')
finish=(ROOT/'scripts/rama_surface_finish.gd').read_text();shader=(ROOT/'shaders/rama_secondary_cloth.gdshader').read_text();profile=json.loads((ROOT/'art/visual-rounds/cloth/material-profile.json').read_text())
checks={'groom_preserves_all_material_json':base.doc['materials']==groom.doc['materials'],'rough_sampler_linear_no_source_color':bool(re.search(r'uniform sampler2D rough_texture[^;]*filter_linear_mipmap[^;]*;',shader))and 'source_color' not in re.search(r'uniform sampler2D rough_texture[^;]*;',shader)[0],'actual_roughness_multiplies_map': 'roughness_value * (use_rough_texture ? dot(texture(rough_texture, UV), rough_channel)' in shader,'finish_sets_scalar_one_and_red':'"roughness_value":1.0' in finish and '"rough_channel":Vector4(1,0,0,0)'in finish,'woven_profile_targets_only_two_cobalt_materials':set(profile['allowed_surface_names'])=={'Cobalt handwoven silk','Cobalt lotus brocade'},'candidate_retains_specular_038':profile['preserve_specular_value']==.38,'candidate_map_mean_increases':rows['woven_candidate']['red_mean']>rows['woven_baseline']['red_mean'],'candidate_map_variation_decreases':rows['woven_candidate']['red_std']<rows['woven_baseline']['red_std']}
imports={}
for name in ['woven','hair']:
 path=ROOT/f'assets/materials/rama-finish/{name}-roughness.png.import';imports[name]={'sha256':sha(path),'declares_mipmaps_generate':'mipmaps/generate=true'in path.read_text()}
source=[Path(__file__),base.path,groom.path,ROOT/'scripts/rama_surface_finish.gd',ROOT/'scripts/rama_secondary_motion.gd',ROOT/'shaders/rama_secondary_cloth.gdshader',ROOT/'scripts/production_lighting.gd',ROOT/'art/visual-rounds/cloth/material-profile.json']+list(paths.values())
report={'task':'R3-03','source_commit':'0437ea91edf6989ff78c1eeadb3661f4825b60f2','checks':checks,'passed':all(checks.values()),'maps':rows,'import_settings':imports,'source_sha256':{str(p):sha(p)for p in source},'decision':'No light or hair material correction justified by this source audit; use existing woven candidate as the sole roughness change, preserve lights. Enable candidate woven mips in isolated import and verify actual payload. Hair mips remain an explicit possible independent diagnostic, not bundled art correction.','scope':'Source scalar distributions, shader/owner contract and material preservation only. No BRDF luminance, native imported binding or new pixels measured.'}
(OUT/'material-controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':checks,'maps':rows,'imports':imports},indent=2));assert report['passed']
