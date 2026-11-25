// 全国ページ（dog-trainer/index.html）の写真は、サイズ上限のため 1 枚目だけ HTML に書き、残りは ga.js が足す。
// ここでは (1) HTML の 1 枚目だけでも写真が全体のまま見えること、(2) ga.js を通すとぼかしの背景・2枚目以降・枚数・ドット・矢印が付くことを確かめる。
const assert = require('node:assert/strict');
const fs = require('node:fs');
const html = fs.readFileSync('dog-trainer/index.html', 'utf8');
const gaFull = fs.readFileSync('ga.js', 'utf8');
// 写真の部分（先頭の (function(){ … all(); まで）だけを動かす。あとの解析用の処理は対象外
const cut = gaFull.indexOf('\n  all();\n');
assert.ok(cut > 0, 'photo block not found in ga.js');
const ga = gaFull.slice(0, cut) + '\n  all();\n})();';

// ---- (1) HTML 側 ----
const strips = [...html.matchAll(/<div class="cs-ph" data-gph="([^"]+)" data-n="(\d+)">(.*?)<\/div>(?:<small class="cs-ph-c">[^<]*<\/small>)?<\/div>/g)];
assert.ok(strips.length > 0, 'no compact national strips');
for (const [, id, n, inner] of strips) {
  assert.ok(+n >= 1 && +n <= 5, id);
  assert.match(inner, /^<div class="cs-ph-s"><i class="cs-ph-i"><img src="\/img\/fac\/[a-z]+\/[^"]+_1\.webp" alt="[^"]*1" loading="lazy" decoding="async"><\/i>$/, id);
}
assert.match(html, /\.cs-ph-i img\{position:relative;display:block;width:100%;height:100%;object-fit:contain\}/);   // 切らない
assert.match(html, /\.cs-ph-s\{display:flex;aspect-ratio:4\/3/);

// ---- (2) ga.js 側（最小の DOM で実行）----
class El {
  constructor(tag) { this.tag = tag; this.attrs = {}; this.kids = []; this.parentNode = null; this.dataset = {}; this.ls = {}; this.textContent = ''; this.clientWidth = 300; this.scrollLeft = 0; }
  get children() { return this.kids; }
  get className() { return this.attrs.class || ''; } set className(v) { this.attrs.class = v; }
  get src() { return this.attrs.src; } set src(v) { this.attrs.src = v; } get alt() { return this.attrs.alt || ''; } set alt(v) { this.attrs.alt = v; } set loading(v) { this.attrs.loading = v; } set decoding(v) { this.attrs.decoding = v; } set type(v) { this.attrs.type = v; }
  setAttribute(k, v) { this.attrs[k] = String(v); } getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; } removeAttribute(k) { delete this.attrs[k]; }
  appendChild(c) { if (c.parentNode) c.parentNode.kids.splice(c.parentNode.kids.indexOf(c), 1); c.parentNode = this; this.kids.push(c); return c; }
  insertBefore(c, ref) { if (c.parentNode) c.parentNode.kids.splice(c.parentNode.kids.indexOf(c), 1); c.parentNode = this; this.kids.splice(this.kids.indexOf(ref), 0, c); return c; }
  get nextSibling() { const k = this.parentNode.kids; return k[k.indexOf(this) + 1] || null; }
  addEventListener(t, f) { this.ls[t] = f; }
  scrollBy(o) { this.scrolled = o; }
  has(sel) { const [tag, cls] = sel.startsWith('.') ? [null, sel.slice(1)] : [sel, null]; return (!tag || this.tag === tag) && (!cls || this.className.split(' ').includes(cls)); }
  all(sel, out = []) { for (const c of this.kids) { if (c.has(sel)) out.push(c); c.all(sel, out); } return out; }
  querySelector(sel) { return this.all(sel)[0] || null; }
  querySelectorAll(sel) { return this.all(sel); }
}
function run(n) {
  const root = new El('html'), p = new El('div'), s = new El('div'), i = new El('i'), img = new El('img');
  p.className = 'cs-ph'; p.setAttribute('data-n', n); s.className = 'cs-ph-s'; i.className = 'cs-ph-i';
  img.setAttribute('src', '/img/fac/trainer/X1_1.webp'); img.setAttribute('alt', '名前の写真1'); img.setAttribute('loading', 'lazy');
  i.appendChild(img); s.appendChild(i); p.appendChild(s); const holder = new El('div'); holder.appendChild(p); root.appendChild(holder);
  const dq = (sel) => root.all(sel.replace(/\[data-n\]$/, ''), []).filter(e => sel.includes('[data-n]') ? e.getAttribute('data-n') !== null : true);
  global.document = { documentElement: root, createElement: (t) => new El(t), querySelectorAll: dq };
  global.MutationObserver = class { observe() {} };
  new Function(ga)();
  return { p, s, holder };
}
for (const n of [1, 3, 5]) {
  const { p, s } = run(n);
  assert.equal(p.getAttribute('data-n'), null, 'data-n removed');
  assert.equal(s.kids.length, n, 'slides');
  const first = s.kids[0].kids;
  assert.deepEqual(first.map(e => e.className), ['b', ''], 'blur twin then whole photo');
  assert.equal(first[0].getAttribute('aria-hidden'), 'true');
  assert.equal(first[1].getAttribute('src'), '/img/fac/trainer/X1_1.webp');
  s.kids.forEach((sl, k) => { const im = sl.kids[sl.kids.length - 1]; assert.equal(im.getAttribute('src'), `/img/fac/trainer/X1_${k + 1}.webp`); assert.equal(im.getAttribute('alt'), `名前の写真${k + 1}`); assert.equal(im.getAttribute('loading'), 'lazy'); });
  const wrap = s.parentNode;
  if (n > 1) {
    assert.equal(wrap.className.split(' ')[0], 'cs-ph-w', 'wrapped for controls');
    assert.deepEqual(wrap.kids.filter(e => e.tag === 'button').map(e => e.className), ['cs-ph-a l', 'cs-ph-a r']);
    assert.equal(wrap.kids.find(e => e.className === 'cs-ph-d').kids.length, n, 'dots');
    wrap.kids.find(e => e.className === 'cs-ph-a r').ls.click();
    assert.equal(s.scrolled.left, 300, 'arrow scrolls one whole photo');
    assert.ok(/ f/.test(wrap.className), 'first slide: no left arrow');
    s.scrollLeft = 300 * (n - 1); s.ls.scroll();
    assert.ok(/ e/.test(wrap.className), 'last slide: no right arrow');
    assert.equal(p.kids.find(e => e.className === 'cs-ph-n').textContent, '📷 ' + n, 'count badge');
  } else {
    assert.equal(s.parentNode, p, 'single photo: no controls');
  }
}
console.log('National photo cards: first photo in HTML, ga.js adds blur, slides, dots, arrows.');
