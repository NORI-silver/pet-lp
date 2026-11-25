const {test}=require('node:test');
const assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
test('night reception uses minutes, preserves 24h and distinguishes treatment end',()=>{
 const script=`import sys
sys.path.insert(0, 'tools')
import gen_prefcats as g, faccard as f
by={h['id']:h for h in g._HOS if 'id' in h}
assert [g._late(by[k]) for k in ('H059','H020','H014')]==[1470,1470,1440]
rows=[by['H059'],by['H020'],by['H014'],{'hours':'24時間'},{'hours':'予約制'},{'hours':'22時〜翌5時'}]
assert g._hours_counts(rows)==dict(all=1,past0=4,till5=2,unknown=1)
assert g._late({'hours':'20時〜24時30分'})==1470
assert f._edge_line('paw','診る動物','犬・猫・うさぎ・フェレット',f.CATS['hospital'])[2]=='犬・猫のほか うさぎ・フェレット'
assert f._edge_line('paw','診る動物','猫',f.CATS['hospital'])[2]=='猫だけ'
`;
 try {execFileSync(process.env.PYTHON||'python3.12',['-c',script],{encoding:'utf8'});}
 catch(e){if(e.code!=='ENOENT'||process.env.PYTHON)throw e;execFileSync('python3',['-c',script],{encoding:'utf8'});}
});
