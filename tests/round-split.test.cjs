// 往復を行きと帰りで別の会社に頼む（Nori 2026-10-31「往復はそれぞれ別の会社に頼めるようにして」）
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const ctx = vm.createContext({ Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs', 'utf8'), ctx);
ctx.sign_ = s => crypto.createHmac('sha256', 'test-secret').update(s).digest('hex');
ctx.Utilities = { formatDate(d) { return new Date(d.getTime() + 9 * 3600000).toISOString().slice(0, 16); } };
ctx.CONFIG.DEFAULT_PARTNER_HOURS = '0-24';
ctx.PropertiesService = { getScriptProperties: () => ({ getProperty: () => null, setProperty() {} }) };
const partner = (id, extra = {}) => ({ id, name: '確認用 ' + id, areas: ['東京'], active: true, email: 'test@example.invalid', careOk: true, big: true, luggage: true, riders: 3, pets: 5, cageMust: '不要', cageLend: true, lead: 3, hours: '0-24', car: 'ワンボックス', ...extra });
let partners = [partner('P002'), partner('P003')];
ctx.partners_ = () => partners;
const A = { lat: 35.63, lng: 139.66 }, B = { lat: 35.64, lng: 139.70 };
const day = new Date(Date.now() + 48 * 3600000 + 9 * 3600000).toISOString().slice(0, 10);
const p = { pref: '東京都', pickup: '世田谷区', dropoff: '目黒区', datetime: day + 'T10:00', trip: '往復', return_datetime: day + 'T16:00',
  return_pickup: '目黒区', return_dropoff: '世田谷区', riders: '1人', luggage: '少なめ', species: '犬', weight: '8', cage: '持ち込む', care: '不要',
  pet_count: '1', pets_json: '[]', route_details: JSON.stringify({ km: 8, backKm: 12, from: A, to: B, backFrom: B, backTo: A }) };

// 候補：往復のときは、1社で往復の候補に加えて、行き・帰りそれぞれ片道の候補も返す
const res = JSON.parse(JSON.stringify(ctx.selectionQuotes_(p)));
assert.ok(res.ok && res.cards.length === 2 && res.legs && res.legs.go.length === 2 && res.legs.back.length === 2);
const go = res.legs.go.find(c => c.id === 'P002'), back = res.legs.back.find(c => c.id === 'P003');
assert.equal(go.price.local.method, '片道');
assert.ok(res.legs.back[0].price.amount > res.legs.go[0].price.amount, '帰りは12kmで計算（行きより高い）');
assert.equal(JSON.parse(JSON.stringify(ctx.selectionQuotes_({ ...p, trip: '片道' }))).legs, undefined, '片道には legs なし');

// 受付：2件の片道の依頼として保存し、それぞれ選んだ会社にだけ送る
let saved = [], receipts = [], waves = [], cache = new Map(), n = 0;
ctx.LockService = { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) };
ctx.CacheService = { getScriptCache: () => ({ get: k => cache.get(k), put: (k, v) => cache.set(k, v) }) };
ctx.SpreadsheetApp = { flush() {} };
ctx.sheet_ = () => ({ appendRow: row => saved.push(row), getLastRow: () => saved.length + 1, getRange: () => ({ setNumberFormat() {} }) });
ctx.ensureReqHeaders_ = () => ctx.REQ_HEADERS;
ctx.newId_ = () => 'ID' + (++n);
ctx.sendReceipt_ = r => receipts.push(r['受付番号']);
ctx.sendWave_ = id => { waves.push(id); return 'selected'; };
ctx.notifyAdmin_ = () => {}; ctx.isTest_ = () => true; ctx.adminUrl_ = () => ''; ctx.whenText_ = () => '';
const H = ctx.REQ_HEADERS, col = (row, h) => row[H.indexOf(h)];
const req = { ...p, name: 'テスト', tel: '00000000000', email: 'test@example.invalid', contact: 'メール', req_key: 'split-1', split: '1',
  partner_id: go.id, quote_token: go.token, quote_expires: go.expires, back_partner_id: back.id, back_quote_token: back.token, back_quote_expires: back.expires };
const out = ctx.receive_(req);
assert.deepEqual(JSON.parse(JSON.stringify(out)), { ok: true, id: 'ID1', back_id: 'ID2' });
assert.equal(saved.length, 2);
assert.deepEqual(saved.map(r => col(r, '指定した提携先ID')), ['P002', 'P003']);
assert.deepEqual(saved.map(r => col(r, '片道・往復')), ['片道', '片道']);
assert.deepEqual(saved.map(r => col(r, 'お迎えの場所')), ['世田谷区', '目黒区']);
assert.equal(col(saved[1], '希望日時').getTime(), ctx.parseJst_(p.return_datetime).getTime(), '帰りは帰りの日時');
assert.deepEqual(saved.map(r => col(r, 'ペアの受付番号')), ['ID2', 'ID1']);
assert.ok(/^行き/.test(col(saved[0], '区間')) && /^帰り/.test(col(saved[1], '区間')));
assert.deepEqual(waves, ['ID1', 'ID2']); assert.deepEqual(receipts, ['ID1', 'ID2']);
// 送り直しは同じ2件の番号を返し、増やさない
assert.deepEqual(JSON.parse(JSON.stringify(ctx.receive_(req))), { ok: true, id: 'ID1', back_id: 'ID2' });
assert.equal(saved.length, 2);
// 帰りの選択が古い・違うときは、どちらも保存しない
assert.equal(ctx.receive_({ ...req, req_key: 'split-2', back_quote_token: 'bad' }).error, 'selection_changed');
assert.equal(ctx.receive_({ ...req, req_key: 'split-3', back_quote_token: 'bad' }).leg, 'back');
assert.equal(saved.length, 2);
// 行きの候補の署名を帰りに使い回せない
assert.equal(ctx.receive_({ ...req, req_key: 'split-4', back_partner_id: go.id, back_quote_token: go.token, back_quote_expires: go.expires }).ok, false);

// 会社あての文面：区間ともう片方の受付番号
const r0 = {}; H.forEach((h, i) => { r0[h] = saved[0][i]; });
assert.ok(ctx.rideText_(r0).includes('■ 区間：行き（往復の1/2）。帰りは別のご依頼です（受付番号 ID2）'));
assert.equal(ctx.legTag_(r0), '・行き');
console.log('PASS: round trip split into go/back legs with separate companies, signed per leg, saved as two linked one-way requests');
