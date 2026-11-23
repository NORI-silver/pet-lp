// 提携の確認ページ（a=pconf）：公式サイトの内容を入れて開き、答えを「提携の確認」タブとメールに残す（Nori 2026-11-14）
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const rows=[],mails=[];
let privateAvailable=true, privateConfigured=true;
const sheet={appendRow:r=>rows.push(r),getLastRow:()=>rows.length+1,getRange:()=>({setNumberFormat(){},createTextFinder:key=>({matchEntireCell(){return this},findNext(){return rows.some(r=>r[7]===key);}})})};
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite,isNaN,
  PropertiesService:{getScriptProperties:()=>({getProperty:k=>k==='PCONF_FARE_PILOT' ? (privateConfigured?'on':'') : k==='PCONF_PRIVATE_FILE_ID' ? (privateConfigured?'test-restricted':'') : 'secret'})},
  Utilities:{computeHmacSha256Signature:(s,k)=>[...crypto.createHmac('sha256',k).update(s).digest()],base64EncodeWebSafe:(b)=>Buffer.from(b).toString('base64').replace(/\+/g,'-').replace(/\//g,'_')},
  ContentService:{createTextOutput:s=>({text:s,setMimeType(){return this}}),MimeType:{JSON:'json'}},
  HtmlService:{createHtmlOutput:h=>({html:h,setTitle(){return this},addMetaTag(){return this}})},
  LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})},
  SpreadsheetApp:{getActive:()=>({getId:()=> 'booking'}),openById:()=>{if(!privateAvailable)throw Error('not configured');return {getId:()=> 'restricted'};}}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
