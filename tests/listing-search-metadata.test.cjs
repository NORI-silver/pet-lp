const test=require('node:test'),fs=require('node:fs'),a=require('node:assert/strict');
test('primary non-taxi listings explain the service rather than using prices and counts as metadata',()=>{
 const cases={'pet-hotel':'夜間スタッフ','pet-sitter':'自宅に来て食事や散歩','dog-trainer':'吠えや散歩','trimming':'トリミングカー',
 'sougi':'立ち会い・返骨','dogrun':'犬の体重制限','hospital':'動物の種類や往診','hinan':'ペットを連れて避難',
 'jichitai/maigo':'地域の届け先','jichitai/tebanasu':'自治体の相談窓口'};
 for(const [dir,term] of Object.entries(cases)){
   const h=fs.readFileSync(dir+'/index.html','utf8'), t=h.match(/<title>([^<]+)<\/title>/)[1], d=h.match(/<meta name="description" content="([^"]+)"/)[1];
   a.doesNotMatch(t,/タクシー|\d+(?:か所|件|店|院|施設)の一覧/,dir);
   a.ok(d.includes(term),dir);a.ok(h.includes('<meta property="og:title" content="'+t+'">'),dir);
   a.ok(h.includes('<meta property="og:description" content="'+d+'">'),dir);
 }
 const tr=fs.readFileSync('trimming/chiba/index.html','utf8'), desc=tr.match(/<meta name="description" content="([^"]+)"/)[1];
 a.match(desc,/^千葉県で/);a.doesNotMatch(desc,/最安|2,000円|北海道/);
 const sitter=fs.readFileSync('pet-sitter/chiba/index.html','utf8');
 a.match(sitter,/<title>千葉県のペットシッター｜留守番・老犬の訪問介護/);
});
