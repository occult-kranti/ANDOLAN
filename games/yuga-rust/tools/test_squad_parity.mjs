// Exercise the native room and its packaged Wasm worker with the same public input.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { once } from 'node:events';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const tool = fileURLToPath(import.meta.url);
const crate = path.resolve(path.dirname(tool), '..');
const { values } = parseArgs({
  options: {
    binary: {
      type: 'string',
      default: path.join(crate, 'target/release', process.platform === 'win32' ? 'room.exe' : 'room'),
    },
    wasm: {
      type: 'string',
      default: path.join(crate, 'target/wasm32-unknown-unknown/release/yuga_rust.wasm'),
    },
    report: { type: 'string' },
  },
});
const wasm = path.resolve(values.wasm);
const worker = path.join(crate, 'tools/room-wasm.mjs');
const programs = [[path.resolve(values.binary)], [process.execPath, worker, wasm]];
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const seats = [0, 1, 2, 3, 4, 5];
const team = (seat) => (seat % 2 === 0 ? 'sun' : 'moon');
const neutral = () => seats.map(() => ({}));
const direction = (a, b) => {
  const dx = b[0] - a[0],
    dz = b[1] - a[1],
    n = Math.hypot(dx, dz);
  return n ? [dx / n, dz / n] : [0, 1];
};
const cast = (slot, origin, target) => ({
  casts: [{ slot, ground: target, aim: direction(origin, target) }],
});
const mixed = ['rama', 'hanuman', 'hanuman', 'rama', 'rama', 'hanuman'];
const court = seats.map((seat) => [11 + Math.floor(seat / 2) * 0.35, seat % 2 ? 1 : -1]);
const checks = { compared_frames: 0, compared_seat_snapshots: 0, compared_remote_portraits: 0 };
const transcript = createHash('sha256');
const tolerance = 0.0001;
let numericFields = 0,
  maxError = 0,
  maxErrorField = null;
function compare(a, b, field = '$') {
  if (typeof a === 'number') {
    assert.ok(typeof b === 'number' && Number.isFinite(a) && Number.isFinite(b), field);
    numericFields++;
    const delta = Math.abs(a - b);
    if (delta > maxError) {
      maxError = delta;
      maxErrorField = field;
    }
    if (Number.isInteger(a) && Number.isInteger(b)) assert.equal(a, b, field);
    else assert.ok(delta <= tolerance, field + ' differs by ' + delta);
  } else if (a !== null && typeof a === 'object') {
    assert.ok(b !== null && typeof b === 'object' && Array.isArray(a) === Array.isArray(b), field);
    const keys = Object.keys(a);
    assert.equal(Object.keys(b).length, keys.length, field);
    for (const key of keys) {
      assert.ok(Object.hasOwn(b, key), field + '.' + key);
      compare(a[key], b[key], field + '.' + key);
    }
  } else assert.equal(a, b, field);
}

function peer([cmd, ...args]) {
  const child = spawn(cmd, args, { stdio: ['pipe', 'pipe', 'pipe'] });
  let errors = '';
  child.stderr.on('data', (data) => {
    errors += data;
  });
  const done = once(child, 'exit');
  const lines = createInterface({ input: child.stdout, crlfDelay: Infinity })[Symbol.asyncIterator]();
  return {
    async send(input) {
      const watchdog = setTimeout(() => child.kill('SIGKILL'), 15000);
      try {
        if (!child.stdin.write(JSON.stringify(input) + '\n')) await once(child.stdin, 'drain');
        const row = await lines.next();
        assert.ok(!row.done, 'Room stopped or timed out before publishing a frame: ' + errors);
        return JSON.parse(row.value);
      } finally {
        clearTimeout(watchdog);
      }
    },
    async close() {
      child.stdin.end();
      const [status] = await done;
      assert.equal(status, 0, errors);
    },
    abort() {
      child.kill();
    },
  };
}

