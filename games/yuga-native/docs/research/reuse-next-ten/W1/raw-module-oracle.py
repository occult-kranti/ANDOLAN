"""Independent raw GLB whole-piece audit and deliberate partial-face negative."""
from pathlib import Path
import argparse, collections, copy, hashlib, json, struct

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--selection',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    raw=args.source.read_bytes()
    size=struct.unpack_from('<I',raw,12)[0]
    document=json.loads(raw[20:20+size])
    binary=raw[28+size:]
    def accessor(index):
        a=document['accessors'][index];v=document['bufferViews'][a['bufferView']]
        components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        code={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']]
        fmt='<'+code*components;stride=v.get('byteStride',struct.calcsize(fmt))
        offset=v.get('byteOffset',0)+a.get('byteOffset',0)
        return [struct.unpack_from(fmt,binary,offset+i*stride) for i in range(a['count'])]
    selection=json.loads(args.selection.read_text())
    def inspect(selection):
        rows=[];total=collision=0
        for row in selection['selected']:
            node=next(n for n in document['nodes'] if n.get('name')==row['node'])
            primitive=document['meshes'][node['mesh']]['primitives'][row['surface']]
            positions=accessor(primitive['attributes']['POSITION'])
            indices=[v[0] for v in accessor(primitive['indices'])]
            selected=set(row['source_triangle_ids'])
            touched=collections.defaultdict(int)
            for triangle in range(len(indices)//3):
                flag=1 if triangle in selected else 2
                for corner in range(3): touched[positions[indices[triangle*3+corner]]]|=flag
            shared=sum(value==3 for value in touched.values())
            valid_ids=len(selected)==len(row['source_triangle_ids']) and row['source_triangle_ids']==sorted(selected) and min(selected)>=0 and max(selected)*3+2<len(indices)
            rows.append({'node':row['node'],'triangles':len(selected),'exact_positions_shared_with_unselected':shared,'source_attributes':sorted(primitive['attributes']),'node_has_no_transform':set(node)=={'name','mesh'},'material_name_matches':document['materials'][primitive['material']]['name']==row['material'],'ordered_unique_in_range_ids':valid_ids})
            total+=len(selected)
            if row['collision']:collision+=len(selected)
        return {'passed':total==17862 and collision==6706 and len(rows)==11 and all(not row['exact_positions_shared_with_unselected'] and row['node_has_no_transform'] and row['material_name_matches'] and row['ordered_unique_in_range_ids'] for row in rows),'triangles':total,'collision_triangles':collision,'surfaces':len(rows),'rows':rows}
    original=inspect(selection)
    bad=copy.deepcopy(selection)
    largest=max(bad['selected'],key=lambda row:len(row['source_triangle_ids']))
    removed=largest['source_triangle_ids'].pop(len(largest['source_triangle_ids'])//2)
    negative=inspect(bad)
    report={'schema':1,'scope':'Raw exact-coordinate source-component membership, attributes and material-name audit. It does not qualify native extraction, composed-world collision, visual art, authority or hardware.','source_sha256':digest(args.source),'selection_sha256':digest(args.selection),'source_contract_matches':digest(args.source)=='1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33','original':original,'negative':{'scope':'In-memory deletion of one face from largest selected row; no source/selection file mutated.','node':largest['node'],'removed_triangle':removed,'result':negative},'negative_detected':not negative['passed'],'passed':original['passed'] and not negative['passed']}
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'triangles':original['triangles'],'negative_detected':report['negative_detected'],'negative_shared_positions':sum(row['exact_positions_shared_with_unselected'] for row in negative['rows'])}))
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
