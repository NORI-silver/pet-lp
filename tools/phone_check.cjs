#!/usr/bin/env node
// [G] スマホの画面で、言われる前に気づく（Nori 2026-11-16「指示しなくてもできるようにしたい」）。
// ページをスマホの幅（390×844）で開き、写真を撮り、AGENTS.md「品質の決まり」のうち目で見ないと分からないことを確かめる。
// 何も送らない・何も書き換えない（写真とまとめを出力のフォルダに置くだけ）。
//
// 使い方（リポジトリの一番上で）:
//   node tools/phone_check.cjs --changed            … main から変わったページ（生成ファイルふくむ）。PRを出す前・報告の前に必ず
//   node tools/phone_check.cjs /hinan/ /sougi/       … ページを指定
//   node tools/phone_check.cjs --sample             … 分野ごとに入口・県・1件ずつ（週1回の見回り）
//   オプション: --out <フォルダ>（既定 /tmp/phone-check）、--max <数>（既定 40）、--base <URL>（既定はリポジトリをその場で配る）
// 出力: <out>/report.md（違反の一覧）と <out>/<ページ>.png（最初の2画面分）。報告では写真を自分の目で見てから書く。
//
// 見ること:
//   overflow  横にはみ出してスクロールできる
//   first     施設の分野で、さがす欄か結果のカードが最初の1.3画面に入っていない（説明・記事が先）
//   tallgrid  ボタン・リンクが8つ以上ならぶ箱が1画面より高い（47都道府県のボタンなど）
//   uneven    横にならんだカードの高さがそろっていない（8px 以上の差）
//   textonly  アイコン・図・表・ボタンのない、文字だけの画面がある（2画面目より下）
//   tiny      本文の字が 11px より小さい
//   form      ペットタクシーのページで、フォームの最初の入力欄（お迎えの都道府県）が最初の1画面に入っていない
//   dup       フォームの上に「無料」が2回以上・準備中のお知らせがある
const {chromium} = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), {execSync} = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const OUT = opt('--out', '/tmp/phone-check'), MAX = +opt('--max', 40);
const FAC = ['hospital', 'pet-hotel', 'dogrun', 'pet-sitter', 'trimming', 'dog-trainer', 'rojin-home', 'sougi', 'joto',
  'inu-yado', 'pet-yado', 'inu-cafe', 'jichitai', 'hinan', 'emergency'];
const W = 390, H = 844;
// 県のページ（さがす欄が先に来るべきページ）。記事（/dogrun/survey/ など）は入れない
const PREF = new Set('hokkaido aomori iwate miyagi akita yamagata fukushima ibaraki tochigi gunma saitama chiba tokyo kanagawa niigata toyama ishikawa fukui yamanashi nagano gifu shizuoka aichi mie shiga kyoto osaka hyogo nara wakayama tottori shimane okayama hiroshima yamaguchi tokushima kagawa ehime kochi fukuoka saga nagasaki kumamoto oita miyazaki kagoshima okinawa night cat exotic large-dog visit'.split(' '));

