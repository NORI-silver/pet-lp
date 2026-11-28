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
  // カウンタ: 読めない・壊れている・上限が無い: 出さない。キーが無い(null)ときだけ0件
  assert.strictEqual((await gate(mem({}, { failGet: 1 }), L, T, TZ)).reason, "counter-error");
  assert.strictEqual((await gate(mem({}, { badGet: 1 }), L, T, TZ)).reason, "counter-bad");
  for (const bad of [undefined, "", "0", NaN, -1, 1.5, {}, []]) assert.strictEqual((await gate({ get: async () => bad, incr: async () => ({ ok: true }) }, L, T, TZ)).reason, "counter-bad", "壊れた値は0にしない: " + String(bad));
  assert.ok((await gate({ get: async () => null, incr: async () => ({ ok: true }) }, L, T, TZ)).allow, "null=キーが無い=0件");
  assert.strictEqual((await gate(mem({}), { month: 3 }, T, TZ)).reason, "no-limit");
  assert.strictEqual((await gate(mem({}), null, T, TZ)).reason, "no-limit");
  // 時刻・タイムゾーンが不正でも reject せず deny
  for (const [t, z] of [[NaN, TZ], [Infinity, TZ], ["x", TZ], [T, "Not/AZone"], [T, ""], [T, undefined], [undefined, TZ]]) assert.deepStrictEqual(await gate(mem({}), L, t, z), { allow: false, reason: "bad-time" }, "bad-time: " + String(t) + "/" + String(z));
  // 1訪問あたりの上限
  const V = { month: 10, day: 10, visit: 2 };
  assert.ok((await gate(mem({}), V, T, TZ, { used: 1 })).allow);
  assert.strictEqual((await gate(mem({}), V, T, TZ, { used: 2 })).reason, "visit-limit");
  assert.strictEqual((await gate(mem({}), V, T, TZ, { used: -1 })).reason, "visit-bad");
  assert.strictEqual((await gate(mem({}), V, T, TZ, { used: "1" })).reason, "visit-bad");
  assert.ok((await gate(mem({}), V, T, TZ)).allow, "used が無ければ0");
  // 日の加算のあとで月の加算が失敗したら、日の分は戻さない（使いすぎ側に倒す）
  const sp = mem({}); const inc = sp.incr; sp.incr = async (k, l) => (k[0] === "m" ? { ok: false, n: 0 } : inc(k, l));
  assert.deepStrictEqual(await gate(sp, L, T, TZ), { allow: false, reason: "month-limit", daySpent: true });
  assert.strictEqual(sp.m["d:2026-11-28"], 1, "日の分は戻さない");
  // （この偽カウンタは呼び出しの約束を確かめるだけ。本物のバックエンドの原子性・料金の安全は証明しない）
  // 同時に10件来ても、上限を超えて通さない（incr が一度に判断する）
  const c = mem({}), r = await Promise.all(Array.from({ length: 10 }, () => gate(c, { month: 100, day: 4 }, T, TZ)));
  assert.strictEqual(r.filter((x) => x.allow).length <= 4 && c.m["d:2026-11-28"] <= 4, true, "同時でも日の上限を超えない");
  // 施設の照合: 住所が合っても建物・階・部屋が決まらなければ「候補」。出してよいのは確かめ済みの placeId が同じときだけ
  const ours = { name: "わんポイント（Happy Pet Station）", address: "愛知県豊川市当古町本郷前6-2" }, N = ours.name;
  const st = (o, c) => identity(o, c).status + "/" + identity(o, c).reason + "/" + identity(o, c).ok;
  assert.strictEqual(st(ours, { name: N, address: "愛知県豊川市当古町本郷前6-2" }), "candidate/same-number-unit-unknown/false", "名前・市・町・番地が合っても確定ではなく候補");
  assert.strictEqual(st(ours, { name: N, address: "日本、〒441-1111 愛知県豊川市当古町本郷前６−２" }), "candidate/same-number-unit-unknown/false");
  assert.strictEqual(st(ours, { name: N, address: "愛知県豊川市当古町本郷前6-2 ビルA 2F" }), "candidate/building-unit-unresolved/false", "片方にだけ建物・階がある: 未解決の候補");
  assert.strictEqual(st({ name: N, address: "愛知県豊川市当古町本郷前6-2 ビルA 2F" }, { name: N, address: "愛知県豊川市当古町本郷前6-2 ビルA 2F" }), "candidate/building-unit-unresolved/false", "同じ建物・階でも住所の文字だけでは確定しない");
  assert.strictEqual(st({ name: N, address: "愛知県豊川市当古町本郷前6-2 ビルA 2F" }, { name: N, address: "愛知県豊川市当古町本郷前6-2 ビルA 3F" }), "rejected/building-unit-conflict/false", "階が食い違う");
  assert.strictEqual(st({ name: N, address: "愛知県豊川市当古町本郷前6-2（ビルA）" }, { name: N, address: "愛知県豊川市当古町本郷前6-2（ビルB）" }), "rejected/building-unit-conflict/false", "建物名が食い違う");
  assert.strictEqual(st(ours, { name: N, address: "愛知県豊川市当古町本郷前6-3" }), "rejected/different-street-number/false");
  assert.strictEqual(st(ours, { name: N, address: "愛知県豊川市八幡町鐘鋳場227-1" }), "rejected/different-town/false");
  assert.strictEqual(st(ours, { name: N, address: "愛知県豊川市当古町本郷前6" }), "rejected/different-street-number/false");
  assert.strictEqual(st(ours, { name: N, address: "愛知県豊川市" }), "rejected/unresolved-address/false");
  assert.strictEqual(st(ours, { name: N, address: "愛知県豊川市当古町" }), "rejected/unresolved-address/false");
  assert.strictEqual(st({ name: N, address: "豊川市当古町6-2" }, { name: N, address: "愛知県豊川市当古町6-2" }), "candidate/same-number-unit-unknown/false");
  assert.strictEqual(st(ours, { name: N, address: "東京都豊島区1-1" }), "rejected/wrong-pref/false");
  assert.strictEqual(st(ours, { name: N, address: "愛知県豊橋市当古町本郷前6-2" }), "rejected/wrong-city/false");
  assert.strictEqual(st(ours, { name: "わんポイント別店", address: "愛知県豊川市当古町本郷前6-2" }), "rejected/name-differs/false");
  assert.strictEqual(st({ name: N }, { name: N, address: "愛知県豊川市当古町本郷前6-2" }), "rejected/no-address/false");
  assert.strictEqual(st(ours, null), "rejected/no-candidate/false");
  // 確かめ済みの placeId が同じときだけ ok:true。違えば住所が同じでも rejected
  assert.deepStrictEqual(identity({ name: N, placeId: "P1" }, { name: "別名", placeId: "P1" }), { ok: true, status: "verified-place-id", reason: "verified-place-id" });
  assert.strictEqual(st({ name: N, address: ours.address, placeId: "P1" }, { name: N, address: ours.address, placeId: "P2" }), "rejected/place-id-differs/false");
  console.log("ok review-gate");
})().catch((e) => { console.error(e); process.exit(1); });
