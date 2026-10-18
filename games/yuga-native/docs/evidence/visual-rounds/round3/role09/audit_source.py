from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image
from glb_read import GLB,sha
repo=Path('/workspace/ANDOLAN');native=repo/'games/yuga-native';out=Path(__file__).parent
checks=[];rows=[]
def check(name,ok,**facts):checks.append({'name':name,'passed':bool(ok),**facts})
manifest=json.load(open('/workspace/scratch/visual-round3/role-08/groom-r6/groom-manifest.json'))
for level,item in manifest['levels'].items():
 a,b=GLB(item['source']),GLB(item['output']);p=b.doc['meshes'][2]['primitives'][0];first=item['retained_vertices'];attrs=p['attributes'];c=b.array(attrs['COLOR_0'],True);n=b.array(attrs['NORMAL']);t=b.array(attrs['TANGENT'])
 check(level+' exact material/sampler/texture/image JSON',all(a.doc.get(k)==b.doc.get(k) for k in ['materials','samplers','textures','images']))
 check(level+' embedded image bytes exact',all(a.image_bytes(x)==b.image_bytes(y) for x,y in zip(a.doc['images'],b.doc['images'])))
 material=b.doc['materials'][p['material']]
 check(level+' opaque double-sided hair with exact material name',material.get('alphaMode','OPAQUE')=='OPAQUE' and material.get('doubleSided') is True and material['name']=='Swept black hair')
 check(level+' normalized alpha semantic new mask',np.all(c[:,:3]==1) and c[first:,3].min()==0 and 0<c[first:,3].max()<=.78001,actual_max=float(c[first:,3].max()))
 check(level+' authored new TBN orthonormal handed',np.max(abs(np.linalg.norm(n[first:],axis=1)-1))<1e-5 and np.max(abs(np.linalg.norm(t[first:,:3],axis=1)-1))<1e-5 and np.max(abs((n[first:]*t[first:,:3]).sum(1)))<1e-5 and np.all(abs(t[first:,3])==1))
 protected=['skins','animations'];check(level+' rig and embedded clips JSON exact',all(a.doc[k]==b.doc[k] for k in protected))
 rows.append({'level':level,'source_sha256':sha(a.path),'candidate_sha256':sha(b.path),'material_count':len(b.doc['materials']),'image_count':len(b.doc['images']),'new_alpha_displacement_max_m':float((c[first:,3]**2*.018).max())})
profile=json.load(open(native/'art/visual-rounds/cloth/material-profile.json'));tex=native/profile['texture'];im=Image.open(tex);pixels=np.array(im);linear=pixels.astype(float)/255
shader=(native/'shaders/rama_secondary_cloth.gdshader').read_text();finish=(native/'scripts/rama_surface_finish.gd').read_text()
check('woven texture is scalar linear-data PNG',im.mode=='L' and im.size==(1024,1024) and 'srgb' not in {k.lower() for k in im.info} and 'gamma' not in im.info)
check('shader red roughness channel is independent of base sRGB', 'uniform sampler2D rough_texture : hint_default_white, filter_linear_mipmap, repeat_enable;' in shader and 'rough_channel' in shader and 'base_texture : source_color' in shader and 'rough_texture : source_color' not in shader)
check('opacity does not consume alpha motion mask','ALPHA =' not in shader and 'weight * weight' in shader)
# Counterexample: a color/packed-map accidentally routed through the RED slot
# visibly differs. This measures an independent gate rather than relaxing it.
packed=np.stack([np.full_like(linear,.1),linear,np.full_like(linear,.9)],axis=-1)
check('wrong channel adversary is distinguishable',float(abs(packed[:,:,0]-linear).max())>.6)
check('actual texture remains moderate roughness',float(linear.min())>=.75 and float(linear.max())<=.83,minimum=float(linear.min()),mean=float(linear.mean()),maximum=float(linear.max()))
check('source profile scopes material replacement and resource sharing',profile['allowed_surface_names']==['Cobalt handwoven silk','Cobalt lotus brocade'] and profile['channel']=='RED' and profile['roughness_multiplier']==1 and profile['mipmaps_generate'] is True)
result={'task':'R3-09','passed':all(x['passed'] for x in checks),'count':len(checks),'checks':checks,'levels':rows,'texture_sha256':sha(tex),'source_hashes':{str(x.relative_to(repo)):sha(x) for x in [native/'scripts/rama_surface_finish.gd',native/'scripts/rama_secondary_motion.gd',native/'shaders/rama_secondary_cloth.gdshader',native/'art/visual-rounds/cloth/material-profile.json',Path(__file__),out/'glb_read.py']},'scope':'Independent source/material/channel audit. Imported lifecycle and actual resource format require separate staged engine evidence. Baseline secondary shader still retains old TBN after displacement; optional frame experiment excluded.'}
(out/'source-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'count':len(checks),'failed':[x for x in checks if not x['passed']]}))
