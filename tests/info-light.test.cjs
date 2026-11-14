// 情報ページ（病院・ドッグラン・火葬・ホテルなど）の軽い型を守る（2026-11-08 戦略「施設ページは共通の重い部分を読み込まない軽い型に」）
// ・トップの重いJS（app.js）やフォームを読み込まない ・読み込むJSは決まった小さいものだけ ・ページ1枚の大きさに上限
// ・ペットタクシーへの案内（data-taxi-cta）を必ず持つ（tools/taxi_cta.py）
// 上限を超えたら、全国のページに全部の施設を並べず、県のページへのリンクにする（施設が増えたとき用）
const fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib'),assert=require('node:assert/strict');
const DIRS=['hospital','dogrun','jichitai','sougi','pet-hotel','pet-sitter','trimming','dog-trainer','rojin-home','inu-yado','inu-cafe','hinan','joto'];
const ALLOW=new Set(['/ga.js','/reviews.js','/facility.js']);
const MAX_GZ=60*1024, MAX_INLINE=24*1024, MAX_JS=24*1024;
let pages=0, big=[0,''];
function walk(d){ for(const f of fs.readdirSync(d,{withFileTypes:true})){ const p=path.join(d,f.name); if(f.isDirectory()) walk(p); else if(f.name==='index.html') check(p); } }
function check(p){
  const h=fs.readFileSync(p,'utf8');
  if(/http-equiv="refresh"/.test(h)) return;  // 県のページへ移した病院の案内（tools/thin_hosp.py）
  pages++;
  const gz=zlib.gzipSync(h,{level:9}).length; if(gz>big[0]) big=[gz,p];
  assert.ok(gz<=MAX_GZ, p+' is '+gz+' bytes gzipped (limit '+MAX_GZ+'): link to prefecture pages instead of listing everything');
  for(const m of h.matchAll(/<script[^>]*\ssrc="([^"]+)"/g)) assert.ok(ALLOW.has(m[1]), p+' loads '+m[1]+' (info pages must not load the top page scripts)');
  for(const m of h.matchAll(/<script(?![^>]*\ssrc)[^>]*>([\s\S]*?)<\/script>/g)) assert.ok(Buffer.byteLength(m[1])<=MAX_INLINE, p+' has an inline script of '+Buffer.byteLength(m[1])+' bytes');
  assert.ok(!/id="petForm"/.test(h), p+' contains the booking form');
  assert.ok(/data-taxi-cta="/.test(h) || p==='sougi/index.html', p+' has no pet taxi button (tools/taxi_cta.py)');
}
DIRS.forEach(d=>{ if(fs.existsSync(d)) walk(d); });
for(const f of ALLOW){ const n=fs.statSync('.'+f).size; assert.ok(n<=MAX_JS, f+' is '+n+' bytes (limit '+MAX_JS+')'); }
assert.ok(pages>100, 'only '+pages+' info pages found');
console.log('PASS: '+pages+' info pages stay light (largest '+big[1]+' '+Math.round(big[0]/1024)+'KB gz)');