ctx.ensureSheet_=()=>sheet; ctx.log_=()=>{}; ctx.notifyAdmin_=(s,t)=>mails.push([s,t]);
const id='De5faaf3', tok=ctx.demoToken_(id);
assert.ok(ctx.DISPLAY_COMPANIES.some(c=>c.id===id));
ctx.PCONF[id] = {name:'テスト会社', sections:[{h:'条件', items:[
  {k:'origin', l:'お迎えの起点', tag:'site', type:'text', v:'テスト駅'},
  {k:'ng_area', l:'行けない地域', tag:'site', type:'check', o:['沖縄県','離島'], v:['沖縄県','離島']},
  {k:'back', l:'戻る分', tag:'need', type:'text'}
]}], examples:[{l:'テスト区間', yen:'1,234円', d:'内訳は例'}]};
const page=ctx.pconfPage_({a:'pconf',t:tok}).html;
assert.ok(page.includes('テスト駅') && page.includes('入力してください') && page.includes('1,234円'));
assert.ok(/name="f_ng_area_0" value="1" checked/.test(page));                              // サイトの内容は先に選んである
assert.ok(ctx.pconfPage_({a:'pconf',t:id+'.xxxxxxxxxxxxxxxx'}).html.includes('リンクが正しくありません'));
assert.ok(ctx.pconfPage_({a:'pconf',t:tok,go:'1'},true).html.includes('お名前を入れてください'));   // 名前がなければ送らない
assert.equal(rows.length,0);
const done=ctx.pconfPage_({a:'pconf',t:tok,go:'1',name:'テスト',f_origin:'テスト駅',f_ng_area_0:'1',f_back:'別途確認',f_back_more:'確認用',ex0:'ちがう',ex0_fix:'4,600円'},true).html;
assert.ok(done.includes('ありがとうございました') && rows.length===1 && mails.length===1);
assert.ok(rows[0][4].includes('行けない地域：沖縄県　←') && rows[0][4].includes('確認用') && rows[0][5].includes('ちがう（4,600円）'));
assert.ok(!mails[0][1].includes('4,600') && !mails[0][1].includes('テスト') && mails[0][1].includes('送信だけでは'));
console.log('PASS: partner confirm page opens prefilled with the demo token and records answers without touching the partner sheet');
delete ctx.PCONF[id];
// 全社：公式サイトの情報（DISPLAY_COMPANIES）から下書きを作る。新しい会社は会社名・メール・ホームページから始める（2026-11-15）
{
  const c=ctx.DISPLAY_COMPANIES.find(x=>x.id==='De5faaf3'), tok=ctx.demoToken_(c.id);
  const page=ctx.pconfPage_({a:'pconf',t:tok}).html;
  assert.ok(page.includes(c.name) && page.includes('サイトより') && page.includes('3,300円で5kmまで') && page.includes('6. 料金の例'), 'auto page with site data and examples');
  assert.ok(/お店から5kmの場所 → 10km先[^]*?\d[\d,]*円/.test(page), 'examples are priced');
  assert.ok(page.includes('白ナンバーの車では、提携をお受けできません'));
  const start=ctx.pconfPage_({a:'pconf','new':'1'}).html;
  assert.ok(start.includes('ホームページのURL') && !start.includes('1. どこへ行けるか'));
  const known=ctx.pconfPage_({a:'pconf','new':'1',step:'2',co:'杉並店',email:'a@b.jp',site:'https://www.pet-taxi-tokyo-suginami.com/fare'},true).html;
  assert.ok(known.includes('3,300円で5kmまで') && known.includes('name="co" value="杉並店"'), 'known site gets prefilled');
  const blank=ctx.pconfPage_({a:'pconf','new':'1',step:'2',co:'新しい会社',email:'a@b.jp',site:'https://example.com/'},true).html;
  assert.ok(blank.includes('1. どこへ行けるか') && !blank.includes('サイトより') && !blank.includes('6. 料金の例'), 'unknown site is blank');
  const n=rows.length;
  assert.ok(ctx.pconfPage_({a:'pconf','new':'1',step:'2',go:'1',co:'新しい会社',email:'bad',name:'山田'},true).html.includes('メールアドレス'));
  const ok=ctx.pconfPage_({a:'pconf','new':'1',step:'2',go:'1',co:'新しい会社',email:'a@b.jp',site:'https://example.com/',name:'山田',f_radius:'上限なし',f_plate:'黒ナンバー（貨物軽自動車の届出）'},true).html;
  assert.ok(ok.includes('ありがとうございました') && rows.length===n+1 && rows[n][1]==='（新規）' && rows[n][2]==='新しい会社' && rows[n][4].includes('a@b.jp') && rows[n][4].includes('上限なし') && !rows[n][4].includes('←サイトの内容から変更'));
  // 公式サイトの情報がある会社は全部開ける（例が出せるかどうかに関わらず、エラーにならない）
  ctx.DISPLAY_COMPANIES.forEach(x=>{ const h=ctx.pconfPage_({a:'pconf',t:ctx.demoToken_(x.id)}).html; assert.ok(h.includes('この内容で送る'), x.id); });
}
console.log('PASS: every company with site data gets a prefilled confirm page; new companies start from name, email and homepage');

