// 公式サイトの定額（空港送迎など）と、書き写した料金表（ラッキー・ミント）の計算（Nori 2026-11-02「空港とか定額が載ってるならそれ使ってよあたりまえ」）
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs', 'utf8'), ctx);
const C = id => ctx.DISPLAY_COMPANIES.find(x => x.id === id);
const from = { lat: 35, lng: 135 }, to = { lat: 35.1, lng: 135.1 };
function price(id, o) {
  const c = C(id), shop = { lat: c.shop[0], lng: c.shop[1] };
  const road = {}; road[ctx.roadKey_(shop, from)] = o.pick; road[ctx.roadKey_(to, shop)] = o.back || 0;
  ctx.ROAD = road; vm.runInContext('ROAD_KM = ROAD', ctx);
  return ctx.displayPrice_(c, { pref: o.pref || '', trip: o.trip || '片道', pickup: o.pickup, dropoff: o.dropoff, datetime: o.at,
    return_pickup: o.rp, return_dropoff: o.rd, return_datetime: o.rat,
    route_details: JSON.stringify({ km: o.km, backKm: o.km, from, to, backFrom: to, backTo: from }) });
}
// ラッキーペットサービス：見積もりの返事と1円まで同じ
assert.equal(price('D72024d3', { pickup: '神戸市灘区 JR六甲道駅', dropoff: '尼崎市立花町3丁目', at: '2026-11-18 19:50', km: 16, pick: 15 }).amount, 10400);
assert.equal(price('D72024d3', { pickup: '西宮市 JR西宮駅', dropoff: '大阪国際空港', at: '2026-11-21 07:40', km: 15, pick: 3 }).amount, 8300);
// ミント：お迎え・乗車とも距離ごとの表。20km超はお見積もり
assert.equal(price('D1c2a5e3', { pickup: '堺市堺区', dropoff: '堺市中区', at: '2026-11-18 14:00', km: 10, pick: 12 }).amount, 3410 + 3300);
assert.equal(price('D1c2a5e3', { pickup: '岸和田市', dropoff: '堺市中区', at: '2026-11-18 14:00', km: 23, pick: 15 }), null);
// シエロ：船橋→羽田は定額10,000円（高速代込み）。逆向きも同じ
let r = price('De3f35f2', { pickup: '千葉県船橋市 船橋駅', dropoff: '羽田空港 第1ターミナル', at: '2026-11-21 07:40', km: 36, pick: 15, back: 42 });
assert.equal(r.amount, 10000); assert.equal(r.fixed, true); assert.equal(r.tollIncluded, true);
assert.equal(price('De3f35f2', { pickup: '成田空港', dropoff: '千葉県松戸市', at: '2026-11-21 12:00', km: 40, pick: 30, back: 3 }).amount, 15000);
// 定額に当たらない区間はいつもの式
assert.equal(price('De3f35f2', { pickup: '我孫子市 我孫子駅', dropoff: '柏市西原', at: '2026-11-18 19:50', km: 12, pick: 20, back: 22 }).fixed, undefined);
// てんりん：京都府から伊丹は12,000円（税別）、往復の定額
assert.equal(price('D25bac67', { pref: '京都', pickup: '京都市左京区', dropoff: '大阪国際空港（伊丹空港）', at: '2026-11-21 07:40', km: 53, pick: 8 }).amount, 13200);
assert.equal(price('D25bac67', { pref: '京都', trip: '往復', pickup: '京都市左京区', dropoff: '関西国際空港', rp: '関西国際空港', rd: '京都市左京区', at: '2026-11-21 07:40', rat: '2026-11-25 15:00', km: 100, pick: 8 }).amount, 40700);
// aiai：パック便20,000円より式のほうが安ければ式（返事 17,325円）
r = price('D13b7c6f', { pickup: '札幌市東区', dropoff: '新千歳空港', at: '2026-11-21 07:40', km: 51, pick: 10 });
assert.ok(!r.fixed && r.amount < 20000);
console.log('PASS: site fixed fares (airport) and transcribed fare tables');
