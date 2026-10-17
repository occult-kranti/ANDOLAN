#!/usr/bin/env python3
"""Five safe calls into the exact reviewed Mikk authoring component.

Separate from static REA acceptance; not an all-input semantic oracle.
"""
import argparse
import ctypes
import hashlib
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binary', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
expected = '0f038e6f83f5fce5e10d0b8c14028f96ed7368229c59bded44a2512dda91bb4a'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
if digest(args.binary) != expected:
    parser.error('Use the exact reviewed component, not an arbitrary shared library')
if args.report.exists():
    parser.error('Use a fresh report path')
library = ctypes.CDLL(str(args.binary.resolve()))
function = library.yuga_mikk_generate
fp = ctypes.POINTER(ctypes.c_float)
ip = ctypes.POINTER(ctypes.c_uint32)
function.argtypes = [fp, fp, fp, ctypes.c_uint32, ip, ctypes.c_uint32, fp, ctypes.c_size_t]
function.restype = ctypes.c_int
base = {'positions': [0., 0., 0., 1., 0., 0., 0., 1., 0.],
        'normals': [0., 0., 1.] * 3, 'uvs': [0., 0., 1., 0., 0., 1.]}
checks = []
cases = [('valid_triangle', None, None, 0),
         ('nan_position', 'positions', float('nan'), 2),
         ('positive_inf_position', 'positions', float('inf'), 2),
         ('nan_normal', 'normals', float('nan'), 2),
         ('nan_uv', 'uvs', float('nan'), 2)]
for name, field, value, expected_return in cases:
    values = {key: list(values_) for key, values_ in base.items()}
    if field:
        values[field][0] = value
    buffers = {key: (ctypes.c_float * len(values_))(*values_)
               for key, values_ in values.items()}
    indices = (ctypes.c_uint32 * 3)(0, 1, 2)
    result = (ctypes.c_float * 12)()
    code = function(buffers['positions'], buffers['normals'], buffers['uvs'],
                    3, indices, 3, result, 12)
    checks.append({'name': name, 'native_return': code,
                   'expected_return': expected_return, 'passed': code == expected_return})
# This is one IEEE predicate interpretation, not an executed replacement function.
predicate = 3.4028234663852886e38 < math.fabs(float('nan'))
checks.append({'name': 'ieee_nan_maxfloat_less_abs_is_false',
               'passed': predicate is False, 'rendered_predicate_result': predicate})
checks.append({'name': 'binary_unchanged', 'passed': digest(args.binary) == expected})
report = {'passed': all(check['passed'] for check in checks), 'checks': checks,
          'binary_sha256': expected, 'script_sha256': digest(Path(__file__)),
          'target_executed': True,
          'scope': 'Five fixed-size native calls, one predicate interpretation and input identity. No arbitrary pointers, underallocated buffers, all-input equivalence, game runtime or art acceptance.'}
args.report.parent.mkdir(parents=True, exist_ok=True)
args.report.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': len(checks), 'native_calls': 5}))
raise SystemExit(0 if report['passed'] else 1)
