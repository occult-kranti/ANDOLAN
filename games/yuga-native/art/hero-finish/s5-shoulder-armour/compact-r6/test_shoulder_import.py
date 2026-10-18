"""Adversaries for oriented imported-triangle canonicalization; no engine."""
import argparse
import json
from pathlib import Path
import numpy as np
from compare_shoulder_import import oriented_faces, triangle_mask, sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    assert not args.report.exists()
    records = [np.array([i, 0.0, 1.0, .25], dtype='<f4').tobytes() for i in range(4)]
    triangles = np.array([[0, 1, 2], [0, 2, 3], [0, 1, 2]])
    expected = oriented_faces(records, triangles)
    checks = []

    def check(name, result):
        checks.append({'name': name, 'passed': bool(result)})
        assert result, name

    reordered = triangles[[2, 0, 1]][:, [1, 2, 0]]
    check('Triangle order and cyclic rotations are equivalent', oriented_faces(records, reordered) == expected)
    reversed_triangles = triangles.copy()
    reversed_triangles[0] = reversed_triangles[0, [0, 2, 1]]
    check('One reversed triangle is rejected', oriented_faces(records, reversed_triangles) != expected)
    check('Missing triangle is rejected', oriented_faces(records, triangles[:-1]) != expected)
    check('Extra triangle is rejected', oriented_faces(records, np.vstack([triangles, triangles[1]])) != expected)
    mutated = records.copy()
    changed = np.frombuffer(mutated[1], dtype='<f4').copy()
    changed[3] = .5
    mutated[1] = changed.tobytes()
    check('Noncap attribute mutation is rejected', oriented_faces(mutated, triangles) != expected)
    mutated = records.copy()
    changed = np.frombuffer(mutated[1], dtype='<f4').copy()
    changed[1] = -0.0
    mutated[1] = changed.tobytes()
    check('Signed-zero attribute mutation is rejected', oriented_faces(mutated, triangles) != expected)
    rejected = False
    try:
        triangle_mask(np.array([True, False, False, False]), triangles)
    except AssertionError:
        rejected = True
    check('Mixed selected/nonselected triangle is rejected', rejected)
    check('Selection preserves all triangle multiplicities', expected[(records[0], records[1], records[2])] == 2)
    report = {'schema': 1, 'passed': all(c['passed'] for c in checks),
              'test_sha256': sha(__file__),
              'comparator_sha256': sha(Path(__file__).with_name('compare_shoulder_import.py')),
              'checks': checks, 'scope': 'Eight synthetic comparator seam checks. No actual shoulder import or renderer execution.'}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{len(checks)}/{len(checks)} topology comparator seam checks pass')


if __name__ == '__main__':
    main()
