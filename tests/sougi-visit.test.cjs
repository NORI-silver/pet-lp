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
let nPub = 0, nOther = 0, nHold = 0, listed = 0;
for (const f of D) {
  if (!f.visit) continue;
  assert.ok(all.includes(`data-fid="${f.id}"`), f.name + ': 一覧に出ている');
  listed++;
  const b = card(all, f.id);
  if (f.visit === 'public') {
    nPub++; assert.ok(f.addr && f.notice && b.includes(esc(f.notice)), f.name + ': 来訪先の住所と注記をカードに書く');
    assert.ok(/data-route/.test(b) && /emg-taxi/.test(b), f.name + ': 確認済みの来館先には経路とタクシーを出す');
  } else {
    nOther++;
    assert.ok(!/data-route/.test(b), f.name + ': 経路を出さない');
    assert.ok(!/ data-to="/.test(b.slice(0, b.indexOf('>') + 1)), f.name + ': data-to を持たない');
    assert.ok(!/href="\/\?to=/.test(b), f.name + ': タクシーの行き先を入れない（href で確認）');
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
  assert.equal(legacy, 0, '来館先の状態が未設定の施設はない（未確認は visit=unconfirmed で経路を出さない）');
  assert.equal(D.length + H.length, 375, '375 = 一覧 + 確認中（287件に、公式サイトで名前・市区町村・できることを確認した88件を足した。来館先は未確認のまま）');
  assert.equal(D.length, 375); assert.equal(audited, 375);
  const ADD88 = ["S5a9c04", "S31bdd1", "S61972f", "S700006", "S914b08", "S0e1fbc", "Sc36d29", "S506c06", "Sb8d6d3", "Sd62a6b", "Sfe40ab", "S945602", "S83ff41", "Se12f76", "S9442d8", "Saa5452", "S72450c", "S988c93", "S4687c1", "S2cfc55", "S26181b", "S935237", "S6dbcac", "Scd87c1", "S66beae", "S166aad", "Sf5bb9b", "Sb2450b", "Sba17be", "S2525e3", "S1ba768", "Sbd4890", "Se163c2", "S861624", "S5427f2", "S91cdeb", "S0ab20a", "S1ec0ba", "S95d0f0", "S3179d0", "Sa4ba53", "Sc5525a", "Sf6b48d", "Sea883a", "S91ce9a", "Sdeb88b", "S62d2dd", "S4ba613", "S8d6f0d", "Sf41910", "Sbf2397", "S744f45", "S086402", "Sff6ad1", "Sa91572", "S8a446c", "S8fe9c9", "S235bde", "S709052", "S756e5c", "Sbdae50", "S273f50", "Sc77f93", "Sc0a54f", "S57bb52", "Scd13d6", "Sda8df6", "S4bac65", "Sd695c4", "S9136f2", "Saabf58", "S0c8a7c", "S89c6d8", "Sf45ce2", "S633846", "S992687", "S0d4f89", "Sf74c92", "S52503b", "Sf9d876", "S0780b0", "S908c69", "S6fd14b", "S89cb0a", "S6e8535", "S2bbcbc", "S2e65ad", "S5db1e2"];
  for (const id of ADD88) { const f = D.find((x) => x.id === id); assert.ok(f, id + ': 足した88件に入っている'); assert.equal(f.visit, 'unconfirmed', id + ': 足した施設は来館先を未確認のまま'); assert.ok(!f.addr, id + ': 住所は載せない'); }
  assert.equal(ADD88.length, 88); const PUB = D.filter((f) => f.visit === 'public').map((f) => f.id);
  assert.equal(PUB.length, 47);
  const PREV31 = ["S04bc24", "S0c4f9d", "S11d757", "S14b5f5", "S14d646", "S1e7daf", "S2bdcf2", "S38d591", "S3a0faa", "S5493f2", "S54ff62", "S5ba910", "S66990f", "S6acf91", "S751c9a", "S7f4bb0", "S8ed284", "S9459f3", "S9c2cde", "Sc0ed0c", "Sccfc1e", "Scf95e2", "Sd0ac1f", "Sd95a31", "Sddda98", "Se247dc", "Se459ec", "Se4eee5", "Seb57a2", "Seb65c7", "Sef79f6"], RESTORED16 = ["S0a98c9", "S1b8c6d", "S2358f8", "S31d6ce", "S50a5de", "S5818be", "S7755d5", "S822672", "S934111", "S9b3bec", "Sa2a9dd", "Sa2fae7", "Sb22bec", "Sd0edb1", "Sece5b2", "Sfd6400"];
  for (const id of PREV31) assert.ok(PUB.includes(id), id + ': 以前から確認済みの31件は変わらない');
  for (const id of RESTORED16) assert.ok(PUB.includes(id), id + ': 住所と来館先を確認した16件');
  for (const id of ['S08b96f', 'Sbd2aea']) assert.ok(!PUB.includes(id), id + ': 確認が終わるまで経路を出さない');
}
{
  // お迎えだけの施設は「お迎え対応」だけ、訪問火葬だけの施設は「訪問火葬対応」だけを、カードに書く（一方を他方と読ませない）
  let nP = 0, nV = 0;
  for (const f of D) {
    if (!f.visit) continue;
    if (!all.includes(`data-fid="${f.id}"`)) continue;
    if (!f.notice && f.visit === 'unconfirmed') continue; // 未監査の旧データ（来館先は未確認で経路なし）。お迎え/訪問の区別は監査後に書く
    const sv = f.services || [], b = card(all, f.id);
    const pick = sv.includes('お迎え'), vis = sv.includes('訪問火葬');
    if (pick && !vis) { nP++; assert.ok(b.includes('お迎え対応') && !b.includes('訪問火葬対応'), f.name + ': お迎えだけ'); }
    if (vis && !pick) { nV++; assert.ok(b.includes('訪問火葬対応') && !b.includes('お迎え対応'), f.name + ': 訪問火葬だけ'); }
  }
  assert.equal(nP, 27); assert.equal(nV, 34); // 監査済み（お迎えは復元12件を足して15→27）のの内訳（未監査の旧データはこの行を持たない）
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
{
  // 全287件：お迎え・訪問火葬のサービスは、データにある限りカードのタグに残る（来館先の安全対応でサービスを消さない）
  let n = 0;
  for (const f of D) {
    const sv = f.services || [];
    if (!(sv.includes('お迎え') || sv.includes('訪問火葬'))) continue;
    const b = card(all, f.id); n++;
    assert.ok(b.includes('お迎えまたは訪問火葬'), f.name + ': サービスのタグが残る');
  }
  assert.equal(listed, 375, '375件すべてが一覧に出ている');
  assert.ok(n > 100, 'お迎え/訪問の施設が多数ある: ' + n);
}
{
  // 施設ごとの詳しいページ：来館先が確認できていない施設には、カードと同じ注記を出し、施設までの移動を前提にした文と行き先を入れない
  const fs2 = require('fs'), path2 = require('path');
  const byId = Object.fromEntries(D.map((f) => [f.id, f]));
  let n = 0, nNon = 0;
  for (const pf of fs2.readdirSync(path2.join('.', 'sougi'), { withFileTypes: true })) {
    if (!pf.isDirectory()) continue;
    for (const d of fs2.readdirSync(path2.join('.', 'sougi', pf.name), { withFileTypes: true })) {
      if (!d.isDirectory() || !/^s[0-9a-f]{6}$/.test(d.name)) continue;
      const html = fs2.readFileSync(path2.join('.', 'sougi', pf.name, d.name, 'index.html'), 'utf8');
      const f = D.find((x) => x.id.toLowerCase() === d.name);
      assert.ok(f, d.name + ': データにある');
      n++;
      const m = /<div class="emg-item emg-co[^"]*sg-pv[^"]*"[^>]*>/.exec(html);
      assert.ok(m, f.name + ': 詳しいページにカードがある');
      if (f.visit !== 'public') {
        nNon++;
        assert.ok(!/ data-to="/.test(m[0]), f.name + ': 詳しいページのカードに行き先を入れない');
        assert.ok(!/href="\/\?to=/.test(html) && !/data-route/.test(html), f.name + ': 詳しいページに経路・タクシーの行き先を入れない');
        assert.ok(html.includes(esc(f.notice || TXT[f.visit])), f.name + ': 詳しいページに来館先未確認の注記');
        assert.ok(!html.includes('家の前から施設の前まで'), f.name + ': 施設までの移動を前提にした文を出さない');
        assert.ok(!html.includes('火葬場や霊園への移動に、ペットタクシーを探す'), f.name + ': 施設への移動を前提にしたボタン文を出さない');
        assert.ok(!html.includes('火葬場や霊園への移動は、ペットタクシーで'), f.name + ': 移動の見出し（施設への移動を前提にした文）を出さない');
        assert.ok(html.includes('来館先が分かったら、ペットタクシーで'), f.name + ': 来館先未確認の見出しを出す');
        assert.ok(html.includes('href="' + f.u.replace(/&/g, '&amp;') + '"'), f.name + ': 公式サイトのリンクは残す');
      } else {
        assert.ok(/ data-to="/.test(m[0]), f.name + ': 確認済みなら行き先を入れる');
      }
    }
  }
  assert.equal(n, 30, '詳しいページは30件');
  console.log('sougi-visit detail pages ok', n, nNon);
}
