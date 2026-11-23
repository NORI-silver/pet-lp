const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const props = {PLACES_API_KEY:'k'};
ctx.PropertiesService = {getScriptProperties:()=>({getProperty:k=>props[k]||null,setProperty:(k,v)=>{props[k]=v;}})};
ctx.Utilities = {formatDate:()=> '202610'};
ctx.log_ = ()=>{};
ctx.sign_ = (s)=> 'KEY-' + s;
ctx.DASH_DATA = [{id:'K001',pref:'東京都',name:'ペットエクスプレス',review_q:'ペットエクスプレス 世田谷',review_name:'ペットエクスプレス'},
  {id:'K002',pref:'東京都',name:'別の会社',review_q:'別の会社',review_name:'別の会社'}];
let calls = [];
ctx.UrlFetchApp = {fetch:(url,o)=>{ calls.push(url);
  if (url.includes('searchText')) { const q = JSON.parse(o.payload).textQuery;
    return {getContentText:()=>JSON.stringify({places: q.includes('エクスプレス') ? [{id:'PID',displayName:{text:'ペットエクスプレス'}}] : [{id:'X',displayName:{text:'まったく違うお店'}}]})}; }
  return {getResponseCode:()=>200,getContentText:()=>JSON.stringify({displayName:{text:'ペットエクスプレス'},rating:4.8,userRatingCount:6,googleMapsUri:'https://maps.example/p'})}; }};
assert.equal(ctx.dashScores('wrong', ['K001']).ok, false);                       // リンクの鍵が違えば取り寄せない
const r = JSON.parse(JSON.stringify(ctx.dashScores('KEY-dash', ['K001','K002','K999'])));
assert.deepEqual(r.scores.K001, {rating:4.8,count:6,place:'ペットエクスプレス',url:'https://maps.example/p'});
assert.equal(r.scores.K002.error, 'notfound');                                    // 名前が合わない場所は出さない
assert.equal(r.scores.K999, undefined);
assert.equal(props['PLACE_ID_D_K001_ペットエクスプレス 世田谷'], 'PID');               // 保存するのは場所のIDだけ
assert.equal(props.REVIEW_COUNT_202610, '1'); assert.equal(props.REVIEW_DASH_COUNT_202610, '1');
props.REVIEW_DASH_COUNT_202610 = String(ctx.CONFIG.REVIEW_DASH_MONTHLY_LIMIT);
assert.equal(ctx.dashScores('KEY-dash', ['K001']).scores.K001.error, 'limit');    // 一覧の上限を超えたら取り寄せない
new Function('var DASH=[],DASH_KEY="";' + ctx.DASH_JS.replace(/draw\(\);\s*$/, ''));  // ページのスクリプトが読める
assert.ok(!/<\/script/i.test(ctx.DASH_BODY));
console.log('PASS: dashboard reviews need the link key, match place names, store only place IDs, respect the monthly cap');
