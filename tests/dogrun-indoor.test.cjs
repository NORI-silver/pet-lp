const {test}=require('node:test');
const assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
test('indoor dogruns are confirmed by their actual facilities, not unrelated indoor mentions',()=>{
 const p=`import sys
sys.path.insert(0, 'tools')
import gen_dogrun as d
all_ids = {r['id'] for r in d.RUNS if 'indoor' in d.ff_keys(r)[0]}
assert all_ids == d._INDOOR_IDS and len(all_ids) >= 5, all_ids
assert {'D143','D194','D187','D209','D200'} <= all_ids
chiba = {r['id']: r for r in d.RUNS if r['pref'] == '千葉県' and r['id'] in all_ids}
assert {'D213','D216','D217','D218'} <= chiba.keys(), chiba.keys()
wag = chiba['D216']
assert '大型犬は貸切のみ' in wag['size'] and '10kg以下' in wag['size']
assert 'large' in d.ff_keys(wag)[0] and '前日' in d._INDOOR_BOOKING['D216']
for key in ('D217','D218'):
 assert 'large' not in d.ff_keys(chiba[key])[0] and 'free' not in d.ff_keys(chiba[key])[0]
assert not all_ids.intersection({'D002','D019','D146','D154'}), all_ids
print('ok')`;
 let out;
 try { out=execFileSync(process.env.PYTHON || 'python3.12',['-c',p],{encoding:'utf8'}); }
 catch (e) { if (e.code!=='ENOENT' || process.env.PYTHON) throw e; out=execFileSync('python3',['-c',p],{encoding:'utf8'}); }
 assert.equal(out.trim(),'ok');
});
