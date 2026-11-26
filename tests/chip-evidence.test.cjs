// 「カード払い」「日曜も」の印：実際のカードの文（出どころは各ID）で、肯定の根拠があるものだけに付くことを確かめる
const cp = require('child_process'), path = require('path');
const root = path.join(__dirname, '..');
const py = `
import sys, json
sys.path.insert(0, 'tools')
import chip_evidence as ce
f = json.load(open('tests/fixtures/chip-evidence.json', encoding='utf-8'))
out = {'card': [[x['id'], ce.card_ok(x['pay']), x['ok']] for x in f['card']],
       'sunday': [[x['id'], ce.sunday_ok([(a, b, None) for a, b in x['rows']]), x['ok']] for x in f['sunday']]}
print(json.dumps(out, ensure_ascii=False))
`;
const r = cp.spawnSync('python3', ['-c', py], { cwd: root, encoding: 'utf8' });
if (r.status !== 0) { console.error(r.stderr); process.exit(1); }
const o = JSON.parse(r.stdout); let fail = 0;
for (const k of ['card', 'sunday']) for (const [id, got, want] of o[k]) if (got !== want) { console.error(`FAIL ${k} ${id}: got ${got}, want ${want}`); fail++; }
if (o.card.length < 15 || o.sunday.length < 15) { console.error('too few fixtures'); fail++; }
if (fail) process.exit(1);
console.log('chip-evidence ok', o.card.length + o.sunday.length);
