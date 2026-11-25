#!/usr/bin/env python3
"""Make a reversible, bounded rest-space facial candidate from the existing rig.

Requires Python 3 and NumPy. Preserves animation, indices, joints, weights, UVs,
images and material assignments. It appends position/normal/tangent accessors;
the historical GLB and its bytes are never overwritten.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "hero-rama-lod"))
from glb_lod import GLB


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smooth(a, b, v):
    t = np.clip((v - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def warp(points, config):
    x, y, z = points.T
    g = config["face_gate"]
    gate = (smooth(*g["bottom"], y) * (1 - smooth(*g["top"], y)) * smooth(*g["front"], z))
    out = points.copy()
    # Gaussian pair is evaluated separately on each side, but coincides at the
    # centerline when x_abs=0. A smooth sign factor avoids a seam at X=0.
    for form in config["forms"]:
        a, b = form["x_abs"], form["radius_x"]
        lateral = .5 * (np.exp(-((x-a)/b)**2) + np.exp(-((x+a)/b)**2)) if a else np.exp(-(x/b)**2)
        vertical = np.exp(-((y - form["y"]) / form["radius_y"]) ** 2)
        strength = gate * lateral * vertical
        out[:, 0] += form["outward_m"] * strength * np.tanh(x / .012)
        out[:, 1] += form["up_m"] * strength
        out[:, 2] += form["forward_m"] * strength
    return out


class Writer:
    def __init__(self, source):
        self.doc = source.doc
        self.data = bytearray(source.binary[:self.doc['buffers'][0]['byteLength']])

    def attribute(self, values, kind, bounds=False):
        arr = np.asarray(values, dtype='<f4')
        self.data.extend(b'\0' * (-len(self.data) % 4))
        v = len(self.doc['bufferViews'])
        self.doc['bufferViews'].append({'buffer':0, 'byteOffset':len(self.data), 'byteLength':arr.nbytes, 'target':34962})
        self.data.extend(arr.tobytes())
        a = {'bufferView':v, 'componentType':5126, 'count':len(arr), 'type':kind}
        if bounds:
            a['min'] = arr.min(axis=0).tolist(); a['max'] = arr.max(axis=0).tolist()
        i = len(self.doc['accessors']); self.doc['accessors'].append(a)
        return i

    def save(self, path):
        self.doc['buffers'][0]['byteLength'] = len(self.data)
        self.data.extend(b'\0' * (-len(self.data) % 4))
        j = json.dumps(self.doc, ensure_ascii=False, separators=(',', ':')).encode()
        j += b' ' * (-len(j) % 4)
        payload = struct.pack('<4sII', b'glTF', 2, 28 + len(j) + len(self.data))
        payload += struct.pack('<II', len(j), 0x4e4f534a) + j
        payload += struct.pack('<II', len(self.data), 0x004e4942) + self.data
        path.write_bytes(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=HERE/'refinement.json')
    parser.add_argument('--output', type=Path, default=HERE/'hanuman-face-candidate.glb')
    parser.add_argument('--report', type=Path, default=HERE/'refinement-report.json')
    args = parser.parse_args()
    c = json.loads(args.config.read_text()); source = (HERE / c['source']).resolve()
    if source == args.output.resolve(): raise ValueError('Refusing to overwrite baseline')
    if digest(source) != c['source_sha256']: raise ValueError('Unexpected baseline digest')
    glb = GLB(source); writer = Writer(glb)
    reports = []
    for mi, pi, p in glb.primitives():
        name = glb.doc['materials'][p['material']]['name']
        if name not in c['affected_materials']: continue
        attrs = p['attributes']; points = glb.array(attrs['POSITION']).astype(np.float64)
        adjusted = warp(points, c); distance = np.linalg.norm(adjusted - points, axis=1)
        eps = 1.e-5
        J = np.stack([(warp(points + v * eps, c) - warp(points - v * eps, c)) / (2 * eps) for v in np.eye(3)], axis=2)
        determinants = np.linalg.det(J)
        if determinants.min() < c['quality_bounds']['minimum_jacobian_determinant']: raise ValueError('Warp folds')
        if distance.max() > c['quality_bounds']['maximum_displacement_m']: raise ValueError('Warp exceeds scope')
        n = glb.array(attrs['NORMAL']).astype(float)
        normal = np.linalg.solve(J.transpose(0,2,1), n[:,:,None])[:,:,0]
        normal /= np.linalg.norm(normal, axis=1, keepdims=True).clip(1.e-10)
        unchanged = distance < 1.e-10; normal[unchanged] = n[unchanged]
        attrs['POSITION'] = writer.attribute(adjusted, 'VEC3', bounds=True)
        attrs['NORMAL'] = writer.attribute(normal, 'VEC3')
        if 'TANGENT' in attrs:
            old = glb.array(attrs['TANGENT']).astype(float)
            tangent = (J @ old[:,:3,None])[:,:,0]
            tangent -= normal * np.einsum('ij,ij->i', normal, tangent)[:,None]
            tangent /= np.linalg.norm(tangent,axis=1,keepdims=True).clip(1.e-10)
            tangent[unchanged] = old[unchanged,:3]
            attrs['TANGENT'] = writer.attribute(np.column_stack((tangent,old[:,3])), 'VEC4')
        reports.append({'mesh':mi,'primitive':pi,'material':name,'vertices':len(points),
                        'moved_over_0.01mm':int((distance>1.e-5).sum()),'max_displacement_m':float(distance.max()),
                        'minimum_jacobian_determinant':float(determinants.min())})
    args.output.parent.mkdir(parents=True,exist_ok=True);writer.save(args.output)
    result={'source_sha256':digest(source),'candidate_sha256':digest(args.output),'config_sha256':digest(args.config),
            'coordinate_system':c['coordinate_system'],'forms':c['forms'],'materials':reports,
            'unchanged_contract':['skeleton','animation','skin weights','joint indices','triangles','UVs','textures','material assignments'],
            'limits':['Geometric bounds do not prove visual quality, expression fit or animated collision.',
                      'The lower face and lower eyelid margin can move; eyeballs, brows, hair, hands, armor and weapon are unchanged.']}
    args.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__ == '__main__': main()
