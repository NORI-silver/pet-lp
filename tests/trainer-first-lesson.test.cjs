const assert = require('node:assert/strict');
const fs = require('node:fs');
const {select} = require('../dog-trainer/first-lesson.js');
const menus = require('../tools/trainer_compare.json');
const defaults = {city:'千葉市',mode:'school',issue:'',age:'',weight:'',breed:''};
const m = req => select(menus,{...defaults,...req});
assert.deepEqual(m({age:'5'}).map(e=>e.m.id),['TC044-puppy']);
assert.deepEqual(m({age:'7'}).map(e=>e.m.id),['TC044-private']);
assert.equal(m({age:'6'}).length,0);
assert.ok(m({}).every(e=>e.unknown.includes('対象月齢')));
assert.equal(m({city:'other'}).length,0);
assert.deepEqual(m({city:'市原市'}).map(e=>e.m.price),['5,500円（税込）']);
assert.equal(m({city:'市原市',mode:'visit'}).length,0);
assert.ok(m({city:'佐倉市',mode:'visit'}).some(e=>e.m.id==='TC033-trial'));
assert.ok(m({city:'佐倉市',mode:'visit',weight:'50',issue:'bite',breed:'セントバーナード'}).every(e=>e.unknown.includes('噛みつきの状況と受け入れ可否')));
assert.ok(m({city:'東金市',mode:'day'}).every(e=>e.m.contact.startsWith('https://') && !e.m.contact.includes('select-type')));
assert.ok(m({city:'東金市',mode:'day'}).some(e=>e.m.kind==='check'));
for (const path of ['dog-trainer/index.html','dog-trainer/chiba/index.html']) {
  const html=fs.readFileSync(path,'utf8');
  assert.equal((html.match(/id="first-lesson"/g)||[]).length,1);
  assert.ok(html.includes('id="ffRes"'));
  assert.ok(html.indexOf('/dog-trainer/first-lesson-data.js') < html.indexOf('/dog-trainer/first-lesson.js'));
}
assert.ok(!fs.readFileSync('dog-trainer/tokyo/index.html','utf8').includes('id="first-lesson"'));
console.log('初回料金・地域・月齢・確認が必要な条件・既存の一覧: OK');

// Exercise submit, render, adjustment and empty states without contacting any external endpoint.
const vm = require('node:vm');
const generated={window:{}};
vm.runInNewContext(fs.readFileSync('dog-trainer/first-lesson-data.js','utf8'),generated);
assert.deepEqual(JSON.parse(JSON.stringify(generated.window.trainerFirstLessonMenus)),menus);
const element = () => ({textContent:'', children:[], href:'', append(...x){this.children.push(...x);}, replaceChildren(...x){this.children=x;}, focus(){this.focused=true;}});
const events={}, status=element(), results=element(), button={disabled:true};
let request = {...defaults,city:'市原市'};
const form={addEventListener(n,fn){events[n]=fn;},reportValidity:()=>true,querySelector:()=>button};
const panel={querySelector(sel){return ({form,'.tc-status':status,'.tc-results':results,'.tc-data':{textContent:JSON.stringify(menus)}})[sel];}};
vm.runInNewContext(fs.readFileSync('dog-trainer/first-lesson.js','utf8'),{
  window:generated.window, document:{querySelector:()=>panel,createElement:element},
  FormData:class{[Symbol.iterator](){return Object.entries(request)[Symbol.iterator]();}}
});
assert.equal(button.disabled,false);
let prevented=false;
events.submit({preventDefault(){prevented=true;}});
assert.ok(prevented && status.focused);
assert.equal(results.children.length,1);
assert.ok(results.children[0].children.some(e=>e.textContent==='5,500円（税込）'));
assert.ok(results.children[0].children.some(e=>e.href==='https://i-onlywan.com/contact'));
events.input();
assert.equal(results.children.length,0);
request={...request,city:'other'};
events.submit({preventDefault(){}});
assert.match(status.textContent,/受け入れ不可という意味ではありません/);
console.log('フォームの比較・結果の表示・入力変更・結果なし: OK');

const sakura = m({city:'佐倉市',mode:'visit',weight:'50',issue:'bark'});
assert.ok(sakura.some(e=>e.m.id==='TC071-trial' && e.m.kind==='trial' && e.m.priceType==='base' && !e.unknown.includes('大型犬の受け入れ')));
assert.ok(sakura.some(e=>e.m.id==='TC090-counsel' && e.m.kind==='counsel' && e.unknown.includes('大型犬の受け入れ')));
assert.deepEqual(m({city:'船橋市',mode:'school'}).filter(e=>e.m.id.startsWith('T132-')).map(e=>e.m.price),['0円','3,300円']);
assert.ok(!m({city:'市原市',mode:'visit'}).some(e=>e.m.id==='TC071-trial'));
