import { createGameServer } from './server.js';

const port = Number(process.env.PORT ?? 3001);
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('PORT must be an integer between 1 and 65535');
const server = await createGameServer({ port, host: process.env.HOST ?? '0.0.0.0', dataDir: process.env.ANDOLAN_DATA_DIR });
console.log(`ANDOLAN development room service listening on ${port}; /health and /ws available.`);
let closing = false;
for (const signal of ['SIGINT', 'SIGTERM'] as const) process.on(signal, () => {
  if (closing) return;
  closing = true;
  void server.close().then(() => process.exit(0), error => { console.error(error); process.exit(1); });
});
