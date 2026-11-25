// One authoritative Rust/WASM match. stdin/stdout use the same line protocol as src/bin/room.rs.
import { once } from 'node:events';
import { readFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';

const wasmPath = process.argv[2];
if (!wasmPath || process.argv.length !== 3) throw Error('Usage: node room-wasm.mjs path/to/room.wasm');
const { instance } = await WebAssembly.instantiate(await readFile(wasmPath), {});
const game = instance.exports;
for (const name of ['duel_start', 'duel_cast', 'duel_reload', 'duel_step', 'duel_snapshot', 'duel_snapshot_len']) {
  if (typeof game[name] !== 'function') throw Error('Room authority lacks the required export ' + name);
}
if (!(game.memory instanceof WebAssembly.Memory)) throw Error('Missing room memory export');

const decoder = new TextDecoder('utf-8', { fatal: true });
const hero = new Map([['hanuman', 0], ['rama', 1]]);
const zero = [0, 0];

function snapshot(seat) {
  const start = game.duel_snapshot(seat) >>> 0;
  const size = game.duel_snapshot_len() >>> 0;
  const memory = game.memory.buffer;
  if (!start || !size || start + size > memory.byteLength) throw Error('Invalid snapshot from room authority');
  // The next Rust call can grow memory or replace the snapshot buffer. Decode now.
  return decoder.decode(new Uint8Array(memory, start, size));
}

async function send(accepted) {
  const states = '[' + accepted.map((_,seat) => snapshot(seat)).join(',') + ']';
  const packet = '{"states":' + states + ',"accepted":' + JSON.stringify(accepted) + '}\n';
  if (!process.stdout.write(packet)) await once(process.stdout, 'drain');
}

function record(value, fields) {
  return value !== null && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).every(key => fields.includes(key));
}

function point(value) {
  return Array.isArray(value) && value.length === 2 && value.every(x => Number.isFinite(x) && Number.isFinite(Math.fround(x)));
}

function parsePlayer(player) {
  if (!record(player, ['motion', 'casts', 'reload'])) throw Error('Invalid input fields');
  const { motion = {}, casts = [], reload = false } = player;
  if (!record(motion, ['movement', 'aim']) || !Array.isArray(casts) || casts.length > 4 || typeof reload !== 'boolean') {
    throw Error('Invalid room input');
  }
  const { movement = zero, aim = zero } = motion;
  if (!point(movement) || !point(aim)) throw Error('Invalid motion');
  for (const cast of casts) {
    if (!record(cast, ['slot', 'ground', 'aim']) || !Number.isSafeInteger(cast.slot) || cast.slot < 0 ||
        !point(cast.ground) || !point(cast.aim)) throw Error('Invalid cast');
  }
  return { movement, aim, casts, reload };
}

let seatCount = 0;
for await (const line of createInterface({ input: process.stdin, crlfDelay: Infinity })) {
  const data = JSON.parse(line);
  if (!seatCount) {
    let roster;
    if (record(data, ['sun', 'moon']) && hero.has(data.sun) && hero.has(data.moon)) {
      roster = [data.sun, data.moon];
      if (game.duel_start(...roster.map(h => hero.get(h))) !== 1) throw Error('Invalid duel roster');
    } else if (record(data, ['heroes']) && Array.isArray(data.heroes) && [6, 10].includes(data.heroes.length) && data.heroes.every(h => hero.has(h))) {
      const init = data.heroes.length === 10 ? 'team_init' : 'squad_init';
      for (const name of [init, 'squad_motion', 'squad_advance']) {
        if (typeof game[name] !== 'function') throw Error('Missing squad authority export ' + name);
      }
      roster = data.heroes;
      if (game[init](...roster.map(h => hero.get(h))) !== 1) throw Error('Invalid squad roster');
    } else throw Error('Invalid room roster');
    seatCount = roster.length;
    await send(roster.map(() => null));
    continue;
  }
  if (!record(data, ['players', 'ticks']) || !Number.isInteger(data.ticks) || data.ticks < 1 || data.ticks > 4 ||
      !Array.isArray(data.players) || data.players.length !== seatCount) throw Error('Invalid room frame');
  const players = data.players.map(parsePlayer);
  const accepted = players.map((player, seat) => {
    if (player.reload) game.duel_reload(seat);
    let result = null;
    for (const { slot, ground, aim } of player.casts) {
      // Rust validates the selected hero's kit; bound before the u32 WASM conversion.
      result = slot < 6 && game.duel_cast(seat, slot, ...ground, ...aim) === 1;
    }
    return result;
  });
  if (seatCount === 2) {
    const [sun, moon] = players;
    for (let i = 0; i < data.ticks; i++) game.duel_step(...sun.movement, ...sun.aim, ...moon.movement, ...moon.aim);
  } else {
    players.forEach(({movement, aim}, seat) => {
      if (game.squad_motion(seat, ...movement, ...aim) === 0) throw Error('Invalid squad motion');
    });
    if (game.squad_advance(data.ticks) === 0) throw Error('Invalid squad tick count');
  }
  await send(accepted);
}
