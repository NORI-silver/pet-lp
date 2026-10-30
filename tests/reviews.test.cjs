const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const props = {PLACES_API_KEY:'k', 'PLACE_ID_P002_ペットエクスプレス 世田谷区上馬':'PID'};
ctx.PropertiesService = {getScriptProperties:()=>({getProperty:k=>props[k]||null,setProperty:(k,v)=>{props[k]=v;}})};
ctx.Utilities = {formatDate:()=> '202610'};
ctx.log_ = ()=>{};
let asked = [];
ctx.UrlFetchApp = {fetch:(url,o)=>{ asked.push(o.headers['X-Goog-FieldMask']); return {getResponseCode:()=>200,getContentText:()=>JSON.stringify({rating:4.8,userRatingCount:6,reviews:[
  {rating:5,relativePublishTimeDescription:'1か月前',text:{text:'やさしい運転でした'},authorAttribution:{displayName:'A',uri:'https://maps.example/a',photoUri:'https://img.example/a'},googleMapsUri:'https://maps.example/r1'}]})}; }};
const r = JSON.parse(JSON.stringify(ctx.selectionReviews_('P002')));
assert.equal(r.ok, true);
assert.equal(r.reviews[0].author, 'A'); assert.equal(r.reviews[0].authorUrl, 'https://maps.example/a'); assert.equal(r.reviews[0].url, 'https://maps.example/r1');
assert.ok(asked[0].includes('reviews'));
assert.equal(ctx.selectionReviews_('NOPE').ok, false);           // 提携先でない会社は取り寄せない
assert.equal(props.REVIEW_COUNT_202610, '1');                     // 月の回数に数える
const score = JSON.parse(JSON.stringify(ctx.selectionReview_({id:'P002'})));
assert.deepEqual(score, {rating:4.8, count:6});                   // カードの点数にはリンクを付けない
console.log('PASS: reviews come with author and per-review links, count against the monthly cap, unknown partners refused');