async function match(heroes, exercise) {
  const peers = programs.map(peer);
  let packet;
  const exchange = async (input) => {
    const [native, portable] = await Promise.all(peers.map((p) => p.send(input)));
    // Compare all keys, integer counters, ordered receipts and floating-point transforms.
    compare(native, portable);
    assert.equal(native.states.length, 6);
    assert.equal(native.accepted.length, 6);
    for (const [i, s] of native.states.entries()) {
      assert.equal(s.seat, i);
      assert.equal(s.team, team(i));
      assert.equal(s.hero, heroes[i]);
      assert.equal(s.tick, native.states[0].tick);
      assert.equal(s.army.tick, s.tick);
      assert.deepEqual(
        s.roster.map((other) => other.seat),
        seats.filter((seat) => seat !== i),
      );
      for (const remote of s.roster) {
        assert.deepEqual(remote.actor, native.states[remote.seat].actor);
        assert.deepEqual(remote.events, native.states[remote.seat].events);
        assert.equal(remote.hero, heroes[remote.seat]);
        assert.equal(remote.team, team(remote.seat));
        assert.equal(remote.respawn_ticks, native.states[remote.seat].respawn_ticks);
      }
      assert.notEqual(s.opponent.team, s.team);
    }
    const ids = native.states.map((s) => s.actor.id);
    assert.equal(new Set(ids).size, 6);
    transcript.update(JSON.stringify(input) + '\n' + JSON.stringify(native) + '\n');
    checks.compared_frames++;
    checks.compared_seat_snapshots += 6;
    checks.compared_remote_portraits += 30;
    packet = native;
    return packet;
  };
  try {
    await exchange({ heroes });
    assert.deepEqual(
      packet.accepted,
      seats.map(() => null),
    );
    async function step(players = neutral(), ticks = 1) {
      return exchange({ players, ticks });
    }
    async function advance(ticks, players = neutral()) {
      while (ticks > 0) {
        const n = Math.min(4, ticks);
        await step(players, n);
        ticks -= n;
      }
    }
    async function walkTogether() {
      const start = packet.states.map((s) => s.actor.pos);
      const delta = court.map((q, i) => q.map((x, j) => x - start[i][j]));
      const n = Math.max(1, ...delta.map((d) => Math.ceil(Math.hypot(...d) / 0.25)));
      await advance(
        n,
        delta.map((d, i) => ({
          motion: { movement: d.map((x) => x / (0.25 * n)), aim: direction(court[i], court[i ^ 1]) },
        })),
      );
      for (const i of seats)
        assert.ok(
          Math.hypot(...packet.states[i].actor.pos.map((x, j) => x - court[i][j])) < 0.005,
          'Failed to walk to open court, seat ' + i + ' ended at ' + packet.states[i].actor.pos,
        );
    }
    const result = await exercise({ step, advance, walkTogether, states: () => packet.states });
    await Promise.all(peers.map((p) => p.close()));
    return result;
  } finally {
    for (const p of peers) p.abort();
  }
}

async function jointKnockouts() {
  return match(
    seats.map(() => 'hanuman'),
    async ({ step, advance, walkTogether, states }) => {
      await walkTogether();
      const accepted = seats.map(() => 0);
      const damageTicks = [];
      let prior = states()[0].actor.hp;
      for (let t = 0; t < 150; t++) {
        const q = await step(seats.map((i) => cast(0, court[i], court[i ^ 1])));
        q.accepted.forEach((ok, i) => {
          if (ok) accepted[i]++;
        });
        const hp = q.states[0].actor.hp;
        assert.ok(
          q.states.every((s) => s.actor.hp === hp),
          'simultaneous damage changed by seat order',
        );
        if (hp < prior) damageTicks.push(q.states[0].tick);
        prior = hp;
        if (hp === 0) break;
      }
      const death = states()[0].tick;
      assert.equal(prior, 0, 'all six heroes must be defeated by ordinary enemy swings');
      assert.ok(damageTicks.length > 1);
      assert.equal(new Set(accepted).size, 1);
      assert.ok(states().every((s) => s.respawn_ticks === 60 && s.knockouts === 1 && !s.actor.alive));
      const rejected = await step(seats.map((i) => cast(0, court[i], court[i ^ 1])));
      assert.deepEqual(
        rejected.accepted,
        seats.map(() => false),
      );
      await advance(58);
      assert.ok(states().every((s) => s.respawn_ticks === 1 && !s.actor.alive));
      await advance(1);
      assert.ok(
        states().every(
          (s) =>
            s.respawn_ticks === 0 && s.actor.alive && s.actor.hp === s.actor.max_hp && s.actor.shield === 0,
        ),
      );
      return {
        court,
        attacks_accepted: accepted,
        damage_ticks: damageTicks,
        simultaneous_knockout_tick: death,
        simultaneous_respawn_tick: states()[0].tick,
      };
    },
  );
}

