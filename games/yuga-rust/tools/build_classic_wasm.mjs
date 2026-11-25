// Regenerate the browser's standalone classic simulation using Cargo's actual artifact path.
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFile,writeFile,rename,rm,readdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import { dirname, resolve } from 'node:path';
const project=fileURLToPath(new URL('../',import.meta.url));
function checked(command,args){
  const result=spawnSync(command,args,{cwd:project,encoding:'utf8',stdio:['ignore','pipe','inherit']});
  if(result.error)throw result.error;
  assert.equal(result.status,0,command+' build step failed');
  return result.stdout;
}
checked(process.execPath,['tools/export-classic-roster.mjs','--check']);
const stdout=checked('cargo',['build','--manifest-path','classic-wasm/Cargo.toml','--locked','--release','--target','wasm32-unknown-unknown','--lib','--message-format=json']);
const binary=stdout.trim().split('\n').map(row=>JSON.parse(row))
  .find(row=>row.reason==='compiler-artifact' && row.target.name==='yuga_classic_roster')
  ?.filenames.find(file=>file.endsWith('.wasm'));
assert.ok(binary,'Cargo did not report the classic Wasm artifact');
const data=await readFile(binary);
const exports=WebAssembly.Module.exports(await WebAssembly.compile(data)).map(v=>v.name);
for(const name of ['memory','roster_input_capacity','roster_input_ptr','roster_reset','roster_command','roster_snapshot_ptr','roster_snapshot_len','roster_error_ptr','roster_error_len'])
  assert.ok(exports.includes(name),'Missing classic ABI export '+name);
const metadata=JSON.parse(checked('cargo',['metadata','--format-version=1','--locked','--manifest-path','classic-wasm/Cargo.toml','--filter-platform','wasm32-unknown-unknown']));
const blocks=new Map(), credits=[];
for (const p of metadata.packages.filter(p=>p.name!=='yuga-classic-roster').sort((a,b)=>a.name<b.name?-1:1)) {
  const root=dirname(p.manifest_path);
  const candidates=(await readdir(root,{withFileTypes:true})).filter(f=>f.isFile() && /^(license|licence|copying|notice)(?:[.-]|$)/i.test(f.name)).map(f=>f.name);
  if(p.license_file && !candidates.includes(p.license_file)) candidates.push(p.license_file);
  if (!candidates.length) throw new Error('Review missing notice for '+p.name);
  for(const name of candidates.sort()){
    const text=(await readFile(resolve(root,name),'utf8')).trim();
    const key=createHash('sha256').update(text).digest('hex').slice(0,16);
    blocks.set(key,text);
    credits.push(p.name+' '+p.version+' · '+p.license+' · '+name+' ['+key+']');
  }
}
const notice='YUGA classic roster Wasm · third-party notices\n\nIncludes the resolved Rust build dependency graph.\n\n'+credits.join('\n')+'\n\n'+[...blocks].map(([key,text])=>'['+key+']\n'+text).join('\n\n')+'\n';
await writeFile(resolve(project,'classic-wasm/THIRD-PARTY.txt'),notice);
const dest=fileURLToPath(new URL('../../yuga/client/assets/classic-roster.wasm',import.meta.url));
const tmp=dest+'.'+process.pid+'.tmp';
try {await writeFile(tmp,data,{flag:'wx'});await rename(tmp,dest);}finally{await rm(tmp,{force:true});}
console.log(data.length+' bytes  '+createHash('sha256').update(data).digest('hex')+'  '+dest);
