const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
const ctx=vm.createContext({});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const companies=JSON.parse(fs.readFileSync('tools/display_companies.json','utf8')).companies;
const a={lat:35.97,lng:139.75}, b={lat:35.91,lng:139.72};
function quote(id,pickup,km=10,time='12:00') {
  const c=ctx.DISPLAY_COMPANIES.find(x=>x.id===id);
  ctx.roadKm_=()=>pickup;
  return ctx.displayPrice_(c,{datetime:'2026-11-27T'+time,trip:'片道',weight:5,
    route_details:JSON.stringify({km,backKm:km,from:a,to:b})});
}
const K='D853ae97', Y='D7f0d2a2';
assert.equal(companies.find(c=>c.id===K).fare.pick.kmMode,'nearest');
assert.equal(companies.find(c=>c.id===Y).fare.pick.kmMode,undefined);
for (const [km,charged] of [[0.49,0],[0.5,1],[29.49,29],[29.5,30],[30,30],[30.1,30],[30.5,31]]) {
  assert.equal(quote(K,km).local.pickup,165*charged);
}
assert.equal(quote(K,5,10.1).local.ride,4290,'riding distance remains rounded upward');
assert.equal(quote(Y,30.1).local.pickup,5115,'Kyoto remains rounded upward');
for (const [pk,km,t,yen] of [[5,10,'12:00',4950],[20,30,'12:00',10725],[10,20,'23:00',10725],[60,80,'12:00',25575]]) {
  assert.equal(quote(K,pk,km,t).amount,yen);
}
console.log('PASS: Kasukabe pickup only uses half-up to whole km; four approved samples, occupied distance and Kyoto unchanged.');
