// 会社のお返事で予約できる期限：お返事から24時間か、お迎えの1時間前の早いほう。キャンセルの決まりの見せ方
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx=vm.createContext({Date,JSON,Math,Number,String,Object,Array,isFinite});
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const H=3600000, t=Date.UTC(2026,10,1,0,0);
assert.equal(ctx.quoteUntil_({time:t,at:t+72*H}),t+24*H);          // 3日後のお迎え → お返事から24時間
assert.equal(ctx.quoteUntil_({time:t,at:t+5*H}),t+4*H);            // 5時間後のお迎え → お迎えの1時間前
assert.match(ctx.cancelRuleText_({name:'A社',cancelRule:'前日まで無料'}),/前日まで無料（A社の規定）/);
assert.match(ctx.cancelRuleText_({name:'A社',cancelRule:''}),/A社のキャンセル規定によります/);
console.log('PASS: quote expiry = min(reply+24h, pickup-1h); cancel rule shown before booking');
