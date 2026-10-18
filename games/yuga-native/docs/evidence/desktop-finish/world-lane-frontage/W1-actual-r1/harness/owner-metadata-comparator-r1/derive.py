from pathlib import Path
import hashlib,json,difflib
base=Path('/workspace/scratch/yuga-frontage-helper-r2/compare_frontage.py')
out=Path(__file__).parent
old=base.read_text()
insert='''OWNER_KEY = 'metadata/yuga_surface_finish_owner'
OWNER_NAMES = {
    'Worked warm gold · bounded secondary',
    'Swept black hair · bounded secondary',
    'Cobalt handwoven silk · bounded secondary',
    'Cobalt lotus brocade · bounded secondary',
}

def normalize_finish_owner(report, label, errors):
    # Resource metadata contains Node.get_instance_id(), not a renderer value.
    # Preserve the original report; admit exactly four named ShaderMaterials,
    # one positive process-local owner across all three views, and no other key.
    normalized = copy.deepcopy(report)
    owner_ids = set()
    audit = []
    for shot in normalized['shots']:
        remap = {}
        names = []
        rows = {}
        for raw_hash, row in shot['materials'].items():
            properties = row.get('properties', {})
            if OWNER_KEY not in properties:
                rows[raw_hash] = row
                continue
            owner = properties[OWNER_KEY]
            name = properties.get('resource_name')
            require(row.get('class') == 'ShaderMaterial' and name in OWNER_NAMES,
                    label+' only four named finish ShaderMaterials', errors)
            require(type(owner) is int and owner > 0,
                    label+' positive integer finish owner metadata', errors)
            if type(owner) is int:
                owner_ids.add(owner)
            names.append(name)
            properties[OWNER_KEY] = 'process-local RamaSurfaceFinish owner'
            normalized_hash = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
            require(normalized_hash not in rows, label+' unique normalized material row', errors)
            rows[normalized_hash] = row
            remap[raw_hash] = normalized_hash
            audit.append({'shot':shot['id'], 'name':name, 'raw_owner_id':owner,
                          'raw_material_sha256':raw_hash, 'normalized_material_sha256':normalized_hash})
        require(len(names) == 4 and set(names) == OWNER_NAMES,
                label+' exact four owned material rows per view', errors)
        shot['materials'] = rows
        references = {key:0 for key in remap}
        for mesh in shot['meshes']:
            for key in ('material_override', 'material_overlay'):
                value = mesh[key]
                if value in remap:
                    references[value] += 1
                    mesh[key] = remap[value]
            surfaces = []
            for value in mesh['surfaces']:
                if value in remap:
                    references[value] += 1
                surfaces.append(remap.get(value, value))
            mesh['surfaces'] = surfaces
        require(all(count > 0 for count in references.values()),
                label+' every normalized material referenced by retained mesh', errors)
    require(len(owner_ids) == 1, label+' one stable finish owner across all four materials/all views', errors)
    return normalized, audit

'''
new=old.replace('def differences(a, b, path=\'\'):',insert+'def differences(a, b, path=\'\'):')
new=new.replace("def compare(a,b):\n    errors=[]", "def compare(a,b):\n    errors=[]\n    a, owner_a = normalize_finish_owner(a, 'baseline', errors)\n    b, owner_b = normalize_finish_owner(b, 'candidate', errors)")
new=new.replace("return {'passed':not errors and all(row['passed'] for row in rows),'errors':errors", "return {'passed':not errors and all(row['passed'] for row in rows),'finish_owner_metadata_normalization':{'baseline':owner_a,'candidate':owner_b,'scope':'Only exact process-local owner metadata; all other material values remain strict. Per-branch consistency, not direct Node-ID ownership observation.'},'errors':errors")
(out/'compare_frontage.py').write_text(new)
(out/'parent-successor.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(base),tofile='compare_frontage.py')))
print(hashlib.sha256(new.encode()).hexdigest())
