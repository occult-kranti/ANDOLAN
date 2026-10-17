#!/usr/bin/env python3
"""Bounded byte-level comparison; does not modify packs or establish visual equivalence."""
from pathlib import Path
import hashlib,importlib.util,json,struct,zstandard
ROOT=Path('/workspace/ANDOLAN');PROJECT=ROOT/'games/yuga-native';EVIDENCE=PROJECT/'docs/evidence/mythic-published'
LOCAL=Path('/workspace/scratch/yuga-next/mythic-package-r3/yuga-native-linux.pck');PUBLIC=Path('/workspace/scratch/yuga-next/mythic-public-linux.pck')
spec=importlib.util.spec_from_file_location('compare_packager',PROJECT/'tools/package-native.py');packager=importlib.util.module_from_spec(spec);spec.loader.exec_module(packager)
def payloads(path):
 data=path.read_bytes();assert data[:4]==b'GDPC';version=struct.unpack_from('<I',data,4)[0];base=struct.unpack_from('<Q',data,24)[0];position=struct.unpack_from('<Q',data,32)[0] if version==3 else 96
 count=struct.unpack_from('<I',data,position)[0];position+=4;out={}
 for _ in range(count):
  length=struct.unpack_from('<I',data,position)[0];position+=4;name=data[position:position+length].rstrip(b'\0').decode();position+=length;offset,size=struct.unpack_from('<QQ',data,position);position+=36;out[name]=data[base+offset:base+offset+size]
 return out

def decode(data):
 if data[:4]==b'RSRC':return data,'uncompressed RSRC'
 assert data[:4]==b'RSCC';mode,block,total=struct.unpack_from('<III',data,4);assert mode==2 and block==4096
 count=(total+block-1)//block;sizes=struct.unpack_from('<'+'I'*count,data,16);position=16+count*4;out=[]
 for size in sizes:
  out.append(zstandard.ZstdDecompressor().decompress(data[position:position+size],max_output_size=block));position+=size
 decoded=b''.join(out);assert len(decoded)==total;return decoded,'RSCC zstd blocks'

def node_ids(data):
 marker=b'\x05\0\0\0\x09\0\0\0node_ids\0\x20\0\0\0';start=data.find(marker);assert start>=0 and data.find(marker,start+1)==-1
 start+=len(marker);count=struct.unpack_from('<I',data,start)[0];start+=4;end=start+4*count;assert 0<count<100000 and end<=len(data)
 assert data[end:end+19]==b'\x05\0\0\0\x0b\0\0\0conn_count\0'
 return {'start':start,'end_exclusive':end,'int32_count':count}

def main():
 checked={k:packager.inspect_pack(p) for k,p in [('local',LOCAL),('public',PUBLIC)]};raw={k:payloads(p) for k,p in [('local',LOCAL),('public',PUBLIC)]};assert set(raw['local'])==set(raw['public'])
 rows=[];identical=0
 for name in sorted(raw['local']):
  a=raw['local'][name];b=raw['public'][name]
  if a==b:identical+=1;continue
  da,codec=decode(a);db,other=decode(b);assert codec==other and len(da)==len(db)
  na=node_ids(da);nb=node_ids(db);assert na==nb
  changed=[i for i in range(len(da)) if da[i]!=db[i]];outside=[i for i in changed if not na['start']<=i<na['end_exclusive']]
  rows.append({'path':name,'raw_bytes_local':len(a),'raw_bytes_public':len(b),'raw_sha256_local':hashlib.sha256(a).hexdigest(),'raw_sha256_public':hashlib.sha256(b).hexdigest(),'codec':codec,'decoded_bytes_each':len(da),'decoded_sha256_local':hashlib.sha256(da).hexdigest(),'decoded_sha256_public':hashlib.sha256(db).hexdigest(),'differing_decoded_bytes':len(changed),'serialized_node_ids_span':na,'differing_bytes_inside_node_ids_span':len(changed)-len(outside),'outside_node_ids_differences':[{'offset':i,'local_byte':da[i],'public_byte':db[i]} for i in outside]})
 result={'passed':True,'scope':'All original pack MD5 entries inspected, then differing payloads compared after lossless RSCC zstd decoding. Identifies serialized node_ids byte spans; does not infer complete semantic, visual, collision or animation equivalence. Two remaining nature-resource bytes are explicitly unexplained. No source/resource normalization or modifications performed. Public package OS testing remains independent.','byte_identity':False,'input_packs':{k:{f:checked[k][f] for f in ['bytes','sha256','entry_count']} for k in checked},'identical_payloads':identical,'different_payloads':len(rows),'rows':rows,'tool_sources':{'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'packager_sha256':hashlib.sha256((PROJECT/'tools/package-native.py').read_bytes()).hexdigest(),'zstandard_version':zstandard.__version__}}
 target=EVIDENCE/'pck-decompressed-comparison.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'comparison_completed':True,'identical_payloads':identical,'different_payloads':len(rows),'different_bytes_outside_node_ids':sum(len(r['outside_node_ids_differences']) for r in rows)},indent=2))
if __name__=='__main__':main()
