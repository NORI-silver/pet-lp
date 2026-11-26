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
function find(v){v=v.replace(/[\s　]/g,'');var PS=document.getElementById('jcP'),pv=PS?PS.value:'';if(!v)return pv?D.m.filter(function(m){return m[0]===pv}):[];var h=[],kv=kata(v);
 D.m.forEach(function(m){if(pv&&m[0]!==pv)return;var full=m[0]+m[1];if(m[1]===v||full===v||m[1].indexOf(v)===0||full.indexOf(v)===0||(v.length>=2&&m[2]&&m[2].indexOf(kv)===0))h.push(m)});
 var ex=h.filter(function(m){return m[1]===v||m[0]+m[1]===v});return ex.length===1?ex:h}
function sug(){var v=Q.value;var PS=document.getElementById('jcP');if(!v.trim()&&!(PS&&PS.value)){S.innerHTML='';return}load(function(){if(Q.value!==v)return;var h=find(v);if(!v.trim()){S.innerHTML=h.slice(0,12).map(function(m,i){return'<button type="button" data-i="'+i+'">'+esc(m[1])+'</button>'}).join('')+(h.length>12?'<span class="jc-src">続けて市区町村を入れるとしぼれます</span>':'');S.querySelectorAll('button').forEach(function(b){b.onclick=function(){pick(h[+b.getAttribute('data-i')])}});return}
 var WD=!(PS&&PS.value)&&/区$/.test(v.replace(/[\s　]/g,''));if(!WD&&h.length===1&&(h[0][1]===v.replace(/[\s　]/g,'')||h[0][0]+h[0][1]===v.replace(/[\s　]/g,'')))return pick(h[0]);
 S.innerHTML=(h.length?h.slice(0,8).map(function(m,i){return'<button type="button" data-i="'+i+'">'+esc(m[0]+m[1])+'</button>'}).join('')+(h.length>8?'<span class="jc-src">続けて入れるとしぼれます</span>':''):'<span class="jc-src">見つかりません。市区町村の名前で入れてください（例：佐倉市）</span>')+(WD?'<span class="jc-src">同じ名前の区が、ほかの市にもあります。政令指定都市（大阪市・横浜市など）の区は、市の名前（例：大阪市）で選んでください。</span>':'');
 S.querySelectorAll('button').forEach(function(b){b.onclick=function(){pick(h[+b.getAttribute('data-i')])}})})}
