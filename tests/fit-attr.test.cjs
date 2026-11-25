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
