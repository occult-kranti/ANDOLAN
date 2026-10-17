"""R2-10 independent CPU reconstruction and deliberately broken controls.

Candidate source deltas are mapped onto baseline imported vertices. This is
explicitly not a substitute for the candidate's own Godot import or pixels.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path('/workspace/ANDOLAN')
NATIVE = ROOT / 'games/yuga-native'
OUT = Path('/workspace/scratch/visual-round2/role-10')
RUNTIME = Path('/workspace/scratch/visual-round2/role-05/baseline-runtime-r3.json')
parser = argparse.ArgumentParser()
parser.add_argument('--candidate', type=Path, default=Path('/workspace/scratch/visual-round2/role-08/face-form-candidate-r5/candidate.glb'))
parser.add_argument('--output', type=Path, default=OUT/'face-motion-counterexamples.json')
parser.add_argument('--held-ring', type=Path)
parser.add_argument('--candidate-face-report', type=Path)
args = parser.parse_args()
CANDIDATE = args.candidate
HELD = args.held_ring or CANDIDATE.parent / 'reconstruction.held-ring.json'
BASELINE = NATIVE / 'assets/heroes/rama-hero.glb'
sys.path.insert(0, str(NATIVE / 'art/hero-rama-lod'))
from glb_lod import GLB
spec = importlib.util.spec_from_file_location('role05', NATIVE / 'docs/evidence/visual-rounds/round2/role05/analyze_deformation.py')
role05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(role05)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def cpu(mesh, poses, weights):
    points = mesh['p'].copy()
    for i, name in enumerate(mesh['shape_names']):
        points += weights.get(name, 0) * mesh['d'][i]
    out = np.zeros_like(points)
    for joint_index, bind in enumerate(mesh['binds']):
        influence = np.sum(np.where(mesh['j'] == joint_index, mesh['w'], 0), axis=1)
        rows = np.flatnonzero(influence)
        if len(rows):
            matrix = np.asarray(poses[bind['name']]) @ mesh['inv'][joint_index]
            transformed = points[rows] @ matrix[:3, :3].T + matrix[:3, 3]
            out[rows] += transformed * influence[rows, None]
    return out

def ray_front(vertices, indices, xy):
    # Independent signed-area barycentric +Z ray, no role05 ray helper.
    tri = vertices[indices]
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    denominator = (b[:, 1]-c[:, 1])*(a[:, 0]-c[:, 0]) + (c[:, 0]-b[:, 0])*(a[:, 1]-c[:, 1])
    valid = np.abs(denominator) > 1e-13
    denom = np.where(valid, denominator, 1)
    u = ((b[:, 1]-c[:, 1])*(xy[0]-c[:, 0]) + (c[:, 0]-b[:, 0])*(xy[1]-c[:, 1]))/denom
    v = ((c[:, 1]-a[:, 1])*(xy[0]-c[:, 0]) + (a[:, 0]-c[:, 0])*(xy[1]-c[:, 1]))/denom
    w = 1-u-v
    hits = valid & (u >= -1e-6) & (v >= -1e-6) & (w >= -1e-6)
    return float(np.max(u[hits]*a[hits,2]+v[hits]*b[hits,2]+w[hits]*c[hits,2])) if hits.any() else -100.

checks = []
def check(name, passed, **data):
    checks.append(dict(name=name, passed=bool(passed), **data))
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)

runtime = json.loads(RUNTIME.read_text())
baseline = role05.read_meshes(runtime)
candidate = copy.deepcopy(baseline)
source, changed = GLB(BASELINE), GLB(CANDIDATE)
face = ('RamaFace', 'Rama warm skin')
body = ('RamaHero', 'Rama warm skin')
lip = ('RamaHero', 'Natural lips')
for key, mi, pi in [(face,1,0), (body,2,11), (lip,2,12)]:
    accessor = source.doc['meshes'][mi]['primitives'][pi]['attributes']['POSITION']
    before, after = source.array(accessor), changed.array(accessor)
    distance, indices = cKDTree(before).query(baseline[key]['p'])
    check('Imported baseline maps to source: '+str(key), distance.max()<2e-7, maximum_mapping_error_m=float(distance.max()))
    candidate[key]['p'] += (after-before)[indices]
    bounds = changed.doc['accessors'][accessor]
    check('Corrected candidate POSITION bounds: '+str(key), np.array_equal(after.min(axis=0),bounds['min']) and np.array_equal(after.max(axis=0),bounds['max']))

meta = json.loads((NATIVE/'art/hero-rama-face/candidate.json').read_text())
coords = np.asarray([[r['position'][0],r['position'][2],-r['position'][1]] for r in meta['boundary']])
fd, fi = cKDTree(baseline[face]['p']).query(coords)
bd, bi = cKDTree(baseline[body]['p']).query(coords)
check('All 146 boundary witnesses independently remap',len(fi)==146 and max(fd.max(),bd.max())<2e-7)
ld, li = cKDTree(baseline[body]['p']).query(baseline[lip]['p'])
lip_rows = np.flatnonzero(ld<1e-7)
held = np.asarray(json.loads(HELD.read_text())['positions_gltf_m'])
hd, hi = cKDTree(baseline[face]['p']).query(held)
held_delta = float(np.linalg.norm(candidate[face]['p'][hi]-baseline[face]['p'][hi],axis=1).max())
held_morph = float(np.linalg.norm(candidate[face]['d'][:,hi],axis=2).max())
check('Exact 288 held source positions and all four target deltas fixed',len(held)==288 and hd.max()<2e-7 and held_delta==0 and held_morph==0,maximum_rest_delta_m=held_delta,maximum_target_delta_m=held_morph)

rows=[]
maximum_reference_error=0
for sample in runtime['samples']:
    p={key:cpu(mesh,sample['bone_global_poses'],sample['morph_weights']) for key,mesh in candidate.items()}
    base_face=cpu(baseline[face],sample['bone_global_poses'],sample['morph_weights'])
    reference=role05.skin(baseline[face],sample['bone_global_poses'],sample['morph_weights'])
    maximum_reference_error=max(maximum_reference_error,float(abs(base_face-reference).max()))
    seam=float(np.linalg.norm(p[face][fi]-p[body][bi],axis=1).max())
    lip_gap=float(np.linalg.norm(p[lip][lip_rows]-p[body][li[lip_rows]],axis=1).max())
    rows.append(dict(id=sample['id'],seam_m=seam,lip_gap_m=lip_gap,finite=all(np.isfinite(v).all()for v in p.values())))
check('Independent bone-accumulation evaluator agrees with role05 slot evaluator',maximum_reference_error<1e-12,maximum_difference_m=maximum_reference_error)
check('37 actual baseline poses with mapped candidate retain finite attachments',len(rows)==37 and all(r['finite'] and r['seam_m']<.00005 and r['lip_gap_m']<.00005 for r in rows),samples=len(rows),maximum_boundary_m=max(r['seam_m']for r in rows),maximum_lip_m=max(r['lip_gap_m']for r in rows),lip_vertex_witnesses=len(lip_rows))

rest=runtime['bone_global_rests']
eye_keys=[('RamaHero',n) for n in ['Warm sclera','Deep brown iris','Pupil']]
eyes=[];eye_tri=[];offset=0
for key in eye_keys:
    eyes.append(cpu(candidate[key],rest,{}));eye_tri.append(candidate[key]['tri']+offset);offset+=len(eyes[-1])
eyes=np.concatenate(eyes);eye_tri=np.concatenate(eye_tri)
ray_xy={s:[(c[0]+dx,c[2]+dy) for dx in np.linspace(-.010,.010,9)for dy in np.linspace(-.003,.004,7)]for s,c in meta['eyeOriginsBlender'].items()}
eye_depth={s:np.array([ray_front(eyes,eye_tri,p)for p in points])for s,points in ray_xy.items()}
def visibility(mesh,weights,eye_push=0):
    p=cpu(mesh,rest,weights)
    return {s:int(np.sum(np.array([ray_front(p,mesh['tri'],xy)for xy in points])<eye_depth[s]+eye_push-.0002))for s,points in ray_xy.items()}

grid=[]
for left,right in [(0,0),(.25,0),(.5,0),(.75,0),(1,0),(0,.25),(0,.5),(0,.75),(0,1),(.25,.75),(.75,.25),(.5,.5),(1,1)]:
    weights=role05.target(left,right)
    a,b=visibility(baseline[face],weights),visibility(candidate[face],weights)
    grid.append(dict(left=left,right=right,baseline_visible=a,candidate_visible=b))
check('Independent actual-eye rays find no new visibility at 13 partial/full/asymmetric combinations',all(r['baseline_visible']==r['candidate_visible']for r in grid),samples=grid)
check('Independent full single and combined blink coverage',all((r['left']!=1 or r['candidate_visible']['L']==0) and (r['right']!=1 or r['candidate_visible']['R']==0)for r in grid))

broken=copy.deepcopy(candidate[face]);broken['p'][fi[0],2]+=.001
gap=float(np.linalg.norm(cpu(broken,rest,{})[fi]-cpu(candidate[body],rest,{})[bi],axis=1).max())
check('Counterexample: 1 mm attachment displacement is rejected',gap>.00005,measured_gap_m=gap)
closed=visibility(candidate[face],role05.target(1,1))
broken=copy.deepcopy(candidate[face]);broken['d'][broken['shape_names'].index('rama_blink_left')]=0
lost=visibility(broken,role05.target(1,1))
check('Counterexample: missing left full-blink target exposes actual eye',lost['L']>closed['L'],control=closed,mutant=lost)
half=visibility(candidate[face],role05.target(.5,.5))
check('Counterexample: full closure substituted at half phase is detected',half!=closed,half_visible=half,overclosed_visible=closed)
penetration=visibility(candidate[face],role05.target(1,1),eye_push=.020)
check('Counterexample: 20 mm forward eye displacement breaches closure',any(penetration[s]>closed[s]for s in closed),control=closed,mutant=penetration)
baseline_fail=json.loads((Path('/workspace/scratch/visual-round2/role-08')/'baseline-face-check.json').read_text())
candidate_fail=json.loads((args.candidate_face_report or CANDIDATE.parent/'face-check.json').read_text())
fail0=[c for c in baseline_fail['checks']if not c['passed']]
fail1=[c for c in candidate_fail['checks']if not c['passed']]
check('Pre-existing two open-cornea failures remain explicitly identical',len(fail0)==2 and fail0==fail1,failures=fail1,total_each=19)
result=dict(task='R2-10',passed=all(c['passed']for c in checks),checks=checks,count=len(checks),actual_baseline_pose_samples=rows,source_pins={str(p):sha(p)for p in [Path(__file__),RUNTIME,Path(runtime['imported_mesh_path']),BASELINE,CANDIDATE,HELD,Path(role05.__file__)]},scope='Independent CPU skin evaluator plus independent ray implementation. Candidate source deltas mapped to actual baseline imported vertices; candidate Godot import and 36 adjacent raw images NOT reviewed by this report. Static source-to-baseline replay does not establish continuous art acceptance, collision-free geometry, full locomotion or AAA parity.',remaining_gates=['Actual candidate imported arrays replay','36 adjacent baseline/candidate raw frames inspected individually with exact source pins','Rendered open/partial/full expression and aim/extreme contact review'])
OUT.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=result['passed'],count=len(checks),report=str(args.output))))
sys.exit(0 if result['passed']else 1)
