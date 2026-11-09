// 2026-11-10 提携の申し込みの答え（行き先の範囲・大きい子と大人の組み合わせ・介護のくわしいこと・経由地・ワクチンの証明）で候補をしぼる。
// 申し込みは提携先シートの1行になる（受付中は×）。何も送らない
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite, Infinity });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'), ctx);
const blank = { id:'PX', riders:null, pets:null, big:null, luggage:null, cageMust:'', cageLend:null, careTri:null, careOk:true, hours:'', rideHours:'0-24', maxKg:null, maxBig:null, lendKg:null, petOnly:null, vacMust:null,
  destScope:'', destKm:null, combo:[null,null,null,null,null], comboLug:null, careCan:'', careStaff:null, careStaffMore:false, careKg:null, careTools:'', via:null, vacProof:'' };
const at = (h, m = 12) => new Date(Date.UTC(2026, m - 1, 1, h - 9, 0));
const req = (o = {}) => ({ '都府県':'東京', '希望日時': at(10), '同乗人数':'1人', 'ペット数':1, '体重kg':5, 'キャリー':'持ち込む', '介助':'不要', '荷物':'手荷物くらい', ...o });
const pets = a => JSON.stringify(a);
const ck = (pt, r) => ctx.checks_({ ...blank, ...pt }, r);

