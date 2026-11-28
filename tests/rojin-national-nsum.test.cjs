// 老犬ホーム：条件つきの料金（R020・R038・R059）。見せる金額には必ず条件がついていて、全文と出典へ行ける道があること。
//  全国のページの料金の行は、次のどちらか（どちらの形でもよい。条件を落とした金額だけの行は不可）：
//   (a) 金額のない案内（県のページの「詳しく見る」へ）＋ その施設の県のページのカードへのリンク
//   (b) 条件つきの要約（rojin.json の sum そのまま）＋ 同じカードの中に料金の全文と出典
//  県のページのカード：料金の全文（rojin.json の v そのまま）と出典のリンク・確認日が「詳しく見る」にある。
const fs = require("fs"), assert = require("assert");
const root = __dirname + "/..";
const J = JSON.parse(fs.readFileSync(root + "/tools/rojin.json", "utf8"));
const pref = { R059: "miyagi", R038: "fukuoka", R020: "aichi" };
const plain = s => s.replace(/<[^>]+>/g, "").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#x27;|&#39;/g, "'").replace(/&amp;/g, "&");
function card(h, fid) {
  const i = h.indexOf('data-fid="' + fid + '"'); if (i < 0) return null;
  const j = h.indexOf('data-fid="', i + 10); return h.slice(i, j < 0 ? h.length : j);
}
const nat = fs.readFileSync(root + "/rojin-home/index.html", "utf8");
for (const [fid, p] of Object.entries(pref)) {
  const fact = J.homes.find(h => h.id === fid).facts.find(f => f.k === "料金");
  const pg = fs.readFileSync(root + "/rojin-home/" + p + "/index.html", "utf8");
  const c = card(pg, fid);
  assert(c, fid + " 県のページにカードがない");
  const ct = plain(c);
  assert(ct.includes("料金（全文）") && ct.includes(fact.v), fid + " 県のページに料金の全文（rojin.json の v）がない");
  assert(/出典：/.test(ct) && /確認日 2026-/.test(ct) && /<a href="https?:[^"]+"[^>]*>公式サイト/.test(c), fid + " 県のページのカードに出典と確認日がない");
  const yp = c.match(/<li class="yen"><b>料金<\/b><span>(.*?)<\/span>/);
  assert(yp && [fact.sum, fact.v].includes(plain(yp[1])), fid + " 県のページのカードの料金の行は、条件つきの要約か全文: " + (yp && plain(yp[1])));
  const n = card(nat, fid);
  if (!n) continue;
  const y = n.match(/<li class="yen"><b>料金<\/b><span>(.*?)<\/span>/);
  const row = y ? plain(y[1]) : "";
  console.log(fid, "national row:", row);
  const pointer = fact.nsum && row === fact.nsum && !/[0-9０-９]/.test(row);
  const summary = row === fact.sum;
  assert(pointer || summary, fid + " 全国のページの料金の行が、案内でも条件つきの要約でもない: " + row);
  if (pointer) assert(n.includes('href="/rojin-home/' + p + '/#c-' + fid + '"'), fid + " 案内の先が、この施設の県のページのカードではない");
  else assert(plain(n).includes(fact.v) && /出典：/.test(plain(n)), fid + " 要約だけで全文と出典への道がない");
}
console.log("ok rojin-national-nsum");
