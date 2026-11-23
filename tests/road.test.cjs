// お迎え・回送の距離は車の道のり（Nori 2026-11-01「直線距離はやめて。車での最短距離にして」）。取れないときだけ直線×1.3
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs', 'utf8'), ctx);
ctx.PropertiesService = { getScriptProperties: () => ({ getProperty: () => null, setProperty() {} }) };
ctx.partners_ = () => [];
const c = ctx.DISPLAY_COMPANIES.find(x => x.id === 'De5faaf3'); // COCOタク 杉並店：お迎え 1kmごと165円
const shop = { lat: c.shop[0], lng: c.shop[1] }, from = { lat: 35.69, lng: 139.70 }, to = { lat: 35.66, lng: 139.70 };
const when = new Date(Date.now() + 48 * 3600000 + 9 * 3600000).toISOString().slice(0, 10) + ' 13:00';
const p = { pref: '東京都', pickup: '新宿区', dropoff: '渋谷区', datetime: when, trip: '片道', weight: '5', pet_count: '1', riders: '1名', cage: '持っている', care: '不要',
  route_details: JSON.stringify({ km: 10, backKm: 10, from, to, backFrom: to, backTo: from }) };
// 道路データ：場所たち（from,to）のあとにお店たちが並ぶ行列。お店→from を 12.3km、to→お店を 20km にする
let urls = [];
ctx.UrlFetchApp = { fetch(url) {
  urls.push(url);
  const coords = url.split('/driving/')[1].split('?')[0].split(';').map(s => s.split(',').map(Number));
  const idx = coords.findIndex(([lng, lat]) => Math.abs(lat - shop.lat) < 1e-4 && Math.abs(lng - shop.lng) < 1e-4);
  const d = coords.map(() => coords.map(() => 5000));
  d[idx][0] = 12300; d[1][idx] = 20000;
  return { getResponseCode: () => 200, getContentText: () => JSON.stringify({ code: 'Ok', distances: d }) };
} };
const cards = ctx.displayCards_(ctx.selectionRide_(p), p);
const card = cards.find(x => x.id === c.id);
assert.equal(urls.length, 1, '道路データには1回だけ聞く');
assert.equal(card.price.local.pickup, 13 * 165, 'お迎えは車の道のり12.3km→13km×165円');
assert.match(card.price.pickupNote, /車の道のり/);
// 取れないときは直線×1.3（カードに概算と書く）
ctx.ROAD_KM = null;
ctx.UrlFetchApp = { fetch() { throw new Error('つながらない'); } };
const card2 = ctx.displayCards_(ctx.selectionRide_(p), p).find(x => x.id === c.id);
assert.equal(card2.price.local.pickup, Math.ceil(ctx.kmBetween_(shop, from) * 1.3) * 165);
assert.match(card2.price.pickupNote, /直線距離をもとにした概算/);
console.log('road ok');
