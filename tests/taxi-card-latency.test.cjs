'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const script = fs.readFileSync(new URL('../app.js', 'file://' + __filename), 'utf8');
const begin = script.indexOf('  function showEstimate(){');
const end = script.indexOf('\n  // 入力を変えたら、前の結果', begin);
assert.ok(begin >= 0 && end > begin, 'generated taxi form contains showEstimate');

const a = {lat:35.67, lng:139.70}, b = {lat:35.64, lng:139.69};
const go = {km:10, hw:2, min:20}, back = {km:13, hw:1, min:28};
const tick = () => new Promise(resolve => setImmediate(resolve));
function run(trip, initialPref = '東京都') {
  const calls = [], fields = {
    pref:{value:initialPref}, pickup:{value:'出発'}, dropoff:{value:'到着'},
    retOther:{checked:false}, estMap:{}, partnerResults:{}, prefFix:{}
  };
  let resolvePref;
  const prefJob = new Promise(resolve => { resolvePref = resolve; });
  const c = vm.createContext({
    routeDetails:null, estSeq:0, lastKm:0, lastKmHigh:0, lastFare:'', lastFareNum:0, est:{},
    form:{querySelector(q){return {value:q.includes('via_on') ? 'なし' : trip};}},
    $:id=>fields[id], clearPartners(){}, showLoading(){}, partnerBlock:()=>'', NO_PICK:[],
    geocode:q=>Promise.resolve(q==='出発' ? a : b), prefOf:()=>prefJob,
    routeOf:pts=>{ calls.push(pts[0] === a ? 'go' : 'back'); return Promise.resolve(pts[0] === a ? go : back); },
    localOf:r=>({...r, km:r.km + 0.15*r.hw}), kmOf:r=>r.km,
    queuePartners:now=>{ assert.equal(now, true); calls.push('quotes'); },
    drawMap:()=>calls.push('map'), setSelect:(el,v)=>{el.value=v;}, estNow:()=>calls.push('recheck')
  });
  vm.runInContext(script.slice(begin,end) + '\nshowEstimate();', c);
  return {c, calls, fields, resolvePref};
}

test('片道：県の確認中に行きの経路だけを調べ、料金を地図より先に聞く', async () => {
  const {c, calls, resolvePref} = run('片道');
  await tick();
  assert.deepEqual(calls, ['go']);
  resolvePref('東京都');
  await tick();
  assert.deepEqual(calls, ['go','quotes','map']);
  assert.equal(c.routeDetails.km, 10.3);
  assert.equal(c.routeDetails.highKm, 10);
  assert.equal(c.routeDetails.highBackKm, 10); // highway fare validation expects both values, even for a one-way trip
});

test('往復：行きと帰りを別々に調べ、往復の料金用の距離を維持する', async () => {
  const {c, calls, resolvePref} = run('往復');
  await tick();
  assert.deepEqual(calls, ['go','back']);
  resolvePref('東京都');
  await tick();
  assert.deepEqual(calls, ['go','back','quotes','map']);
  assert.equal(c.routeDetails.km, 10.3);
  assert.equal(c.routeDetails.backKm, 13.15);
  assert.equal(c.routeDetails.highBackKm, 13);
});

test('県が食い違うときは先に直し、古い県で候補を取り寄せない', async () => {
  const {c, calls, fields, resolvePref} = run('片道', '千葉県');
  await tick();
  resolvePref('東京都');
  await tick();
  assert.deepEqual(calls, ['go', 'recheck']);
  assert.equal(fields.pref.value, '東京都');
  assert.equal(c.routeDetails, null);
});

test('同じ住所の検索が進行中なら、時刻が変わっても取り寄せは1回', async () => {
  const start = script.indexOf('  function geocode(q, near){');
  const stop = script.indexOf('\n  // 位置から都県を調べる', start);
  assert.ok(stop > start && start >= 0);
  let asked = 0, resolve;
  const request = new Promise(r => { resolve = r; });
  const c = vm.createContext({
    geoCache:{}, geoPending:Object.create(null), pickedPlace:{}, PREF_HEAD:/^東京都/,
    $:()=>({value:'東京都'}), looksAddress:()=>true,
    gsi:()=>{asked++;return request;}, osm:()=>null
  });
  vm.runInContext(script.slice(start, stop), c);
  const p1 = c.geocode('東京都渋谷区道玄坂1丁目', false);
  const p2 = c.geocode('東京都渋谷区道玄坂1丁目', false);
  assert.equal(p1,p2);
  await tick();
  assert.equal(asked,1);
  resolve(a);
  assert.equal(await p1,a);
  assert.equal(await c.geocode('東京都渋谷区道玄坂1丁目', false),a);
  assert.equal(asked,1);
});

test('問い合わせ文のコピーはなく、公式サイトへ進むリンクは残る', () => {
  assert.doesNotMatch(script, /copyAsk|copy-ask|問い合わせ文をコピー/);
  assert.match(script, /公式サイトで問い合わせ ↗/);
  assert.match(script, /track\("official_site", o\)/);
});
