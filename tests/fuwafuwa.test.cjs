// ふわふわペットタクシー（P066）：提携の確認ページの答え（2026-11-14）どおりに計算・絞り込みをする
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite,isNaN,
  PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'secret'})},
  Session:{getEffectiveUser:()=>({getEmail:()=>'admin@example.com'})},
  Utilities:{computeHmacSha256Signature:(s,k)=>[...crypto.createHmac('sha256',k).update(s).digest()],base64EncodeWebSafe:(b)=>Buffer.from(b).toString('base64').replace(/\+/g,'-').replace(/\//g,'_')}});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
assert.equal(ctx.isOpen_('P066'),true); assert.equal(ctx.openDisplay_('P066').id,'D5598693');
const c=vm.runInContext("DISPLAY_COMPANIES.filter(function(x){return x.id==='D5598693';})[0]",ctx);
const shop={lat:c.shop[0],lng:c.shop[1]};
// お迎えの場所（起点から道のり pk km）と行き先を作り、道のりを ROAD_KM に入れて計算する
let n=0;
function quote(pk, km, time){
  n++; const from={lat:35.3+n*0.01,lng:139.3}, to={lat:35.9,lng:139.9};
  vm.runInContext('ROAD_KM = ROAD_KM || {}',ctx);
  ctx.ROAD_KM[ctx.roadKey_(shop,from)]=pk; ctx.ROAD_KM[ctx.roadKey_(to,shop)]=pk+km;
  const r=ctx.displayPriceCalc_(c,{trip:'片道',pref:'神奈川県',datetime:'2026-12-01T'+time,pickup:'横浜市',dropoff:'動物病院',weight:5,pet_count:1,
    route_details:JSON.stringify({km,backKm:km,from,to,backFrom:to,backTo:from})});
  return r && r.amount;
}
assert.equal(quote(5,10,'10:00'),4100);    // 横浜市泉区（起点から5km）→ 10km、昼
assert.equal(quote(20,30,'10:00'),10100);  // 起点から20km → 30km、昼（お迎え 20km×100円）
assert.equal(quote(10,20,'23:00'),8930);   // 起点から10km → 20km、23時（実走の3割増し＋お迎え1,000円）
assert.equal(quote(10,120,'23:00'),quote(10,120,'10:00')); // 100km以上は深夜割増なし
assert.equal(quote(450,450,'10:00'),null); // 大阪（起点から450km）→ 横浜：割引があるのでお見積もり
console.log('PASS: ふわふわの料金は平さんが「合っている」と答えた計算例と同じ');
// 往復でもお迎え対応費は行きの1回だけ
{
  const from={lat:35.2,lng:139.2}, to={lat:35.95,lng:139.95};
  ctx.ROAD_KM[ctx.roadKey_(shop,from)]=20; ctx.ROAD_KM[ctx.roadKey_(shop,to)]=40; ctx.ROAD_KM[ctx.roadKey_(to,shop)]=40; ctx.ROAD_KM[ctx.roadKey_(from,shop)]=20;
  const r=ctx.displayPriceCalc_(c,{trip:'往復',pref:'神奈川県',datetime:'2026-12-01T10:00',return_datetime:'2026-12-01T15:00',pickup:'A',dropoff:'B',weight:5,pet_count:1,
    route_details:JSON.stringify({km:30,backKm:30,from,to,backFrom:to,backTo:from})});
  assert.equal(r.local.pickup,2000);
}
console.log('PASS: 往復でもお迎え対応費は1回分');
// 絞り込み：行けない地域・関東を通らない依頼・乗る距離がお迎えより短い依頼は出さない
const ride=(pref,dropoff,from,to,km)=>({'都府県':pref,'行き先':dropoff,_route:{km,from,to}});
const yokohama={lat:35.466,lng:139.622}, yoyogi={lat:35.672,lng:139.695}, osaka={lat:34.702,lng:135.496}, fukuoka={lat:33.59,lng:130.42}, naha={lat:26.21,lng:127.68};
assert.equal(ctx.reachOk_(c,'神奈川',ride('神奈川','代々木公園（渋谷区）',yokohama,yoyogi,30)),true);
assert.equal(ctx.reachOk_(c,'大阪',ride('大阪','横浜駅（横浜市西区）',osaka,yokohama,450)),true);  // 行き先が関東（県名なしでも位置で）
assert.equal(ctx.reachOk_(c,'大阪',ride('大阪','福岡県福岡市',osaka,fukuoka,620)),false);        // 関東を通らない
assert.equal(ctx.reachOk_(c,'大阪',ride('大阪','大阪府吹田市',osaka,{lat:34.76,lng:135.52},10)),false); // 乗る距離がお迎えより短い
assert.equal(ctx.reachOk_(c,'沖縄',ride('沖縄','神奈川県横浜市',naha,yokohama,1600)),false);      // 行けない地域
assert.equal(ctx.reachOk_(c,'神奈川',ride('神奈川','沖縄県那覇市',yokohama,naha,1600)),false);
console.log('PASS: ふわふわの絞り込み（行けない地域・関東近県・乗る距離）');
