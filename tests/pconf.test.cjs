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
const id='De5faaf3', tok=ctx.demoToken_(id);
assert.ok(ctx.DISPLAY_COMPANIES.some(c=>c.id===id));
ctx.PCONF[id] = {name:'テスト会社', sections:[{h:'条件', items:[
  {k:'origin', l:'お迎えの起点', tag:'site', type:'text', v:'テスト駅'},
  {k:'ng_area', l:'行けない地域', tag:'site', type:'check', o:['沖縄県','離島'], v:['沖縄県','離島']},
  {k:'back', l:'戻る分', tag:'need', type:'text'}
]}], examples:[{l:'テスト区間', yen:'1,234円', d:'内訳は例'}]};
function send(q, change) {
  const preview = ctx.pconfPage_(q).html;
  const hidden = k => preview.match(new RegExp('name="' + k + '" value="([^"]*)"'))?.[1];
  const parameter = { ...q, kind:'pconf', go:'1', terms_accept:'1', details_reviewed:'1',
    terms_version:hidden('terms_version'), terms_proof:hidden('terms_proof'), ...change };
  return ctx.doPost({parameter}).html;
}
const page=ctx.pconfPage_({a:'pconf',t:tok}).html;
assert.ok(page.includes('テスト駅') && page.includes('入力してください') && page.includes('1,234円'));
assert.ok(/name="f_ng_area_0" value="1" checked/.test(page));                              // サイトの内容は先に選んである
assert.ok(ctx.pconfPage_({a:'pconf',t:id+'.xxxxxxxxxxxxxxxx'}).html.includes('リンクが正しくありません'));
assert.ok(send({a:'pconf',t:tok}).includes('お名前を入れてください'));   // 名前がなければ送らない
assert.equal(rows.length,0);
const done=send({a:'pconf',t:tok,go:'1',name:'テスト',intake_email:'booking+pet@Example.test',f_origin:'テスト駅',f_ng_area_0:'1',f_back:'別途確認',f_back_more:'確認用',ex0:'ちがう',ex0_fix:'4,600円'});
assert.match(page, /<form method="post" action="https:\/\/script\.google\.com[^"]+"/);
assert.match(page, /name="terms_accept" value="1" required>/);
assert.doesNotMatch(page, /name="terms_accept"[^>]+checked/);
assert.ok(done.includes('ありがとうございました') && rows.length===1 && mails.length===1);
assert.ok(rows[0][4].includes('行けない地域：沖縄県　←') && rows[0][4].includes('確認用') && rows[0][5].includes('ちがう（4,600円）'));
assert.ok(mails[0][1].includes('受付を始めるのは、運営者が確かめてから'));
assert.equal(JSON.parse(rows[0][6]).terms.version, ctx.PTERMS_VER.hash);
assert.equal(JSON.parse(rows[0][6]).terms.at, rows[0][0].toISOString());
assert.equal(JSON.parse(rows[0][6]).terms.surface, 'pconf-application');
assert.match(page, /name="intake_email" type="email"[^>]*required[^>]*value=""/);
assert.equal(JSON.parse(rows[0][6]).intake_email, 'booking+pet@example.test');
assert.match(rows[0][4], /予約依頼の通知先メール/);
assert.ok(!mails[0][1].includes('booking+pet@example.test'));
const basic = {a:'pconf',t:tok,name:'テスト',intake_email:'booking+pet@example.test',f_back:'手入力を保持'};
for (const patch of [{terms_accept:undefined}, {terms_accept:'0'}, {terms_version:'old'}, {terms_proof:'wrong'}]) {
  const invalid = send(basic, patch);
  assert.match(invalid, /role="alert"/);
  assert.match(invalid, /手入力を保持/);
  assert.doesNotMatch(invalid, /name="terms_accept"[^>]+checked/);
  assert.match(invalid,/name="intake_email"[^>]+value="booking\+pet@example.test"/);
}
for(const dest of [undefined,'not-an-email','user@example.test,other@example.test','user..name@example.test','user@example-.test','user@localhost','a'.repeat(65)+'@example.test']) {
  const invalid=send(basic,{intake_email:dest});
  assert.match(invalid,/有効なメールアドレスを1件/);
  assert.match(invalid,/手入力を保持/);
}
assert.equal(rows.length,1);
assert.equal(mails.length,1);
assert.match(ctx.doGet({parameter:{...basic,go:'1',terms_accept:'1',terms_version:ctx.PTERMS_VER.hash,terms_proof:ctx.pconfTermsProof_(basic,id)}}).html, /role="alert"/);
assert.match(ctx.doPost({parameter:{kind:'pconf'},parameters:{terms_accept:['1','0']}}).html, /未送信/);
const other = ctx.demoToken_('D7f0d2a2');
assert.match(send(basic,{t:other}), /role="alert"/);
const originalVersion=ctx.PTERMS_VER;
const oldProof=ctx.pconfTermsProof_(basic,id);
ctx.PTERMS_VER={...originalVersion,hash:'deadbeef1234'};
assert.match(send(basic,{terms_version:originalVersion.hash,terms_proof:oldProof}), /role="alert"/);
ctx.PTERMS_VER={};
assert.match(ctx.pconfPage_(basic).html, /現在、送信できません/);
ctx.PTERMS_VER=originalVersion;
assert.equal(rows.length,1);
assert.equal(mails.length,1);
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
  const known=ctx.pconfPage_({a:'pconf','new':'1',step:'2',co:'杉並店',email:'a@b.jp',site:'https://www.pet-taxi-tokyo-suginami.com/fare'}).html;
  const bare=ctx.doPost({parameter:{kind:'pconf',new:'1',step:'2',co:'杉並店',email:'a@b.jp',site:'www.pet-taxi-tokyo-suginami.com/fare'}}).html;
  assert.match(bare,/name="site"[^>]+value="https:\/\/www\.pet-taxi-tokyo-suginami\.com\/fare"/);
  assert.match(bare,/3,300円で5kmまで/);
  const invalidStep1=ctx.doPost({parameter:{kind:'pconf',new:'1',step:'2',co:'テスト会社',email:'a@b.jp',site:'<script>'}}).html;
  assert.match(invalidStep1,/有効なURLかドメイン/);
  assert.match(invalidStep1,/name="co"[^>]+テスト会社/);
  assert.doesNotMatch(invalidStep1,/<script>/);
  assert.equal(ctx.pconfSiteValue_('javascript://example.jp'),null);
  assert.equal(ctx.pconfSiteValue_('example.jp@other.jp'),null);
  assert.ok(known.includes('3,300円で5kmまで') && known.includes('name="co" value="杉並店"'), 'known site gets prefilled');
  const blank=ctx.pconfPage_({a:'pconf','new':'1',step:'2',co:'新しい会社',email:'a@b.jp',site:'https://example.com/'}).html;
  assert.ok(blank.includes('1. どこへ行けるか') && !blank.includes('サイトより') && !blank.includes('6. 料金の例'), 'unknown site is blank');
  const n=rows.length;
  const fields={f_origin:'佐倉市',f_radius:'上限なし',f_dest:'全国どこへでも',f_hours:'毎日 9時〜17時',
    f_animals:'犬・猫',f_maxkg:'50kgまで',f_riders:'2人まで',f_petonly:'できない',f_tax:'税別',f_ride:'5kmまで3000円',
    f_pick:'かからない',f_pick2:'往復は受けない',f_back:'かからない',f_wait:'待機は受けない',f_night:'なし',
    f_toll_4:'1',f_long:'同じ料金表で計算',f_plate:'黒ナンバー（貨物軽自動車の届出）',f_car:'1台'};
  for (const changed of [{f_animals:''},{f_radius:'架空'},{f_maxkg:'0kg'},{f_pick:'〇km以上なら、距離のぜんぶ×単価'},{f_toll_0:'1'},{f_night:'22時から割増'},{f_plate:'白ナンバー'},{f_long:'〇kmを超えるとお見積もり（下に書いてください）',f_long_more:'0km'}]) {
    const rejected=send({a:'pconf','new':'1',step:'2',co:'新しい会社',email:'a@b.jp',site:'https://example.com/',name:'山田',...fields,...changed});
    assert.match(rejected,/各項目に修正箇所/); assert.match(rejected,/佐倉市/); assert.equal(rows.length,n);
  }
  assert.ok(send({a:'pconf','new':'1',step:'2',co:'新しい会社',email:'bad',name:'山田'}).includes('メールアドレス'));
  assert.match(send({a:'pconf','new':'1',step:'2',co:'新しい会社',email:'a@b.jp',site:'https://example.com/',name:'山田',...fields},{details_reviewed:undefined}),/事前に入っている項目も含め/);
  assert.equal(rows.length,n);
  const baseApplication={a:'pconf',new:'1',step:'2',co:'新しい会社',email:'a@b.jp',site:'example.com',name:'山田',...fields,memo:'保持する記述'};
  const badSite=send(baseApplication,{site:'@invalid'});
  assert.match(badSite,/有効なURLかドメイン/);
  assert.match(badSite,/name="site"[^>]+value="@invalid"/);
  assert.match(badSite,/保持する記述/);
  assert.match(badSite,/name="f_origin"[^>]+value="佐倉市"/);
  assert.equal(rows.length,n);
  const municipality={...baseApplication,f_radius:'都道府県・市区町村を指定'};
  assert.match(send(municipality),/対象の地域名か/);
  const perRequest={...baseApplication,f_radius:'依頼ごとに判断',f_radius_more:'要相談'};
  assert.match(send(perRequest),/対象の地域名か/);
  const schema=ctx.pconfAuto_({name:'新しい会社'});
  assert.equal(ctx.pconfValidate_(schema,{...municipality,f_radius_more:'大阪市・堺市'}).radius,undefined);
  assert.equal(ctx.pconfValidate_(schema,{...perRequest,f_radius_more:'大阪市発で受け渡し場所と車両の空きにより判断'}).radius,undefined);
  const cityDestination={...baseApplication,f_dest:'都道府県・市区町村を指定'};
  assert.match(send(cityDestination),/対象の地域名か/);
  assert.equal(ctx.pconfValidate_(schema,{...cityDestination,f_dest_more:'大阪市・神戸市・関西空港'}).dest,undefined);
  const conditionalDestination={...baseApplication,f_dest:'依頼ごとに判断',f_dest_more:'要相談'};
  assert.match(send(conditionalDestination),/対象の地域名か/);
  assert.equal(ctx.pconfValidate_(schema,{...conditionalDestination,f_dest_more:'大阪市から片道100km超は日程と車両の空きにより判断'}).dest,undefined);
  assert.equal(rows.length,n);
  const alteredSite=send(baseApplication,{site:'corrected.com'});
  assert.match(alteredSite,/規約の版または入力内容/);
  assert.match(alteredSite,/保持する記述/);
  assert.equal(rows.length,n);
  const ok=send({...baseApplication,site:'corrected.com',f_radius:'都道府県・市区町村を指定',f_radius_more:'大阪市・堺市'});
  assert.ok(ok.includes('ありがとうございました') && rows.length===n+1 && rows[n][1]==='（新規）' && rows[n][2]==='新しい会社' && rows[n][4].includes('a@b.jp') && rows[n][4].includes('大阪市・堺市') && !rows[n][4].includes('←サイトの内容から変更'));
  assert.equal(JSON.parse(rows[n][6]).site,'https://corrected.com');
  assert.equal(JSON.parse(rows[n][6]).intake_email,'a@b.jp');
  assert.match(JSON.parse(rows[n][6]).a.radius,/大阪市・堺市/);
  // 公式サイトの情報がある会社は全部開ける（例が出せるかどうかに関わらず、エラーにならない）
  ctx.DISPLAY_COMPANIES.forEach(x=>{ const h=ctx.pconfPage_({a:'pconf',t:ctx.demoToken_(x.id)}).html; assert.ok(h.includes('この内容で送る'), x.id); });
}
console.log('PASS: every company with site data gets a prefilled confirm page; new companies start from name, email and homepage');
// One-company prefill from public pages. No other company, rate engine, or intake state changes.
{
  const id='D01478c8', c=ctx.DISPLAY_COMPANIES.find(x=>x.id===id);
  const sameFields=ctx.pconfAuto_({name:c.name});
  const before=[rows.length,mails.length], originalExamples=ctx.pconfExamples_;
  let calls=0;
  ctx.pconfExamples_=v=>{ if(v.shop||v.fare) calls++; return originalExamples(v); };
  const ir=ctx.pconfOf_(id);
  assert.deepEqual(ir.sections.map(s=>s.items.map(i=>i.k)),sameFields.sections.map(s=>s.items.map(i=>i.k)));
  const fields=Object.fromEntries(ir.sections.flatMap(s=>s.items).map(i=>[i.k,i]));
  assert.equal(fields.origin.v,'大阪市北区');
  for(const k of ['radius','dest','hours','same','maxkg','riders','night_how','long','pick2','back','toll']) assert.ok(!fields[k].v&&!fields[k].mv,k);
  assert.match(fields.ride.v,/10kmまで：片道3,000円／往復5,400円/);
  assert.match(fields.ride.v,/30kmまで：片道6,800円／往復12,200円/);
  assert.match(fields.wait.v,/31〜45分300円、46〜60分600円/);
  assert.match(fields.night.note,/22:00〜翌7:00/);
  const h=ctx.pconfPage_({a:'pconf',t:ctx.demoToken_(id)}).html;
  assert.match(h,/アイアールサービス/);
  assert.match(h,/name="f_hours" maxlength="400" value=""/);
  assert.doesNotMatch(h,/6\. 料金の例|name="ex\d/);
  assert.equal(ir.examples.length,0);
  assert.equal(calls,0);
  // Transport and field checks only; these extra inputs are synthetic answers, not IR terms.
  const q={a:'pconf',t:ctx.demoToken_(id),name:'テスト担当',intake_email:'ir-bookings@example.test',
    f_origin:fields.origin.v,f_radius:'都道府県・市区町村を指定',f_radius_more:'大阪市・堺市',
    f_dest:'依頼ごとに判断',f_dest_more:'テスト：大阪市発で片道100km超は空き状況により判断',f_hours:'テスト：9時〜17時',f_animals:fields.animals.v,
    f_maxkg:'個別に判断：車の寸法と体重で判断',f_riders:'テスト：1人',f_petonly:'できない',
    f_tax:fields.tax.v,f_ride:fields.ride.v,f_pick:fields.pick.v,f_pick_more:fields.pick.mv,
    f_pick2:'行きの1回だけ',f_back:'かからない',f_wait:fields.wait.v,
    f_night:'22時〜7時は100円',f_night_how:'乗る時刻がその時間帯のとき',
    f_toll_5:'1',f_long:'〇kmを超えるとお見積もり（下に書いてください）',f_long_more:'30km',
    f_plate:fields.plate.v,f_car:'テスト車両1台'};
  assert.match(send({...q,f_night:''}),/各項目に修正箇所/);
  assert.match(send({...q,f_radius_more:'要相談'}),/対象の地域名か/);
  assert.match(send({...q,f_pick2:''}),/各項目に修正箇所/);
  assert.match(send({...q,f_dest_more:''}),/対象の地域名か/);
  assert.match(send(q,{intake_email:undefined}),/有効なメールアドレスを1件/);
  assert.match(send(q,{terms_accept:undefined}),/チェックしてください/);
  assert.deepEqual([rows.length,mails.length],before);
  assert.match(send(q),/ありがとうございました/);
  const stored=JSON.parse(rows.at(-1)[6]);
  assert.equal(stored.terms.version,ctx.PTERMS_VER.hash);
  assert.equal(stored.intake_email,'ir-bookings@example.test');
  assert.ok(!mails.at(-1)[1].includes('ir-bookings@example.test'));
  assert.match(stored.a.radius,/大阪市・堺市/);
  assert.match(stored.a.dest,/大阪市発で片道100km超は空き状況により判断/);
  assert.equal(rows.at(-1)[5],'');
  rows.pop(); mails.pop();

  assert.deepEqual([rows.length,mails.length],before);
  assert.ok(!Object.values(ctx.CONFIG.OPEN_PARTNERS).includes(id));
  assert.ok(ctx.pconfOf_('De5faaf3').examples.length);
  ctx.pconfExamples_=originalExamples;
}
console.log('PASS: IR only, same schema, public values, no speculative examples, no writes or acceptance changes.');
