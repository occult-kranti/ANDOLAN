#!/usr/bin/env python3
"""Independent symmetry and local smoothness sample for the configured warp."""
import json
import argparse
from pathlib import Path
import numpy as np
from refine import warp

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--config',type=Path,default=HERE/'refinement.json')
parser.add_argument('--output',type=Path,default=HERE/'field-check.json')
args=parser.parse_args()
c=json.loads(args.config.read_text())
# Sample a 3D domain, not just the original mesh vertices. This tests the
# formula for the given configuration, not every continuous coordinate.
x,y,z=np.meshgrid(np.linspace(-.12,.12,49),np.linspace(1.735,1.89,63),
                  np.linspace(.10,.30,7),indexing='ij')
p=np.column_stack((x.ravel(),y.ravel(),z.ravel()))
q=warp(p,c); mirrored=p.copy();mirrored[:,0]*=-1
reflected=warp(mirrored,c);reflected[:,0]*=-1
mirror_error=float(np.abs(q-reflected).max())
eps=1e-5
J=np.stack([(warp(p+v*eps,c)-warp(p-v*eps,c))/(2*eps) for v in np.eye(3)],axis=2)
det=np.linalg.det(J)
assert mirror_error < 1e-12, 'Field is not bilateral across X=0'
assert float(det.min()) > c['quality_bounds']['minimum_jacobian_determinant'], 'Sampled fold'
out_start=c['face_gate']['top'][1]
outside=p[:,1]>=out_start
assert np.array_equal(q[outside],p[outside]), 'Changed a point above the face gate'
result={'scope':'21,609 rest-space samples; no claim of continuous global proof',
        'points':len(p),'max_mirror_error_m':mirror_error,
        'minimum_jacobian_determinant':float(det.min()),
        'max_sampled_displacement_m':float(np.linalg.norm(q-p,axis=1).max()),
        'unchanged_above_y_m':out_start,'unchanged_points_above_gate':int(outside.sum())}
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
