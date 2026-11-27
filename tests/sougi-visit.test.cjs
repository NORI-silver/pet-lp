// 葬儀・火葬：来館して使える場所が公式サイトで確認できている施設（visit=public）だけに、経路・タクシーの行き先を付ける。
// ほかは理由をカードに書き、経路とタクシーを出さない。確認中の施設（tools/sougi_hold.json）は一覧に出さない。
const fs = require('node:fs');
const assert = require('node:assert/strict');
const D = JSON.parse(fs.readFileSync('tools/sougi_facilities.json', 'utf8')).facilities;
const H = JSON.parse(fs.readFileSync('tools/sougi_hold.json', 'utf8')).facilities;
const TXT = { unconfirmed: '来館できる場所（火葬場・霊園）は、確認した公式サイトのページでは分かりませんでした。', none: '訪問での火葬です。来館して使える施設は、確認した公式サイトのページには書かれていません。', office: '受付の事務所です。' };
const esc = (t) => t.replace(/&/g, '&amp;');
const pages = {};
for (const d of fs.readdirSync('sougi', { withFileTypes: true })) if (d.isDirectory() && fs.existsSync(`sougi/${d.name}/index.html`)) pages[d.name] = fs.readFileSync(`sougi/${d.name}/index.html`, 'utf8');
const all = Object.values(pages).join('\n');
function card(h, id) {
  const i = h.indexOf(`data-fid="${id}"`); assert.ok(i > 0, id + ': card exists');
  const e = h.indexOf('<div class="emg-item', i + 10);
  return h.slice(i, e > 0 ? e : i + 4000);
}
let nPub = 0, nOther = 0, nHold = 0;
for (const f of D) {
  if (!f.visit) continue;
  const b = card(all, f.id);
  if (f.visit === 'public') {
    nPub++; assert.ok(f.addr && f.notice && b.includes(esc(f.notice)), f.name + ': 来訪先の住所と注記をカードに書く');
    assert.ok(/data-route/.test(b) && /emg-taxi/.test(b), f.name + ': 確認済みの来館先には経路とタクシーを出す');
  } else {
    nOther++;
    assert.ok(!/data-route/.test(b), f.name + ': 経路を出さない');
    assert.ok(!/class="emg-taxi[^"]*"[^>]*href="\/\?to=/.test(b), f.name + ': タクシーの行き先を入れない');
    assert.ok(b.includes(esc(f.notice || TXT[f.visit])), f.name + ': 理由をカードに書く');
    assert.ok(b.includes('href="' + f.u.replace(/&/g, '&amp;') + '"') || b.includes('公式サイト'), f.name + ': 公式サイトのリンクは残す');
  }
}
for (const f of H) { nHold++; assert.ok(!all.includes(`data-fid="${f.id}"`), f.name + ': 確認中の施設は一覧に出さない'); }
assert.ok(nPub > 0 && nOther > 0 && nHold > 0, 'public/other/hold are all present');
console.log('sougi-visit ok', nPub, nOther, nHold);
{
  const audited = D.filter((f) => f.visit).length, legacy = D.filter((f) => !f.visit).length;
  assert.equal(D.length + H.length, 287, '287 = 一覧 + 確認中');
  assert.equal(D.length, 286); assert.equal(legacy, 202); assert.equal(audited, 84);
}
