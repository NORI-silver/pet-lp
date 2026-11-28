// tools/review_gate.cjs の確認（外部には何も触らない。カウンタはテスト用の偽物）。
const assert = require("assert"), { gate, identity, monthKey } = require("../tools/review_gate.cjs");
const TZ = "Asia/Tokyo", T = Date.UTC(2026, 10, 28, 3, 0, 0); // 2026-11-28 12:00 JST
function mem(init, opt) { const m = Object.assign({}, init), o = opt || {};
  return { m, async get(k) { if (o.failGet) throw new Error("x"); return o.badGet ? "abc" : (m[k] || 0); },
    async incr(k, lim) { await Promise.resolve(); if ((m[k] || 0) >= lim) return { ok: false, n: m[k] || 0 }; m[k] = (m[k] || 0) + 1; return { ok: true, n: m[k] }; } }; }
(async () => {
  const L = { month: 3, day: 2 };
  // 月の境目はタイムゾーンで決まる：UTC では 11/30 15:30 でも JST では 12/1
  assert.strictEqual(monthKey(Date.UTC(2026, 10, 30, 15, 30), "Asia/Tokyo").month, "2026-12");
  assert.strictEqual(monthKey(Date.UTC(2026, 10, 30, 15, 30), "UTC").month, "2026-11");
  // 通常: 日の上限(2)で止まる。月の上限(3)は日をまたいで効く
  const s = mem({});
  assert.ok((await gate(s, L, T, TZ)).allow); assert.ok((await gate(s, L, T, TZ)).allow);
  assert.deepStrictEqual(await gate(s, L, T, TZ), { allow: false, reason: "day-limit" });
  const next = T + 86400e3;
  assert.ok((await gate(s, L, next, TZ)).allow);
  assert.deepStrictEqual(await gate(s, L, next + 86400e3, TZ), { allow: false, reason: "month-limit" });
  // 12月に入れば月のカウントは別のキー
  assert.ok((await gate(s, L, Date.UTC(2026, 11, 1, 3), TZ)).allow);
  // カウンタが読めない・壊れている・上限が無い: 出さない
  assert.strictEqual((await gate(mem({}, { failGet: 1 }), L, T, TZ)).reason, "counter-error");
  assert.strictEqual((await gate(mem({}, { badGet: 1 }), L, T, TZ)).reason, "counter-bad");
  assert.strictEqual((await gate(mem({}), { month: 3 }, T, TZ)).reason, "no-limit");
  // 同時に10件来ても、上限を超えて通さない（incr が一度に判断する）
  const c = mem({}), r = await Promise.all(Array.from({ length: 10 }, () => gate(c, { month: 100, day: 4 }, T, TZ)));
  assert.strictEqual(r.filter((x) => x.allow).length <= 4 && c.m["d:2026-11-28"] <= 4, true, "同時でも日の上限を超えない");
  // 施設の照合
  const ours = { name: "わんポイント（Happy Pet Station）", address: "愛知県豊川市当古町本郷前6-2" };
  assert.deepStrictEqual(identity(ours, { name: "わんポイント（Happy Pet Station）", address: "愛知県豊川市当古町本郷前6-2" }), { ok: true, reason: "confirmed" });
  assert.strictEqual(identity(ours, { name: "わんポイント（Happy Pet Station）", address: "日本、愛知県豊川市八幡町" }).ok, false, "住所の頭が違う書き方は、確実でないので出さない");
  assert.strictEqual(identity(ours, { name: "わんポイント（Happy Pet Station）", address: "東京都豊島区1-1" }).reason, "wrong-pref");
  assert.strictEqual(identity(ours, { name: "わんポイント（Happy Pet Station）", address: "愛知県豊橋市1-1" }).reason, "wrong-city");
  assert.strictEqual(identity(ours, { name: "わんポイント別店", address: "愛知県豊川市1-1" }).reason, "name-differs");
  assert.strictEqual(identity({ name: ours.name }, { name: ours.name, address: "愛知県豊川市1" }).reason, "no-address");
  assert.strictEqual(identity(ours, { name: ours.name }).reason, "no-address");
  console.log("ok review-gate");
})().catch((e) => { console.error(e); process.exit(1); });
