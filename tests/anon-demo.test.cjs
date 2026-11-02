// 提携していない会社は名前を出さない。見本のリンクの会社だけ名前つき・問い合わせは送れない（Nori 2026-11-02「AとC」）
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite,isNaN,
  PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'secret'})},
  Utilities:{computeHmacSha256Signature:(s,k)=>[...crypto.createHmac('sha256',k).update(s).digest()],base64EncodeWebSafe:(b)=>Buffer.from(b).toString('base64').replace(/\+/g,'-').replace(/\//g,'_')}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const c=vm.runInContext('DISPLAY_COMPANIES[0]',ctx);
assert.equal(ctx.anonLabel_('東京都','杉並区・中野区を中心に'),'東京都・杉並区あたりの会社');
assert.equal(ctx.anonLabel_('東京都','東京23区'),'東京都の会社');
assert.equal(ctx.anonLabel_('大阪府',''),'大阪府の会社');
const card=()=>({id:c.id,label:c.name,display_only:true,shop:[35.70512,139.63649],price:{amount:5000}});
const a=ctx.anonCard_(card(),c.pref,c.area_text,'');
assert.ok(a.anon && a.label.indexOf(c.name)<0 && a.display_only);          // 名前を出さない
assert.equal(JSON.stringify(a.shop),"[35.71,139.64]");                                     // お店の場所はまるめる
const tok=ctx.demoToken_(c.id);
assert.equal(ctx.demoId_(tok),c.id);
assert.equal(ctx.demoId_(c.id+'.xxxxxxxxxxxxxxxx'),'');                     // 署名が違えば見本にしない
const d=ctx.anonCard_(card(),c.pref,c.area_text,c.id);
assert.ok(d.demo && d.label===c.name && !d.display_only && !d.token);        // 見本の会社は名前つき・トークンなし（送れない）
assert.equal(ctx.isAnon_(c.id,''),true); assert.equal(ctx.isAnon_(c.id,c.id),false);
console.log('PASS: unpartnered companies are anonymous; demo link shows only that company by name, without a send token');
