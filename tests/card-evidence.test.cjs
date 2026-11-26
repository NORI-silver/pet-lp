const test=require('node:test'), assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
test('confirmed card data does not turn limitations, FAQs or surcharges into matches',()=>{
const py=`
import sys,re,html
sys.path.insert(0,'tools')
import gen_hotels,ownerfit,faccard,uikit,gen_sitters,gen_sougi,facility_cards
h=next(h for h in gen_hotels.J['hotels'] if h['id']=='PHt475672a')
yes,no=ownerfit.keys('pet-hotel',h['url'])
assert 'big' in yes and not {'sen','med','pup','staff24'}.intersection(yes)
assert {'staff24','night_staff'} <= set(no)
out=faccard.build_card(gen_hotels._card(html.escape,h),faccard.CATS['pet-hotel'],{}).split('class="fc-fit"')[0]
assert all(x in out for x in ('9,900円','11,000円','8歳未満','スタッフ不在','動物取扱業'))
assert ownerfit._find('大型駐車場完備','big')==0
assert 'big' not in uikit._keys(" data-fit='{\\\"s\\\":[\\\"l\\\"]}'>",'dog-trainer','https://kitanodog.com/')[0]
sf=next(s for s in gen_sougi.F['facilities'] if s['id']=='S105757')
yes,no=ownerfit.keys('sougi',sf['u'])
assert 'call24' in no and '深夜・早朝も受付' not in facility_cards.sougi_tags(sf)
assert '電話受付9:00〜17:00' in gen_sougi._fcard(html.escape,sf)
sit=next(s for s in gen_sitters.J['sitters'] if s['id']=='S175')
assert faccard._yen_of(sit)==4700 and '訪問介護60分4,800円' in gen_sitters._card(html.escape,sit)
assert 'big' in ownerfit.keys('trimming','https://www.dogsalon-purumo.com/')[1]
print('ok')`;
const text=execFileSync(process.env.PYTHON || 'python3',['-c',py],{encoding:'utf8'});
assert.equal(text.trim(),'ok');
});

test('shared result cards show only selected match tokens, not unknown/no/default dog',()=>{
const fs=require('node:fs'), vm=require('node:vm');
const source=fs.readFileSync('tools/find.js','utf8');
const body=source.slice(source.indexOf('  function matchLabels('),source.indexOf('  function apply('));
const ctx={LBL:{big:'大型犬',sen:'シニア',pickup:'送迎あり','a:dog':'犬',older:'60歳以上'},
 el(){return {hidden:false};}};
vm.createContext(ctx);vm.runInContext(body,ctx);
const node={querySelector(){return null;},appendChild(){}};
const it={_k:' big sen older ',_no:' sen ',querySelector(){return node;}};
ctx.matchLabels(it,['big','sen','pickup','a:dog','older'],true);
assert.equal(it._matchNote.textContent,'絞り込みに使った条件：大型犬・年齢・同居条件は詳細を確認');
ctx.matchLabels(it,[],true);
assert.equal(it._matchNote.hidden,true);
});

test('hospital result keeps confirmed active feature visible even with many badges',()=>{
const fs=require('node:fs'), vm=require('node:vm');
const source=fs.readFileSync('tools/hosp_find.js','utf8');
const body=source.slice(source.indexOf('  function card('),source.indexOf('  function match('));
const ctx={LABEL:{late:'19時以降も',open:'いま受付中'},NEEDL:{night:'夜間・救急'},
 FEAT:[['night','夜間・救急'],['late','19時以降も']],keys:()=>['late','night','open'],
 TB:'',enc:encodeURIComponent,openNow:()=>null,has:(r,k)=>r.y.includes(k), esc:String,picHtml:()=>''};
vm.createContext(ctx);vm.runInContext(body,ctx);
const text=ctx.card({n:'病院',u:'https://example.org',y:['night','late']},['open']);
assert.equal((text.match(/19時以降も/g)||[]).length,1);
assert.match(text,/class="u">いま受付中は不明/);
});

test('regional navigation is independent of prefecture data on individual cards',()=>{
const fs=require('node:fs'), vm=require('node:vm');
const src=fs.readFileSync('tools/find.js','utf8');
const body=src.slice(src.indexOf('  var parts ='),src.indexOf('  var items ='));
const ctx={location:{pathname:'/dogrun/tokyo/'},cat:'dogrun',SLUG:{'東京都':'tokyo','千葉県':'chiba'}};
vm.createContext(ctx);vm.runInContext(body,ctx);
assert.equal(ctx.routePf,'東京都');
ctx.location.pathname='/dogrun/chiba/chiba-shi/';
vm.runInContext(body,ctx);
assert.equal(ctx.routePf,'千葉県');
ctx.location.pathname='/dogrun/indoor/';
vm.runInContext(body,ctx);
assert.equal(ctx.routePf,'');
});

test('regional lists without a shared finder receive one native-navigation mount and script',()=>{
const py=`
import sys
sys.path.insert(0,'tools')
import uikit
page='<main><div class="emg"></div></main></body>'
args=('dog-trainer',['dog-trainer','tokyo'],{'tokyo','chiba'})
with_nav=uikit.pref_nav(page,*args)
assert with_nav.count('data-pref-nav="dog-trainer"') == 1
assert with_nav.count(uikit.PLACE_JS) == 1
assert with_nav == uikit.pref_nav(with_nav.replace(uikit.PLACE_JS+'\\n',''),*args)
already=page.replace('<main>','<main><div id="ffPlace"></div>')
assert uikit.pref_nav(already,*args) == already
print('ok')`;
const {execFileSync}=require('node:child_process');
assert.equal(execFileSync(process.env.PYTHON || 'python3',['-c',py],{encoding:'utf8'}).trim(),'ok');
});
