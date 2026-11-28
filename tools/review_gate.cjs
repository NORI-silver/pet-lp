// S3 の下準備（どのページにも読み込まれない。本番は変えない。外部（Google・バックエンド）には一切触らない）。
// 口コミを「出す前」の判断を2つだけ、約束（契約）として書いておく。迷ったら「出さない」。
//
// 1. gate(): 月・日・1訪問あたりの件数の門。
//    store.get(key) の約束: 「キーがまだ無い」ときだけ null を返す（0件として扱う）。数（0以上の整数）はその件数。
//      それ以外（undefined・空文字・文字・NaN・負・小数・例外）は「壊れている/読めない」で出さない（counter-bad / counter-error）。
//    store.incr(key, limit) の約束: 上限を超えないよう1回で判断し {ok, n} を返す。
//    日 → 月の順に数える。日を数えたあとに月の加算が失敗したら、日の分は戻さない（rollback しない。
//    使いすぎ側に倒す＝その日はその分を使ったものとして扱う）。
//    時刻・タイムゾーンが不正なときも例外にせず {allow:false, reason:"bad-time"}。
//    注意: テストの偽カウンタは呼び出しの約束を確かめるだけ。本物のバックエンドの原子性・月のリセット・料金の安全は何も証明しない（未確認）。
// 2. identity(): 施設の照合。確かめ済みの placeId が同じときだけ ok:true。
//    住所が合っても、建物・階・部屋の違いは住所の文字だけでは決められないので ok:false の status:"candidate"（候補）。
//    建物・階・部屋の書き方が両方にあって食い違えば status:"rejected"。candidate は人が確かめるか placeId が付くまで出さない。
"use strict";
function monthKey(nowMs, tz) {
  if (typeof nowMs !== "number" || !Number.isFinite(nowMs) || typeof tz !== "string" || !tz) throw new RangeError("bad-time");
  const p = new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date(nowMs));
  const g = (t) => p.find((x) => x.type === t).value;
  return { month: g("year") + "-" + g("month"), day: g("year") + "-" + g("month") + "-" + g("day") };
}
const validCount = (n) => typeof n === "number" && Number.isInteger(n) && n >= 0;
// visit: {used: 今回の訪問で既に出した件数}（無ければ 0）。limits.visit が無ければ訪問の上限は見ない。
async function gate(store, limits, nowMs, tz, visit) {
  let k;
  try { k = monthKey(nowMs, tz); } catch (e) { return { allow: false, reason: "bad-time" }; }
  try {
    if (!limits || !(limits.month >= 0) || !(limits.day >= 0)) return { allow: false, reason: "no-limit" };
    if (limits.visit !== undefined) {
      const used = !visit || visit.used === undefined ? 0 : visit.used;
      if (!(limits.visit >= 0) || !validCount(used)) return { allow: false, reason: "visit-bad" };
      if (used >= limits.visit) return { allow: false, reason: "visit-limit" };
    }
    for (const [key, lim, why] of [["m:" + k.month, limits.month, "month-limit"], ["d:" + k.day, limits.day, "day-limit"]]) {
      let n = await store.get(key);
      if (n === null) n = 0; // 本当にキーが無いときだけ
      if (!validCount(n)) return { allow: false, reason: "counter-bad" };
      if (n >= lim) return { allow: false, reason: why };
    }
    const a = await store.incr("d:" + k.day, limits.day);
    if (!a || a.ok !== true) return { allow: false, reason: "day-limit" };
    const b = await store.incr("m:" + k.month, limits.month);
    if (!b || b.ok !== true) return { allow: false, reason: "month-limit", daySpent: true }; // 日の分は戻さない
    return { allow: true };
  } catch (e) { return { allow: false, reason: "counter-error" }; }
}
const norm = (s) => String(s || "").normalize("NFKC").replace(/[\s　・\-－ー]/g, "").toLowerCase();
const PREF = /^(北海道|東京都|京都府|大阪府|.{2,3}県)/;
const pref = (a) => (String(a || "").normalize("NFKC").match(PREF) || [])[1] || "";
// 住所を「市区町村 / 町名 / 番地の数字列 / 番地のあとの残り（建物・階・部屋）」に分ける。番地が読み取れなければ null。
function parts(addr) {
  const a = String(addr).normalize("NFKC").replace(/^日本[、,\s]*/, "").replace(/^〒?\d{3}-?\d{4}\s*/, "");
  const rest = a.replace(PREF, ""), m = rest.match(/^(.+?[市区町村])(.*)$/);
  if (!m) return null;
  const tail = m[2].replace(/（([^）]*)）|\(([^)]*)\)/g, " $1$2 ");
  const k = tail.match(/^(\D*?)(\d+(?:[丁目番地号\-－ー−‐‑–—]+\d+)*)(.*)$/);
  if (!k) return null;
  return { city: m[1], town: k[1].replace(/\s+/g, ""), nums: k[2].match(/\d+/g).map(Number), unit: norm(k[3].replace(/^[丁目番地号\-－ー−‐‑–—\s]+/, "")) };
}
// ours / cand: {name, address, placeId?}。placeId は「前に人が確かめた」安定した施設IDだけ（名前や住所から作らない）。
// 結果 {ok, status, reason}。ok は status が "verified-place-id" のときだけ true。
//   "verified-place-id": 確かめ済みの同じ placeId。
//   "candidate": 名前・市区町村・町名・番地の数字が合う。ただし建物・階・部屋は住所の文字だけでは決められない（片方にしか無い／両方に無い）。出さない。
//   "rejected": 都道府県・市・町・番地・名前が違う、住所が足りない、建物・階・部屋の書き方が両方にあって食い違う、など。
function identity(ours, cand) {
  const no = (reason) => ({ ok: false, status: "rejected", reason });
  if (!ours || !cand) return no("no-candidate");
  if (ours.placeId && cand.placeId) return ours.placeId === cand.placeId ? { ok: true, status: "verified-place-id", reason: "verified-place-id" } : no("place-id-differs");
  if (!ours.address || !cand.address) return no("no-address");
  const a = String(ours.address).normalize("NFKC"), b = String(cand.address).normalize("NFKC");
  if (pref(a) && pref(b) && pref(a) !== pref(b)) return no("wrong-pref");
  const pa = parts(a), pb = parts(b);
  if (!pa || !pb) return no("unresolved-address");
  if (pa.city !== pb.city) return no("wrong-city");
  if (norm(ours.name) !== norm(cand.name)) return no("name-differs");
  if (pa.town !== pb.town) return no("different-town");
  if (pa.nums.join("-") !== pb.nums.join("-")) return no("different-street-number");
  if (pa.unit && pb.unit && pa.unit !== pb.unit) return no("building-unit-conflict");
  return { ok: false, status: "candidate", reason: pa.unit || pb.unit ? "building-unit-unresolved" : "same-number-unit-unknown" };
}
module.exports = { gate, identity, monthKey };