{
  const c=ctx.pconfFarePilot_('Dcb3b5a2'), t=ctx.demoToken_(c.id);
  assert.equal(ctx.pconfFarePilot_('P064').id,c.id);
  const fv=ctx.pconfFareToken_(c.id,Date.now()+3600000,'testNonceOnly');
  const p=ctx.pconfPage_({a:'pconf',t,fv}).html;
  assert.doesNotMatch(ctx.pconfPage_({a:'pconf',t}).html,/お迎え20km：/);
  assert.doesNotMatch(ctx.pconfPage_({a:'pconf',new:'1',step:'2',site:'https://pettaxi-osanpo.com'},true).html,/お迎え20km：/);
  assert.match(ctx.pconfPage_({a:'pconf',t,fv:fv+'bad'}).html,/受け付けていません/);
  assert.match(ctx.pconfPage_({a:'pconf',t,fv:ctx.pconfFareToken_(c.id,Date.now()-10,'testNonceOnly')}).html,/受け付けていません/);
  assert.match(p,/data-pconf method="post"/);
  assert.ok(p.includes(ctx.webUrl_()));
  assert.doesNotMatch(p,/action="https:\/\/pet.shiokonbu.com\/go\//);
  assert.match(p,/<details><summary>公開の料金を確認・訂正する/);
  assert.match(p,/公式サイトの料金/);
  assert.match(p,/お迎え20km/);
  assert.doesNotMatch(p,/6. 料金の例/);
  const q={a:'pconf',t,fv,go:'1',name:'テスト',
    pf_limit:'20000',pf_mode:'flat',pf_add:'1234',pf_basis:'road',pf_pickround:'ceil',pf_round:'ceil',pf_tax:'incl',
    pf_near:'4500',pf_at:'3900',pf_far:'5434'};
  Object.keys(ctx.PCONF_PUBLIC_FARE).forEach(k=>q['f_'+k]=ctx.PCONF_PUBLIC_FARE[k]);
  // ¥300 exactly in either direction passes; an illustrative result still never activates a fare.
  const d=ctx.pconfFareDraft_(c,q);
  assert.equal(d.check.status,'examples_passed');
  assert.equal(d.check.ready,false);
  assert.equal(d.check.cases[0].actual,4200);
  assert.equal(d.check.cases[2].actual,5434);
  assert.equal(d.check.cases[2].shown,5400);
  const roundedGap=ctx.pconfFareDraft_(c,{...q,pf_add:'260',pf_far:'4160'}).check;
  assert.equal(roundedGap.cases[2].actual,4460);
  assert.equal(roundedGap.cases[2].shown,4500);
  assert.equal(roundedGap.status,'mismatch');
  const app=fs.readFileSync('app.js','utf8');
  const js=app.split('\n').filter(line=>/function (yen|roundYenText)\(/.test(line)).join('\n');
  for (let y of [0,99,100,4460,5434]) {
    assert.equal(vm.runInNewContext(js+';roundYenText("'+y+'円")'),ctx.roundYenText_(y+'円'));
  }
  assert.equal(ctx.pconfFareDraft_(c,{...q,pf_near:'4501'}).check.status,'mismatch');
  assert.equal(ctx.pconfFareDraft_(c,{...q,pf_at:'3899'}).check.status,'mismatch');
  assert.equal(ctx.pconfFareDraft_(c,{...q,pf_add:''}).check.status,'needs_review');
  assert.equal(ctx.pconfFareDraft_(c,{...q,pf_add:'0',pf_far:'4200'}).check.status,'examples_passed');
  assert.equal(ctx.pconfFareDraft_(c,{...q,pf_mode:'manual'}).check.status,'needs_review');
  assert.equal(ctx.pconfFareDraft_(c,{...q,pf_tax:''}).check.status,'needs_review');
  assert.equal(ctx.pconfFareDraft_(c,{...q,pf_basis:'other'}).check.status,'needs_review');
  const missing=JSON.parse(JSON.stringify(c));
  delete missing.fare.back;
  assert.equal(ctx.pconfFareDraft_(missing,q).check.status,'needs_review');
  for (const [m, incomplete] of [[19999,false],[20000,false],[20001,true]]) {
    const f=ctx.pconfFareFixture_(c,m,5000);
    assert.equal(ctx.displayPrice_(c,f.input,f.lookup).incompleteFees,incomplete);
  }
  const far=ctx.pconfFareFixture_(c,21000,5000);
  assert.equal(ctx.displayPrice_(c,far.input,()=>null).incompleteFees,true);
  const coco=ctx.DISPLAY_COMPANIES.find(x=>x.id==='De5faaf3');
  const f=ctx.pconfFareFixture_(coco,10000,5000,'23:00');
  const n=ctx.displayPrice_(coco,f.input,f.lookup).local;
  assert.equal(n.ride,3300);
  assert.equal(n.pickup,1650);
  assert.equal(n.nightExtra,3300);
  const getCount=rows.length;
  assert.match(ctx.pconfPage_(q).html,/受け付けられません/);
  assert.equal(rows.length,getCount);
  const webReply=ctx.doPost({parameter:{...q,fmt:'json'}});
  assert.match(JSON.parse(webReply.text).html,/いただいた内容/);
  assert.equal(JSON.parse(rows.at(-1)[6]).fareReview.check.status,'examples_passed');
  assert.doesNotMatch(mails.at(-1).join(' '),/1234|5434|テスト/);
  let once=rows.length, onceMail=mails.length;
  assert.match(ctx.doPost({parameter:q}).html,/ありがとうございました/);
  assert.equal(rows.length,once);
  assert.equal(mails.length,onceMail);
  const correction={...q,fv:ctx.pconfFareToken_(c.id,Date.now()+3600000,'correctionNonce'),f_pick_public:'変更テスト'};
  ctx.doPost({parameter:correction});
  assert.equal(JSON.parse(rows.at(-1)[6]).fareReview.check.status,'public_correction_needs_review');
  privateAvailable=false;
  const count=rows.length, mailCount=mails.length;
  assert.match(ctx.doPost({parameter:{...q,fv:ctx.pconfFareToken_(c.id,Date.now()+3600000,'failureNonce')}}).html,/送信できませんでした/);
  assert.equal(rows.length,count);
  assert.equal(mails.length,mailCount);
  privateConfigured=false;
  assert.doesNotMatch(ctx.pconfPage_({a:'pconf',t}).html,/お迎え20km：/);
  assert.match(ctx.doPost({parameter:q}).html,/受け付けていません/);
  const legacy={a:'pconf',t:ctx.demoToken_('De5faaf3'),go:'1',name:'テスト'};
  assert.match(ctx.doPost({parameter:legacy}).html,/ありがとうございました/);
  if (process.env.PCONF_PREVIEW) {
    const h=p.replace('<meta charset="utf-8">',`<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="form-action 'none'">`)
      .replace(/<form[^>]+>/,'<form data-preview="true">').replace(/<input type="hidden"[^>]+>/g,'').replace('<button type="submit">','<button type="button" disabled>');
    fs.writeFileSync(process.env.PCONF_PREVIEW,h);
  }
  console.log('PASS: local fare pilot price boundary, parity, provenance, safe request and pending review');
}

// Exercise both existing static wrapper steps, using the real frontend handler and server responses.
(async () => {
  const relay=fs.readFileSync('go/index.html','utf8');
  const hook=relay.slice(relay.indexOf('  function hookPartnerConfirm()'), relay.indexOf('  if (CK) try'));
  const calls=[], pages=[];
  let submit;
  const button={disabled:false, after(){}};
  const form={dataset:{},querySelector:q=>q.includes('button') ? button : null,addEventListener:(name,fn)=>{assert.equal(name,'submit');submit=fn;}};
  let formValues={a:'pconf',new:'1',step:'2',co:'見本',email:'example@example.invalid',site:'https://example.invalid'};
  const body={querySelector:()=>form,set innerHTML(h){pages.push(h);form.dataset.pconfHook='';}};
  const host={URLSearchParams, FormData:function(){return formValues;},document:{createElement:()=>({setAttribute(){}})},window:{scrollTo(){}},body,title:{},API:'https://gas.test/exec',
    fetch:async (url,init)=>{calls.push({url,init});const r=ctx.doPost({parameter:Object.fromEntries(init.body)});return {json:async()=>JSON.parse(r.text)};}};
  vm.runInNewContext(hook+';hookPartnerConfirm();',host);
  let prevented=false;submit({preventDefault(){prevented=true;}});
  await new Promise(setImmediate);
  assert.equal(prevented,true);
  assert.equal(calls[0].url,'https://gas.test/exec');
  assert.equal(calls[0].init.method,'POST');
  assert.equal(calls[0].init.body.get('email'),formValues.email);
  assert.match(pages[0],/1. どこへ行けるか/);
  formValues={...formValues,go:'1',name:'見本'};
  button.disabled=false;
  submit({preventDefault(){}});
  await new Promise(setImmediate);
  assert.equal(calls[1].init.body.get('go'),'1');
  assert.match(pages[1],/いただいた内容/);
  console.log('PASS: /go/ wrapper exchanges both signup steps via Apps Script POST JSON');
})().catch(e=>{console.error(e);process.exitCode=1;});
