// 裏側の並び（情報の充実度）の検査：安定ソート・同点は元の順・お金/提携は使わない・UIに「情報が多い」並び替えを出さない
const cp = require('child_process'), fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const py = `
import sys, json
sys.path.insert(0, 'tools')
import richsort as r
rich = {"id":"a","name":"A","url":"https://x","facts":[{"k":"料金","yen":1000},{"k":"営業時間"}],"hours":"9-18","addr":"x"}
thin = {"id":"b","name":"B"}
tie1 = {"id":"c","name":"C"}; tie2 = {"id":"d","name":"D"}
paid = {"id":"e","name":"E","partner":True,"paid":True,"sponsor":True}
out = [x["id"] for x in r._sorted([thin, tie1, rich, tie2, paid], {})]
print(json.dumps(out))
`;
const res = cp.spawnSync('python3', ['-c', py], { cwd: root, encoding: 'utf8' });
if (res.status !== 0) { console.error(res.stderr); process.exit(1); }
const out = JSON.parse(res.stdout);
let fail = 0;
const ok = (c, m) => { if (!c) { console.error('FAIL ' + m); fail++; } };
ok(out[0] === 'a', '情報が多い施設が先頭');
ok(JSON.stringify(out.slice(1)) === JSON.stringify(['b', 'c', 'd', 'e']), '同点（情報なし・お金/提携の記載だけ）は元の順を保つ: ' + out);
const sel = fs.readFileSync(path.join(root, 'tools/uikit.py'), 'utf8');
ok(!/情報が多い/.test(sel), 'uikit に「情報が多い」並び替えが無い');
if (fail) process.exit(1);
console.log('richsort ok');