// ふつうの依頼は、新しい項目で何も増えない
assert.equal(JSON.stringify(ck({}, req())), '{"ng":[],"ask":[]}');
// 行き先：距離の上限と、都道府県の中だけ
assert.ok(ck({ destKm:50 }, req({ '概算km': 80 })).ng[0].includes('80km'));
assert.equal(ck({ destKm:50 }, req({ '概算km': 30 })).ng.length, 0);
assert.ok(ck({ destScope:'お迎えの都道府県の中だけ' }, req({ '行き先':'神奈川県横浜市中区' })).ng[0].includes('神奈川'));
assert.equal(ck({ destScope:'お迎えの都道府県の中だけ' }, req({ '行き先':'東京都目黒区' })).ng.length, 0);
assert.ok(ck({ destScope:'お迎えの都道府県の中だけ' }, req({ '行き先':'○○動物病院', '_route': { km: 60 } })).ask[0].includes('60km'));
// お迎えの範囲：お店（練馬）から20kmまでの会社に、横浜のお迎えは届かない
const nerima = { shopLL:{ lat:35.737, lng:139.654 }, radiusKm:20 };
assert.ok(ck(nerima, req({ '_route': { from:{ lat:35.466, lng:139.622 } } })).ng[0].includes('20kmまで'));
assert.equal(ck(nerima, req({ '_route': { from:{ lat:35.70, lng:139.70 } } })).ng.length, 0);
// 経由地
assert.ok(ck({ via:false }, req({ '経由地':'渋谷駅' })).ng.includes('途中で寄る'));
assert.ok(ck({}, req({ '経由地':'渋谷駅' })).ask[0].includes('渋谷駅'));
assert.equal(ck({ via:true }, req({ '経由地':'渋谷駅' })).ask.length, 0);
// 組み合わせ：大型犬4頭＋大人2人は、4頭のときの大人の人数で決める（Nori 2026-11-10）
const bigs = (k, riders, o = {}) => req({ 'ペット数':k, '体重kg':30, '同乗人数': riders + '人', 'ペットJSON': pets(Array(k).fill({ species:'犬', weight:'30' })), ...o });
const van4 = { pets:5, maxBig:9, combo:[2, 2, 2, 1, 0] };
assert.ok(ck(van4, bigs(4, 2)).ng.some(x => x.includes('大型犬4頭と大人2人')));
assert.equal(ck(van4, bigs(4, 0, { '同乗人数':'0人（ペットだけ）' })).ng.length, 0);
assert.equal(ck(van4, bigs(2, 2)).ng.length, 0);
assert.ok(!ck(van4, bigs(2, 2)).ask.some(x => x.includes('大人2人が一緒')));          // 分かっているので確かめない
assert.ok(ck(van4, bigs(3, 2)).ng.some(x => x.includes('大人1人まで')));
assert.ok(ck({ ...van4, combo:[2, 2, -1, -1, -1] }, bigs(2, 1)).ng.includes('大型犬2頭'));
assert.ok(ck({ pets:5, maxBig:9 }, bigs(4, 2)).ask.some(x => x.includes('大型犬4頭と大人2人')));  // 答えがない会社は確かめる
assert.ok(ck({ ...van4, comboLug:false }, bigs(1, 1, { '荷物':'多め' })).ng.includes('大型犬と大きな荷物'));
// 小さい子だけ：いちばん多い頭数のときの大人の人数
const smalls = (k, riders) => req({ 'ペット数':k, '同乗人数': riders + '人', 'ペットJSON': pets(Array(k).fill({ species:'犬', weight:'5' })) });
assert.ok(ck({ pets:4, combo:[1, null, null, null, null] }, smalls(4, 2)).ng.some(x => x.includes('4匹と大人2人')));
assert.ok(ck({ pets:4, combo:[1, null, null, null, null] }, smalls(2, 2)).ask.some(x => x.includes('2匹と大人2人')));
// 介護：できることがそろっていれば確かめない。足りない・重すぎる・道具がないときだけ
const care = (kg, need) => req({ '介助':'必要', 'ペットJSON': pets([{ species:'犬', weight:String(kg), care:'必要', care_need: need }]) });
const able = { careTri:true, careCan:'歩けない（抱っこで運ぶ）・寝たきり（担架やマットで運ぶ）', careKg:30, careStaff:2, careTools:'ストレッチャー（担架）' };
assert.equal(ck(able, care(12, ['寝たきり（担架やマットで運ぶ）'])).ask.length, 0);
assert.ok(ck(able, care(35, ['寝たきり（担架やマットで運ぶ）'])).ng[0].includes('35kg'));
assert.ok(ck(able, care(12, ['酸素や点滴などの医療機器がある'])).ask.some(x => x.includes('医療機器')));
assert.ok(ck({ ...able, careTools:'介護用マット・クッション' }, care(12, ['酸素や点滴などの医療機器がある'])).ask.some(x => x.includes('酸素ボンベ')));
assert.ok(ck({ ...able, careKg:Infinity, careStaff:1 }, care(25, ['歩けない（抱っこで運ぶ）'])).ask.some(x => x.includes('1人で')));
assert.ok(ck({ careTri:false }, care(5, [])).ng.includes('介護が必要な子'));
assert.ok(ck({}, care(5, ['寝たきり（担架やマットで運ぶ）'])).ask[0].includes('寝たきり')); // 申し込みの答えがない会社はいままでどおり
// ワクチンの証明：狂犬病だけの会社は、狂犬病の記入がない犬だけ確かめる
assert.ok(ck({ vacProof:'証明が必要（狂犬病の予防注射だけ）' }, req({ 'ペットJSON': pets([{ species:'犬', weight:'5', vaccine:'済' }]) })).ask[0].includes('狂犬病'));
assert.equal(ck({ vacProof:'証明が必要（狂犬病の予防注射だけ）' }, req({ 'ペットJSON': pets([{ species:'猫', weight:'4' }]) })).ask.length, 0);
assert.equal(ck({ vacProof:'接種していなくても乗せられる' }, req({ 'ペットJSON': pets([{ species:'犬', weight:'5' }]) })).ask.length, 0);
// 答えの読み方
assert.equal(ctx.tri3_('相談して決める'), null);
assert.equal(ctx.tri3_('受けられない'), false);
assert.equal(ctx.tri3_('できる（1か所ごとに料金を足す）'), true);
assert.equal(ctx.prefIn_('大阪府泉大津市'), '大阪');
assert.equal(ctx.prefIn_('京都府京都市'), '京都');

