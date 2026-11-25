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
assert not all_ids.intersection({'D002','D019','D146','D154'}), all_ids
print('ok')`;
 let out;
 try { out=execFileSync(process.env.PYTHON || 'python3.12',['-c',p],{encoding:'utf8'}); }
 catch (e) { if (e.code!=='ENOENT' || process.env.PYTHON) throw e; out=execFileSync('python3',['-c',p],{encoding:'utf8'}); }
 assert.equal(out.trim(),'ok');
});
