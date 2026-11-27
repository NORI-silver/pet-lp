// 料金の要約（facts の sum）：全文を消さない・金額は全文にあるものだけ・税や別料金の条件を落とさない（Nori 2026-11-27）
const fs=require('node:fs'),assert=require('node:assert/strict'),cp=require('node:child_process');
const d=JSON.parse(fs.readFileSync('tools/rojin.json','utf8'));
const must={ // 施設ごとに、要約に必ず残す条件（意味の確認。文字の有無だけで十分とはしない）
  R004:['110,000円','253,000円','396,000円','税の表示はない','3か月プランの表のみ','33,000円','終身一括は「―」','全文'],
  R005:['小型犬（5kg未満・13歳以上）','110,000円','550,000円','高くなる','577,500円','表示のまま'],
  R012:['税込110,000円','税込143,000円','税込176,000円','税込209,000円','6か月プラン','330,000円ずつ','預り金（一口）100,000円','介護料金が別'],
  R018:['体重7kgまでが936,000円','税の表示なし','何か月分かは画像に書かれていない','ほかの体重・要介護犬のプラン・1泊・デイサービスは金額が異なり全文に記載','100,000円'],
  R033:['小型110,000円','中型・大型は全文に記載','税の表示と体重の目安は公式の表にない','1,320,000円（内1か月分は保証金）','介護が必要な場合は介護料が別','介護A〜Cは1日あたり'],R107:['小型犬（8kg未満）165,000円','中型犬（20kg未満）198,000円','大型犬（35kg未満）231,000円','料金表に税の表示はない','6か月・1年','30,000円'],R130:['59,500円から、超大型犬（40kg以上）140,500円','税込・税別の表記は料金表にない','ほかの体重・3か月の料金は全文','月30,000円または50,000円','月100,000円または150,000円','食事介助・歩行介助・投薬介助はそれぞれ1か月15,000円'],
  R044:['入所金110,000円','45kg以上は要相談','2,200円'],R055:['税込','要相談'],R010:['超小型犬（5kg未満）143,000円から、大型犬（15〜20kg）231,000円','ほかの区分は全文に記載','税込','軽度60,000円から重度180,000円','医療予備費50,000円','20kg超は要相談'],
  R022:['小型犬95,000円から、超大型犬160,000円','税別の表示は1か月の表の直後のみ','日帰り・宿泊の表に税の表示はない','中型・大型犬・猫は全文に記載','日帰り・宿泊で各1,000円','1か月で15,000円'],R082:['税込','延長1時間ごとに500円'],
};
let n=0;
const recs={};
for(const h of d.homes){
  for(const f of (h.facts||[])){
    if(f.k!=='料金'||!f.sum) continue; n++; recs[h.id]=f;
    const figs=f.sum.match(/\d[\d,]*/g)||[];
    for(const g of figs) assert.ok(f.v.includes(g),`${h.id}: 要約の数字 ${g} が全文にない`);
    assert.ok(f.sum.length<f.v.length,`${h.id}: 要約が全文より短くない`);
    assert.ok(!/\d[\d,]*円まで/.test(f.sum),`${h.id}: 「◯円まで」は検査で止まる表示`);
    assert.ok(f.src&&f.checked,`${h.id}: 出典と確認日がない`);
    if(/税込/.test(f.sum)) assert.ok(/税込/.test(f.v),`${h.id}: 全文にない税込`);
    if(/税別/.test(f.sum)) assert.ok(/税別/.test(f.v),`${h.id}: 全文にない税別`);
if(h.id==='R022') assert.ok(!/いずれも税別/.test(f.v)&&/日帰り・宿泊の表には税の表示がない/.test(f.v),'R022: 全文の税の範囲');
    assert.ok(!/要確認|問い合わせ|連絡/.test(f.sum.replace('終身は問い合わせ','')),`${h.id}: 事業者への連絡をほのめかす語`);
  }
}
assert.ok(n>=12,'要約が12件未満');
for(const [id,ws] of Object.entries(must)){ assert.ok(recs[id],id+' に sum がない'); for(const w of ws) assert.ok(recs[id].sum.includes(w),`${id}: 要約に「${w}」がない`); }
// 実際のカード生成（cardpolicy.card）：全文が詳しく見るに一字も変わらず入り、出典と確認日が付く
const py=`
import json,sys,html
sys.path.insert(0,'tools'); import cardpolicy as cp
d=json.load(open('tools/rojin.json',encoding='utf-8')); out={}
for h in d['homes']:
    f=next((x for x in h.get('facts',[]) if isinstance(x,dict) and x.get('k')=='料金' and x.get('sum')),None)
    if not f: continue
    blk='<div class="emg-item emg-co fc cs" data-cat="rojin" data-fid="%s"><div class="fc-body"></div></div>'%h['id']
    t=html.unescape(cp.card(blk,h,'rojin'))
    top=t.split('<details')[0]; det=t.split('<details',1)[1]
    out[h['id']]=[f['sum'] in top, f['v'] not in top, ('料金（全文）：'+f['v']) in det and html.unescape(det).count(f['v'])==1, f['src'] in html.unescape(det) and f['checked'] in det]
print(json.dumps(out))`;
const r=cp.spawnSync('python3',['-c',py],{encoding:'utf8'});
if(r.status===0){ const o=JSON.parse(r.stdout); assert.equal(Object.keys(o).length,n,'生成したカードの数'); for(const [id,v] of Object.entries(o)) assert.deepEqual(v,[true,true,true,true],id+' のカード：上に要約・全文は詳しく見る・出典と日付'); }
else assert.fail('python3 でカードを作れない: '+r.stderr.slice(-300));
console.log('PASS: fee summaries keep every figure and condition; full fact verbatim in details with source and date ('+n+')');
