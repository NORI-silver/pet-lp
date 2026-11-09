// XとInstagramの画像（アイコン・ヘッダー・投稿10枚）と posts.md を作る。
// 使い方：リポジトリのいちばん上で `node sns/gen.cjs`。何も投稿しない。
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const OUT = path.join(__dirname, 'img');
const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'posts.json'), 'utf8'));
fs.mkdirSync(OUT, { recursive: true });

const C = { orange: '#ff6a1a', cream: '#fff6ef', ink: '#1c1a18', soft: '#ffe2cc', sub: '#6b625c' };
const FONT = `<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@500;800&display=swap" rel="stylesheet">`;
const BASE = `*{box-sizing:border-box;margin:0;padding:0}body{font-family:"M PLUS Rounded 1c",sans-serif;color:${C.ink}}`;
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const b64 = f => 'data:image/jpeg;base64,' + fs.readFileSync(path.join(ROOT, f)).toString('base64');
const illust = fs.readFileSync(path.join(__dirname, 'illust.svg'), 'utf8').replace(/<metadata>[\s\S]*?<\/metadata>/, '');
const paw = `<svg viewBox="0 0 32 32" width="56" height="56"><rect width="32" height="32" rx="8" fill="${C.orange}"/><g fill="#fff" transform="translate(4 4)"><circle cx="6" cy="9" r="2.2"/><circle cx="10" cy="5.5" r="2.2"/><circle cx="14" cy="5.5" r="2.2"/><circle cx="18" cy="9" r="2.2"/><path d="M12 11c-3 0-6 3.6-6 6.2 0 1.8 1.5 2.8 3 2.8 1.2 0 2-.6 3-.6s1.8.6 3 .6c1.5 0 3-1 3-2.8C18 14.6 15 11 12 11z"/></g></svg>`;

// 肉球マーク（サイトの favicon と同じ形）。size=一辺px、op=濃さ（ヘッダー用に薄くもできる）
const pawBig = (size, r) => `<svg viewBox="0 0 32 32" width="${size}" height="${size}"><rect width="32" height="32" rx="${32 * r}" fill="${C.orange}"/><g fill="#fff" transform="translate(4 4)"><circle cx="6" cy="9" r="2.2"/><circle cx="10" cy="5.5" r="2.2"/><circle cx="14" cy="5.5" r="2.2"/><circle cx="18" cy="9" r="2.2"/><path d="M12 11c-3 0-6 3.6-6 6.2 0 1.8 1.5 2.8 3 2.8 1.2 0 2-.6 3-.6s1.8.6 3 .6c1.5 0 3-1 3-2.8C18 14.6 15 11 12 11z"/></g></svg>`;

function postHtml(p) {
  return `<!doctype html><html><head><meta charset="utf-8">${FONT}<style>${BASE}
  body{width:1080px;height:1350px;background:${C.cream};display:flex;flex-direction:column}
  .ph{height:620px;background:url(${b64(p.photo)}) center/cover}
  .bd{flex:1;padding:48px 72px 0;display:flex;flex-direction:column}
  .tag{align-self:flex-start;background:${C.orange};color:#fff;font-weight:800;font-size:30px;padding:8px 26px;border-radius:40px}
  h1{font-weight:800;font-size:62px;line-height:1.3;margin:26px 0 24px;white-space:pre-line}
  ul{list-style:none}li{font-weight:500;font-size:34px;line-height:1.45;padding-left:46px;position:relative;margin-bottom:12px}
  li:before{content:"";position:absolute;left:4px;top:15px;width:22px;height:22px;border-radius:50%;background:${C.orange}}
  .note{font-size:24px;color:${C.sub};margin-top:6px}
  .ft{margin-top:auto;display:flex;align-items:center;gap:16px;padding:22px 0 34px;border-top:3px solid ${C.soft};font-weight:800;font-size:32px}
  </style></head><body><div class="ph"></div><div class="bd">
  <div class="tag">${esc(p.tag)}</div><h1>${esc(p.head)}</h1>
  <ul>${p.points.map(t => `<li>${esc(t)}</li>`).join('')}</ul>
  ${p.note ? `<div class="note">※${esc(p.note)}</div>` : ''}
  <div class="ft">${paw}ペットのくらし窓口</div></div></body></html>`;
}

const headerHtml = `<!doctype html><html><head><meta charset="utf-8">${FONT}<style>${BASE}
  body{width:1500px;height:500px;background:${C.cream};position:relative;overflow:hidden}
  .t{position:absolute;left:90px;top:110px}
  .t b{display:block;font-weight:800;font-size:68px}
  .t span{display:block;font-weight:500;font-size:32px;color:${C.sub};margin-top:14px}
  .il{position:absolute;right:110px;top:85px;width:330px}
  </style></head><body>
  <div class="t"><b>ペットのくらし窓口</b><span>犬・猫と暮らす家族のための、ペットサービスさがし</span></div>
  <div class="il">${pawBig(330, 0.18)}</div></body></html>`;

(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  for (const p of data.posts.filter(p => p.points)) { // カード画像は最初の10本だけ（いまは使っていない）
    await pg.setContent(postHtml(p), { waitUntil: 'networkidle' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.screenshot({ path: path.join(OUT, `post${String(p.no).padStart(2, '0')}.jpg`), type: 'jpeg', quality: 88 });
  }
  // X のヘッダー（1500×500）。左下はアイコンと重なるので文字は上半分に置く。
  await pg.setViewportSize({ width: 1500, height: 500 });
  await pg.setContent(headerHtml, { waitUntil: 'networkidle' });
  await pg.evaluate(() => document.fonts.ready);
  await pg.screenshot({ path: path.join(OUT, 'x-header.png') });
  // アイコン（X・Instagram共通、1024×1024）。丸く切り抜かれても肉球が真ん中に来るように四角いまま全面オレンジ。
  await pg.setViewportSize({ width: 1024, height: 1024 });
  await pg.setContent(`<!doctype html><html><body style="margin:0">${pawBig(1024, 0)}</body></html>`);
  await pg.screenshot({ path: path.join(OUT, 'avatar.png') });
  await b.close();

  // posts.md（Nori さんがコピーして貼るための一覧）
  const tags = data.ig_tags_common;
  let md = `# 最初の10投稿（コピーして使う）\n\n` +
    `このファイルは \`node sns/gen.cjs\` で \`posts.json\` から作っています。直すときは \`posts.json\` を直してください。\n` +
    `どの投稿にもリンクは入れていません（Nori 2026-11-02）。画像は \`sns/img/postNN.jpg\`（X・Instagram共通、1080×1350）。\n\n`;
  for (const p of data.posts.filter(p => p.points)) {
    const n = String(p.no).padStart(2, '0');
    const xBody = p.x.split('\n').filter(l => !l.startsWith('#')).join('\n');
    const ig = [xBody, p.ig_add, 'くわしくは、プロフィールのサイトの「ガイド」にまとめています。', '', [...new Set([...tags, ...(p.ig_extra || [])])].join(' ')]
      .filter(v => v !== undefined).join('\n\n').replace(/\n\n\n\n/g, '\n\n');
    md += `## ${p.no}. ${p.tag}（もとの記事：/guide/${p.guide}/）\n\n画像：\`sns/img/post${n}.jpg\`\n\n### X\n\n\`\`\`\n${p.x}\n\`\`\`\n\n### Instagram\n\n\`\`\`\n${ig}\n\`\`\`\n\n`;
  }
  fs.writeFileSync(path.join(__dirname, 'posts.md'), md);
  console.log('ok');
})();
