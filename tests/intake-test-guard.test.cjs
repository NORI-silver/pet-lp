const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const context = vm.createContext({});
vm.runInContext(fs.readFileSync('booking/Code.gs', 'utf8'), context);
context.json_ = (obj) => obj;
const effects = [];
const forbidden = (kind) => () => { effects.push(kind); throw Error(kind); };
context.log_ = forbidden('log');
context.notifyAdmin_ = forbidden('admin');
context.sendReceipt_ = forbidden('receipt');
context.sendWave_ = forbidden('wave');
context.LockService = { getScriptLock: forbidden('lock') };
context.sheet_ = forbidden('sheet');
context.CONFIG.TEST_MODE = false;

const request = {
  pref: '東京', pickup: '見本駅', dropoff: '見本動物病院', datetime: '2099-12-11T14:45',
  trip: '片道', species: '猫', weight: '100', cage: '持っている', care: '不要',
  riders: '1人', email: 'fixture@example.invalid', contact: 'メール'
};
const post = (fields) => context.doPost({parameter: {...request, ...fields}});
for (const [name, tel] of [['TESｔ', '00000000000'], [' ＴＥＳＴ　', '０0０-００００-００００'], ['Test', '0000000000']]) {
  const result = post({name, tel});
  assert.equal(result.ok, false);
  assert.equal(result.error, 'invalid_phone');
}
assert.deepEqual(effects, [], 'the public POST never locks, saves, logs, or queues a notification, even if a signed quote is omitted');
assert.equal(post({name:'TEST', tel:'00000000000', trip:'往復', split:'1', partner_id:'fixture', quote_token:'fixture', quote_expires:'4000000000'}).error, 'invalid_phone');
assert.deepEqual(effects, [], 'both legs are blocked before request creation');

const row = (name, tel, email = 'fixture@example.invalid') => ({'お名前':name, '電話番号':tel, 'メール':email, 'お客さまLINE':'fixture-line'});
context.CONFIG.LINE_CHANNEL_ACCESS_TOKEN = 'fixture-not-secret';
context.liveSending_ = () => true;
context.pickedIds_ = () => [];
context.adminEmail_ = () => 'sink@example.invalid';
context.mail_ = (to) => { effects.push(to); return true; };
context.linePush_ = (to) => { effects.push(to); return true; };
context.footer_ = () => '';
const partner = {email:'partner@example.invalid', lineId:'partner-fixture-line'};
const oldDummy = row('TESｔ', "'00000000000");
assert.equal(context.isTest_(oldDummy), true);
assert.equal(context.deliver_(partner, 'request', '', oldDummy), false);
assert.equal(context.deliver_(partner, 'close', '', oldDummy), false);
context.toCustomer_(oldDummy, 'receipt or close', '');
assert.deepEqual(effects, [], 'any already-saved dummy row is silent on both sides');
assert.equal(context.isTest_(row('Test', '09012345678')), false, 'an actual name Test is not blocked');
assert.equal(context.isTest_(row('テスト 花子','00000000000')), true, 'existing intentional demo stays routed to operator');
assert.equal(context.deliver_(partner, 'demo', '', row('テスト 花子','00000000000')), 'auto');
assert.deepEqual(effects.splice(0), ['sink@example.invalid']);
assert.equal(context.isTest_(row('担当者','09000000000','sink@example.invalid')), true, 'operator email path unchanged');
assert.equal(context.deliver_(partner, 'normal', '', row('Test', '09012345678')), 'auto');
assert.deepEqual(effects.splice(0), ['partner-fixture-line']);
assert.equal(context.isDummyPublicIntake_('山田', '00000000000'), false, 'an ambiguous single signal is unchanged');
assert.equal(context.isDummyPublicIntake_('テスト 花子', '00000000000'), false);
console.log('PASS: dummy booking POST is silent; old dummy outbox is silent; genuine and deliberate sandbox paths unchanged.');
