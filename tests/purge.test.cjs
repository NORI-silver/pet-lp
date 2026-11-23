// 古い個人情報を消す：お迎えの日（なければ受付日）から1年たった行だけ
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite,isNaN});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const D=86400000, now=Date.UTC(2027,11,1);
assert.equal(ctx.purgeDue_({'受付日時':new Date(now-400*D),'お迎え予定':new Date(now-300*D)},now,365),false); // お迎えから1年たっていない
assert.equal(ctx.purgeDue_({'受付日時':new Date(now-400*D),'お迎え予定':''},now,365),true);
assert.equal(ctx.purgeDue_({'受付日時':''},now,365),false);                                                  // 日付が分からない行は消さない
const vals=[['受付日時','お名前','料金の目安'],[new Date(now-400*D),'山田','5000'],[new Date(now-10*D),'佐藤','3000']];
let written=[];const sh={getDataRange:()=>({getValues:()=>vals.map(r=>r.slice())}),getRange:(r)=>({setValues:(v)=>written.push([r,v[0]])})};
assert.equal(ctx.purgeSheet_(sh,['お名前','電話番号'],now,365),1);
assert.deepEqual(written[0][1],[vals[1][0],'（削除済み）','5000']);                                            // 料金は残す
console.log('PASS: personal data cleared one year after pickup; fare kept');
