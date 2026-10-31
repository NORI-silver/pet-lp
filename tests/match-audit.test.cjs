// マッチング検査（tools/match_audit.cjs）：サイトに出すかの仕分けと、抜け（黙って除外・見落とし）の見つけ方
const assert = require('node:assert/strict');
const { listing, derive, auditCompany, ctx } = require('../tools/match_audit.cjs');
const base = { pref: '東京都', name: 'テスト', inactive: '', hotel: 'いいえ', lic: '', note: '', op: '', area: '世田谷', ch_group: 'メール・フォームあり',
  hours: '不明', cap: '不明', ride: '不明', large_dog: '不明', animals: '不明', cage: '不明', care: '不明', cars: '不明', lead: '不明', pet_only: '不明', dog_only: '' };
const c = o => ({ ...base, ...o });

// サイトに出すか（Nori 2026-10-31）
assert.equal(listing(c({ inactive: '閉鎖・停止（サイト閉鎖）' }))[0], '除外');
assert.equal(listing(c({ inactive: '自社施設との送迎だけ' }))[0], '除外');
assert.equal(listing(c({ name: '赤帽松弘運送店' }))[0], '輸送のときだけ');
assert.equal(listing(c({ name: '動物救急車' }))[0], '緊急タブだけ');
assert.equal(listing(c({}))[0], '候補');

// サイトの文章から値をつくる
const f1 = derive(c({ cap: '犬2〜3頭、付添1〜3名', animals: '犬（ほかは不明）', hours: '20:00〜翌5:00 年中無休' }));
assert.equal(f1.f.riders, 3); assert.equal(f1.f.pets, 3);
assert.deepEqual(f1.f.species, ['犬']);
assert.deepEqual(f1.f.overnight, [20, 5]);
assert.ok(f1.gaps.some(g => /日をまたぐ/.test(g[1])));
assert.equal(derive(c({ animals: '飼育が認められた動物（ワクチン接種済み）' })).f.vacMust, true);

// 分からない会社：大人3人は checks_ では「確かめる」なのに、軽バン扱いで黙って外れる
const blank = { id: 'X', riders: null, pets: null, big: null, luggage: null, cageMust: '', cageLend: null, careTri: null, careOk: true, hours: '', rideHours: '', maxKg: null, maxBig: null, lendKg: null, petOnly: null, vacMust: null };
const res = auditCompany(blank, derive(c({ animals: '犬（ほかは不明）' })).f);
assert.ok(res.d['人数'].drop > 0 && res.d['荷物'].drop > 0 && res.d['貸しケージの大きさ'].drop > 0);
// 犬だけの会社に猫の依頼が出てしまう（しくみは種類を見ない）
assert.ok(res.d['動物の種類'].miss > 0);
assert.ok(res.ex.some(x => x.kind === 'miss' && /猫は乗せていない/.test(x.why)));
// 本番のしくみが直れば数が変わることを確かめるため、checks_ を本番の関数から使っている
assert.equal(typeof ctx.checks_, 'function');
console.log('PASS: match audit sorts companies for listing and finds silent drops and missed conditions');
