// 利用者の指示（2026-11-27）：「口コミ」のボタンから Google マップへ飛ばさない。経路（maps/dir）や「地図」のリンクは別なので残す。
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const A = /<a\b[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/g;
let pages = 0, bad = [];
function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.name === '.git' || e.name === 'node_modules') continue;
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p);
    else if (/\.(html|json)$/.test(e.name)) {
      const t = fs.readFileSync(p, 'utf8');
      if (!t.includes('google.com/maps')) continue;
      pages++;
      const u = t.replace(/\\u0026/g, '&').replace(/\\"/g, '"').replace(/\\\//g, '/');
      for (const m of u.matchAll(A)) {
        const text = m[2].replace(/<[^>]+>/g, '');
        if (/google\.com\/maps/.test(m[1]) && /口コミ/.test(text)) bad.push(p + ': ' + text.slice(0, 30));
      }
    }
  }
}
walk('.');
assert.equal(bad.length, 0, 'マップへ飛ぶ口コミのリンクが残っている: ' + bad.slice(0, 5).join(' | '));
for (const f of ['hosp.js', 'tools/hosp_find.js', 'tools/faccard.py', 'tools/gen_dogrun.py']) {
  const s = fs.readFileSync(f, 'utf8');
  assert.ok(!/Google Mapsの口コミ/.test(s), f + ': マップへ飛ぶ口コミのボタンの文を持たない');
}
assert.ok(!/data-k="review"/.test(fs.readFileSync('hosp.js', 'utf8')), 'hosp.js: 口コミのボタンを作らない');
console.log('no-maps-review ok', pages);
