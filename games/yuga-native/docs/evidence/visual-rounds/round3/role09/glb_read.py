"""Independent minimal GLB reader for exact source audits; refuses sparse arrays."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
class GLB:
 def __init__(self,path):
  self.path=Path(path);self.raw=self.path.read_bytes();magic,version,size=struct.unpack_from('<III',self.raw)
  assert magic==0x46546c67 and version==2 and size==len(self.raw)
  at=12;self.doc=None;self.binary=None
  while at<len(self.raw):
   length,kind=struct.unpack_from('<II',self.raw,at);body=self.raw[at+8:at+8+length];at+=8+length
   if kind==0x4e4f534a:self.doc=json.loads(body)
   elif kind==0x004e4942:self.binary=body
  assert self.doc is not None and self.binary is not None
 def array(self,index,normalize=False):
  a=self.doc['accessors'][index];assert 'sparse' not in a
  v=self.doc['bufferViews'][a['bufferView']];assert v.get('buffer',0)==0
  dtype=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
  at=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',n*dtype.itemsize)
  x=np.ndarray((a['count'],n),dtype=dtype,buffer=self.binary,offset=at,strides=(stride,dtype.itemsize)).copy()
  if normalize and a.get('normalized',False):
   x=x.astype(float)/np.iinfo(dtype).max
   if dtype.kind=='i':x=np.maximum(x,-1)
  return x[:,0] if n==1 else x
 def image_bytes(self,image):
  v=self.doc['bufferViews'][image['bufferView']];start=v.get('byteOffset',0);return self.binary[start:start+v['byteLength']]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
