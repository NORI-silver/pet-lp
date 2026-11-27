// 経路を見る は目立つボタンではなく「くわしく見る」の中（閉じた状態）に置く（利用者の了承：2026-11-27）。
// すべての data-route が ①<details>の中 ②open なし ③.ux-c-a（大きいボタン）の外 であること。行き先（href）は今までと同じ。
const assert = require('assert'), fs = require('fs'), path = require('path');
function walk(d, out) {
  for (const f of fs.readdirSync(d, { withFileTypes: true })) {
    if (f.name === '.git' || f.name === 'node_modules' || f.name === 'tests') continue;
    const q = path.join(d, f.name);
    if (f.isDirectory()) walk(q, out); else if (f.name === 'index.html') out.push(q);
  }
  return out;
}
const root = path.join(__dirname, '..');
let total = 0, pages = 0;
for (const f of walk(root, [])) {
  const h = fs.readFileSync(f, 'utf8');
  if (!h.includes('data-route')) continue;
  pages++;
  const re = /<(\/?)(details|div)\b([^>]*)>|data-route/g;
  const st = []; let m;
  while ((m = re.exec(h))) {
    if (m[0] === 'data-route') {
      total++;
      const det = [...st].reverse().find(x => x.t === 'details');
      assert.ok(det, f + ': 経路が「くわしく見る」の外にある');
      assert.ok(!/\bopen\b/.test(det.a), f + ': 経路の入れ物が最初から開いている');
      assert.ok(!st.some(x => x.t === 'div' && /\bux-c-a\b/.test(x.a)), f + ': 経路が大きいボタンの列にある');
    } else if (m[1]) {
      for (let i = st.length - 1; i >= 0; i--) if (st[i].t === m[2]) { st.length = i; break; }
    } else st.push({ t: m[2], a: m[3] });
  }
}
console.log('route-in-details: pages', pages, 'routes', total);
assert.ok(total > 0);
