import assert from 'node:assert/strict';
import {createArenaServer} from './compiled-server/games/yuga/server/server.js';
import {writeFile} from 'node:fs/promises';
const server=await createArenaServer({port:0,host:'127.0.0.1'});
try { const health=await fetch(`http://127.0.0.1:${server.address.port}/health`).then(r=>r.json());
assert.equal(health.protocol,2);assert.equal(health.simulationHz,20);assert.equal(health.snapshotHz,10);assert.equal(health.rooms,0);
await writeFile(new URL('./compiled-smoke.json',import.meta.url),JSON.stringify({passed:true,health}));
} finally {await server.close();}
