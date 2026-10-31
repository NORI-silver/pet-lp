// 表示だけの会社（tools/display_companies.json）はカードに出るが、予約の依頼は送れない（Nori 2026-10-31）
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const call = (fn,...args) => JSON.parse(JSON.stringify(ctx[fn](...args)));
ctx.sign_ = s => crypto.createHmac('sha256','test-secret').update(s).digest('hex');
ctx.Utilities = { formatDate(d) { return new Date(d.getTime()+9*3600000).toISOString().slice(0,16); } };
ctx.CONFIG.DEFAULT_PARTNER_HOURS='0-24';
ctx.PropertiesService={getScriptProperties:()=>({getProperty:()=>null,setProperty(){}})};
const disp = ctx.DISPLAY_COMPANIES;
assert.ok(disp.length >= 30, '掲載候補が入っている');
assert.ok(!JSON.stringify(disp).match(/@|\d{2,4}-\d{2,4}-\d{3,4}/), '連絡先は入れない');
const D = disp.find(c => c.areas.includes('東京')).id;
const partner = (id,extra={}) => ({id,name:'確認用 '+id,areas:['東京'],active:true,email:'test@example.invalid',careOk:true,big:true,luggage:true,riders:3,pets:5,cageMust:'不要',cageLend:true,lead:3,hours:'0-24',car:'ワンボックス',...extra});
// 提携先シートに同じIDの行があっても、表示だけの会社には送らない
const partners=[partner('P002'),partner(D)];
ctx.partners_ = () => partners;
const point = {lat:35.63,lng:139.66};
const when = new Date(Date.now()+48*3600000+9*3600000).toISOString().slice(0,10)+'T12:00';
const p={pref:'東京都',pickup:'世田谷区',dropoff:'目黒区',datetime:when,trip:'片道',riders:'2人',luggage:'少なめ',species:'犬',weight:'5',cage:'持っている',care:'不要',pet_count:'1',pets_json:'[]',route_details:JSON.stringify({km:10,backKm:10,from:point,to:point,backFrom:point,backTo:point})};
let cards=call('selectionQuotes_',p).cards;
assert.equal(cards[0].id,'P002');
assert.ok(!cards[0].display_only);
const shown=cards.filter(c=>c.display_only);
assert.equal(shown.length, disp.filter(c=>c.areas.includes('東京')).length);
shown.forEach(c=>{ assert.equal(c.token,undefined); assert.equal(c.review,null); assert.equal(c.price.amount,null); });
assert.equal(cards.filter(c=>c.id===D).length,1);
assert.ok(cards.find(c=>c.id===D).display_only);
// 依頼しようとしても断る（トークンを作っても）
const exp=Date.now()+60000;
assert.equal(call('validateSelection_',{...p,partner_id:D,quote_expires:String(exp),quote_token:ctx.quoteSignature_(p,D,exp,{amount:null,text:'料金はお見積もり',night:''})}).error,'selection_unavailable');
// 一斉のお知らせにも入らない
const r={...ctx.selectionRide_(p)};
assert.deepEqual(call('pickPartners_',r,1).map(x=>x.id),['P002']);
// 往復の行き・帰りの候補には出さない
const round={...p,trip:'往復',return_datetime:when.replace('12:00','15:00'),return_pickup:p.dropoff,return_dropoff:p.pickup};
const q=call('selectionQuotes_',round);
assert.ok(!q.legs.go.some(c=>c.display_only) && !q.legs.back.some(c=>c.display_only));
// スイッチを切ると今の提携先だけに戻る
ctx.CONFIG.SHOW_ALL_CANDIDATES=false;
assert.deepEqual(call('selectionQuotes_',p).cards.map(c=>c.id),['P002']);
console.log('display-only ok', shown.length);
