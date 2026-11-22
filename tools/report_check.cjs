#!/usr/bin/env node
// [G] Nori さん向けの資料・報告ページの点検（Nori 2026-11-22「体制図がまず見にくい。図にして。説明を要所に加えて。この指摘はずっとしてます」）。
// 使い方: node tools/report_check.cjs <ページ.html> [出力フォルダ]
// スマホの幅（390px、明るい・暗い）で写真を撮り、次を見る。NG があれば終了コード1。写真は必ず自分の目で見てから出す。
//   first   最初の1画面に図（svg・img・canvas・table）がない
//   wall    図・表・カードのない文字が続く（400字）
//   over    横にはみ出している
//   svgtext 図の中の文字が箱からはみ出している（text が同じ g の中の rect より広い）
const {chromium} = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const file = process.argv[2]; const out = process.argv[3] || '/tmp/report-check';
  if (!file) { console.log('使い方: node tools/report_check.cjs <ページ.html> [出力フォルダ]'); process.exit(2); }
  fs.mkdirSync(out, {recursive: true});
  let html = fs.readFileSync(file, 'utf8');
  if (!/<!doctype/i.test(html)) html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-size:14px}</style></head><body>' + html + '</body></html>';
  const tmp = path.join(out, 'page.html'); fs.writeFileSync(tmp, html);
  const b = await chromium.launch(); const ng = [];
  for (const scheme of ['light', 'dark']) {
    const p = await b.newPage({viewport: {width: 390, height: 844}, colorScheme: scheme});
    await p.goto('file://' + path.resolve(tmp)); await p.waitForTimeout(600);
    const shot = path.join(out, `shot-${scheme}.png`); await p.screenshot({path: shot, fullPage: true});
    if (scheme === 'dark') { console.log('写真:', shot); continue; }
    const r = await p.evaluate(() => {
      const res = {};
      const vis = [...document.querySelectorAll('svg,img,canvas,table')].filter(e => e.getBoundingClientRect().width > 120);
      res.first = !vis.some(e => e.getBoundingClientRect().top < innerHeight);
      res.over = document.documentElement.scrollWidth > innerWidth + 1;
      let run = 0, max = 0;
      const walk = n => { for (const c of n.childNodes) {
        if (c.nodeType === 1 && /^(SVG|IMG|CANVAS|TABLE|UL|OL)$/i.test(c.tagName)) { run = 0; continue; }
        if (c.nodeType === 1 && /\b(c|card|box)\b/.test(c.className || '')) { run = 0; continue; }
        if (c.nodeType === 3) { run += c.textContent.trim().length; max = Math.max(max, run); }
        else if (c.nodeType === 1 && !/^(SCRIPT|STYLE)$/i.test(c.tagName)) walk(c);
      } };
      walk(document.body); res.wall = max;
      const bad = [];
      for (const t of document.querySelectorAll('svg text')) {
        const tb = t.getBoundingClientRect();
        const boxes = [...t.ownerSVGElement.querySelectorAll('rect')].map(x => x.getBoundingClientRect())
          .filter(rb => tb.top >= rb.top - 1 && tb.bottom <= rb.bottom + 1 && tb.left < rb.right && tb.right > rb.left);
        if (boxes.length && !boxes.some(rb => tb.left >= rb.left - 1 && tb.right <= rb.right + 1)) bad.push(t.textContent.trim());
      }
      res.svgtext = bad; return res;
    });
    if (r.first) ng.push('first: 最初の1画面に図がない');
    if (r.over) ng.push('over: 横にはみ出している');
    if (r.wall > 400) ng.push(`wall: 図・表のない文字が ${r.wall}字 続く`);
    for (const t of r.svgtext) ng.push(`svgtext: 図の文字が箱からはみ出している「${t}」`);
    console.log('写真:', shot);
  }
  await b.close();
  for (const n of ng) console.log('NG:', n);
  console.log(`NG ${ng.length}件（写真を自分の目で見てから出す）`);
  process.exit(ng.length ? 1 : 0);
})();
