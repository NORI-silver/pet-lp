// data-fit はシングルクォートで書く（&quot; を使わない分だけ小さい）。値はDOM上で同じでなければならない。
// 「& ' < > " 」を含む値でも、読み戻した値が元と同じことを確かめる。
const {test}=require('node:test'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process'),fs=require('node:fs'),path=require('node:path');
test('data-fit single-quote form round-trips awkward characters', ()=>{
  const py=`
import sys,json,html
sys.path.insert(0,'tools')
import faccard
for t in ['犬 & 猫 <b> it\\'s "q"','a&amp;b','x\\'y"z<>&','']:
    d={'at':t,'a':['dog']}
    a=faccard.fit_attr_str(d)
    old=' data-fit="'+html.escape(json.dumps(d,ensure_ascii=False,separators=(',',':')))+'"'
    assert json.loads(faccard.fit_attr_values(a)[0])==d
    assert faccard.fit_attr_values(old)==faccard.fit_attr_values(a)
    assert faccard.fit_single_quote(old)==a
print('ok')`;
  assert.equal(execFileSync('python3',['-c',py],{encoding:'utf8'}).trim(),'ok');
});
test('every data-fit in info pages is single-quoted and parses as JSON', ()=>{
  let n=0;
  (function walk(d){for(const f of fs.readdirSync(d,{withFileTypes:true})){const p=path.join(d,f.name);if(f.isDirectory()){if(!['.git','node_modules'].includes(f.name))walk(p);}else if(f.name==='index.html'){
    const h=fs.readFileSync(p,'utf8');
    assert.ok(!/ data-fit="/.test(h), p+' has a double-quoted data-fit');
    for(const m of h.matchAll(/ data-fit='([^']*)'/g)){const v=m[1].replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&amp;/g,'&');JSON.parse(v);n++;}
  }}})('.');
  assert.ok(n>1000,'only '+n+' data-fit found');
});
test('closed (受け入れ休止) homes carry cl=1 and fit.js never counts them as a match', ()=>{
  const py=`
import sys,json
sys.path.insert(0,'tools')
import faccard
a=json.loads(faccard.fit_attr_values(faccard.fit_attr(['dog','cat'],False,closed=True))[0])
assert a['cl']==1 and a['a']==['dog','cat'], a
assert 'cl' not in json.loads(faccard.fit_attr_values(faccard.fit_attr(['dog']))[0])
h=[x for x in json.load(open('tools/rojin.json'))['homes'] if x['id']=='R158'][0]
assert h['closed'] and h['animals']=='犬・猫'
print('ok')`;
  assert.equal(execFileSync('python3',['-c',py],{encoding:'utf8'}).trim(),'ok');
  const js=fs.readFileSync('fit.js','utf8');
  assert.ok(js.includes('if (f.cl) r.push(["ng"'), 'judge must mark closed homes ng');
  assert.ok(js.includes('c._fit.cl ? [["ng"'), 'closed chip must show without any filter');
});
test('R158 closed: static badge + data-closed in the generated card, and find.js never counts it as an animal match', ()=>{
  const t=fs.readFileSync('rojin-home/kanagawa/index.html','utf8');
  const i=t.indexOf('data-fid="R158"'); assert.ok(i>0,'R158 card missing');
  const open=t.slice(t.lastIndexOf('<div',i),t.indexOf('>',i)+1);
  assert.ok(/ data-closed="1"/.test(open),'R158 needs data-closed');
  const blk=t.slice(i,i+6000);
  assert.ok(/<span class="pc-cl">現在、受け入れを休止中<\/span>/.test(blk),'static 休止 badge missing');
  assert.ok(/受け入れ<\/b><span>犬・猫 現在、受け入れを休止/.test(blk),'受け入れ row must lead with the suspension');
  for(const jf of ['tools/find.js','find.js']){const js=fs.readFileSync(jf,'utf8');
  assert.ok(js.includes('it._cl = it.hasAttribute("data-closed")'));
  assert.ok(/if \(it\._cl && ks\.length\) \{ if \(ks\.some\(function\(k\)\{ return k\.indexOf\("a:"\) === 0; \}\)\) return 2; r = 1; \}/.test(js),'judge must exclude closed on animal picks and demote on other picks: '+jf);}
});
