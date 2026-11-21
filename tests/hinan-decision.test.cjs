const fs = require('node:fs');
const assert = require('node:assert/strict');
const index = JSON.parse(fs.readFileSync('hinan/munis.json', 'utf8'));
const cases = [
  ['栃木県', '鹿沼市', 'tochigi/kanuma-shi', '受け入れは避難所の状況によります', '倉庫などがあり避難者の同意', '大型の動物は避難所での受け入れがむずかしい'],
  ['愛知県', '西尾市', 'aichi/nishio-shi', '屋外の指定場所でリードにつなぐかケージ', '人の生活場所とは別の屋外の指定場所', '軒下・駐輪場・テント'],
  ['鳥取県', '米子市', 'tottori/yonago-shi', '大型犬が入れる大きさのケージなど', '指定されたペットの場所でケージなどに入れ', 'リードでつな'],
  ['愛知県', '長久手市', 'aichi/nagakute-shi', '受け入れる種類・大きさは各避難所が開設後に決めます', '屋外にペット用の場所を設ける予定', '屋内（空き教室'],
];
for (const [pref, city, path, large, place, stale] of cases) {
  const page = fs.readFileSync(`hinan/${path}/index.html`, 'utf8');
  const panel = page.split('id="uchinoko"')[1]?.split('<!--/thin0-->')[0] || '';
  assert.ok(panel.includes(large), `${city} panel does not show the municipality’s large-dog allowance and caveat`);
  assert.ok(panel.includes(place), `${city} panel does not show source-backed shelter placement`);
  assert.ok(!panel.includes(stale), `${city} panel includes an inferred claim that conflicts with the municipality`);
  const finder = index[pref].find(x => x[0] === city);
  assert.equal(finder[2], `/hinan/${path}/`);
  assert.ok(finder[7][4].includes(large), `${city} finder loses the caveat`);
}
console.log('PASS: evacuation panel and finder preserve four cities’ case-by-case conditions');
