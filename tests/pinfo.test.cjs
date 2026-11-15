// 掲載情報の追加（a=pinfo）：提携している会社だけが写真・特典・設備などを送れ、決まりに合わない言い方は止め、写真はカードと同じ横3：縦2だけを受け付ける
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
assert.ok(page.includes('PETTA東京') && page.includes('data-pinfo-up') && page.includes('（5〜30%）') && page.includes('pct_off_until') && page.includes('早朝・深夜の割増なし'));
// 特典は終わりの日と数字の上限、ひとことは禁止の言い方で止める
const later=new Date(Date.now()+30*864e5).toISOString().slice(0,10);
let r=ctx.pinfoPage_({s:tok,go:'1',pct_off:'50',pct_off_until:later}).html;
assert.ok(r.includes('5〜30%') && rows.length===0);
r=ctx.pinfoPage_({s:tok,go:'1',yen_off:'500',yen_off_until:later,equip:['ケージの貸し出し','ペットシーツ'],note:'地域最安！お電話は03-1234-5678'}).html;
assert.ok(rows.length===3, 'offer + equip + note');
assert.equal(rows[0][3],'特典'); assert.ok(rows[0][4].startsWith('500円オフ')); assert.equal(rows[0][6],'確認待ち');
const note=rows.find(x=>x[3]==='ひとこと'); assert.equal(note[6],'直してください'); assert.ok(/電話番号/.test(note[7]) && /くらべる言い方/.test(note[7]));
assert.ok(mails.length===3 && mails[0][1].includes('a=pinfo_ok'));
assert.ok(sent.length===1 && sent[0][0]==='petta@example.jp' && sent[0][2].includes('500円オフ'), 'receipt to the partner');
// 期間のない特典は止める（特典ごとに期間）
let n1=rows.length;
r=ctx.pinfoPage_({s:tok,go:'1',night_free:'1',yen_off:'500',yen_off_until:later,equip:['ケージの貸し出し','ペットシーツ'],note:'地域最安！お電話は03-1234-5678'}).html;
assert.ok(r.includes('「早朝・深夜の割増なし」の「いつまで」'));
rows.splice(n1); sent.length=1; mails.length=3;
// 同じ内容をもう一度送っても行は増えない
ctx.pinfoPage_({s:tok,go:'1',yen_off:'500',yen_off_until:later,equip:['ケージの貸し出し','ペットシーツ'],note:'地域最安！お電話は03-1234-5678'});
assert.equal(rows.length,4, 'only the rejected note is re-sent');
// 登録・届出を選んだら番号が要る。お支払い方法は受け付ける。人数・頭数の項目はない
let n0=rows.length;
r=ctx.pinfoPage_({s:tok,go:'1',cred:['運送の届出（黒ナンバー）'],equip:['ケージの貸し出し','ペットシーツ'],yen_off:'500',yen_off_until:later,note:''}).html;
assert.ok(r.includes('番号を入れてください') && !rows.slice(n0).some(x=>x[3]==='許可・資格・保険'));
ctx.pinfoPage_({s:tok,go:'1',cred:['運送の届出（黒ナンバー）'],cred_no:'関自貨第123号',pay:['現金','クレジットカード'],equip:['ケージの貸し出し','ペットシーツ'],yen_off:'500',yen_off_until:later,note:''});
assert.ok(rows.some(x=>x[3]==='許可・資格・保険' && x[4].includes('関自貨第123号')) && rows.some(x=>x[3]==='お支払い方法' && x[4]==='現金・クレジットカード'));
assert.ok(!page.includes('多頭の同乗') && !page.includes('飼い主さんの同乗') && !page.includes('得意な行き先'));
// 写真はページが横3：縦2に切り抜いたものだけ。小さい・形がちがうものは断る
assert.ok(/小さいので/.test(ctx.pinfoPhoto_({t:tok,rights:'1',w:'800',h:'533',data:'x'}).error));
assert.ok(/形が合いません/.test(ctx.pinfoPhoto_({t:tok,rights:'1',w:'1600',h:'1200',data:'x'}).error));
// 運転手の写真は正方形で、写っている方の了解が要る
assert.ok(/了解/.test(ctx.pinfoPhoto_({t:tok,rights:'1',photo_kind:'運転手',w:'800',h:'800',data:'x'}).error));
assert.ok(/正方形/.test(ctx.pinfoPhoto_({t:tok,rights:'1',consent:'1',photo_kind:'運転手',w:'1500',h:'1000',data:'x'}).error));
assert.ok(!page.includes('臨時のお休み') && !page.includes('name="off"'));
console.log('PASS: partner listing page logs in by email link, accepts only partners, blocks banned wording');
{
  // 公開した行だけ・期限内の特典だけ・横長の写真だけを候補カード用に出す
  rows.length=0; ctx.CacheService={getScriptCache:()=>({get:()=>null,put(){},remove(){}})};
  const later=new Date(Date.now()+30*864e5).toISOString().slice(0,10), past='2020-01-01';
  const row=(kind,state,data)=>rows.push([new Date(),'P063','PETTA東京',kind,'',  '○',state,'',JSON.stringify(data)]);
  row('特典','公開',{list:[{label:'10%オフ',text:'10%オフ（'+later+'まで）',until:later},{text:'早朝・深夜の割増なし（2025/01/01まで）',until:later},{text:'古い',until:past}]});
  row('設備・できること','公開',{list:['ケージの貸し出し']});
  row('お支払い方法','公開',{list:['現金']});
  row('ひとこと','公開',{text:'大型犬もどうぞ'});
  row('写真','公開',{file:'abc',w:1600,h:1067,kind:'車の中'});
  row('写真','公開',{file:'tall',w:900,h:1600,kind:'車の外'});
  row('写真','公開',{file:'out',w:1500,h:1000,kind:'車の外'});
  row('写真','公開',{file:'drv',w:800,h:800,kind:'運転手'});
  row('写真','直してください',{file:'ng',w:1600,h:1000,kind:'お店'});
  const pub=ctx.pinfoPublic_()['P063'];
  const ud=Number(later.slice(5,7))+'/'+Number(later.slice(8,10));
  assert.equal(JSON.stringify(pub.offers),JSON.stringify([{k:'',n:null,t:'10%オフ',until:ud},{k:'',n:null,t:'早朝・深夜の割増なし',until:ud}]));
  assert.deepEqual(pub.tags,['ケージの貸し出し']); assert.equal(pub.note,'大型犬もどうぞ');
  assert.equal(pub.photos.length,2); assert.ok(pub.photos[0].url.includes('out') && pub.photos[1].url.includes('abc'), 'car outside first'); assert.ok(pub.driver.includes('drv'), 'driver photo goes next to the name');
  assert.equal(JSON.stringify(pub.offers.map(o=>o.k||'')),JSON.stringify(['','']));
  console.log('PASS: only approved, unexpired, landscape items reach the cards');
}
