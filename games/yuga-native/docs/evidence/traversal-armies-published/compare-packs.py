from pathlib import Path
import hashlib,struct,json,importlib.util,zstandard
ROOT=Path('/workspace/ANDOLAN/games/yuga-native')
spec=importlib.util.spec_from_file_location('package_native',ROOT/'tools/package-native.py');packager=importlib.util.module_from_spec(spec);spec.loader.exec_module(packager)
FILES={'local':Path('/tmp/yuga-traversal-local-linux/yuga-native-linux-x86_64/yuga-native.pck'),'published':Path('/tmp/yuga-traversal-public-linux/yuga-native-linux-x86_64/yuga-native.pck')}
def sha(data):return hashlib.sha256(data).hexdigest()
def packed(path):
 d=path.read_bytes();ver=struct.unpack_from('<I',d,4)[0];base=struct.unpack_from('<Q',d,24)[0];p=struct.unpack_from('<Q',d,32)[0] if ver==3 else 96
 count=struct.unpack_from('<I',d,p)[0];p+=4;entries={};ranges=[]
 for _ in range(count):
  n=struct.unpack_from('<I',d,p)[0];p+=4;name=d[p:p+n].rstrip(b'\0').decode();p+=n;offset,size=struct.unpack_from('<QQ',d,p);p+=36
  entries[name]=d[base+offset:base+offset+size];ranges.append((base+offset,base+offset+size))
 ranges.sort();padding=0
 for i,(a,b) in enumerate(ranges[:-1]):
  pad=d[b:ranges[i+1][0]];assert not any(pad);padding+=len(pad)
 return entries,{'header_bytes':ranges[0][0],'payload_bytes':sum(len(v) for v in entries.values()),'zero_inter_payload_padding':padding,'directory_and_tail_bytes':len(d)-ranges[-1][1]}
def decode(data):
 if data[:4]==b'RSRC':return data
 assert data[:4]==b'RSCC';mode,block,total=struct.unpack_from('<III',data,4);assert mode==2
 count=total//block+1;lengths=struct.unpack_from('<'+'I'*count,data,16);p=16+4*count;out=[]
 for i,n in enumerate(lengths):
  expected=min(block,total-i*block);out.append(zstandard.ZstdDecompressor().decompress(data[p:p+n],max_output_size=max(expected,1)));p+=n;assert len(out[-1])==expected
 result=b''.join(out);assert len(result)==total;return result
class Resource:
 def __init__(self,data):self.d=data;self.p=4 if data[:4]==b'RSRC' else 0;self.fields={};self.resources=[];self.header()
 def read(self,n):
  assert 0<=self.p<=len(self.d)-n,(self.p,n,len(self.d));v=self.d[self.p:self.p+n];self.p+=n;return v
 def num(self,code='I'):return struct.unpack('<'+code,self.read(struct.calcsize('<'+code)))[0]
 def string(self):return self.read(self.num()).rstrip(b'\0').decode()
 def mapped(self):
  n=self.num();return self.read(n&0x7fffffff).rstrip(b'\0').decode() if n&0x80000000 else self.strings[n]
 def header(self):
  endian,real64,major,minor,fmt=[self.num() for _ in range(5)];assert endian==0 and major==4 and fmt==6
  self.main_type=self.string();self.num('Q');flags=self.num();self.real=8 if flags&4 else 4;self.num('Q')
  if flags&8:self.string()
  self.read(44);self.strings=[self.string() for _ in range(self.num())]
  for _ in range(self.num()):
   self.string();self.string()
   if flags&2:self.num('Q')
  refs=[(self.string(),self.num('Q')) for _ in range(self.num())]
  for index,(path,offset) in enumerate(refs):
   self.p=offset;kind=self.string();props={};prefix=f'{index}/{path}/{kind}'
   for _ in range(self.num()):
    name=self.mapped();props[name]=self.variant(prefix+'/'+name)
   self.resources.append({'path':path,'kind':kind,'properties':props})
 def variant(self,path):
  t=self.num();start=self.p
  if t==1:v=None
  elif t in (2,3,23):v=self.num()
  elif t==40:v=self.num('Q')
  elif t==4:v=self.num('d' if self.real==8 else 'f')
  elif t==41:v=self.num('d')
  elif t in (5,44):v=self.string()
  elif t in (10,11,12,13,14,15,16,17,18,20,45,46,47,50,51,52):
   counts={10:2,11:4,12:3,13:4,14:4,15:6,16:9,17:12,18:6,20:4,45:2,46:4,47:3,50:4,51:4,52:16};width=4 if t in (20,45,46,47,51) else self.real;v={'raw':self.read(counts[t]*width).hex()}
  elif t==22:
   a=self.num('H');b=self.num('H');v={'nodepath':[self.mapped() for _ in range(a+(b&0x7fff))],'absolute':bool(b&0x8000)}
  elif t==24:
   tag=self.num();v={'reference_type':tag}
   if tag in (2,3):v['index']=self.num()
   elif tag==1:v.update(type=self.string(),path=self.string())
   else:assert tag==0
  elif t in (42,43):v=None
  elif t==26:
   v={}
   for i in range(self.num()&0x7fffffff):
    key=self.variant(path+'/key'+str(i));assert isinstance(key,(str,int,float)),key;v[key]=self.variant(path+'/'+str(key))
  elif t==30:v=[self.variant(path+'/'+str(i)) for i in range(self.num()&0x7fffffff)]
  elif t==34:v=[self.string() for _ in range(self.num())]
  elif t in (31,32,33,35,36,37,48,49,53):
   count=self.num();stride={31:1,32:4,33:4,35:self.real*3,36:16,37:self.real*2,48:8,49:8,53:self.real*4}[t];offset=self.p;self.read(count*stride)
   v={'offset':offset,'bytes':count*stride,'count':count,'variant':t}
   if t==31:self.read((-count)%4)
  else:raise ValueError(('unknown variant',t,path,self.p))
  self.fields[path]={'type':t,'start':start,'end':self.p,'value':v};return v

