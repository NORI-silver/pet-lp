// カードの data-k に、data-ft・data-tags と同じ印を二重に書かない（find.js が足して使うので、結果は同じで容量だけ減る）。
const fs = require('fs'), path = require('path'), assert = require('assert');
const root = path.join(__dirname, '..', 'dog-trainer');  // 容量の上限があるドッグトレーナーのページ（一覧・都道府県・市区町村）
let cards = 0, dup = [];
(function walk(d) {
  for (const f of fs.readdirSync(d, { withFileTypes: true })) {
    if (['.git', 'node_modules'].includes(f.name)) continue;
    const p = path.join(d, f.name);
    if (f.isDirectory()) walk(p);
    else if (f.name === 'index.html') {
      const h = fs.readFileSync(p, 'utf8');
      for (const m of h.matchAll(/<[a-z]+[^>]*\sdata-ffi[\s>][^>]*>/g)) {
        const attr = (n) => { const x = m[0].match(new RegExp('\\s' + n + '="([^"]*)"')); return x ? x[1].replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#x27;/g, "'") : ''; };
        const ex = new Set([attr('data-ft'), attr('data-tags')].join('|').split('|').filter(Boolean).map(x => x.trim().replace(/ /g, '_')));
        cards++;
        for (const k of attr('data-k').split(' ').filter(Boolean)) if (ex.has(k)) dup.push(p + ' ' + k);
      }
    }
  }
})(root);
assert(cards > 500, 'cards found: ' + cards);
assert.strictEqual(dup.length, 0, 'duplicate data-k tokens: ' + dup.slice(0, 5).join(', '));
console.log('ok', cards, 'cards');
