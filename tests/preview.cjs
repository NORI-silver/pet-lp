// Local-only preview. Uses the actual selection code with fictional partner records.
// Never calls Apps Script, writes reservations, or sends mail.
const http=require('node:http'), fs=require('node:fs'), path=require('node:path'), vm=require('node:vm'), crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite});
vm.runInContext(fs.readFileSync(path.join(root,'booking/Code.gs'),'utf8'),ctx);
ctx.selectionReview_=()=>null; // 口コミは外へ取りに行かない
if(process.env.PREVIEW_BOOKABLE)ctx.CONFIG.SHOW_ALL_CANDIDATES=false; // 依頼できる会社のカード（複数社の選択）を確かめるとき
ctx.sign_=s=>crypto.createHmac('sha256','local-preview-only').update(s).digest('hex');
ctx.Utilities={formatDate(d){return new Date(d.getTime()+9*3600000).toISOString().slice(0,16);}};
ctx.partners_=()=>['P002','P003','DEMO'].map((id,i)=>({id,name:['ペットエクスプレス','くりき','表示確認用の事業者'][i],active:true,areas:['東京'],email:'demo@example.invalid',big:true,careOk:true,cageMust:'不要',cageLend:true,riders:3,pets:5,luggage:true,hours:'0-24',lead:0,car:'ワンボックス',payMethod:'現地で直接お支払い',payWhen:''}));
let searches=0,requests=0,lastPartner='';
const fixtures=`<script>
const originalFetch=window.fetch.bind(window);
window.fetch=function(url,options){
 const u=String(url); let data;
 if(u.includes('msearch.gsi.go.jp')) { const q=new URL(u).searchParams.get('q'); data=[{properties:{title:q},geometry:{coordinates:q.includes('目黒')?[139.698,35.641]:[139.67,35.63]}}]; }
 else if(u.includes('nominatim.openstreetmap.org')) data=[{lat:'35.63',lon:'139.67'}];
 else if(u.includes('mreversegeocoder.gsi.go.jp')) data={results:{muniCd:'13112'}};
 else if(u.includes('router.project-osrm.org/table')) { const pts=new URL(u).pathname.split('/').pop().split(';').map(x=>x.split(',').map(Number)); const src=new URL(u).searchParams.get('sources').split(';').map(Number); const R=Math.PI/180,km=(a,b)=>6371*2*Math.asin(Math.sqrt(Math.sin((b[1]-a[1])*R/2)**2+Math.cos(a[1]*R)*Math.cos(b[1]*R)*Math.sin((b[0]-a[0])*R/2)**2)); data={code:'Ok',distances:src.map(i=>[Math.round(km(pts[i],pts[0])*1000*(1.2+(i%3)*0.2))])}; } // 確認用：直線×1.2〜1.6を道のりとして返す
 else if(u.includes('router.project-osrm.org')) data={code:'Ok',routes:[{distance:10000,duration:1200,legs:[{steps:[{name:'確認用高速道路',distance:5000}]}],geometry:{coordinates:[[139.67,35.63],[139.698,35.641]]}}]};
 if(data!==undefined) return Promise.resolve(new Response(JSON.stringify(data),{headers:{'Content-Type':'application/json'}}));
 return originalFetch(url,options);
};
</script>`;
http.createServer(async(req,res)=>{
 const url=new URL(req.url,'http://127.0.0.1');
 if(url.pathname==='/__state'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({searches,requests,lastPartner}));}
 if(url.pathname==='/demo-api' && req.method==='POST'){
  let raw='';for await(const chunk of req)raw+=chunk;
  const p=Object.fromEntries(new URLSearchParams(raw)); let result;
  if(p.kind==='quotes'){searches++;result=ctx.selectionQuotes_(p);}
  else if(p.kind==='scores'){const sc={};String(p.ids||'').split(',').forEach((id,i)=>{if(i%3!==2)sc[id]={rating:Math.round((3+((i*7)%20)/10)*10)/10,count:3+i*4};});result={ok:true,scores:sc};} // 確認用の点数（本物ではない）
  else if(p.split==='1'){ // 往復を行き・帰りで別の会社に
   const g=ctx.validateSelection_(ctx.legParams_(p,'go')), b=ctx.validateSelection_(ctx.withPick_(ctx.legParams_(p,'back'),p.back_partner_id,p.back_quote_token,p.back_quote_expires));
   if(g.ok&&b.ok){requests++;lastPartner=p.partner_id+'+'+p.back_partner_id;result={ok:true,id:'DEMO-GO',back_id:'DEMO-BACK'};} else result={ok:false,error:(g.ok?b:g).error};
  }
  else {result=ctx.validateSelection_(p);if(result.ok){requests++;lastPartner=p.partner_id;result={ok:true,id:'DEMO-ONLY'};}}
  res.setHeader('Content-Type','application/json');return res.end(JSON.stringify(result));
 }
 let filename=path.resolve(root,'.'+decodeURIComponent(url.pathname));
 if(!filename.startsWith(root+path.sep)&&filename!==root){res.statusCode=403;return res.end();}
 if(fs.existsSync(filename)&&fs.statSync(filename).isDirectory())filename=path.join(filename,'index.html');
 if(!fs.existsSync(filename)){res.statusCode=404;return res.end();}
 let body=fs.readFileSync(filename);
 const ext=path.extname(filename);res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.jpg':'image/jpeg','.webp':'image/webp','.png':'image/png','.svg':'image/svg+xml'})[ext]||'application/octet-stream');
 if(filename===path.join(root,'index.html'))body=body.toString().replace('var GAS_URL = "https://script.google.com/macros/s/AKfycbyy-cTvD-t8DFGhEyA2IbFiXWoB50kl_2_97WiVdMlXec8sIbI2NVUkkyn-45VkIMc_5g/exec";','var GAS_URL = "/demo-api";').replace('</head>',fixtures+'</head>').replace('<body>','<body><div style="padding:12px;background:#fff1b8;text-align:center;font-weight:bold">動作確認用：表示データはサンプルです。予約保存・メール送信は行いません。</div>');
 res.end(body);
}).listen(Number(process.env.PET_PREVIEW_PORT)||8765,'127.0.0.1',()=>console.log('Preview: http://127.0.0.1:8765/#form'));
