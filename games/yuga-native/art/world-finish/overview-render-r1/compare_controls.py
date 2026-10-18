"""Strict overview review controls. Presentation differences are explicit, never authority."""
import argparse,hashlib,json
from pathlib import Path

PRESENTATION={'hud','overview_composition','overview_scroll','visible_hud_peers','visible_panels','lane_label_effectively_visible'}
COUNTERS={'process_frame','physics_frame','drawn_frame','file','sha256'}

def differences(a, b, path=''):
    if type(a) is not type(b): return [{'path': path, 'a': a, 'b': b}]
    if isinstance(a, dict):
        result = []
        for key in sorted(a.keys() | b.keys()):
            if key not in a or key not in b: result.append({'path': path + '/' + key, 'missing': 'baseline' if key not in a else 'candidate'})
            else: result.extend(differences(a[key], b[key], path + '/' + key))
        return result
    if isinstance(a, list):
        if len(a) != len(b): return [{'path': path, 'length_a': len(a), 'length_b': len(b)}]
        return [entry for i, (x, y) in enumerate(zip(a, b)) for entry in differences(x, y, path + '/' + str(i))]
    return [] if a == b else [{'path': path, 'a': a, 'b': b}]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['baseline','candidate','output']:p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();a=json.loads(args.baseline.read_text());b=json.loads(args.candidate.read_text())
    assert a['complete'] and b['complete'] and len(a['shots'])==len(b['shots'])==3
    results=[]
    for x,y in zip(a['shots'],b['shots']):
        assert x['id']==y['id']
        raw=differences(x,y)
        control=differences({k:v for k,v in x.items() if k not in PRESENTATION|COUNTERS|{'camera'}},{k:v for k,v in y.items() if k not in PRESENTATION|COUNTERS|{'camera'}})
        xc,yc=x['camera'],y['camera']
        camera=differences({k:v for k,v in xc.items() if k!='transform'},{k:v for k,v in yc.items() if k!='transform'})
        basis=differences(xc['transform'][:3],yc['transform'][:3])
        results.append({'id':x['id'],'passed':not control and not camera and not basis,'forbidden_control_differences':control,'camera_nontranslation_differences':camera+basis,'declared_presentation_differences':[r for r in raw if r['path'].split('/')[1] in PRESENTATION|{'camera'}],'global_frame_counters':{k:[x[k],y[k]] for k in ['process_frame','physics_frame','drawn_frame']}})
    report={'passed':all(row['passed'] for row in results),'scope':'Exact original playercamera/full sampled164bone poses/unit root+joints/light/authority clocks/player/collision equality. Candidate changes only overview camera translation and declared information-column/HUD/scroll presentation. No art, temporal, full interaction or hardware acceptance.','baseline_report_sha256':hashlib.sha256(args.baseline.read_bytes()).hexdigest(),'candidate_report_sha256':hashlib.sha256(args.candidate.read_bytes()).hexdigest(),'shots':results}
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'shots':[(r['id'],r['passed']) for r in results]}));raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
