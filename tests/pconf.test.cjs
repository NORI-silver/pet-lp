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
  assert.ok(known.includes('3,300円で5kmまで') && known.includes('name="co" value="杉並店"'), 'known site gets prefilled');
  const blank=ctx.pconfPage_({a:'pconf','new':'1',step:'2',co:'新しい会社',email:'a@b.jp',site:'https://example.com/'}).html;
  assert.ok(blank.includes('1. どこへ行けるか') && !blank.includes('サイトより') && !blank.includes('6. 料金の例'), 'unknown site is blank');
  const n=rows.length;
  assert.ok(ctx.pconfPage_({a:'pconf','new':'1',step:'2',go:'1',co:'新しい会社',email:'bad',name:'山田'}).html.includes('メールアドレス'));
  const ok=ctx.pconfPage_({a:'pconf','new':'1',step:'2',go:'1',co:'新しい会社',email:'a@b.jp',site:'https://example.com/',name:'山田',f_radius:'上限なし',f_plate:'黒ナンバー（貨物軽自動車の届出）'}).html;
  assert.ok(ok.includes('ありがとうございました') && rows.length===n+1 && rows[n][1]==='（新規）' && rows[n][2]==='新しい会社' && rows[n][4].includes('a@b.jp') && rows[n][4].includes('上限なし') && !rows[n][4].includes('←サイトの内容から変更'));
  // 公式サイトの情報がある会社は全部開ける（例が出せるかどうかに関わらず、エラーにならない）
  ctx.DISPLAY_COMPANIES.forEach(x=>{ const h=ctx.pconfPage_({a:'pconf',t:ctx.demoToken_(x.id)}).html; assert.ok(h.includes('この内容で送る'), x.id); });
}
console.log('PASS: every company with site data gets a prefilled confirm page; new companies start from name, email and homepage');
