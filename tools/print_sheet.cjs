// [B] 被リンク：tools/print_sheet.html から印刷用の PDF（/print/pet-bousai-sheet.pdf）と見本の画像を作る。何も送らない。
// 使い方：node tools/print_sheet.cjs
const { chromium } = require("playwright");
const path = require("path"), fs = require("fs");
(async () => {
  const root = path.resolve(__dirname, "..");
  fs.mkdirSync(path.join(root, "print"), { recursive: true });
  const b = await chromium.launch(), p = await b.newPage();
  await p.goto("file://" + path.join(__dirname, "print_sheet.html"), { waitUntil: "networkidle" }); await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: path.join(root, "print/pet-bousai-sheet.pdf"), format: "A4", printBackground: true, preferCSSPageSize: true });
  await p.setViewportSize({ width: 794, height: 1123 });
  await p.screenshot({ path: path.join(root, "print/pet-bousai-sheet.png"), fullPage: true });
  await b.close();
  console.log("ok print/pet-bousai-sheet.pdf");
})();
