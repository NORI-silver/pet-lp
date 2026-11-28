// S3 の下準備（どのページにも読み込まれない。本番は変えない）。
// 口コミを「出す前」の2つの判断だけを、外部（Google・バックエンド）に触らずに書いておく。
//  1. 件数の門（gate）: 月・日・1訪問あたりの上限。数え方は呼び出し側が渡す（本物のカウンタはここにない）。
//  2. 施設の照合（identity）: 名前＋市だけでは確定しない。番地まで合う、または確かめ済みの施設IDが同じときだけ ok。迷ったら出さない。
// 注意: テストの偽カウンタは「呼び出しの約束」を確かめるだけ。本物のバックエンドの原子性・料金の安全は何も証明しない（未確認）。
"use strict";
function monthKey(nowMs, tz) {
  const p = new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date(nowMs));
  const g = (t) => p.find((x) => x.type === t).value;
  return { month: g("year") + "-" + g("month"), day: g("year") + "-" + g("month") + "-" + g("day") };
}
// store: {get(key)->number|Promise, incr(key, limit)->{ok:boolean, n:number}} （incr は上限を超えないよう一度に判断する）
// 読めない・壊れているときは "deny"（出さない）。上限の既定値は呼び出し側が決める。
async function gate(store, limits, nowMs, tz) {
  const k = monthKey(nowMs, tz);
  try {
    for (const [key, lim] of [["m:" + k.month, limits.month], ["d:" + k.day, limits.day]]) {
      if (!(lim >= 0)) return { allow: false, reason: "no-limit" };
      const n = Number(await store.get(key));
      if (!Number.isFinite(n) || n < 0) return { allow: false, reason: "counter-bad" };
      if (n >= lim) return { allow: false, reason: key[0] === "m" ? "month-limit" : "day-limit" };
    }
    const a = await store.incr("d:" + k.day, limits.day), b = a.ok ? await store.incr("m:" + k.month, limits.month) : { ok: false };
    if (!a.ok || !b.ok) return { allow: false, reason: a.ok ? "month-limit" : "day-limit" };
    return { allow: true };
  } catch (e) { return { allow: false, reason: "counter-error" }; }
}
const norm = (s) => String(s || "").normalize("NFKC").replace(/[\s　・\-－ー]/g, "").toLowerCase();
const PREF = /^(北海道|東京都|京都府|大阪府|.{2,3}県)/;
const pref = (a) => (String(a || "").normalize("NFKC").match(PREF) || [])[1] || "";
// 住所を「市区町村 / 町名 / 番地の数字列」に分ける。番地が読み取れなければ null（確実でない）。
function parts(addr) {
  const a = String(addr).normalize("NFKC").replace(/^日本[、,\s]*/, "").replace(/^〒?\d{3}-?\d{4}\s*/, "");
  const rest = a.replace(PREF, ""), m = rest.match(/^(.+?[市区町村])(.*)$/);
  if (!m) return null;
  const tail = m[2].replace(/（[^）]*）|\([^)]*\)/g, ""); // 括弧の補足（建物名など）は照合に使わない
  const k = tail.match(/^(\D*?)(\d+(?:[丁目番地号\-－ー−‐‑–—]+\d+)*)/); // 町名のあとの最初の番地のかたまりだけ読む（建物名・階数は読まない）
  if (!k) return null;
  const nums = k[2].match(/\d+/g).map(Number), town = k[1].replace(/\s+/g, "");
  return nums.length ? { city: m[1], town, nums } : null;
}
// ours / cand: {name, address, placeId?}。placeId は「前に人が確かめた」安定した施設IDだけを入れる（名前や住所から作らない）。
// 結果: ok:true は (a) 確かめ済みの同じ placeId、または (b) 名前・市区町村・町名・番地の数字が全部合うときだけ。
// 同じ市の同名の別店舗、番地の違い、番地なし・読み取れない住所は ok:false（出さない）。名前＋市だけでは確定しない。
function identity(ours, cand) {
  if (!ours || !cand) return { ok: false, reason: "no-candidate" };
  if (ours.placeId && cand.placeId) return ours.placeId === cand.placeId ? { ok: true, reason: "verified-place-id" } : { ok: false, reason: "place-id-differs" };
  if (!ours.address || !cand.address) return { ok: false, reason: "no-address" };
  const a = String(ours.address).normalize("NFKC"), b = String(cand.address).normalize("NFKC");
  if (pref(a) && pref(b) && pref(a) !== pref(b)) return { ok: false, reason: "wrong-pref" };
  const pa = parts(a), pb = parts(b);
  if (!pa || !pb) return { ok: false, reason: "unresolved-address" };
  if (pa.city !== pb.city) return { ok: false, reason: "wrong-city" };
  if (norm(ours.name) !== norm(cand.name)) return { ok: false, reason: "name-differs" };
  if (pa.town !== pb.town) return { ok: false, reason: "different-town" };
  if (pa.nums.join("-") !== pb.nums.join("-")) return { ok: false, reason: "different-street-number" };
  return { ok: true, reason: "confirmed" };
}
module.exports = { gate, identity, monthKey };
