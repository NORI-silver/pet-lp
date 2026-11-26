// 動物病院を自分の条件でさがす（tools/hosp_find.py が prefkeep の関数と一緒に /hosp.js に書き出す）
// 最初に見えるのは「地域・動物・診療ニーズ」の3つ。ほかは「詳しい条件で絞り込む」の中（Nori 2026-11-15 の依頼書）
  var TB = ' target="_blank" rel="noopener"', enc = encodeURIComponent, $id = document.getElementById.bind(document);
  var box = $id("hf");
  if (!box) return;
  var sel = $id("hospPref"), det = $id("hfDet"), detN = $id("hfDetN"),
      list = $id("hfList"), sum = $id("hfSum");
  var SLUG = __SLUG__, LABEL = __LABEL__, REG = __REG__, SYM = __SYM__, av = null;
  list.addEventListener("click", function(ev){ var b = ev.target.closest("button[data-pk]"); if (!b) return; pick.set([{p: b.getAttribute("data-pk")}]); box.scrollIntoView({behavior: "smooth", block: "start"}); });
  var NEED = {night:["night"],sunhol:["sun","hol"],h24:["h24"],visit:["visit"],spec:["spec"]}
  var NEEDL = {night:"夜間・救急",sunhol:"日曜・祝日",h24:"24時間",visit:"往診",spec:"専門診療"}
  // 病院の種類は「そういう病院か」なので、書いていなければ合わない（要確認には入れない）
  var STRICT = {night:1,visit:1,catspec:1,exospec:1,large:1,h24:1,catroom:1,ct:1,spec:1}
  var FEAT = [["night","夜間・救急"],["h24","24時間"],["visit","往診"],["catspec","猫専門"],["exospec","うさぎ・鳥などの専門"],["large","大型犬の設備"],["sun","日曜診療"],["hol","祝日診療"],["late","19時以降も"],["park","駐車場あり"],["card","カード可"]]
  var on = {}, need = NEED[box.dataset.preset] ? box.dataset.preset : "", data = null, near = {}, shown = 30, places = [], cache = {}, pick = null, spots = [];
  if (box.dataset.preset && !NEED[box.dataset.preset]) on[box.dataset.preset] = 1;
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
  function night(){ var h = new Date().getHours(); return h >= 19 || h < 8; }
  function keys(){ var k = Object.keys(on); (NEED[need] || []).forEach(function(x){ if (k.indexOf(x) < 0) k.push(x); }); return k; }
  function has(r, k){
    if (k === "spec") return ["catspec", "exospec", "large"].some(function(x){ return r.y.indexOf(x) >= 0; }) || !!(r.d && r.d.length);
    if (k.slice(0, 2) === "d:") return !!(r.d && r.d.indexOf(k.slice(2)) >= 0);
    if (k.slice(0, 2) === "y:") return (r.d || []).some(function(d){ return (SYM[k] || []).indexOf(d) >= 0; });
    return r.y.indexOf(k) >= 0;
  }
  // いま受付中か：受付時間（曜日で変わらない病院だけ t がある）と休診の文から。分からないときは null（要確認に回す）
  function openNow(r){
    if (!r.t) return null;
    var d = new Date(), wd = "日月火水木金土"[d.getDay()];
    if (r.x && r.x.indexOf(wd + "曜") >= 0) return false;
    var m = d.getHours() * 60 + d.getMinutes();
    return r.t.some(function(t){ return (m >= t[0] && m < t[1]) || (t[1] > 1440 && m < t[1] - 1440); });
  }
  function judge(r, ks){
    // 0＝合う、1＝書いていない（要確認）、2＝合わない
    var g = 0, unk = [];
    for (var i = 0; i < ks.length; i++) {
      var k = ks[i];
      if (k === "open") { var o = openNow(r); if (o === true) continue; if (o === false) return [2, []]; g = 1; unk.push(k); continue; }
      if (has(r, k)) continue;
      if (r.no.indexOf(k) >= 0 || STRICT[k]) return [2, []];
      g = 1; unk.push(k);
    }
    return [g, unk];
  }
  // どこで：選んだ場所（県・市区町村・駅。いくつでも）のどれかに合えばよい。往診は来てくれる地域で見る（Nori 2026-11-16）
  function typed(){ return pick && !(pick.open && pick.open()) ? (pick.text() || "").trim() : ""; }
  function placeOk(r, p){
    var visitOk = function(x){ return r.y.indexOf("visit") >= 0 && (r.vz || (r.ar || "").indexOf(x) >= 0); };
    if (r._p !== p.p) return false;
    if (p.c) return r.c === p.c || r.c.indexOf(p.c) === 0 || visitOk(p.c);
    if (p.s) { var b = p.s.replace(/駅$/, ""); return (r.st || "").indexOf(p.s) >= 0 || (r.ad || "").indexOf(b) >= 0; }
    return true;
  }
  function place(r){
    var t = typed();
    if (places.length && !places.some(function(p){ return placeOk(r, p); })) return false;
    if (t) { var hay = [r.n, r.c, r.ad, r.st, r.ar].join(" "); if (hay.indexOf(t) < 0 && !(r.y.indexOf("visit") >= 0 && (r.vz || (r.ar || "").indexOf(t) >= 0))) return false; }
    return true;
  }
  function plabel(){ return places.map(PlacePick.label).join("・"); }
  function paintBtns(){
    box.querySelectorAll("button[data-v]").forEach(function(b){
      var k = b.dataset.v;
      b.setAttribute("aria-pressed", on[k] ? "true" : "false");
      // その県で1院も当てはまらないボタンは出さない（押しても0件になるだけなので）。犬・猫はいつも出す
      b.hidden = !!av && k !== "dog" && k !== "cat" && !on[k] && !av[k];
      if (on[k] && b.classList.contains("hf-x")) b.parentNode.classList.add("open");
    });
    var sos = box.querySelector(".hf-sos"); if (sos) sos.hidden = need === "night";
    box.querySelectorAll("button[data-need]").forEach(function(b){ b.setAttribute("aria-pressed", b.dataset.need === need ? "true" : "false"); });
    box.querySelectorAll(".hf-det .hf-r").forEach(function(r){ r.hidden = ![].some.call(r.querySelectorAll("button[data-v]"), function(b){ return !b.hidden; }); });
    var n = Object.keys(on).filter(function(k){ return !box.querySelector('.hf-det button[data-v="' + k + '"]') ? false : true; }).length;
    detN.textContent = n ? n : "";
  }
  // カードのイメージ写真（無料の写真素材。本物の病院の写真ではないので「イメージ」と書き、alt は空）。となりが同じ写真にならないよう順番に回す
  // カードの写真（使ってよいと確かめた写真だけ。tools/cardphoto.py と同じ形）。ない病院は共通の枠（Nori 2026-11-16）
  function picHtml(r){
    if (!r.ph) return '<div class="cs-ph cs-ph0"' + (r.rv ? ' data-gph="' + esc(r.rv) + '"' : '') + ' aria-hidden="true"></div>';
    var ps = r.ph[0], im = ps.map(function(p, i){ return '<img src="' + esc(p) + '" alt="' + esc(r.n) + 'の写真' + (i + 1) + '" width="520" height="347" loading="lazy" decoding="async">'; }).join("");
    return '<div class="cs-ph"><div class="cs-ph-s">' + im + '</div>' + (ps.length > 1 ? '<span class="cs-ph-n" aria-hidden="true">📷 ' + ps.length + '</span>' : '') + (r.ph[1] ? '<small class="cs-ph-c">' + esc(r.ph[1]) + '</small>' : '') + '</div>';
  }
  function card(r, unk){
    var b = [];
    if (r.a) b.push('<span>' + esc(r.a.length > 22 ? r.a.slice(0, 22) + "…" : r.a) + '</span>');
    function badge(l){ var x = '<span>' + esc(l) + '</span>'; if (l && b.indexOf(x) < 0) b.push(x); }
    keys().forEach(function(k){ if (k === "open" ? openNow(r) : has(r, k)) badge(LABEL[k] || NEEDL[k] || k.slice(2)); });
    FEAT.forEach(function(f){ if (b.length < 6 && has(r, f[0])) badge(f[1]); });
    unk.forEach(function(k){ b.push('<span class="u">' + esc(LABEL[k] || NEEDL[k] || k.slice(2)) + 'は不明</span>'); });
    var top = r.tel ? '<a href="tel:' + esc(r.tel) + '" data-k="tel" data-ga>📞 電話する</a>' : '<a href="' + esc(r.u) + '"' + TB + ' data-k="site" data-ga>公式サイト ↗</a>';
    var route = r.ad ? '<a class="l" href="https://www.google.com/maps/dir/?api=1&destination=' + enc(r.ad) + '"' + TB + ' data-k="route">📍 経路を見る</a>' : '';
    var sub = [];
    if (r.tel) sub.push('<a href="' + esc(r.u) + '"' + TB + ' data-k="site" data-ga>公式サイト</a>');
    if (r.pg) sub.push('<a href="' + esc(r.pg) + '">診療内容の詳細</a>');
    if (r.ad && r.y.indexOf("visit") < 0) sub.push('<a href="/?to=' + enc(r.ad) + '#form" data-k="taxi" data-ga>🚕 ペットタクシーの料金</a>');
    sub.push('<a href="https://www.google.com/maps/search/?api=1&query=' + enc(r.n + ' ' + (r.ad || '')) + '"' + TB + ' data-k="review">Google Mapsの口コミ</a>');
    return '<div class="hc">' + picHtml(r) + '<a class="hc-n" href="' + esc(r.pg || r.u) + '"' + (r.pg ? '' : TB) + '>' + esc(r.n) + '</a>'
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
    var v = places.length ? places[0].p : "";
    if (!v) {
      // 県がまだ決まっていないとき（位置が分からないときなど）は、空のままにせず、地方ごとの県のボタン（病院の数つき）を出す
      sum.innerHTML = "都道府県を選ぶと、合う病院が並びます"; box.parentNode.classList.remove("hf-on");
      list.innerHTML = '<div class="pk">' + REG.map(function(g){
        return '<details class="pk-g"><summary>' + esc(g[0]) + '</summary><div class="pk-b">' + g[1].map(function(x){
          return '<button type="button" data-pk="' + esc(x[0]) + '">' + esc(x[0]) + '<small>' + x[1] + '</small></button>'; }).join("") + '</div></details>';
      }).join("") + '</div>';
      return;
    }
    if (!data) { sum.textContent = "読み込んでいます…"; return; }
    var ks = keys(), m = match(data.filter(function(r){ return !r.far; }), ks, true), ok = m[0], unk = m[1];
    // 夜の時間に開いたときは、夜間・救急の病院を先に（受付中とは言い切らない）
    var nightFirst = night() && need !== "night";
    // 写真のある病院を先に（Nori 2026-11-22）
    ok.sort(function(a, b){ return (b[0].ph ? 1 : 0) - (a[0].ph ? 1 : 0); });
    if (nightFirst) ok.sort(function(a, b){ return (b[0].y.indexOf("night") >= 0) - (a[0].y.indexOf("night") >= 0); });
    var t = typed(), pl = plabel() + (t ? "「" + t + "」" : "");
    sum.innerHTML = esc(pl) + "で合う病院 " + ok.length + "院" + (unk.length ? "<small>ほかに、公式の情報に書いていないので要確認 " + unk.length + "院</small>" : "")
      + (nightFirst && ok.some(function(x){ return x[0].y.indexOf("night") >= 0; }) ? "<small>夜の時間なので、夜間・救急の病院を先に並べています</small>" : "");
    var all = ok.concat(unk), html = ""; pic = 0;
    all.slice(0, shown).forEach(function(x, i){
      if (i === ok.length && unk.length) html += '<p class="hf-h">条件が公式の情報に書いていない病院（行く前に確かめてください）</p>';
      html += card(x[0], x[1]);
    });
    if (all.length > shown) html += '<button type="button" class="hf-more">あと' + (all.length - shown) + '院を見る</button>';
    if (!ok.length) {
      // 0件のとき：どの条件を外せば何院見つかるか
      var alt = [];
      ks.forEach(function(k){
        var rest = ks.filter(function(x){ return x !== k; }), n = match(data.filter(function(r){ return !r.far; }), rest, true)[0].length;
        if (n) alt.push('<button type="button" data-drop="' + esc(k) + '">「' + esc(LABEL[k] || NEEDL[k] || (NEEDL[need] && NEED[need].indexOf(k) >= 0 ? NEEDL[need] : k.slice(2))) + '」を外す（' + n + '院）</button>');
      });
      if (places.some(function(p){ return p.c || p.s; }) || t) { var n2 = match(data.filter(function(r){ return !r.far; }), ks, false)[0].length; if (n2) alt.push('<button type="button" data-drop="place">' + esc(prefsOf().join("・")) + 'の全体で見る（' + n2 + '院）</button>'); }
      alt.push('<a href="/emergency/#pref=' + enc(v) + '">緊急のときの連絡先</a>');
      html = '<div class="hf-none">' + esc(pl) + "で、この条件に合う病院はまだ見つかっていません。<div class=\"hf-alt\">" + alt.join("") + "</div></div>" + html;
    }
    // 少ないとき（3院まで）は、近くの県の病院も
    if (ok.length < 3) {
      var nb = [];
      PlacePick.near(v).forEach(function(p){ if (near[p] && prefsOf().indexOf(p) < 0) match(near[p].filter(function(r){ return !r.far; }), ks, false)[0].forEach(function(x){ nb.push([x[0], p]); }); });
      data.filter(function(r){ return r.far; }).forEach(function(r){ if (!judge(r, ks)[0]) nb.push([r, ""]); });
      if (nb.length) html += '<p class="hf-h">近くの県の病院</p>' + nb.slice(0, 8).map(function(x){ return card(x[0], []); }).join("");
      else if (!Object.keys(near).length) loadNear(v);
    }
    list.innerHTML = html;
    box.parentNode.classList.add("hf-on");
    if (window.petReviews) window.petReviews(list);
  }
  function prefsOf(){ var o = []; places.forEach(function(p){ if (o.indexOf(p.p) < 0) o.push(p.p); }); return o; }
  function loadNear(v){
    if (loadNear.v === v) return; loadNear.v = v;
    Promise.all(PlacePick.near(v).map(function(p){ return SLUG[p] ? fetch("/hospital/data/" + SLUG[p] + ".json").then(function(r){ return r.json(); }).then(function(j){ near[p] = j; }).catch(function(){}) : null; }))
      .then(function(){ if (places.length && places[0].p === v) draw(); });
  }
  function get(pf){
    if (cache[pf]) return Promise.resolve(cache[pf]);
    return fetch("/hospital/data/" + SLUG[pf] + ".json").then(function(r){ return r.json(); }).catch(function(){ return []; })
      .then(function(j){ j.forEach(function(r){ r._p = pf; }); cache[pf] = j; spots = []; return j; });
  }
  function load(){
    data = null; av = null; near = {}; loadNear.v = ""; draw();
    var ps = prefsOf().filter(function(p){ return SLUG[p]; }), key = ps.join(",");
    if (!ps.length) return;
    load.k = key;
    Promise.all(ps.map(get)).then(function(js){
      if (load.k !== key) return;
      // 選んだ県のデータで1院以上に当てはまる条件
      data = [].concat.apply([], js); av = {};
      data.forEach(function(r){ if (!r.far) { r.y.forEach(function(k){ av[k] = 1; }); (r.d || []).forEach(function(d){ av["d:" + d] = 1; }); if (r.t) av["open"] = 1; Object.keys(SYM).forEach(function(k){ if (has(r, k)) av[k] = 1; }); } });
      shown = 30; draw();
    });
  }
  // 候補：読み込んだ県の、区（政令市）と駅の名前（病院の情報に書いてあるものだけ）
  function extra(t){
    if (!spots.length) {
      var seen = {};
      Object.keys(cache).forEach(function(pf){ cache[pf].forEach(function(r){
        if (r.far) return;
        if (/^.+市.+区$/.test(r.c)) { var k = pf + "|c|" + r.c; if (!seen[k]) { seen[k] = {p: pf, c: r.c, n: 0}; spots.push(seen[k]); } seen[k].n++; }
        (r.st || "").replace(/([一-龥ぁ-んァ-ヶーa-zA-Z0-9]{1,12})駅/g, function(m0, nm){ var k2 = pf + "|s|" + nm; if (!seen[k2]) { seen[k2] = {p: pf, s: nm + "駅", n: 0}; spots.push(seen[k2]); } seen[k2].n++; return m0; });
      }); });
      spots.sort(function(a, b){ return b.n - a.n; });
    }
    if (!t) return [];
    var kn = function(x){ return x.replace(/[ァ-ヶ]/g, function(c){ return String.fromCharCode(c.charCodeAt(0) - 96); }); };
    return spots.filter(function(x){ var nm = kn(x.c || x.s); return nm.indexOf(t) === 0 || (t.length >= 2 && nm.indexOf(t) >= 0); }).slice(0, 5);
  }
  box.addEventListener("click", function(ev){
    var b = ev.target.closest("button, a[data-sos]"); if (!b || b.closest(".pp")) return;
    if (b.dataset.sos !== undefined) { ev.preventDefault(); need = "night"; draw(); list.scrollIntoView({behavior: "smooth"}); try { window.gtag && gtag("event", "hosp_sos", {pref: sel.value || "all"}); } catch (x) {} return; }
    if (b.classList.contains("hf-mo")) { b.parentNode.classList.add("open"); return; }
    if (b.id === "hfGo") { list.scrollIntoView({behavior: "smooth"}); return; }
    if (b.id === "hfClear") { on = {}; need = ""; pick.clearText(); shown = 30; draw(); return; }
    if (b.dataset.need !== undefined) {
      need = b.dataset.need;
      // 専門診療は、診療科目などを選べるように開く
      if (need === "spec") det.open = true;
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
    if (d) { var k = d.dataset.drop; if (k === "place") { pick.clearText(); pick.set(prefsOf().map(function(p){ return {p: p}; })); return; } else if (on[k]) delete on[k]; else need = ""; draw(); return; }
    // 公式サイト・電話・タクシー・経路はここだけで数える（ga.js は data-ga のリンクを数えない）。会社ごとに集計できるよう病院名と行き先のホストも送る（2026-11-16）
    var a = ev.target.closest("a[data-k]"), c = a && a.closest(".hc"), nm = c && c.querySelector(".hc-n");
    if (a) try { window.gtag && gtag("event", {taxi: "facility_taxi", tel: "tel_click", route: "hosp_route"}[a.dataset.k] || "official_site", {cat: "hospital", from: "hosp_find", company_name: nm ? nm.textContent.trim().slice(0, 80) : "", host: a.dataset.k === "site" ? a.hostname : "", pref: sel.value || "", transport_type: "beacon"}); } catch (x) {}
  });
  // どこで：都道府県（いくつでも）・市区町村・駅の候補つきの入力（/place.js）
  var tm, cnt0 = {};
  REG.forEach(function(g){ g[1].forEach(function(x){ cnt0[x[0]] = x[1]; }); });
  pick = PlacePick({root: $id("hfPlace"), unit: "院", ph: "都道府県・市区町村・駅名",
    prefs: [].filter.call(sel.options, function(o){ return o.value; }).map(function(o){ return [o.value, cnt0[o.value] || 0]; }),
    extra: extra,
    cnt: function(p){ var j = cache[p.p]; if (!j) return null; var n = 0; j.forEach(function(r){ if (!r.far && placeOk(r, p)) n++; }); return n; },
    typed: function(){ clearTimeout(tm); tm = setTimeout(function(){ shown = 30; draw(); }, 150); },
    onChange: function(ps){
      places = ps;
      [].forEach.call(box.querySelectorAll(".pref-guess"), function(g){ g.remove(); });
      var first = ps.length ? ps[0].p : "";
      sel.value = first; if (first) prefPut(first); prefLinks(first);
      if (!box.dataset.pref) try { history.replaceState(null, "", location.pathname + location.search + (first ? "#pref=" + enc(first) : "")); } catch (x) {}
      try { window.gtag && gtag("event", "hosp_filter", {key: "place", on: ps.length, pref: prefsOf().join(",") || "all"}); } catch (x) {}
      if (prefsOf().join(",") !== load.k) load(); else { shown = 30; draw(); }
    }});
  function start(ps){ ps = ps.filter(function(p){ return SLUG[p.p]; }); pick.set(ps, true); places = pick.get(); if (places.length) { sel.value = places[0].p; prefLinks(sel.value); } load(); }
  if (box.dataset.pref) {
    // 県・市区町村のページ：そのページの場所から。ほかの県も足せる
    start([box.dataset.city ? {p: box.dataset.pref, c: box.dataset.city} : {p: box.dataset.pref}]);
  } else {
    // 前に選んだ場所（ほかの分野で選んだものも）→ URL の #pref= → 覚えた県 → 位置からの推測
    var sv = pick.saved(), mh = location.hash.match(/^#pref=(.+)$/), hv = null;
    if (mh) { try { hv = decodeURIComponent(mh[1]); } catch (x) {} }
    if (hv && !sv.some(function(p){ return p.p === hv; })) sv = [{p: hv}];
    if (!sv.length && prefGet()) sv = [{p: prefGet()}];
    start(sv);
    if (!places.length) { draw(); prefGuess(sel, function(){ if (sel.value && !places.length) start([{p: sel.value}]); }); }
  }
