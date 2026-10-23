#!/usr/bin/env python3
"""Verify an actual capture separately from source-only lifecycle tests."""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image, ImageChops

def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--receipt',type=Path);a=p.parse_args()
 capture=a.capture.resolve();data=json.loads((capture/'capture.json').read_text());receipt=a.receipt if a.receipt else capture/'runner-report.json';runner=json.loads(receipt.read_text());rows=[]
 def check(label,condition,evidence=None):rows.append({'case':label,'passed':bool(condition),'evidence':evidence})
 frames=data['samples'];check('actual Forward+ software adapter',data['renderer']=='forward_plus' and any(x in data['adapter'].lower() for x in ['llvmpipe','lavapipe']),data['adapter'])
 check('all72 advancing frames and3 controls',data['frames']==72 and len(frames)==72 and len(data['controls'])==3)
 check('timestamps advance exactly at simulated12fps',all(abs(f['simulation_s']-i/12)<1e-7 for i,f in enumerate(frames)))
 check('explicit lamp clock advances continuously',all(abs(f['lamp']['phase']-(i+1)/12)<1e-5 for i,f in enumerate(frames)))
 check('software adapter has actual nonzero draw submissions',all(f['draw_calls']>0 and f['rendered_objects']>=4 for f in frames))
 if 'framing_passed' in data:
  check('unoccluded conservative mesh AABBs fit below caption',data['framing_passed'] and all(f['effect_screen_bounds']['fits'] for f in frames))
  check('advancing sequence retains directional shadows',data['sequence_directional_shadows'])
 check('three clear presentation variants',all(not f['day'] and not f['reduced'] for f in frames[:36]) and all(f['day'] and not f['reduced'] for f in frames[36:60]) and all(not f['day'] and f['reduced'] for f in frames[60:]))
 check('effect bounds and finite transforms retained',all(f['effects']['finite'] and f['effects']['active']<=1 and f['effects']['allocated_impacts']<=1 for f in frames))
 check('three cast contacts actually render',sum(1 for i,f in enumerate(frames) if f['effects']['impacts']==1 and (i==0 or frames[i-1]['effects']['impacts']==0))==3)
 check('pool survives contact expiry and is reused',any(f['effects']['pooled_impacts']==1 for f in frames) and max(f['effects']['allocated_impacts'] for f in frames)==1)
 check('natural end before explicit reset',data['final_before_reset']['active']==0 and data['final_before_reset']['impacts']==0 and data['final_before_reset']['pooled_impacts']==1,data['final_before_reset'])
 check('reset clears both active and pool',data['after_reset']['active']==0 and data['after_reset']['allocated_impacts']==0)
 check('staged event stream has no rejections',data['final_before_reset']['counts']['invalid']==0 and data['final_before_reset']['counts']['stale']==0,data['final_before_reset']['counts'])
 reduced=[f['lamp']['light_energy'] for f in frames[60:]];full=[f['lamp']['light_energy'] for f in frames[:36]]
 check('reduced intensity lowers light while preserving cue',0<max(reduced)<min(full) and all(f['lamp']['visible'] for f in frames),{'full_range':[min(full),max(full)],'reduced_range':[min(reduced),max(reduced)]})
 images=[]
 for row in runner['frame_files']:
  path=capture/row['file'];check('file hash '+row['file'],path.stat().st_size==row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'])
 for f in frames:
  image=Image.open(capture/f['file']).convert('RGB');images.append(image)
 check('all actual frame dimensions match',all(i.size==(960,640) for i in images))
 def region(values):
  x,y,w,h=map(int,values);return(x,y,x+w,y+h)
 roi=region(data['sequence_flame_roi']);normal_hashes={hashlib.sha256(i.crop(roi).tobytes()).hexdigest() for i in images[:36]};reduced_hashes={hashlib.sha256(i.crop(roi).tobytes()).hexdigest() for i in images[60:]}
 check('rendered flame region actually changes over time',len(normal_hashes)>24,{'unique_normal_flame_crops':len(normal_hashes),'roi':roi})
 check('reduced-motion flame region remains still',len(reduced_hashes)==1,{'unique_reduced_flame_crops':len(reduced_hashes)})
 controls=data['controls'];check('mask controls hold phase and local light fixed',len({c['lamp_phase'] for c in controls})==1 and all(c['local_light_energy']==0 for c in controls))
 if 'framing_passed' in data:check('only matched controls disable directional shadows',all(c['directional_shadows']==False for c in controls))
 control_images=[Image.open(capture/c['file']).convert('RGB') for c in controls]
 mask_roi=region(data['control_flame_roi']);difference=ImageChops.difference(control_images[0],control_images[1]);crop=difference.crop(mask_roi)
 def changed_pixels(image):
  r,g,b=image.split();maximum=ImageChops.lighter(ImageChops.lighter(r,g),b);return sum(maximum.histogram()[4:])
 changed=changed_pixels(crop)
 check('mask removes visible source pixels in projected flame box',changed>20,{'changed_pixels_over3':changed,'roi':mask_roi})
 # Only the subtitle differs outside the projection; exclude that text band.
 difference.paste((0,0,0),mask_roi);difference.paste((0,0,0),(0,0,960,95))
 outside=changed_pixels(difference)
 check('mask leaves remainder of matched view stable',outside<15,{'changed_pixels_outside_mask_and_subtitle':outside})
 check('replacement visibly fills masked region',ImageChops.difference(control_images[1],control_images[2]).crop(mask_roi).getbbox() is not None)
 passed=all(r['passed'] for r in rows);result={'passed':passed,'checks':rows,'cases':len(rows),'scope':'Actual pixel, temporal, source-hash and lifecycle evidence for staged isolated presentation; no gameplay authority, GPU throughput, final-art approval or hero animation proof'}
 a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':passed,'cases':len(rows),'report':str(a.report),'failures':[r['case'] for r in rows if not r['passed']]}));raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
