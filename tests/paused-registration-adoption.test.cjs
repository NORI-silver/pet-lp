const test = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs');
const read = p => fs.readFileSync(p,'utf8');
test('unpublished categories have no deployable pages or browse entry points', () => {
  for (const f of ['jichitai/touroku','joto','find-data/joto','sitemaps/joto.xml']) {
    assert.equal(fs.existsSync(f),false,f);
  }
  for(const path of ['index.html','jichitai/index.html','jichitai/maigo/index.html','jichitai/tebanasu/index.html','404.html','sitemap.xml','sitemap_index.xml','sitemaps/jichitai.xml','llms.txt','webmcp/data.json','jichitai/data.json','jichitai/jc.js']) {
    assert.doesNotMatch(read(path),/(?:href="|https:\/\/pet\.shiokonbu\.com|\ba\(')\/(?:joto|jichitai\/touroku)(?:[\/"'?#<]|$)/,path);
  }
  const mcp=JSON.parse(read('webmcp/data.json'));
  assert.ok(!mcp.categories.some(c=>c.id==='adoption_center'));
  assert.ok(!('adoption_center' in mcp.items));
  assert.ok(Object.values(JSON.parse(read('jichitai/data.json')).p).every(r=>!r.j));
  assert.match(read('jichitai/index.html'),/href="\/jichitai\/maigo\/"/);
  assert.match(read('jichitai/index.html'),/href="\/jichitai\/tebanasu\/"/);
  assert.match(read('sitemap.xml'),/https:\/\/pet\.shiokonbu\.com\/jichitai\/maigo\//);
  assert.match(read('404.html'),/<meta name="robots" content="noindex">/);
  assert.doesNotMatch(read('robots.txt'),/Disallow:\s*\/(?:joto|jichitai\/touroku)/);
});
