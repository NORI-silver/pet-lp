/* 迷子・犬の登録・飼えなくなったとき（/jichitai/maigo/ ほか）の動き。tools/gen_maigo.py がこのファイルを /jichitai/jc.js に写す。
   市区町村を入れると、その町の窓口・警察・役所・近くの情報で手順のボタンを置きかえる。入れた文字・チラシの中身はどこにも送らない。 */
(function(){
var box=document.querySelector('[data-jc]');if(!box)return;
var K=box.getAttribute('data-jc'),Q=document.getElementById('jcQ'),S=document.getElementById('jcS'),H=document.getElementById('jcH'),R=document.getElementById('jcR'),D=null,wait=[];
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(e){return null}}
function ev(n,p){try{gtag('event',n,p||{})}catch(e){}}
function load(cb){if(D)return cb();wait.push(cb);if(wait.length>1)return;fetch('/jichitai/data.json').then(function(r){return r.json()}).then(function(j){D=j;var w=wait;wait=[];w.forEach(function(f){f()})})}
function a(u,t,l){if(!u)return'';var ext=/^https?:/.test(u);return'<a'+(l?' class="l"':'')+' href="'+esc(u)+'"'+(ext?' target="_blank" rel="noopener"':'')+'>'+esc(t)+(ext?' ↗':'')+'</a>'}
function slot(n,html){var el=document.querySelector('[data-slot="'+n+'"]');if(el&&html!=null)el.innerHTML=html}
function txt(n,s){var el=document.querySelector('[data-slot="'+n+'-t"]');if(el&&s)el.innerHTML=s}
function kata(s){return s.replace(/[ァ-ヶ]/g,function(c){return String.fromCharCode(c.charCodeAt(0)-96)})}
function find(v){v=v.replace(/[\s　]/g,'');if(!v)return[];var h=[],kv=kata(v);
 D.m.forEach(function(m){var full=m[0]+m[1];if(m[1]===v||full===v||m[1].indexOf(v)===0||full.indexOf(v)===0||(v.length>=2&&m[2]&&m[2].indexOf(kv)===0))h.push(m)});
 var ex=h.filter(function(m){return m[1]===v||m[0]+m[1]===v});return ex.length===1?ex:h}
function sug(){var v=Q.value;if(!v.trim()){S.innerHTML='';return}load(function(){var h=find(v);
 if(h.length===1&&(h[0][1]===v.replace(/[\s　]/g,'')||h[0][0]+h[0][1]===v.replace(/[\s　]/g,'')))return pick(h[0]);
 S.innerHTML=h.length?h.slice(0,8).map(function(m,i){return'<button type="button" data-i="'+i+'">'+esc(m[0]+m[1])+'</button>'}).join('')+(h.length>8?'<span class="jc-src">続けて入れるとしぼれます</span>':''):'<span class="jc-src">見つかりません。市区町村の名前で入れてください（例：佐倉市）</span>';
 S.querySelectorAll('button').forEach(function(b){b.onclick=function(){pick(h[+b.getAttribute('data-i')])}})})}
function card(c,sub){if(!c)return'';return'<div class="jc-card cs" style="margin:8px 0 0;width:100%"><b class="ux-c-n">'+esc(c[0])+'</b><p class="ux-c-m">'+esc(sub)+'</p><div class="ux-c-a">'+a(c[1],'公式ページ')+(c[2]?a(c[2],'保護情報',1):a('https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(c[0]),'地図を見る',1))+'</div></div>'}
function pick(m){S.innerHTML='';Q.value=m[1];ls('jcMuni',m[0]+'|'+m[1]);var P=D.p[m[0]]||{},c=D.c[m[4]],city=m[1],pf=m[0];
 H.hidden=false;
 if(K==='maigo'){H.innerHTML='<b>'+esc(pf+city)+'</b>で今日やることです。終わったらチェックを入れてください。';
  slot('center',card(c,c&&c[3]===city?city+'の窓口':pf+'の窓口（'+city+'はこの窓口の受け持ち）'));
  slot('police',a(P.pol,pf==='東京都'?'警視庁に遺失届を出す':'警察に遺失届をオンラインで出す'));
  slot('city',a(m[3],city+'のページを開く'));txt('city',city+'のページで「迷子」「犬の登録」と、道路で亡くなった動物の引き取り（清掃の担当）の窓口を見ます。つらい確認ですが、首輪の色などを伝えておくと、もしものときに連絡をもらえることがあります。');
  slot('vet',a(m[5]||P.h,city+'の近くの動物病院')+a(P.n,'夜間・救急の病院',1));
  slot('hogo',(c&&c[2]?a(c[2],c[0].replace(/（.*）/,'')+'の保護情報'):'')+a('https://www.env.go.jp/nature/dobutsu/aigo/shuyo/link.html','となりの市・県の保護情報',1));
  pro(pf);ev('jichitai_find',{pref:pf,page:K})}
 else if(K==='touroku'){H.innerHTML='<b>'+esc(pf+city)+'</b>の犬の登録は、'+esc(city)+'の窓口です。';
  slot('city',a(m[3],city+'のページで「犬の登録」を見る'));ev('jichitai_find',{pref:pf,page:K})}
 else{H.innerHTML='<b>'+esc(pf+city)+'</b>の近くの相談先です。';
  slot('tmp',(P.o?a(P.o,pf+'のペットホテル'):a('/pet-hotel/','ペットホテル'))+(P.t?a(P.t,pf+'のペットシッター',1):a('/pet-sitter/','ペットシッター',1)));
  slot('rojin',(P.r?a(P.r,pf+'の老犬ホーム'):a('/rojin-home/','老犬ホーム・老猫ホーム'))+a('/guide/rojin-home-cost/','費用のしくみ',1));
  slot('joto',P.j?a(P.j,pf+'の譲渡の窓口と団体'):a('/joto/','譲渡の窓口と団体'));
  slot('center',card(c,c&&c[3]===city?city+'の窓口':pf+'の窓口（'+city+'はこの窓口の受け持ち）'));ev('jichitai_find',{pref:pf,page:K})}}
function covers(d,pf){var ar=d.areas||[];return ar.indexOf('全国')>=0||ar.indexOf(pf)>=0||(d.near||[]).indexOf(pf)>=0}
function local(d,pf){return(d.near||[]).indexOf(pf)>=0||((d.areas||[]).indexOf(pf)>=0&&(d.areas||[])[0]!=='全国')}
/* ペット探偵：その県に来てくれる会社だけを、地元・出張費なしの会社を先にして1つの表に並べる（表は最初の4件と「のこり」に分かれているので、全部の行を集める） */
function pro(pf){var el=document.getElementById('jcPro');if(!el||!D.d||!D.d.length)return;var tb=el.querySelector('tbody');if(!tb)return;
 var rows=pro.rows||(pro.rows=[].slice.call(el.querySelectorAll('tbody tr'))),more=el.querySelector('details.more'),near=[],far=[],off=[];
 D.d.forEach(function(d,i){var r=rows[i];if(!r)return;(covers(d,pf)?(local(d,pf)?near:far):off).push(r)});
 near.concat(far,off).forEach(function(r){tb.appendChild(r)});near.concat(far).forEach(function(r){r.style.display=''});off.forEach(function(r){r.style.display='none'});
 if(more)more.hidden=true;
 var n=el.querySelector('.jc-pn');if(!n){n=document.createElement('p');n.className='jc-pn jc-src';el.insertBefore(n,el.firstChild)}
 n.innerHTML='<b>'+esc(pf)+'に来てくれる会社は'+(near.length+far.length)+'社</b>です。'+(near.length?esc(pf)+'が地元・出張費なしの'+near.length+'社を先に、そのあとに全国に出張する会社を出しています。':'全国に出張する会社です（交通費は会社ごとに別）。')+(off.length?' <button type="button" class="jc-all" style="border:0;background:none;color:#c2410c;text-decoration:underline;padding:0">ほかの地域の会社も見る</button>':'');
 var b=n.querySelector('.jc-all');if(b)b.onclick=function(){off.forEach(function(r){r.style.display=''});b.remove()}}
/* 犬か猫か */
var an=box.querySelectorAll('[data-an]');function setAn(v){an.forEach(function(b){b.setAttribute('aria-pressed',b.getAttribute('data-an')===v)});if(R){R.classList.toggle('jc-dog',v==='dog');R.classList.toggle('jc-cat',v==='cat')}ls('jcAn',v)}
an.forEach(function(b){b.onclick=function(){setAn(b.getAttribute('data-an'));ev('jichitai_animal',{a:b.getAttribute('data-an')})}});if(an.length)setAn(ls('jcAn')==='cat'?'cat':'dog');
/* チェック（この端末にだけ覚える） */
var ck={};try{ck=JSON.parse(ls('jcCk:'+K)||'{}')}catch(e){}
document.querySelectorAll('.jc-ck>li[data-ck]').forEach(function(li){var k=li.getAttribute('data-ck')+(li.getAttribute('data-a')||''),i=li.querySelector('input');if(!i)return;i.checked=!!ck[k];li.classList.toggle('done',i.checked);
 i.onchange=function(){ck[k]=i.checked?1:0;li.classList.toggle('done',i.checked);ls('jcCk:'+K,JSON.stringify(ck))}});
Q.addEventListener('input',sug);Q.addEventListener('focus',function(){load(function(){})},{once:true});
var last=ls('jcMuni');if(last){var p=last.split('|');load(function(){var h=D.m.filter(function(m){return m[0]===p[0]&&m[1]===p[1]});if(h.length)pick(h[0])})}
/* 登録の期限 */
var dd=document.getElementById('jcD'),bd=document.getElementById('jcB'),due=document.getElementById('jcDue');
function fmt(d){return(d.getMonth()+1)+'月'+d.getDate()+'日'}
function calc(){if(!dd||!dd.value){due.innerHTML='';return}var g=new Date(dd.value+'T00:00'),st=g;if(bd&&bd.value){var b=new Date(bd.value+'T00:00'),b90=new Date(b);b90.setDate(b90.getDate()+90);if(b90>st)st=b90}
 var lim=new Date(st);lim.setDate(lim.getDate()+30);var y=st.getMonth()<3?st.getFullYear():st.getFullYear()+1,inSeason=st.getMonth()>=3&&st.getMonth()<=5;
 due.innerHTML='登録と予防注射は <b>'+lim.getFullYear()+'年'+fmt(lim)+'</b> までに。'+(inSeason?'':'そのあとの予防注射は、毎年4月1日〜6月30日に1回（次は'+y+'年）。')+(bd&&bd.value&&st!==g?'<br>生後90日をすぎた日（'+fmt(st)+'）から30日以内で計算しています。':'')}
if(dd){dd.onchange=calc;bd.onchange=calc}
/* 迷子チラシ（この端末の中だけで作り、印刷する） */
var go=document.getElementById('ffGo');if(go)go.onclick=function(){var v=function(id){return(document.getElementById(id).value||'').trim()},pr=document.getElementById('jcPrint'),_m=document.body.appendChild(pr),fs=[].slice.call(document.getElementById('ffPh').files||[]).slice(0,2),cat=R&&R.classList.contains('jc-cat');
 var rows=[['特徴',v('ffKd')],['大きさなど',v('ffSz')],['首輪・特徴',v('ffFt')],['いなくなった日時・場所',v('ffWh')]].filter(function(r){return r[1]});
 var html='<h1>さがしています</h1><div class="ph"></div><p class="nm">迷子の'+(cat?'猫':'犬')+(v('ffNm')?'「'+esc(v('ffNm'))+'」':'')+'</p><table>'+rows.map(function(r){return'<tr><th>'+esc(r[0])+'</th><td>'+esc(r[1])+'</td></tr>'}).join('')+'</table>'+(v('ffAk')?'<p class="ask">'+esc(v('ffAk'))+'</p>':'')+(v('ffCt')?'<p class="ct">連絡先：'+esc(v('ffCt'))+'</p>':'');
 pr.innerHTML=html;var ph=pr.querySelector('.ph'),n=fs.length;ev('jichitai_flyer',{a:cat?'cat':'dog'});
 if(!n)return window.print();fs.forEach(function(f){var r=new FileReader();r.onload=function(){var im=new Image();im.src=r.result;ph.appendChild(im);if(--n===0)setTimeout(function(){window.print()},300)};r.readAsDataURL(f)})};
})();
