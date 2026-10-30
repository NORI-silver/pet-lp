const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ctx = vm.createContext({ console, Date, JSON, Math, Number, String, Object, Array, isFinite });
vm.runInContext(fs.readFileSync('booking/Code.gs','utf8'),ctx);
const noLend = {cageLend:false, cageMust:'○'};
const fits = cage => ctx.fitsCage_(noLend, {'キャリー':cage, '同乗人数':'1人'});
assert.equal(fits('どれでも'), true);           // 「どれでも大丈夫」はしぼりこまない
assert.equal(fits('借りたい'), false);
assert.equal(fits('なし'), false);
assert.equal(fits('どれでも・借りたい'), false); // ほかの子が「借りたい」なら、その条件は残す
assert.ok(ctx.cageText_('どれでも').includes('どれでも大丈夫'));
console.log('PASS: cage "どれでも" matches every company and is explained to companies');
