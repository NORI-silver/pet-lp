// 複数社に予約・見積もりを依頼する（Nori 2026-10-31「複数社に予約、および見積もり依頼できるように。どちらかはユーザが選ぶ」）
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const ctx = vm.createContext({ Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs', 'utf8'), ctx);
ctx.sign_ = s => crypto.createHmac('sha256', 'test-secret').update(s).digest('hex');
ctx.Utilities = { formatDate(d) { return new Date(d.getTime() + 9 * 3600000).toISOString().slice(0, 16); } };
ctx.CONFIG.SHOW_ALL_CANDIDATES = false;
ctx.CONFIG.DEFAULT_PARTNER_HOURS = '0-24';
ctx.PropertiesService = { getScriptProperties: () => ({ getProperty: () => null, setProperty() {} }) };
const partner = (id) => ({ id, name: '確認用 ' + id, areas: ['東京'], active: true, email: 'test@example.invalid', careOk: true, big: true, luggage: true, riders: 3, pets: 5, cageMust: '不要', cageLend: true, lead: 3, hours: '0-24', car: 'ワンボックス' });
const partners = [partner('P002'), partner('P003')];
ctx.partners_ = () => partners;
ctx.partnerById_ = id => partners.find(x => x.id === id);
const A = { lat: 35.63, lng: 139.66 }, B = { lat: 35.64, lng: 139.70 };
const day = new Date(Date.now() + 48 * 3600000 + 9 * 3600000).toISOString().slice(0, 10);
const base = { pref: '東京都', pickup: '世田谷区', dropoff: '目黒区', datetime: day + 'T10:00', trip: '片道', riders: '1人', luggage: '少なめ', species: '犬', weight: '8',
  cage: '持ち込む', care: '不要', pet_count: '1', pets_json: '[]', name: 'テスト', tel: '000', email: 'c@example.invalid', contact: 'メール',
  route_details: JSON.stringify({ km: 8, backKm: 8, from: A, to: B, backFrom: B, backTo: A }) };
const cards = JSON.parse(JSON.stringify(ctx.selectionQuotes_(base))).cards;
assert.equal(cards.length, 2);
const picks = JSON.stringify(cards.map(c => ({ id: c.id, token: c.token, expires: c.expires })));

let rows = [], mails = [], delivered = [];
ctx.LockService = { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) };
ctx.CacheService = { getScriptCache: () => ({ get: () => null, put() {} }) };
ctx.SpreadsheetApp = { flush() {} };
ctx.sheet_ = () => ({ appendRow: row => rows.push(row), getLastRow: () => rows.length + 1, getRange: () => ({ setNumberFormat() {} }) });
ctx.ensureReqHeaders_ = () => ctx.REQ_HEADERS;
let n = 0; ctx.newId_ = () => 'ID' + (++n);
ctx.sendReceipt_ = () => {}; ctx.notifyAdmin_ = () => {}; ctx.adminUrl_ = () => ''; ctx.log_ = () => {}; ctx.bumpCount_ = () => {};
const H = ctx.REQ_HEADERS;
const obj = row => Object.fromEntries(H.map((h, i) => [h, row[i]]));
ctx.findReq_ = id => { const i = rows.findIndex(r => obj(r)['受付番号'] === id); return i < 0 ? null : { rowIndex: i, data: obj(rows[i]) }; };
ctx.setReq_ = (i, o) => { Object.keys(o).forEach(k => { rows[i][H.indexOf(k)] = o[k]; }); };
ctx.toCustomer_ = (r, subject, text) => mails.push({ subject, text });
ctx.deliver_ = (pt, subject) => { delivered.push(pt.id + ' ' + subject); return 'auto'; };
ctx.sendWave_ = id => 'x';

// 予約依頼を2社に：引き受けたお返事が届き、お客さまが1社選んだ時点で決まる。もう1社には締め切りを知らせる（Nori 2026-10-31「お客さまがあとで1社選ぶ」）
const at = new Date(Date.now() + 48 * 3600000);
ctx.page_ = (t) => t;
let res = ctx.receive_({ ...base, picks, mode: 'book' });
assert.equal(res.ok, true);
let r = obj(rows[0]);
assert.equal(r['指定した提携先ID'], 'P002,P003'); assert.equal(r['依頼の種類'], '予約');
assert.equal(ctx.needsChoice_(r), true);
rows[0][H.indexOf('通知した提携先')] = 'P002,P003'; // sendWave_ が記録するもの
const ak = id => ctx.sign_('ID1:' + id);
assert.equal(ctx.acceptPage_({ id: 'ID1', p: 'P003', k: ak('P003'), go: '1', fare: '5000', at: day + 'T10:00' }), '引き受けのお返事を送りました');
assert.equal(obj(rows[0])['状態'], ctx.ST.OPEN, '引き受けただけでは決まらない');
assert.ok(mails.some(m => m.subject.includes('引き受けのお返事が届きました')));
assert.equal(ctx.choosePage_({ id: 'ID1', p: 'P003', k: ctx.sign_('ID1:P003:choose'), go: '1' }), '決まりました');
assert.equal(obj(rows[0])['決定した提携先ID'], 'P003');
assert.ok(delivered.some(d => d.startsWith('P002 【締め切り】')), 'ほかの会社には締め切りを知らせる');
// 1社だけの予約依頼は、今までどおり引き受けた時点で決まる
rows = []; n = 10;
ctx.receive_({ ...base, picks: JSON.stringify([JSON.parse(picks)[0]]), mode: 'book' });
assert.equal(ctx.needsChoice_(obj(rows[0])), false);

// 見積もり依頼：会社の見積もりはお客さまに届くだけで決まらない。お客さまが選んだら決まる
rows = []; mails = []; delivered = []; n = 0;
res = ctx.receive_({ ...base, picks, mode: 'quote', req_key: '' });
assert.equal(res.ok, true);
const id = res.id;
assert.equal(obj(rows[0])['依頼の種類'], '見積もり');
assert.equal(ctx.quote_(id, partners[0], at, 4800, '', '', '').ok, true);
assert.equal(ctx.quote_(id, partners[1], at, 5200, '', '', '').ok, true);
assert.equal(obj(rows[0])['状態'], ctx.ST.OPEN, '見積もりだけでは決まらない');
assert.equal(ctx.quotesOf_(obj(rows[0])).length, 2);
assert.ok(mails.filter(m => m.subject.includes('お見積もりが届きました')).length === 2);
assert.ok(mails[0].text.includes('a=choose'), 'この会社に決めるリンク');
assert.ok(!mails[0].text.includes('c@example.invalid'));
const k = ctx.sign_(id + ':P002:choose');
assert.equal(ctx.choosePage_({ id, p: 'P002', k: 'bad' }), 'リンクが正しくありません');
assert.equal(ctx.choosePage_({ id, p: 'P002', k, go: '1' }), '決まりました');
assert.equal(obj(rows[0])['決定した提携先ID'], 'P002');
assert.equal(obj(rows[0])['料金の目安'], 4800);
assert.equal(ctx.quote_(id, partners[1], at, 3000, '', '', '').ok, false, '決まったあとは見積もりを受け付けない');

// 選んでいない会社や6社以上は断る
assert.equal(ctx.receive_({ ...base, picks: JSON.stringify([{ id: 'P999', token: 'x', expires: Date.now() + 60000 }]) }).ok, false);
assert.equal(ctx.receive_({ ...base, picks: JSON.stringify([1,2,3,4,5,6].map(i => ({ id: 'P00' + i, token: 'x', expires: 1 }))) }).ok, false);
console.log('PASS: multi-company booking (first accept wins) and quote requests (customer chooses)');
