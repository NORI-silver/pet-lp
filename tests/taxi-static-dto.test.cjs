// 行き先（data-to）のあるトリマー・しつけ教室のカードは、/find-data/ のHTMLに料金リンクが最初から1つだけある
// （全件読み込みでカードが置きかわったあとも消えない）。.emg-taxi（「くわしく」以外）と .fac-taxi の両方を数える。
const fs = require("fs"), path = require("path"), assert = require("assert");
let cards = 0; const bad = [], ids = {};
for (const cat of ["dog-trainer", "trimming"]) {
  const dir = path.join(__dirname, "..", "find-data", cat);
  for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".json"))) {
    const j = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"));
    for (const [, hs] of j.groups) for (const h of hs) {
      const ot = h.slice(0, h.indexOf(">") + 1);
      const to = (ot.match(/\bdata-to="([^"]*)"/) || [])[1];
      if (!to || !/[都道府県市区町村郡]/.test(to)) continue;
      cards++;
      const links = (h.match(/<a [^>]*>/g) || []).filter((a) => (/emg-taxi/.test(a) && !/fc-a-info/.test(a)) || /fac-taxi/.test(a));
      const fid = (ot.match(/data-fid="([^"]*)"/) || [])[1];
      if (links.length !== 1) bad.push(cat + "/" + f + " " + fid + " n=" + links.length);
      else { ids[fid] = links[0]; const href = (links[0].match(/href="([^"]*)"/) || [])[1]; if (!href.startsWith("/?to=") || !href.endsWith("#form")) bad.push(fid + " href " + href); }
    }
  }
}
assert.ok(cards >= 13, "data-to cards found: " + cards);
assert.deepStrictEqual(bad, [], "data-to cards without exactly 1 correct static taxi link: " + bad.slice(0, 5).join(", "));
// 愛知のしつけ教室で、これまで静的リンクが無かった13件（T050ほか）に出ている
// （T050・T185・T184は支店が2つ、T189は町名までなので行き先を入れない。tests/trainer-no-dest.test.cjs）
for (const id of ["T054", "T186", "T187", "T188", "T190", "T191", "T051", "T055", "T276"]) assert.ok(ids[id], id + ": 静的の料金リンクがある");
const h54 = decodeURIComponent(ids["T054"].match(/href="([^"]*)"/)[1]);
assert.ok(h54.includes("愛知県名古屋市緑区鳴海町北浦72-1"), "T054 の行き先は data-to と同じ: " + h54);
console.log("ok data-to cards " + cards + " each with exactly 1 static taxi link");
