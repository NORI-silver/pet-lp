const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const clock=Date.parse('2026-11-25T11:00:00Z');
class FixedDate extends Date {constructor(...args){super(...(args.length?args:[clock]))}static now(){return clock}}
const run=(file)=>{
 const c=vm.createContext({Date:FixedDate,Utilities:{formatDate:(d,t,f)=>new Date(+d+9*3600000).toISOString().slice(0,f.length===10?10:16)}});vm.runInContext(fs.readFileSync(file,'utf8'),c);
 const mailbox='offline-only@pet-taxi-kasukabe.com';
 let pt={id:'P014',name:'COCOタク 春日部店',active:true,email:mailbox,lineId:'',areas:['埼玉','全国'],riders:2,pets:5,big:true,maxKg:50,maxBig:5,luggage:null,cageMust:'',cageLend:null,lendKg:null,rideHours:'0-24',hours:'0-24',lead:3,careOk:false,combo:[],vacProof:'混合・狂犬病',petOnly:false};
 let enabled=true,road=null,signatures=0;
 c.cocoIntakeSetting_=x=>x==='春日部'&&enabled?mailbox:'';
 c.partners_=()=>[pt]; c.loadRoadKm_=()=>{}; c.roadKm_=()=>road;
 c.demoId_=()=>''; c.demandLog_=()=>{}; c.pinfoExtra_=()=>null;
 c.quoteSignature_=()=>{signatures++;return 'NORMAL_PATH_OFFLINE_SIGNATURE'};
 function search(o={}){
  const P={species:'犬',weight:5,cage:'持ち込む',care:'不要',vaccine:o.vac?'済':'',rabies:o.vac?'済':''};
  const p={pref:'埼玉県',pickup:'春日部駅',dropoff:'大宮駅',datetime:'2026-11-26T06:25',trip:'片道',
   species:P.species,weight:'5',pet_count:'1',riders:'1人',cage:P.cage,care:P.care,pets_json:JSON.stringify([P]),
   route_details:JSON.stringify({from:{lat:35.979,lng:139.753},to:{lat:35.906,lng:139.624},km:17,backKm:17,routeEstimated:o.routeEstimated===true}),
   ...o.change};
  let result=c.selectionQuotes_(p);return {result, cards:(result.cards||[]).filter(x=>x.id==='P014'||x.id==='D853ae97')};
 }
 return {c,pt,search,setRoad:v=>{road=v},setEnabled:v=>{enabled=v},sig:()=>signatures};
};
const path=require('node:path');
const next=run(path.resolve(__dirname,'../booking/Code.gs'));
for(const datetime of ['2026-11-26T06:25','2026-11-26T12:00']){
 const [card]=next.search({change:{datetime}}).cards;
 assert.ok(card,datetime);assert.equal(card.id,'D853ae97');assert.equal(card.display_only,true);assert.equal(card.listed,true);
 assert.ok(card.price.amount>0);assert.ok(card.price.planNote.includes('受付可否'));assert.equal(card.token,undefined);assert.equal(card.site,'https://pet-taxi-kasukabe.com/');assert.equal(card.expires,undefined);
 assert.equal(next.sig(),0);
}
assert.equal(next.search({vac:true}).cards[0].display_only,true);
next.setRoad(2.1);
assert.equal(next.search({vac:true,routeEstimated:true}).cards[0].display_only,true);
assert.equal(next.sig(),0);
const open=next.search({vac:true}).cards;assert.equal(open.length,1);assert.equal(open[0].id,'P014');assert.ok(open[0].token);
const sign=next.sig();
for(const change of [{riders:'3人'},{care:'必要'},{pref:'沖縄県'},{dropoff:'沖縄県那覇市'},{datetime:'2026-11-25T21:00'},{leg:'go'},
{weight:'51',pets_json:JSON.stringify([{species:'犬',weight:51}])}]){
 assert.equal(next.search({change}).cards.length,0,JSON.stringify(change));
}
// 20:00 JST + 3h45 passes global lead, but same-day display still needs confirmed lead_days=0.
assert.equal(next.search({change:{datetime:'2026-11-25T23:45'}}).result.ok,true);
assert.equal(next.search({change:{datetime:'2026-11-25T23:45'}}).cards.length,0);
const long=next.search({change:{route_details:JSON.stringify({from:{lat:35.979,lng:139.753},to:{lat:35.906,lng:139.624},km:50,backKm:50})}}).cards[0];
assert.equal(long.price.amount,null); assert.equal(long.price.text,'料金は店舗でご確認ください');
next.pt.rideHours='8-18'; assert.equal(next.search().cards.length,0); next.pt.rideHours='0-24';
next.pt.active=false; assert.equal(next.search().cards.length,0); next.pt.active=true;
const oldPause=next.c.publicPaused_; next.c.publicPaused_=k=>k==='P014'||oldPause(k);
assert.equal(next.search().cards.length,0); next.c.publicPaused_=oldPause;
const unknown=next.search({change:{route_details:'{}'}}).cards[0];
assert.equal(unknown.price.amount,null);assert.equal(unknown.display_only,true);
assert.equal(next.sig(),sign);
console.log('PASS quote entrypoint: morning/noon, absent/complete vaccines, road missing/estimated/verified, distinct no-token display vs normal selectable, no duplicates, paused/weight/riders/area/care/time hard blocks.');
