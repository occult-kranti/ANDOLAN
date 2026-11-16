#!/usr/bin/env python3
"""Own one X11 display and render actual tactical screens to a fresh evidence path."""
import argparse,json,os,shutil
from pathlib import Path
import subprocess,time

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,default=Path('games/yuga-native'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--display',type=int,default=142)
    p.add_argument('--motion',action='store_true')
    p.add_argument('--weapon-only',action='store_true')
    p.add_argument('--showcase-only',action='store_true')
    p.add_argument('--map-only',action='store_true')
    p.add_argument('--cache-seed',type=Path)
    args=p.parse_args();out=args.output.resolve();project=args.project.resolve()
    if out.exists() or Path(f'/tmp/.X11-unix/X{args.display}').exists():raise ValueError('Fresh output and unused display required')
    out.parent.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env.update(DISPLAY=f':{args.display}',VK_ICD_FILENAMES='/usr/share/vulkan/icd.d/lvp_icd.json',LP_NUM_THREADS='4')
    for key,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        dest=out.parent/(out.name+'-user')/folder;dest.mkdir(parents=True,exist_ok=True);env[key]=str(dest)
    if args.cache_seed:
        if not args.cache_seed.is_dir():raise ValueError('Missing shader cache seed')
        shutil.copytree(args.cache_seed,Path(env['XDG_CACHE_HOME']),dirs_exist_ok=True)
    with out.with_suffix('.xvfb.log').open('w') as xlog,out.with_suffix('.godot.log').open('w') as log:
        server=subprocess.Popen(['Xvfb',env['DISPLAY'],'-screen','0','1280x720x24','-nolisten','tcp','-ac'],stdout=xlog,stderr=subprocess.STDOUT)
        try:
            for _ in range(40):
                if Path(f'/tmp/.X11-unix/X{args.display}').exists():break
                time.sleep(.1)
            command=['godot','--path',str(project),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync']
            if args.motion:command+=['--fixed-fps','15']
            command+=['--script','res://tools/capture-tactical-motion.gd' if args.motion else 'res://tools/capture-tactical.gd','--','--output='+str(out)]
            if args.weapon_only:command+=['--weapon-only']
            if args.showcase_only:command+=['--showcase-only']
            if args.map_only:command+=['--map-only']
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
        finally:
            server.terminate();server.wait(timeout=10)
    report=json.loads((out/('motion.json' if args.motion else 'review.json')).read_text());logtext=out.with_suffix('.godot.log').read_text()
    good=result.returncode==0 and report['complete'] and 'SCRIPT ERROR:' not in logtext and '\nERROR:' not in logtext
    print(json.dumps({'complete':good,'images':len(report['frames'] if args.motion else report['shots']),'output':str(out),'exit':result.returncode,'cache_seed':str(args.cache_seed) if args.cache_seed else None}))
    raise SystemExit(0 if good else 1)
if __name__=='__main__':main()
