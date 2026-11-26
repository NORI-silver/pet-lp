const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(root, name), 'utf8');
const src = JSON.parse(read('tools/rojin.json')).homes;
const find = read('tools/find.js');
const judge = vm.runInNewContext(find.match(/  function judge\(it, ks, pf, qs\)\{[\s\S]*?(?=\n  function count)/)[0]+';judge', {placeJ:()=>0, geoKm:0, cat:"rojin-home"});
function card(pref, id, shard) {
  const escaped = 'data-fid="'+id+'"';
  if (shard) {
    const cards = JSON.parse(read('find-data/rojin-home/'+pref+'.json')).groups.flatMap(([, rows])=>rows);
    const html = cards.find(row=>row.includes(escaped));
    assert.ok(html, id+' in fetched '+pref);
    return html;
  }
  const html = read('rojin-home/'+pref+'/index.html');
  const pos = html.indexOf(escaped);
  assert.ok(pos >= 0, id+' in direct '+pref);
  return html.slice(html.lastIndexOf('<div ',pos),html.indexOf('class="fc-more',pos));
}
function item(h) {
  const opening = h.slice(0,h.indexOf('>'));
  const attr = key =>' '+(opening.match(new RegExp(' '+key+'="([^"]*)"'))?.[1] || '')+' ';
  return {_k:attr('data-k'),_no:attr('data-no'),_q:''};
}
for (const shard of [false,true]) {
  const lulu = card('chiba','R108',shard);
  assert.match(lulu,/入所金・月額は各：20〜30kg未満22万円／30kg以上33万円/);
  assert.match(lulu,/詳しい所在地は、見学希望の方に施設から個別に案内/);
  assert.equal(judge(item(lulu),['big'],[],''),0);
  assert.equal(judge(item(lulu),['fee'],[],''),0);
  const orange = card('kanagawa','R043',shard);
  assert.match(orange,/大型犬の条件：大型犬も受け入れ。30kg以上は事前相談/);
  assert.equal(judge(item(orange),['big'],[],''),0);
  const kennels = card('tokyo','R011',shard);
  assert.match(kennels,/予約の条件：会員未登録の方は、見学カウンセリングと預かりサービスの予約に制限あり/);
  assert.notEqual(judge(item(kennels),['owner_live_dog'],[],''),0);
  const animal = card('saitama','R007',shard);
  assert.match(animal,/施設スタッフの確認用で、飼い主向けの映像公開はありません/);
  assert.equal(judge(item(animal),['owner_live_dog'],[],''),2);
  const lavie = card('ibaraki','R088',shard);
  assert.equal(judge(item(lavie),['owner_live_dog'],[],''),1,
    'a change in what the provider discloses is not proof of unavailability');
}
assert.ok(src.find(r=>r.id==='R088').facts.some(f=>f.v.includes('20:00〜翌8:00') && f.v.includes('写真・短い動画')));
assert.match(read('rojin-home/index.html'),/施設内の見守り用か、家族も映像を見られるか/);
