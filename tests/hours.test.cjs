// 日をまたぐ営業時間・空欄のケージ貸し出し・犬猫のほかの子（2026-10-31 マッチング検査で見つかった抜け）
const fs=require('fs'),vm=require('vm');const ctx={console};vm.createContext(ctx);
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const a=require('assert');
a.deepEqual(JSON.stringify(ctx.hoursOf_('20時〜翌5時')),'[20,5]');
a.ok(ctx.inHours_(23,[20,5])&&ctx.inHours_(3,[20,5])&&!ctx.inHours_(12,[20,5]));
// nextOpen_ overnight: at 12:00 JST → opens 20:00 same day
const d=new Date('2026-11-01T03:00:00Z'); const o=ctx.nextOpen_(d,'20-5'); a.equal(o.toISOString(),'2026-11-01T11:00:00.000Z');
a.equal(ctx.nextOpen_(new Date('2026-11-01T18:00:00Z'),'20-5').toISOString(),'2026-11-01T18:00:00.000Z'); // 3:00 JST open
a.equal(ctx.nextOpen_(new Date('2026-11-01T12:00:00Z'),'8-18').toISOString(),'2026-11-01T23:00:00.000Z'); // 21:00 → next 8:00
const pt={id:'X',riders:null,pets:null,big:null,luggage:null,cageMust:'',cageLend:null,careTri:null,careOk:true,hours:'',rideHours:'',maxKg:null,maxBig:null,lendKg:null,petOnly:null,vacMust:null};
const r={'同乗人数':'1人','ペット数':1,'体重kg':4,'キャリー':'借りたい','種類':'その他','犬種・猫種':'うさぎ','ペットJSON':JSON.stringify([{species:'その他',breed:'うさぎ',weight:2}])};
a.ok(ctx.fitsCage_(pt,r)); const c=ctx.checks_(pt,r)
a.ok(c.ask.some(x=>/うさぎ/.test(x))&&c.ask.some(x=>/ケージを貸し出せる/.test(x)));
console.log('PASS: overnight hours, blank cage lending and other species become checks');
