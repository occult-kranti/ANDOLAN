"""Independent sparse native-hero hair patch oracle; source is never edited."""
from pathlib import Path
import argparse,copy,hashlib,json,math,struct

def sha(raw): return hashlib.sha256(raw).hexdigest()
def parse(raw):
    magic,version,total,size,kind=struct.unpack_from('<5I',raw)
    assert (magic,version,total,kind)==(0x46546c67,2,len(raw),0x4e4f534a)
    count,bkind=struct.unpack_from('<2I',raw,20+size)
    assert bkind==0x004e4942 and 28+size+count==len(raw)
    return json.loads(raw[20:20+size]),raw[28+size:]

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    source=a.source.read_bytes();candidate=a.candidate.read_bytes()
    doc,old=parse(source);newdoc,new=parse(candidate)
    material=next(i for i,m in enumerate(doc['materials']) if m.get('name')=='Swept black hair')
    primitives=[p for mesh in doc['meshes'] for p in mesh['primitives'] if p.get('material')==material]
    assert len(primitives)==1
    primitive=primitives[0];attrs=primitive['attributes'];count=doc['accessors'][attrs['POSITION']]['count']
    def stream(name):
        index=attrs[name];accessor=doc['accessors'][index];view=doc['bufferViews'][accessor['bufferView']]
        n={'VEC3':3,'VEC4':4}[accessor['type']]
        assert accessor['componentType']==5126 and accessor['count']==count
        return index,view.get('byteOffset',0)+accessor.get('byteOffset',0),view.get('byteStride',4*n),n
    streams={name:stream(name) for name in ['POSITION','NORMAL','TANGENT']}
    def values(data,name):
        _,offset,stride,n=streams[name]
        return [struct.unpack_from('<'+'f'*n,data,offset+i*stride) for i in range(count)]
    before={name:values(old,name) for name in streams};after={name:values(new,name) for name in streams}
    moved={i for i in range(count) if before['POSITION'][i]!=after['POSITION'][i]}
    allowed=set()
    for name,(_,offset,stride,n) in streams.items():
        for i in moved:allowed.update(range(offset+i*stride,offset+i*stride+n*4))
    def outside_difference(data):
        return sum(x!=y and i not in allowed for i,(x,y) in enumerate(zip(old,data)))
    outside=outside_difference(new)
    changed=sum(x!=y for x,y in zip(old,new))
    normalized=copy.deepcopy(newdoc)
    changed_bounds=[]
    for name,(index,_,_,_) in streams.items():
        for field in ['min','max']:
            if field in doc['accessors'][index] and field in newdoc['accessors'][index]:
                if doc['accessors'][index][field]!=newdoc['accessors'][index][field]:changed_bounds.append([name,index,field])
                normalized['accessors'][index][field]=doc['accessors'][index][field]
    bounds={}
    for name,(index,_,_,n) in streams.items():
        actual_min=[min(v[k] for v in after[name]) for k in range(n)]
        actual_max=[max(v[k] for v in after[name]) for k in range(n)]
        declared=newdoc['accessors'][index]
        errors=[abs(x-y) for field,actual in [('min',actual_min),('max',actual_max)] if field in declared for x,y in zip(declared[field],actual)]
        bounds[name]={'accessor':index,'has_declared_bounds':bool(errors),'maximum_error':max(errors,default=0),'actual_min':actual_min,'actual_max':actual_max}
    normal_error=max(abs(math.sqrt(sum(x*x for x in v))-1) for v in after['NORMAL'])
    tangent_error=max(abs(math.sqrt(sum(x*x for x in v[:3]))-1) for v in after['TANGENT'])
    basis_dot=max(abs(sum(x*y for x,y in zip(after['NORMAL'][i],after['TANGENT'][i][:3]))) for i in moved)
    source_basis_dot=max(abs(sum(x*y for x,y in zip(n,t[:3]))) for n,t in zip(before['NORMAL'],before['TANGENT']))
    whole_basis_dot=max(abs(sum(x*y for x,y in zip(n,t[:3]))) for n,t in zip(after['NORMAL'],after['TANGENT']))
    handedness_preserved=all(x[3]==y[3] and abs(y[3])==1 for x,y in zip(before['TANGENT'],after['TANGENT']))
    max_displacement=max(math.dist(before['POSITION'][i],after['POSITION'][i]) for i in moved)
    bad=bytearray(new);protected=next(i for i in range(len(bad)) if i not in allowed);bad[protected]^=1
    negative=outside_difference(bad)
    checks={'source_pin':sha(source)=='db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e','bin_length_unchanged':len(old)==len(new),'json_only_hair_attribute_bounds':normalized==doc,'only_moved_hair_position_normal_tangent_bytes':outside==0,'all_declared_changed_accessor_bounds_match':all(v['maximum_error']<1e-6 for v in bounds.values()),'finite_arrays':all(math.isfinite(x) for vv in after.values() for v in vv for x in v),'normalized_normal_tangent':normal_error<.0001 and tangent_error<.0001,'changed_basis_orthogonal':basis_dot<.0001,'tangent_handedness_preserved':handedness_preserved,'nonempty_bounded_sculpt':0<len(moved)<count and max_displacement<.1,'protected_byte_corruption_detected':negative==1}
    report={'schema':2,'scope':'Independent raw source/candidate byte, accessor, changed basis and protected-byte negative audit. Existing untouched-source basis imperfections are reported separately. No Blender reexecution, native pose/LOD, render or final art pass.','source_sha256':sha(source),'candidate_sha256':sha(candidate),'source_bytes':len(source),'candidate_bytes':len(candidate),'hair_accessor_vertices':count,'moved_vertices':len(moved),'changed_bin_bytes':changed,'protected_bin_differences':outside,'max_displacement_m':max_displacement,'bounds':bounds,'changed_bound_fields':changed_bounds,'max_normal_length_error':normal_error,'max_tangent_length_error':tangent_error,'max_changed_normal_tangent_dot':basis_dot,'max_source_whole_normal_tangent_dot':source_basis_dot,'max_candidate_whole_normal_tangent_dot':whole_basis_dot,'negative':{'scope':'One byte flipped only in an in-memory candidate copy, outside permitted hair arrays. Files unchanged.','protected_bin_offset':protected,'protected_differences':negative},'checks':checks,'passed':all(checks.values())}
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k in ['passed','moved_vertices','max_displacement_m','protected_bin_differences','checks']}));raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
