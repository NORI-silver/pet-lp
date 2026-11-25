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
assert.equal(find(p),undefined);
assert.equal(ctx.isOpen_('P014'),false);
console.log('PASS: mailbox configuration alone cannot release Kasukabe.');
