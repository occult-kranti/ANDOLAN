import { cp, mkdir, rm } from 'node:fs/promises';
await rm('dist/site',{recursive:true,force:true});
await mkdir('dist/site',{recursive:true});
await cp('dist/standalone','dist/site',{recursive:true});
await cp('dist/yuga','dist/site/yuga',{recursive:true});
console.log('Combined site: ANDOLAN at /, YUGA at /yuga/.');
