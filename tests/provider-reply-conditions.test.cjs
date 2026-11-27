const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const read = file => fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
const json = file => JSON.parse(read(file));
const cards = file => json(file).groups.flatMap(([, entries]) => entries);
test('oppotoは公式サイトの記載だけを出し、送迎・しつけの条件や第三者ページの内容は出さない', () => {
  const h = json('tools/hotels.json').hotels.find(x => x.id === 'PHk421d80');
  assert.equal(h.url, 'https://oppoto.com/top');
  assert.equal(h.pickup, false);
  assert.equal(h.pickup_comparison, undefined);
  assert.deepEqual(json('tools/kinki_add.json').hotels.find(x => x.id === h.id), h, '近畿データと同じ内容にする');
  assert.ok(!h.facts.some(f => f.k === '送迎'), '公式に送迎の記載がないので項目を置かない');
  assert.ok(h.facts.every(f => f.src === 'https://oppoto.com/top'), '事実の出どころはすべて公式サイト');
  assert.ok(!/しつけ/.test(h.services));
  const page = read('pet-hotel/shiga/index.html');
  assert.ok(!/chatgpt\.site/.test(page) && !/chatgpt\.site/.test(read('find-data/pet-hotel/shiga.json')) && !/chatgpt\.site/.test(read('webmcp/data.json')));
  const from = page.indexOf('dogsalon oppoto</b></a><p class="pc-loc pin">');
  assert.ok(from > 0, 'oppotoのカードが見つかる');
  const card = page.slice(from, page.indexOf('タクシー料金', from));
  const txt = card.replace(/<[^>]+>/g, ' ');
  assert.doesNotMatch(txt, /10km|月曜|しつけ|無料送迎/);
  assert.match(txt, /1泊¥5,500〜/);
  assert.match(txt, /送迎\s*未確認/);
});
test('青森のわんぷろは公式サイトの1件にだけ施設写真を掲載する', () => {
  const result = cards('find-data/dog-trainer/aomori.json').filter(x => x.includes('わんぷろ'));
  assert.equal(result.length, 1);
  assert.match(result[0], /data-fid="T006"/);
  assert.match(result[0], /\/img\/fac\/trainer\/T006_1\.webp/);
  assert.match(result[0], /https:\/\/wanpro-dog\.jp\//);
});
test('ひまわりはカメラ設置なしを表示し、ライブ視聴には含めない', () => {
  const card = cards('find-data/rojin-home/ibaraki.json').find(x => x.includes('data-fid="R004"'));
  assert.match(card.split('<details')[0], /設置なし。預かり中の様子はブログ・面会・飼い主からの電話/);
  assert.doesNotMatch(card.match(/data-k="([^"]*)"/)?.[1] || '', /owner_live_dog/);
});
test('川越公園カードに許諾済みの写真と提供元を表示する', () => {
  const page = read('dogrun/saitama/index.html');
  assert.match(page, /id="D017"[^>]*>[\s\S]{0,1500}\/img\/fac\/dogrun\/D017_1\.webp/);
  assert.match(page, /写真：川越公園管理事務所/);
});
