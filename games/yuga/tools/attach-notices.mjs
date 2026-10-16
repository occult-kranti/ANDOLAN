import { readFile, writeFile } from 'node:fs/promises';
const path=process.argv[2] || 'dist/yuga/index.html';
const html=await readFile(path,'utf8');
const notices=(await readFile('games/yuga/THIRD_PARTY_NOTICES.md','utf8'))+'\n\n'+(await readFile('THIRD_PARTY_NOTICES.md','utf8'));
const escaped=notices.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const attribution=`<details id="yuga-notices" style="position:fixed;bottom:4px;right:5px;z-index:2;font:9px sans-serif;color:#bcc6bf;max-width:90vw"><summary style="cursor:pointer">Credits &amp; licenses</summary><pre style="white-space:pre-wrap;max-height:60vh;overflow:auto;padding:20px;background:#10232c;max-width:700px">YUGA: Confluence — character anatomy and rig data from MakeHuman (CC0), original costumes, weapons, animation and synthesized audio. See the asset credits and licenses below.\n\n${escaped}</pre></details>`;
await writeFile(path,html.replace('</body>',`${attribution}</body>`));
console.log('YUGA notices embedded.');
