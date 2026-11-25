import * as pc from 'playcanvas';
import { createOriginalEnvironment } from './environment-light.ts';

const heroes = {
    hanuman: { name: 'Hanuman', clips: { fire: 'Vajra Gada', cast1: 'Maruti Udayana', cast2: 'Vajra Kavacha', tail_sweep: 'Lanka Dahan' } },
    rama: { name: 'Rama', clips: {} },
    shiva: { name: 'Shiva', clips: { fire: 'Crescent Spark', cast1: 'Threefold Sweep', cast2: 'Stillwater Coil', cast3: 'Tandava Downbeat' } },
    krishna: { name: 'Krishna', clips: { fire: 'Chakra Flick', cast1: 'Turning Star', cast2: 'Reed Refrain', cast3: 'Govardhan Canopy' } },
};
const ordinary = ['idle', 'run', 'jump', 'fire', 'cast', 'cast1', 'cast2', 'cast3', 'defeat'];
const clipNames = { fire: 'Primary', cast: 'Cast', cast1: 'Cast 1', cast2: 'Cast 2', cast3: 'Cast 3' };
const presets = { front: 0, side: 90, rear: 180 };
const $ = id => document.getElementById(id);
const scene = $('scene'), message = $('message'), picker = $('hero'), scrub = $('scrub'), speed = $('speed'), loop = $('loop'), play = $('play');
const url = new URL(location.href);
const directFile = location.protocol === 'file:';
const initialHero = Object.hasOwn(heroes, url.searchParams.get('hero')) ? url.searchParams.get('hero') : 'hanuman';
const initialView = Object.hasOwn(presets, url.searchParams.get('view')) ? url.searchParams.get('view') : 'front';
const titleCase = s => s.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
function show(text, chooseFile = false) {
    message.textContent = text;
    $('prompt').hidden = !text && !chooseFile;
    $('file-prompt').hidden = !chooseFile;
}
function setControls(ready) {
    for (const input of [play, scrub, speed, loop, ...document.querySelectorAll('[data-view],.clip')]) input.disabled = !ready;
}
function saveLocation(hero, clip, view) {
    const link = new URL(location.href);
    link.searchParams.set('hero', hero);
    if (clip) link.searchParams.set('clip', clip); else link.searchParams.delete('clip');
    if (view) link.searchParams.set('view', view); else link.searchParams.delete('view');
    if (!directFile) history.replaceState(null, '', link);
}
function createStage(app) {
    createOriginalEnvironment(app);
    app.scene.ambientLight = new pc.Color(.28, .31, .33);
    app.scene.skyboxIntensity = .52;
    const key = (name, angles, tint, intensity) => {
        const lamp = new pc.Entity(name, app); app.root.addChild(lamp);
        lamp.addComponent('light', { type: 'directional', color: new pc.Color().fromString(tint), intensity });
        lamp.setEulerAngles(...angles);
    };
    key('Warm softbox', [48, -26, 0], '#ffdfb5', 1.6);
    key('Blue fill', [22, 54, 0], '#b9d8ed', .72);
    key('Edge', [34, 152, 0], '#ffd79e', 1.25);
    const ground = new pc.Entity('Studio plinth', app);
    app.root.addChild(ground);
    ground.addComponent('render', { type: 'cylinder' });
    const mat = new pc.StandardMaterial();
    mat.diffuse = new pc.Color().fromString('#263430');
    mat.shininess = 14;
    mat.update();
    ground.render.meshInstances[0].material = mat;
    ground.setLocalScale(2.6, .032, 2.6);
    ground.setLocalPosition(0, -.022, 0);
    const camera = new pc.Entity('Camera', app); app.root.addChild(camera);
    camera.addComponent('camera', { fov: 32, nearClip: .04, farClip: 100, clearColor: new pc.Color().fromString('#29383b') });
    camera.camera.layers = camera.camera.layers.filter(id => id !== pc.LAYERID_SKYBOX);
    return camera;
}

