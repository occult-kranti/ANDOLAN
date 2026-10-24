"""Recover the exact licensed donor and editable preview; never overwrite files."""
import argparse,gzip,hashlib,json
from pathlib import Path

def sha(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--destination',type=Path,required=True);args=parser.parse_args()
    package=Path(__file__).resolve().parent
    inventory=json.loads((package/'source/compression-receipt.json').read_text())
    targets=[(row,package/row['durable_archive'],args.destination/Path(row['durable_archive']).name.removesuffix('.gz')) for row in inventory['rows']]
    extra=[args.destination/'relocated-refined-source.json',args.destination/'recovery-receipt.json']
    for _,archive,target in targets:
        if target.exists():raise FileExistsError(target)
        assert sha(archive)==next(row['archive_sha256'] for row,a,t in targets if t==target)
    for path in extra:
        if path.exists():raise FileExistsError(path)
    args.destination.mkdir(parents=True,exist_ok=True);results=[]
    for row,archive,target in targets:
        result=hashlib.sha256();size=0
        with gzip.open(archive,'rb') as source,target.open('xb') as output:
            for chunk in iter(lambda:source.read(1024*1024),b''):result.update(chunk);size+=len(chunk);output.write(chunk)
        assert result.hexdigest()==row['source_sha256'] and size==row['source_bytes']
        results.append({'path':str(target),'bytes':size,'sha256':result.hexdigest()})
    source_receipt=package/'evidence/refined-fit-source.json';relocated=json.loads(source_receipt.read_text())
    final=next(result for result in results if result['sha256']==relocated['scene']['sha256'])
    previous=relocated['scene']['path'];relocated['scene']['path']=final['path']
    relocated['relocation']={'original_source_receipt_sha256':sha(source_receipt),'old_path':previous,'note':'Path-only metadata copy for a fresh replay; original saved scene bytes and recorded actual evidence remain unchanged.'}
    with extra[0].open('x') as output:json.dump(relocated,output,indent=2);output.write('\n')
    receipt={'schema_version':1,'scope':'Exact archive recovery only; no art, rig, runtime, pose or LOD promotion','files':results,'relocated_receipt':str(extra[0]),'overwrite_permitted':False}
    with extra[1].open('x') as output:json.dump(receipt,output,indent=2);output.write('\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
