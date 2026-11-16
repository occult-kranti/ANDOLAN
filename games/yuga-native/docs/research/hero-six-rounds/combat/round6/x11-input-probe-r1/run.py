import ctypes as C,ctypes.util,hashlib,json,os,subprocess,time
from pathlib import Path
out=Path(__file__).resolve().parent
engine=Path('/workspaces/ANDOLAN/.local-tools/review/sangam-package-linux-r1/yuga-native-linux-x86_64/godot')
env=os.environ.copy();env.update(DISPLAY=':138',XDG_DATA_HOME=str(out/'user/data'),XDG_CACHE_HOME=str(out/'user/cache'),XDG_CONFIG_HOME=str(out/'user/config'),LP_NUM_THREADS='2')
assert not Path('/tmp/.X138-lock').exists()
xlog=(out/'xvfb.log').open('x');log=(out/'game.log').open('x')
server=subprocess.Popen(['Xvfb',':138','-screen','0','400x300x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xlog,stderr=subprocess.STDOUT)
game=None;d=None;events=[]
x=C.CDLL(ctypes.util.find_library('X11'));xt=C.CDLL(ctypes.util.find_library('Xtst'))
x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p
x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong
x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)]
x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong]
x.XFree.argtypes=[C.c_void_p];x.XFlush.argtypes=[C.c_void_p];x.XCloseDisplay.argtypes=[C.c_void_p]
xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
try:
 time.sleep(.6);d=x.XOpenDisplay(b':138');assert d
 command=[str(engine),'--path',str(out),'--script',str(out/'probe.gd'),'--display-driver','x11','--rendering-method','gl_compatibility','--audio-driver','Dummy','--resolution','400x300','--position','0,0','--max-fps','30']
 game=subprocess.Popen(command,env=env,cwd=out,stdout=log,stderr=subprocess.STDOUT)
 for attempt in range(100):
  if '"kind":"ready"' in (out/'game.log').read_text():break
  if game.poll() is not None:raise RuntimeError('engine exited '+str(game.returncode))
  time.sleep(.2)
 else:raise RuntimeError('probe ready timeout')
 root,parent=C.c_ulong(),C.c_ulong();children=C.POINTER(C.c_ulong)();count=C.c_uint();x.XQueryTree(d,x.XDefaultRootWindow(d),C.byref(root),C.byref(parent),C.byref(children),C.byref(count));target=None
 for i in range(count.value):
  name=C.c_char_p()
  if x.XFetchName(d,children[i],C.byref(name)) and name.value:
   title=name.value.decode(errors='replace')
   if title.startswith('YUGA'):target=children[i]
   x.XFree(name)
 if children:x.XFree(children)
 assert target
 x.XSetInputFocus(d,target,2,0);x.XFlush(d);time.sleep(.4)
 for button,pressed in [(3,True),(3,False),(1,True),(1,False),(3,True),(3,False)]:
  result=xt.XTestFakeButtonEvent(d,button,int(pressed),0);x.XFlush(d)
  events.append({'button':button,'pressed':pressed,'xtest_result':result,'time_unix':time.time()})
  time.sleep(.7)
finally:
 if d:
  for button in (1,3):xt.XTestFakeButtonEvent(d,button,0,0)
  x.XFlush(d)
 if game and game.poll() is None:game.terminate();game.wait(timeout=8)
 if d:x.XCloseDisplay(d)
 server.terminate();server.wait(timeout=8);log.close();xlog.close()
 rows=[]
 for line in (out/'game.log').read_text().splitlines():
  if line.startswith('INPUT_AUDIT '):rows.append(json.loads(line[len('INPUT_AUDIT '):]))
 report={'engine_sha256':hashlib.sha256(engine.read_bytes()).hexdigest(),'command':command,'display':':138','xtest_events':events,'godot_events':rows,'scope':'Tiny independent compatibility-rendered window; no gameplay/assets/shared imports or live package input mutation.'}
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
