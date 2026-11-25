const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const ctx = vm.createContext({Date});
vm.runInContext(fs.readFileSync('booking/Code.gs', 'utf8'), ctx);
const kyoto = ctx.DISPLAY_COMPANIES.find(c => c.id === 'D7f0d2a2');
assert.ok(kyoto);

const from = {lat:35.00, lng:135.00};
const to = {lat:35.01, lng:135.00};
function price(pickupKm, rideKm, hour, round = false) {
  ctx.roadKm_ = (_shop, point) => point.lat === from.lat ? pickupKm : 10;
  ctx.legKm_ = ctx.roadKm_;
  return ctx.displayPrice_(kyoto, {
    trip: round ? '往復' : '片道', pickup:'A', dropoff:'B',
    return_pickup:'B', return_dropoff:'A',
    datetime:'2026-12-05T' + String(hour).padStart(2,'0') + ':00',
    return_datetime:'2026-12-05T16:00',
    route_details:JSON.stringify({km:rideKm, backKm:rideKm, from, to, backFrom:to, backTo:from})
  });
}
for (const [pickup, ride, hour, expected] of [
  [5,10,12,4950], [20,30,12,10725], [10,20,23,10725], [60,80,12,25575]
]) assert.equal(price(pickup, ride, hour).amount, expected);
const round = price(5,10,12,true);
assert.equal(round.local.pickup,825,'往復のお迎え代は行きの1回だけ');
assert.equal(round.amount,9075,'合成ルートの料金。実際のお客さまへの確定額ではない');
console.log('PASS: Kyoto four approved benchmark prices and one outbound pickup on round trips.');
