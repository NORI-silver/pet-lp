// トップの「さがすもの」（#pCat）：ペットタクシー・緊急・迷子・探偵・避難まで選べて、県の選択が行き先に引き継がれること。
// 非公開にした分野（犬と泊まれる宿・カフェ・里親・譲渡・犬の登録）は選択肢に出さない。
const fs = require("fs"), vm = require("vm"), assert = require("assert");
const root = __dirname + "/..";
const html = fs.readFileSync(root + "/index.html", "utf8");
const sel = id => (html.match(new RegExp('<select id="' + id + '"[^>]*>(.*?)</select>', "s")) || [])[1] || "";
const opts = h => [...h.matchAll(/<option([^>]*)>([^<]*)<\/option>/g)].map(m => ({ v: (m[1].match(/value="([^"]*)"/) || [])[1] ?? m[2], t: m[2], sel: /selected/.test(m[1]) }));
const cats = opts(sel("pCat"));
const vals = cats.map(o => o.v);
for (const v of ["taxi", "/hospital/", "/emergency/", "/pet-hotel/", "/pet-sitter/", "/trimming/", "/dog-trainer/", "/rojin-home/", "/dogrun/", "/sougi/", "/jichitai/", "/pet-detective/", "/hinan/"]) assert(vals.includes(v), "選択肢にない: " + v);
for (const v of vals) assert(!/inu-yado|pet-yado|inu-cafe|joto|touroku/.test(v), "非公開の分野が選択肢にある: " + v);
assert.strictEqual(cats.filter(o => o.sel).map(o => o.v).join(), "/hospital/", "既定の選択は動物病院のまま");
const prefs = opts(sel("pPref")).map(o => o.v).filter(Boolean);
assert.strictEqual(prefs.length, 47);
const formPrefs = opts(sel("pref")).map(o => o.v).filter(Boolean);
for (const p of prefs) assert(formPrefs.includes(p), "タクシーのフォームに県がない: " + p);
const code = html.match(/<script>\(function\(\)\{var g=document\.getElementById\("pGo"\).*?<\/script>/s)[0].replace(/^<script>|<\/script>$/g, "");
function run(cat, pref, formHas = true) {
  const log = { href: null, changed: 0, opened: 0, hash: null, order: [] };
  const els = {
    pCat: { value: cat }, pPref: { value: pref },
    pref: { value: "", options: formHas ? [pref] : [], _set(v) { return formHas ? v : ""; } },
    prefFix: { textContent: "", hidden: true },
    taxiOpen: { click() { log.opened++; log.order.push("open"); } },
  };
  let click;
  els.pGo = { addEventListener(_, f) { click = f; } };
  const pr = { _v: "" };
  Object.defineProperty(els.pref, "value", { get() { return pr._v; }, set(v) { log.order.push("set"); pr._v = formHas ? v : ""; } });
  els.pref.dispatchEvent = () => { log.changed++; log.order.push("change"); };
  const ctx = { document: { getElementById: id => els[id] }, location: { set href(v) { log.href = v; } }, history: { replaceState(_a, _b, h) { log.hash = h; } }, Event: function () {}, encodeURIComponent };
  vm.runInNewContext(code, ctx); click();
  return { log, els };
}
// 地域のページがある4県
for (const [p, s] of [["東京都", "tokyo"], ["神奈川県", "kanagawa"], ["埼玉県", "saitama"], ["千葉県", "chiba"]]) {
  assert.strictEqual(run("taxi", p).log.href, "/" + s + "/#form", p);
  assert(fs.existsSync(root + "/" + s + "/index.html"));
}
// 地域のページがない県（43県）：全国のフォームに県を入れたまま進む（地域のページの有無で受け付けを決めない）
for (const p of prefs.filter(p => !["東京都", "神奈川県", "埼玉県", "千葉県"].includes(p))) {
  const r = run("taxi", p);
  assert.strictEqual(r.els.pref.value, p, p + " の選択が残らない");
  assert.strictEqual(r.log.changed, 1, p + " change が発火しない"); assert.strictEqual(r.log.opened, 1, p + " 既存の開く処理を呼んでいない"); assert.strictEqual(r.log.order[0], "open", p + " 県を入れる前に開いていない"); assert.strictEqual(r.log.hash, "#form"); assert.strictEqual(r.log.href, null);
}
// フォームに選択肢がない県（会社がまだない）：消さずに理由を出す
const nf = run("taxi", "沖縄県", false);
assert.strictEqual(nf.els.pref.value, ""); assert(/沖縄県にお迎えに行けるペットタクシーの会社は、まだ見つかっていません/.test(nf.els.prefFix.textContent) && nf.els.prefFix.hidden === false); assert.strictEqual(nf.log.opened, 1);
// 全国は空のまま
const nat = run("taxi", ""); assert.strictEqual(nat.els.pref.value, ""); assert.strictEqual(nat.log.opened, 1);
// ほかの分野は今までどおり
const q = encodeURIComponent("愛知県");
for (const c of ["/hospital/", "/emergency/", "/pet-hotel/", "/pet-sitter/", "/trimming/", "/dog-trainer/", "/rojin-home/", "/dogrun/", "/sougi/", "/jichitai/"]) {
  assert.strictEqual(run(c, "愛知県").log.href, c + "#pref=" + q, c);
  assert.strictEqual(run(c, "").log.href, c, c);
}
assert.strictEqual(run("/pet-detective/", "北海道").log.href, "/pet-detective/?pref=" + encodeURIComponent("北海道"));
assert.strictEqual(run("/pet-detective/", "").log.href, "/pet-detective/");
// 避難：47県すべて、実在する県のページへ
for (const p of prefs) { const h = run("/hinan/", p).log.href; assert(/^\/hinan\/[a-z]+\/$/.test(h), p + " " + h); assert(fs.existsSync(root + h + "index.html"), h + " がない"); }
assert.strictEqual(run("/hinan/", "").log.href, "/hinan/");
console.log("ok home-search-category");
