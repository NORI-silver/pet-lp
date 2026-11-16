// 生成：tools/uikit.py（元は tools/find.js と tools/prefkeep.py）

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

// 施設の一覧の「さがす箱」（共通。tools/uikit.py が /find.js に書き出す。前に prefkeep の関数が付く）。
// 箱 [data-ff]：都道府県（#ffPref、ないページもある）・市区町村や名前の入力（#ffQ）・条件のボタン（data-k）。
// 施設 [data-ffi]：data-k＝公式サイトに書いてある条件、data-q＝名前・市区町村など、data-no＝はっきり「しない」と書いてある条件。
// 書いていない条件は「条件が公式サイトに書いていない」として数え（「分からない」とは出さない）、押せば見られる。合わないと決めつけない。入れた文字は解析に送らない。
(function(){
  var box = document.querySelector("[data-ff]");
  if (!box) return;
  var cat = box.getAttribute("data-ff"), unit = box.getAttribute("data-unit") || "件";
  var sel = document.getElementById("ffPref"), q = null, pick = null, places = [];
  var sum = document.getElementById("ffSum"), alt = document.getElementById("ffAlt"), clr = document.getElementById("ffClear");
  var res = document.getElementById("ffRes"), det = box.querySelector(".ux-det");
  var needPref = box.hasAttribute("data-needpref");
  var items = [].slice.call(document.querySelectorAll("[data-ffi]"));
  var btns = [].slice.call(box.querySelectorAll("button[data-k]"));
  var LBL = {};
  btns.forEach(function(b){ LBL[b.getAttribute("data-k")] = b.getAttribute("data-l") || b.textContent; });
  items.forEach(function(it){
    // 条件：data-k と、カードの印（data-ft・data-tags。区切りは「|」、空白は「_」に）
    var ex = [it.getAttribute("data-ft"), it.getAttribute("data-tags")].join("|").split("|").filter(Boolean).map(function(x){ return x.trim().replace(/ /g, "_"); });
    it._k = " " + (it.getAttribute("data-k") || "") + " " + ex.join(" ") + " ";
    it._no = " " + (it.getAttribute("data-no") || "") + " ";
    var p = it.closest("[data-pref]");
    it._p = it.getAttribute("data-pref") || (p ? p.getAttribute("data-pref") : "");
    it._q = (it.getAttribute("data-q") || it.textContent).toLowerCase();
    // 来てくれる地域（🚗 の行）。出張・訪問の施設は、所在地ではなくこの地域でしぼる（Nori 2026-11-16）
    it._area = "";
    [].forEach.call(it.querySelectorAll(".ux-c-l"), function(r){ var i = r.querySelector("i"); if (i && i.textContent.indexOf("🚗") >= 0) it._area = r.textContent.replace("🚗", "").trim(); });
  });
  // カードのイメージ写真（無料の写真素材。本物の施設の写真ではないので「イメージ」と出し、alt は空）。となりが同じにならないよう順番に回す
  var pics = (box.getAttribute("data-pics") || "").split("|");
  if (pics[1]) {
    var pf = pics[1].split(",");
    [].forEach.call(document.querySelectorAll(".emg-item.fc[data-ffi], .ux-c.dr-card[data-ffi], .yd-card[data-ffi]"), function(c, i){
      if (c.querySelector(".ux-img")) return;
      var d = el("div", "ux-img"), im = document.createElement("img");
      im.src = pics[0] + pf[i % pf.length]; im.alt = ""; im.loading = "lazy"; d.appendChild(im); c.insertBefore(d, c.firstChild);
    });
  }
  var showUnk = false;
  function on(){ return btns.filter(function(b){ return b.getAttribute("aria-pressed") === "true"; }).map(function(b){ return b.getAttribute("data-k"); }); }
  function norm(s){ return (s || "").trim().toLowerCase().replace(/[\s　]+/g, " "); }
  // 1件の判定：0＝合う、1＝書いていない、2＝合わない（県・入力に合わないか、しないと書いてある）
  // 場所の判定：0＝合う、1＝来てくれる地域にはっきり書いていない（近郊・相談など）、2＝合わない
  function cityJ(it, p){
    var c = p.c, base = c.replace(/^(.+?市).+区$/, "$1"), a = it._area;
    if (!a) return (it._q.indexOf(c.toLowerCase()) >= 0 || it._q.indexOf(base.toLowerCase()) >= 0) ? 0 : 2;
    if (a.indexOf(c) >= 0 || a.indexOf(base) >= 0) return 0;
    if (p.p === "東京都" && /区$/.test(c) && /23区/.test(a)) return 0;
    var pn = p.p.replace(/[都道府県]$/, "");
    if (new RegExp(pn + "[都道府県]?(内)?(全域|全体|一円)|^全域").test(a)) return 0;
    return /近郊|周辺|近隣|相談|など|ほか|他|その他/.test(a) ? 1 : 2;
  }
  function placeJ(it, ps){
    if (!ps.length) return 0;
    var best = 2;
    for (var i = 0; i < ps.length; i++) {
      if (it._p && it._p !== ps[i].p) continue;
      if (!ps[i].c) return 0;
      best = Math.min(best, cityJ(it, ps[i]));
      if (!best) return 0;
    }
    return best;
  }
  function judge(it, ks, pf, qs){
    var pj = placeJ(it, pf || []);
    if (pj === 2) return 2;
    if (qs && qs.split(" ").some(function(w){ return it._q.indexOf(w) < 0; })) return 2;
    var r = pj;
    for (var i = 0; i < ks.length; i++) {
      if (it._k.indexOf(" " + ks[i] + " ") >= 0) continue;
      if (ks[i] === "a:dog" && it._no.indexOf(" a:dog ") < 0) continue;  // 犬は「犬は受けない」と書いていなければ合う
      if (it._no.indexOf(" " + ks[i] + " ") >= 0) return 2;
      r = 1;
    }
    return r;
  }
  function count(ks, pf, qs){
    var c = [0, 0];
    items.forEach(function(it){ var j = judge(it, ks, pf, qs); if (j < 2) c[j]++; });
    return c;
  }
  function el(t, c, x){ var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function apply(track){
    var ks = on(), pf = places, qs = norm(pick ? pick.text() : ""), idle = needPref && !pf.length && !qs;
    var c = [0, 0];
    items.forEach(function(it){
      var j = idle ? 2 : judge(it, ks, pf, qs);
      if (j < 2) c[j]++;
      it.hidden = !(j === 0 || (j === 1 && showUnk));
      it.classList.toggle("ux-unk", j === 1);
      var note = it.querySelector(".ux-unk-n");
      if (j === 1) {
        if (!note) { note = el("p", "ux-unk-n"); var b = it.querySelector(".fc-body") || it; b.insertBefore(note, b.children[1] || null); }
        var miss = ks.filter(function(k){ return it._k.indexOf(" " + k + " ") < 0 && k !== "a:dog"; }).map(function(k){ return LBL[k]; });
        note.textContent = (placeJ(it, pf) === 1 ? "近くの地域も相談できます（来てくれる地域：" + it._area.slice(0, 40) + "）。" : "") + (miss.length ? "公式サイトに書いていない条件があります（" + miss.join("・") + "）" : "");
      } else if (note) note.remove();
    });
    // 中身のなくなったまとまり・見出しを隠す
    [].forEach.call(document.querySelectorAll(".fr, .emg-pref, [data-ffg]"), function(g){
      var vis = [].some.call(g.querySelectorAll("[data-ffi]"), function(it){ return !it.hidden; });
      g.hidden = !vis;
      var h = g.previousElementSibling;
      if (h && h.hasAttribute("data-ffh")) h.hidden = !vis;
      // 地域の見出しの件数を、いま見えている数に
      var sm = g.querySelector(".fr-h small, [data-ffn]");
      if (sm) sm.textContent = [].filter.call(g.querySelectorAll("[data-ffi]"), function(it){ return !it.hidden; }).length + unit;
    });
    [].forEach.call(document.querySelectorAll(".emg-region, .ux-region"), function(h){ h.hidden = !!(pf.length || ks.length || qs) || idle; });
    // 県が決まらないとき（位置が分からないときなど）は、空のままにせず、地方ごとの県のボタン（件数つき）を出す
    if (idle && sel && !box._pk) {
      var heads = [].slice.call(document.querySelectorAll(".emg-region"));
      if (heads.length) {
        var pk = el("div", "pk"); box._pk = pk;
        heads.forEach(function(h){
          var bs = [], n = h.nextElementSibling;
          while (n && !n.classList.contains("emg-region")) {
            if (n.matches && n.matches(".emg-pref[data-pref]")) { var c = n.querySelectorAll("[data-ffi]").length; if (c) bs.push([n.getAttribute("data-pref"), c]); }
            n = n.nextElementSibling;
          }
          if (!bs.length) return;
          var d = el("details", "pk-g"), su = el("summary", "", h.textContent), w = el("div", "pk-b");
          bs.forEach(function(x){ var b = el("button", "", x[0]); b.type = "button"; b.setAttribute("data-pk", x[0]); b.append(el("small", "", x[1] + unit)); w.append(b); });
          d.append(su, w); pk.append(d);
        });
        pk.addEventListener("click", function(ev){ var b = ev.target.closest("button[data-pk]"); if (!b) return; pick.set([{p: b.getAttribute("data-pk")}]); box.scrollIntoView({behavior: "smooth", block: "start"}); });
        heads[0].parentNode.insertBefore(pk, heads[0]);
      }
    }
    if (box._pk) box._pk.hidden = !idle;
    // 長い一覧は、はじめの N 件だけ見せて「のこり◯件を見る」（data-ffmore="N"。中身はHTMLにあるので検索にも読める。2026-11-16 見直し）
    [].forEach.call(document.querySelectorAll("[data-ffmore]"), function(g){
      var N = +g.getAttribute("data-ffmore") || 12, vis = [].filter.call(g.querySelectorAll("[data-ffi]"), function(it){ return !it.hidden; });
      var mb = g.nextElementSibling && g.nextElementSibling.classList.contains("ff-more") ? g.nextElementSibling : null;
      vis.forEach(function(it, i){ it.classList.toggle("ff-cut", !g._open && i >= N); });
      if (!g._open && vis.length > N) {
        if (!mb) { mb = el("button", "ff-more"); mb.type = "button"; g.after(mb); mb.onclick = function(){ g._open = true; apply(false); }; }
        mb.textContent = "のこり" + (vis.length - N) + unit + "を見る"; mb.hidden = false;
      } else if (mb) mb.hidden = true;
    });
    // 条件のボタン：いまの場所で1件もないもの・全部に当てはまって意味のないものは隠す（押しているもの・どの動物は残す）
    var all0 = count([], pf, qs)[0];
    btns.forEach(function(b){
      var k = b.getAttribute("data-k"), n = count([k], pf, qs)[0], an = b.getAttribute("data-g") === "a";
      b.hidden = b.getAttribute("aria-pressed") !== "true" && !idle && (an ? !n : (!n || (n >= all0 && all0 > 3)));
    });
    [].forEach.call(box.querySelectorAll(".ux-r, .ux-det"), function(r){ var bs = r.querySelectorAll("button[data-k]"); if (bs.length) r.hidden = ![].some.call(bs, function(b){ return !b.hidden; }); });
    if (det) { var dn = det.querySelectorAll('button[aria-pressed="true"]').length; var sp = det.querySelector("summary span"); if (sp) sp.textContent = dn ? String(dn) : ""; }
    // まとめの行
    sum.textContent = ""; alt.textContent = "";
    if (idle) { sum.append(el("b", "", "都道府県を選ぶか、市区町村の名前を入れると並びます")); }
    else {
      sum.append(el("b", "", c[0] + unit));
      var cond = pf.map(PlacePick.label).concat(qs ? ["「" + qs + "」"] : []).concat(ks.map(function(k){ return LBL[k]; })).filter(Boolean);
      if (cond.length) sum.append(el("small", "", cond.join("・") + (ks.length ? "が公式サイトに書いてある" : "")));
      if (c[1]) {
        var cp = items.filter(function(it){ return it.classList.contains("ux-unk") && placeJ(it, pf) === 1; }).length;
        var lab = cp === c[1] ? "近くの地域も相談できる" : "条件が公式サイトに書いていない";
        var u = el("button", "ux-alt-b", showUnk ? lab + c[1] + unit + "を隠す" : lab + c[1] + unit + "も見る");
        u.type = "button"; u.onclick = function(){ showUnk = !showUnk; apply(false); };
        alt.append(u);
      }
      if (!c[0]) {
        alt.append(el("p", "ux-none", "この条件に合う" + (box.getAttribute("data-noun") || "ところ") + "は、まだ載せていません。条件を外すと見られます。"));
        ks.forEach(function(k){
          var rest = ks.filter(function(x){ return x !== k; }), n = count(rest, pf, qs)[0];
          if (!n) return;
          var b = el("button", "ux-alt-b", "「" + LBL[k] + "」を外す（" + n + unit + "）"); b.type = "button";
          b.onclick = function(){ btns.forEach(function(x){ if (x.getAttribute("data-k") === k) x.setAttribute("aria-pressed", "false"); }); apply(true); };
          alt.append(b);
        });
        if (qs) { var n2 = count(ks, pf, "")[0]; if (n2) { var b2 = el("button", "ux-alt-b", "「" + qs + "」を外す（" + n2 + unit + "）"); b2.type = "button"; b2.onclick = function(){ pick.clearText(); apply(true); }; alt.append(b2); } }
        var cityPs = pf.filter(function(p){ return p.c; });
        if (cityPs.length) { var wide = pf.map(function(p){ return {p: p.p}; }), n4 = count(ks, wide, qs)[0]; if (n4) { var b4 = el("button", "ux-alt-b", wide.map(PlacePick.label).filter(function(x, i, a){ return a.indexOf(x) === i; }).join("・") + "の全体で見る（" + n4 + unit + "）"); b4.type = "button"; b4.onclick = function(){ pick.set(wide.filter(function(x, i){ return !wide.slice(0, i).some(function(y){ return y.p === x.p; }); })); }; alt.append(b4); } }
        if (pf.length && sel) { var n3 = count(ks, [], qs)[0]; if (n3) { var b3 = el("button", "ux-alt-b", "全国で見る（" + n3 + unit + "）"); b3.type = "button"; b3.onclick = function(){ pick.set([]); }; alt.append(b3); } }
      }
    }
    clr.hidden = !(ks.length || qs);
    box.classList.toggle("ux-busy", !!(ks.length || qs || pf.length));
    if (track && window.gtag) gtag("event", "ff_filter", {cat: cat, k: ks.join(","), pref: pf.map(function(p){ return p.p; }).join(","), places: pf.length, n: c[0]});
  }
  box.addEventListener("click", function(ev){
    var b = ev.target.closest("button[data-k]");
    if (b) {
      var was = b.getAttribute("aria-pressed") === "true";
      // どの動物は1つだけ（犬を押したら猫は外す）
      if (b.getAttribute("data-g") === "a") btns.forEach(function(x){ if (x.getAttribute("data-g") === "a") x.setAttribute("aria-pressed", "false"); });
      b.setAttribute("aria-pressed", String(!was)); apply(true); return;
    }
    if (ev.target.closest("#ffGo")) { apply(false); var t = res || document.querySelector("[data-ffi]:not([hidden])"); if (t) t.scrollIntoView({behavior: "smooth", block: "start"}); }
  });
  clr.addEventListener("click", function(){ btns.forEach(function(b){ b.setAttribute("aria-pressed", "false"); }); pick.clearText(); showUnk = false; apply(true); });
  // どこで：都道府県（いくつでも）・市区町村の候補つきの入力（/place.js）
  var spot = document.getElementById("ffPlace"), byPref = {}, fixed = "";
  items.forEach(function(it){ if (it._p) byPref[it._p] = (byPref[it._p] || 0) + 1; });
  if (!sel) { var ks0 = Object.keys(byPref); if (ks0.length === 1) fixed = ks0[0]; }
  var prefs = sel ? [].filter.call(sel.options, function(o){ return o.value; }).map(function(o){ return [o.value, byPref[o.value] || 0]; }) : Object.keys(byPref).map(function(k){ return [k, byPref[k]]; });
  var tm;
  pick = PlacePick({root: spot, prefs: prefs, fixed: fixed, unit: unit,
    ph: spot.getAttribute("data-ph") || "都道府県・市区町村",
    cnt: function(p){ var n = 0; items.forEach(function(it){ if (placeJ(it, [p]) === 0) n++; }); return n; },
    extra: fixed ? function(t){ return []; } : null,
    typed: function(){ clearTimeout(tm); tm = setTimeout(function(){ apply(false); }, 150); },
    onChange: function(ps){
      places = ps;
      [].forEach.call(box.querySelectorAll(".pref-guess"), function(g){ g.remove(); });
      var first = ps.length ? ps[0].p : "";
      if (sel) { sel.value = first; if (first) prefPut(first); prefLinks(first); try { history.replaceState(null, "", location.pathname + location.search + (first ? "#pref=" + encodeURIComponent(first) : "")); } catch (x) {} }
      apply(true);
    }});
  if (!sel) prefLinks(prefGet());
  if (sel) {
    // 前に選んだ場所（ほかの分野で選んだものも）→ URL の #pref= → 覚えた県 → 位置からの推測
    var sv = pick.saved().filter(function(p){ return byPref[p.p] !== undefined || [].some.call(sel.options, function(o){ return o.value === p.p; }); });
    var m = location.hash.match(/^#pref=(.+)$/), hv = null;
    if (m) { try { hv = decodeURIComponent(m[1]); } catch (x) {} }
    if (hv && !sv.some(function(p){ return p.p === hv; })) sv = [{p: hv}];
    if (!sv.length && prefGet()) sv = [{p: prefGet()}];
    sv = sv.filter(function(p){ return [].some.call(sel.options, function(o){ return o.value === p.p; }); });
    if (sv.length) { pick.set(sv, true); places = sv; sel.value = sv[0].p; prefLinks(sel.value); }
    else if (box.hasAttribute("data-guess")) prefGuess(sel, function(){ if (sel.value && !places.length) { pick.set([{p: sel.value}], true); places = pick.get(); } apply(false); });
  } else if (fixed) {
    var sv2 = pick.saved().filter(function(p){ return p.p === fixed && p.c; });
    if (sv2.length) { pick.set(sv2, true); places = sv2; }
  }
  apply(false);
})();