async function start() {
    picker.value = initialHero;
    const app = new pc.Application(scene, { graphicsDeviceOptions: { alpha: false, antialias: true, preserveDrawingBuffer: false } });
    const camera = createStage(app);
    const loaded = new Map(), localFiles = new Map();
    let requestedClip = null;
    let entity, layer, tracks = new Map(), selectedHero = initialHero, clip = '', time = 0, duration = 0;
    let ready = false, version = 0, raf = 0, lastTime = null, draw = true, rendered = 0;
    let playing = !matchMedia('(prefers-reduced-motion: reduce)').matches;
    let yaw = presets[initialView], pitch = 6, zoom = 1, view = initialView, center = new pc.Vec3(0, 1.12, 0), fit = 4.8;
    let meshCount = 0, jointCount = 0;
    function requestDraw() { draw = true; if (!raf && !document.hidden) raf = requestAnimationFrame(frame); }
    function updateCamera() {
        const rect = scene.getBoundingClientRect();
        const aspect = Math.max(.3, rect.width / Math.max(1, rect.height));
        const distance = fit * zoom / Math.min(1, aspect);
        const a = yaw * Math.PI / 180, b = pitch * Math.PI / 180;
        camera.setPosition(center.x + Math.sin(a)*Math.cos(b)*distance, center.y + Math.sin(b)*distance, center.z + Math.cos(a)*Math.cos(b)*distance);
        camera.lookAt(center);
        document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
        requestDraw();
    }
    function sizeCanvas() {
        const r = scene.getBoundingClientRect();
        const pixelRatio = Math.min(devicePixelRatio || 1, 1.5, Math.sqrt(1500000 / Math.max(1, r.width*r.height)));
        app.setCanvasResolution(pc.RESOLUTION_FIXED, Math.max(1, Math.round(r.width*pixelRatio)), Math.max(1, Math.round(r.height*pixelRatio)));
        updateCamera();
    }
    const observer = new ResizeObserver(sizeCanvas);
    observer.observe($('stage'));
    function timeDisplay() {
        scrub.value = String(time); $('clock').textContent = time.toFixed(2) + ' / ' + duration.toFixed(2) + ' s';
        scrub.setAttribute('aria-valuetext', time.toFixed(2) + ' seconds of ' + duration.toFixed(2));
        play.textContent = playing ? 'Pause' : 'Play';
    }
    function frame(now) {
        raf = 0;
        if (document.hidden) { lastTime = null; return; }
        if (ready && playing && lastTime !== null) {
            time += Math.max(0, now-lastTime) / 1000 * Number(speed.value);
            if (time >= duration) {
                if (loop.checked) time %= duration;
                else { time = duration; playing = false; }
            }
        }
        lastTime = now;
        if (draw || (ready && playing) || (ready && time === duration)) {
            if (ready) {
                layer.activeStateCurrentTime = Math.min(time, Math.max(0, duration-.000001));
                timeDisplay();
            }
            app.update(0); app.render(); rendered++;
            draw = false;
        }
        if (ready && playing) raf = requestAnimationFrame(frame);
    }
    function toggle() {
        if (!ready) return;
        if (!playing && time >= duration) time = 0;
        playing = !playing; lastTime = null; timeDisplay(); requestDraw();
    }
    function chooseClip(name, recordLocation = true) {
        if (!tracks.has(name)) return;
        clip = name; time = 0; lastTime = null; duration = tracks.get(name).duration;
        layer.play(name);
        entity.anim.speed = 0;
        layer.activeStateCurrentTime = 0;
        $('clip-title').textContent = heroes[selectedHero].clips[name] || clipNames[name] || titleCase(name);
        scrub.max = String(duration);
        document.querySelectorAll('.clip').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.clip === name)));
        if (recordLocation) saveLocation(selectedHero, clip, view);
        timeDisplay(); requestDraw();
    }
    function installButtons() {
        const rank = n => ordinary.includes(n) ? ordinary.indexOf(n) : ordinary.length;
        const names = [...tracks.keys()].sort((a,b) => rank(a)-rank(b) || a.localeCompare(b));
        const buttons = names.map(name => {
            const b = document.createElement('button'); b.type = 'button'; b.className = 'clip'; b.dataset.clip = name;
            const text = document.createElement('span'); text.textContent = heroes[selectedHero].clips[name] || clipNames[name] || titleCase(name);
            b.append(text);
            if (text.textContent.toLowerCase().replaceAll(' ', '_') !== name) {
                const code = document.createElement('span'); code.className = 'code'; code.textContent = name; b.append(code);
            }
            b.title = name + ' · ' + tracks.get(name).duration.toFixed(2) + ' s';
            b.addEventListener('click', () => chooseClip(name)); return b;
        });
        $('clips').replaceChildren(...buttons);
    }
    function model(hero) {
        if (!loaded.has(hero)) {
            const job = new Promise((resolve, reject) => {
                const filename = hero + '.glb';
                const fileUrl = directFile ? URL.createObjectURL(localFiles.get(hero)) : null;
                app.assets.loadFromUrlAndFilename(fileUrl || '../models/' + filename, filename, 'container', (err, asset) => {
                    if (fileUrl) URL.revokeObjectURL(fileUrl);
                    if (err || !asset?.resource) reject(Error('Could not read ' + filename + '. Choose the model from this motion package.'));
                    else resolve(asset.resource);
                });
            });
            loaded.set(hero, job); job.catch(() => loaded.delete(hero));
        }
        return loaded.get(hero);
    }
    async function selectHero(id, wanted) {
        const ticket = ++version; requestedClip = wanted; ready = false; setControls(false);
        if (entity) { entity.destroy(); entity = null; }
        selectedHero = id; clip = ''; time = 0; duration = 0; timeDisplay();
        $('title').textContent = heroes[id].name; $('mesh-info').textContent = ''; $('clips').replaceChildren();
        $('clip-title').textContent = 'Loading clips'; show('Loading ' + heroes[id].name + '…');
        requestDraw();
        if (directFile && !localFiles.has(id)) {
            $('clip-title').textContent = 'Choose a model';
            show('Open models/' + id + '.glb from the extracted motion package.', true);
            return;
        }
        try {
            const resource = await model(id);
            if (ticket !== version) return;
            entity = resource.instantiateRenderEntity({ castShadows: false, receiveShadows: false });
            app.root.addChild(entity); entity.addComponent('anim', { activate: true });
            tracks = new Map();
            for (const a of resource.animations) {
                const t = a.resource;
                if (!(t instanceof pc.AnimTrack) || !Number.isFinite(t.duration) || t.duration <= 0) continue;
                const name = t.name.split('|').at(-1).replace(/\.\d+$/, '').toLowerCase();
                tracks.set(name,t); entity.anim.assignAnimation(name,t,undefined,1,false);
            }
            if (!ordinary.every(n => tracks.has(n))) throw Error('The model is missing a required animation track.');
            const surfaces = entity.findComponents('render').flatMap(r => r.meshInstances);
            const skin = surfaces.filter(m => m.skinInstance); meshCount = skin.length;
            jointCount = new Set(skin.flatMap(m => m.skinInstance.bones)).size;
            if (!jointCount) throw Error('The model has no skinned rig.');
            const bounds = surfaces[0].aabb.clone();
            for (const m of surfaces.slice(1)) bounds.add(m.aabb);
            const height = Math.max(1, bounds.halfExtents.y * 2);
            center.set(0, Math.max(1.10, Math.min(1.55, bounds.center.y + .1)), 0);
            fit = Math.max(5.25, Math.min(8, height*2.48));
            layer = entity.anim.baseLayer; ready = true; installButtons(); setControls(true);
            $('mesh-info').textContent = jointCount + ' joints · ' + tracks.size + ' clips';
            chooseClip(tracks.has(wanted) ? wanted : 'idle');
            updateCamera(); show('');
        } catch (err) {
            if (ticket !== version) return;
            ready = false;
            if (entity) { entity.destroy(); entity = null; }
            if (directFile) { localFiles.delete(id); loaded.delete(id); }
            setControls(false); $('clip-title').textContent = 'Model unavailable'; show(err.message,directFile);
        }
    }
    function orbit(dx,dy) {
        yaw = ((yaw + dx) % 360 + 360) % 360; pitch = Math.max(-36, Math.min(65,pitch + dy)); view = null;
        updateCamera();
    }
    function setZoom(factor) { zoom = Math.max(.38,Math.min(2.1,zoom*factor)); updateCamera(); }
    document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
        view = button.dataset.view; yaw = presets[view]; pitch = 6; zoom = 1; updateCamera(); saveLocation(selectedHero, clip, view);
    }));
    picker.addEventListener('change', () => { const wanted=clip || requestedClip; selectHero(picker.value,wanted); });
    $('model-file').addEventListener('change', e => {
        const file = e.target.files[0]; e.target.value = '';
        if (!file || !directFile) return;
        const expected = selectedHero + '.glb';
        if (file.name.toLowerCase() !== expected) {
            show('This character uses ' + expected + '. Select it from the models folder.',true);
            return;
        }
        localFiles.set(selectedHero,file);
        selectHero(selectedHero,requestedClip);
    });
    play.addEventListener('click',toggle);
    speed.addEventListener('change', () => { lastTime = null; requestDraw(); });
    scrub.addEventListener('input', () => {
        if (!ready) return;
        time = Number(scrub.value); playing = false; lastTime = null; timeDisplay(); requestDraw();
    });
    scene.addEventListener('keydown', e => {
        if (!ready) return;
        const actions = { ArrowLeft: () => orbit(-12,0), ArrowRight: () => orbit(12,0), ArrowUp: () => orbit(0,8), ArrowDown: () => orbit(0,-8),
            '+': () => setZoom(.88), '=': () => setZoom(.88), '-': () => setZoom(1.14), ' ': toggle };
        if (Object.hasOwn(actions,e.key)) { e.preventDefault(); if (e.key !== ' ' || !e.repeat) actions[e.key](); }
    });
    let drag = null;
    scene.addEventListener('pointerdown', e => {
        if (!ready || !e.isPrimary || e.button !== 0) return;
        scene.setPointerCapture(e.pointerId); drag = [e.pointerId,e.clientX,e.clientY]; scene.focus({preventScroll:true});
    });
    scene.addEventListener('pointermove', e => {
        if (!drag || drag[0] !== e.pointerId) return;
        orbit((drag[1]-e.clientX)*.55,(e.clientY-drag[2])*.35); drag[1]=e.clientX; drag[2]=e.clientY;
    });
    scene.addEventListener('lostpointercapture', () => { drag=null; });
    scene.addEventListener('wheel', e => { if (ready) { e.preventDefault(); setZoom(Math.exp(Math.sign(e.deltaY)*.085)); } }, { passive: false });
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) { if (raf) cancelAnimationFrame(raf); raf=0; lastTime=null; }
        else requestDraw();
    });
    // Read-only QA view samples live nodes after GPU submission; no actions are routed through it.
    window.yugaRigInfo = () => ({
        hero: selectedHero, ready, clip, time, duration, playing, yaw, pitch, zoom, rendered, meshCount, jointCount,
        pose: ready ? ['head','wrist.R','foot.L'].flatMap(n => {
            const q = entity.findByName(n)?.getRotation(); return q ? [q.x,q.y,q.z,q.w] : [];
        }) : [],
    });
    scene.addEventListener('webglcontextlost', event => {
        event.preventDefault(); ready = false; setControls(false); show('Rendering paused. Restoring the graphics context…');
    });
    scene.addEventListener('webglcontextrestored', () => location.reload());
    sizeCanvas(); await selectHero(initialHero,url.searchParams.get('clip'));
}
setControls(false);
start().catch(err => { setControls(false); show(err.message || 'WebGL2 could not start. Enable hardware acceleration and reload.'); });
