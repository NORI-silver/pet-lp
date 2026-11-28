const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const source = fs.readFileSync('booking/Code.gs', 'utf8');
const ctx = vm.createContext({Date, JSON});
vm.runInContext(source, ctx);
const quote = {pid:'supplier-a', at:Date.UTC(2026, 10, 27), time:Date.UTC(2026, 10, 23), fare:7920};
const row = quotes => ({'受付番号':'TEST', '依頼の種類':'問い合わせ', '状態':ctx.ST.OPEN,
  '指定した提携先ID':'supplier-a', '指定した提携先':'テスト事業者', '見積もりJSON':JSON.stringify(quotes)});
function close(r) {
  const sent = { customer: [], admin: [], writes: [], partners: [] };
  Object.assign(ctx, {
    LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})}, SpreadsheetApp:{flush(){}},
    findReq_:()=>({rowIndex:2,data:r}),
    setReq_:(i,v)=>{sent.writes.push(v);Object.assign(r,v);}, log_(){},
    closeOthers_:(...args)=>sent.partners.push(args), toCustomer_:(...args)=>sent.customer.push(args),
    notifyAdmin_:(...args)=>sent.admin.push(args), retryUrl_:()=>'/retry', whenText_:()=> '11月27日 9:00',
    rideText_:()=>'', legTag_:()=>''
  });
  ctx.giveUp_('TEST');
  ctx.giveUp_('TEST'); // a completed case does not send again
  return sent;
}
for (const [quotes, subject, admin, body] of [
  [[quote],/予約が確定しないまま/,/見積もりあり・予約未確定/,/会社から空き状況と料金のお返事がありました/],
  [[{...quote,withdrawn:1}],/取り下げられ/,/取り下げ・予約未確定/,/お返事が取り下げられ/],
  [[],/空いている車が見つかりませんでした/,/見つからず/,/ご案内できる.*お返事がありません/],
]) {
  const result = close(row(quotes));
  assert.equal(result.customer.length,1);
  assert.equal(result.partners.length,1);
  assert.equal(result.writes[0]['状態'],ctx.ST.NONE);
  assert.match(result.customer[0][1],subject);
  assert.match(result.customer[0][2],body);
  assert.match(result.admin[0][0],admin);
  if (quotes.length) assert.doesNotMatch(result.customer[0][1]+result.customer[0][2],/車が見つから|お引き受けできませんでした/);
}
for (const state of [ctx.ST.DONE, ctx.ST.CANCEL, ctx.ST.NONE]) {
  assert.equal(close({...row([quote]), '状態':state}).customer.length,0);
}
assert.match(ctx.unbookedOutcome_(row([null])).label,/見つからず/);
console.log('PASS: booked, cancelled and ended untouched; unselected, withdrawn and no offer distinguished');
