// 全社準備中のあいだも、受け付けを始めた会社（CONFIG.OPEN_PARTNERS）にだけは問い合わせを送れる（Nori 2026-11-08「aiaiはOPENにしていい」）
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite,isNaN,
  PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'secret'})},
  Session:{getEffectiveUser:()=>({getEmail:()=>'admin@example.com'})},
  Utilities:{computeHmacSha256Signature:(s,k)=>[...crypto.createHmac('sha256',k).update(s).digest()],base64EncodeWebSafe:(b)=>Buffer.from(b).toString('base64').replace(/\+/g,'-').replace(/\//g,'_')}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
vm.runInContext("CONFIG.ADMIN_EMAIL='admin@example.com'; liveSending_=function(){return false;}",ctx);
assert.equal(vm.runInContext('CONFIG.SHOW_ALL_CANDIDATES',ctx),true);
assert.equal(ctx.isOpen_('P060'),true); assert.equal(ctx.isOpen_('P061'),true); assert.equal(ctx.isOpen_('P030'),true); assert.equal(ctx.isOpen_('P062'),true); assert.equal(ctx.isOpen_('P053'),false); assert.equal(ctx.isOpen_('P002'),false);
assert.equal(ctx.openDisplay_('P060').id,'D13b7c6f');
assert.equal(ctx.isAnon_('P060',''),false); assert.equal(ctx.isAnon_('P002',''),true);
const row=(ids)=>({'指定した提携先ID':ids,'お名前':'山田','メール':'a@b.jp'});
assert.equal(ctx.isTest_(row('P060')),false);       // aiaiだけあては、B1が止めるでも会社に送る
assert.equal(ctx.isTest_(row('P060,P002')),true);   // ほかの会社が混ざれば送らない
assert.equal(ctx.isTest_(row('P002')),true);
assert.equal(ctx.isTest_(row('')),true);
assert.ok(vm.runInContext("openDisplayIds_().indexOf('D13b7c6f')>=0",ctx)); // 表示だけのカードとは重ねない
console.log('PASS: only OPEN_PARTNERS can receive inquiries while every other company stays in preparation');
// ペッタク：遠くから広島周辺へ送るときは、お迎えに向かう距離の料金をとらない（freeToShopKm）
{
  const c=vm.runInContext("DISPLAY_COMPANIES.filter(function(x){return x.id==='D225080e';})[0]",ctx);
  assert.equal(c.fare.pick.freeToShopKm,80);
  const route=(from,to,km)=>JSON.stringify({km,backKm:km,from,to,backFrom:to,backTo:from});
  const okayama={lat:34.665,lng:133.918}, hiro={lat:34.39,lng:132.46}, kurashiki={lat:34.585,lng:133.772};
  const base={trip:'片道',datetime:'2026-12-01T10:00',pickup:'岡山市',dropoff:'広島市',weight:5,pet_count:1};
  const toHome=ctx.displayPriceCalc_(c,Object.assign({},base,{route_details:route(okayama,hiro,160)}));
  const away=ctx.displayPriceCalc_(c,Object.assign({},base,{dropoff:'倉敷市',route_details:route(okayama,kurashiki,20)}));
  assert.ok(toHome && toHome.local.pickup===0, 'pickup should be free when heading to Hiroshima');
  assert.ok(away && away.local.pickup>0, 'pickup is charged otherwise');
}
console.log('PASS: Pettaku pickup leg is free when bringing a pet from afar to Hiroshima');
// 長距離（渋谷→広島 約805km）：受け付けを始めた会社は計算する、表示だけの会社は「お見積もり」のまま
{
  const route=(from,to,km)=>JSON.stringify({km,backKm:km,from,to,backFrom:to,backTo:from});
  const shibuya={lat:35.658,lng:139.701}, hiro={lat:34.39,lng:132.46};
  const p={trip:'片道',datetime:'2026-12-01T08:30',pickup:'渋谷駅',dropoff:'広島市',weight:5,pet_count:1,route_details:route(shibuya,hiro,805)};
  const pettaku=vm.runInContext("DISPLAY_COMPANIES.filter(function(x){return x.id==='D225080e';})[0]",ctx);
  const r=ctx.displayPriceCalc_(pettaku,p);
  assert.ok(r && r.local.pickup===0 && r.amount>100000, 'Pettaku long-distance estimate');
  const other=vm.runInContext("DISPLAY_COMPANIES.filter(function(x){return x.fare && !x.long;})[0]",ctx);
  assert.equal(ctx.displayPriceCalc_(other,p), null);
  console.log('PASS: long trips are priced only for open partners ('+r.amount+'円)');
}
// 長距離は長距離を受けている会社だけ（Nori 2026-11-08）：aiai（札幌）は対応地域に長距離がないので「お見積もり」
{
  const route=(from,to,km)=>JSON.stringify({km,backKm:km,from,to,backFrom:to,backTo:from});
  const aiai=vm.runInContext("DISPLAY_COMPANIES.filter(function(x){return x.id==='D13b7c6f';})[0]",ctx);
  const sapporo={lat:43.068,lng:141.351}, aomori={lat:40.822,lng:140.747};
  assert.ok(!aiai.long);
  assert.equal(ctx.displayPriceCalc_(aiai,{trip:'片道',datetime:'2026-12-01T08:30',pickup:'札幌駅',dropoff:'青森市',weight:5,pet_count:1,route_details:route(sapporo,aomori,420)}), null);
  console.log('PASS: companies without long-distance service stay "お見積もり" beyond 250km');
}
// 長距離で割合の夜間割増の会社は、夜に走る分だけにかける（Nori 2026-11-08「そうしよう」）
{
  const route=(from,to,km)=>JSON.stringify({km,backKm:km,from,to,backFrom:to,backTo:from});
  const c=vm.runInContext("DISPLAY_COMPANIES.filter(function(x){return x.long && x.fare && x.fare.night && x.fare.night.rate;})[0]",ctx);
  const p={trip:'片道',datetime:'2026-12-01T08:30',pickup:'渋谷駅',dropoff:'広島市',weight:5,pet_count:1,route_details:route({lat:35.658,lng:139.701},{lat:34.39,lng:132.46},923)};
  const r=ctx.displayPriceCalc_(c,p);
  assert.ok(r && r.local.nightExtra>0 && r.local.nightExtra < Math.floor(r.local.ride*c.fare.night.rate), 'night extra only for the night part');
  console.log('PASS: long trips apply a percentage night surcharge only to the night part');
}