async function alliedSupport() {
  return match(mixed, async ({ step, advance, walkTogether, states }) => {
    await walkTogether();
    await step(seats.map((i) => (i === 1 || i === 2 ? cast(0, court[i], court[i ^ 1]) : {})));
    await advance(5);
    const wounded = states().map((s) => s.actor.hp);
    assert.ok(states().every((s, i) => wounded[i] < s.actor.max_hp));
    const sun = await step(seats.map((i) => (i === 0 ? cast(3, court[i], court[i]) : {})));
    assert.deepEqual(sun.accepted, [true, null, null, null, null, null]);
    await advance(15);
    const sunOnly = states().map((s) => s.actor.hp);
    for (const [i, s] of states().entries()) {
      assert.equal(s.actor.shield, team(i) === 'sun' ? 55 : 0);
      assert.ok(
        team(i) === 'sun' ? s.actor.hp > wounded[i] : s.actor.hp === wounded[i],
        'Sun support must exclude all Moon bodies',
      );
    }
    const moon = await step(seats.map((i) => (i === 3 ? cast(3, court[i], court[i]) : {})));
    assert.deepEqual(moon.accepted, [null, null, null, true, null, null]);
    await advance(25);
    const healed = states().map((s) => s.actor.hp);
    assert.ok(
      healed.every((hp, i) => hp > wounded[i]),
      'every wounded teammate must receive healing',
    );
    assert.ok(
      states().every((s) => s.actor.shield === 55),
      'all three Sun and three Moon bodies must receive their allied ward',
    );
    const ids = states().map((s) => s.actor.id);
    for (const caster of [0, 3]) {
      const touched = new Set(
        states()
          [caster].events.flatMap((e) => e.receipts.map((r) => r.unit_id))
          .filter((id) => ids.includes(id)),
      );
      assert.deepEqual(
        [...touched].sort(),
        ids.filter((_, i) => team(i) === team(caster)).sort(),
        'actual hero recipient identities in ward receipts',
      );
    }
    await advance(78);
    assert.ok(
      states().every((s) => s.actor.shield === 0),
      'temporary shields should expire on every seat',
    );
    return {
      hero_ids: mixed,
      injured_hp: wounded,
      hp_after_sun_only: sunOnly,
      healed_hp: healed,
      shield_on_all_six: 55,
      shields_expired: true,
    };
  });
}

async function controls() {
  return match(mixed, async ({ step, advance, states }) => {
    const activations = [];
    // Grounded, diverging lane positions exercise targets, locomotion, melee and moving archery.
    for (const slot of [0, 1, 2, 3, 4]) {
      const starts = states().map((s) => s.actor.pos);
      const q = await step(seats.map((i) => cast(slot, starts[i], slot >= 3 ? starts[i] : starts[i ^ 1])));
      assert.deepEqual(
        q.accepted,
        seats.map(() => true),
        'fresh slot ' + slot,
      );
      for (const s of q.states)
        assert.ok(
          s.events.some((e) => e.kind === 'begin' && e.slot === slot && e.id === s.abilities[slot].id),
          'missing cast start for seat ' + s.seat,
        );
      activations.push(q.accepted.length);
      const dup = await step(seats.map((i) => cast(slot, starts[i], starts[i])));
      assert.deepEqual(
        dup.accepted,
        seats.map(() => false),
      );
      await advance(50);
      for (const s of states())
        assert.ok(
          s.events.some((e) => e.kind === 'release' && e.slot === slot && e.id === s.abilities[slot].id),
          'missing release for seat ' + s.seat,
        );
      if (slot === 0) {
        assert.ok(states().every((s, i) => mixed[i] !== 'rama' || s.ammo === 11));
        await step(seats.map(() => ({ reload: true })));
        assert.ok(states().every((s, i) => mixed[i] !== 'rama' || s.reload_ticks > 0));
        await advance(32);
        assert.ok(states().every((s, i) => mixed[i] !== 'rama' || s.ammo === s.max_ammo));
      }
    }
    return {
      slots: [0, 1, 2, 3, 4],
      accepted_seats_by_slot: activations,
      reloads: ['sun/0', 'moon/3', 'sun/4'],
    };
  });
}

