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
assert.ok(disp.length >= 70, '全国の掲載候補が入っている');
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
// 全社準備中：提携先の会社もトークンなし・表示だけ（料金の目安は出す）
assert.ok(cards[0].display_only); assert.equal(cards[0].token,undefined); assert.equal(cards[0].price.amount,4000);
assert.ok(cards.every(c=>c.display_only && c.token===undefined));
const shown=cards.filter(c=>c.id!=='P002');
assert.equal(shown.length, disp.length); // 絞らない
const nTokyo=disp.filter(c=>c.areas.includes('東京')).length;
assert.ok(shown.slice(0,nTokyo).every(c=>disp.find(d=>d.id===c.id).areas.includes('東京'))); // 対応していそうな会社が先
shown.forEach(c=>{ assert.equal(c.token,undefined); assert.equal(c.review,null); assert.equal(c.price.amount,null); });
assert.equal(cards.filter(c=>c.id===D).length,1);
// 提携先の会社に正しいトークンを作って依頼しても断る
const exp0=Date.now()+60000;
const price0=ctx.selectionPrice_(partners[0],p);
assert.equal(call('validateSelection_',{...p,partner_id:'P002',quote_expires:String(exp0),quote_token:ctx.quoteSignature_(p,'P002',exp0,price0)}).error,'selection_unavailable');
// 依頼しようとしても断る（トークンを作っても）
const exp=Date.now()+60000;
assert.equal(call('validateSelection_',{...p,partner_id:D,quote_expires:String(exp),quote_token:ctx.quoteSignature_(p,D,exp,{amount:null,text:'料金はお見積もり',night:''})}).error,'selection_unavailable');
// 一斉のお知らせにも、どの会社も入らない
const r={...ctx.selectionRide_(p)};
assert.deepEqual(call('pickPartners_',r,1).map(x=>x.id),[]);
assert.deepEqual(call('pickPartners_',r,2).map(x=>x.id),[]);
// 往復の行き・帰りを別の会社にする候補は出さない
const round={...p,trip:'往復',return_datetime:when.replace('12:00','15:00'),return_pickup:p.dropoff,return_dropoff:p.pickup};
assert.equal(call('selectionQuotes_',round).legs,undefined);
// 全国のお迎えでも候補を出す（Nori「全国にして」）。依頼はできない
const osaka=call('selectionQuotes_',{...p,pref:'大阪府'});
assert.ok(osaka.ok && osaka.cards.length>=disp.length && osaka.cards.every(c=>c.display_only));
// スイッチを切ると今の状態（提携先だけ・依頼できる）に戻る。表示だけの会社は同じIDがシートにあっても送らない
ctx.CONFIG.SHOW_ALL_CANDIDATES=false;
const back=call('selectionQuotes_',p).cards;
assert.deepEqual(back.map(c=>c.id),['P002']);
assert.equal(call('selectionQuotes_',{...p,pref:'大阪府'}).error,'area'); assert.ok(!back[0].display_only && back[0].token);
assert.deepEqual(call('pickPartners_',r,1).map(x=>x.id),['P002']);
const q=call('selectionQuotes_',round);
assert.ok(q.legs && !q.legs.go.some(c=>c.id===D));
console.log('display-only ok', shown.length);
