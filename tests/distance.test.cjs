// 候補カードに、お店からお迎えの場所までの直線距離（dist_km）を入れる（Nori 2026-11-01）
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'), ctx);
const rd = from => ({route_details: JSON.stringify({from})});
// 提携先（世田谷のお店）は fares.json の shop から
const shop = ctx.partnerShop_('P002');
assert.ok(Array.isArray(shop) && shop.length === 2);
assert.equal(ctx.shopDistKm_(shop, rd({lat:shop[0], lng:shop[1]})), 0);
const d = ctx.shopDistKm_(shop, rd({lat:35.6812, lng:139.7671})); // 東京駅
assert.ok(d > 9 && d < 11, String(d));
assert.equal(Math.round(d * 10) / 10, d, '小数1けた');
// 分からないときは null（カードには「お店の場所は確認中です」）
assert.equal(ctx.shopDistKm_(null, rd({lat:35.68, lng:139.76})), null);
assert.equal(ctx.shopDistKm_(shop, {route_details: '{}'}), null);
assert.equal(ctx.shopDistKm_(shop, {route_details: 'x'}), null);
assert.equal(ctx.partnerShop_('P999'), null);
// ページ：並び順と距離のフィルター
const html = fs.readFileSync('index.html', 'utf8');
assert.ok(html.includes('value="dist_asc" selected'), '並び順のデフォルトはお店が近い順');
assert.ok(html.includes('id="partnerDist"'), '距離のフィルター');
console.log('distance ok');
