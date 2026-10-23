from pathlib import Path
import collections,hashlib,json,math,struct,sys
p=Path('/workspace/ANDOLAN/games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb')
raw=p.read_bytes();magic,version,total=struct.unpack_from('<III',raw)
assert magic==0x46546c67 and version==2 and total==len(raw)
chunks=[];offset=12
while offset<total:
 size,kind=struct.unpack_from('<II',raw,offset);offset+=8
 chunks.append((kind,raw[offset:offset+size]));offset+=size
assert offset==total
meta=json.loads(next(x for k,x in chunks if k==0x4e4f534a));binary=next(x for k,x in chunks if k==0x004e4942)
formats={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'};widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def accessor(index):
 a=meta['accessors'][index];v=meta['bufferViews'][a['bufferView']];assert not a.get('sparse')
 fmt='<'+formats[a['componentType']]*widths[a['type']];size=struct.calcsize(fmt);stride=v.get('byteStride',size);start=v.get('byteOffset',0)+a.get('byteOffset',0)
 assert start+(a['count']-1)*stride+size<=v.get('byteOffset',0)+v['byteLength']
 return [struct.unpack_from(fmt,binary,start+i*stride) for i in range(a['count'])]
mesh=meta['meshes'][0];assert len(meta['meshes'])==1 and len(mesh['primitives'])==1
prim=mesh['primitives'][0];positions=accessor(prim['attributes']['POSITION']);indices=[x[0] for x in accessor(prim['indices'])];assert len(indices)%3==0
posmap={};ids=[]
for pos in positions:
 assert all(math.isfinite(x) for x in pos)
 if pos not in posmap:posmap[pos]=len(posmap)
 ids.append(posmap[pos])
parent=list(range(len(posmap)))
def find(i):
 while i!=parent[i]:parent[i]=parent[parent[i]];i=parent[i]
 return i
def union(a,b):
 a,b=find(a),find(b)
 if a!=b:parent[b]=a
edges=collections.Counter();zero_index=0;area_zero=0
for off in range(0,len(indices),3):
 t=[ids[x] for x in indices[off:off+3]]
 if len(set(t))<3:zero_index+=1
 for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
  union(a,b);edges[tuple(sorted((a,b)))]+=1
comps=collections.Counter(find(i) for i in range(len(posmap)))
images=[]
for i,img in enumerate(meta.get('images',[])):
 assert 'uri' not in img
 v=meta['bufferViews'][img['bufferView']];data=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 images.append({'index':i,'mimeType':img.get('mimeType'),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
report={'scope':'Independent exact GLB parser / exact-position welded topology only; no repair, skinning, render or artistic acceptance. UV split vertices are not independent physical parts.','source':str(p.relative_to(Path('/workspace/ANDOLAN'))),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'position_vertices':len(positions),'unique_exact_position_vertices':len(posmap),'triangles':len(indices)//3,'position_components':len(comps),'component_vertex_counts_descending':sorted(comps.values(),reverse=True),'position_welded_boundary_edges':sum(v==1 for v in edges.values()),'position_welded_nonmanifold_edges':sum(v>2 for v in edges.values()),'position_welded_degenerate_index_triangles':zero_index,'skins':len(meta.get('skins',[])),'animations':len(meta.get('animations',[])),'images':images,'attributes':list(prim['attributes']),'all_position_components_finite':True,'all_indices_in_bounds':all(0<=x<len(positions) for x in indices),'external_images':0}
out=Path('/workspace/ANDOLAN/games/yuga-native/docs/research/ten-rounds-oct23/review/source-glb-audit.json');out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['images','component_vertex_counts_descending']}))