function pagesFromArgs() {
  if (args.includes('--changed')) {
    let base = 'origin/main';
    try { execSync('git rev-parse --verify origin/main', {cwd: ROOT, stdio: 'ignore'}); } catch (e) { base = 'main'; }
    const files = execSync(`git diff --name-only ${base} -- '*.html'; git diff --name-only -- '*.html'; git ls-files --others --exclude-standard -- '*.html'`, {cwd: ROOT}).toString().split('\n');
    const set = new Set(files.filter(f => f.endsWith('index.html') && !/^(tools|tests|booking|docs|sns|go|hub)\//.test(f)).map(f => '/' + f.replace(/index\.html$/, '')));
    // トップを変えたら地域ページも全部変わるので、代表だけ
    let list = [...set];
    const area = list.filter(p => /^\/(area|tokyo|kanagawa|chiba|saitama)\//.test(p));
    if (area.length > 4) list = list.filter(p => !area.includes(p)).concat(area.slice(0, 3));
    return pickSpread(list);
  }
  if (args.includes('--sample')) {
    const list = ['/', '/tokyo/', '/guide/'];
    for (const c of FAC) {
      if (!fs.existsSync(path.join(ROOT, c))) continue;
      list.push(`/${c}/`);
      const subs = fs.readdirSync(path.join(ROOT, c)).filter(d => fs.existsSync(path.join(ROOT, c, d, 'index.html')));
      for (const s of ['tokyo', 'osaka'].filter(x => subs.includes(x))) list.push(`/${c}/${s}/`);
      const deep = subs.map(s => path.join(c, s)).flatMap(d => fs.readdirSync(path.join(ROOT, d)).filter(x => fs.existsSync(path.join(ROOT, d, x, 'index.html'))).map(x => `/${d}/${x}/`));
      if (deep.length) list.push(deep[Math.floor(deep.length / 2)]);
    }
    const guides = fs.readdirSync(path.join(ROOT, 'guide')).filter(d => fs.existsSync(path.join(ROOT, 'guide', d, 'index.html')));
    for (let i = 0; i < 4; i++) list.push(`/guide/${guides[Math.floor(Math.random() * guides.length)]}/`);
    return list;
  }
  return args.filter((a, i) => a.startsWith('/') && !['--out', '--base', '--max'].includes(args[i - 1]));
}
function pickSpread(list) { // 同じ型のページばかりにならないよう、フォルダごとに散らして MAX まで
  if (list.length <= MAX) return list;
  const by = {};
  for (const p of list) (by[p.split('/').slice(0, 3).join('/')] ||= []).push(p);
  const out = [], keys = Object.keys(by);
  for (let i = 0; out.length < MAX && keys.some(k => by[k].length > i); i++) for (const k of keys) if (by[k][i] && out.length < MAX) out.push(by[k][i]);
  return out;
}

function serve() {
  const types = {'.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.png': 'image/png', '.svg': 'image/svg+xml'};
  return new Promise(res => {
    const s = http.createServer((q, r) => {
      let f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0].split('#')[0]));
      if (f.endsWith('/')) f += 'index.html';
      fs.readFile(f, (e, b) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, {'content-type': types[path.extname(f)] || 'application/octet-stream'}); r.end(b); });
    }).listen(0, () => res(s));
  });
}