function official(links,label){return links?'<details class="jc-cite"><summary>'+esc(label)+'</summary><div>'+links+'</div></details>':''}
function route(name,what,links){return '<li><h3>'+esc(name)+'</h3><p>'+esc(what)+'</p>'+official(links,'公式の受付・連絡方法')+'</li>'}
function card(c,sub){if(!c)return'';return'<div class="jc-card cs" style="margin:8px 0 0;width:100%"><b class="ux-c-n">'+esc(c[0])+'</b><p class="ux-c-m">'+esc(sub)+'</p><div class="ux-c-a">'+a(c[1],'公式ページ')+(c[2]?a(c[2],'保護情報',1):a('https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(c[0]),'地図を見る',1))+'</div></div>'}
function pick(m){S.innerHTML='';Q.value=m[1];var PS1=document.getElementById('jcP');if(PS1)PS1.value=m[0];ls('jcMuni',m[0]+'|'+m[1]);var P=D.p[m[0]]||{},c=D.c[m[4]],city=m[1],pf=m[0];
 H.hidden=false;
 if(K==='maigo'){H.innerHTML='<b>'+esc(pf+city)+'</b>を選択中';
  var loc=document.getElementById('jcLocal'), L=(D.l||{})[pf+city]||{};
  var center=L.center||c, cityName=L.city?L.city[0]:city+'の環境・動物担当', cityUrl=L.city?L.city[1]:m[3], protectedUrl=center&&center[2];
  if(loc){
   var rows=(center?route(center[0],'迷子の情報を伝え、似た犬・猫が収容されていないか確認します。',a(center[1],'担当窓口の連絡方法')):'')
    +route(L.police?L.police[0]:(pf==='東京都'?'警視庁・最寄りの警察署や交番':'最寄りの警察署・交番'),'迷子を遺失届で届けます。急ぐときは直接、警察署・交番に相談してください。',a(P.pol,'遺失届のオンライン受付')+(L.police?a(L.police[1],'警察の案内'):''))
    +route(cityName,'保護・目撃情報や、近くの担当窓口を確認します。',a(cityUrl,L.city?'市の担当窓口':'市区町村の案内・担当課を探す'));
   loc.hidden=false;loc.innerHTML='<ol class="jc-route">'+rows+'</ol>'+(L.hogo?'<details class="jc-cite"><summary>保護情報の見方とお迎えの費用</summary><p>'+esc(L.hogo)+'</p><p>'+esc(L.return)+'</p>'+a(protectedUrl,'最新の保護情報・千葉県の出典')+'</details>':'');
  }
  txt('intro','<b>'+esc(pf+city)+'</b>でいなくなった場合の届け先です。特徴・首輪・写真を用意し、今日のうちに連絡してください。');
  slot('police', '<a href="#report">選んだ地域の警察・受付方法を見る</a>');
  slot('hogo',official((protectedUrl?a(protectedUrl,'担当窓口の最新の保護情報'):'')+a('https://www.env.go.jp/nature/dobutsu/aigo/shuyo/link.html','周辺自治体の公式保護情報'),'最新の保護情報・出典'));
  if(L.hogo)txt('hogo',esc(L.hogo)+'<br>'+esc(L.return));
  slot('vet',a(m[5]||P.h,city+'の近くの動物病院')+a(P.n,'夜間・救急の病院',1));
  reportText();pro(pf);ev('jichitai_find',{pref:pf,page:K})}
 else if(K==='touroku'){H.innerHTML='<b>'+esc(pf+city)+'</b>の犬の登録は、'+esc(city)+'の窓口です。';
  slot('city',a(m[3],city+'のページで「犬の登録」を見る'));ev('jichitai_find',{pref:pf,page:K})}
 else{H.innerHTML='<b>'+esc(pf+city)+'</b>の近くの相談先です。';
  slot('tmp',(P.o?a(P.o,pf+'のペットホテル'):a('/pet-hotel/','ペットホテル'))+(P.t?a(P.t,pf+'のペットシッター',1):a('/pet-sitter/','ペットシッター',1)));
  slot('rojin',(P.r?a(P.r,pf+'の老犬ホーム'):a('/rojin-home/','老犬ホーム・老猫ホーム'))+a('/guide/rojin-home-cost/','費用のしくみ',1));
  slot('joto',P.j?a(P.j,pf+'の譲渡の窓口と団体'):'');
  slot('center',card(c,c&&c[3]===city?city+'の窓口':pf+'の窓口（'+city+'はこの窓口の受け持ち）'));ev('jichitai_find',{pref:pf,page:K})}}
function covers(d,pf){var ar=d.areas||[];return ar.indexOf('全国')>=0||ar.indexOf(pf)>=0||(d.near||[]).indexOf(pf)>=0}
function local(d,pf){return(d.near||[]).indexOf(pf)>=0||!!(d.u&&d.u[pf])||((d.areas||[]).indexOf(pf)>=0&&(d.areas||[])[0]!=='全国')}
/* ペット探偵：その県に来てくれる会社だけを、地元・出張費なしの会社を先にして1つの表に並べる（表は最初の4件と「のこり」に分かれているので、全部の行を集める） */
var detF={};function detApply(){var el=document.getElementById('jcPro');if(!el)return;var act=Object.keys(detF).filter(function(k){return detF[k]});[].forEach.call(el.querySelectorAll('tbody tr'),function(r){if(r.style.display==='none'&&!r._detH)return;var f=' '+(r.getAttribute('data-det')||'')+' ';var ok=act.every(function(k){if(k==='un')return true;if(k==='dg'||k==='ct'||k==='ex')return f.indexOf(' '+k+' ')>=0||(detF.un&&f.indexOf(' un ')>=0);if(k==='n')return !pro.pf||(r.getAttribute('data-near')||'').split('|').indexOf(pro.pf)>=0;return f.indexOf(' '+k+' ')>=0});if(!ok){r._detH=1;r.style.display='none'}else if(r._detH){r._detH=0;r.style.display=''}})}
function pro(pf){pro.pf=pf;var el=document.getElementById('jcPro');if(!el||!D.d||!D.d.length)return;var tb=el.querySelector('tbody');if(!tb)return;
 var rows=pro.rows||(pro.rows=[].slice.call(el.querySelectorAll('tbody tr'))),more=el.querySelector('details.more'),near=[],far=[],off=[];
 D.d.forEach(function(d,i){var r=rows[i];if(!r)return;var l=r.querySelector('[data-det-site]');if(l){if(!l.dataset.base)l.dataset.base=l.getAttribute('href');l.href=(d.u&&d.u[pf])||l.dataset.base}r.setAttribute('data-near',(d.near||[]).join('|'));(covers(d,pf)?(local(d,pf)?near:far):off).push(r)});
 near.concat(far,off).forEach(function(r){tb.appendChild(r)});near.concat(far).forEach(function(r){r._detH=0;r.style.display=''});off.forEach(function(r){r._detH=0;r.style.display='none'});
 if(more)more.hidden=true;
 var n=el.querySelector('.jc-pn');if(!n){n=document.createElement('p');n.className='jc-pn jc-src';el.insertBefore(n,el.firstChild)}
 n.innerHTML='<b>'+esc(pf)+'に来てくれる会社は'+(near.length+far.length)+'社</b>です。'+(near.length?esc(pf)+'で受けている'+near.length+'社（地元・出張費なし・県ごとの窓口がある会社）を先に、そのあとに全国に出張する会社を出しています。':'全国に出張する会社です（交通費は会社ごとに別）。')+(off.length?' <button type="button" class="jc-all" style="border:0;background:none;color:#c2410c;text-decoration:underline;padding:0">ほかの地域の会社も見る</button>':'');
 var b=n.querySelector('.jc-all');if(b)b.onclick=function(){off.forEach(function(r){r.style.display=''});detApply();b.remove()}
 detApply()}
var copy=document.getElementById('jcReportCopy'), report=document.getElementById('jcReportText'), status=document.getElementById('jcReportStatus');
function reportText(){if(!report)return;var dog=R&&R.classList.contains('jc-dog'), selected=H&&!H.hidden?Q.value:'';report.value='種別：'+(dog?'犬':'猫')+'\nいなくなった日時：\nいなくなった場所：'+(selected||'')+'\n特徴（毛色・模様・大きさ・性別）：\n首輪・迷子札：\nマイクロチップの有無：\n連絡先（窓口にのみ伝える）：';if(status)status.textContent=''}
if(copy&&report&&status)copy.addEventListener('click',function(){
 var fallback=function(){report.focus();report.select();status.textContent='記入例を選択しました。手動でコピーできます。'};
 if(!navigator.clipboard||!navigator.clipboard.writeText){fallback();return}
 navigator.clipboard.writeText(report.value).then(function(){status.textContent='コピーしました。'},fallback);
});
/* 探偵の絞り込み（全国対応・猫を探せる・料金が分かる） */
[].forEach.call(document.querySelectorAll('[data-detf]'),function(b){b.onclick=function(){var k=b.getAttribute('data-detf');detF[k]=!detF[k];b.setAttribute('aria-pressed',detF[k]?'true':'false');if(pro.pf)pro(pro.pf);else{var el=document.getElementById('jcPro');if(el)[].forEach.call(el.querySelectorAll('tbody tr'),function(r){r.style.display='';r._detH=0});detApply()}}});
/* 犬か猫か */
var an=box.querySelectorAll('[data-an]');function setAn(v){an.forEach(function(b){b.setAttribute('aria-pressed',b.getAttribute('data-an')===v)});if(R){R.classList.toggle('jc-dog',v==='dog');R.classList.toggle('jc-cat',v==='cat')}ls('jcAn',v);reportText()}
an.forEach(function(b){b.onclick=function(){setAn(b.getAttribute('data-an'));ev('jichitai_animal',{a:b.getAttribute('data-an')})}});if(an.length)setAn(ls('jcAn')==='cat'?'cat':'dog');
/* チェック（この端末にだけ覚える） */
var ck={};try{ck=JSON.parse(ls('jcCk:'+K)||'{}')}catch(e){}
document.querySelectorAll('.jc-ck>li[data-ck]').forEach(function(li){var k=li.getAttribute('data-ck')+(li.getAttribute('data-a')||''),i=li.querySelector('input');if(!i)return;i.checked=!!ck[k];li.classList.toggle('done',i.checked);
 i.onchange=function(){ck[k]=i.checked?1:0;li.classList.toggle('done',i.checked);ls('jcCk:'+K,JSON.stringify(ck))}});
var DEF=null;function snap(){DEF={};[].forEach.call(document.querySelectorAll('[data-slot]'),function(e){DEF[e.getAttribute('data-slot')]=e.innerHTML})}
function rs(){if(!DEF)return;[].forEach.call(document.querySelectorAll('[data-slot]'),function(e){var k=e.getAttribute('data-slot');if(k in DEF)e.innerHTML=DEF[k]})}
if(K==='maigo')snap();
var PS0=document.getElementById('jcP');if(PS0)PS0.addEventListener('change',function(){Q.value='';H.hidden=true;rs();var loc=document.getElementById('jcLocal');if(loc)loc.hidden=true;reportText();sug()});
Q.addEventListener('input',function(){var loc=document.getElementById('jcLocal');if(loc){loc.hidden=true;H.hidden=true}rs();reportText();sug()});
if(K==='maigo'){var flyer=document.getElementById('jcFly');function openFlyer(){if(location.hash==='#jcFly'&&flyer)flyer.open=true}window.addEventListener('hashchange',openFlyer);openFlyer()}Q.addEventListener('focus',function(){load(function(){})},{once:true});
var last=ls('jcMuni');if(last){var p=last.split('|');load(function(){var h=D.m.filter(function(m){return m[0]===p[0]&&m[1]===p[1]});if(h.length&&!Q.value.trim())pick(h[0])})}
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
