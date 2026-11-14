// 提携の確認ページ（a=pconf）：公式サイトの内容を入れて開き、答えを「提携の確認」タブとメールに残す（Nori 2026-11-14）
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const rows=[],mails=[];
const sheet={appendRow:r=>rows.push(r),getLastRow:()=>rows.length+1,getRange:()=>({setNumberFormat(){}})};
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite,isNaN,
  PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'secret'})},
  Utilities:{computeHmacSha256Signature:(s,k)=>[...crypto.createHmac('sha256',k).update(s).digest()],base64EncodeWebSafe:(b)=>Buffer.from(b).toString('base64').replace(/\+/g,'-').replace(/\//g,'_')},
  HtmlService:{createHtmlOutput:h=>({html:h,setTitle(){return this},addMetaTag(){return this}})},
  LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})},
  SpreadsheetApp:{getActive:()=>({})}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
ctx.ensureSheet_=()=>sheet; ctx.log_=()=>{}; ctx.notifyAdmin_=(s,t)=>mails.push([s,t]);
const id='D5598693', tok=ctx.demoToken_(id);
assert.ok(ctx.PCONF[id] && ctx.DISPLAY_COMPANIES.some(c=>c.id===id));                   // 見本のリンクと同じ合言葉で開ける会社
const page=ctx.pconfPage_({a:'pconf',t:tok}).html;
assert.ok(page.includes('緑園都市駅') && page.includes('入力してください') && page.includes('107,600円'));
assert.ok(/name="f_ng_area_0" value="1" checked/.test(page));                              // サイトの内容は先に選んである
assert.ok(ctx.pconfPage_({a:'pconf',t:id+'.xxxxxxxxxxxxxxxx'}).html.includes('リンクが正しくありません'));
assert.ok(ctx.pconfPage_({a:'pconf',t:tok,go:'1'}).html.includes('お名前を入れてください'));   // 名前がなければ送らない
assert.equal(rows.length,0);
const done=ctx.pconfPage_({a:'pconf',t:tok,go:'1',name:'平',f_origin:'相鉄線 緑園都市駅（車両基地）',f_ng_area_0:'1',f_back:'かかる（下に書いてください）',f_back_more:'1km100円',ex0:'ちがう',ex0_fix:'4,600円'}).html;
assert.ok(done.includes('ありがとうございました') && rows.length===1 && mails.length===1);
assert.ok(rows[0][4].includes('行けない地域：沖縄県　←') && rows[0][4].includes('1km100円') && rows[0][5].includes('ちがう（4,600円）'));
assert.ok(mails[0][1].includes('受付を始めるのは、運営者が確かめてから'));
console.log('PASS: partner confirm page opens prefilled with the demo token and records answers without touching the partner sheet');
