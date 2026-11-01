// 候補カードに、お店の位置（shop）を入れる。ページが車の道のりを調べて近い順に並べる（Nori 2026-11-01「直線で出すのやめて。クルマでの最短ルートでだして」）
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'), ctx);
const shop = ctx.partnerShop_('P002');
assert.ok(Array.isArray(shop) && shop.length === 2);
assert.equal(ctx.partnerShop_('P999'), null);
const html = fs.readFileSync('index.html', 'utf8');
assert.ok(html.includes('value="dist_asc" selected'), '並び順のデフォルトはお店が近い順');
assert.ok(html.includes('id="partnerDist"'), '距離のフィルター');
assert.ok(html.includes('table/v1/driving/') && html.includes('destinations=0'), '道路データで道のりを調べる');
assert.ok(!/お迎えの場所まで 直線/.test(html), '直線距離は出さない');
console.log('distance ok');
