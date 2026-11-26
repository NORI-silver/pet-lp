// 施設の一覧の「さがす箱」（共通。tools/uikit.py が /find.js に書き出す。前に prefkeep の関数が付く）。
// 箱 [data-ff]：都道府県（#ffPref、ないページもある）・市区町村や名前の入力（#ffQ）・条件のボタン（data-k）。
// 施設 [data-ffi]：data-k＝公式サイトに書いてある条件、data-q＝名前・市区町村など、data-no＝はっきり「しない」と書いてある条件。
// 書いていない条件は「条件が公式サイトに書いていない」として数え（「分からない」とは出さない）、押せば見られる。合わないと決めつけない。入れた文字は解析に送らない。
(function(){
  function at(n,k){ return n.getAttribute(k); }
  function id(s){ return document.getElementById(s); }
  function qa(s){ return document.querySelectorAll(s); }
  function each(a, f){ [].forEach.call(a, f); }
  var box = document.querySelector("[data-ff]");
  if (!box) return;
  var cat = at(box,"data-ff"), unit = at(box,"data-unit") || "件";
  var sel = id("ffPref"), q = null, pick = null, places = [];
  var sum = id("ffSum"), alt = id("ffAlt"), clr = id("ffClear");
  var res = id("ffRes"), det = box.querySelector(".ux-det");
  var needPref = box.hasAttribute("data-needpref");
  var SLUG = __SLUG__; // 都道府県→URLの名前（tools/uikit.py が tools/prefs.py から差し込む。県のページどうしの移動に使う）
  var items = Array.from(qa("[data-ffi]"));
  var btns = Array.from(box.querySelectorAll("button[data-k]"));
  var LBL = {};
  btns.forEach(function(b){ LBL[at(b,"data-k")] = at(b,"data-l") || b.textContent; });
  var idxCtr = 0;
  function initItem(it){
    if (it._idx === undefined) it._idx = idxCtr++;
    // 条件：data-k と、カードの印（data-ft・data-tags。区切りは「|」、空白は「_」に）
    var ex = [at(it,"data-ft"), at(it,"data-tags")].join("|").split("|").filter(Boolean).map(function(x){ return x.trim().replace(/ /g, "_"); });
    it._k = " " + (at(it,"data-k") || "") + " " + ex.join(" ") + " ";
    it._no = " " + (at(it,"data-no") || "") + " ";
    var p = it.closest("[data-pref]");
    it._p = at(it,"data-pref") || (p ? at(p,"data-pref") : "");
    it._q = (at(it,"data-q") || it.textContent).toLowerCase();
    it._near = it.hasAttribute("data-near") || !!it.closest("[data-near]");
    it._yen = +(at(it,"data-yen") || 0) || null;
    it._ll = it.hasAttribute("data-lat") ? [+at(it,"data-lat"), +at(it,"data-lng")] : null;
    // 来てくれる地域（🚗 の行）。出張・訪問の施設は、所在地ではなくこの地域でしぼる（Nori 2026-11-16）
    it._area = "";
    each(it.querySelectorAll(".ux-c-l"), function(r){ var i = r.querySelector("i"); if (i && i.textContent.indexOf("🚗") >= 0) it._area = r.textContent.replace("🚗", "").trim(); });
  }
  items.forEach(initItem);
  // 表示順（Nori 2026-11-25）：標準は生成時の並び（情報が多い順）。グループ（市区町村）の中だけで並べかえる
  var sortSel = id("ffSort");
  function doSort(){
    var mode = sortSel ? sortSel.value : "", seen = [], groups = [];
    items.forEach(function(it){ var p = it.parentNode; if (!p) return; var gi = seen.indexOf(p); if (gi < 0) { seen.push(p); groups.push([p, []]); gi = groups.length - 1; } groups[gi][1].push(it); });
    groups.forEach(function(g){
      var arr = g[1].slice();
      arr.sort(function(a, b){
        if (mode === "photo") { var pa = a.querySelector('img[src*="/img/fac/"]') ? 0 : 1, pb = b.querySelector('img[src*="/img/fac/"]') ? 0 : 1; if (pa !== pb) return pa - pb; }
        else if (mode === "name") { var na = at(a,"data-name") || "", nb = at(b,"data-name") || ""; if (na !== nb) return na < nb ? -1 : 1; }
        else if (mode === "priceAsc") { var ya = a._yen || 1e12, yb = b._yen || 1e12; if (ya !== yb) return ya - yb; }
        else if (mode === "priceDesc") { var za = a._yen || -1, zb = b._yen || -1; if (za !== zb) return zb - za; }
        return a._idx - b._idx;
      });
      arr.forEach(function(it){ g[0].appendChild(it); });
    });
  }
  if (sortSel) sortSel.addEventListener("change", doSort);
  var nearSel = id("ffNear");
  if (nearSel) nearSel.addEventListener("change", function(){
    geoKm = +nearSel.value || 0;
    if (geoKm && !geoPos && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(function(p){ geoPos = [p.coords.latitude, p.coords.longitude]; apply(false); }, function(){ geoKm = 0; nearSel.value = ""; apply(false); });
    }
    apply(false);
  });
  // カードのイメージ写真（無料の写真素材。本物の施設の写真ではないので「イメージ」と出し、alt は空）。となりが同じにならないよう順番に回す
  var pics = (at(box,"data-pics") || "").split("|");
  if (pics[1]) {
    var pf = pics[1].split(",");
    each(qa(".emg-item.fc[data-ffi], .ux-c.dr-card[data-ffi], .yd-card[data-ffi]"), function(c, i){
      if (c.querySelector(".ux-img")) return;
      var d = el("div", "ux-img"), im = document.createElement("img");
      im.src = pics[0] + pf[i % pf.length]; im.alt = ""; im.loading = "lazy"; d.appendChild(im); c.insertBefore(d, c.firstChild);
    });
  }
  var showUnk = false;
  // 県を選んだら、その県の施設を全部その場に出す（県のページへのリンクで逃がさない。Nori 2026-11-24）。
  // 全国のページは県ごとに数件だけなので、県ページ・市区町村ページから作った /find-data/ を読み、
  // その県のまとまりを全部のカード（市区町村ごとの見出しつき）に置きかえる。
  var fullState = {};
  function loadFull(p){
    if (!sel || fullState[p]) return;
    var sec = document.querySelector('.emg-pref[data-pref="' + p + '"]');
    if (!sec || !sec.querySelector(".fr-more") || !SLUG[p]) return;
    fullState[p] = 1;
    var note = el("p", "ff-load", "読み込んでいます…");
    sec.appendChild(note);
    fetch("/find-data/" + cat + "/" + SLUG[p] + ".json").then(function(r){ return r.json(); }).then(function(j){
      var html = (j.groups || []).map(function(g){
        return '<div class="fr ff-full">' + (g[0] ? '<h3 class="fr-h">' + g[0].replace(/[<>&"]/g, "") + "<small>" + g[1].length + unit + "</small></h3>" : "") + '<div class="fr-s">' + g[1].join("") + "</div></div>";
      }).join("");
      if (!html) { fullState[p] = 2; note.remove(); return; }
      var tpl = document.createElement("template");
      tpl.innerHTML = html;
      var kids = Array.from(sec.children), first = null, drop = [];
      kids.forEach(function(ch){
        var isNear = ch.querySelector && ch.querySelector("[data-near]");
        if ((ch.classList.contains("fr") && !isNear) || ch.classList.contains("fr-more")) { if (!first) first = ch; drop.push(ch); }
      });
      var old = [];
      drop.forEach(function(ch){ each(ch.querySelectorAll("[data-ffi]"), function(it){ old.push(it); }); });
      if (first) sec.insertBefore(tpl.content, first);
      drop.forEach(function(ch){ ch.remove(); });
      items = items.filter(function(it){ return old.indexOf(it) < 0; });
      each(sec.querySelectorAll(".ff-full [data-ffi]"), function(it){ initItem(it); items.push(it); });
      fullState[p] = 2;
      note.remove();
      apply(false);
    }).catch(function(){ fullState[p] = 2; note.remove(); });
  }
  function maybeLoad(){ places.forEach(function(p){ loadFull(p.p); }); }
  function on(){ return btns.filter(function(b){ return at(b,"aria-pressed") === "true"; }).map(function(b){ return at(b,"data-k"); }); }
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
  var geoPos = null, geoKm = 0;
  function distKm(a, b){
    var R = 6371, dLa = (b[0] - a[0]) * Math.PI / 180, dLo = (b[1] - a[1]) * Math.PI / 180;
    var h = Math.sin(dLa / 2) * Math.sin(dLa / 2) + Math.cos(a[0] * Math.PI / 180) * Math.cos(b[0] * Math.PI / 180) * Math.sin(dLo / 2) * Math.sin(dLo / 2);
    return 2 * R * Math.asin(Math.sqrt(h));
  }
  function judge(it, ks, pf, qs){
    if (geoKm && geoPos) { if (!it._ll || distKm(geoPos, it._ll) > geoKm) return 2; }
    if (!(pf && pf.length) && it._near) return 2; // 近くの県の施設（老犬ホームなど）は、その県を選んだときだけ（県を選ばないと同じ施設が2回出るため）
    var pj = placeJ(it, pf || []);
    if (pj === 2) return 2;
    if (qs && qs.split(" ").some(function(w){ return it._q.indexOf(w) < 0; })) return 2;
    if (ks.indexOf("a:cat") >= 0 && ks.indexOf("owner_live_dog") >= 0 && ks.indexOf("a:dog") < 0) return 2;
    var r = pj;
    if (cat === "sougi" && ks.indexOf("合同火葬") >= 0 && ks.indexOf("お骨を返してもらえる") >= 0 && it._no.indexOf(" 合同火葬+お骨を返してもらえる ") >= 0) return 2;
    for (var i = 0; i < ks.length; i++) {
      if (it._no.indexOf(" " + ks[i] + " ") >= 0) return 2;
      if (it._k.indexOf(" " + ks[i] + " ") >= 0) continue;
      // 犬は「犬は受けない」と書いていなければ合う
      if (ks[i] === "a:dog") continue;
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
  // Match labels are a compact explanation of the current search, not new facility claims.
  function matchLabels(it, ks, visible){
    var note = it._matchNote;
    var matched = visible ? ks.filter(function(k){
      return LBL[k] && it._k.indexOf(" " + k + " ") >= 0 && it._no.indexOf(" " + k + " ") < 0;
    }).map(function(k){ return k === "older" ? "年齢・同居条件は詳細を確認" : LBL[k]; }) : [];
    var value = matched.join("・");
    if (!value) { if (note) note.hidden = true; return; }
    if (!note) {
      var b = it.querySelector(".fc-body") || it;
      var h = b.querySelector(".fc-name,.ux-c-n,.yd-n");
      note = it._matchNote = el("p", "fc-catch");
      if (h) h.after(note); else b.appendChild(note);
    }
    note.hidden = false;
    if (note._value !== value) { note._value = value; note.textContent = "絞り込みに使った条件：" + value; }
  }
  function apply(track){
    doSort();
    var ks = on(), pf = places, qs = norm(pick && !(pick.open && pick.open()) ? pick.text() : ""), idle = needPref && !pf.length && !qs;
    var c = [0, 0];
    items.forEach(function(it){
      var j = idle ? 2 : judge(it, ks, pf, qs);
      if (j < 2) c[j]++;
      it.hidden = !(j === 0 || (j === 1 && showUnk));
      it.classList.toggle("ux-unk", j === 1);
      matchLabels(it, ks, !it.hidden);
      var note = it.querySelector(".ux-unk-n");
      if (j === 1) {
        if (!note) { note = el("p", "ux-unk-n"); var b = it.querySelector(".fc-body") || it; b.insertBefore(note, b.children[1] || null); }
        var miss = ks.filter(function(k){ return it._k.indexOf(" " + k + " ") < 0 && k !== "a:dog"; }).map(function(k){ return LBL[k]; });
        note.textContent = (placeJ(it, pf) === 1 ? "近くの地域も相談できます（来てくれる地域：" + it._area.slice(0, 40) + "）。" : "") + (miss.length ? "公式サイトに書いていない条件があります（" + miss.join("・") + "）" : "");
      } else if (note) note.remove();
    });
    // 中身のなくなったまとまり・見出しを隠す
    each(qa(".fr, .emg-pref, [data-ffg]"), function(g){
      var vis = [].some.call(g.querySelectorAll("[data-ffi]"), function(it){ return !it.hidden; });
      g.hidden = !vis;
      var h = g.previousElementSibling;
      if (h && h.hasAttribute("data-ffh")) h.hidden = !vis;
      // 地域の見出しの件数を、いま見えている数に
      var sm = g.querySelector(".fr-h small, [data-ffn]");
      if (sm) sm.textContent = [].filter.call(g.querySelectorAll("[data-ffi]"), function(it){ return !it.hidden; }).length + unit;
    });
    each(qa("[data-near-h]"), function(h){ h.hidden = !pf.length; });
    each(qa(".emg-region, .ux-region"), function(h){ h.hidden = !!(pf.length || ks.length || qs) || idle; });
    // 県が決まらないとき（位置が分からないときなど）は、空のままにせず、地方ごとの県のボタン（件数つき）を出す
    if (idle && sel && !box._pk) {
      var heads = Array.from(qa(".emg-region"));
      if (heads.length) {
        var pk = el("div", "pk"); box._pk = pk;
        heads.forEach(function(h){
          var bs = [], n = h.nextElementSibling;
          while (n && !n.classList.contains("emg-region")) {
            if (n.matches && n.matches(".emg-pref[data-pref]")) { var c = [].filter.call(n.querySelectorAll("[data-ffi]"), function(it){ return !it._near; }).length, nn = n.querySelectorAll("[data-ffi]").length - c; if (c || nn) bs.push([at(n,"data-pref"), c, nn]); }
            n = n.nextElementSibling;
          }
          if (!bs.length) return;
          var d = el("details", "pk-g"), su = el("summary", "", h.textContent), w = el("div", "pk-b");
          bs.forEach(function(x){ var b = el("button", "", x[0]); b.type = "button"; b.setAttribute("data-pk", x[0]); b.append(el("small", "", x[1] ? x[1] + unit : "近くの県")); w.append(b); });
          d.append(su, w); pk.append(d);
        });
        pk.addEventListener("click", function(ev){ var b = ev.target.closest("button[data-pk]"); if (!b) return; pick.set([{p: at(b,"data-pk")}]); box.scrollIntoView({behavior: "smooth", block: "start"}); });
        heads[0].parentNode.insertBefore(pk, heads[0]);
      }
    }
    if (box._pk) box._pk.hidden = !idle;
    // 長い一覧は、はじめの N 件だけ見せて「のこり◯件を見る」（data-ffmore="N"。中身はHTMLにあるので検索にも読める。2026-11-16 見直し）
    each(qa("[data-ffmore]"), function(g){
      var N = +at(g,"data-ffmore") || 12, vis = [].filter.call(g.querySelectorAll("[data-ffi]"), function(it){ return !it.hidden; });
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
      var k = at(b,"data-k"), n = count([k], pf, qs)[0], an = at(b,"data-g") === "a";
      b.hidden = at(b,"aria-pressed") !== "true" && !idle && (an ? !n : (!n || (n >= all0 && all0 > 3)));
    });
    each(box.querySelectorAll(".ux-r, .ux-det"), function(r){ var bs = r.querySelectorAll("button[data-k]"); if (bs.length) r.hidden = ![].some.call(bs, function(b){ return !b.hidden; }); });
    if (det) { var dn = det.querySelectorAll('button[aria-pressed="true"]').length; var sp = det.querySelector("summary span"); if (sp) sp.textContent = dn ? String(dn) : ""; }
    // まとめの行
    sum.textContent = ""; alt.textContent = "";
    if (idle) { sum.append(el("b", "", "都道府県を選ぶか、市区町村の名前を入れると並びます")); }
    else {
      sum.append(el("b", "", c[0] + unit));
      // 「どこで」と「うちの子」を分けて、飼い主さんの言い方で（Nori 2026-11-17「自分の子にあてはまるものを探してる」）
      var where = pf.map(PlacePick.label).concat(qs ? ["「" + qs + "」"] : []).filter(Boolean).join("・");
      var mine = ks.map(function(k){ return LBL[k] ? "「" + LBL[k] + "」" : ""; }).filter(Boolean).join("");
      if (where || mine) sum.append(el("small", "", (where ? where + (mine ? "で、" : "") : "") + (mine ? mine + "に合うところ（公式サイトの情報をもとに）" : "")));
      if (c[1]) {
        var cp = items.filter(function(it){ return it.classList.contains("ux-unk") && placeJ(it, pf) === 1; }).length;
        var lab = cp === c[1] ? "近くの地域も相談できる" : "条件が公式サイトに書いていない";
        var u = el("button", "ux-alt-b", showUnk ? lab + c[1] + unit + "を隠す" : lab + c[1] + unit + "も見る");
        u.type = "button"; u.onclick = function(){ showUnk = !showUnk; apply(false); };
        alt.append(u);
      }
      if (!c[0]) {
        alt.append(el("p", "ux-none", "この条件に合う" + (at(box,"data-noun") || "ところ") + "は、まだ載せていません。条件を外すと見られます。"));
        ks.forEach(function(k){
          var rest = ks.filter(function(x){ return x !== k; }), n = count(rest, pf, qs)[0];
          if (!n) return;
          var b = el("button", "ux-alt-b", "「" + LBL[k] + "」を外す（" + n + unit + "）"); b.type = "button";
          b.onclick = function(){ btns.forEach(function(x){ if (at(x,"data-k") === k) x.setAttribute("aria-pressed", "false"); }); apply(true); };
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
    // 選んでいる県のまとまりでは、県のページへのリンク（見出し）を出さない（全部その場に出すため）
    if (sel) each(qa(".emg-pref[data-pref]"), function(s){ s.classList.toggle("ff-sel", pf.some(function(p){ return p.p === at(s,"data-pref"); })); });
    maybeLoad();
    if (track && window.gtag) gtag("event", "ff_filter", {cat: cat, k: ks.join(","), pref: pf.map(function(p){ return p.p; }).join(","), places: pf.length, n: c[0]});
  }
  box.addEventListener("click", function(ev){
    var b = ev.target.closest("button[data-k]");
    if (b) {
      var was = at(b,"aria-pressed") === "true";
      // どの動物は1つだけ（犬を押したら猫は外す）
      if (at(b,"data-g") === "a") btns.forEach(function(x){ if (at(x,"data-g") === "a") x.setAttribute("aria-pressed", "false"); });
      b.setAttribute("aria-pressed", String(!was)); apply(true); return;
    }
    if (ev.target.closest("#ffGo")) { apply(false); var t = res || document.querySelector("[data-ffi]:not([hidden])"); if (t) t.scrollIntoView({behavior: "smooth", block: "start"}); }
  });
  clr.addEventListener("click", function(){ btns.forEach(function(b){ b.setAttribute("aria-pressed", "false"); }); pick.clearText(); showUnk = false; apply(true); });
  // どこで：県のボックス（いくつでも）と市区町村のボックスの2つ（/place.js。2026-11-24 Nori「県と市町村は分けた方がいい」）
  var spot = id("ffPlace"), byPref = {}, fixed = "";
  items.forEach(function(it){ if (it._p) byPref[it._p] = (byPref[it._p] || 0) + 1; });
  if (!sel) { var ks0 = Object.keys(byPref); if (ks0.length === 1) fixed = ks0[0]; }
  // 県のページ（/分野/県/）では、ほかの県・ほかの県の市区町村も候補に出し、選んだらその県のページへ移る（2026-11-24 Nori「東京とかほかの県でさがせない」）
  var curSlug = location.pathname.replace(/\/+$/, "").split("/").pop();
  var navPref = !!fixed && SLUG[fixed] === curSlug;
  var prefs = sel ? [].filter.call(sel.options, function(o){ return o.value; }).map(function(o){ return [o.value, byPref[o.value] || 0]; }) : navPref ? Object.keys(SLUG).map(function(k){ return [k, byPref[k] || 0]; }) : Object.keys(byPref).map(function(k){ return [k, byPref[k]]; });
  var tm;
  pick = PlacePick({root: spot, prefs: prefs, fixed: navPref ? "" : fixed, home: navPref ? fixed : "", unit: unit,
    ph: at(spot,"data-ph") || "都道府県・市区町村",
    cnt: function(p){ var n = 0; items.forEach(function(it){ if (placeJ(it, [p]) === 0) n++; }); return n; },
    extra: fixed ? function(t){ return []; } : null,
    typed: function(){ clearTimeout(tm); tm = setTimeout(function(){ apply(false); }, 150); },
    onChange: function(ps){
      places = ps;
      if (navPref) {
        var other = null;
        for (var i = 0; i < ps.length; i++) if (ps[i].p !== fixed) { other = ps[i]; break; }
        if (other) {
          // 選んだ場所は PlacePick が端末に覚えている（petPlaces）ので、移った先の県のページで市区町村まで引き継がれる
          var base = location.pathname.replace(/[^/]+\/?$/, ""), url = base + SLUG[other.p] + "/";
          var has = [].some.call(qa("a[href]"), function(a){ return (at(a,"href") || "").split("#")[0] === url; });
          location.href = has ? url : base + "#pref=" + encodeURIComponent(other.p);
          return;
        }
      }
      each(box.querySelectorAll(".pref-guess"), function(g){ g.remove(); });
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