// 申し込み → 提携先シートの1行（受付中は×）
const rows = [ctx.PARTNER_HEADERS.slice(0, 20), ['P061', 'ペッタク', '', '', 'a@example.com']];
const sheet = {
  getLastRow: () => rows.length, getLastColumn: () => rows[0].length,
  getRange: (r, c, nr, nc) => ({
    getValues: () => rows.slice(r - 1, r - 1 + nr).map(x => { const o = []; for (let i = 0; i < nc; i++) o.push(x[c - 1 + i] ?? ''); return o; }),
    setValues: v => { v[0].forEach((x, i) => { rows[r - 1][c - 1 + i] = x; }); return { setFontWeight: () => ({ setBackground: () => {} }) }; },
  }),
  appendRow: r => rows.push(r),
};
ctx.SpreadsheetApp = { getActive: () => ({ getSheetByName: () => sheet }) };
ctx.LockService = { getScriptLock: () => ({ waitLock: () => {}, releaseLock: () => {} }) };
ctx.Utilities = { formatDate: () => '2026/11/10 07:00' };
ctx.log_ = () => {};
const id = ctx.applyPartner_({ '会社名・屋号':'テスト練馬', '都道府県の一覧':'東京都・埼玉県', '飼い主さんの同乗':'3人まで', '乗せられる頭数':'4頭以上', '大きい子（20kg以上）の数':'2頭まで',
  '乗せられる体重':'40kgまで', 'ペットだけの送迎':'できない', 'ケージ':'必要（貸し出しあり）', '当日の依頼':'空いていれば受ける', '当日の締め切り':'お迎えの 1時間前まで',
  '介護が必要な子':'受けられない', '大きい子1頭のときの大人':'大人3人まで', '大きい子2頭のときの大人':'大人2人まで', '大きい子4頭のときの大人':'その頭数は乗せられない', '途中で寄る':'できる（料金は距離と待ち時間のとおり）', '行き先までの距離':'距離に上限がある', '行き先までの上限':'乗っている距離 100kmまで',
  'お迎えに行ける範囲':'20kmまで', 'お店の位置':'35.7370,139.6540', 'お店の住所':'東京都練馬区練馬1丁目', '貸し出せるケージ':'大型犬用（40kgまで）',
  'キャンセル料':'前日まで無料、当日はかかる', '当日のキャンセル料':'運賃の 50％', '受けられる時間帯':'毎日 0:00〜24:00' }, '生形（テスト練馬）', 'b@example.com');
assert.equal(id, 'P062');
const h = rows[0], last = rows[rows.length - 1], v = k => last[h.indexOf(k)];
assert.ok(h.includes('申し込みの内容') && h.includes('行き先の上限km'));
assert.equal(v('受付中'), '×');
assert.equal(v('担当者名'), '生形');
assert.equal(v('同乗できる人数'), 3);
assert.equal(v('乗せられるペット数'), 5);
assert.equal(v('大型犬の最大頭数'), 2);
assert.equal(v('大型犬の最大kg'), 40);
assert.equal(v('ペットだけOK'), '×');
assert.equal(v('ケージ貸し出し'), '○');
assert.equal(v('何時間前まで'), 1);
assert.equal(v('介助OK'), '×');
assert.equal(v('行き先の上限km'), 100);
assert.equal(v('お迎えの範囲km'), 20);
assert.equal(v('お店の緯度経度'), '35.7370,139.6540');
assert.equal(v('貸し出しケージの最大kg'), 40);
assert.equal(v('キャンセル規定'), '前日まで無料、当日は運賃の 50％');
assert.deepEqual(JSON.parse(JSON.stringify(ctx.hoursOf_(v('営業時間')))), [0, 24]);
assert.equal(ctx.comboOf_(v('大型犬1頭のときの大人')), 3);
assert.equal(ctx.comboOf_(v('大型犬4頭以上のときの大人')), -1);
assert.equal(ctx.comboOf_(v('大型犬3頭のときの大人')), null);
assert.equal(ctx.tri3_(v('途中で寄る')), true);
console.log('PASS: partner application answers become a partner-sheet row and narrow candidates, including big-dog × adult combinations');
