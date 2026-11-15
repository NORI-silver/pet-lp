// 掲載情報の追加（a=pinfo）：提携している会社だけが写真・特典・設備などを送れ、決まりに合わない言い方は止め、臨時のお休みは候補から外す（Nori 2026-11-15）
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const rows=[],mails=[];
const sheet={appendRow:r=>rows.push(r),getLastRow:()=>rows.length+1,getRange:()=>({setNumberFormat(){},getValues:()=>rows.map(r=>r.slice())})};
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite,isNaN,
  PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'secret'})},
  Utilities:{computeHmacSha256Signature:(s,k)=>[...crypto.createHmac('sha256',k).update(s).digest()],base64EncodeWebSafe:(b)=>Buffer.from(b).toString('base64').replace(/\+/g,'-').replace(/\//g,'_')},
  HtmlService:{createHtmlOutput:h=>({html:h,setTitle(){return this},addMetaTag(){return this}})},
  LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})},
  SpreadsheetApp:{getActive:()=>({})}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
ctx.ensureSheet_=()=>sheet; ctx.sheet_=()=>sheet; ctx.log_=()=>{}; ctx.notifyAdmin_=(s,t)=>mails.push([s,t]);
ctx.partners_=()=>[{id:'P063',name:'PETTA東京',email:'petta@example.jp'},{id:'P030',name:'練馬杉並店',email:'nerima@example.jp'}];
const sent=[]; ctx.mail_=(to,sub,body)=>{sent.push([to,sub,body]);return true;};
const props={}; ctx.PropertiesService.getScriptProperties=()=>({getProperty:k=>k==='SECRET'||!(k in props)?'secret':props[k],setProperty:(k,v)=>{props[k]=v;}});
// 提携していない会社の合言葉では開けない
{ const h=ctx.pinfoPage_({t:ctx.demoToken_('De5faaf3')}).html; assert.ok(h.includes('name="email"') && !h.includes('data-pinfo-up')); }
// 提携先IDでも、表示の会社のIDでも、ログインのメールを頼む画面になる（合言葉だけでは中に入れない）
const inv=ctx.demoToken_('P063');
assert.equal(ctx.pinfoPid_(ctx.demoToken_('D3661eb1')),'P063');
const login=ctx.pinfoPage_({t:inv}).html;
assert.ok(login.includes('ログインのリンクをメールで受け取る') && !login.includes('data-pinfo-up'));
// メールは登録のアドレスにだけ届き、答えの文は同じ
const a=ctx.pinfoPage_({mail:'1',email:'stranger@example.jp'}).html, b=ctx.pinfoPage_({mail:'1',email:'PETTA@example.jp'}).html;
assert.equal(a,b); assert.equal(sent.length,1); assert.equal(sent[0][0],'petta@example.jp');
const link=sent[0][2].match(/a=pinfo&s=([^\s]+)/)[1], tok=decodeURIComponent(link);
ctx.pinfoPage_({mail:'1',t:inv}); assert.equal(sent.length,1, '5 minutes between login mails');
// 期限切れ・書き換えたリンクでは入れない
assert.equal(ctx.pinfoSessionPid_(tok),'P063');
assert.equal(ctx.pinfoSessionPid_(tok, Date.now()+25*3600e3),'');
assert.equal(ctx.pinfoSessionPid_(tok.replace('P063','P030')),'');
// 止めた会社は入れない
ctx.PINFO_STOP.push('P063'); assert.equal(ctx.pinfoSessionPid_(tok),''); ctx.PINFO_STOP.pop();
sent.length=0;
const page=ctx.pinfoPage_({s:tok}).html;
assert.ok(page.includes('PETTA東京') && page.includes('data-pinfo-up') && page.includes('お迎え料金が◯kmまで無料'));
// 特典は終わりの日と数字の上限、ひとことは禁止の言い方で止める
const later=new Date(Date.now()+30*864e5).toISOString().slice(0,10);
let r=ctx.pinfoPage_({s:tok,go:'1',of0:'first_pct',of0n:'50',of0u:later}).html;
assert.ok(r.includes('1〜30%') && rows.length===0);
r=ctx.pinfoPage_({s:tok,go:'1',of0:'pick_free',of0n:'5',of0u:later,equip:['ケージの貸し出し','ペットシーツ'],note:'地域最安！お電話は03-1234-5678'}).html;
assert.ok(rows.length===3, 'offer + equip + note');
assert.equal(rows[0][3],'特典'); assert.ok(rows[0][4].startsWith('お迎え料金が5kmまで無料')); assert.equal(rows[0][6],'確認待ち');
const note=rows.find(x=>x[3]==='ひとこと'); assert.equal(note[6],'直してください'); assert.ok(/電話番号/.test(note[7]) && /くらべる言い方/.test(note[7]));
assert.ok(mails.length===3 && mails[0][1].includes('a=pinfo_ok'));
assert.ok(sent.length===1 && sent[0][0]==='petta@example.jp' && sent[0][2].includes('お迎え料金が5kmまで無料'), 'receipt to the partner');
// 同じ内容をもう一度送っても行は増えない
ctx.pinfoPage_({s:tok,go:'1',of0:'pick_free',of0n:'5',of0u:later,equip:['ケージの貸し出し','ペットシーツ'],note:'地域最安！お電話は03-1234-5678'});
assert.equal(rows.length,4, 'only the rejected note is re-sent');
// 臨時のお休みも確認を通し、公開にしたらその日のお迎えは候補から外す
ctx.pinfoPage_({s:tok,go:'1',off:'2026-12-31 2027-01-01',equip:['ケージの貸し出し','ペットシーツ'],of0:'pick_free',of0n:'5',of0u:later,note:''});
const off=rows.find(x=>x[3]==='臨時のお休み'); assert.equal(off[6],'確認待ち');
ctx.PINFO_ALL_=null; assert.ok(!ctx.pinfoOffDays_('P063')['2027-01-01']);
off[6]='公開'; ctx.PINFO_ALL_=null;
assert.ok(ctx.pinfoOffDays_('P063')['2027-01-01']);
console.log('PASS: partner listing page logs in by email link, accepts only partners, blocks banned wording, reviews day-offs');
{
  const res=ctx.checks_({id:'P063',hours:'0-24',rideHours:'0-24'},{'希望日時':'2027-01-01T01:00:00Z','ペット':'[]'});
  assert.ok(res.ng.some(x=>x.includes('臨時のお休み')), JSON.stringify(res));
  const res2=ctx.checks_({id:'P063',hours:'0-24',rideHours:'0-24'},{'希望日時':'2027-01-03T01:00:00Z','ペット':'[]'});
  assert.ok(!res2.ng.some(x=>x.includes('臨時のお休み')));
  console.log('PASS: day-off excludes the partner from that day');
}
