const test=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs');
const pages={
 '/dogrun/aichi/':['aichi-outdoor-choices','1時間2,000円','事前登録','5種以上'],
 '/dog-trainer/saitama/':['saitama-training-choices','5,000円','48,000円','5,500円'],
 '/trimming/osaka/':['osaka-grooming-cost','14,800円','1,100〜2,200円','交通費'],
 '/sougi/chiba/':['chiba-cremation-cost','4kg','8kg','返骨'],
 '/pet-hotel/osaka/':['osaka-large-stay','7,700円','11,000円','カメラ']
};
const read=p=>fs.readFileSync('.'+p+'index.html','utf8');
test('five local comparisons show concrete criteria in existing canonical routes',()=>{
 for(const [path,[id,...words]] of Object.entries(pages)){
  const h=read(path), start=h.indexOf('id="'+id+'"');
  assert.ok(start>=0,path+' comparison');
  assert.equal(h.indexOf('id="'+id+'"',start+1),-1,path+' single comparison');
  if (id==='osaka-large-stay'||id==='chiba-cremation-cost') assert.ok(h.slice(0,start).includes('href="#'+id+'"'),path+' links to its comparison from above');
  const block=h.slice(start,start+10500);
  for(const w of words)assert.ok(block.includes(w),path+': '+w);
  assert.ok(h.includes('rel="canonical" href="https://pet.shiokonbu.com'+path+'"'),path+' canonical');
 }
 for(const [path,id] of [['/dogrun/saitama/','aichi-outdoor-choices'],['/dog-trainer/osaka/','saitama-training-choices'],['/trimming/chiba/','osaka-grooming-cost'],['/sougi/tokyo/','chiba-cremation-cost'],['/pet-hotel/chiba/','osaka-large-stay']]) assert.ok(!read(path).includes('id="'+id+'"'),path+' not affected');
 assert.ok(!fs.existsSync('jichitai/touroku/index.html'));
 assert.ok(!fs.existsSync('joto/index.html'));
});
