// マッチング検査（tools/match_audit.cjs）の結果を、1枚の表のページにする。社内用（会社名・ツール名を出してよい）
'use strict';
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// しくみ全体の抜け。count は当てはまる会社の数（候補・輸送・緊急の会社だけ数える）
const SYS = [
  { t: '分からない人数・頭数・荷物を「軽バン」とみなして、黙って外している', where: 'booking/Code.gs の fitsCar_（CONFIG.DEFAULT_CAR：大人2人・2匹・荷物少なめ）',
    d: 'checks_ は「分からないので会社が確かめる」としているのに、その前の fitsCar_ が大人3人・3匹以上・荷物多めの依頼を外す。会社は候補に出ず、お客さまには「見つかりません」と出る。', fix: '空欄は外さずに「確かめる」に回す（checks_ に任せる）。', hit: r => ['人数', '頭数', '荷物'].some(k => r.combos.d[k].drop) },
  { t: 'ケージの貸し出しが分からない会社を「用意なし」とみなして外している', where: 'fitsCage_（「借りたい」は ケージ貸し出し=○ の会社だけ）',
    d: '貸し出しの欄が空欄の会社は、「借りたい」を選んだお客さまの候補に一度も出ない。', fix: '空欄は「確かめる」に回し、大きさ（何kgの子まで）も一緒に確かめる。', hit: r => r.combos.d['貸しケージの大きさ'].drop },
  { t: '動物の種類を見ていない（うさぎ・鳥、猫を乗せない会社）', where: 'checks_・QUOTE_FIELDS（species を受け取っていない）',
    d: 'フォームで「その他」や「猫」を選んでも、犬だけの会社や種類が分からない会社がそのまま候補に出る。犬と猫を一緒に乗せられるかも見ていない。', fix: '予約シートに「乗せられる動物」（犬・猫・その他）の列を足し、分からない会社は確かめる項目にする。', hit: r => r.combos.d['動物の種類'].miss },
  { t: 'エリアを都県でしか見ていない', where: 'selectionCandidates_（pt.areas に都県が入っているか）',
    d: '多摩の店に江戸川のお迎えが、松戸の店に八王子のお迎えが候補として出る。帰りのお迎えの場所（往復で「ちがう場所」）のエリアも見ていない。', fix: '予約シートに「お店の場所」と「何kmまで」を足し、迎車料金の計算にすでにある距離（shop）で判定する。', hit: r => r.company.some(x => x.dim === 'エリア' && x.level === 'gap') },
  { t: '日をまたぐ営業時間（例 20〜翌5時）を書けない', where: 'hoursOf_・checks_（開始 < 終了 の前提）',
    d: '「20-5」と入れると、昼の依頼が通り、夜の依頼が外れる（逆になる）。', fix: 'hoursOf_ を日またぎに対応させる。', hit: r => r.gaps.some(x => /日をまたぐ/.test(x.text)) },
  { t: '「受付の時間」と「送迎できる時間」が分かれていない会社が多い', where: '予約シート「営業時間」「送迎できる時間」',
    d: '「受付24時間」は送迎の時間ではない。送迎の時間が空欄だと、営業時間（空欄なら8〜18時）の外は全部「確かめる」になる。「時間外は相談」の会社は時間外が外れる。', fix: '問い合わせで送迎できる時間を聞いて、送迎できる時間の列に入れる。', hit: r => r.gaps.some(x => x.dim === '時間') || r.company.some(x => x.dim === '時間') },
  { t: '割増は「倍率」「1つの時間帯」「乗る時刻だけ」でしか計算できない', where: 'selectionPrice_ の night()・tools/fares.json の night / night_hours',
    d: '「21〜8時 +3,300円」のような固定額、「21〜5時・5〜8時」のような2つの時間帯、割増の時間をまたぐ乗車（乗った時刻／着いた時刻／走った分）の決まりが入らない。COCOタクの各店は固定額。', fix: 'fares.json に固定額・複数の時間帯・またぎ方を足し、問い合わせの答えで埋める。', hit: r => r.company.some(x => x.dim === '料金' && /固定額|2つ/.test(x.text)) },
  { t: '持参のケージが車に入るかを聞いていない', where: 'checks_（ケージは「必須」と「貸し出し」だけ）',
    d: '25kg以上の子を自分のケージで乗せるとき、軽バンや車種の分からない会社にそのまま依頼が行く。人数が多いと特に入らない。', fix: '予約シートに車の荷室の大きさ（大型ケージが載るか）を足すか、大型犬＋持参ケージは「確かめる」に入れる。', hit: r => r.combos.d['持参ケージと車'].miss },
  { t: 'ワクチンが必須の会社なのに、予約シートに入っていない', where: '予約シート「ワクチン必須」',
    d: 'サイトに「ワクチン接種済みの動物」と書いてある会社でも、予約シートの欄が空欄だと、未接種の子の依頼を聞かずに出す。', fix: 'サイトの情報から「ワクチン必須」を○にする。', hit: r => r.combos.d['ワクチン'].miss },
  { t: '締切「前日◯時まで」を書けない', where: '予約シート「何時間前まで」（数字1つ）', d: '朝早い便は前日◯時まで、のような締切は「何時間前」に直せない。', fix: '「前日の締切時刻」の列を足す。', hit: r => r.gaps.some(x => x.dim === '締切') || r.company.some(x => x.dim === '締切') },
  { t: '料金表に入っているのは2社だけ', where: 'tools/fares.json', d: 'ほかの会社は候補カードが「料金はお見積もり」になる。お迎え料金がkm制の会社は、お店の位置がないと計算できない。待ち時間・高速代・追加料金（大型犬・多頭・介助・ケージ）も多くの会社で分からない。', fix: '提携したら fares.json に足す。問い合わせの答えで待ち時間・追加料金を埋める。', hit: r => r.company.some(x => /fares\.json）に入っていない/.test(x.text)) },
  { t: 'キャンセルの決まり・往復の支払いが候補カードに出ていない', where: '候補カード（selectionQuotes_ は支払い方法・時期だけ）', d: '会社ごとに「前日12時まで無料、当日50%」などちがうのに、お客さまが選ぶときに見えない。往復の支払い（別々かまとめてか）も分からない。', fix: 'キャンセルの決まりを予約シートに入れ、カードに出す。', hit: r => r.status !== '除外' },
  { t: '返事の速さをまだ測っていない', where: '問い合わせの記録（reply 列）', d: 'すべての会社が「未問い合わせ」。メールを読める時間（営業時間）から間に合うかは計算しているが、実際に何時間で返事が来るかは分からない。', fix: '問い合わせの返事が来た時刻を記録して、遅い会社は候補の順番を下げるか外す。', hit: r => r.status !== '除外' }
];
const LV = { miss: ['見落とし', 'miss'], drop: ['黙って除外', 'drop'], gap: ['しくみ外', 'gap'], ask: ['要確認', 'ask'], ok: ['OK', 'ok'] };
const SHORT = { 'エリア': 'エリア', '時間': '時間', '大型犬': '大型犬', '大型犬のkg': 'kg', '頭数': '頭数', '大型犬の頭数': '大型頭数', '人数': '人数', '頭数×人数': '頭×人', '荷物': '荷物', 'ケージ必須': 'ケージ', '貸しケージの大きさ': '貸ケージ', '持参ケージと車': '持参×車', 'ペットだけ': 'ペットだけ', 'ワクチン': 'ワクチン', '動物の種類': '種類', '介護の中身': '介護', '割増のまたぎ': '割増', '料金': '料金', '支払い': '支払い', '締切': '締切', 'キャンセル': 'キャンセル', '返事の速さ': '返事' };

