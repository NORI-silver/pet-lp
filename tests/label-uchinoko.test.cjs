// 「うちの子は／うちの子にあてはまるもの」の見出しが、どのページのさがす欄にも残っていないこと（よく使用される項目にそろえた。Nori 2026-11-26）。
// 生成元のない古いページ（tools/orphan_labels.py）は、かけ直しても同じ結果になること。
const test = require('node:test'), assert = require('node:assert'), fs = require('fs'), path = require('path'), cp = require('child_process');
const root = path.join(__dirname, '..');
test('no visible old filter heading on any page', () => {
  const bad = [];
  (function walk(d) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (e.name.startsWith('.') || e.name === 'node_modules' || e.name === 'tools' || e.name === 'tests') continue;
      const f = path.join(d, e.name);
      if (e.isDirectory()) walk(f);
      else if (e.name === 'index.html' && /class="(ux-l|fp-l)">うちの子/.test(fs.readFileSync(f, 'utf8'))) bad.push(path.relative(root, f));
    }
  })(root);
  assert.deepStrictEqual(bad, []);
});
test('orphan normalization is idempotent and touches only the heading', () => {
  const out = cp.execFileSync('python3', ['-c', `
import sys,os,shutil,tempfile
sys.path.insert(0,'tools')
import orphan_labels as O
t=tempfile.mkdtemp()
src='<html><head><meta name="robots" content="max-image-preview:large"></head><body><span class="ux-l">うちの子にあてはまるもの</span><span class="fp-l">うちの子は</span><a href="/x/">x</a></body></html>'
for d in O.ORPHANS:
    os.makedirs(os.path.join(t,d)); open(os.path.join(t,d,'index.html'),'w',encoding='utf-8').write(src)
n1=O.normalize(t); n2=O.normalize(t)
h=open(os.path.join(t,O.ORPHANS[0],'index.html'),encoding='utf-8').read()
assert n1==len(O.ORPHANS) and n2==0, (n1,n2)
assert 'うちの子' not in h and h.count('よく使用される項目')==2 and 'max-image-preview:large' in h and 'href="/x/"' in h
print('ok')`], { cwd: root }).toString();
  assert.match(out, /ok/);
});
