// S3 の下準備（どのページにも読み込まれない。本番は変えない）。
// 口コミを「出す前」の2つの判断だけを、外部（Google・バックエンド）に触らずに書いておく。
//  1. 件数の門（gate）: 月・日・1訪問あたりの上限。数え方は呼び出し側が渡す（本物のカウンタはここにない）。
//  2. 施設の照合（identity）: 名前だけの一致は使わない。確実に合うときだけ "confirmed"。迷ったら出さない。
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
const pref = (a) => (String(a || "").normalize("NFKC").match(/^(北海道|東京都|京都府|大阪府|.{2,3}県)/) || [])[1] || "";
// ours: {name, address}  cand: {name, address}（Google が返した候補）。住所が無い・都道府県が違う・市区町村が違えば出さない。
function identity(ours, cand) {
  if (!ours || !cand || !ours.address || !cand.address) return { ok: false, reason: "no-address" };
  const a = String(ours.address).normalize("NFKC"), b = String(cand.address).normalize("NFKC");
  if (pref(a) && pref(b) && pref(a) !== pref(b)) return { ok: false, reason: "wrong-pref" };
  const city = (x) => (x.replace(/^(北海道|東京都|京都府|大阪府|.{2,3}県)/, "").match(/^(.+?[市区町村])/) || [])[1] || "";
  if (!city(a) || city(a) !== city(city(b) ? b : "")) return { ok: false, reason: "wrong-city" };
  if (norm(ours.name) !== norm(cand.name)) return { ok: false, reason: "name-differs" };
  return { ok: true, reason: "confirmed" };
}
module.exports = { gate, identity, monthKey };
