import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

export const digest = bytes => createHash('sha256').update(bytes).digest('hex');

export async function packageUnderTest(filename) {
  const html = path.resolve(filename);
  const archive = path.join(path.dirname(html), 'yuga-rust-confluence.zip');
  const bytes = execFileSync('unzip', ['-p', archive, 'yuga-rust.html'], {maxBuffer: 128 * 1024 * 1024});
  assert.ok(bytes.equals(await readFile(html)), 'ZIP member matches the standalone HTML byte-for-byte');
  return {html, bytes, html_sha256: digest(bytes), zip_sha256: digest(await readFile(archive))};
}

export function launchChromium(graphics = true) {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  const args = ['--no-sandbox', '--disable-dev-shm-usage'];
  if (graphics) args.push('--enable-unsafe-swiftshader', '--use-angle=swiftshader');
  else args.push('--disable-webgl');
  return chromium.launch({headless: true, executablePath, args});
}

export async function openOffline(context, game, onDocument = () => {}) {
  const local = await context.newPage();
  try {
    await local.goto(pathToFileURL(game.html).href, {waitUntil: 'domcontentloaded', timeout: 120_000});
    return {tab: local, entry: 'file'};
  } catch (error) {
    if (!String(error).includes('ERR_BLOCKED_BY_ADMINISTRATOR')) throw error;
    await local.close();
  }
  // Hosts with an enterprise file:// restriction can still open the real ZIP via loopback.
  const tab = await context.newPage();
  const server = createServer((request, response) => {
    if (request.method !== 'GET' || request.url !== '/yuga-rust.html') {
      response.writeHead(404).end();
      return;
    }
    response.writeHead(200, {'Content-Type': 'text/html; charset=utf-8', 'Content-Length': game.bytes.length});
    response.end(game.bytes);
  });
  await new Promise((resolve, reject) => server.once('error', reject).listen(0, '127.0.0.1', resolve));
  const url = 'http://127.0.0.1:' + server.address().port + '/yuga-rust.html';
  onDocument(url);
  let served = false;
  try {
    await context.route(/^https?:\/\//, route => {
      if (!served && route.request().isNavigationRequest() && route.request().url() === url) {
        served = true;
        return route.continue();
      }
      return route.abort();
    });
    await context.setOffline(false);
    await tab.goto(url, {waitUntil: 'domcontentloaded', timeout: 120_000});
    await context.setOffline(true);
    assert.ok(served && await tab.evaluate(() => !navigator.onLine));
    return {tab, entry: 'loopback HTTP, ZIP member, then offline (file URL blocked by managed Chromium)'};
  } finally {
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
}
