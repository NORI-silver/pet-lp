// 送迎のあとの確認（Nori 2026-11-01「キャンセルを直接事業者に伝えられたら、こっちは判断できない」）
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs', 'utf8'), ctx);
ctx.sign_ = s => crypto.createHmac('sha256', 'test-secret').update(s).digest('hex');
ctx.Utilities = { formatDate(d, tz, f) { const j = new Date(d.getTime() + 9 * 3600000); return f === 'H' ? String(j.getUTCHours()) : j.toISOString().slice(0, 16); } };
const H = 3600000;
const noonJst = Date.UTC(2026, 10, 2, 3, 0); // 2026-11-02 12:00 JST
const r = (o = {}) => ({ '状態': '決定', 'メール': 'a@example.invalid', 'お迎え予定': new Date(noonJst - 20 * H), '送迎確認': '', ...o });
assert.equal(ctx.rideCheckDue_(r(), noonJst), true);
assert.equal(ctx.rideCheckDue_(r({ '送迎確認': '確認中' }), noonJst), false); // 2回は聞かない
assert.equal(ctx.rideCheckDue_(r({ '状態': '取り消し' }), noonJst), false); // サイトで取り消した予約には聞かない
assert.equal(ctx.rideCheckDue_(r({ 'お迎え予定': new Date(noonJst - 2 * H) }), noonJst), false); // 早すぎる
assert.equal(ctx.rideCheckDue_(r({ 'お迎え予定': new Date(noonJst - 20 * 24 * H) }), noonJst), false); // 古すぎる
assert.equal(ctx.rideCheckDue_(r(), noonJst - 10 * H), false); // 夜中の2時（JST）には送らない
assert.equal(ctx.rideCheckDue_(r({ 'メール': '' }), noonJst), false);
// ページ：署名が違えば答えを受け付けない
ctx.JSON_PAGE = true;
ctx.ContentService = { createTextOutput: t => ({ setMimeType: () => JSON.parse(t) }), MimeType: { JSON: 'json' } };
let saved = null, admin = null;
ctx.findReq_ = () => ({ rowIndex: 2, data: r({ '送迎確認': '確認中', '決定した提携先': '確認用' }) });
ctx.setReq_ = (i, o) => { saved = o; };
ctx.log_ = () => {};
ctx.notifyAdmin_ = (s) => { admin = s; };
ctx.fmt_ = () => '11/1 16:00';
assert.equal(ctx.ridePage_({ a: 'ride', id: 'PT1', k: 'bad', go: '1', ans: 'cancel' }).title, 'リンクが正しくありません');
assert.equal(saved, null);
const k = ctx.sign_('PT1:ride');
assert.equal(ctx.ridePage_({ a: 'ride', id: 'PT1', k }).title, '無事に送迎できましたか？'); // 開いただけでは記録しない（メールのリンクの先読み対策）
assert.equal(saved, null);
ctx.ridePage_({ a: 'ride', id: 'PT1', k, go: '1', ans: 'cancel' });
assert.equal(saved['送迎確認'], 'キャンセル（お客さま回答）');
assert.match(admin, /キャンセル/);
console.log('ride-check ok');
