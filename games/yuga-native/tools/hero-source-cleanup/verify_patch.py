#!/usr/bin/env python3
"""Independently verify a topology-preserving source/candidate GLB patch."""
import argparse,hashlib,json,math,struct
from pathlib import Path

EXPECTED_SOURCE='0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b'
def parse(raw):
 if len(raw)<20 or struct.unpack_from('<III',raw)!=(0x46546c67,2,len(raw)):raise ValueError('Invalid GLB header')
 offset=12;doc=None;binary=None
 while offset<len(raw):
  n,t=struct.unpack_from('<II',raw,offset);offset+=8
  if offset+n>len(raw):raise ValueError('Invalid chunk size')
  if t==0x4e4f534a:doc=json.loads(raw[offset:offset+n])
  elif t==0x004e4942:binary=offset
  offset+=n
 if doc is None or binary is None:raise ValueError('Missing GLB chunks')
 return doc,binary

def accessor(doc,binary,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
 if a['componentType']!=5126 or a['type']!='VEC3' or v.get('buffer',0)!=0:raise ValueError('Unsupported attribute')
 return binary+v.get('byteOffset',0)+a.get('byteOffset',0),v.get('byteStride',12),a['count']

def verify_bytes(original,candidate,expected_source=EXPECTED_SOURCE):
 if hashlib.sha256(original).hexdigest()!=expected_source:raise ValueError('Unexpected source hash')
 if len(candidate)!=len(original):raise ValueError('Container size changed')
 doc,binary=parse(original);other,other_binary=parse(candidate)
 if doc!=other or binary!=other_binary:raise ValueError('Container metadata changed')
 if len(doc['meshes'])!=1 or len(doc['meshes'][0]['primitives'])!=1:raise ValueError('Unexpected primitive layout')
 p=doc['meshes'][0]['primitives'][0];po,ps,n=accessor(doc,binary,p['attributes']['POSITION']);no,ns,nn=accessor(doc,binary,p['attributes']['NORMAL'])
 if n!=nn:raise ValueError('Position/normal counts differ')
 coverage=bytearray(len(original));moved=[];normals=[];max_delta=0.
 for i in range(n):
  op=original[po+i*ps:po+i*ps+12];cp=candidate[po+i*ps:po+i*ps+12];on=original[no+i*ns:no+i*ns+12];cn=candidate[no+i*ns:no+i*ns+12]
  if op==cp and on==cn:continue
  x,y,z=struct.unpack('<3f',op);bx,by,bz=x,-z,y
  if not(-.115<=bx<=.095 and .045<=by<=.13 and .25<=bz<=.415):raise ValueError('Changed vertex outside protected rear-hair envelope')
  pnew=struct.unpack('<3f',cp);nnew=struct.unpack('<3f',cn)
  if not all(math.isfinite(q) for q in (*pnew,*nnew)):raise ValueError('Nonfinite candidate attribute')
  delta=math.dist((x,y,z),pnew)
  if delta>.00250001:raise ValueError('Displacement exceeds cap')
  if abs(sum(q*q for q in nnew)-1)>.0001:raise ValueError('Candidate normal is not unit length')
  max_delta=max(max_delta,delta)
  if op!=cp:moved.append(i)
  if on!=cn:normals.append(i)
  coverage[po+i*ps:po+i*ps+12]=b'\x01'*12;coverage[no+i*ns:no+i*ns+12]=b'\x01'*12
 if not moved:raise ValueError('Candidate has no position change')
 if len(set(moved)|set(normals))>2000:raise ValueError('Affected vertex budget exceeded')
 differences=[i for i,(a,b) in enumerate(zip(original,candidate)) if a!=b]
 if any(not coverage[i] for i in differences):raise ValueError('UV/index/image/material/nonpermitted bytes changed')
 image_checks=[]
 for im in doc.get('images',[]):
  v=doc['bufferViews'][im['bufferView']];off=binary+v.get('byteOffset',0);data=original[off:off+v['byteLength']]
  image_checks.append({'mime_type':im.get('mimeType'),'bytes':len(data),'source_sha256':hashlib.sha256(data).hexdigest(),'candidate_sha256':hashlib.sha256(candidate[off:off+v['byteLength']]).hexdigest()})
 return {'passed':True,'scope':'Exact-byte and displacement eligibility only; not visual improvement or production acceptance.','source_sha256':expected_source,'candidate_sha256':hashlib.sha256(candidate).hexdigest(),'vertices':n,'moved_vertices':len(moved),'normal_changed_vertices':len(normals),'max_displacement':max_delta,'changed_bytes':len(differences),'all_other_bytes_exact':True,'images':image_checks}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--report',type=Path);a=p.parse_args()
 try:d=verify_bytes(a.source.read_bytes(),a.candidate.read_bytes())
 except (OSError,ValueError,KeyError,struct.error) as e:d={'passed':False,'error':str(e)}
 if a.report:a.report.write_text(json.dumps(d,indent=2)+'\n')
 print(json.dumps(d,indent=2));return 0 if d['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
