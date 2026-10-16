import { cp, mkdir, rm } from 'node:fs/promises';
await rm('dist/site',{recursive:true,force:true});
await mkdir('dist/site',{recursive:true});
await cp('dist/standalone','dist/site',{recursive:true});
await cp('dist/yuga','dist/site/yuga',{recursive:true});
await cp('dist/yuga-lab','dist/site/yuga/lab',{recursive:true});
await cp('dist/yuga-lane-lab','dist/site/yuga/lane-lab',{recursive:true});
await cp('dist/yuga-control-lab','dist/site/yuga/control-lab',{recursive:true});
console.log('Combined site: ANDOLAN at /, YUGA at /yuga/, labs at /yuga/lab/, /yuga/lane-lab/ and /yuga/control-lab/.');
