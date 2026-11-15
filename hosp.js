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
// 動物病院を自分の条件でさがす（tools/hosp_find.py が prefkeep の関数と一緒に /hosp.js に書き出す）
  var box = document.getElementById("hf");
  if (!box) return;
  var sel = document.getElementById("hospPref"), csel = document.getElementById("hfCity"), list = document.getElementById("hfList"), sum = document.getElementById("hfSum");
  var SLUG = {"北海道": "hokkaido", "青森県": "aomori", "岩手県": "iwate", "宮城県": "miyagi", "秋田県": "akita", "山形県": "yamagata", "福島県": "fukushima", "茨城県": "ibaraki", "栃木県": "tochigi", "群馬県": "gunma", "新潟県": "niigata", "富山県": "toyama", "石川県": "ishikawa", "福井県": "fukui", "山梨県": "yamanashi", "長野県": "nagano", "岐阜県": "gifu", "静岡県": "shizuoka", "愛知県": "aichi", "三重県": "mie", "滋賀県": "shiga", "京都府": "kyoto", "大阪府": "osaka", "兵庫県": "hyogo", "奈良県": "nara", "和歌山県": "wakayama", "鳥取県": "tottori", "島根県": "shimane", "岡山県": "okayama", "広島県": "hiroshima", "山口県": "yamaguchi", "徳島県": "tokushima", "香川県": "kagawa", "愛媛県": "ehime", "高知県": "kochi", "福岡県": "fukuoka", "佐賀県": "saga", "長崎県": "nagasaki", "熊本県": "kumamoto", "大分県": "oita", "宮崎県": "miyazaki", "鹿児島県": "kagoshima", "沖縄県": "okinawa", "東京都": "tokyo", "神奈川県": "kanagawa", "埼玉県": "saitama", "千葉県": "chiba"}, LABEL = {"dog": "犬", "cat": "猫", "rabbit": "うさぎ", "hamster": "ハムスター・モルモット", "ferret": "フェレット", "bird": "鳥", "reptile": "爬虫類", "fish": "魚", "night": "夜間・救急", "h24": "24時間", "late": "19時以降も", "early": "朝9時前から", "sat": "土曜も", "sun": "日曜も", "hol": "祝日も", "nohol": "年中無休", "nolunch": "昼休みなし", "visit": "家に来てくれる（往診）", "catspec": "猫専門", "exospec": "うさぎ・鳥などの専門", "large": "大型犬の設備", "catroom": "猫用の待合室", "noresv": "予約なしでも", "resv": "予約できる", "park": "駐車場", "card": "カード払い", "hotel": "ペットホテル", "trim": "トリミング", "school": "しつけ教室・パピークラス", "ct": "CT・MRI"}, AVAIL = {"北海道":{"cat":8,"dog":6,"late":5,"night":5,"card":2,"catroom":1,"catspec":1,"early":2,"resv":3,"sat":1,"d:歯科":1,"d:消化器科":1,"nolunch":2,"bird":1,"ct":1,"exospec":1,"ferret":1,"hamster":1,"rabbit":1,"reptile":1,"d:CT・MRI":1,"visit":1},"青森県":{"cat":1,"dog":1,"late":1,"night":1,"nolunch":1},"岩手県":{"cat":1,"dog":1,"late":1,"night":1,"nolunch":1},"宮城県":{"cat":3,"dog":2,"late":3,"night":2,"catroom":1,"catspec":1,"resv":1,"sat":1,"d:循環器科":1,"nolunch":1},"秋田県":{"cat":1,"dog":1,"late":1,"night":1,"nolunch":1},"山形県":{"cat":2,"dog":2,"late":2,"night":2,"nolunch":1},"福島県":{"cat":2,"dog":2,"late":2,"night":2,"nolunch":1},"茨城県":{"cat":5,"dog":4,"early":2,"h24":1,"late":3,"night":3,"hol":1,"nohol":1,"sat":1,"sun":1,"resv":2,"visit":2,"card":1},"栃木県":{"cat":5,"dog":5,"late":5,"night":4,"nolunch":2,"bird":2,"ferret":2,"hamster":2,"rabbit":2,"reptile":2,"resv":2,"exospec":1,"sat":2,"sun":2,"hol":1,"nohol":1},"群馬県":{"cat":3,"dog":2,"late":3,"night":3,"ct":1,"d:CT・MRI":1},"埼玉県":{"bird":3,"cat":20,"dog":19,"exospec":1,"ferret":3,"hamster":4,"hol":2,"rabbit":4,"resv":10,"sat":2,"sun":2,"large":1,"late":9,"night":6,"card":6,"visit":11,"catroom":1,"catspec":1,"nolunch":2,"reptile":1},"千葉県":{"cat":11,"dog":11,"late":8,"night":7,"visit":2,"bird":2,"exospec":2,"ferret":2,"hamster":2,"rabbit":2,"reptile":2,"resv":3,"nolunch":1,"hol":1,"park":1,"sat":1,"sun":1,"early":2,"h24":2},"東京都":{"cat":233,"dog":227,"late":53,"visit":18,"hol":64,"nohol":8,"resv":37,"sat":148,"sun":73,"bird":62,"early":16,"ferret":63,"hamster":98,"hotel":126,"park":117,"rabbit":108,"night":11,"nolunch":10,"card":11,"trim":93,"fish":2,"reptile":11,"ct":3,"large":2,"d:整形外科":1,"d:腫瘍科":1,"d:CT・MRI":3,"h24":9,"catroom":6,"catspec":6,"exospec":4,"d:皮膚科":3,"noresv":3,"d:循環器科":1,"d:健康診断":8,"d:眼科":2,"d:歯科":2,"d:耳鼻科":1,"d:消化器科":1,"d:呼吸器科":1,"d:行動診療":1},"神奈川県":{"cat":26,"dog":23,"visit":13,"d:東洋医学":1,"early":5,"ferret":6,"h24":4,"hamster":8,"late":13,"night":8,"rabbit":8,"bird":5,"exospec":2,"fish":1,"reptile":3,"nolunch":5,"resv":11,"card":7,"catroom":2,"catspec":2,"hol":4,"noresv":1,"sat":5,"nohol":3,"sun":3,"large":1,"park":1,"d:眼科":1},"新潟県":{"cat":2,"dog":1,"late":1,"night":1,"card":1,"catroom":1,"catspec":1,"park":1,"resv":1,"sat":1,"sun":1,"d:呼吸器科":1},"富山県":{"card":1,"cat":4,"dog":3,"resv":1,"visit":1,"late":3,"night":3},"石川県":{"cat":1,"dog":1,"late":1,"night":1},"福井県":{"cat":3,"dog":3,"early":1,"late":3,"night":3},"山梨県":{"cat":2,"dog":2,"late":2,"night":2},"長野県":{"cat":5,"dog":5,"late":3,"night":3,"resv":1,"visit":2,"card":1,"ferret":1,"hamster":1,"rabbit":1},"岐阜県":{"cat":1,"dog":1,"late":1,"night":1},"静岡県":{"cat":3,"dog":3,"early":1,"h24":1,"late":3,"night":3},"愛知県":{"cat":11,"dog":9,"visit":3,"catroom":1,"catspec":1,"late":6,"night":6,"hol":2,"nohol":2,"nolunch":2,"sat":3,"sun":3,"early":2,"h24":2,"large":1,"noresv":1,"d:消化器科":1,"resv":1},"三重県":{"cat":3,"dog":3,"resv":1,"visit":1,"late":2,"night":2,"nolunch":1},"滋賀県":{"cat":4,"dog":4,"late":3,"night":3,"bird":1,"card":1,"ferret":1,"hamster":1,"rabbit":1,"reptile":1,"resv":1,"visit":1,"ct":1,"hol":1,"nohol":1,"nolunch":1,"sat":1,"sun":1,"d:CT・MRI":1},"京都府":{"cat":8,"dog":7,"late":5,"night":3,"bird":3,"card":3,"ferret":3,"hamster":3,"rabbit":3,"reptile":3,"resv":5,"visit":1,"catroom":1,"catspec":1,"hol":3,"hotel":1,"sat":4,"exospec":2,"sun":3,"ct":1,"nohol":1,"d:CT・MRI":1,"large":1},"大阪府":{"bird":88,"cat":243,"dog":241,"early":4,"ferret":61,"hamster":118,"park":221,"rabbit":122,"hol":104,"late":156,"sat":196,"sun":113,"card":3,"h24":1,"resv":24,"visit":3,"reptile":5,"hotel":2,"trim":3,"catroom":3,"night":7,"catspec":2,"nolunch":8,"nohol":4,"large":1,"d:歯科":2,"d:消化器科":2,"ct":1,"d:CT・MRI":1,"school":2,"fish":1,"d:整形外科":1,"d:腫瘍科":1},"兵庫県":{"cat":9,"dog":9,"late":6,"night":5,"ct":1,"d:CT・MRI":1,"resv":4,"nolunch":2,"rabbit":1,"visit":2,"large":2,"d:消化器科":1,"hol":2,"nohol":1,"sat":2,"sun":2,"noresv":1},"奈良県":{"cat":1,"dog":1,"early":1,"h24":1,"late":1,"night":1,"nolunch":1},"和歌山県":{"cat":3,"dog":3,"visit":1,"late":2,"night":2,"nolunch":2},"鳥取県":{"cat":1,"dog":1,"late":1,"night":1,"nolunch":1},"島根県":{"cat":2,"dog":2,"late":2,"night":2,"nolunch":1},"岡山県":{"bird":1,"cat":3,"dog":3,"ferret":1,"hamster":1,"late":2,"night":2,"rabbit":1,"reptile":1,"nolunch":1,"large":1,"noresv":1,"park":1,"resv":1,"d:消化器科":1},"広島県":{"cat":3,"dog":2,"late":2,"night":2,"card":1,"catroom":1,"catspec":1,"hol":1,"resv":1,"sun":1},"山口県":{"cat":3,"dog":3,"ferret":1,"hamster":1,"late":3,"night":3,"rabbit":1},"徳島県":{"cat":3,"dog":3,"late":3,"night":3,"hol":1,"nohol":1,"nolunch":1,"sat":1,"sun":1},"香川県":{"cat":1,"dog":1,"late":1,"night":1},"愛媛県":{"cat":1,"dog":1,"late":1,"night":1},"高知県":{"cat":1,"dog":1,"late":1,"night":1},"福岡県":{"cat":8,"dog":7,"late":3,"night":2,"hol":1,"large":2,"sat":2,"sun":1,"bird":1,"card":2,"exospec":1,"ferret":1,"hamster":1,"rabbit":1,"reptile":1,"resv":2,"visit":2,"d:健康診断":1,"nolunch":1,"catroom":1,"catspec":1},"佐賀県":{"card":1,"cat":2,"dog":2,"late":2,"visit":1,"night":1,"nolunch":1},"長崎県":{"cat":1,"dog":1,"late":1,"night":1,"nolunch":1},"熊本県":{"card":1,"cat":4,"dog":4,"visit":1,"exospec":1,"park":1,"rabbit":2,"sat":1,"sun":1,"late":2,"night":2,"bird":1,"ferret":1,"hamster":1,"reptile":1},"大分県":{"cat":2,"dog":2,"visit":1,"bird":1,"ferret":1,"hamster":1,"late":1,"night":1,"nolunch":1,"rabbit":1,"reptile":1},"宮崎県":{"cat":2,"dog":1,"late":2,"night":2,"nolunch":1,"resv":1},"鹿児島県":{"cat":3,"dog":2,"early":1,"late":3,"resv":2,"visit":1,"night":2,"nolunch":1},"沖縄県":{"bird":1,"cat":2,"dog":2,"ferret":1,"hamster":1,"late":2,"night":2,"nolunch":2,"rabbit":1,"reptile":1}};
  var on = {}, data = null, shown = 30, firstCity = box.dataset.city || "";
  var AN = {dog: 1, cat: 1};
  // 病院の種類は「そういう病院か」なので、書いていなければ合わない（要確認には入れない）
  var STRICT = {night: 1, visit: 1, catspec: 1, exospec: 1, large: 1, h24: 1, catroom: 1, ct: 1};
  (box.dataset.preset || "").split(",").forEach(function(k){ if (k) on[k] = 1; });
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
  function openNow(r){
    if (!r.t) return false;
    var d = new Date(), m = d.getHours() * 60 + d.getMinutes(), wd = "日月火水木金土".charAt(d.getDay());
    if (r.x && (r.x.indexOf(wd) >= 0 || /不定/.test(r.x))) return false;  // 今日が休みの病院、休みが決まっていない病院は出さない
    return r.t.some(function(x){ return (m >= x[0] && m < x[1]) || (m + 1440 >= x[0] && m + 1440 < x[1]); });
  }
  function night(){ var h = new Date().getHours(); return h >= 19 || h < 8; }
  function paintBtns(){
    var av = AVAIL[sel.value] || null;
    box.querySelectorAll("button[data-v]").forEach(function(b){
      var k = b.dataset.v;
      b.setAttribute("aria-pressed", on[k] ? "true" : "false");
      // その県で1院も当てはまらないボタンは出さない（押しても0件になるだけなので）。犬・猫はいつも出す
      b.hidden = !!av && !AN[k] && !on[k] && !av[k];
    });
    box.querySelectorAll(".hf-c").forEach(function(c){
      var mo = c.querySelector(".hf-mo"); if (!mo) return;
      var rest = [].filter.call(c.querySelectorAll("button.hf-x"), function(b){ return !b.hidden; });
      mo.hidden = !rest.length || c.classList.contains("open");
      [].forEach.call(c.querySelectorAll("button.hf-x"), function(b){ if (on[b.dataset.v]) c.classList.add("open"); });
    });
    box.querySelectorAll(".hf-r").forEach(function(r){ var c = r.querySelector(".hf-c"); if (!c.querySelector("select")) r.hidden = ![].some.call(c.querySelectorAll("button[data-v]"), function(b){ return !b.hidden; }); });
  }
  function judge(r){
    // 0＝合う、1＝書いていない（要確認）、2＝合わない
    var g = 0, unk = [];
    for (var k in on) {
      if (r.y.indexOf(k) >= 0 || (k.slice(0, 2) === "d:" && r.d && r.d.indexOf(k.slice(2)) >= 0)) continue;
      if (r.no.indexOf(k) >= 0 || STRICT[k]) return [2, []];
      g = 1; unk.push(k);
    }
    return [g, unk];
  }
  function card(r, unk){
    var b = [];
    if (openNow(r)) b.push('<span class="now">いま受付時間内</span>');
    ["night", "visit", "catspec", "exospec", "large", "h24"].forEach(function(k){ if (r.y.indexOf(k) >= 0) b.push('<span>' + esc(LABEL[k]) + '</span>'); });
    for (var k in on) if (b.length < 8 && ["night", "visit", "catspec", "exospec", "large", "h24", "dog", "cat"].indexOf(k) < 0 && (r.y.indexOf(k) >= 0 || (r.d && r.d.indexOf(k.slice(2)) >= 0))) b.push('<span>' + esc(LABEL[k] || k.slice(2)) + '</span>');
    unk.forEach(function(k){ b.push('<span class="u">' + esc(LABEL[k] || k.slice(2)) + 'は不明</span>'); });
    var ex = (r.a || "").split(/[・、,\s（）()]+/).filter(function(x){ return x && !/^(犬|猫|イヌ|ネコ|犬猫)$/.test(x.trim()); }).join("・");
    var h = '<div class="hc"><a class="hc-n" href="' + esc(r.u) + '" target="_blank" rel="noopener">' + esc(r.n) + '</a>'
      + (b.length ? '<p class="hc-b">' + b.join("") + '</p>' : '')
      + ((r.ad || r.c) ? '<p class="hc-l"><i aria-hidden="true">📍</i><span>' + esc(r.ad || r.c) + '</span></p>' : '')
      + (r.h ? '<p class="hc-l"><i aria-hidden="true">🕘</i><span>' + esc(r.h) + '</span></p>' : '')
      + (r.x ? '<p class="hc-l"><i aria-hidden="true">💤</i><span>休み：' + esc(r.x) + '</span></p>' : '')
      + (r.ar ? '<p class="hc-l"><i aria-hidden="true">🏠</i><span>来てくれる地域：' + esc(r.ar) + '</span></p>' : '')
      + (ex ? '<p class="hc-l"><i aria-hidden="true">🐾</i><span>' + esc(ex) + '</span></p>' : '')
      + (r.d ? '<p class="hc-l"><i aria-hidden="true">🩺</i><span>' + esc(r.d.join("・")) + '</span></p>' : '')
      + '<div class="hc-a fc-acts">' + (r.rv ? '<div class="emg-score" data-id="' + esc(r.rv) + '"></div>' : '')
      + (r.ad && r.y.indexOf("visit") < 0 ? '<a href="/?to=' + encodeURIComponent(r.ad) + '#form" data-k="taxi">🚕 タクシー料金</a>' : '')
      + (r.pg ? '<a href="' + esc(r.pg) + '">くわしく</a>' : '')
      + '<a class="o" href="' + esc(r.u) + '" target="_blank" rel="noopener" data-k="site">公式サイト ↗</a></div></div>';
    return h;
  }
  function draw(){
    paintBtns();
    var v = sel.value;
    if (!v) { list.innerHTML = ""; sum.innerHTML = "都道府県を選ぶと、合う病院が下に並びます"; box.parentNode.classList.remove("hf-on"); return; }
    if (!data) { sum.textContent = "読み込んでいます…"; return; }
    var c = csel.value, ok = [], unk = [], far = [];
    data.forEach(function(r){
      if (c && r.c !== c && !(r.y.indexOf("visit") >= 0 && (r.vz || (r.ar || "").indexOf(c) >= 0))) return;
      var j = judge(r); if (j[0] === 2) return;
      (r.far ? far : j[0] ? unk : ok).push([r, j[1]]);
    });
    // 夜の時間に開いたときは、夜間・救急の病院を先に
    var nightFirst = night() && !on.night;
    if (nightFirst) ok.sort(function(a, b){ return (b[0].y.indexOf("night") >= 0) - (a[0].y.indexOf("night") >= 0); });
    ok.sort(function(a, b){ return openNow(b[0]) - openNow(a[0]); });  // いま受付時間内の病院を先に
    var n = ok.length, place = v + (c ? " " + c : "");
    sum.innerHTML = esc(place) + "で合う病院 " + n + "院" + (unk.length ? "<small>ほかに、書いていないので要確認 " + unk.length + "院</small>" : "") + (nightFirst && n ? "<small>いまは夜なので、夜間・救急の病院を先に並べています</small>" : "");
    var all = ok.concat(unk), html = "", i = 0;
    all.slice(0, shown).forEach(function(x){
      if (i === ok.length && unk.length) html += '<p class="hf-h">条件が公式の情報に書いていない病院（行く前に確かめてください）</p>';
      html += card(x[0], x[1]); i++;
    });
    if (!all.length) {
      html = '<div class="hf-none">' + esc(place) + "で、この条件に合う病院はまだ見つかっていません。条件を1つ外すか、市区町村を「すべて」にしてみてください。</div>";
      if (far.length) html += '<p class="hf-h">近くの県の病院</p>' + far.map(function(x){ return card(x[0], x[1]); }).join("");
    }
    list.innerHTML = html + (all.length > shown ? '<button type="button" class="hf-more">あと' + (all.length - shown) + '院を見る</button>' : '');
    box.parentNode.classList.add("hf-on");
    if (window.petReviews) window.petReviews(list);
  }
  function load(){
    data = null; draw();
    var v = sel.value; if (!v || !SLUG[v]) { fillCities([]); return; }
    fetch("/hospital/data/" + SLUG[v] + ".json").then(function(r){ return r.json(); }).then(function(j){
      if (sel.value !== v) return;
      data = j; fillCities(j); shown = 30; draw();
    }).catch(function(){ data = []; draw(); });
  }
  function fillCities(j){
    var cs = {}; j.forEach(function(r){ if (!r.far && r.c) cs[r.c] = (cs[r.c] || 0) + 1; });
    var keep = firstCity || csel.value; firstCity = "";
    csel.innerHTML = '<option value="">市区町村すべて</option>' + Object.keys(cs).sort().map(function(c){ return '<option value="' + esc(c) + '">' + esc(c) + "（" + cs[c] + "）</option>"; }).join("");
    if (keep && cs[keep]) csel.value = keep;
  }
  box.addEventListener("click", function(ev){
    var b = ev.target.closest("button"); if (!b) return;
    if (b.classList.contains("hf-mo")) { b.parentNode.classList.add("open"); b.hidden = true; return; }
    if (b.id === "hfClear") { on = {}; csel.value = ""; shown = 30; draw(); return; }
    var k = b.dataset.v; if (!k) return;
    if (on[k]) delete on[k]; else on[k] = 1;
    shown = 30; draw();
    try { window.gtag && gtag("event", "hosp_filter", {key: k, on: on[k] ? 1 : 0, pref: sel.value || "all"}); } catch (x) {}
  });
  list.addEventListener("click", function(ev){
    var m = ev.target.closest(".hf-more"); if (m) { shown += 30; draw(); return; }
    var a = ev.target.closest("a[data-k]"); if (a) try { window.gtag && gtag("event", a.dataset.k === "taxi" ? "facility_taxi" : "official_site", {cat: "hospital", from: "hosp_find"}); } catch (x) {}
  });
  csel.addEventListener("change", function(){ shown = 30; draw(); });
  if (box.dataset.pref) { sel.value = box.dataset.pref; }
  function apply(){ load(); }
  if (box.dataset.pref) { prefLinks(sel.value); sel.addEventListener("change", function(){ prefPut(sel.value); prefLinks(sel.value); apply(); }); apply(); }
  else { prefKeep(sel, apply); if (!sel.value) { draw(); prefGuess(sel, apply); } }

})();
