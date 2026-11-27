// 葬儀・火葬は施設の正確な場所を確認できていない（市区町村の中心で代用していた）ので、
// 「現在地から○km以内」の絞り込みを出さず、理由を表示する。ほかの種類の絞り込みは変えない。
const fs = require('node:fs');
const assert = require('node:assert/strict');
const NOTE = '施設の正確な場所は確認できていないため、近さでは絞れません。';
const sougi = ['sougi/index.html', ...fs.readdirSync('sougi', { withFileTypes: true }).filter(d => d.isDirectory()).map(d => `sougi/${d.name}/index.html`).filter(f => fs.existsSync(f))];
assert.ok(sougi.length >= 47, '葬儀・火葬の一覧ページが揃っている');
for (const f of sougi) {
  const h = fs.readFileSync(f, 'utf8');
  if (!h.includes('class="ux-find"')) continue;
  assert.ok(!h.includes('id="ffNear"'), f + ': 現在地からの距離の選択肢を出さない');
  assert.ok(!h.includes('<option value="10">10km以内</option>'), f + ': km以内の選択肢がない');
  assert.ok(h.includes(NOTE), f + ': 理由を表示する');
}
for (const f of ['pet-hotel/tokyo/index.html', 'rojin-home/tokyo/index.html', 'pet-sitter/tokyo/index.html']) {
  const h = fs.readFileSync(f, 'utf8');
  assert.ok(h.includes('id="ffNear"') && h.includes('10km以内'), f + ': ほかの種類は距離の絞り込みを残す');
  assert.ok(!h.includes(NOTE), f + ': 葬儀の注意書きを出さない');
}
console.log('sougi-no-radius ok');
