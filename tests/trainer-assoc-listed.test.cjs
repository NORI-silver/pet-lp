// 協会の一覧に名前あり：公式の一覧ページで確認できた施設だけ、日付つきの文にする（会員・認定の確認とは書かない）
const fs = require('fs'), assert = require('assert');
const d = JSON.parse(fs.readFileSync('tools/trainers.json', 'utf8')).trainers;
const lst = d.filter(t => t.assoc_listed);
assert.ok(lst.length >= 20, 'assoc_listed が少なすぎる: ' + lst.length);
for (const t of lst) {
  assert.ok(t.assoc, t.id + ': assoc が無いのに assoc_listed がある');
  assert.equal(t.assoc_listed.checked, '2026-11-27', t.id);
  for (const k of Object.keys(t.assoc_listed)) {
    if (k === 'checked') continue;
    assert.ok(t.assoc.split('・').includes(k), t.id + ': ' + k + ' が assoc に無い');
    assert.ok(/^https:\/\/(japdt\.com\/|www\.jaha\.or\.jp\/owners\/dog-class\/)/.test(t.assoc_listed[k]), t.id + ': 出どころのURLが公式の一覧ではない');
  }
}
const html = fs.readFileSync('dog-trainer/tokyo/index.html', 'utf8');
assert.ok(/一覧に掲載（2026-11-27確認。一覧に載っているだけで、資格や認定の確認ではありません）/.test(html), '東京のページに日付つきの文がない');
assert.ok(!/協会所属|認定済み|会員確認済み/.test(html), '会員・認定と読める言い方がある');
console.log('trainer-assoc-listed ok', lst.length);
