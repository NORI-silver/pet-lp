// 候補カードの星をまとめて取り寄せる（selectionScores_）。表示だけの会社も、名前を確かめて場所を決め、月の上限を守る
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const dc = vm.runInContext('DISPLAY_COMPANIES', ctx).filter(c => c.review_q && c.review_name);
assert.ok(dc.length >= 50, '表示だけの会社に口コミを探すことばが入っている');
const a = dc[0], b = dc[1];
const props = {PLACES_API_KEY:'k', REVIEW_COUNT_202610:'0'};
ctx.PropertiesService = {getScriptProperties:()=>({getProperty:k=>props[k]||null,setProperty:(k,v)=>{props[k]=v;}})};
ctx.Utilities = {formatDate:()=> '202610'};
ctx.log_ = ()=>{};
let calls = [];
const resp = (o) => ({getResponseCode:()=>200,getContentText:()=>JSON.stringify(o)});
ctx.UrlFetchApp = {fetchAll:(reqs)=>reqs.map(q=>{ calls.push(q.url);
  if (q.url.includes('searchText')) {
    const t = JSON.parse(q.payload).textQuery;
    if (t === a.review_q) return resp({places:[{id:'X',displayName:{text:'ちがうお店'}},{id:'PA',displayName:{text:a.review_name+' 本店'}}]});
    return resp({places:[{id:'Z',displayName:{text:'ちがうお店'}}]}); // b は名前が合わない
  }
  return resp({rating:4.2,userRatingCount:12});
})};
let r = JSON.parse(JSON.stringify(ctx.selectionScores_([a.id,b.id,'NOPE',a.id].join(','))));
assert.deepEqual(r.scores, {[a.id]:{rating:4.2,count:12}});
assert.equal(props['PLACE_ID_D_'+a.id+'_'+a.review_q], 'PA');     // 名前の合う場所を選ぶ
assert.equal(props['PLACE_ID_D_'+b.id+'_'+b.review_q], '-');      // 合わなければ星を出さない
assert.equal(props.REVIEW_COUNT_202610, '1');                       // 点数の取り寄せだけを数える
calls = [];
ctx.selectionScores_(a.id);
assert.equal(calls.filter(u=>u.includes('searchText')).length, 0); // 場所のIDは覚えている
props.REVIEW_COUNT_202610 = '900';
calls = [];
r = JSON.parse(JSON.stringify(ctx.selectionScores_(a.id)));
assert.deepEqual(r.scores, {}); assert.equal(calls.length, 0);      // 月の上限を超えたら取り寄せない
assert.equal(ctx.selectionReviews_(a.id).ok !== undefined, true);   // 表示だけの会社も口コミ本文を見られる
console.log('PASS: scores fetched in one batch, place names checked, monthly cap kept');