async function measure(page) {
  return page.evaluate(({W, H}) => {
    const out = [];
    const vis = el => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !el.closest('details:not([open])'); };
    const top = el => el.getBoundingClientRect().top + scrollY;
    // 横のはみ出し
    if (document.documentElement.scrollWidth > W + 2) {
      const wide = [...document.querySelectorAll('main *')].filter(e => vis(e) && e.getBoundingClientRect().right > W + 2 && !e.closest('[style*="overflow"],.fr,.fr-s,.hf-c,.tbl,pre,.catbar,.cat-bar') && getComputedStyle(e.parentElement).overflowX === 'visible').slice(0, 1);
      out.push(['overflow', `ページの幅 ${document.documentElement.scrollWidth}px` + (wide[0] ? `（${wide[0].tagName.toLowerCase()}.${(wide[0].className || '').toString().split(' ')[0]}）` : '')]);
    }
    const main = document.querySelector('main') || document.body;
    // さがす欄・結果が先か（施設の分野だけ。呼ぶ側で判断）
    const first = [...main.querySelectorAll('select,input:not([type=hidden]),.ux-find,.hf,.hn-find,.ux-c,.emg-item,.fr,.yd-pref,.yd-pick')].filter(vis)[0];
    const firstTop = first ? Math.round(top(first)) : null;
    // ボタン・リンクの箱が高すぎる
    for (const box of main.querySelectorAll('div,p,ul,nav,section')) {
      if (!vis(box)) continue;
      const kids = [...box.children].filter(k => /^(A|BUTTON|LI)$/.test(k.tagName) && vis(k));
      if (kids.length >= 8 && box.getBoundingClientRect().height > H && kids.every(k => k.textContent.trim().length <= 12)) {
        out.push(['tallgrid', `${kids.length}個のボタン・リンクで ${Math.round(box.getBoundingClientRect().height)}px（「${kids[0].textContent.trim()}」…）`]); break;
      }
    }
    // 横にならんだカードの高さ
    const seen = new Set();
    for (const c of main.querySelectorAll('[class*="card"],.ux-c,.fr-c,.emg-item,.tile,[class*="-tile"]')) {
      const p = c.parentElement; if (!p || seen.has(p) || !vis(c)) continue; seen.add(p);
      const row = [...p.children].filter(k => k.className === c.className && vis(k));
      if (row.length < 2) continue;
      const rows = {};
      for (const k of row) (rows[Math.round(k.getBoundingClientRect().top)] ||= []).push(k.getBoundingClientRect().height);
      // 横にスワイプする列は、同じ高さに並ぶものどうしでくらべる
      const lines = Object.values(rows).filter(r => r.length >= 2);
      const bad = lines.find(r => Math.max(...r) - Math.min(...r) >= 8);
      if (bad) { out.push(['uneven', `.${c.className.toString().split(' ')[0]} の高さ ${Math.round(Math.min(...bad))}〜${Math.round(Math.max(...bad))}px`]); break; }
    }
    // 文字だけの画面（2画面目より下で、1画面ぶんの中に図・アイコン・表・ボタンがひとつもない）
    const visuals = [...main.querySelectorAll('img,svg,picture,table,button,select,input,canvas,iframe,[class*="card"],[class*="tile"],[class*="icon"],[class*="vz"],[class*="chip"],[class*="tag"],.ux-c,.emg-item,summary,i,.i,figure')].filter(vis).map(e => [top(e), top(e) + e.getBoundingClientRect().height]);
    const emoji = /[\u{1F300}-\u{1FAFF}☀-➿]/u;
    for (const e of main.querySelectorAll('li,h2,h3,b,span')) if (vis(e) && emoji.test(e.textContent.slice(0, 4))) visuals.push([top(e), top(e) + 20]);
    const mainTop = top(main), mainEnd = mainTop + main.getBoundingClientRect().height;
    for (let y = mainTop + H; y + H <= mainEnd; y += H / 2) {
      if (!visuals.some(([a, b]) => b > y && a < y + H)) {
        const txt = [...main.querySelectorAll('p')].filter(p => vis(p) && top(p) >= y && top(p) < y + H).map(p => p.textContent.trim()).join('').length;
        if (txt > 400) { out.push(['textonly', `${Math.round(y / H * 10) / 10}画面目あたりに文字だけの画面（${txt}字）`]); break; }
      }
    }
    // 小さすぎる字
    for (const e of main.querySelectorAll('p,li,td,dd,span,a')) {
      if (!vis(e) || !e.childNodes.length || ![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 6)) continue;
      const fs = parseFloat(getComputedStyle(e).fontSize);
      if (fs < 11) { out.push(['tiny', `${fs}px「${e.textContent.trim().slice(0, 20)}」`]); break; }
    }
    return {out, firstTop, height: document.documentElement.scrollHeight};
  }, {W, H});
}

