// 確認していない掲載だけの施設（tools/sougi_listing_only.json）が、記事の数え上げ（施設数・料金の分布・できることの数）を増やさないことを確かめる。
// 分からないことを「ない」と数えないため。
const fs = require('fs'), assert = require('assert');
const fac = JSON.parse(fs.readFileSync('tools/sougi_facilities.json', 'utf8')).facilities;
const lo = JSON.parse(fs.readFileSync('tools/sougi_listing_only.json', 'utf8')).ids;
const ids = new Set(lo);
assert.strictEqual(ids.size, lo.length, 'duplicate ids in listing-only');
assert.strictEqual(lo.length, 81); // 87 - 6 (料金を公式サイトで確認して外した: S1ba768 Sbd4890 Se163c2 S861624 S5427f2 S91cdeb)
const byId = Object.fromEntries(fac.map(f => [f.id, f]));
for (const i of lo) {
  const f = byId[i];
  assert(f, 'listing-only id missing from facilities: ' + i);
  assert.strictEqual(f.visit, 'unconfirmed', i);
  assert(!f.price && (f.services || []).length === 0, 'listing-only record has audited data: ' + i);
}
const counted = fac.filter(f => !ids.has(f.id));
const priced = counted.filter(f => f.price).length;
assert.strictEqual(fac.filter(f => f.price).length, priced, 'listing-only records must not carry prices');
for (const p of ['guide/pet-cremation-types/index.html', 'guide/pet-memorial/index.html']) {
  const h = fs.readFileSync(p, 'utf8');
  // 数の分母（一覧の総数・数え上げの母数）を書かない。分からないことを「ない」と数えない。
  assert(!h.includes(fac.length + '施設'), p + ' must not state the total incl. listing-only: ' + fac.length);
  assert(!h.includes(counted.length + '施設'), p + ' must not state a cohort total/denominator: ' + counted.length);
  assert(!h.includes('確認し終えた'), p + ' must not claim a completed audit');
}
const c = fs.readFileSync('guide/pet-cremation-types/index.html', 'utf8');
const title = (c.match(/<title>([^<]*)<\/title>/) || [])[1] || '';
// タイトルの数は、記事の真ん中・幅の数え上げに入れた施設（料金の例だけ budget_example_only は除く）と同じ集団にする。
const med = counted.filter(f => f.price && !f.budget_example_only).length;
assert(title.includes(med + '施設'), 'title must use the same cohort as the medians (budget_example_only excluded): ' + med);
if (med !== priced) assert(!title.includes(priced + '施設'), 'title must not use the larger priced count: ' + priced);
for (const p of ['guide/pet-memorial/index.html']) {
  const h = fs.readFileSync(p, 'utf8');
  assert(!/火葬場\d+施設のうち/.test(h), 'no fire-facility denominator');
}
console.log('ok guide wording; priced=' + priced + ' listing-only=' + lo.length + ' counted=' + counted.length);