function malformedLines() {
  const roster = { heroes: mixed },
    tail = neutral;
  function atLast(player) {
    const arr = tail();
    // If a decoder applies the first player's valid cast before parsing the last player's bad value, the frame isn't atomic.
    arr[0] = cast(0, [0, 0], [0, 1]);
    arr[5] = player;
    return { players: arr, ticks: 1 };
  }
  const cases = [
    [{ heroes: mixed.slice(0, 5) }],
    [{ heroes: [...mixed, 'rama'] }],
    [{ heroes: mixed.with(5, 'unknown') }],
    [roster, { players: neutral().slice(0, 5), ticks: 1 }],
    [roster, { players: neutral(), ticks: 0 }],
    [roster, { players: neutral(), ticks: 5 }],
    [roster, atLast({ motion: { movement: [0, 'no'] } })],
    [roster, atLast({ casts: Array(5).fill({ slot: 0, ground: [0, 0], aim: [0, 1] }) })],
    [roster, atLast({ motion: { movement: [0, 1e100] } })],
    [roster, atLast({ invalid: true })],
  ];
  for (const trace of cases)
    for (const [cmd, ...args] of programs) {
      const proc = spawnSync(cmd, args, {
        input: trace.map((v) => JSON.stringify(v)).join('\n') + '\n',
        encoding: 'utf8',
        timeout: 15000,
        maxBuffer: 2 * 1024 * 1024,
      });
      assert.equal(proc.error, undefined);
      assert.ok(
        Number.isInteger(proc.status) && proc.status !== 0,
        'invalid trace accepted: ' + JSON.stringify(trace),
      );
      const replies = proc.stdout.trim().split('\n').filter(Boolean);
      assert.equal(replies.length, trace.length - 1, 'malformed input must never publish partial frame');
      if (replies.length) assert.ok(JSON.parse(replies[0]).states.every((s) => s.tick === 540));
    }
  return cases.length;
}

async function rejectedAbi() {
  const bytes = await readFile(wasm);
  const fresh = async () => (await WebAssembly.instantiate(bytes, {})).instance.exports;
  const [control, probe] = await Promise.all([fresh(), fresh()]);
  for (const g of [control, probe]) {
    assert.equal(g.squad_init(...mixed.map((h) => (h === 'rama' ? 1 : 0))), 1);
    seats.forEach((i) => assert.equal(g.squad_motion(i, 0.1 * i, 0.08, 0, 1), 1));
  }
  const decode = new TextDecoder();
  function read(g) {
    return seats.map((i) => {
      const start = g.duel_snapshot(i),
        len = g.duel_snapshot_len();
      assert.ok(start > 0 && len > 0);
      return JSON.parse(decode.decode(new Uint8Array(g.memory.buffer, start, len)));
    });
  }
  const before = read(probe);
  const invalid = [
    ['unknown roster', () => probe.squad_init(0, 0, 0, 0, 0, 2)],
    ['seat outside room', () => probe.squad_motion(6, 0, 0, 0, 1)],
    ['nonfinite movement', () => probe.squad_motion(5, NaN, 0, 0, 1)],
    ['nonfinite aim', () => probe.squad_motion(0, 0.9, 0, Infinity, 1)],
    ['empty frame', () => probe.squad_advance(0)],
    ['oversized frame', () => probe.squad_advance(5)],
    ['bad action slot', () => probe.duel_cast(0, 5, 0, 0, 1, 0)],
    ['invalid cast ground', () => probe.duel_cast(4, 3, Infinity, 0, 1, 0)],
    ['invalid cast aim', () => probe.duel_cast(4, 3, 0, 0, NaN, 0)],
    ['bad reload seat', () => probe.duel_reload(6)],
  ];
  for (const [label, fn] of invalid) {
    assert.equal(fn(), 0, label);
    assert.deepEqual(read(probe), before, label + ' visibly mutated a squad');
  }
  assert.equal(probe.duel_snapshot(6), 0);
  assert.equal(probe.duel_snapshot_len(), 0);
  for (const g of [control, probe]) assert.equal(g.squad_advance(4), 1);
  assert.deepEqual(
    read(probe),
    read(control),
    'invalid staged motion changed the next legal four-tick frame',
  );
  return invalid.map(([s]) => s);
}

const knockouts = await jointKnockouts();
const allied_support = await alliedSupport();
const kit_controls = await controls();
const malformed_traces = malformedLines();
const rejected_abi = await rejectedAbi();
const report = {
  scope:
    'Full decoded native and Wasm NDJSON frames for six controllable seats, including all five remote portraits. Integer counters and ordered events match exactly, floating transforms use absolute tolerance 0.0001.',
  floating_tolerance: tolerance,
  max_absolute_numeric_error: maxError,
  max_error_field: maxErrorField,
  numeric_fields_compared: numericFields,
  ...checks,
  transcript_sha256: transcript.digest('hex'),
  knockouts,
  allied_support,
  kit_controls,
  malformed_traces_rejected_by_both: malformed_traces,
  abi_rejections_with_unchanged_all_seat_state: rejected_abi,
  staged_inputs_survive_rejections: true,
  node: process.version,
  hashes: {
    native_sha256: sha(await readFile(values.binary)),
    wasm_sha256: sha(await readFile(wasm)),
    worker_sha256: sha(await readFile(worker)),
    test_sha256: sha(await readFile(tool)),
  },
};
const output = JSON.stringify(report, null, 2) + '\n';
if (values.report) await writeFile(values.report, output);
process.stdout.write(output);