function level(r, k) {
  const v = r.combos.d[k], lv = new Set(r.company.filter(x => x.dim === k).map(x => x.level));
  if (r.gaps.some(x => x.dim === k)) lv.add('gap');
  if (v.miss || lv.has('miss')) return 'miss';
  if (v.drop) return 'drop';
  if (lv.has('gap')) return 'gap';
  if (v.ask || lv.has('unknown')) return 'ask';
  return 'ok';
}

module.exports = function (meta, results, questions, NEW_Q) {
  const live = results.filter(r => r.combos);
  const rows = live.map(r => {
    const t = r.combos.typ, pc = x => Math.round(1000 * x / t.all) / 10;
    return { id: r.id, pref: r.pref, name: r.name, url: r.url, status: r.status, book: r.book, sheet: r.sheet,
      typ: { clean: pc(t.clean), ask: pc(t.ask), ng: pc(t.ng), drop: pc(t.drop), miss: pc(t.miss) },
      lv: meta.dims.map(k => level(r, k)),
      notes: r.gaps.concat(r.company).map(x => ({ dim: x.dim, level: x.level, text: x.text })),
      ex: r.combos.ex.filter(x => x.kind !== 'ng').slice(0, 14),
      sheetDiff: r.sheetCombos ? { drop: r.sheetCombos.typ.drop, miss: r.sheetCombos.typ.miss, all: r.sheetCombos.typ.all } : null,
      add: (questions[r.id] || {}).add || [] };
  });
  const sys = SYS.map(s => ({ t: s.t, where: s.where, d: s.d, fix: s.fix, n: live.filter(r => r.status !== '除外' && s.hit(r)).length }));
  const excluded = results.filter(r => r.status === '除外').map(r => ({ pref: r.pref, name: r.name, why: r.why }));
  const counts = {}; results.forEach(r => counts[r.status] = (counts[r.status] || 0) + 1);
  const book4 = live.filter(r => r.status === '候補' && r.book).length;
  const data = JSON.stringify({ rows, dims: meta.dims.map(k => SHORT[k] || k), dimsFull: meta.dims, LV, newQ: Object.values(NEW_Q).filter(Boolean) }).replace(/</g, '\\u003c');
  const gen = meta.generated.slice(0, 16).replace('T', ' ') + ' UTC';
  return `<title>マッチング検査</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* 検査票：左に会社、右に観点の格子。状態は色＋文字で示す */
:root{--bg:#f4f6f5;--panel:#ffffff;--ink:#1b2422;--sub:#5b6866;--line:#d9e0de;--accent:#14655d;
--miss:#c2362b;--miss-bg:#fbe5e2;--drop:#b4610f;--drop-bg:#fcecd9;--gap:#6a46a8;--gap-bg:#ece5f7;--ask:#8a7300;--ask-bg:#f7f0c9;--ok:#4f7d5c;--ok-bg:#e3efe6;
--body:"Zen Kaku Gothic New","Hiragino Sans","Noto Sans JP",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121816;--panel:#1a2220;--ink:#e3ebe8;--sub:#9aa9a5;--line:#2e3a37;--accent:#5cc2b5;
--miss:#ff8a7d;--miss-bg:#4a201c;--drop:#f0a95a;--drop-bg:#46301a;--gap:#bba0f0;--gap-bg:#33284a;--ask:#e3cd5b;--ask-bg:#3d3713;--ok:#8cc49b;--ok-bg:#1f3527;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121816;--panel:#1a2220;--ink:#e3ebe8;--sub:#9aa9a5;--line:#2e3a37;--accent:#5cc2b5;
--miss:#ff8a7d;--miss-bg:#4a201c;--drop:#f0a95a;--drop-bg:#46301a;--gap:#bba0f0;--gap-bg:#33284a;--ask:#e3cd5b;--ask-bg:#3d3713;--ok:#8cc49b;--ok-bg:#1f3527;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:14px;line-height:1.6}
.wrap{max-width:1280px;margin:0 auto;padding-block:28px 60px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:28px}
h1{font-size:26px;margin:0;font-weight:700;letter-spacing:.02em}h2{font-size:18px;margin:0 0 10px;text-wrap:balance}
.lede{color:var(--sub);max-width:70ch;margin:6px 0 0}
.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
.tally{display:flex;flex-wrap:wrap;gap:10px}
.tally div{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:10px 14px;min-width:120px}
.tally b{display:block;font-family:var(--mono);font-size:22px;font-weight:500}
.tally span{color:var(--sub);font-size:12px}
.legend{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:13px;color:var(--sub)}
.chip{display:inline-block;border-radius:3px;padding:0 6px;font-size:11px;font-weight:500;line-height:20px;white-space:nowrap}
.miss{background:var(--miss-bg);color:var(--miss)}.drop{background:var(--drop-bg);color:var(--drop)}.gap{background:var(--gap-bg);color:var(--gap)}.ask{background:var(--ask-bg);color:var(--ask)}.ok{background:var(--ok-bg);color:var(--ok)}
.sys{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(min(100%,380px),1fr))}
.sys article{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:12px 14px;display:grid;gap:4px;min-width:0}
.sys h3{font-size:14.5px;margin:0;display:flex;gap:8px;align-items:baseline;justify-content:space-between}
.sys h3 .n{font-family:var(--mono);color:var(--accent);font-size:13px;white-space:nowrap}
.sys p{margin:0;color:var(--sub);font-size:13px}.sys .fix{color:var(--ink)}.sys code{font-family:var(--mono);font-size:12px}
.controls{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center}
.controls label{font-size:13px;color:var(--sub);display:flex;gap:6px;align-items:center}
select,input[type=search]{font:inherit;font-size:13px;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:4px 8px}
.tbl{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:middle}
thead th{position:sticky;top:0;background:var(--panel);font-weight:500;color:var(--sub);font-size:11px;white-space:nowrap}
th.v{writing-mode:vertical-rl;height:72px;padding:6px 2px;text-align:left}
td.c{padding:3px 2px;text-align:center}
td.c i{display:block;width:18px;height:18px;border-radius:3px;margin:auto;font-style:normal;font-size:10px;line-height:18px}
td.name{min-width:190px}td.name a{color:var(--ink);text-decoration:none;font-weight:500}td.name a:hover{text-decoration:underline}
td.name small{display:block;color:var(--sub);font-size:11px}
tr.row{cursor:pointer}tr.row:hover td{background:color-mix(in srgb,var(--accent) 6%,transparent)}
tr.row:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.bar{display:flex;height:8px;width:110px;border-radius:2px;overflow:hidden;background:var(--line)}
.bar span{display:block;height:100%}
.detail td{background:var(--bg);padding:12px 14px}
.detail .cols{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr))}
.detail h4{margin:0 0 4px;font-size:12px;color:var(--sub);font-weight:500;letter-spacing:.04em}
.detail ul{margin:0;padding-left:18px;display:grid;gap:3px}
.detail li{font-size:12.5px}
.status{font-size:11px;color:var(--sub);white-space:nowrap}
.ex{list-style:none;padding:0;display:grid;gap:8px 18px;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));margin:0}
.ex li{font-size:13px}
@media (prefers-reduced-motion:no-preference){tr.row td{transition:background .12s}}
</style>
<div class="wrap">
<header>
<h1>マッチング検査</h1>
<p class="lede">予約フォームで選べる組み合わせ（1社 ${meta.combosPerCompany.toLocaleString()} 通り：時刻8つ×動物7通り×頭数4×人数4×荷物2×ケージ4×介護3×ワクチン2×片道/往復）を、全国 ${results.length} 社に当てた結果です。しぼりこみは本番と同じ booking/Code.gs の関数で動かし、会社の条件は各社サイトに書いてあることだけから作っています。作成 <span class="mono">${esc(gen)}</span>。社内用。</p>
</header>
<section>
<h2>サイトに残る会社</h2>
<div class="tally">
<div><b>${counts['候補'] || 0}</b><span>候補に出せる会社（全国）</span></div>
<div><b>${book4}</b><span>うち今の予約エリア（1都3県）</span></div>
<div><b>${counts['輸送のときだけ'] || 0}</b><span>輸送のときだけ出す（赤帽など）</span></div>
<div><b>${counts['緊急タブだけ'] || 0}</b><span>緊急タブだけ（救急搬送・往診）</span></div>
<div><b>${counts['除外'] || 0}</b><span>外す（閉鎖・ホテル送迎だけ など）</span></div>
</div>
</section>
<section>
<h2>しくみ全体の抜け</h2>
<div class="sys">${sys.map(s => `<article><h3><span>${esc(s.t)}</span><span class="n">${s.n}社</span></h3><p>${esc(s.d)}</p><p><code>${esc(s.where)}</code></p><p class="fix">直し方：${esc(s.fix)}</p></article>`).join('')}</div>
</section>
<section>
<h2>事業者ごとの表</h2>
<div class="legend"><span><span class="chip miss">見落とし</span> 受けられないのに候補に出る／料金表とサイトがずれる</span><span><span class="chip drop">黙って除外</span> 分からないのに外している</span><span><span class="chip gap">しくみ外</span> サイトにあるが、しくみに入れる欄・計算がない</span><span><span class="chip ask">要確認</span> 分からないので会社が確かめる（問い合わせで埋める）</span><span><span class="chip ok">OK</span></span></div>
<div class="controls" style="margin:12px 0">
<label for="fStatus">区分 <select id="fStatus"><option value="候補">候補に出せる会社</option><option value="輸送のときだけ">輸送のときだけ</option><option value="緊急タブだけ">緊急タブだけ</option><option value="">すべて</option></select></label>
<label for="fArea">地域 <select id="fArea"><option value="4">1都3県</option><option value="">全国</option></select></label>
<label for="fQ">名前 <input type="search" id="fQ" placeholder="例：COCO"></label>
<span class="status" id="count"></span>
</div>
<div class="tbl"><table><thead id="th"></thead><tbody id="tb"></tbody></table></div>
<p class="lede">帯は「よくある依頼」（犬・猫、2匹まで、大人1〜2人、荷物少なめ、7:50〜21:30）での内訳です：<span class="chip ok">そのまま出せる</span> <span class="chip ask">会社が確認</span> <span class="chip" style="background:var(--line);color:var(--sub)">正しく除外</span> <span class="chip drop">黙って除外</span> <span class="chip miss">見落とし</span>。行を押すと中身が開きます。</p>
</section>
<section>
<h2>問い合わせの下書きに足す項目の候補</h2>
<ul>${Object.values(NEW_Q).filter(Boolean).map(q => `<li>${esc(q)}</li>`).join('')}<li>返事の速さは聞かずに、返事が来た時刻を記録する</li></ul>
</section>
<section>
<h2>外す会社（${excluded.length}社）</h2>
<ul>${excluded.map(e => `<li>${esc(e.pref)} ${esc(e.name)}：${esc(e.why)}</li>`).join('')}</ul>
</section>
</div>
<script>
const D=${data};
const BOOK=['東京都','神奈川県','埼玉県','千葉県'];
const $=id=>document.getElementById(id);
const e=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
$('th').innerHTML='<tr><th>事業者</th><th>よくある依頼</th>'+D.dims.map((d,i)=>'<th class="v" title="'+e(D.dimsFull[i])+'">'+e(d)+'</th>').join('')+'</tr>';
const LVK=['miss','drop','gap','ask','ok'];
function render(){
  const st=$('fStatus').value,ar=$('fArea').value,q=$('fQ').value.trim().toLowerCase();
  const rows=D.rows.filter(r=>(!st||r.status===st)&&(!ar||BOOK.includes(r.pref)||r.pref==='全国')&&(!q||r.name.toLowerCase().includes(q)));
  $('count').textContent=rows.length+'社';
  $('tb').innerHTML=rows.map((r,i)=>{
    const t=r.typ;
    const bar='<div class="bar" title="そのまま '+t.clean+'%／確認 '+t.ask+'%／除外 '+t.ng+'%／黙って除外 '+t.drop+'%／見落とし '+t.miss+'%"><span class="ok" style="width:'+t.clean+'%;background:var(--ok)"></span><span style="width:'+t.ask+'%;background:var(--ask)"></span><span style="width:'+t.ng+'%;background:var(--sub);opacity:.35"></span><span style="width:'+t.drop+'%;background:var(--drop)"></span><span style="width:'+t.miss+'%;background:var(--miss)"></span></div>';
    const cells=r.lv.map((l,j)=>'<td class="c"><i class="'+l+'" title="'+e(D.dimsFull[j])+'：'+D.LV[l][0]+'">'+(l==='ok'?'':D.LV[l][0][0])+'</i></td>').join('');
    return '<tr class="row" tabindex="0" data-i="'+D.rows.indexOf(r)+'"><td class="name"><a href="'+e(r.url)+'" target="_blank" rel="noopener">'+e(r.name)+'</a><small>'+e(r.pref)+(r.sheet?' ・予約シート '+e(r.sheet.id)+(r.sheet.active?'（受付中）':''):'')+(r.status!=='候補'?' ・'+e(r.status):'')+'</small></td><td>'+bar+'<small class="mono" style="color:var(--sub)">'+t.clean+'% / '+t.ask+'%</small></td>'+cells+'</tr>';
  }).join('');
}
function detail(r){
  const by=l=>r.notes.filter(n=>n.level===l);
  const li=a=>a.length?'<ul>'+a.map(n=>'<li><span class="chip '+(n.level==='unknown'?'ask':n.level==='info'?'ok':n.level)+'">'+e(n.dim)+'</span> '+e(n.text)+'</li>').join('')+'</ul>':'<p class="status">なし</p>';
  const ex=r.ex.length?'<ul class="ex">'+r.ex.map(x=>'<li><span class="chip '+x.kind+'">'+e(D.LV[x.kind]?D.LV[x.kind][0]:x.kind)+'・'+e(x.dim)+'</span><br>'+e(x.input)+'<br><span style="color:var(--sub)">→ '+e(x.why)+'</span></li>').join('')+'</ul>':'';
  const sd=r.sheetDiff?'<p class="status">予約シートの今の値で動かすと、よくある依頼 '+r.sheetDiff.all+' 通りのうち 黙って除外 '+r.sheetDiff.drop+'・見落とし '+r.sheetDiff.miss+'</p>':'';
  return '<tr class="detail"><td colspan="'+(D.dims.length+2)+'"><div class="cols"><div><h4>しくみに入らない・ずれている</h4>'+li(by('miss').concat(by('gap')))+sd+'</div><div><h4>分からないこと（問い合わせで聞く）</h4>'+li(by('unknown'))+(r.add.length?'<h4 style="margin-top:8px">下書きに足す質問</h4><ul>'+r.add.map(a=>'<li>'+e(a)+'</li>').join('')+'</ul>':'')+'</div><div><h4>メモ</h4>'+li(by('info'))+'</div></div><h4 style="margin-top:12px">入力の例</h4>'+ex+'</td></tr>';
}
function toggle(tr){
  const n=tr.nextElementSibling;
  if(n&&n.classList.contains('detail')){n.remove();return;}
  tr.insertAdjacentHTML('afterend',detail(D.rows[Number(tr.dataset.i)]));
}
$('tb').addEventListener('click',ev=>{if(ev.target.closest('a'))return;const tr=ev.target.closest('tr.row');if(tr)toggle(tr);});
$('tb').addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){const tr=ev.target.closest('tr.row');if(tr){ev.preventDefault();toggle(tr);}}});
['fStatus','fArea','fQ'].forEach(id=>$(id).addEventListener('input',render));
render();
</script>
`;
};
