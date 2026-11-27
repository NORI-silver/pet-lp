// 確認していない掲載だけの施設（tools/sougi_listing_only.json）が、記事の数え上げ（施設数・料金の分布・できることの数）を増やさないことを確かめる。
// 分からないことを「ない」と数えないため。
const fs = require('fs'), assert = require('assert');
const fac = JSON.parse(fs.readFileSync('tools/sougi_facilities.json', 'utf8')).facilities;
const lo = JSON.parse(fs.readFileSync('tools/sougi_listing_only.json', 'utf8')).ids;
const ids = new Set(lo);
assert.strictEqual(ids.size, lo.length, 'duplicate ids in listing-only');
assert.strictEqual(lo.length, 88);
const byId = Object.fromEntries(fac.map(f => [f.id, f]));
for (const i of lo) {
  const f = byId[i];
  assert(f, 'listing-only id missing from facilities: ' + i);
  assert.strictEqual(f.visit, 'unconfirmed', i);
  assert(!f.price && (f.services || []).length === 0, 'listing-only record has audited data: ' + i);
}
const audited = fac.filter(f => !ids.has(f.id));
const priced = audited.filter(f => f.price).length;
for (const p of ['guide/pet-cremation-types/index.html', 'guide/pet-memorial/index.html']) {
  const h = fs.readFileSync(p, 'utf8');
  assert(h.includes(audited.length + '施設'), p + ' must count only the audited ' + audited.length);
  assert(!h.includes(fac.length + '施設'), p + ' must not use the total including listing-only records: ' + fac.length);
}
const c = fs.readFileSync('guide/pet-cremation-types/index.html', 'utf8');
assert(c.includes(priced + '施設'), 'priced count must come from the audited cohort: ' + priced);
console.log('ok guide cohort audited=' + audited.length + ' priced=' + priced + ' listing-only=' + lo.length);
