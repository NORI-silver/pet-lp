// 提携のご案内ページの「画面の見本」画像を作る（node tools/partner_shots.cjs）。
// booking/Code.gs の本物の文面・画面を、架空の依頼で表示して撮る。何も送らない・保存しない。
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'), out=path.join(root,'img/partner');
fs.mkdirSync(out,{recursive:true});
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite});
vm.runInContext(fs.readFileSync(path.join(root,'booking/Code.gs'),'utf8'),ctx);
ctx.sign_=s=>crypto.createHmac('sha256','shots-only').update(s).digest('hex');
ctx.Utilities={formatDate(d,tz,f){const j=new Date(d.getTime()+9*3600000),z=n=>String(n).padStart(2,'0');const t={yyyy:j.getUTCFullYear(),MM:z(j.getUTCMonth()+1),M:j.getUTCMonth()+1,dd:z(j.getUTCDate()),d:j.getUTCDate(),HH:z(j.getUTCHours()),H:j.getUTCHours(),mm:z(j.getUTCMinutes())};return f.replace(/'([^']*)'/g,'\u0000$1\u0000').split('\u0000').map((x,i)=>i%2?x:x.replace(/yyyy|MM|M|dd|d|HH|H|mm/g,k=>t[k])).join('');}};
let html='';
ctx.HtmlService={createHtmlOutput:h=>{html=h;const o={setTitle:()=>o,addMetaTag:()=>o};return o;}};
ctx.linkBase_=()=>'https://pet.shiokonbu.com/go/';
const pt={id:'P900',name:'見本ペットタクシー',person:'',active:true,areas:['東京'],email:'x@example.invalid',big:true,careOk:true,cageMust:'不要',cageLend:true,riders:3,pets:5,luggage:true,hours:'0-24',lead:0,car:'ワンボックス',payMethod:'現金',payWhen:'降りるとき'};
ctx.partners_=()=>[pt];ctx.partnerById_=()=>pt;
const when=new Date('2026-11-20T01:30:00Z'); // 10:30 JST
const r={'受付番号':'R-見本','状態':ctx.ST.OPEN,'依頼の種類':'問い合わせ','希望日時':when,'片道・往復':'片道','都府県':'東京','お迎えの場所':'世田谷区 桜新町駅の近く','行き先':'目黒区の動物病院','種類':'犬','犬種・猫種':'柴犬','体重kg':'10','年齢':'12','性別':'','キャリー':'持っている','介助':'不要','同乗人数':'1人','荷物':'少なめ','ペット数':'1','指定した提携先ID':'P900,P901,P902','概算料金':'','見積もりJSON':'[]'};
ctx.findReq_=()=>({rowIndex:2,data:r});
const mail=ctx.requestText_(r,pt);
const subject='【空き状況と料金のお問い合わせ】東京・'+ctx.whenText_(r);
ctx.acceptPage_({a:'accept',id:'R-見本',p:'P900',k:ctx.sign_('R-見本:P900')});
const accept=html;
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const mailHtml=`<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#f3f1ee;font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;color:#1c1a18}
.m{max-width:560px;margin:0 auto;background:#fff;min-height:100vh}.h{padding:16px 18px;border-bottom:1px solid #eee}.s{font-weight:800;font-size:17px;line-height:1.5}.f{font-size:13px;color:#6b665f;margin-top:6px}
.b{padding:16px 18px;white-space:pre-wrap;font-size:14px;line-height:1.75;word-break:break-all}.b a{color:#1a5fd0}</style>
<div class="m"><div class="h"><div class="s">${esc(subject)}</div><div class="f">差出人：ペットタクシー予約窓口</div></div><div class="b">${esc(mail).replace(/(https:\/\/\S+)/g,'<a>$1</a>')}</div></div>`;
(async()=>{
 const b=await chromium.launch({args:['--lang=ja-JP']});const p=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:2,locale:'ja-JP'});
 for(const [name,h] of [['mail',mailHtml],['reply',accept]]){
  await p.setContent(h,{waitUntil:'load'});
  if(name==='reply'){await p.fill('input[name=fare]','5200');await p.fill('textarea[name=msg]','前日にお電話でお迎えの場所を確認します');await p.evaluate(()=>{const i=document.querySelector('input[name=at]');i.type='text';i.value='2026/11/20 10:30';document.activeElement.blur();});} // 撮る環境が英語なので、日時の欄だけ日本の表示にする
  const png=path.join(out,name+'.png');await p.screenshot({path:png,fullPage:true});
  if(name==='reply'){ // 依頼内容の箱（メールと同じ）は省き、題名と入力欄だけをつなげる
   const box=await p.evaluate(()=>{const b=document.querySelectorAll('.box');const r1=b[0].getBoundingClientRect(),r2=b[1].getBoundingClientRect();return [r1.top+scrollY,r2.bottom+scrollY];});
   require('node:child_process').execFileSync('python3',['-c',`from PIL import Image
im=Image.open('${png}');w,h=im.size;a=int(${box[0]}*2)-8;c=int(${box[1]}*2)+16
top=im.crop((0,0,w,a));bot=im.crop((0,c,w,h));n=Image.new('RGB',(w,top.height+bot.height),'white');n.paste(top,(0,0));n.paste(bot,(0,top.height));n.save('${png}')`]);
  }
 }
 await b.close();
 // ページで使うのは webp だけ（png は消す）
 for(const n of ['mail','reply']){require('node:child_process').execFileSync('python3',['-c',`from PIL import Image;im=Image.open('${out}/${n}.png');im.save('${out}/${n}.webp','WEBP',quality=80);print(im.size)`],{stdio:'inherit'});fs.unlinkSync(path.join(out,n+'.png'));}
 console.log('ok');
})();
