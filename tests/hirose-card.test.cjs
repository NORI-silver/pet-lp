const assert = require('node:assert/strict');
const fs = require('node:fs');
const address = '京都府京都市右京区嵯峨広沢南下馬野町1-1';
for (const file of ['dog-trainer/kyoto/index.html', 'dog-trainer/index.html']) {
  const page = fs.readFileSync(file, 'utf8');
  const at = page.indexOf('data-fid="T114"');
  assert.ok(at > 0, file);
  const card = page.slice(at, page.indexOf('data-fid=', at + 9));
  const route = card.match(/href="([^"]+)"[^>]*data-route>([^<]+)<\/a>/);
  assert.ok(route, file);
  assert.equal(new URL(route[1].replaceAll('&amp;', '&')).searchParams.get('destination'), address, file);
  assert.equal(route[2], '事業所への経路', file);
  assert.match(card, /data-to="京都府京都市右京区嵯峨広沢南下馬野町1-1" data-to-label="教室"/);
  assert.match(card, /data-gph="T114"[^>]*><div class="cs-ph-s"><i class="cs-ph-i"><img class="b" src="\/img\/fac\/trainer\/T114_1.webp"[^>]*><img src="\/img\/fac\/trainer\/T114_1.webp"/);
  assert.match(page, /\.cs-ph-i img\{position:relative;display:block;width:100%;height:100%;object-fit:contain\}/);
  assert.match(page, /\.cs-ph-s\{display:flex;aspect-ratio:4\/3/);
  assert.match(page, /\.cs-ph\{position:relative;background:#f6efe8;overflow:hidden\}/);
  assert.doesNotMatch(page, /\.cs-ph\{position:relative;aspect-ratio:2\/1/);
}
console.log('Hirose: both pages use the Kyoto office address and preserve the full photo frame.');
