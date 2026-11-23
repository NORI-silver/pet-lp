// 会社がお返事を取り下げると、お客さまはその内容で予約できなくなる（Nori 2026-11-08）
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const sent=[],rows={};
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite,isNaN,
  PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'secret'})},
  LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})},SpreadsheetApp:{flush(){}},
  Utilities:{computeHmacSha256Signature:(s,k)=>[...crypto.createHmac('sha256',k).update(s).digest()],base64EncodeWebSafe:(b)=>Buffer.from(b).toString('base64').replace(/\+/g,'-').replace(/\//g,'_')}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const now=Date.now();
rows.R1={'受付番号':'R1','状態':ctx.ST.OPEN,'依頼の種類':'問い合わせ','お名前':'テスト','見積もりJSON':JSON.stringify([{pid:'P9',at:now+86400000,fare:5000,time:now}])};
Object.assign(ctx,{
  findReq_:id=>rows[id]?{rowIndex:2,data:rows[id]}:null,
  setReq_:(i,o)=>Object.assign(rows.R1,o),
  partnerById_:id=>id==='P9'?{id:'P9',name:'テスト交通'}:null,
  toCustomer_:(r,s,t)=>sent.push(['c',s,t]),notifyAdmin_:(s)=>sent.push(['a',s]),log_(){},
  page_:(t,h)=>({t,h}),rideText_:()=>'',linkBase_:()=>'https://x/'});
const k=ctx.sign_('R1:P9:withdraw');
assert.equal(ctx.withdrawPage_({id:'R1',p:'P9',k:'bad'}).t,'リンクが正しくありません');
assert.equal(ctx.withdrawPage_({id:'R1',p:'P9',k}).t,'お返事を取り下げますか？');      // まず確認の画面
assert.equal(ctx.withdrawPage_({id:'R1',p:'P9',k,go:'1'}).t,'お返事を取り下げました');
assert.ok(JSON.parse(rows.R1['見積もりJSON'])[0].withdrawn);
assert.ok(sent.some(x=>x[0]==='c'&&/取り下げられました/.test(x[1])));               // お客さまに知らせる
assert.equal(ctx.withdrawPage_({id:'R1',p:'P9',k,go:'1'}).t,'取り下げ済みです');
const ck=ctx.sign_('R1:P9:choose');
assert.equal(ctx.choosePage_({id:'R1',p:'P9',k:ck,go:'1'}).t,'このお返事は取り下げられました'); // 押しても予約にならない
console.log('PASS: partner can withdraw a reply; customer can no longer book it');
// 確定後に会社がやむを得ず取り消す
rows.R1['状態']=ctx.ST.DONE; rows.R1['決定した提携先ID']='P9'; rows.R1['お迎え予定']=new Date(now+86400000);
Object.assign(ctx,{fmt_:()=>'11/20 10:30',retryUrl_:()=>'https://x/retry',legTag_:()=>''});
const pk=ctx.sign_('R1:P9:pcancel');
assert.equal(ctx.partnerCancelPage_({id:'R1',p:'P9',k:pk}).t,'このご予約を取り消しますか？');
assert.equal(ctx.partnerCancelPage_({id:'R1',p:'P9',k:pk,go:'1'}).t,'ご予約を取り消しました');
assert.equal(rows.R1['状態'],ctx.ST.CANCEL);
assert.ok(sent.some(x=>x[0]==='c'&&/お受けできなくなりました/.test(x[1])));
assert.equal(ctx.partnerCancelPage_({id:'R1',p:'P9',k:pk,go:'1'}).t,'取り消しは必要ありません');
console.log('PASS: partner can cancel a confirmed booking; customer is told');
