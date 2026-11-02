// ふつうのタクシー（ご案内だけ）：データと運賃の計算（Nori 2026-11-02「公開」）
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync('index.html', 'utf8');
assert.match(html, /var REGULAR_TAXI_ON = (true|false);/);
const data = JSON.parse(html.match(/\/\*TAXIS\*\/var TAXIS = (.*?);\/\*\/TAXIS\*\//)[1]);
const src = JSON.parse(fs.readFileSync('tools/regular_taxis.json', 'utf8'));
assert.equal(data.taxis.length, src.taxis.length, 'gen_areas.py で書き込まれている');
for (const t of src.taxis) {
  assert.ok(t.rule_src.startsWith('https://') && t.fare_src.startsWith('https://'), t.id + ' 出典あり');
  assert.ok(!/\d{2,4}-\d{2,4}-\d{3,4}/.test(JSON.stringify(t)), t.id + ' 電話番号を入れない');
  assert.ok(t.cities.length && t.fare.add_m > 0, t.id);
}
const fn = html.match(/function taxiMeter\(f, km, night\)\{[\s\S]*?\n  \}/)[0];
const ctx = vm.createContext({ Math });
vm.runInContext(fn, ctx);
const daiwa = src.taxis.find(t => t.id === 'daiwa-tokyo').fare;
// 東京23区 5km：500円＋ceil(4000/232)=18×100円＝2,300円、迎車500円＋予約500円＝3,300円
assert.equal(ctx.taxiMeter(daiwa, 5, false), 3300);
assert.equal(ctx.taxiMeter(daiwa, 1, false), 1500, '初乗りの距離まで');
assert.equal(ctx.taxiMeter(daiwa, 5, true), 2300 * 1.2 + 1000, '夜は運賃だけ2割増');
// どの都道府県のページにも同じものが入っている
assert.ok(fs.readFileSync('app.js', 'utf8').includes('"id": "mk-nagoya"'), '地域ページが読む app.js にも入っている');
for (const f of ['tokyo/index.html', 'area/aichi/index.html']) assert.ok(fs.readFileSync(f, 'utf8').includes('id="taxiBox"'), f);
console.log('regular taxi ok');
