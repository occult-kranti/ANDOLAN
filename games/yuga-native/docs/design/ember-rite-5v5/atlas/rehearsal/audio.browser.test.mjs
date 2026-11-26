/** Play the generated rehearsal. Inspect receipts in its UI and sample its actual Web Audio output. */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { launchChromium } from "../../../../../../yuga-rust/tools/browser-package.mjs";

const html = await readFile(new URL("../rehearsal.html", import.meta.url));
const server = createServer((request, response) => {
  if (request.url.split("?")[0] !== "/rehearsal") { response.writeHead(404).end(); return; }
  response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" }).end(html);
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const address = "http://127.0.0.1:" + server.address().port + "/rehearsal";
const browser = await launchChromium(false);
const errors = [];
const evidence = { browser: browser.version(), rehearsalSha256: createHash("sha256").update(html).digest("hex") };
const scoreNames = ["drone", "low-drum", "hand-drum", "reed", "expiry", "quench"];
const identities = {};
for (const name of scoreNames) {
  const asset = new URL("../../../../../art/yagna-audio/" + name + ".flac", import.meta.url);
  const data = await readFile(asset);
  // FLAC's STREAMINFO includes the MD5 of the source PCM in its first 42 bytes.
  identities[[...data.subarray(0, 42)].join(",")] = name;
}

// The splitter taps the same master output as the speakers. No extra signal enters the game graph.
function installOutputMeter(identities) {
  const connect = AudioNode.prototype.connect;
  const taps = new Map(), starts = [], decoded = new WeakMap(), sources = new WeakMap();
  const decode = BaseAudioContext.prototype.decodeAudioData;
  BaseAudioContext.prototype.decodeAudioData = function(bytes, ...args) {
    const id = identities[new Uint8Array(bytes).subarray(0, 42).join(",")];
    const result = decode.call(this, bytes, ...args);
    if (id) result.then(buffer => decoded.set(buffer, id), () => {});
    return result;
  };
  AudioNode.prototype.connect = function(destination, ...args) {
    const result = connect.call(this, destination, ...args);
    if (destination instanceof AudioDestinationNode) {
      const ctx = this.context;
      if (!taps.has(ctx)) {
        const speakers = ctx.createGain();
        speakers.channelCount = 2;
        speakers.channelCountMode = "explicit";
        speakers.channelInterpretation = "speakers";
        const splitter = ctx.createChannelSplitter(2);
        connect.call(speakers, splitter);
        const channels = [0, 1].map(index => {
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 1024;
          connect.call(splitter, analyser, index);
          return analyser;
        });
        taps.set(ctx, { speakers, channels });
      }
      connect.call(this, taps.get(ctx).speakers);
    }
    return result;
  };
  for (const proto of [OscillatorNode.prototype, AudioBufferSourceNode.prototype]) {
    const start = proto.start, stop = proto.stop;
    proto.start = function(...args) {
      const result = start.apply(this, args);
      const clock = document.querySelector("#clock")?.textContent.match(/^(\d+):(\d+(?:\.\d+)?)$/);
      const record = { asset: decoded.get(this.buffer), duration: this.buffer?.duration ?? 0, loop: this.loop === true,
        start: args[0] || this.context.currentTime, wall: performance.now() / 1000, offset: args[1] || 0, stops: [],
        displayedClock: clock ? Number(clock[1]) * 60 + Number(clock[2]) : null };
      sources.set(this, record);
      starts.push(record);
      return result;
    };
    proto.stop = function(when) {
      const now = this.context.currentTime;
      const result = stop.call(this, when ?? now);
      sources.get(this)?.stops.push({ now, when: when ?? now });
      return result;
    };
  }
  window.emberTestOutput = {
    starts, count: () => taps.size,
    sample(milliseconds) {
      return new Promise(resolve => {
        const samples = [new Float32Array(1024), new Float32Array(1024)];
        const sum = [0, 0], peaks = [0, 0];
        let difference = 0, frames = 0;
        const interval = setInterval(() => {
          for (const [context, { channels }] of taps) {
            if (context.state !== "running") continue;
            channels.forEach((analyser, ch) => analyser.getFloatTimeDomainData(samples[ch]));
            for (let i = 0; i < samples[0].length; i++) {
              for (let ch = 0; ch < 2; ch++) {
                const value = samples[ch][i];
                sum[ch] += value * value;
                peaks[ch] = Math.max(peaks[ch], Math.abs(value));
              }
              difference = Math.max(difference, Math.abs(samples[0][i] - samples[1][i]));
            }
            frames += samples[0].length;
          }
        }, 8);
        setTimeout(() => {
          clearInterval(interval);
          resolve({ rms: sum.map(x => Math.sqrt(x / Math.max(1, frames))), peaks, difference });
        }, milliseconds);
      });
    }
  };
}

async function trackCaptions(page) {
  await page.locator("#sound-caption").evaluate(el => {
    const history = [];
    let previous = "";
    new MutationObserver(() => {
      const type = el.dataset.type, text = el.textContent.trim(), latest = type + "/" + text;
      if (type && text && latest !== previous) history.push({ type, text });
      previous = latest;
    }).observe(el, { childList: true, attributes: true, subtree: true });
    window.emberTestCaptions = history;
  });
}
const events = page => page.evaluate(() => window.emberTestCaptions.map(c => c.type));
async function choose(page, id, value) {
  await page.locator("#" + id).selectOption(value);
  await page.locator("#plan").focus();
}
async function hold(page, key, time) {
  await page.keyboard.down(key);
  await page.clock.runFor(time);
  await page.keyboard.up(key);
  await page.clock.runFor(80);
}
const marker = page => page.locator("#player").getAttribute("transform");
async function playCue(page, type) {
  await page.locator("#practice-cue").selectOption(type);
  await page.locator("#play-source").click();
}
async function sampleOnClick(page, type) {
  await page.locator("#practice-cue").selectOption(type);
  // Arm the sampler before the native click so even a short attack is measured.
  const measurement = page.evaluate(() => window.emberTestOutput.sample(550));
  await page.locator("#play-source").click();
  return measurement;
}

try {
  const drill = await browser.newContext();
  drill.on("page", p => p.on("pageerror", e => errors.push(e.message)));
  await drill.clock.install({ time: new Date("2030-01-01T00:00:00Z") });
  await drill.clock.pauseAt(new Date("2030-01-01T00:00:01Z"));
  const page = await drill.newPage();
  await page.goto(address + "?map=mandala&exercise=explore&listen=1");
  await drill.setOffline(true);
  await trackCaptions(page);
  assert.equal(await page.locator("#captions").isChecked(), true);
  assert.equal(await page.locator("#play-source").isDisabled(), true);
  await choose(page, "start", "a");
  await page.locator("#place-source").click();
  const placed = await page.locator("#practice-marker").getAttribute("transform");
  for (const type of ["footstep", "hanuman_leap", "kali_tandava", "kindle_start"]) {
    await playCue(page, type);
    assert.equal(await page.locator("#sound-caption").getAttribute("data-type"), type);
    await page.clock.runFor(2000);
  }
  await page.locator("#plan").focus();
  await hold(page, "a", 4500);
  const x = Number((await marker(page)).match(/translate\(([-.\d]+)/)[1]);
  assert.ok(x < -20 && x > -25);
  assert.equal(await page.locator("#practice-marker").getAttribute("transform"), placed);
  for (const type of ["footstep", "hanuman_leap"]) {
    const before = (await events(page)).length;
    await playCue(page, type);
    assert.equal((await events(page)).length, before, type + " outside its radius");
  }
  await playCue(page, "kali_tandava");
  assert.equal(await page.locator("#sound-caption").getAttribute("data-type"), "kali_tandava");
  await playCue(page, "kindle_start");
  assert.equal(await page.locator("#sound-caption").getAttribute("data-type"), "kindle_start");
  evidence.fixedSourceTrialMetres = -x;

  await choose(page, "start", "ford");
  await hold(page, "w", 1000);
  assert.match(await page.locator("#sound-caption").textContent(), /water|splash|shallows/i);
  await choose(page, "start", "temple_s");
  const foldBase = (await events(page)).length;
  await hold(page, "e", 650);
  assert.ok((await events(page)).slice(foldBase).includes("fold_start"));
  assert.ok(!(await events(page)).slice(foldBase).includes("fold"));
  await page.clock.runFor(1800);
  await hold(page, "e", 3300);
  assert.equal((await events(page)).slice(foldBase).filter(t => t === "fold").length, 1);

  await choose(page, "mode", "carry");
  await choose(page, "start", "a");
  await page.keyboard.press("g");
  await page.clock.runFor(100);
  assert.equal((await events(page)).at(-1), "drop");
  await hold(page, "e", 90);
  assert.equal((await events(page)).at(-1), "recover");
  const idle = (await events(page)).length;
  assert.ok(await page.locator("#interrupt").isDisabled());
  assert.equal((await events(page)).length, idle);
  await page.clock.runFor(80);
  await page.locator("#plan").focus();
  await page.keyboard.down("e");
  await page.clock.runFor(600);
  await page.locator("#interrupt").click();
  await page.clock.runFor(500);
  await page.keyboard.up("e");
  await page.clock.runFor(1800);
  const interrupted = (await events(page)).slice(idle);
  assert.deepEqual(interrupted, ["kindle_start", "cancel"]);
  await page.locator("#plan").focus();
  await hold(page, "e", 4150);
  assert.ok(await page.locator("#handoff").isVisible());
  assert.ok((await events(page)).includes("kindled"));
  await page.locator("#handoff").click();
  assert.equal(await page.locator("#start").inputValue(), "b");
  assert.match(await page.locator("#clock").textContent(), /0:40/);
  await choose(page, "start", "a");
  await hold(page, "w", 250);
  await hold(page, "e", 3600);
  assert.match(await page.locator("#status").textContent(), /Quenched/);
  assert.ok((await events(page)).includes("quench_start"));
  assert.equal((await events(page)).at(-1), "quenched");
  await page.locator("#reset").click();
  await page.locator("#plan").focus();
  await hold(page, "w", 150);
  await page.clock.runFor(40200);
  assert.equal((await events(page)).at(-1), "burned");
  await choose(page, "mode", "carry");
  await hold(page, "w", 100);
  await page.clock.runFor(100200);
  assert.equal((await events(page)).at(-1), "expired");
  evidence.approachTimeout = { simulatedSeconds: 100, finalClock: await page.locator("#clock").textContent(), receipt: "expired" };
  evidence.observedCueTypes = [...new Set(await events(page))];
  await drill.close();

  const real = await browser.newContext();
  real.on("page", p => p.on("pageerror", e => errors.push(e.message)));
  await real.addInitScript(installOutputMeter, identities);
  const live = await real.newPage();
  await live.goto(address + "?map=mandala&exercise=explore&listen=1");
  await real.setOffline(true);
  await live.locator("#sound-toggle").waitFor();
  assert.deepEqual(await live.evaluate(() => [window.emberTestOutput.count(), window.emberTestOutput.starts.length]), [0, 0]);
  await live.locator("#sound-toggle").focus();
  await live.keyboard.press("Enter");
  await live.waitForFunction(() => window.emberTestOutput.count() > 0);
  await live.locator("#place-source").click();
  await live.locator("#plan").focus();
  await live.keyboard.down("d");
  await live.waitForFunction(() => Number(document.querySelector("#player").getAttribute("transform").match(/translate\(([-.\d]+)/)[1]) >= 2);
  await live.keyboard.up("d");
  await live.locator("#turn-left").click();
  await live.evaluate(() => window.emberTestOutput.sample(500));
  const left = await sampleOnClick(live, "kali_tandava");
  await live.locator("#turn-right").click();
  await live.locator("#turn-right").click();
  const right = await sampleOnClick(live, "kali_tandava");
  assert.ok(left.rms[0] > left.rms[1] * 1.4, JSON.stringify(left));
  assert.ok(right.rms[1] > right.rms[0] * 1.4, JSON.stringify(right));
  await live.locator("#mix-settings > summary").click();
  await live.locator("#mono").check();
  await live.evaluate(() => window.emberTestOutput.sample(150));
  const mono = await sampleOnClick(live, "kali_tandava");
  assert.ok(mono.peaks[0] > .0001 && mono.difference < .0001, JSON.stringify(mono));
  evidence.output = { left, right, mono };
  await live.locator("#captions").uncheck();
  const noCaption = await sampleOnClick(live, "hanuman_leap");
  assert.ok(Math.max(...noCaption.peaks) > .0001);
  assert.equal(await live.locator("#sound-caption").textContent(), "");
  await live.locator("#captions").check();
  await live.getByRole("button", { name: "Mute sound" }).click();
  await live.evaluate(() => window.emberTestOutput.sample(150));
  const masterMute = await sampleOnClick(live, "kindle_start");
  assert.ok(Math.max(...masterMute.peaks) < .0001);
  assert.equal(await live.locator("#sound-caption").getAttribute("data-type"), "kindle_start");
  await live.getByRole("button", { name: "Enable sound" }).click();
  await live.locator("#effects-volume").focus();
  await live.keyboard.press("Home");
  const quiet = await sampleOnClick(live, "hanuman_leap");
  assert.ok(Math.max(...quiet.peaks) < .0001, JSON.stringify(quiet));
  assert.equal(await live.locator("#sound-caption").getAttribute("data-type"), "hanuman_leap");
  await live.locator("#restore-mix").click();
  assert.equal(await live.locator("#mono").isChecked(), false);
  assert.equal(await live.locator("#effects-volume").inputValue(), "100");
  await live.getByRole("button", { name: "Enable sound" }).click();
  await choose(live, "mode", "carry");
  await choose(live, "start", "a");
  const windupStart = await live.evaluate(() => window.emberTestOutput.starts.length);
  await live.keyboard.down("e");
  await live.waitForFunction(i => window.emberTestOutput.starts.length > i, windupStart);
  await live.keyboard.up("e");
  await live.waitForFunction(i => window.emberTestOutput.starts[i].stops.length > 0, windupStart);
  const windup = await live.evaluate(i => window.emberTestOutput.starts[i], windupStart);
  assert.ok(windup.stops[0].when < windup.start + windup.duration);
  assert.ok(windup.stops[0].when - windup.stops[0].now <= .025);
  evidence.cancelFadeMilliseconds = Math.round((windup.stops[0].when - windup.stops[0].now) * 1000);
  await choose(live, "mode", "retake");
  await live.keyboard.down("w");
  await live.waitForFunction(() => window.emberTestOutput.starts.some(s => Math.abs(s.duration - 10) < .001));
  await live.keyboard.up("w");
  const music = await live.evaluate(() => window.emberTestOutput.sample(350));
  assert.ok(Math.max(...music.peaks) > .001);
  await live.locator("#music-volume").focus();
  await live.keyboard.press("Home");
  await live.evaluate(() => window.emberTestOutput.sample(150));
  const musicMuted = await live.evaluate(() => window.emberTestOutput.sample(250));
  assert.ok(Math.max(...musicMuted.peaks) < .0001);
  await live.keyboard.press("End");
  await live.waitForFunction(() => window.emberTestOutput.starts.some(s => s.asset === "drone" && s.offset > .4));
  const other = await real.newPage();
  for (const tab of [live, other]) {
    const cdp = await real.newCDPSession(tab);
    await cdp.send("Emulation.setFocusEmulationEnabled", { enabled: false });
  }
  await live.bringToFront();
  await other.bringToFront();
  await live.waitForFunction(() => !document.hasFocus() && document.querySelector("#pause").textContent === "Resume");
  await live.bringToFront();
  await live.evaluate(() => window.emberTestOutput.sample(150));
  const muted = await live.evaluate(() => window.emberTestOutput.sample(350));
  assert.ok(Math.max(...muted.peaks) < .0001, JSON.stringify(muted));
  evidence.burnPeak = Math.max(...music.peaks);
  evidence.afterTabReturnPeak = Math.max(...muted.peaks);
  await other.close();
  await live.locator("#reset").click();
  const from = await live.evaluate(() => window.emberTestOutput.starts.length);
  await live.locator("#plan").focus();
  await live.keyboard.down("w");
  await live.waitForFunction(from => window.emberTestOutput.starts.slice(from).some(s => s.asset === "drone"), from);
  await live.keyboard.up("w");
  for (const name of ["low-drum", "hand-drum", "reed"]) {
    await live.waitForFunction(([from, name]) => window.emberTestOutput.starts.slice(from).some(s => s.asset === name),
      [from, name], { timeout: 16000 });
  }
  await live.locator("#music-volume").focus();
  await live.waitForFunction(() => Number(document.querySelector("#clock").textContent.split(":")[1]) <= 7.5);
  await live.keyboard.press("Home");
  await live.waitForFunction(() => Number(document.querySelector("#clock").textContent.split(":")[1]) <= 7.2);
  const late = await live.evaluate(() => window.emberTestOutput.starts.length);
  await live.keyboard.press("End");
  await live.waitForFunction(i => window.emberTestOutput.starts.slice(i).filter(s => s.loop).length >= 4, late);
  const lateSources = await live.evaluate(i => window.emberTestOutput.starts.slice(i).filter(s => s.loop).slice(0, 4), late);
  assert.deepEqual(lateSources.map(s => s.asset), ["drone", "low-drum", "hand-drum", "reed"]);
  const phase = lateSources[0].offset;
  for (const source of lateSources) {
    assert.ok(Math.abs(source.offset - phase) < .025);
    assert.ok(Math.abs(source.offset - (40 - source.displayedClock) % 10) < .35);
  }
  evidence.lateMusicRestore = { clockSecondsRemaining: lateSources[0].displayedClock,
    offsetsSeconds: Object.fromEntries(lateSources.map(s => [s.asset, Number(s.offset.toFixed(3))])) };
  await live.waitForFunction(from => window.emberTestOutput.starts.slice(from).some(s => s.asset === "expiry"), from);
  assert.match(await live.locator("#status").textContent(), /fire completed/i);
  const score = await live.evaluate(from => window.emberTestOutput.starts.slice(from).filter(s => s.asset), from);
  const stageNames = ["drone", "low-drum", "hand-drum", "reed", "expiry"];
  const stage = name => score.find(s => s.asset === name);
  for (const [i, name] of stageNames.entries()) {
    // The real audio clock may run ahead of an overloaded renderer. The displayed fire clock owns layer eligibility.
    assert.ok(Math.abs(40 - stage(name).displayedClock - i * 10) < .4, JSON.stringify(score));
  }
  assert.equal(score.filter(s => s.asset === "expiry").length, 1);
  assert.equal(score.filter(s => s.asset === "quench").length, 0);
  evidence.burnOnsetsSeconds = Object.fromEntries(stageNames.map(name => [name, {
    audioClock: Number((stage(name).start - score[0].start).toFixed(3)),
    wallClock: Number((stage(name).wall - score[0].wall).toFixed(3)),
    displayedSecondsRemaining: stage(name).displayedClock
  }]));
  await live.locator("#reset").click();
  await choose(live, "start", "a");
  await live.keyboard.down("w");
  await live.waitForFunction(() => document.querySelector("#interact").textContent.includes("Quench"));
  await live.keyboard.up("w");
  await live.keyboard.down("e");
  await live.waitForFunction(() => window.emberTestOutput.starts.some(s => s.asset === "quench"));
  await live.keyboard.up("e");
  assert.match(await live.locator("#status").textContent(), /Quenched/);
  await real.close();

  const mobile = await browser.newContext({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });
  mobile.on("page", p => p.on("pageerror", e => errors.push(e.message)));
  await mobile.addInitScript(() => {
    Object.defineProperty(window, "AudioContext", { value: undefined });
    Object.defineProperty(window, "webkitAudioContext", { value: undefined });
  });
  const touch = await mobile.newPage();
  await touch.goto(address + "?map=ayodhya&exercise=explore&listen=1");
  await touch.locator("#sound-toggle").tap();
  assert.match(await touch.locator("#sound-status").textContent(), /unavailable|unsupported/i);
  await touch.locator("#place-source").tap();
  await touch.locator("#practice-cue").selectOption("kali_tandava");
  await touch.locator("#play-source").tap();
  assert.equal(await touch.locator("#sound-caption").getAttribute("data-type"), "kali_tandava");
  assert.ok(await touch.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await mobile.close();

  const embedded = await browser.newContext({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });
  await embedded.addInitScript(installOutputMeter, identities);
  const host = await embedded.newPage();
  host.on("pageerror", e => errors.push(e.message));
  await host.setContent('<iframe id="sheet" sandbox="allow-scripts" title="Ember Rite rehearsal" style="width:350px;height:760px"></iframe>');
  await host.evaluate(() => {
    const sheet = document.querySelector("#sheet");
    window.addEventListener("message", event => {
      if (event.source === sheet.contentWindow && event.data?.type === "yuga.ember.audio.read")
        sheet.contentWindow.postMessage({ type: "yuga.ember.audio.restore", mix: { enabled: true, music: .37, mono: true } }, "*");
    });
  });
  await host.locator("#sheet").evaluate((el, html) => { el.srcdoc = html; }, html.toString());
  const frame = host.frameLocator("#sheet");
  await frame.getByRole("button", { name: "Resume sound" }).waitFor();
  assert.equal(await frame.locator("#master-volume").evaluate(() => window.origin), "null");
  assert.equal(await frame.locator("#music-volume").inputValue(), "37");
  assert.ok(await frame.locator("#mono").isChecked());
  await frame.locator("#listening-lab > summary").tap();
  await frame.locator("#place-source").tap();
  await frame.locator("#play-source").tap();
  assert.equal(await frame.locator("#practice-caption").textContent(), await frame.locator("#sound-caption").textContent());
  const frameOutput = () => frame.locator("#plan").evaluate(() => [window.emberTestOutput.count(), window.emberTestOutput.starts.length]);
  assert.deepEqual(await frameOutput(), [0, 0], "Stored sound preference requires a gesture in this frame");
  await frame.locator("#sound-toggle").tap();
  await frame.locator("#practice-cue").selectOption("kali_tandava");
  await frame.locator("#play-source").tap();
  const [contexts, voices] = await frameOutput();
  assert.equal(contexts, 1);
  assert.ok(voices > 0);
  await embedded.close();
  assert.deepEqual(errors, []);
  console.log(JSON.stringify(evidence, null, 2));
} finally {
  await browser.close();
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
}
