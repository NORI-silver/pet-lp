// 会社ごとの条件の確かめ（checks_）：分かっている「できない」は候補から外し、分からない条件は引き受けのときに確かめる
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'), ctx);
const blank = { id:'PX', riders:null, pets:null, big:null, luggage:null, cageMust:'', cageLend:null, careTri:null, careOk:true, hours:'', rideHours:'', maxKg:null, maxBig:null, lendKg:null, petOnly:null, vacMust:null };
const at = h => new Date(Date.UTC(2026, 11, 1, h - 9, 0));
const req = (o = {}) => ({ '希望日時': at(10), '同乗人数':'1人', 'ペット数':1, '体重kg':5, 'キャリー':'持ち込む', '介助':'不要', '荷物':'手荷物くらい', ...o });
const pets = a => JSON.stringify(a);

// 小型犬1匹・昼・飼い主1人なら、確かめることはない
assert.equal(JSON.stringify(ctx.checks_(blank, req())), '{"ng":[],"ask":[]}');
// 送迎できる時間：分かっていれば外す、分からなければ確かめる
assert.ok(ctx.checks_({ ...blank, rideHours:'8-18' }, req({ '希望日時': at(21) })).ng[0].includes('21:00'));
assert.ok(ctx.checks_(blank, req({ '希望日時': at(21) })).ask[0].includes('21:00'));
// 大型犬：kg の上限・頭数・人数との組み合わせ
const two = req({ 'ペット数':2, '体重kg':38, '同乗人数':'2人', 'ペットJSON': pets([{weight:'38'},{weight:'30'}]) });
assert.ok(ctx.checks_({ ...blank, maxKg:35 }, two).ng.some(x => x.includes('38kg')));
assert.ok(ctx.checks_({ ...blank, big:false }, two).ng.includes('大型犬'));
const a2 = ctx.checks_(blank, two).ask.join('\n');
assert.ok(a2.includes('38kgの子が乗れる') && a2.includes('大型犬2頭が一緒') && a2.includes('大型犬2頭と大人2人') && a2.includes('2匹が一緒'));
assert.ok(ctx.checks_({ ...blank, maxKg:45, maxBig:1 }, two).ng.includes('大型犬2頭'));
// 人数・荷物
assert.ok(ctx.checks_({ ...blank, riders:2 }, req({ '同乗人数':'3人' })).ng.includes('大人3人'));
assert.ok(ctx.checks_({ ...blank, luggage:false }, req({ '荷物':'多め（スーツケース…）' })).ng.includes('荷物が多い'));
// ケージ：貸し出しの大きさ
assert.ok(ctx.checks_({ ...blank, cageLend:true, lendKg:20 }, req({ 'キャリー':'借りたい', '体重kg':30 })).ng[0].includes('30kg'));
assert.ok(ctx.checks_({ ...blank, cageLend:true }, req({ 'キャリー':'借りたい', '体重kg':30 })).ask.some(x => x.includes('30kgの子が入るケージ')));
assert.equal(ctx.checks_({ ...blank, cageLend:true }, req({ 'キャリー':'借りたい', '体重kg':4 })).ask.length, 0);
assert.ok(ctx.checks_(blank, req({ '同乗人数':'2人' })).ask.some(x => x.includes('大人2人')));
assert.ok(ctx.checks_({ ...blank, cageMust:'○' }, req({ 'キャリー':'なし' })).ng.includes('ケージの条件'));
// 介護の中身・ペットだけ・ワクチン
const care = req({ '介助':'必要', 'ペットJSON': pets([{weight:'8', care:'必要', care_need:['寝たきり（担架やマットで運ぶ）'], care_note:'3階'}]) });
assert.ok(ctx.checks_(blank, care).ask.some(x => x.includes('寝たきり') && x.includes('3階')));
assert.ok(ctx.checks_({ ...blank, careTri:false }, care).ng.includes('介護が必要な子'));
assert.ok(ctx.checks_({ ...blank, petOnly:false }, req({ '同乗人数':'0人（ペットだけ）' })).ng.includes('ペットだけの送迎'));
assert.ok(ctx.checks_(blank, req({ '同乗人数':'0人（ペットだけ）' })).ask.some(x => x.includes('ペットだけ')));
assert.equal(ctx.checks_({ ...blank, vacMust:true }, req({ 'ペットJSON': pets([{weight:'5', vaccine:'済'}]) })).ask.length, 0);
assert.ok(ctx.checks_({ ...blank, vacMust:true }, req({ 'ペットJSON': pets([{weight:'5'}]) })).ask[0].includes('ワクチン'));
// 割増の境目の近く（東京・世田谷の会社は18時から）
assert.ok(ctx.checks_({ ...blank, id:'P002', rideHours:'0-24' }, req({ '希望日時': at(17) })).ask.some(x => x.includes('割増')));
assert.equal(ctx.checks_({ ...blank, id:'P002', rideHours:'0-24' }, req({ '希望日時': at(14) })).ask.length, 0);
// 軽バンは大型犬2頭まで・20〜29kgは聞かない・30kg以上は確かめる（Nori 2026-10-31）
const van = { ...blank, car:'軽バン（スズキ エブリイ）' };
const big = (kgs, o = {}) => req({ 'ペット数':kgs.length, '体重kg':Math.max(...kgs), 'ペットJSON': pets(kgs.map(k => ({ weight:String(k) }))), ...o });
assert.ok(!ctx.checks_(van, big([25, 22])).ask.some(x => /kgの子が乗れる|頭が一緒/.test(x)));
assert.ok(ctx.checks_(van, big([30, 25, 22])).ng.some(x => x.includes('軽バンは2頭まで')));
assert.ok(ctx.checks_(van, big([32])).ask.includes('32kgの子が乗れる'));
assert.ok(ctx.checks_(blank, big([25, 22])).ask.includes('大型犬2頭が一緒に乗れる')); // 車が分からない会社は確かめる
assert.ok(ctx.checks_(van, big([28], { 'キャリー':'どれでも' })).ask.some(x => x.includes('28kgの子が入る大きさのケージ')));
// 引き受け画面：確かめることの数だけチェック欄が出る
assert.equal((ctx.askBoxes_(blank, two).match(/type="checkbox"/g) || []).length, ctx.checks_(blank, two).ask.length);
assert.equal(ctx.askBoxes_(blank, req()), '');
console.log('PASS: per-company checks exclude known mismatches and turn unknowns into checkboxes the company must confirm');
