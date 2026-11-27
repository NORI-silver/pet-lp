// 葬儀・火葬：来館して使える場所が公式サイトで確認できている施設（visit=public）だけに、経路・タクシーの行き先を付ける。
// ほかは理由をカードに書き、経路とタクシーを出さない。確認中の施設（tools/sougi_hold.json）は一覧に出さない。
const fs = require('node:fs');
const assert = require('node:assert/strict');
const D = JSON.parse(fs.readFileSync('tools/sougi_facilities.json', 'utf8')).facilities;
const H = JSON.parse(fs.readFileSync('tools/sougi_hold.json', 'utf8')).facilities;
const TXT = { unconfirmed: '来館できる場所（火葬場・霊園）は、このカードでは確認できていません。', none: '訪問火葬対応：ご自宅などへ火葬車が来て火葬します。来館して使える施設は、このカードでは確認できていません。', office: '受付の事務所です。' };
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
assert.ok(nPub > 0 && nOther > 0, 'public/other are both present');
console.log('sougi-visit ok', nPub, nOther, nHold);
{
  const audited = D.filter((f) => f.visit).length, legacy = D.filter((f) => !f.visit).length;
  assert.equal(D.length + H.length, 287, '287 = 一覧 + 確認中');
  assert.equal(D.length, 287); assert.equal(legacy, 202); assert.equal(audited, 85);
}
{
  // お迎えだけの施設は「お迎え対応」だけ、訪問火葬だけの施設は「訪問火葬対応」だけを、カードに書く（一方を他方と読ませない）
  let nP = 0, nV = 0;
  for (const f of D) {
    if (!f.visit) continue;
    const sv = f.services || [], b = card(all, f.id);
    const pick = sv.includes('お迎え'), vis = sv.includes('訪問火葬');
    if (pick && !vis) { nP++; assert.ok(b.includes('お迎え対応') && !b.includes('訪問火葬対応'), f.name + ': お迎えだけ'); }
    if (vis && !pick) { nV++; assert.ok(b.includes('訪問火葬対応') && !b.includes('お迎え対応'), f.name + ': 訪問火葬だけ'); }
  }
  assert.ok(nP > 0 && nV > 0, 'pickup-only and visiting-only both present');
  console.log('sougi-visit pickup/visiting ok', nP, nV);
}

{
  // 火葬車を霊園に置いて行う火葬は、自宅へ来る訪問火葬とは別。
  const id = 'S2bdcf2', location = '千葉県木更津市中里2-9-15';
  const official = 'https://mp-gardenkisaragi.com/petkasou/';
  assert.equal(D.filter((f) => f.id === id).length, 1);
  assert.ok(!H.some((f) => f.id === id));
  const filterData = JSON.parse(fs.readFileSync('find-data/sougi/chiba.json', 'utf8'));
  const cityCards = filterData.groups.find(([city]) => city === '木更津市')[1];
  const filtered = cityCards.find((html) => html.includes(`data-fid="${id}"`));
  assert.ok(filtered, '木更津市の絞り込みでも出る');
  for (const html of [card(pages.chiba, id), filtered]) {
    assert.ok(html.includes(official));
    assert.ok(html.includes(`data-to="${location}"`));
    assert.ok(html.includes('霊園駐車場'));
    assert.ok(html.includes('17,100円'));
    assert.ok(html.includes('data-yen="17100"'));
    assert.match(html, /data-no="[^"]*\bbig\b/);
    const tags = html.match(/data-tags="([^"]*)"/)?.[1]?.split('|') || [];
    for (const key of ['訪問火葬','お迎え','お迎えまたは訪問火葬','立ち会い','合同火葬','大型犬','p15']) assert.ok(!tags.includes(key), key);
  }
  assert.ok(!card(pages.chiba, 'S36f47a').includes('data-route'));
  assert.ok(pages.chiba.includes('href="#chiba-cremation-cost"') && pages.chiba.includes('id="chiba-cremation-cost"'));
}
