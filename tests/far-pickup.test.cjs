// 県の外へのお迎え（Nori 2026-11-14「ほんとにそこを乗車位置にしたときに迎えに行ける会社が一つもないなら消して」）
// 公式サイトに「山口県内へお迎えに上がります」と書いている福岡の会社は、山口県のお迎えでも候補に出る。料金の打ち止めは30kmまで
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const happy = ctx.DISPLAY_COMPANIES.find(c => c.id === 'Df31960d');
assert.deepEqual([...happy.far], ['山口']);
const shimonoseki = {lat:33.958, lng:130.941}, yamaguchi = {lat:34.178, lng:131.474}, hiroshima = {lat:34.396, lng:132.459};
assert.ok(ctx.displayServes_(happy, '福岡', null));
assert.ok(ctx.displayServes_(happy, '山口', shimonoseki));
assert.ok(ctx.displayServes_(happy, '山口', yamaguchi), '山口市（お店から約150km）も出す');
assert.ok(!ctx.displayServes_(happy, '広島', hiroshima), '書いていない県には出さない');
assert.ok(!ctx.displayServes_(happy, '熊本', null));
// 選択欄：山口は「（県外の会社のみ）」、沖縄は消す
const html = fs.readFileSync('index.html','utf8');
const far = JSON.parse(html.match(/var FAR_PREFS = (\[[^\]]*\]);/)[1]);
const local = JSON.parse(html.match(/var AREA_PREFS = (\[[^\]]*\]);/)[1]);
assert.ok(far.includes('山口') && far.includes('鹿児島'));
assert.ok(!far.includes('沖縄') && !local.includes('沖縄'));
assert.ok(far.every(p => !local.includes(p)));
console.log('far-pickup ok');
