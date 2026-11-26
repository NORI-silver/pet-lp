// 迷子探偵の絞り込み印：実際の31社のデータで、キャンセル条件と別途費用の判定を確かめる
const cp = require('child_process'), path = require('path');
const root = path.join(__dirname, '..');
const py = `
import sys, json
sys.path.insert(0, 'tools')
import maigo_flags as m
d = json.load(open('tools/maigo_private.json', encoding='utf-8'))['detectives']
cx = [x['name'] for x in d if m.has_cancel(x)]
ef = [x['name'] for x in d if m.has_separate_fee(x)]
fx = {
 'noinfo': m.has_cancel({'cancel': '記載なし'}),
 'unverified': m.has_cancel({'cancel': '別ページ（未確認）'}),
 'none': m.has_cancel({}),
 'nofee_stated': m.has_cancel({'cancel': 'キャンセル料なし（当日も可）'}),
 'amount_unknown': m.has_cancel({'cancel': '時期によりキャンセル料がかかる場合あり（金額の記載なし）'}),
 'table': m.has_cancel({'cancel': [{'when': '前日まで', 'yen': 16500}]}),
 'included_only': m.has_separate_fee({'extra_fees': [{'what': '料金の条件', 'text': '交通費・宿泊費・機材費・チラシ代込み。成功報酬なし'}]}),
 'variation_only': m.has_separate_fee({'extra_fees': [{'what': '料金の条件', 'text': '猫の3日捜索は10万円が目安。人数・範囲・機材などで変動'}]}),
 'hours_only': m.has_separate_fee({'extra_fees': [{'what': '料金の条件', 'text': '営業時間9時〜18時、土日祝休み。緊急時は相談'}]}),
 'mixed': m.has_separate_fee({'extra_fees': [{'what': 'チラシ', 'text': 'チラシ代は料金にふくむ'}, {'what': '交通費', 'text': '出張の交通費は実費'}]}),
 'included_and_individual_quote': m.has_separate_fee({'extra_fees': [{'what': '料金の条件', 'text': '捜索・機材・移動費込み。地域や捜索の条件で金額が変わる'}, {'what': '料金の条件', 'text': '延長・遠方出張などは個別見積もり'}]}),
 'plain_separate': m.has_separate_fee({'extra_fees': [{'what': '交通費', 'text': 'ガソリン代・高速道路料金・駐車場代・遠方の宿泊費'}]}),
 'empty': m.has_separate_fee({'extra_fees': []}),
}
print(json.dumps({'n': len(d), 'cx': cx, 'ef': ef, 'fx': fx}, ensure_ascii=False))
`;
const r = cp.spawnSync('python3', ['-c', py], { cwd: root, encoding: 'utf8' });
if (r.status !== 0) { console.error(r.stderr); process.exit(1); }
const o = JSON.parse(r.stdout);
let fail = 0; const ok = (c, m) => { if (!c) { console.error('FAIL ' + m); fail++; } };
ok(o.n === 31, '31社');
ok(o.cx.length === 8, 'キャンセル条件が書いてある会社は8社（実際は ' + o.cx.length + '）');
for (const n of ['PET RESCUE', 'ネコちゃん探偵のプロ', '猫探偵センター', '名探偵キャッツ', 'ペット探偵オリネコ', '滋賀プロテクト', 'ペット探偵イブ', '迷いペット捜索隊'])
  ok(o.cx.some(x => x.includes(n)), 'cx に ' + n);
for (const n of ['ジャパンロストペットレスキュ', 'キャットプロ', '猫専門探偵社ファインドキャッ', 'アニマルブレイン', '総合調査 紫苑'])
  ok(!o.cx.some(x => x.includes(n)), 'cx に入れない ' + n);
ok(o.ef.length === 21, '別途費用の記載がある会社は21社（実際は ' + o.ef.length + '）');
for (const n of ['ベストティアーズ24', '猫探偵やま〜ず'])
  ok(!o.ef.some(x => x.includes(n)), 'ef に入れない ' + n);
for (const n of ['PET RESCUE', 'おたすけプラス', 'ペット探偵ポーズワン', '総合探偵社フリースタイル', 'あおぞら探偵社', '迷子猫探偵バリニーズ'])
  ok(o.ef.some(x => x.includes(n)), 'ef に ' + n);
const f = o.fx;
ok(!f.noinfo && !f.unverified && !f.none, '記載なし/未確認/なし はキャンセル条件にしない');
ok(f.nofee_stated && f.amount_unknown && f.table, 'キャンセル料なしの記載・金額なしの条件・料金表は条件にする');
ok(!f.included_only && !f.variation_only && !f.hours_only && !f.empty, '込みのみ・変動のみ・営業時間のみ・空は別途費用にしない');
ok(f.mixed && f.included_and_individual_quote && f.plain_separate, '別途費用の文言が残る場合は別途費用にする');
if (fail) process.exit(1);
console.log('maigo-flags ok');
