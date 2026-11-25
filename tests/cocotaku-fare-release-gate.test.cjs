// Offline evidence: the display calculator can emit precise-looking numbers even
// when the provider's rate for the route is unresolved. Never use those numbers
// as provider-confirmed expected totals in tests for the final booking flow.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const props = {
  KASUKABE_INTAKE_ENABLED:'1', KASUKABE_AUTOMATIC_QUOTE_ENABLED:'1',
  KASUKABE_INTAKE_VERIFIED_EMAIL:'offline-test@pet-taxi-kasukabe.com',
  KYOTO_INTAKE_ENABLED:'1', KYOTO_INTAKE_PARTNER_ID:'P999',
  KYOTO_INTAKE_VERIFIED_EMAIL:'offline-test@example.invalid'
};
const ctx = vm.createContext({PropertiesService:{getScriptProperties:()=>({getProperty:k=>props[k]})}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const day = new Date(Date.now()+48*3600000).toISOString().slice(0,10);
const a = {lat:35.97,lng:139.75}, b = {lat:35.91,lng:139.72};
const p = {pref:'埼玉県',pickup:'埼玉県春日部市テスト町1',dropoff:'埼玉県春日部市テスト町2',
  datetime:day+'T12:00',trip:'片道',weight:'5',riders:'1人',species:'犬',pet_count:'1',cage:'持ち込む',care:'不要',
  pets_json:JSON.stringify([{species:'犬',weight:'5',cage:'持ち込む',care:'不要',vaccine:'済',rabies:'済'}])};
const kas = {id:'P014',name:'COCOタク 春日部店',active:true,email:props.KASUKABE_INTAKE_VERIFIED_EMAIL};
const kyo = {id:'P999',name:'COCOタク 京都店',active:true,petOnly:false,email:props.KYOTO_INTAKE_VERIFIED_EMAIL};
const find = id => ctx.DISPLAY_COMPANIES.find(x=>x.id===id);
assert.equal(ctx.COCOTAKU_INTAKE_INTEGRATION_READY,false,'keep automatic booking disabled until branch tariffs are confirmed');
for (const pickup of [29.5,30,30.5]) {
  ctx.roadKm_=()=>pickup;
  const q={...p,route_details:JSON.stringify({km:10,backKm:10,from:a,to:b})};
  assert.ok(ctx.displayPrice_(find('D853ae97'),q).amount > 0,'document a current display-price output, not a confirmed rate');
  assert.equal(ctx.selectionPrice_(kas,q).amount,null,'never pass the unresolved display price into checkout');
}
ctx.roadKm_=()=>35;
const q={...p,pref:'京都府',pickup:'京都府京都市テスト町1',dropoff:'京都府京都市テスト町2',
  route_details:JSON.stringify({km:32,backKm:32,highKm:32,highBackKm:32,from:a,to:b})};
assert.ok(ctx.displayPrice_(find('D7f0d2a2'),q).highway.amount>0,'current display omits the unknown highway deadhead cost');
assert.equal(ctx.selectionPrice_(kyo,q),null);
assert.equal(ctx.isOpen_('P999'),false);
console.log('PASS: unconfirmed Kasukabe threshold and Kyoto highway fare cannot become automatic booking rates through configuration alone');
