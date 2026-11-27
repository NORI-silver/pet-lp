'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const markup = p => fs.readFileSync(path.join(root, p), 'utf8');
const brand = 'ペットのくらし窓口';
const types = ['rojin-home','dog-trainer/chiba','dogrun','pet-sitter','trimming','pet-hotel','hospital','sougi','guide','guide/night-emergency-survey','guide/train-plane-rules','jichitai'];
test('検索のページ題は内容を残し、末尾で旧サイト名を使わない', () => {
  for (const p of types) {
    const h=markup(p+'/index.html');
    const t=h.match(/<title>([^<]*)<\/title>/i)?.[1];
    assert.ok(t && t.includes(brand), p);
    assert.doesNotMatch(t, /(?:[｜|]| - )\s*(?:ペットタクシー(?:の?予約窓口)?|SHIOKONBU)\s*$/i, p);
    assert.match(h, /<meta property="og:site_name" content="ペットのくらし窓口">/, p);
  }
});
test('ホームは総合の窓口、ペットタクシーは分野のひとつとして残る', () => {
  const h=markup('index.html');
  assert.match(h, /<title>ペットのくらし窓口｜[^<]*ペットタクシー[^<]*<\/title>/);
  for (const name of ['WebSite','Organization']) {
    const meta=[...h.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)]
      .flatMap(([,s]) => {const data=JSON.parse(s);return data['@graph']||data;})
      .find(x=>x['@type']===name);
    assert.ok(meta, name);
    assert.equal(meta.name, brand);
    assert.equal(meta.alternateName, undefined);
  }
});