reports={k:packager.inspect_pack(v) for k,v in FILES.items()};payloads={};layouts={}
for k,p in FILES.items():payloads[k],layouts[k]=packed(p)
a,b=payloads['local'],payloads['published'];assert a.keys()==b.keys()
changed=[];generated=0;shading=[]
for path in sorted(a):
 if a[path]==b[path]:continue
 left,right=decode(a[path]),decode(b[path]);assert len(left)==len(right)
 l,r=Resource(left),Resource(right);assert l.fields.keys()==r.fields.keys()
 masked_left,masked_right=bytearray(left),bytearray(right);idfields=[]
 for field,info in l.fields.items():
  if not field.endswith('/PackedScene/_bundled/node_ids'):continue
  other=r.fields[field];assert info['type']==other['type']==32 and info['value']==other['value'];d=info['value'];o,n=d['offset'],d['bytes'];lv=struct.unpack_from('<'+'I'*d['count'],left,o);rv=struct.unpack_from('<'+'I'*d['count'],right,o)
  different=sum(x!=y for x,y in zip(lv,rv));generated+=different
  idfields.append({'field':field,'offset':o,'bytes':n,'changed_ids':different,'local_values':lv,'published_values':rv});masked_left[o:o+n]=bytes(n);masked_right[o:o+n]=bytes(n)
 residual=[i for i,(x,y) in enumerate(zip(masked_left,masked_right)) if x!=y]
 local_shading=[]
 for at in residual:
  containing=[(field,info) for field,info in l.fields.items() if info['type']==31 and info['value']['offset']<=at<info['value']['offset']+info['value']['bytes']]
  assert len(containing)==1,(path,at,containing)
  field,info=containing[0];assert field.endswith('/vertex_data') and '/ArrayMesh/_surfaces/' in field
  prefix=field.rsplit('/',1)[0];surface_index=int(prefix.rsplit('/',1)[1]);resource_index=int(field.split('/',1)[0]);props=l.resources[resource_index]['properties'];surface=props['_surfaces'][surface_index]
  assert surface['format']==34896613383
  begin=info['value']['offset'];vertex_index=(at-begin)//8;component_offset=(at-begin)%8;assert component_offset in (6,7)
  angle_offset=begin+vertex_index*8+6;lv=struct.unpack_from('<4H',left,begin+vertex_index*8);rv=struct.unpack_from('<4H',right,begin+vertex_index*8);assert lv[:3]==rv[:3] and abs(lv[3]-rv[3])==1
  record={'path':path,'field':field,'internal_resource_index':resource_index,'resource_name':props.get('resource_name'),'surface_index':surface_index,'surface_name':surface.get('name'),'vertex_count':surface.get('vertex_count'),'vertex_index':vertex_index,'angle_offset':angle_offset,'local_xyz_angle_u16':lv,'published_xyz_angle_u16':rv,'angle_step':abs(lv[3]-rv[3]),'angle_bound_degrees':360/65535}
  if record not in local_shading:local_shading.append(record)
  masked_left[angle_offset:angle_offset+2]=b'\0\0';masked_right[angle_offset:angle_offset+2]=b'\0\0'
 assert masked_left==masked_right,(path,'unclassified differences')
 shading+=local_shading
 changed.append({'path':path,'local':{'bytes':len(a[path]),'sha256':sha(a[path])},'published':{'bytes':len(b[path]),'sha256':sha(b[path])},'decoded_bytes':len(left),'decoded_local_sha256':sha(left),'decoded_published_sha256':sha(right),'node_id_fields':idfields,'quantized_shading_changes':local_shading,'all_other_decoded_bytes_identical':True,'classified_field_masked_sha256':sha(masked_left)})
summary={'passed':True,'entry_count':len(a),'identical_payloads':len(a)-len(changed),'differing_payloads':len(changed),'same_entry_names':True,'generated_node_identifiers_changed':generated,'quantized_shading_values_changed':len(shading),'unclassified_decoded_changes':0,'all_other_decoded_bytes_identical':True,'scripts_shaders_audio_manifests_project_binary_identical':True}
report={'schema':1,'scope':'Independent PCK bytes plus current decoded Godot binary resource fields. No Godot runtime or renderer executed; this is not runtime/visual acceptance. Cross-host numerical cause is not established.','method':['Verify every stored PCK MD5 and SHA256, same resource inventory.','Decode RSCC Zstandard block tables; independently parse resource headers, tables, all property Variants.','Mask only currently parsed PackedScene._bundled.node_ids and explicitly identified one-step compressed tangent-basis angles. Require all remaining decoded bytes exactly equal.'],'summary':summary,'packs':{k:{f:v for f,v in d.items() if f!='entries'} for k,d in reports.items()},'paths':{k:str(v) for k,v in FILES.items()},'layouts':layouts,'changed_resources':changed,'shading_changes':shading,'parser_sha256':sha(Path(__file__).read_bytes()),'format_sources':[{'path':str(p),'sha256':sha(p.read_bytes())} for p in [Path('/tmp/yuga-file_access_compressed.cpp'),Path('/tmp/yuga-resource_format_binary.cpp'),Path('/tmp/yuga-resource_format_binary.h')]]}
Path('/tmp/yuga-traversal-pck-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(summary,indent=2));print(json.dumps({'layouts':layouts,'shading':shading},indent=2))
