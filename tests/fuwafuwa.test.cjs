// 公開停止した事業者が候補から外れても、既存予約用の参照は失われない。
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const ctx = vm.createContext({ Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs', 'utf8'), ctx);
const pid = 'P066', did = 'D5598693';
const partner = id => ({id, name:'確認用事業者', active:true, email:'test@example.invalid', areas:['神奈川']});
const existing = partner(pid), other = partner('P099');
ctx.partners_ = () => [existing, other];
ctx.fitsCar_ = ctx.fitsCage_ = ctx.inTime_ = ctx.reachable_ = ctx.openNear_ = () => true;
ctx.checks_ = () => ({ng:[], ask:[]});
ctx.sign_ = s => require('node:crypto').createHash('sha256').update(s).digest('hex').slice(0, 24);
const ids = list => Array.from(list, x => x.id);
const ride = {'都府県':'神奈川','介助':'不要'};
for (const showAll of [true, false]) {
  ctx.CONFIG.SHOW_ALL_CANDIDATES = showAll;
  assert.deepEqual(ids(ctx.selectionCandidates_(ride)), ['P099']);
  assert.ok(!ids(ctx.pickPartners_(ride, 1)).includes(pid));
  assert.equal(ctx.validateSelection_({partner_id:pid}).error, 'selection_unavailable');
}
assert.ok(!ctx.isOpen_(pid) && !ctx.openDisplay_(pid));
assert.ok(!ctx.DISPLAY_COMPANIES.some(c => c.id === did));
assert.equal(ctx.demoId_(ctx.demoToken_(pid)), '');
assert.equal(ctx.demoId_(ctx.demoToken_(did)), '');
assert.equal(ctx.pconfOf_(did), null);
assert.ok(!ctx.pinfoOpen_(pid));
assert.equal(ctx.reviewTarget_(pid), null);
assert.equal(ctx.reviewTarget_(did), null);
assert.equal(ctx.partnerById_(pid), existing);
assert.equal(ctx.partnerById_(other.id), other);
const browser = fs.readFileSync('app.js', 'utf8');
const list = JSON.parse(browser.match(/\/\*PUBLIC_PAUSE\*\/var PUBLIC_PAUSE = (.*?);/)[1]);
assert.deepEqual(list, [did,pid]);
assert.ok(browser.includes('result.cards = visible(result.cards)'));
assert.ok(browser.includes('go:visible(result.legs.go), back:visible(result.legs.back)'));
console.log('PASS: suspended listing is absent across public candidate, selection, demo, review and partner-info paths; existing partner lookup remains intact');
