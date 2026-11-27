// D033（過去の冬の期間だけ確認できた特設ドッグラン）は、カードの面に「終了・今年度は未確認」と書く
const fs = require('fs'), assert = require('assert');
for (const f of ['dogrun/index.html', 'dogrun/ibaraki/index.html']) {
  const h = fs.readFileSync(f, 'utf8');
  const i = h.search(/<(?:a|h3) class="ux-c-n"[^>]*>国営ひたち海浜公園 冬の特設ドッグラン/), a = h.lastIndexOf('<div class="ux-c', i), b = h.indexOf('くわしく見る', i);
  const blk = h.slice(a, b + 20);
  assert.ok(i > 0 && /2026年度は未確認/.test(blk) && /終了/.test(blk), f + ': D033 の面に終了・未確認を書く');
  assert.ok(!/class="ok">無料/.test(blk) && !/data-k="[^"]*(free|areadiv|bigonly)/.test(blk), f + ': D033 に無料・エリア分けの印は付けない');
}
console.log('dogrun-face ok');
