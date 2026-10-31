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
// お迎えの都道府県に対応している会社だけ（Nori 2026-10-31「大阪の住所で全国の会社が出た」）。お店が遠すぎる会社も外す
const inT=c=>disp.find(d=>d.id===c.id).areas.includes('東京');
assert.ok(shown.length>0 && shown.every(inT));
assert.equal(shown.length, disp.filter(c=>ctx.displayServes_(c,'東京',point)&&ctx.displayInTime_(c,ctx.selectionRide_(p)['希望日時'],new Date())).length);
shown.forEach(c=>{ assert.equal(c.token,undefined); assert.equal(c.review,null); });
// 料金表がある会社は料金の目安を出す（安い順、お見積もりの会社はあと）
const priced=shown.filter(c=>c.price.amount!=null);
assert.ok(priced.length>=5, '料金つきの会社がある');
const amts=shown.map(c=>c.price.amount==null?Infinity:c.price.amount);
assert.deepEqual(amts,[...amts].sort((a,b)=>a-b));
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
// 大阪のお迎えでは大阪に対応している会社だけ。料金も出る（Nori 2026-10-31）
const sakai={lat:34.573,lng:135.483}, umeda={lat:34.702,lng:135.496};
const osaka=call('selectionQuotes_',{...p,pref:'大阪府',pickup:'堺市堺区',dropoff:'大阪市北区',route_details:JSON.stringify({km:16,backKm:16,from:sakai,to:umeda,backFrom:umeda,backTo:sakai})});
assert.ok(osaka.ok && osaka.cards.length>0 && osaka.cards.every(c=>c.display_only));
assert.ok(osaka.cards.every(c=>disp.find(d=>d.id===c.id).areas.includes('大阪')), osaka.cards.map(c=>c.label).join(','));
assert.ok(!osaka.cards.some(c=>/東京|神奈川|札幌|福岡|広島/.test(disp.find(d=>d.id===c.id).pref)));
assert.ok(osaka.cards.some(c=>c.price.amount>0), '大阪でも料金が出る');
// 料金の計算（決まった式）：COCOタク 東京小平店 3,300円（5kmまで）＋165円/km、お迎え 165円/km（お店から）、回送なし、21〜8時は3,300円
const coco=disp.find(c=>c.id==='D400f012');
const at=(h)=>new Date(Date.now()+48*3600000+9*3600000).toISOString().slice(0,10)+'T'+h;
const shopPt={lat:coco.shop[0],lng:coco.shop[1]}, dest={lat:35.70,lng:139.40};
const rd=(km)=>JSON.stringify({km,backKm:km,from:shopPt,to:dest,backFrom:dest,backTo:shopPt});
let pr=call('displayPrice_',coco,{...p,datetime:at('12:00'),route_details:rd(10)});
assert.equal(pr.local.ride,3300+5*165); assert.equal(pr.local.pickup,0); assert.equal(pr.local.returnFee,0); assert.equal(pr.local.nightExtra,0);
assert.equal(pr.amount,Math.ceil((3300+5*165)/100)*100);
pr=call('displayPrice_',coco,{...p,datetime:at('22:00'),route_details:rd(10)});
assert.equal(pr.local.nightExtra,3300);
// お店から離れた場所のお迎えは迎車代がかかる（直線×1.3を1km単位で切り上げ）
const far={lat:coco.shop[0]+0.05,lng:coco.shop[1]};
pr=call('displayPrice_',coco,{...p,datetime:at('12:00'),route_details:JSON.stringify({km:10,backKm:10,from:far,to:dest,backFrom:dest,backTo:far})});
assert.equal(pr.local.pickup,Math.ceil(ctx.kmBetween_(shopPt,far)*1.3)*165);
// 税抜の料金表は消費税10%を足す
const tx={id:'X',fare:{base:[2000,5],tiers:[[6,null,200]],tax:'税抜'}};
pr=call('displayPrice_',tx,{...p,route_details:rd(10)});
assert.equal(pr.local.ride,Math.ceil(3000*1.1)); assert.ok(/税抜/.test(pr.planNote));
// 料金表がない会社はお見積もり
assert.equal(ctx.displayPrice_({id:'Y'},p),null);
// 営業時間・当日予約でしぼる（Nori 2026-10-31）。日本時間で日時を作る
const J=(d,h)=>new Date(Date.UTC(2026,10,d,h-9,0)); // 2026-11-d h時（11/2は月曜）
const T=(o)=>({hours:'',flex:false,closed:[],lead_days:null,cut:null,...o});
const f=(c,at,now)=>ctx.displayInTime_(T(c),at,now);
assert.equal(f({},J(2,12),J(2,8)),true); // 分からない会社は出す
assert.equal(f({hours:'8-20'},J(3,21),J(2,8)),false); // お迎えが営業時間の外
assert.equal(f({hours:'8-20',flex:true},J(3,21),J(2,8)),true); // 時間外も相談できる会社は出す
assert.equal(f({closed:[1]},J(2,12),J(1,8)),false); // 月曜定休
assert.equal(f({lead_days:1},J(2,15),J(2,9)),false); // 前日までの会社は当日に出さない
assert.equal(f({lead_days:1},J(3,15),J(2,9)),true);
assert.equal(f({lead_days:3},J(4,15),J(2,9)),false); // 3日前まで
assert.equal(f({lead_days:0,cut:16},J(2,20),J(2,17)),false); // 当日予約は16時まで
assert.equal(f({lead_days:0,cut:16},J(2,20),J(2,13)),true);
assert.equal(f({hours:'8-19'},J(2,23),J(2,20)),false); // 当日：今日の営業が終わっている
assert.equal(f({hours:'8-20'},J(2,12),J(2,7)),true); // 当日：8時に開いて12時のお迎えは間に合う
assert.equal(f({hours:'8-20'},J(2,10),J(2,6)),false); // 当日：8時に開いてから10時のお迎えまで3時間ない
assert.equal(f({hours:'0-24'},J(2,23),J(2,20)),true);
// スイッチを切ると今の状態（提携先だけ・依頼できる）に戻る。表示だけの会社は同じIDがシートにあっても送らない
ctx.CONFIG.SHOW_ALL_CANDIDATES=false;
const back=call('selectionQuotes_',p).cards;
assert.deepEqual(back.map(c=>c.id),['P002']);
assert.equal(call('selectionQuotes_',{...p,pref:'大阪府'}).error,'area'); assert.ok(!back[0].display_only && back[0].token);
assert.deepEqual(call('pickPartners_',r,1).map(x=>x.id),['P002']);
const q=call('selectionQuotes_',round);
assert.ok(q.legs && !q.legs.go.some(c=>c.id===D));
console.log('display-only ok', shown.length);
