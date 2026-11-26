const test = require('node:test'), fs = require('node:fs'), assert = require('node:assert/strict');
const h = p => fs.readFileSync(p+'/index.html','utf8');
const title = x => x.match(/<title>([^<]+)<\/title>/)[1];
const desc = x => x.match(/<meta name="description" content="([^"]+)"/)[1];
test('senior-care search titles and descriptions match each page geographic scope', () => {
 const national=h('rojin-home'), chiba=h('rojin-home/chiba');
 for(const [text,url] of [[national,'rojin-home/'],[chiba,'rojin-home/chiba/']]){
  assert.doesNotMatch(title(text),/タクシー/);
  assert.ok(text.includes('rel="canonical" href="https://pet.shiokonbu.com/'+url+'"'));
 }
 assert.match(desc(national),/^老犬ホームは、シニア犬/);
 assert.doesNotMatch(desc(national),/北海道|千葉/);
 assert.match(national,/<div class="emg-tips" id="rojin-overview">/);
 assert.match(national,/<section class="emg-pref"[^>]*data-pref="北海道"[^>]*data-nosnippet>/);
 assert.match(national,/href="\/rojin-home\/chiba\/"/);
 assert.match(title(chiba),/^千葉県の老犬ホーム・老猫ホーム/);
 assert.match(desc(chiba),/^千葉県で.+入所金・月額、見学/);
 assert.doesNotMatch(desc(chiba),/北海道|タクシー/);
 assert.doesNotMatch(chiba,/<section class="emg-pref"[^>]*data-nosnippet/);
});
