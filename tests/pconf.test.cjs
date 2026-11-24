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
const done=send({a:'pconf',t:tok,go:'1',name:'テスト',f_origin:'テスト駅',f_ng_area_0:'1',f_back:'別途確認',f_back_more:'確認用',ex0:'ちがう',ex0_fix:'4,600円'});
assert.match(page, /<form method="post" action="https:\/\/script\.google\.com[^"]+"/);
assert.match(page, /name="terms_accept" value="1" required>/);
assert.doesNotMatch(page, /name="terms_accept"[^>]+checked/);
assert.ok(done.includes('ありがとうございました') && rows.length===1 && mails.length===1);
assert.ok(rows[0][4].includes('行けない地域：沖縄県　←') && rows[0][4].includes('確認用') && rows[0][5].includes('ちがう（4,600円）'));
assert.ok(mails[0][1].includes('受付を始めるのは、運営者が確かめてから'));
assert.equal(JSON.parse(rows[0][6]).terms.version, ctx.PTERMS_VER.hash);
assert.equal(JSON.parse(rows[0][6]).terms.at, rows[0][0].toISOString());
assert.equal(JSON.parse(rows[0][6]).terms.surface, 'pconf-application');
const basic = {a:'pconf',t:tok,name:'テスト',f_back:'手入力を保持'};
for (const patch of [{terms_accept:undefined}, {terms_accept:'0'}, {terms_version:'old'}, {terms_proof:'wrong'}]) {
  const invalid = send(basic, patch);
  assert.match(invalid, /role="alert"/);
  assert.match(invalid, /手入力を保持/);
  assert.doesNotMatch(invalid, /name="terms_accept"[^>]+checked/);
}
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
  assert.equal(rows.length,n);
  const alteredSite=send(baseApplication,{site:'corrected.com'});
  assert.match(alteredSite,/規約の版または入力内容/);
  assert.match(alteredSite,/保持する記述/);
  assert.equal(rows.length,n);
  const ok=send({...baseApplication,site:'corrected.com',f_radius:'都道府県・市区町村を指定',f_radius_more:'大阪市・堺市'});
  assert.ok(ok.includes('ありがとうございました') && rows.length===n+1 && rows[n][1]==='（新規）' && rows[n][2]==='新しい会社' && rows[n][4].includes('a@b.jp') && rows[n][4].includes('大阪市・堺市') && !rows[n][4].includes('←サイトの内容から変更'));
  assert.equal(JSON.parse(rows[n][6]).site,'https://corrected.com');
  assert.match(JSON.parse(rows[n][6]).a.radius,/大阪市・堺市/);
  // 公式サイトの情報がある会社は全部開ける（例が出せるかどうかに関わらず、エラーにならない）
  ctx.DISPLAY_COMPANIES.forEach(x=>{ const h=ctx.pconfPage_({a:'pconf',t:ctx.demoToken_(x.id)}).html; assert.ok(h.includes('この内容で送る'), x.id); });
}
console.log('PASS: every company with site data gets a prefilled confirm page; new companies start from name, email and homepage');
