'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
test('海岸寺のページ：確認できた体重帯、選び方、出典を出し、noindex主判定は通常のまま',()=>{
  const page=read('sougi/kagawa/s0b9ae7/index.html');
  for(const s of ['体重と見送り方で火葬を選ぶ','15,400円','23,100円','52,800円','74,800円','https://kagawa-pet.com/pages/26/']) assert.ok(page.includes(s),s);
  assert.doesNotMatch(page,/<meta name="robots" content="[^"]*noindex/i);
  assert.match(read('sitemaps/sougi.xml'),/\/sougi\/kagawa\/s0b9ae7\//);
});
test('老犬ホーム費用：月額と初月を区別し、別の期間を相場にしない',()=>{
  const page=read('guide/rojin-home-cost/index.html');
  for(const s of ['290,000円','140,000円','328,735円','全国相場ではなく','https://kk-lavie.com/senior-dog/','https://rouken-kaigo.co.jp/price/']) assert.ok(page.includes(s),s);
  assert.match(page, /初月(?:<[^>]+>)*290,000円/);
  assert.doesNotMatch(page,/この記事には金額を書いていません/);
});
test('愛知のしつけ：無料の自治体教室と有料の預かりを区別して表示',()=>{
  const page=read('dog-trainer/aichi/index.html');
  for(const s of ['豊田市','25,000円','69,500円']) assert.ok(page.includes(s),s);
  assert.match(page, /無料/);
});
