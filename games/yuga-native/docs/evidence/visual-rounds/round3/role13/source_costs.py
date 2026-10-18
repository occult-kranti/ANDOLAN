"""Independent accessor/view accounting; source bytes are not GPU allocation."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parents[1]/'role09'))
from glb_read import GLB,sha
OUT=Path(__file__).parent
MAN=Path('/workspace/scratch/visual-round3/role-08/groom-r6/groom-manifest.json')
def active_accessors(doc):
 ids=set()
 for mesh in doc['meshes']:
  for p in mesh['primitives']:
   ids.update(p['attributes'].values())
   if 'indices' in p:ids.add(p['indices'])
   for t in p.get('targets',[]):ids.update(t.values())
 for skin in doc.get('skins',[]):
  if 'inverseBindMatrices' in skin:ids.add(skin['inverseBindMatrices'])
 for a in doc.get('animations',[]):
  for s in a['samplers']:ids.update([s['input'],s['output']])
 return ids
def measure(g):
 rows=[]
 for mi,mesh in enumerate(g.doc['meshes']):
  for pi,p in enumerate(mesh['primitives']):
   assert p.get('mode',4)==4
   vertices=g.doc['accessors'][p['attributes']['POSITION']]['count'];indices=g.doc['accessors'][p['indices']]['count'] if 'indices' in p else vertices
   rows.append({'mesh':mi,'primitive':pi,'material':g.doc['materials'][p['material']]['name'],'vertices':vertices,'triangles':indices//3})
 active=active_accessors(g.doc);views=set()
 for a in active:
  accessor=g.doc['accessors'][a]
  if 'bufferView' in accessor:views.add(accessor['bufferView'])
  if 'sparse' in accessor:views.update(accessor['sparse'][kind]['bufferView'] for kind in ['indices','values'])
 views.update(i['bufferView'] for i in g.doc.get('images',[]) if 'bufferView' in i)
 deadviews=set(range(len(g.doc['bufferViews'])))-views
 return {'file_bytes':len(g.raw),'binary_bytes':len(g.binary),'active_triangles':sum(r['triangles'] for r in rows),'active_vertices_sum':sum(r['vertices'] for r in rows),'active_buffer_view_bytes':sum(g.doc['bufferViews'][i]['byteLength'] for i in views),'unreferenced_buffer_view_bytes':sum(g.doc['bufferViews'][i]['byteLength'] for i in deadviews),'unreferenced_views':sorted(deadviews),'embedded_image_bytes':sum(len(g.image_bytes(i)) for i in g.doc.get('images',[])),'materials':len(g.doc['materials']),'images':len(g.doc.get('images',[])),'rows':rows}
def main():
 manifest=json.loads(MAN.read_text());levels={};checks=[]
 for level,entry in manifest['levels'].items():
  old=GLB(entry['source']);new=GLB(entry['output']);a=measure(old);b=measure(new)
  hair=next(r for r in b['rows'] if r['material']=='Swept black hair');prior=next(r for r in a['rows'] if r['material']=='Swept black hair')
  expected=(29448,13450,6444)[['near','mid','far'].index(level)]
  checks.append({'name':level+' independent hair triangle total','passed':hair['triangles']==expected,'actual':hair['triangles']})
  checks.append({'name':level+' preserves complete old binary prefix','passed':new.binary[:len(old.binary)]==old.binary})
  oldp=old.doc['meshes'][2]['primitives'][0];oldids=set(oldp['attributes'].values())|{oldp['indices']};oldviews={old.doc['accessors'][a]['bufferView'] for a in oldids}
  checks.append({'name':level+' old hair views are unreferenced','passed':oldviews<=set(b['unreferenced_views'])})
  levels[level]={'source_sha256':sha(old.path),'candidate_sha256':sha(new.path),'baseline':a,'candidate':b,'hair_triangles_delta':hair['triangles']-prior['triangles'],'added_file_bytes':len(new.raw)-len(old.raw),'appended_binary_bytes':len(new.binary)-len(old.binary),'old_hair_retained_dead_bytes':sum(old.doc['bufferViews'][v]['byteLength'] for v in oldviews)}
 result={'task':'R3-13','passed':all(x['passed'] for x in checks),'checks':checks,'levels':levels,'source_manifest_sha256':sha(MAN),'probe_sha256':sha(__file__),'scope':'Independent active accessor, referenced buffer-view and retained byte counts. Distinct views assumed nonoverlapping as authored. Unreferenced payload remains in package; runtime mesh arrays omit it. No VRAM, FPS, draw-call or load-time claims.'}
 (OUT/'source-costs.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:{n:v for n,v in x.items() if n not in ['baseline','candidate']}|{'baseline_triangles':x['baseline']['active_triangles'],'candidate_triangles':x['candidate']['active_triangles'],'file_bytes':x['candidate']['file_bytes'],'unreferenced_bytes':x['candidate']['unreferenced_buffer_view_bytes']} for k,x in levels.items()},indent=2));assert result['passed']
if __name__=='__main__':main()
