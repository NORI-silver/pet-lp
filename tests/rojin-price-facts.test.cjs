// 老犬ホーム R020・R038・R059：料金の事実と、並べ替え・絞り込みの目印を、出来上がったページ全部で確かめる。
//  1. カードの料金の行は、rojin.json の条件つきの要約（sum）。条件を落とした金額だけの行にしない。全文（v）と出典は同じカードの「詳しく見る」にある。
//  2. 価格順の目印 data-yen は、公式サイトの料金表の基本の金額だけ。上限・加算・預かり金・面会費の最小値を拾わない。比べる土台にならない料金（永代預りの一時払い）は data-yen を付けない。
//  3. R020 は中型犬（15kg未満）も受ける。「うちの子」の絞り込みで中型を選んでも出る。
// 全国のページと県のページの、この施設のカードを1枚ずつ全部調べる（最初の1枚だけではない）。
const fs = require("fs"), assert = require("assert");
const root = __dirname + "/..";
const J = JSON.parse(fs.readFileSync(root + "/tools/rojin.json", "utf8"));
const plain = s => s.replace(/<[^>]+>/g, "").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#x27;|&#39;/g, "'").replace(/&amp;/g, "&");
const wantYen = { R020: null, R038: null, R059: null };   // 3施設とも null＝価格順の基準を付けない。R020 は1か月（預かり金込みの合計）、R038 は1日あたり／期間合計（大型は食い違い）、R059 は永代預りの一時払いで、数え方がそろわず、同じ土台で並べると誤解を招く。また explicit な yen を付けると県ごとの料金表・並び順にも入るので、全国の施設の見え方が変わってしまう
const prefPage = { R020: "aichi", R038: "fukuoka", R059: "miyagi" };
const forbidden = { R020: [25000, 50000, 10000, 34100, 52000], R038: [300, 3000, 550, 33000], R059: [10000, 12000, 15000, 20000] };
const pages = [["", fs.readFileSync(root + "/rojin-home/index.html", "utf8")]];
for (const d of fs.readdirSync(root + "/rojin-home", { withFileTypes: true })) {
  if (d.isDirectory() && fs.existsSync(root + "/rojin-home/" + d.name + "/index.html")) pages.push([d.name, fs.readFileSync(root + "/rojin-home/" + d.name + "/index.html", "utf8")]);
}
function instances(h, fid) {   // この施設のカード全部（開始タグ＋次のカードまで）
  const out = [], rx = new RegExp('<div[^>]*data-fid="' + fid + '"[^>]*>', "g"); let m;
  while ((m = rx.exec(h))) { const nx = h.indexOf('<div class="emg-item', m.index + 10); out.push({ tag: m[0], body: h.slice(m.index, nx < 0 ? h.length : nx) }); }
  return out;
}
let total = 0;
for (const fid of Object.keys(wantYen)) {
  const home = J.homes.find(h => h.id === fid), fact = home.facts.find(f => f.k === "料金");
  assert(fact.sum && fact.v && fact.src && fact.checked, fid + " 料金の事実に sum・v・出典・確認日がそろっていない");
  assert.strictEqual(fact.yen === undefined ? "missing" : fact.yen, null, fid + " rojin.json は yen: null と明記する");
  let n = 0, inPref = 0;
  for (const [name, h] of pages) {
    for (const c of instances(h, fid)) {
      n++; if (name === prefPage[fid]) inPref++;
      const ct = plain(c.body);
      const y = c.body.match(/<li class="yen"><b>料金<\/b><span>(.*?)<\/span>/);
      assert(y, fid + " " + (name || "全国") + " 料金の行がない");
      assert.strictEqual(plain(y[1]), fact.sum, fid + " " + (name || "全国") + " 料金の行は条件つきの要約（sum）: " + plain(y[1]));
      if (ct.includes(fact.v) || name === prefPage[fid]) {   // 全文がカードにある（県のページでは必ず）：出典・確認日も同じカードにある
        assert(ct.includes(fact.v), fid + " " + (name || "全国") + " 料金の全文（v）が同じカードにない");
        assert(/出典：/.test(ct) && /確認日 2026-/.test(ct), fid + " " + (name || "全国") + " 出典と確認日がない");
      } else {      // 全国のページの軽い形のカード：要約（sum）だけ載せ、全文・出典は自分の施設の県のページへの「詳しく見る」リンクで開ける（リンク先に全文があることは県のページの検査で確かめる）
        const lk = c.body.match(/<a [^>]*href="(\/rojin-home\/[a-z0-9-]+\/)(#[^"]*)?"[^>]*>[^<]*詳しく見る[^<]*/);
        assert(lk, fid + " 全国 全文へのリンク（県のページで詳しく見る）がない");
        assert.strictEqual(lk[1], "/rojin-home/" + prefPage[fid] + "/", fid + " 全国 リンク先が自分の施設の県のページではない: " + lk[1]);
        const pp = root + lk[1] + "index.html"; assert(fs.existsSync(pp), fid + " リンク先のページがない");
        if (lk[2]) assert(fs.readFileSync(pp, "utf8").includes('id="' + lk[2].slice(1) + '"'), fid + " リンク先に " + lk[2] + " の位置がない");
      }
      const dy = c.tag.match(/data-yen="(\d+)"/);
      if (wantYen[fid] === null) assert(!dy, fid + " 並べ替えの基準にならない料金に data-yen が付いている: " + (dy && dy[1]));
      else { assert(dy, fid + " data-yen がない"); assert.strictEqual(+dy[1], wantYen[fid], fid + " data-yen"); }
      if (dy) assert(!forbidden[fid].includes(+dy[1]), fid + " data-yen が上限・加算・預かり金・面会費の金額: " + dy[1]);
    }
  }
  assert(inPref >= 1, fid + " 県のページにカードがない");
  total += n; console.log(fid, "cards checked:", n, "(pref page", inPref + ")");
}
// R020：中型犬（15kg未満）も受ける。絞り込みの目印に中型が入り、公式サイトにない大型は入らない
{
  const home = J.homes.find(h => h.id === "R020");
  assert(/中型犬15kg未満は満12歳以上/.test(home.animals) && /小型犬5kg未満は満10歳以上/.test(home.animals), "R020 受け入れる動物の文が、小型（満10歳以上）・中型（満12歳以上）を書いていない");
  for (const [name, h] of pages) for (const c of instances(h, "R020")) {
    const fit = JSON.parse(c.tag.match(/data-fit='([^']*)'/)[1]);
    assert(fit.s && fit.s.includes("s") && fit.s.includes("m") && !fit.s.includes("l"), "R020 " + (name || "全国") + " data-fit の大きさ: " + JSON.stringify(fit.s));
  }
}
// R020 の返金（A 半額／B 全額／C 残額）と、R038 の食い違いの書き方
{
  const v20 = J.homes.find(h => h.id === "R020").facts.find(f => f.k === "料金").v;
  assert(/短期預かりは何日で[^。]*返金なし/.test(v20) && /7日以内[^。]*半額返金/.test(v20) && /B（死亡時の諸費用）[^。]*全額返金/.test(v20) && /C（予備費）[^。]*残り[^。]*返金/.test(v20), "R020 返金の文（A・B・C）");
  const f38 = J.homes.find(h => h.id === "R038").facts.find(f => f.k === "料金");
  assert(/一致しない/.test(f38.v) && /一致しない/.test(f38.sum) && /132,000円/.test(f38.v) && /4,840円/.test(f38.v), "R038 大型1か月の食い違いを書いていない");
  assert(!/30日分にすると|月は30日/.test(f38.v + f38.sum), "R038 サイトが書いていない期間（30日）を決めつけない");
}
assert(total >= Object.keys(wantYen).length * 1 + 2, "カードの数が少なすぎる: " + total);   // 3施設とも県のページに1枚以上（上の inPref）＋全国のページの R059 など。全国のページに出る施設は取り込みで変わるので、数は下限だけ見る
console.log("ok rojin-price-facts", total);
