#!/usr/bin/env python3
"""Fresh isolated Node transport + native Godot authority + two actual native clients.

Uses existing installed npm dependencies and Godot4.6.3. No editor import/render.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NATIVE = ROOT / 'games/yuga-native'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stop(child):
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=4)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=4)


def wait_json(path, process, timeout=6):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('process exited before readiness: ' + str(path))
        if path.exists():
            try:
                return json.loads(path.read_text())
            except json.JSONDecodeError:
                pass
        time.sleep(.025)
    raise TimeoutError('readiness deadline: ' + str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--godot', default='godot')
    parser.add_argument('--negative-control', choices=['flatten'], help='Deliberately flatten only the copied native wire position; expected to fail')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(ROOT):
        raise ValueError('fresh outside-checkout output required')
    output.mkdir(parents=True)
    project = output / 'project'
    (project / 'scripts').mkdir(parents=True)
    source_paths = [NATIVE / 'scripts/arena_client.gd', NATIVE / 'scripts/arena_interpolator.gd', NATIVE / 'scripts/player.gd', NATIVE / 'tests/physics_authority_cases.gd', NATIVE / 'assets/contracts/physics-fixture-v1.json', ROOT / 'games/yuga/server/server.ts', ROOT / 'games/yuga/server/authority-factory.ts', ROOT / 'games/yuga/server/clock.ts', ROOT / 'games/yuga/shared/simulation.ts', ROOT / 'games/yuga/shared/types.ts', ROOT / 'games/yuga/shared/map.ts', ROOT / 'package-lock.json']
    source_paths += [p for p in HERE.iterdir() if p.is_file()]
    before = {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    for name in ['authority_actor.gd', 'native_authority.gd', 'client_cases.gd', 'contract_cases.gd', 'bridge-contract.json']:
        shutil.copyfile(HERE / name, project / name)
    if args.negative_control == 'flatten':
        script = project / 'authority_actor.gd'
        original = script.read_text()
        if original.count('"y":position.y') != 1:
            raise RuntimeError('negative-control wire target changed')
        script.write_text(original.replace('"y":position.y', '"y":0.0'))
    for name in ['arena_client.gd', 'arena_interpolator.gd']:
        shutil.copyfile(NATIVE / 'scripts' / name, project / 'scripts' / name)
    shutil.copyfile(NATIVE / 'assets/contracts/physics-fixture-v1.json', project / 'physics-fixture-v1.json')
    (project / 'project.godot').write_text('config_version=5\n[application]\nconfig/name="Isolated native authority pilot"\n[threading]\nworker_pool/max_threads=1\n[physics]\ncommon/physics_ticks_per_second=60\n')
    # Directly import the production server; inject the typed native factory.
    # No server source copy, import substitution or dynamic module selector.
    (output / 'package.json').write_text('{"private":true,"type":"module"}\n')
    (output / 'node_modules').symlink_to(ROOT / 'node_modules', target_is_directory=True)
    (output / 'adaptation.json').write_text(json.dumps({'mode': 'direct-server-import-with-typed-authority-factory', 'sourceSha256': before['games/yuga/server/server.ts'], 'authorityContractSha256': before['games/yuga/server/authority-factory.ts'], 'factory': 'createNativePilotAuthority', 'onlyChanges': []}, indent=2) + '\n')
    env = os.environ.copy()
    env.update({'GODOT_SILENCE_ROOT_WARNING': '1', 'OMP_NUM_THREADS': '1'})
    processes = []
    handles = []
    result = {'passed': False, 'scope': 'Real loopback native3D authority feasibility; no browser3D, rendering, production protocol or complete-match acceptance', 'negativeControl': args.negative_control, 'sourceSha256': before, 'engine': subprocess.check_output([args.godot, '--version'], text=True).strip(), 'node': subprocess.check_output(['node', '--version'], text=True).strip(), 'npmVersions': {name: json.loads((ROOT / 'node_modules' / name / 'package.json').read_text())['version'] for name in ['ws', 'tsx']}}
    try:
        if not result['engine'].startswith('4.6.3.'):
            raise RuntimeError('Godot4.6.3 required')
        for name in ['native_authority.gd', 'client_cases.gd', 'contract_cases.gd']:
            run = subprocess.run([args.godot, '--headless', '--path', str(project), '--script', 'res://' + name, '--check-only'], env=env, capture_output=True, text=True, timeout=10)
            (output / (name + '.compile.log')).write_text(run.stdout + run.stderr)
            if run.returncode or 'SCRIPT ERROR' in run.stdout + run.stderr:
                raise RuntimeError('compile failed: ' + name)
        with (output / 'native-contract.log').open('w') as log:
            native_contract = subprocess.run([args.godot, '--headless', '--path', str(project), '--script', 'res://contract_cases.gd', '--', '--report=' + str(output / 'native-contract.json')], env=env, stdout=log, stderr=subprocess.STDOUT, timeout=10)
        result['nativeContract'] = json.loads((output / 'native-contract.json').read_text())
        with (output / 'typescript-contract.log').open('w') as log:
            ts_contract = subprocess.run([str(ROOT / 'node_modules/.bin/tsx'), '--test', str(HERE / 'native_state.test.ts'), str(HERE / 'authority_factory.test.ts')], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=15)
        result['typescriptContractExitCode'] = ts_contract.returncode
        if native_contract.returncode or not result['nativeContract']['passed'] or ts_contract.returncode:
            raise RuntimeError('cheap contract counterexample failed')
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            native_port = listener.getsockname()[1]
        native_log = (output / 'native.log').open('w'); handles.append(native_log)
        native = subprocess.Popen([args.godot, '--headless', '--path', str(project), '--script', 'res://native_authority.gd', '--', '--port=' + str(native_port), '--ready=' + str(output / 'native-ready.json'), '--report=' + str(output / 'native-report.json')], env=env, stdout=native_log, stderr=subprocess.STDOUT, start_new_session=True)
        processes.append(native)
        ready = wait_json(output / 'native-ready.json', native)
        harness = f'''import {{createArenaServer}} from {json.dumps((ROOT / 'games/yuga/server/server.ts').as_uri())};
import {{connectNative,closeNative,bridgeStats,createNativePilotAuthority}} from {json.dumps((HERE / 'vertical_simulation.ts').as_uri())};
import {{writeFile}} from 'node:fs/promises';
await connectNative({native_port},{json.dumps(ready['fixtureHash'])},{json.dumps(ready['contractHash'])});
const factoryChecks={{nonzeroBotsRejected:false,secondRoomRejected:false}};
try{{createNativePilotAuthority({{room:'INVALID-BOTS',seed:1,botsPerTeam:1}});}}
catch(error){{factoryChecks.nonzeroBotsRejected=error instanceof Error&&error.message==='Native pilot authority does not simulate bots';}}
const server=await createArenaServer({{port:0,host:'127.0.0.1',simulation:{{duration:30,botsPerTeam:0}},authorityFactory:createNativePilotAuthority}});
const address=server.address;if(!address||typeof address==='string')throw Error('listener missing');
await writeFile({json.dumps(str(output / 'server-ready.json'))},JSON.stringify({{url:`ws://127.0.0.1:${{address.port}}/ws`}}));
let closing=false;process.on('SIGTERM',async()=>{{if(closing)return;closing=true;
try{{createNativePilotAuthority({{room:'SECOND-ROOM',seed:2,botsPerTeam:0}});}}
catch(error){{factoryChecks.secondRoomRejected=error instanceof Error&&error.message==='Native pilot authority supports one room';}}
await server.close();closeNative();await writeFile({json.dumps(str(output / 'server-report.json'))},JSON.stringify({{bridgeStats,factoryChecks,roomsAfterClose:server.rooms.size}}));process.exit(0);}});
'''
        (output / 'harness.mts').write_text(harness)
        server_log = (output / 'server.log').open('w'); handles.append(server_log)
        server_process = subprocess.Popen([str(ROOT / 'node_modules/.bin/tsx'), str(output / 'harness.mts')], env=env, cwd=ROOT, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
        processes.append(server_process)
        endpoint = wait_json(output / 'server-ready.json', server_process)
        clients = {}
        for role in ['host', 'guest']:
            log = (output / (role + '.log')).open('w'); handles.append(log)
            client_env = env.copy()
            for key in ['DATA', 'CONFIG', 'CACHE']:
                client_env['XDG_' + key + '_HOME'] = str(output / role / key.lower())
            command = [args.godot, '--headless', '--path', str(project), '--script', 'res://client_cases.gd', '--', '--role=' + role, '--url=' + endpoint['url'], '--coordination=' + str(output / 'room.json'), '--report=' + str(output / (role + '-report.json'))]
            clients[role] = subprocess.Popen(command, env=client_env, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            processes.append(clients[role])
        result['clients'] = {}
        for role, process in clients.items():
            code = process.wait(timeout=22)
            report = json.loads((output / (role + '-report.json')).read_text())
            result['clients'][role] = {'passed': report['passed'], 'exitCode': code, 'identity': report['identity'], 'peer': report['peer'], 'checks': report['checks']}
        server_process.send_signal(signal.SIGTERM); server_process.wait(timeout=5)
        result['server'] = json.loads((output / 'server-report.json').read_text())
        result['native'] = json.loads((output / 'native-report.json').read_text())
        states = result['native']['samples']
        stages = {name: [row for row in states if row['stage'] == name] for name in ['stacked','ramp-stairs','ledge-ceiling','aim','underpass','expiry']}
        poses = lambda stage, slot: [actor for row in stages[stage] for actor in row['actors'] if actor['bridgeSlot'] == slot]
        stacked0, stacked1 = poses('stacked',0), poses('stacked',1)
        ramp, stairs = poses('ramp-stairs',0), poses('ramp-stairs',1)
        ledge, ceiling = poses('ledge-ceiling',0), poses('ledge-ceiling',1)
        aim0, aim1 = poses('aim',0), poses('aim',1)
        lower, upper = poses('underpass',0), poses('underpass',1)
        expiry = poses('expiry',0)
        result['physicsChecks'] = {
            'distinct_same_xz_stacked_supports': all(abs(a['x']-b['x'])<.001 and abs(a['z']-b['z'])<.001 and b['y']-a['y']>2.9 for a,b in zip(stacked0,stacked1)) and any(a['support']=='deck-lower' for a in stacked0) and any(a['support']=='deck-upper' for a in stacked1),
            'native_capsule_climbs_ramp': max(a['y'] for a in ramp)>2.5,
            'stairs_do_not_invent_automatic_step': max(a['z'] for a in stairs)<.01 and max(a['y'] for a in stairs)<.1,
            'walk_off_ledge_falls_to_road': max(a['y'] for a in ledge)>1.4 and min(a['y'] for a in ledge[-5:])<.1,
            'low_ceiling_bounds_server_jump': .05<max(a['y'] for a in ceiling)<.25,
            'remote_positive_pitch_hits_high_target': any(a['shot'].get('target')=='target-high' for a in aim0),
            'remote_level_pitch_hits_low_target': any(a['shot'].get('target')=='target-low' for a in aim1),
            'underpass_and_bridge_keep_elevation': any(a['support']=='road' for a in lower) and any(a['support']=='bridge' for a in upper) and min(a['y'] for a in upper)>4.2,
            'stale_intent_expires_without_client_position': any(a['nativeTick']-a['bridgeInputTick']>32 for a in expiry) and all(abs(a['velocity'][2])<.01 for a in expiry if a['nativeTick']-a['bridgeInputTick']>32) and max(a['z'] for a in expiry)-min(a['z'] for a in expiry)<6.0,
            'two_unique_native_clients': result['clients']['host']['identity']!=result['clients']['guest']['identity'] and result['clients']['host']['peer']==result['clients']['guest']['identity'] and result['clients']['guest']['peer']==result['clients']['host']['identity'],
            'existing_stale_sequence_guard_active': result['server']['bridgeStats']['staleInputs']>=2,
            'native_packets_versioned_and_valid': result['server']['bridgeStats']['nativePackets']>100 and result['server']['bridgeStats']['rejectedNativePackets']==0,
            'server_cleanup': result['server']['roomsAfterClose']==0,
        }
        result['passed'] = all(row['passed'] and row['exitCode']==0 for row in result['clients'].values()) and all(result['physicsChecks'].values()) and all(result['server']['factoryChecks'].values())
    except Exception as error:
        result['failure'] = type(error).__name__ + ': ' + str(error)
    finally:
        for process in reversed(processes): stop(process)
        for handle in handles: handle.close()
    result['sourcesUnchanged'] = before == {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    result['passed'] = result['passed'] and result['sourcesUnchanged']
    (output / 'integration-report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'report': str(output / 'integration-report.json'), 'physicsChecks': result.get('physicsChecks'), 'failure': result.get('failure')}))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
