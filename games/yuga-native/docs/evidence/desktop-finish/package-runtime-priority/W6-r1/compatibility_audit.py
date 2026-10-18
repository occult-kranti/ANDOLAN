"""Compare the preserved default/dce output contract without an engine."""
from pathlib import Path
import importlib.util, json, hashlib, shutil, tempfile
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.PROJECT=PROJECT
    return mod
old=module('before_runtime_variant',HERE/'before/tools/package-native.py')
new=module('after_runtime_variant',PROJECT/'tools/package-native.py')
proof=PROJECT/new.PUBLIC_RUNTIME_PROOF
previous=old.public_runtime_provenance(proof)
current=new.public_runtime_provenance(proof)
selection={'exporter':{'bytes':138981968,'sha256':new.PUBLIC_RUNTIME_EXPORTER_SHA,'version':new.PUBLIC_RUNTIME_EXPORTER_VERSION,'role':'PCK export and imported-font proof'},'linux_runtime':{**new.PUBLIC_LINUX_RUNTIME,'kind':current['kind'],'provenance':current}}
checks={'dce_provenance_dictionary_unchanged':previous==current,'default_linux_readme_bytes_unchanged':old.start_readme('linux')==new.start_readme('linux'),'dce_linux_readme_bytes_unchanged':old.start_readme('linux',selection)==new.start_readme('linux',selection),'windows_readme_bytes_unchanged':old.start_readme('windows',selection)==new.start_readme('windows',selection)}
with tempfile.TemporaryDirectory(prefix='yuga-runtime-output-') as folder:
    roots=[]
    for label,mod in [('old',old),('new',new)]:
        root=Path(folder)/label;(root/'NOTICE').mkdir(parents=True)
        for name in ['GODOT-LICENSE.txt','GODOT-COPYRIGHT.txt']:
            shutil.copyfile(PROJECT/'NOTICE'/name,root/'NOTICE'/name)
        mod.copy_public_runtime_notice(root,selection)
        roots.append({p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()})
    checks['dce_complete_notice_payload_bytes_unchanged']=roots[0]==roots[1]
result={'scope':'Read retained prior source plus current source; small temporary notice copies only; no engine/export','passed':all(checks.values()),'checks':checks,'old_source_sha256':hashlib.sha256((HERE/'before/tools/package-native.py').read_bytes()).hexdigest(),'new_source_sha256':hashlib.sha256((PROJECT/'tools/package-native.py').read_bytes()).hexdigest()}
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
