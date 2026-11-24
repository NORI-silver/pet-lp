const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict'), crypto = require('node:crypto');
const props = {}, mailbox = 'offline-fixture-do-not-send@pet-taxi-kasukabe.com';
const ctx = vm.createContext({Date, PropertiesService:{getScriptProperties:()=>({getProperty:k=>props[k]})}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
ctx.sign_ = v=>crypto.createHmac('sha256','offline-test').update(v).digest('hex');
ctx.json_ = x=>x;
ctx.Utilities = {formatDate(d) { return new Date(d.getTime()+9*3600000).toISOString().slice(0,16); }};
ctx.CONFIG.DEFAULT_PARTNER_HOURS='0-24';
const pt={id:'P014',name:'春日部テスト用',active:true,areas:['埼玉'],email:mailbox,hours:'0-24',lead:1};
const other={...pt,id:'P030',name:'既存の会社',email:'existing@example.invalid'};
ctx.partners_ = ()=>[pt,other];
ctx.displayCards_=()=>[]; // 公開比較の既存データに依存しない
ctx.demandLog_=()=>{}; // ネットワークや表に一切書かない
ctx.loadRoadKm_=()=>{};
const day=new Date(Date.now()+48*3600000+9*3600000).toISOString().slice(0,10);
const pet={species:'犬',weight:'5',cage:'持ち込む',care:'不要',vaccine:'済',rabies:'済'};
const p={pref:'埼玉県',pickup:'日本、〒344-0000 埼玉県春日部市テスト町1',dropoff:'春日部市テスト町2',datetime:day+'T12:00',trip:'片道',riders:'1人',
 species:'犬',weight:'5',cage:'持ち込む',care:'不要',pet_count:'1',pets_json:JSON.stringify([pet])};
const search=q=>ctx.doPost({parameter:{...q,kind:'quotes'}}).cards;
const find=q=>search(q).find(c=>c.id==='P014');
assert.equal(find(p),undefined);
assert.equal(ctx.isOpen_('P014'),false);
props.KASUKABE_INTAKE_ENABLED='1';
assert.equal(find(p),undefined);
props.KASUKABE_INTAKE_VERIFIED_EMAIL=mailbox;
const card=find(p);
assert.ok(card?.token && card.listed);
assert.equal(card.price.amount,null);
assert.match(card.price.text,/未確定.*会社.*確定料金/);
assert.ok(!JSON.stringify(card).includes(mailbox));
assert.ok(search(p).find(c=>c.id==='P030')?.token);
const choose={...p,partner_id:'P014',quote_token:card.token,quote_expires:String(card.expires)};
assert.equal(ctx.validateSelection_(choose).ok,true);
assert.equal(ctx.validateSelection_({...choose,pickup:'埼玉県春日部市テスト町3'}).error,'selection_changed');
for (const extra of [
 {pickup:'越谷市テスト町'}, {dropoff:'京都府京都市春日部市'}, {pickup:'春日部市'}, {pref:'千葉県'},
 {trip:'往復',return_datetime:day+'T13:00'}, {leg:'go'}, {date:day},
 {wait_time:'10'}, {via:'春日部市テスト町3'}, {datetime:day+'T08:59'}, {datetime:day+'T18:00'},
 {pet_count:'2'}, {riders:'0人（ペットだけ）'}, {riders:'3人'}, {species:'猫'}, {care:'必要'}, {luggage:'多め'},
 {cage:'借りたい'}, {weight:'11',pets_json:JSON.stringify([{...pet,weight:'11'}])},
 {pets_json:JSON.stringify([{...pet,rabies:''}])},{pets_json:JSON.stringify([{...pet,weight:'8'}])},{pets_json:'[]'}]) {
 assert.equal(find({...p,...extra}),undefined,JSON.stringify(extra));
 assert.notEqual(ctx.validateSelection_({...choose,...extra}).ok,true,JSON.stringify(extra));
}
pt.email='different@example.invalid'; assert.equal(find(p),undefined); pt.email=mailbox;
pt.lineId='other-channel'; assert.equal(find(p),undefined); delete pt.lineId;
pt.active=false; assert.equal(find(p),undefined); pt.active=true;
let row, saved=[], targets=[], receiptCount=0;
ctx.LockService={getScriptLock:()=>({waitLock(){},releaseLock(){}})};
ctx.SpreadsheetApp={flush(){}};
ctx.sheet_=()=>({appendRow:values=>{saved.push(values);row={rowIndex:2,data:Object.fromEntries(ctx.REQ_HEADERS.map((h,i)=>[h,values[i]]))};},getLastRow:()=>saved.length+1,getRange:()=>({setNumberFormat(){}})});
ctx.ensureReqHeaders_=()=>ctx.REQ_HEADERS;
ctx.newId_=()=> 'OFFLINE-FIXTURE';
ctx.sendReceipt_=()=>{receiptCount++;};ctx.notifyAdmin_=()=>{};ctx.isTest_=()=>true;
ctx.rideText_=()=>'';ctx.whenText_=()=>'';ctx.adminUrl_=()=>'';ctx.log_=()=>{};
ctx.findReq_=()=>row;ctx.setReq_=(_,values)=>Object.assign(row.data,values);
ctx.requestText_=()=>'';ctx.requestHtml_=()=>'';ctx.deliver_=recipient=>{targets.push(recipient.id);return 'auto';};
const result=ctx.doPost({parameter:{...choose,name:'テスト',tel:'00000000000',email:'test@example.invalid',contact:'メール'}});
assert.equal(result.id,'OFFLINE-FIXTURE');
assert.equal(saved.length,1);assert.equal(receiptCount,1);
assert.equal(row.data['状態'],ctx.ST.OPEN);
assert.equal(row.data['依頼の種類'],'問い合わせ');
assert.equal(row.data['概算料金'],'');
assert.deepEqual(targets,['P014']);
ctx.sendWave_('OFFLINE-FIXTURE',1);ctx.sendWave_('OFFLINE-FIXTURE',2);
assert.deepEqual(targets,['P014']);
row.data['通知した提携先']='';row.data['指定した提携先ID']='';
ctx.sendWave_('OFFLINE-FIXTURE',1);ctx.sendWave_('OFFLINE-FIXTURE',2);
assert.equal(targets.filter(x=>x==='P014').length,1);
row.data['通知した提携先']='';row.data['指定した提携先ID']='P014';row.data['行き先']='越谷市';
ctx.sendWave_('OFFLINE-FIXTURE',1);assert.equal(targets.filter(x=>x==='P014').length,1);
delete props.KASUKABE_INTAKE_ENABLED;
assert.equal(find(p),undefined);
assert.equal(ctx.validateSelection_(choose).error,'selection_unavailable');
console.log('PASS: held and pinned Kasukabe one-way pilot; exact candidate, signed selection, pending request and selected-only delivery are scoped; no actual mail or storage.');
