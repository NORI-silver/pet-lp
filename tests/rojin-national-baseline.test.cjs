// 老犬ホームの全国のページ（/rojin-home/）：2026-11-28 時点で見えていた施設は、あとの取り込みで減らさない（増えるのは自由）。
// 理由：全国のページの件数を決める見積もり（tools/faccard.py の _too_big）が、料金の項目を足しただけで県ごと3件から2件に落ち、20件がこのページから消えたため。
// 一致を求めるのではなく「入っていること」だけを見るので、あとの取り込みで施設が増えても、基準の見直しは要らない。
const fs=require('node:fs'),assert=require('node:assert/strict');
const BASE=["R001", "R003", "R004", "R005", "R006", "R007", "R009", "R010", "R011", "R013", "R014", "R016", "R018", "R019", "R021", "R022", "R023", "R024", "R025", "R026", "R027", "R028", "R029", "R030", "R031", "R032", "R033", "R034", "R035", "R036", "R037", "R040", "R043", "R045", "R046", "R047", "R049", "R050", "R051", "R055", "R057", "R058", "R059", "R063", "R064", "R065", "R066", "R067", "R068", "R069", "R070", "R072", "R075", "R076", "R079", "R080", "R081", "R082", "R083", "R084", "R085", "R086", "R087", "R088", "R091", "R092", "R094", "R096", "R097", "R098", "R099", "R100", "R101", "R108", "R111", "R113", "R120", "R131", "R132", "R133", "R134", "R137", "R138", "R140", "R141", "R145", "R147", "R149", "R150", "R151", "R153", "R158", "R160", "R165", "R166", "Rc8b985c", "Rt33ff67b"];
const h=fs.readFileSync('rojin-home/index.html','utf8');
const have=new Set([...h.matchAll(/data-fid="([A-Za-z0-9]+)"/g)].map(m=>m[1]));
const missing=BASE.filter(i=>!have.has(i));
assert.deepEqual(missing,[],'全国のページから消えた施設：'+missing.join(','));
console.log('rojin national baseline preserved:',BASE.length,'of',have.size);
