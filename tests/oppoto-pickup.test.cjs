// dogsalon oppoto（PHk421d80）の送迎：出典に今は書かれていないので「不明」に戻す（送迎なし、とは書かない）。
// 元の記載は retired_facts に出どころつきで残す。生成されたページには出さない。
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const d = JSON.parse(fs.readFileSync(path.join(root, 'tools/hotels.json'), 'utf8')).hotels.find(h => h.id === 'PHk421d80');
let fail = 0; const ok = (c, m) => { if (!c) { console.error('FAIL ' + m); fail++; } };
ok(d, 'レコードがある');
ok(d.pickup === undefined, 'pickup の印がない（不明）');
ok(!d.facts.some(f => f.k === '送迎'), '有効な事実に送迎がない');
ok(d.facts.some(f => f.k === '料金'), '料金の事実は残る（出どころは元のまま）');
const r = (d.retired_facts || []).find(f => f.k === '送迎');
ok(r && r.src && r.checked && r.reason && /不明/.test(r.reason), '元の記載が出どころ・確認日・理由つきで残る');
const web = JSON.parse(fs.readFileSync(path.join(root, 'tools/hotels_web.json'), 'utf8'));
ok(!('PHk421d80' in web), '送迎の文を含む収集文は有効な文として使わない');
const html = fs.readFileSync(path.join(root, 'pet-hotel/shiga/index.html'), 'utf8');
const i = html.indexOf('dogsalon oppoto', html.indexOf('<section class="emg-pref"'));
ok(i > 0, 'ページにカードが載っている');
const j = html.indexOf('class="emg-item', i + 10);
const card = html.slice(i, j > 0 ? j : i + 6000);
ok(!/10km|送迎/.test(card), 'カードに送迎・10kmの文がない');
ok(!/data-ft="[^"]*来てくれる・送迎/.test(html.slice(Math.max(0, i - 1200), i + 100)), '送迎のしぼりこみの印がない');
const row = html.indexOf('dogsalon oppoto', html.indexOf('<table', i));
ok(row > 0, '比較表に載っている');
ok(!/×/.test(html.slice(row, row + 800)), '比較欄に×を出さない（不明は空）');
if (fail) process.exit(1);
console.log('oppoto-pickup ok');

// 元データのどの写しにも、oppoto の送迎が有効な記載として残っていないこと（kinki_add.py を回しても戻らない）
{
  const fs = require('fs'), pth = require('path');
  for (const f of ['tools/hotels.json', 'tools/kinki_add.json']) {
    const L = JSON.parse(fs.readFileSync(pth.join(__dirname, '..', f), 'utf8')).hotels;
    const r = L.find(x => x.id === 'PHk421d80');
    if (!r) { console.error('missing PHk421d80 in ' + f); process.exit(1); }
    if ('pickup' in r || (r.facts || []).some(x => x.k === '送迎') || !(r.retired_facts || []).length) {
      console.error('oppoto pickup still active (or retired record missing) in ' + f); process.exit(1);
    }
  }
}
