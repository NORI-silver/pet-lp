// 提携先の「乗せられる動物」：書いてある会社には対象外の動物の依頼を送らない。空欄の会社は確かめてもらう
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const base={riders:3,pets:5,luggage:true,big:true,maxKg:null,maxBig:null,cageMust:'不要',cageLend:true,lendKg:null,careOk:true,hours:'0-24',rideHours:'0-24'};
const r=sp=>({'種類':sp,'体重kg':'3','ペット数':'1','同乗人数':'1人','キャリー':'持っている','介助':'不要'});
const ng=(animals,req)=>ctx.checks_({...base,animals:ctx.animalsOf_(animals)},req);
assert.equal(ng('犬・猫',r('うさぎ')).ng.length,1);           // 犬猫だけの会社にうさぎは送らない
assert.equal(ng('犬・猫・うさぎ',r('うさぎ')).ng.length,0);
assert.equal(ng('すべて',r('うさぎ')).ng.length,0);
assert.equal(ng('犬のみ',r('猫')).ng.length,1);                       // 犬だけの会社に猫は送らない
assert.equal(ng('犬・猫',r('犬')).ng.length,0);
const blank=ng('',r('うさぎ'));                                // 空欄は今までどおり確かめてもらう
assert.equal(blank.ng.length,0);assert.ok(blank.ask.some(x=>/犬・猫のほかの子/.test(x)));
assert.equal(ng('',r('猫')).ask.filter(x=>/犬・猫のほか/.test(x)).length,0);
console.log('PASS: partner animal list excludes requests for animals the company does not carry; blank keeps asking');
