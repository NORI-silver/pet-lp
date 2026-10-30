// Local-only preview. Uses the actual selection code with fictional partner records.
// Never calls Apps Script, writes reservations, or sends mail.
const http=require('node:http'), fs=require('node:fs'), path=require('node:path'), vm=require('node:vm'), crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite});
vm.runInContext(fs.readFileSync(path.join(root,'booking/Code.gs'),'utf8'),ctx);
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
 else if(u.includes('router.project-osrm.org')) data={code:'NoRoute'};
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
  else {result=ctx.validateSelection_(p);if(result.ok){requests++;lastPartner=p.partner_id;result={ok:true,id:'DEMO-ONLY'};}}
  res.setHeader('Content-Type','application/json');return res.end(JSON.stringify(result));
 }
 let filename=path.resolve(root,'.'+decodeURIComponent(url.pathname));
 if(!filename.startsWith(root+path.sep)&&filename!==root){res.statusCode=403;return res.end();}
 if(fs.existsSync(filename)&&fs.statSync(filename).isDirectory())filename=path.join(filename,'index.html');
 if(!fs.existsSync(filename)){res.statusCode=404;return res.end();}
 let body=fs.readFileSync(filename);
 const ext=path.extname(filename);res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.jpg':'image/jpeg','.webp':'image/webp','.png':'image/png','.svg':'image/svg+xml'})[ext]||'application/octet-stream');
 if(filename===path.join(root,'index.html'))body=body.toString().replace('var GAS_URL = "https://script.google.com/macros/s/AKfycbyxsd8L8g_5Nt3HnApx2ZQnXFyPBsNfuHSvBlJKRVDtAIVr0EnqB-0raxwMPNOVl_Jg/exec";','var GAS_URL = "/demo-api";').replace('</head>',fixtures+'</head>').replace('<body>','<body><div style="padding:12px;background:#fff1b8;text-align:center;font-weight:bold">動作確認用：表示データはサンプルです。予約保存・メール送信は行いません。</div>');
 res.end(body);
}).listen(8765,'127.0.0.1',()=>console.log('Preview: http://127.0.0.1:8765/#form'));
