const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),cp=require('node:child_process');
test('verified funeral cards distinguish attendance, ashes and plan-specific negatives',()=>{
const py=`
import sys
sys.path.insert(0,'tools')
from uikit import _keys
from ownerfit import checked_condition_status
G='合同火葬'; A='立ち会い'; R='お骨を返してもらえる'
for url in ['https://ypet.info/','https://www.yaku-yoke.com/doubutukuyo.html','https://www.pet-kasou.biz/']:
 y,n=_keys('class="emg-item"','sougi',url)
 assert R in y and G+'+'+R in n and G+'+'+A in n,(url,y,n)
for url in ['https://ichikawa-pet.co.jp/about','https://funabashi-petsaijyou.com/']:
 y,n=_keys('class="emg-item"','sougi',url)
 assert {A,R} <= set(y) and G in n,(url,y,n)
y,n=_keys('class="emg-item" data-tags="立ち会い"','sougi','https://ypet.info/')
assert A not in y and A not in n
assert checked_condition_status('sougi','https://ypet.info/')[A]==0
y,n=_keys('class="emg-item"','sougi','https://iwaki-pet-reien.com/price/index.html')
assert {A,R}<=set(y) and G+'+'+R in n and G+'+'+A not in n
print('ok')`;
assert.equal(cp.execFileSync(process.env.PYTHON||'python3',['-c',py],{encoding:'utf8'}).trim(),'ok');
});
test('same-plan negatives override independently matching options only when both are selected',()=>{
 const src=fs.readFileSync('tools/find.js','utf8');
 const ctx={geoKm:0,cat:'sougi',placeJ:()=>0};
 vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('  function judge('),src.indexOf('  function count(')),ctx);
 const a='立ち会い',g='合同火葬',r='お骨を返してもらえる';
 const card={_k:' '+[a,g,r].join(' ')+' ',_no:' '+g+'+'+a+' '+g+'+'+r+' '};
 assert.equal(ctx.judge(card,[g,r],[],''),2);
 assert.equal(ctx.judge(card,[a,g],[],''),2);
 assert.equal(ctx.judge(card,[a,r],[],''),0);
 assert.equal(ctx.judge(card,[g],[],''),0);
 assert.equal(ctx.judge({...card,_no:' '},[g,a],[],''),1);
 assert.equal(ctx.judge({...card,_no:' ',_k:card._k+g+'+'+a+' '},[g,a],[],''),0);
 ctx.cat='pet-hotel';
 assert.equal(ctx.judge(card,[g,r],[],''),0);
});
