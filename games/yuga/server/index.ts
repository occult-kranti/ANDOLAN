import { createArenaServer } from './server.js';

const port = Number(process.env.PORT || 3005);
const server = await createArenaServer({ port: Number.isInteger(port) && port > 0 && port <= 65535 ? port : 3005 });
console.log(`YUGA arena listening on ${JSON.stringify(server.address)}`);
let closing = false;
async function close() { if (closing) return; closing = true; await server.close(); process.exit(0); }
process.on('SIGINT', () => { void close(); });
process.on('SIGTERM', () => { void close(); });
