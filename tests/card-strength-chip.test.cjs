// カードの強み（写真に重ねる／写真なしは文字の札）：否定・休止・条件つき・キーワードだけでは出さない
const fs = require('fs'), assert = require('assert'), path = require('path');
function card(dir, id) {
  const hit = [];
  (function walk(d) { for (const f of fs.readdirSync(d, { withFileTypes: true })) { const q = path.join(d, f.name); if (f.isDirectory()) walk(q); else if (f.name === 'index.html') { const t = fs.readFileSync(q, 'utf8'); const i = t.indexOf('data-fid="' + id + '"'); if (i > 0) { const j = t.indexOf('data-fid="', i + 10); hit.push(t.slice(i, j > 0 ? j : i + 9000)); } } } })(dir);
  return hit[0] || '';
}
const strength = c => ((c.match(/<div class="pc-ov">.*?<\/div>/s) || [''])[0] + ((c.match(/<p class="pc-st">.*?<\/p>/s) || [''])[0]));
const r004 = card('rojin-home', 'R004'); assert.ok(r004, 'R004 が無い'); assert.ok(!/見守りカメラ/.test(strength(r004)), 'R004：設置なしなのに見守りカメラの強み');
const r007 = card('rojin-home', 'R007'); assert.ok(!/見守りカメラ/.test(strength(r007)), 'R007：確認用のカメラを強みにしている');
const r101 = card('rojin-home', 'R101'); assert.ok(/スタッフが24時間常駐（公式サイトの記載）/.test(strength(r101)), 'R101：24時間スタッフの札がない');
assert.ok(!/獣医/.test(strength(r101)), 'R101：獣医の強みを出している'); assert.ok(/見学のみの受付を停止/.test(r101), 'R101：見学停止の文が消えた');
const s336 = card('pet-sitter', 'S336'); assert.ok(/<p class="pc-st">.*動物取扱業：登録ありと公式に記載/s.test(s336), 'S336：写真なしの札がない');
for (const id of ['Rt4013e88']) assert.equal(card('rojin-home', id), '', id + ' が一覧に残っている（出どころが老人ホームの紹介サイト）');
assert.ok(!fs.readFileSync('tools/rojin.json', 'utf8').includes('r-guide.jp/sakoujyu') && !fs.readFileSync('tools/trainers.json', 'utf8').includes('r-guide.jp/sakoujyu') && !fs.readFileSync('tools/grooming.json', 'utf8').includes('r-guide.jp/sakoujyu'), '老人ホームの紹介サイトの出どころが残っている');
const s333 = card('pet-sitter', 'S333'); assert.ok(!/動物取扱業：登録あり/.test(strength(s333)), 'S333：登録証の画像だけの記載を強みにしている');
const h = JSON.parse(fs.readFileSync('tools/hotels.json', 'utf8')).hotels;
for (const id of ['PHt2ed3d70']) { const x = h.find(r => r.id === id); assert.ok(x, id); }
const all = fs.readFileSync('pet-hotel/index.html', 'utf8') + fs.readdirSync('find-data/pet-hotel').map(f => fs.readFileSync('find-data/pet-hotel/' + f, 'utf8')).join('');
assert.ok(!/板橋区内は送迎無料/.test(all), '休止中の送迎が強みとして出ている');
assert.ok(!/<span>大型犬可（\d+kgまで）<\/span>/.test(all), '料金表のkgだけで大型犬可の札が出ている');
assert.ok(!/>[^<]*[⑨☆※■●][^<]*は送迎無料</.test(all), '記号つきのラベル');
console.log('card-strength-chip ok');