(async () => {
  const list = pagesFromArgs();
  if (!list.length) { console.log('見るページがありません（--changed で変わったページがない）'); return; }
  fs.mkdirSync(OUT, {recursive: true});
  const srv = opt('--base') ? null : await serve();
  const base = opt('--base', srv ? `http://127.0.0.1:${srv.address().port}` : '');
  const b = await chromium.launch();
  const ctx = await b.newContext({viewport: {width: W, height: H}, deviceScaleFactor: 1, locale: 'ja-JP', isMobile: true, hasTouch: true});
  // 外への通信（解析・地図・口コミ）は止める。何も送らない
  await ctx.route('**/*', r => r.request().url().startsWith(base) ? r.continue() : r.abort());
  const rep = ['# スマホの画面の点検', '', `${new Date().toISOString().slice(0, 16)}・${list.length}ページ・幅${W}px`, ''];
  let n = 0;
  for (const p of list) {
    const page = await ctx.newPage();
    try {
      await page.goto(base + p, {waitUntil: 'load', timeout: 30000});
      await page.waitForTimeout(400);
      const m = await measure(page);
      const cat = p.split('/')[1];
      const seg = p.split('/').filter(Boolean);
      if (FAC.includes(cat) && (seg.length === 1 || seg.length === 2 && PREF.has(seg[1])) && (m.firstTop === null || m.firstTop > H * 1.3))
        m.out.unshift(['first', m.firstTop === null ? 'さがす欄も結果のカードもない' : `さがす欄・結果が ${Math.round(m.firstTop / H * 10) / 10} 画面目から`]);
      // ペットタクシーのページ（トップ・地域）は、フォームの最初の入力欄（お迎えの都道府県）が最初の1画面に入る（Nori 2026-11-16「フォームに行くまでスクロールが長すぎる」）
      const prefTop = await page.evaluate(() => { const e = document.getElementById('pref'); return e && document.getElementById('petForm') ? Math.round(e.getBoundingClientRect().top + scrollY) : null; });
      // フォームの上で同じことを2回言わない（「無料」は1か所・準備中のお知らせなし。Nori 2026-11-16「端折れる部分はなくして」）
      const above = await page.evaluate(() => { const f = document.getElementById('petForm'), mn = document.querySelector('main'); if (!f || !mn) return null; const w = document.createTreeWalker(mn, NodeFilter.SHOW_TEXT); let t = '', n; while ((n = w.nextNode())) { if (f.compareDocumentPosition(n) & Node.DOCUMENT_POSITION_PRECEDING && !f.contains(n) && n.parentElement && n.parentElement.getClientRects().length) t += n.textContent; } return t; }); // 見えている文字だけ
      if (above !== null) { const nf = (above.match(/無料/g) || []).length; if (nf > 1 || /準備中/.test(above)) m.out.unshift(['dup', `フォームの上に「無料」が${nf}回${/準備中/.test(above) ? '・準備中のお知らせ' : ''}（1回に）`]); }
      if (prefTop !== null && prefTop + 40 > H) m.out.unshift(['form', `フォームの最初の入力欄が ${Math.round(prefTop / H * 10) / 10} 画面目から（1画面目に入れる）`]);
      const shot = path.join(OUT, (p.replace(/^\/|\/$/g, '').replace(/\//g, '_') || 'top') + '.png');
      await page.screenshot({path: shot, clip: {x: 0, y: 0, width: W, height: Math.min(H * 2, m.height)}});
      rep.push(`## ${p} ${m.out.length ? '— ' + m.out.length + '件' : '— OK'}`, `写真: ${shot}`, ...m.out.map(([k, v]) => `- [${k}] ${v}`), '');
      n += m.out.length;
      if (m.out.length) console.log(p, m.out.map(x => x.join(' ')).join(' / '));
    } catch (e) { rep.push(`## ${p} — 開けない`, String(e).slice(0, 200), ''); console.log(p, '開けない', String(e).slice(0, 120)); n++; }
    await page.close();
  }
  rep.splice(3, 0, `見つかったこと：${n}件`, '');
  fs.writeFileSync(path.join(OUT, 'report.md'), rep.join('\n'));
  console.log(`${list.length}ページ・見つかったこと ${n}件 → ${path.join(OUT, 'report.md')}`);
  await b.close(); if (srv) srv.close();
  process.exitCode = args.includes('--strict') && n ? 1 : 0;
})();
