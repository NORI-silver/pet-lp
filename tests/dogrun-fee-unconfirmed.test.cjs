// 公式ページに料金が書かれていないドッグランを「無料」にしない（不在は無料の根拠にならない）
const fs = require('fs'), assert = require('assert');
const d = JSON.parse(fs.readFileSync('tools/dogrun.json', 'utf8'));
const L = Array.isArray(d) ? d : Object.values(d).find(Array.isArray);
for (const r of L) if (r.fee && /記載なし/.test(r.fee)) assert.ok(r.fee.startsWith('未確認'), r.id + ': 記載なしを無料にしている');
const html = fs.readFileSync('dogrun/saitama/index.html', 'utf8');
const i = html.indexOf('id="D174"'); assert.ok(i > 0);
const card = html.slice(i, html.indexOf('id="D', i + 10) > 0 ? html.indexOf('id="D', i + 10) : i + 6000);
const txt = card.replace(/<[^>]+>/g, ' ');
assert.ok(/料金\s+未確認/.test(txt), 'D174 の料金が未確認になっていない');
assert.ok(!/料金\s+無料/.test(txt), 'D174 が無料と読める');
console.log('dogrun-fee-unconfirmed ok');
