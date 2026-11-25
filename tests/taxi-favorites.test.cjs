'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {model} = require('../taxi-favorites.js');
const config = model({D1a:['公開の会社','https://example.com/'],D2a:['掲載停止','https://example.com/']},{P001:'D1a',P002:'D2a'},['D2a','P009']);
test('保存値は公開IDだけ、提携受付の別IDは公開IDに正規化', () => {
  assert.deepEqual(config.read(JSON.stringify(['P001','D1a','D2a','P009','D3a',{id:'D1a',fare:1234}])),['D1a']);
  assert.deepEqual(config.read('not json'),[]);
  assert.deepEqual(config.offer({id:'P001',label:'予約情報',fare:1234,token:'private'}),{id:'D1a',label:'公開の会社'});
});
test('掲載停止・非公開・見本は保存不可', () => {
  for(const card of [{id:'D2a'},{id:'P002'}, {id:'P009'}, {id:'P874'}, {id:'D1a',demo:true}, {id:'D1a',anon:true}, {id:'D1a',anonTag:'A'}]){
    assert.equal(config.offer(card),null);
  }
  assert.equal(config.offer({id:'D1a',anon:true,site:'https://example.com/'}).id,'D1a');
});
