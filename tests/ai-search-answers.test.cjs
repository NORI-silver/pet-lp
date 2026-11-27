'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const read=p=>fs.readFileSync(p,'utf8');
function publiclyReadable(s){
  assert.doesNotMatch(s, /<meta name="robots" content="[^"]*(?:noindex|nosnippet)/);
}
function block(page,id){
  const s=read(page);
  publiclyReadable(s);
  const start=s.indexOf('id="'+id+'"');
  assert.ok(start>=0,id);
  const body=s.slice(start,start+12000);
  assert.match(body,/<h3>[^<]+<\/h3><p>/);
  return body;
}
test('千葉：静的本文で同じ体重の一任料金を比べ、出典と追加費用が読める',()=>{
  const s=block('sougi/chiba/index.html','chiba-cremation-cost');
  for (const x of ['21,500円','23,650円','25,000円','31,350円','骨つぼの大きさにより追加費用','https://ichikawa-pet.co.jp/price','https://www.pet594.com/plan/pet-kobetsuso/']) assert.ok(s.includes(x),x);
});
test('大阪：夜間の人・施設カメラ、税込と税抜、上限と料金区分を混同しない',()=>{
  const s=block('pet-hotel/osaka/index.html','osaka-large-stay');
  for (const x of ['24時間11,000円（税込）','大型犬24時間11,000円（税抜）','スタッフは不在','犬の体重上限','https://dogfirst-osaka.com/hotel/','https://blissdog.jp/?page_id=81']) assert.ok(s.includes(x),x);
});
