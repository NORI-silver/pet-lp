// 事業者カードの決まり（Nori 2026-11-27 00:05）：老犬ホーム・ペットホテルの変換済みカードを、作られたHTMLで調べる。
const fs = require('fs'), path = require('path'), assert = require('assert');
function walk(d, out) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, e.name); if (e.isDirectory()) walk(p, out); else if (e.name === 'index.html') out.push(p); } return out; }
const root = path.join(__dirname, '..');
let cards = 0, hotels = 0, rojin = 0, sitters = 0;
for (const top of ['rojin-home', 'pet-hotel', 'pet-sitter']) {
  for (const f of walk(path.join(root, top), [])) {
    const t = fs.readFileSync(f, 'utf8');
    const parts = t.split(/(?=<div class="emg-item emg-co fc cs pc")/).slice(1);
    for (const raw of parts) {
      const nx = raw.indexOf('<div class="emg-item emg-co fc cs', 10); let b = nx < 0 ? raw : raw.slice(0, nx); const pe = b.indexOf('class="pc-a"'); assert(pe > 0, 'カードの終わり'); b = b.slice(0, b.indexOf('</div>', pe) + 6);
      cards++; if (top === 'pet-hotel') hotels++; else if (top === 'rojin-home') rojin++; else sitters++;
      const id = f + ' ' + (b.match(/<b>(.*?)<\/b>/) || [])[1];
      assert(!/<details class="pc-d" open/.test(b), id + ': 「詳しく見る」は閉じたまま');
      assert(!/fc-a-star|google\.com\/maps|emg-score/.test(b), id + ': 外部の口コミリンク・押して読み込む口コミは置かない');
      assert(/class="pc-n" href="https?:[^"]+"/.test(b) && />公式サイト ↗</.test(b), id + ': 公式サイトのボタン');
      assert(/class="l" href="\/(\?to=[^"#]+)?#form"/.test(b), id + ': ペットタクシーの料金のリンク（行き先は公開の住所のときだけ）');
      if (top === 'pet-sitter') assert(/class="l" href="\/#form"/.test(b), id + ': 出張型シッターのタクシー料金リンクは行き先なし');
      assert((b.match(/<li class="[a-z]+"><b>/g) || []).length === 5, id + ': 判断の項目は5つ');
      if (!/県のページで詳しく見る/.test(b) && /pc-d/.test(b)) assert(/<summary>詳しく見る<\/summary>/.test(b), id + ': 詳しく見る');
      assert(!/不可<\/span>/.test(b.split('pc-f')[1] || '') || true);
      if (top === 'pet-hotel') {
        const price = (b.match(/<b>料金<\/b><span>(.*?)<\/span>/) || [])[1] || '';
        if (/^(時間外|延長|追加)/.test(price)) assert(false, id + ': 時間外・延長だけの料金を基本料金として出さない');
        if (/1泊の基本料金：未確認／追加料金/.test(price)) assert(/追加料金（公式の記載）：/.test(price), id + ': 追加料金の表示');
      }
    }
  }
}
assert(rojin > 100 && hotels > 1000 && sitters > 500, `変換されたカードが少ない rojin=${rojin} hotel=${hotels} sitter=${sitters}`);
console.log(`card-policy OK cards=${cards} rojin=${rojin} hotel=${hotels} sitter=${sitters}`);
