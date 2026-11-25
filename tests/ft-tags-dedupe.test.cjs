// ドッグトレーナーのカードの data-ft に、data-tags と同じ印を二重に書かない（find.js が data-ft と data-tags を足して使うので、結果は同じで容量だけ減る）。
const fs = require('fs'), path = require('path'), assert = require('assert');
const root = path.join(__dirname, '..', 'dog-trainer');
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
        const tg = new Set(attr('data-tags').split('|').filter(Boolean).map(x => x.trim()));
        cards++;
        for (const k of attr('data-ft').split('|').filter(Boolean)) if (tg.has(k.trim())) dup.push(p + ' ' + k);
      }
    }
  }
})(root);
assert(cards > 500, 'cards found: ' + cards);
assert.strictEqual(dup.length, 0, 'duplicate data-ft tokens: ' + dup.slice(0, 5).join(', '));
console.log('ok', cards, 'cards');
