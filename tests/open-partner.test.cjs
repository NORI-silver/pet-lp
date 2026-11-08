// 全社準備中のあいだも、受け付けを始めた会社（CONFIG.OPEN_PARTNERS）にだけは問い合わせを送れる（Nori 2026-11-08「aiaiはOPENにしていい」）
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite,isNaN,
  PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'secret'})},
  Session:{getEffectiveUser:()=>({getEmail:()=>'admin@example.com'})},
  Utilities:{computeHmacSha256Signature:(s,k)=>[...crypto.createHmac('sha256',k).update(s).digest()],base64EncodeWebSafe:(b)=>Buffer.from(b).toString('base64').replace(/\+/g,'-').replace(/\//g,'_')}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
vm.runInContext("CONFIG.ADMIN_EMAIL='admin@example.com'; liveSending_=function(){return false;}",ctx);
assert.equal(vm.runInContext('CONFIG.SHOW_ALL_CANDIDATES',ctx),true);
assert.equal(ctx.isOpen_('P060'),true); assert.equal(ctx.isOpen_('P002'),false);
assert.equal(ctx.openDisplay_('P060').id,'D13b7c6f');
assert.equal(ctx.isAnon_('P060',''),false); assert.equal(ctx.isAnon_('P002',''),true);
const row=(ids)=>({'指定した提携先ID':ids,'お名前':'山田','メール':'a@b.jp'});
assert.equal(ctx.isTest_(row('P060')),false);       // aiaiだけあては、B1が止めるでも会社に送る
assert.equal(ctx.isTest_(row('P060,P002')),true);   // ほかの会社が混ざれば送らない
assert.equal(ctx.isTest_(row('P002')),true);
assert.equal(ctx.isTest_(row('')),true);
assert.ok(vm.runInContext("openDisplayIds_().indexOf('D13b7c6f')>=0",ctx)); // 表示だけのカードとは重ねない
console.log('PASS: only OPEN_PARTNERS can receive inquiries while every other company stays in preparation');
