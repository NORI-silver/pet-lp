const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const read = file => fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
const json = file => JSON.parse(read(file));
const cards = file => json(file).groups.flatMap(([, entries]) => entries);
test('oppotoのトリミング送迎はホテル送迎と区別し、カードと比較表に出す', () => {
  const h = json('tools/hotels.json').hotels.find(x => x.id === 'PHk421d80');
  assert.equal(h.pickup, false);
  assert.match(h.facts.find(f => f.k === '送迎').v, /原則月曜日.*10km圏内.*ホテルやしつけ教室のみの利用は対象外/);
  assert.match(read('pet-hotel/shiga/index.html'), /data-l="送迎">トリミングのみ無料/);
  const card = cards('find-data/pet-hotel/shiga.json').find(x => x.includes('data-fid="PHk421d80"'));
  assert.doesNotMatch(card.match(/data-flags="([^"]*)"/)[1], /\bpickup\b/);
  assert.match(card.split('<details')[0], /display:block;overflow:visible[^>]*>送迎：[^<]*ホテルやしつけ教室のみの利用は対象外/);
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
