from pathlib import Path
import json,hashlib
ROOT=Path(__file__).parents[1];OUT=Path(__file__).parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 paths={s:ROOT/'role06'/s/'diagnostic' for s in ['baseline','candidate-r7']};data={s:json.loads((p/'capture.json').read_text()) for s,p in paths.items()};checks=[];images=[]
 for side,d in data.items():
  checks.append({'name':side+' complete unchanged source','passed':d['complete'] and d['source_unchanged'] and d['source_sha256']==d['source_after_sha256']})
  for shot in d['shots']:
   path=paths[side]/(shot['id']+'.png');actual=sha(path);checks.append({'name':side+' '+shot['id']+' original digest','passed':actual==shot['sha256']});images.append({'side':side,'id':shot['id'],'path':str(path),'sha256':actual})
 rows={s:{r['id']:r for r in d['shots']} for s,d in data.items()}
 for id,a in rows['baseline'].items():
  b=rows['candidate-r7'][id]
  fields=['viewport','camera','player_transform','visual_yaw','night','pose_pin','rendered_pose_globals','rendered_pose_pin','face','motion','lod','body_velocity','ground_contact','render_settings','tree_paused','ui_visible','light']
  checks.append({'name':id+' direct paired controls','passed':all(a[k]==b[k] for k in fields),'fields':fields,'different_fields':[k for k in fields if a[k]!=b[k]]})
  dynamics=['cloth_offset','cloth_velocity','hair_offset','hair_velocity','elapsed','reset_count','last_reason']
  checks.append({'name':id+' actual secondary dynamics','passed':all(a['secondary'][k]==b['secondary'][k] for k in dynamics)})
 result={'task':'R3-15','passed':all(x['passed'] for x in checks),'count':len(checks),'checks':checks,'images':images,'capture_report_hashes':{s:sha(p/'capture.json') for s,p in paths.items()},'probe_sha256':sha(__file__),'scope':'Independent direct metadata and original PNG digest comparison. Subjective art disposition is in REVIEW.md; pixel difference is not used as an improvement score.'}
 (OUT/'diagnostic-identity.json').write_text(json.dumps(result,indent=2)+'\n');print(result['passed'],result['count']);assert result['passed']
if __name__=='__main__':main()
