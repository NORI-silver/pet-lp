// 葬儀・火葬の全国のページ（/sougi/）：2026-11-28 時点で見えていた施設は、あとの取り込みで減らさない（増えるのは自由）。
// 理由：88件を足したとき、県ごとに2件だけ出す枠から、すでに出ていた3件が押し出されたため（tools/faccard.py の _SOUGI_NATIONAL_KEEP）。
const fs=require('node:fs'),assert=require('node:assert/strict');
const BASE=["S0b9ae7", "S0d9e61", "S117e63", "S11d757", "S1b8c6d", "S1f8f5f", "S2a5368", "S2de21d", "S3f334a", "S41c14a", "S5222d0", "S546706", "S57a0db", "S611d1d", "S6940fc", "S6f6b42", "S70883b", "S7755d5", "S7c8f28", "S822672", "S8cafa0", "S932ef2", "S971a58", "Sa4611d", "Sb4f878", "Sbcaec6", "Scce51a", "Sd0edb1", "Sda5bf8", "Sf259f2", "Sf73179", "Sfb3759", "Sfff2f8"];
const h=fs.readFileSync('sougi/index.html','utf8');
const have=new Set([...h.matchAll(/data-fid="([^"]+)"/g)].map(m=>m[1]));
const missing=BASE.filter(i=>!have.has(i));
assert.deepEqual(missing,[],'全国のページから消えた施設：'+missing.join(','));
console.log('sougi national baseline preserved:',BASE.length,'of',have.size);
