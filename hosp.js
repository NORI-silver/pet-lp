// 生成ファイル（tools/hosp_find.py）。手で直さない
(function(){
var PREF_KEY = "petInfoPref";
function prefGet(){ try { return localStorage.getItem(PREF_KEY); } catch (x) { return null; } }
function prefPut(v){ try { localStorage.setItem(PREF_KEY, v); } catch (x) {} }
// 都道府県でしぼりこめるページへのリンクに、いまの県を付ける
function prefLinks(v){
  document.querySelectorAll("a[href]").forEach(function(a){
    var h = a.getAttribute("href");
    if (!/^\/(hospital|dogrun|jichitai|sougi|rojin-home|dog-trainer|pet-sitter|trimming|pet-hotel|emergency)\//.test(h)) return;
    h = h.replace(/#pref=.*$/, "");
    if (h.indexOf("#") >= 0) return;
    a.setAttribute("href", v ? h + "#pref=" + encodeURIComponent(v) : h);
  });
}
function prefKeep(sel, apply){
  var m = location.hash.match(/^#pref=(.+)$/), v = null;
  if (m) { try { v = decodeURIComponent(m[1]); } catch (x) {} }
  if (v === null) v = prefGet();
  if (v !== null && [].some.call(sel.options, function(o){ return o.value === v; })) {
    sel.value = v; apply(); prefPut(v);
  }
  prefLinks(sel.value);
  sel.addEventListener("change", function(){
    apply(); prefPut(sel.value); prefLinks(sel.value);
    try { history.replaceState(null, "", location.pathname + location.search + (sel.value ? "#pref=" + encodeURIComponent(sel.value) : "")); } catch (x) {}
  });
}

function prefGuess(sel, apply){
  if (sel.value) return;
  var NAMES = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"], LL = [[43.06,141.35],[40.82,140.74],[39.70,141.15],[38.27,140.87],[39.72,140.10],[38.24,140.36],[37.75,140.47],[36.34,140.45],[36.57,139.88],[36.39,139.06],[35.86,139.65],[35.61,140.12],[35.69,139.69],[35.45,139.64],[37.90,139.02],[36.70,137.21],[36.59,136.63],[36.07,136.22],[35.66,138.57],[36.65,138.18],[35.39,136.72],[34.98,138.38],[35.18,136.91],[34.73,136.51],[35.00,135.87],[35.02,135.76],[34.69,135.52],[34.69,135.18],[34.69,135.83],[34.23,135.17],[35.50,134.24],[35.47,133.05],[34.66,133.93],[34.40,132.46],[34.19,131.47],[34.07,134.56],[34.34,134.04],[33.84,132.77],[33.56,133.53],[33.61,130.42],[33.25,130.30],[32.74,129.87],[32.79,130.74],[33.24,131.61],[31.91,131.42],[31.56,130.56],[26.21,127.68]];
  function at(lat, lng){ var best = -1, bd = Infinity; LL.forEach(function(p, i){ var dy = lat - p[0], dx = (lng - p[1]) * Math.cos((lat + p[0]) * Math.PI / 360), d = dx * dx + dy * dy; if (d < bd) { bd = d; best = i; } }); return best >= 0 && bd < 4 ? NAMES[best] : ""; }
  function use(v, how){
    if (!v || sel.value || ![].some.call(sel.options, function(o){ return o.value === v; })) return;
    sel.value = v; apply(); prefLinks(v);
    var g = document.createElement("p"); g.className = "pref-guess"; g.style.cssText = "margin:6px 0 0;font-size:.82rem;color:#6b5a4e";
    g.textContent = how + "から、" + v + "を選んでいます。ちがうときは、上で選び直してください（「すべての都道府県」で全国）。";
    sel.parentNode.appendChild(g);
    sel.addEventListener("change", function(){ g.remove(); }, {once: true});
    try { window.gtag && gtag("event", "pref_guess", {pref: v, how: how.indexOf("いまいる") === 0 ? "geo" : "ip"}); } catch (x) {}
  }
  function byNet(){ fetch("https://get.geojs.io/v1/ip/geo.json").then(function(r){ return r.json(); }).then(function(d){ if (d && d.country_code === "JP") use(at(+d.latitude, +d.longitude), "通信の情報（おおよその地域）"); }).catch(function(){}); }
  if (navigator.permissions && navigator.geolocation) navigator.permissions.query({name: "geolocation"}).then(function(st){
    if (st.state !== "granted") return byNet();
    navigator.geolocation.getCurrentPosition(function(p){ use(at(p.coords.latitude, p.coords.longitude), "いまいる場所"); }, byNet, {maximumAge: 600000, timeout: 5000});
  }).catch(byNet); else byNet();
}
var box = document.getElementById("hf");
if (!box) return;
var sel = document.getElementById("hospPref"), csel = document.getElementById("hfCity"), q = document.getElementById("hfQ"),
dl = document.getElementById("hfCities"), det = document.getElementById("hfDet"), detN = document.getElementById("hfDetN"),
list = document.getElementById("hfList"), sum = document.getElementById("hfSum");
var SLUG = {"北海道": "hokkaido", "青森県": "aomori", "岩手県": "iwate", "宮城県": "miyagi", "秋田県": "akita", "山形県": "yamagata", "福島県": "fukushima", "茨城県": "ibaraki", "栃木県": "tochigi", "群馬県": "gunma", "新潟県": "niigata", "富山県": "toyama", "石川県": "ishikawa", "福井県": "fukui", "山梨県": "yamanashi", "長野県": "nagano", "岐阜県": "gifu", "静岡県": "shizuoka", "愛知県": "aichi", "三重県": "mie", "滋賀県": "shiga", "京都府": "kyoto", "大阪府": "osaka", "兵庫県": "hyogo", "奈良県": "nara", "和歌山県": "wakayama", "鳥取県": "tottori", "島根県": "shimane", "岡山県": "okayama", "広島県": "hiroshima", "山口県": "yamaguchi", "徳島県": "tokushima", "香川県": "kagawa", "愛媛県": "ehime", "高知県": "kochi", "福岡県": "fukuoka", "佐賀県": "saga", "長崎県": "nagasaki", "熊本県": "kumamoto", "大分県": "oita", "宮崎県": "miyazaki", "鹿児島県": "kagoshima", "沖縄県": "okinawa", "東京都": "tokyo", "神奈川県": "kanagawa", "埼玉県": "saitama", "千葉県": "chiba"}, LABEL = {"dog": "犬", "cat": "猫", "rabbit": "うさぎ", "hamster": "ハムスター・モルモット", "ferret": "フェレット", "bird": "鳥", "reptile": "爬虫類", "fish": "魚", "night": "夜間・救急", "h24": "24時間", "late": "19時以降も", "early": "朝9時前から", "sat": "土曜も", "sun": "日曜も", "hol": "祝日も", "nohol": "年中無休", "nolunch": "昼休みなし", "visit": "家に来てくれる（往診）", "catspec": "猫専門", "exospec": "うさぎ・鳥などの専門", "large": "大型犬の設備", "catroom": "猫用の待合室", "noresv": "予約なしでも", "resv": "予約できる", "park": "駐車場", "card": "カード払い", "hotel": "ペットホテル", "trim": "トリミング", "school": "しつけ教室・パピークラス", "ct": "CT・MRI"}, NEAR = {"北海道":["青森県","岩手県","秋田県"],"青森県":["岩手県","秋田県","北海道"],"岩手県":["秋田県","青森県","宮城県"],"宮城県":["山形県","福島県","岩手県"],"秋田県":["岩手県","青森県","山形県"],"山形県":["宮城県","福島県","新潟県"],"福島県":["山形県","宮城県","新潟県"],"茨城県":["栃木県","千葉県","埼玉県"],"栃木県":["茨城県","群馬県","埼玉県"],"群馬県":["栃木県","埼玉県","長野県"],"埼玉県":["東京都","神奈川県","千葉県"],"千葉県":["東京都","神奈川県","埼玉県"],"東京都":["埼玉県","神奈川県","千葉県"],"神奈川県":["東京都","埼玉県","千葉県"],"新潟県":["山形県","福島県","長野県"],"富山県":["石川県","長野県","福井県"],"石川県":["富山県","福井県","岐阜県"],"福井県":["石川県","岐阜県","富山県"],"山梨県":["静岡県","群馬県","神奈川県"],"長野県":["群馬県","富山県","山梨県"],"岐阜県":["愛知県","三重県","福井県"],"静岡県":["山梨県","神奈川県","愛知県"],"愛知県":["岐阜県","三重県","滋賀県"],"三重県":["愛知県","奈良県","滋賀県"],"滋賀県":["京都府","奈良県","大阪府"],"京都府":["滋賀県","奈良県","大阪府"],"大阪府":["奈良県","兵庫県","京都府"],"兵庫県":["大阪府","和歌山県","奈良県"],"奈良県":["大阪府","滋賀県","京都府"],"和歌山県":["兵庫県","徳島県","大阪府"],"鳥取県":["岡山県","島根県","兵庫県"],"島根県":["鳥取県","岡山県","広島県"],"岡山県":["香川県","徳島県","鳥取県"],"広島県":["愛媛県","山口県","島根県"],"山口県":["広島県","大分県","福岡県"],"徳島県":["香川県","和歌山県","岡山県"],"香川県":["岡山県","徳島県","高知県"],"愛媛県":["広島県","高知県","大分県"],"高知県":["愛媛県","香川県","徳島県"],"福岡県":["佐賀県","熊本県","長崎県"],"佐賀県":["福岡県","熊本県","長崎県"],"長崎県":["佐賀県","熊本県","福岡県"],"熊本県":["佐賀県","長崎県","大分県"],"大分県":["熊本県","山口県","福岡県"],"宮崎県":["鹿児島県","熊本県","大分県"],"鹿児島県":["宮崎県","熊本県","長崎県"],"沖縄県":["鹿児島県","宮崎県","長崎県"]}, REG = [["北海道・東北",[["北海道",8],["宮城県",3],["福島県",1]]],["関東",[["茨城県",5],["栃木県",5],["群馬県",3],["埼玉県",20],["千葉県",55],["東京都",382],["神奈川県",26]]],["中部",[["新潟県",2],["富山県",4],["石川県",1],["福井県",1],["山梨県",2],["長野県",5],["岐阜県",1],["静岡県",3],["愛知県",11]]],["近畿",[["三重県",1],["滋賀県",2],["京都府",8],["大阪府",266],["兵庫県",9],["奈良県",1],["和歌山県",1]]],["中国・四国",[["岡山県",3],["広島県",3],["山口県",1],["徳島県",1],["香川県",1],["愛媛県",1],["高知県",1]]],["九州・沖縄",[["福岡県",8],["佐賀県",1],["熊本県",4],["大分県",2],["宮崎県",1],["鹿児島県",3],["沖縄県",2]]]], av = null;
list.addEventListener("click", function(ev){ var b = ev.target.closest("button[data-pk]"); if (!b) return; sel.value = b.getAttribute("data-pk"); sel.dispatchEvent(new Event("change")); box.scrollIntoView({behavior: "smooth", block: "start"}); });
var NEED = {night: ["night"], sunhol: ["sun", "hol"], h24: ["h24"], visit: ["visit"], spec: ["spec"]};
var NEEDL = {night: "夜間・救急", sunhol: "日曜・祝日", h24: "24時間", visit: "往診", spec: "専門診療"};
var STRICT = {night: 1, visit: 1, catspec: 1, exospec: 1, large: 1, h24: 1, catroom: 1, ct: 1, spec: 1};
var FEAT = [["night", "夜間・救急"], ["h24", "24時間"], ["visit", "往診"], ["catspec", "猫専門"], ["exospec", "うさぎ・鳥などの専門"], ["large", "大型犬の設備"],
["sun", "日曜診療"], ["hol", "祝日診療"], ["late", "19時以降も"], ["park", "駐車場あり"], ["card", "カード可"]];
var on = {}, need = NEED[box.dataset.preset] ? box.dataset.preset : "", data = null, near = {}, shown = 30, firstCity = box.dataset.city || "";
if (box.dataset.preset && !NEED[box.dataset.preset]) on[box.dataset.preset] = 1;
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
function night(){ var h = new Date().getHours(); return h >= 19 || h < 8; }
function keys(){ var k = Object.keys(on); (NEED[need] || []).forEach(function(x){ if (k.indexOf(x) < 0) k.push(x); }); return k; }
function has(r, k){
if (k === "spec") return ["catspec", "exospec", "large"].some(function(x){ return r.y.indexOf(x) >= 0; }) || !!(r.d && r.d.length);
if (k.slice(0, 2) === "d:") return !!(r.d && r.d.indexOf(k.slice(2)) >= 0);
return r.y.indexOf(k) >= 0;
}
function judge(r, ks){
var g = 0, unk = [];
for (var i = 0; i < ks.length; i++) {
var k = ks[i];
if (has(r, k)) continue;
if (r.no.indexOf(k) >= 0 || STRICT[k]) return [2, []];
g = 1; unk.push(k);
}
return [g, unk];
}
function place(r){
var t = (q.value || "").trim(), c = csel.value;
var visitOk = function(x){ return r.y.indexOf("visit") >= 0 && (r.vz || (r.ar || "").indexOf(x) >= 0); };
if (c && r.c !== c && !visitOk(c)) return false;
if (t && !c) { var hay = [r.n, r.c, r.ad, r.st, r.ar].join(" "); if (hay.indexOf(t) < 0 && !visitOk(t)) return false; }
return true;
}
function paintBtns(){
box.querySelectorAll("button[data-v]").forEach(function(b){
var k = b.dataset.v;
b.setAttribute("aria-pressed", on[k] ? "true" : "false");
b.hidden = !!av && k !== "dog" && k !== "cat" && !on[k] && !av[k];
if (on[k] && b.classList.contains("hf-x")) b.parentNode.classList.add("open");
});
var sos = box.querySelector(".hf-sos"); if (sos) sos.hidden = need === "night";
box.querySelectorAll("button[data-need]").forEach(function(b){ b.setAttribute("aria-pressed", b.dataset.need === need ? "true" : "false"); });
box.querySelectorAll(".hf-det .hf-r").forEach(function(r){ r.hidden = ![].some.call(r.querySelectorAll("button[data-v]"), function(b){ return !b.hidden; }); });
var n = Object.keys(on).filter(function(k){ return !box.querySelector('.hf-det button[data-v="' + k + '"]') ? false : true; }).length;
detN.textContent = n ? n : "";
}
function picHtml(r){
if (!r.ph) return '<div class="cs-ph cs-ph0"' + (r.rv ? ' data-gph="' + esc(r.rv) + '"' : '') + ' aria-hidden="true"></div>';
var ps = r.ph[0], im = ps.map(function(p, i){ return '<img src="' + esc(p) + '" alt="' + esc(r.n) + 'の写真' + (i + 1) + '" width="520" height="347" loading="lazy" decoding="async">'; }).join("");
return '<div class="cs-ph"><div class="cs-ph-s">' + im + '</div>' + (ps.length > 1 ? '<span class="cs-ph-n" aria-hidden="true">📷 ' + ps.length + '</span>' : '') + (r.ph[1] ? '<small class="cs-ph-c">' + esc(r.ph[1]) + '</small>' : '') + '</div>';
}
function card(r, unk){
var b = [];
if (r.a) b.push('<span>' + esc(r.a.length > 22 ? r.a.slice(0, 22) + "…" : r.a) + '</span>');
FEAT.forEach(function(f){ if (f[0] === "late" && r.y.indexOf("night") >= 0) return; if (b.length < 6 && r.y.indexOf(f[0]) >= 0) b.push('<span>' + esc(f[1]) + '</span>'); });
keys().forEach(function(k){ if (k.slice(0, 2) === "d:" && has(r, k)) b.push('<span>' + esc(k.slice(2)) + '</span>'); });
unk.forEach(function(k){ b.push('<span class="u">' + esc(LABEL[k] || NEEDL[k] || k.slice(2)) + 'は不明</span>'); });
var top = r.tel ? '<a href="tel:' + esc(r.tel) + '" data-k="tel" data-ga>📞 電話する</a>' : '<a href="' + esc(r.u) + '" target="_blank" rel="noopener" data-k="site" data-ga>公式サイト ↗</a>';
var route = r.ad ? '<a class="l" href="https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(r.ad) + '" target="_blank" rel="noopener" data-k="route">📍 経路を見る</a>' : '';
var sub = [];
if (r.tel) sub.push('<a href="' + esc(r.u) + '" target="_blank" rel="noopener" data-k="site" data-ga>公式サイト</a>');
if (r.pg) sub.push('<a href="' + esc(r.pg) + '">診療内容の詳細</a>');
if (r.ad && r.y.indexOf("visit") < 0) sub.push('<a href="/?to=' + encodeURIComponent(r.ad) + '#form" data-k="taxi" data-ga>🚕 ペットタクシーの料金</a>');
return '<div class="hc">' + picHtml(r) + '<a class="hc-n" href="' + esc(r.pg || r.u) + '"' + (r.pg ? '' : ' target="_blank" rel="noopener"') + '>' + esc(r.n) + '</a>'
+ (b.length ? '<p class="hc-b">' + b.join("") + '</p>' : '')
+ ((r.ad || r.c) ? '<p class="hc-l"><i aria-hidden="true">📍</i><span>' + esc(r.ad || r.c) + '</span></p>' : '')
+ (r.h ? '<p class="hc-l"><i aria-hidden="true">🕘</i><span>診療時間：' + esc(r.h) + '</span></p>' : '')
+ (r.x ? '<p class="hc-l"><i aria-hidden="true">💤</i><span>休診：' + esc(r.x) + '</span></p>' : '')
+ (r.ar ? '<p class="hc-l"><i aria-hidden="true">🏠</i><span>来てくれる地域：' + esc(r.ar) + '</span></p>' : '')
+ '<div class="hc-a2">' + top + route + '</div>'
+ '<div class="hc-a fc-acts">' + (r.rv ? '<div class="emg-score" data-id="' + esc(r.rv) + '"></div>' : '') + sub.join("") + '</div></div>';
}
function match(arr, ks, usePlace){
var ok = [], unk = [];
arr.forEach(function(r){
if (usePlace && !place(r)) return;
var j = judge(r, ks); if (j[0] === 2) return;
(j[0] ? unk : ok).push([r, j[1]]);
});
return [ok, unk];
}
function draw(){
paintBtns();
var v = sel.value;
if (!v) {
sum.innerHTML = "都道府県を選ぶと、合う病院が並びます"; box.parentNode.classList.remove("hf-on");
list.innerHTML = '<div class="pk">' + REG.map(function(g){
return '<details class="pk-g"><summary>' + esc(g[0]) + '</summary><div class="pk-b">' + g[1].map(function(x){
return '<button type="button" data-pk="' + esc(x[0]) + '">' + esc(x[0]) + '<small>' + x[1] + '</small></button>'; }).join("") + '</div></details>';
}).join("") + '</div>';
return;
}
if (!data) { sum.textContent = "読み込んでいます…"; return; }
var ks = keys(), m = match(data.filter(function(r){ return !r.far; }), ks, true), ok = m[0], unk = m[1];
var nightFirst = night() && need !== "night";
if (nightFirst) ok.sort(function(a, b){ return (b[0].y.indexOf("night") >= 0) - (a[0].y.indexOf("night") >= 0); });
var t = (q.value || "").trim(), pl = v + (csel.value ? " " + csel.value : t ? "「" + t + "」" : "");
sum.innerHTML = esc(pl) + "で合う病院 " + ok.length + "院" + (unk.length ? "<small>ほかに、公式の情報に書いていないので要確認 " + unk.length + "院</small>" : "")
+ (nightFirst && ok.some(function(x){ return x[0].y.indexOf("night") >= 0; }) ? "<small>夜の時間なので、夜間・救急の病院を先に並べています</small>" : "");
var all = ok.concat(unk), html = ""; pic = 0;
all.slice(0, shown).forEach(function(x, i){
if (i === ok.length && unk.length) html += '<p class="hf-h">条件が公式の情報に書いていない病院（行く前に確かめてください）</p>';
html += card(x[0], x[1]);
});
if (all.length > shown) html += '<button type="button" class="hf-more">あと' + (all.length - shown) + '院を見る</button>';
if (!ok.length) {
var alt = [];
ks.forEach(function(k){
var rest = ks.filter(function(x){ return x !== k; }), n = match(data.filter(function(r){ return !r.far; }), rest, true)[0].length;
if (n) alt.push('<button type="button" data-drop="' + esc(k) + '">「' + esc(LABEL[k] || NEEDL[k] || (NEEDL[need] && NEED[need].indexOf(k) >= 0 ? NEEDL[need] : k.slice(2))) + '」を外す（' + n + '院）</button>');
});
if (csel.value || t) { var n2 = match(data.filter(function(r){ return !r.far; }), ks, false)[0].length; if (n2) alt.push('<button type="button" data-drop="place">' + esc(v) + 'の全体で見る（' + n2 + '院）</button>'); }
alt.push('<a href="/emergency/#pref=' + encodeURIComponent(v) + '">緊急のときの連絡先</a>');
html = '<div class="hf-none">' + esc(pl) + "で、この条件に合う病院はまだ見つかっていません。<div class=\"hf-alt\">" + alt.join("") + "</div></div>" + html;
}
if (ok.length < 3) {
var nb = [];
(NEAR[v] || []).forEach(function(p){ if (near[p]) match(near[p].filter(function(r){ return !r.far; }), ks, false)[0].forEach(function(x){ nb.push([x[0], p]); }); });
data.filter(function(r){ return r.far; }).forEach(function(r){ if (!judge(r, ks)[0]) nb.push([r, ""]); });
if (nb.length) html += '<p class="hf-h">近くの県の病院</p>' + nb.slice(0, 8).map(function(x){ return card(x[0], []); }).join("");
else if (!Object.keys(near).length) loadNear(v);
}
list.innerHTML = html;
box.parentNode.classList.add("hf-on");
if (window.petReviews) window.petReviews(list);
}
function loadNear(v){
if (loadNear.v === v) return; loadNear.v = v;
Promise.all((NEAR[v] || []).map(function(p){ return SLUG[p] ? fetch("/hospital/data/" + SLUG[p] + ".json").then(function(r){ return r.json(); }).then(function(j){ near[p] = j; }).catch(function(){}) : null; }))
.then(function(){ if (sel.value === v) draw(); });
}
function load(){
data = null; av = null; near = {}; loadNear.v = ""; draw();
var v = sel.value; if (!v || !SLUG[v]) { fillCities([]); return; }
fetch("/hospital/data/" + SLUG[v] + ".json").then(function(r){ return r.json(); }).then(function(j){
if (sel.value !== v) return;
data = j; av = {};  // その県のデータで1院以上に当てはまる条件
j.forEach(function(r){ if (!r.far) { r.y.forEach(function(k){ av[k] = 1; }); (r.d || []).forEach(function(d){ av["d:" + d] = 1; }); } });
fillCities(j); shown = 30; draw();
}).catch(function(){ data = []; draw(); });
}
function fillCities(j){
var cs = {}; j.forEach(function(r){ if (!r.far && r.c) cs[r.c] = (cs[r.c] || 0) + 1; });
var keep = firstCity || csel.value; firstCity = "";
var names = Object.keys(cs).sort();
csel.innerHTML = '<option value="">市区町村すべて</option>' + names.map(function(c){ return '<option value="' + esc(c) + '">' + esc(c) + "</option>"; }).join("");
dl.innerHTML = names.map(function(c){ return '<option value="' + esc(c) + '">'; }).join("");
if (keep && cs[keep]) { csel.value = keep; q.value = keep; } else if (!cs[q.value]) { csel.value = ""; }
}
function onQ(){ var t = (q.value || "").trim(); csel.value = [].some.call(csel.options, function(o){ return o.value && o.value === t; }) ? t : ""; shown = 30; draw(); }
q.addEventListener("input", onQ);
box.addEventListener("click", function(ev){
var b = ev.target.closest("button, a[data-sos]"); if (!b) return;
if (b.dataset.sos !== undefined) { ev.preventDefault(); need = "night"; draw(); list.scrollIntoView({behavior: "smooth"}); try { window.gtag && gtag("event", "hosp_sos", {pref: sel.value || "all"}); } catch (x) {} return; }
if (b.classList.contains("hf-mo")) { b.parentNode.classList.add("open"); return; }
if (b.id === "hfGo") { list.scrollIntoView({behavior: "smooth"}); return; }
if (b.id === "hfClear") { on = {}; need = ""; csel.value = ""; q.value = ""; shown = 30; draw(); return; }
if (b.dataset.need !== undefined) {
need = b.dataset.need;
if (need === "spec") det.open = true;  // 専門診療は、診療科目などを選べるように開く
shown = 30; draw();
try { window.gtag && gtag("event", "hosp_filter", {key: "need:" + (need || "none"), on: 1, pref: sel.value || "all"}); } catch (x) {}
return;
}
var k = b.dataset.v; if (!k) return;
if (on[k]) delete on[k]; else on[k] = 1;
shown = 30; draw();
try { window.gtag && gtag("event", "hosp_filter", {key: k, on: on[k] ? 1 : 0, pref: sel.value || "all"}); } catch (x) {}
});
list.addEventListener("click", function(ev){
var m = ev.target.closest(".hf-more"); if (m) { shown += 30; draw(); return; }
var d = ev.target.closest("button[data-drop]");
if (d) { var k = d.dataset.drop; if (k === "place") { csel.value = ""; q.value = ""; } else if (on[k]) delete on[k]; else need = ""; draw(); return; }
var a = ev.target.closest("a[data-k]"), c = a && a.closest(".hc"), nm = c && c.querySelector(".hc-n");
if (a) try { window.gtag && gtag("event", {taxi: "facility_taxi", tel: "tel_click", route: "hosp_route"}[a.dataset.k] || "official_site", {cat: "hospital", from: "hosp_find", company_name: nm ? nm.textContent.trim().slice(0, 80) : "", host: a.dataset.k === "site" ? a.hostname : "", pref: sel.value || "", transport_type: "beacon"}); } catch (x) {}
});
if (box.dataset.pref) { sel.value = box.dataset.pref; }
function apply(){ load(); }
if (box.dataset.pref) { prefLinks(sel.value); sel.addEventListener("change", function(){ prefPut(sel.value); prefLinks(sel.value); q.value = ""; apply(); }); apply(); }
else { prefKeep(sel, function(){ q.value = ""; apply(); }); if (!sel.value) { draw(); prefGuess(sel, apply); } }
})();
