// 行き先が1つに決まらないしつけ教室のカードには、行き先（data-to）を入れず、通常の料金ページへのリンクと理由を出す。
// 対象は ID で決める（「／」の入った文字を全部はずすのではない）。値は 2026-11-28 に find-data で確認。
const fs = require("fs"), path = require("path"), assert = require("assert");
const BRANCH = ["T050", "T004", "T005", "T023", "T185", "T184", "T015", "T118", "T037"];
const AREA = ["T029", "T031", "T034", "T060", "T070", "T109", "T145", "T189"];
const NOTE = { branch: "支店により行き先が異なります", area: "住所未確定のため行き先なし" };
const seen = {}, withTo = {};
const dir = path.join(__dirname, "..", "find-data", "dog-trainer");
for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".json"))) {
  const j = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"));
  for (const [, hs] of j.groups) for (const h of hs) {
    const ot = h.slice(0, h.indexOf(">") + 1);
    const fid = (ot.match(/data-fid="([^"]*)"/) || [])[1];
    const to = (ot.match(/\bdata-to="([^"]*)"/) || [])[1];
    const links = (h.match(/<a [^>]*>/g) || []).filter((a) => (/emg-taxi/.test(a) && !/fc-a-info/.test(a)) || /fac-taxi/.test(a));
    const kind = BRANCH.includes(fid) ? "branch" : AREA.includes(fid) ? "area" : null;
    if (kind) {
      (seen[fid] = seen[fid] || []).push(1);
      assert.ok(!to, fid + ": 行き先を入れない: " + to);
      assert.ok(ot.includes('data-to-note="' + kind + '"'), fid + ": 理由の印");
      assert.ok(!/data-to-label/.test(ot), fid + ": data-to-label もない");
      assert.strictEqual(links.length, 1, fid + ": 料金リンクは1つ");
      assert.ok(/href="\/#form"/.test(links[0]), fid + ": 通常の料金ページ（行き先なし）: " + links[0]);
            assert.ok(h.includes("<span style=\"display:block;overflow:visible\">" + NOTE[kind] + "</span>"), fid + ": カードに理由が見える");
      assert.ok(!/data-route/.test(h), fid + ": 経路のリンクは出さない");
    } else if (to) {
      withTo[fid] = to;
    }
  }
}
for (const id of BRANCH.concat(AREA)) assert.ok(seen[id], id + ": find-data にある");
// 対象以外（住所が1つの教室）は今までと同じ：行き先あり、「／」なし、番地などの数字あり
const rest = Object.entries(withTo);
assert.strictEqual(rest.length, 225, "対象以外で行き先のある教室は225件: " + rest.length);
for (const [fid, to] of rest) { assert.ok(!/[／;；]/.test(to), fid + ": 住所が2つ以上のものは残っていない: " + to); assert.ok(/[\d０-９]/.test(to), fid + ": 番地などのない行き先は残っていない: " + to); }
assert.strictEqual(withTo["T054"], "愛知県名古屋市緑区鳴海町北浦72-1");
assert.ok(withTo["T114"], "T114（京都の事業所の指定）は行き先のまま");
console.log("ok no-dest cohort " + (BRANCH.length + AREA.length) + ", other data-to " + rest.length);
