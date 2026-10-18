"""Original compact rigid pauldron: ordinary existing shoulder01.L attachment."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import build_armour as original
from build_armour import ROOT,GLB,SOURCE_SHA,sha

def surface_fn(layer):
 starts=[-.005,.070,.100];ends=[.082,.105,.115];radii=[.111,.091,.076]
 def point(u,v):
  degrees=-5+50*u;theta=math.radians(degrees)
  end=ends[layer]+.005*math.cos(3*theta)+.004*math.cos(theta);s=starts[layer]*(1-v)+end*v
  radius=radii[layer]+.010*max(math.sin(theta),0)-.009*max(-math.sin(theta),0)+.009*math.sin(math.pi*v)-.006*v+.004*math.cos(theta)*math.sin(math.pi*v)
  radius=max(radius,float(original.ENVELOPE([[s,degrees]])[0])+[.018,.012,.008][layer])
  return np.array([radius*math.sin(theta),s,radius*math.cos(theta)])
 return point

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();out=args.output.resolve();assert not out.exists()
 source=ROOT/'assets/heroes/rama-hero.glb';assert sha(source)==SOURCE_SHA;g=GLB(source)
 ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);rest=np.linalg.inv(ib)
 names=[g.doc['nodes'][j]['name'] for j in g.doc['skins'][0]['joints']];assert names[49]=='shoulder01.L' and names[50]=='upperarm01.L'
 original.fit_envelope(g,ib[50]);original.surface_fn=surface_fn
 convert=ib[49]@rest[50];out.mkdir(parents=True);levels={}
 for level in ['near','mid','far']:
  shapes=original.geometry(level)
  for shape in shapes:shape.v=[p for p in (np.c_[np.array(shape.v),np.ones(len(shape.v))]@convert.T)[:,:3]]
  levels[level]=original.write_glb(out/('shoulder-armour-'+level+'.glb'),shapes,{'review_only':True,'default_activation':False,'source_hero_sha256':SOURCE_SHA,'attachment_bone':'shoulder01.L','source_joint_slot':49,'original_geometry':True,'new_bone_writers':0,'secondary_alpha':0})
 manifest={'schema':1,'generator':str(Path(__file__).relative_to(ROOT)),'generator_sha256':sha(__file__),'dependencies':{str(Path(original.__file__).relative_to(ROOT)):sha(original.__file__)},'source_hero_sha256':SOURCE_SHA,
  'attachment':{'bone':'shoulder01.L','index':49,'inverse_bind_matrix':ib[49].tolist(),'global_rest_matrix':rest[49].tolist(),'coordinate_frame':'Source shoulder01.L bone-local metres. Ordinary rigid attachment; no skin/solver/new bone writer.'},
  'levels':levels,'shape':{'outer_arc_degrees':[-5,45],'axial_starts_in_upperarm_rest_m':[-.005,.070,.100],'axial_base_ends_in_upperarm_rest_m':[.082,.105,.115],'shell_thickness_m':[.0035,.003,.003],'edge_radius_m':[.0027,.0023,.0023],'secondary_alpha':0,'form':'Hard domed cap, two short overlapping cobalt lames, rolled gold borders, original five-petal repousse lotus. Medial/back wrap removed; no radius inflation from r4.'},
  'original_reference':{'path':'../yuga/art/references/rama-hanuman-sita.png','sha256':sha(ROOT/'../yuga/art/references/rama-hanuman-sita.png'),'use':'Visual form reference only; no image or mesh extraction.'},
  'scope':'Concrete inactive3LOD original compact sculpture. Source-rest, dense action contacts, imported helper and matched images are independent gates. R4 and all canonical hero arrays remain untouched.'}
 (out/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');assert sha(source)==SOURCE_SHA
 print(json.dumps({k:{n:r[n] for n in ['sha256','triangles','bytes']} for k,r in levels.items()},indent=2))
if __name__=='__main__':main()
