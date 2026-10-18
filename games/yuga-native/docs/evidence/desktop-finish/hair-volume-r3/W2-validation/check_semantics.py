"""Independent census comparison; uses frozen exported semantic records, no Blender."""
from pathlib import Path
import argparse,copy,gzip,hashlib,json
PROJECT=Path(__file__).resolve().parents[5]
def read(p):return json.loads(gzip.decompress(p.read_bytes())if p.suffix=='.gz'else p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();assert not args.output.exists()
 parent=PROJECT/'docs/evidence/desktop-finish/hair-sculpt-design/W2-clay-framing-r3/semantic-after.json';beforepath=args.build/'semantic-before.json.gz';afterpath=args.build/'semantic-after.json.gz';before=read(beforepath);after=read(afterpath);checks=[]
 def check(name,passed,**facts):checks.append(dict(name=name,passed=bool(passed),**facts))
 check('owner before census equals independently retained parent',read(parent)==before)
 for category in ['cameras','lights','worlds','scene']:check(category+' exact',before[category]==after[category])
 sources={k for k in after['objects']if k.startswith('SOURCE_LOFT_')};check('exactly six new named source mesh objects',len(sources)==6 and set(after['objects'])-set(before['objects'])==sources and set(after['meshes'])-set(before['meshes'])==sources)
 for category in ['objects','meshes']:
  protected={k:v for k,v in before[category].items()if k!='EDITABLE_WholeHair_CoarseClay'}
  check(category+' all existing nonhair records exact',all(after[category].get(k)==v for k,v in protected.items()),protected_records=len(protected))
 bm=copy.deepcopy(before['materials']);am=copy.deepcopy(after['materials']);name='Neutral warm clay — design only';bu=bm[name]['properties'].pop('users');au=am[name]['properties'].pop('users')
 check('material shaders and all properties exact except six expected extra users',bm==am and au==bu+6,before_users=bu,after_users=au)
 check('source cages hidden only from render and retain subdivision1',all(after['objects'][k]['hide_render']and not after['objects'][k]['hide_viewport']and len(after['objects'][k]['modifiers'])==1 and after['objects'][k]['modifiers'][0]['type']=='SUBSURF'and after['objects'][k]['modifiers'][0]['levels']==1 for k in sources))
 union=after['objects']['EDITABLE_WholeHair_CoarseClay'];check('derived union visible and no modifiers',not union['hide_render']and not union['hide_viewport']and not union['modifiers'])
 check('derived transform exact',union['matrix_world']==before['objects']['EDITABLE_WholeHair_CoarseClay']['matrix_world']and union['matrix_basis']==before['objects']['EDITABLE_WholeHair_CoarseClay']['matrix_basis'])
 result=dict(scope='Independent equality of exported persistent semantic records, not an independent reload of the saved blend. No render or art acceptance.',passed=all(c['passed']for c in checks),checks=checks,inputs=[dict(path=str(x),sha256=sha(x))for x in [parent,beforepath,afterpath]],checker_sha256=sha(Path(__file__)))
 args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(0 if result['passed']else 1)
if __name__=='__main__':main()
