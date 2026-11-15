// 施設の一覧の「さがす箱」（共通。tools/uikit.py が /find.js に書き出す。前に prefkeep の関数が付く）。
// 箱 [data-ff]：都道府県（#ffPref、ないページもある）・市区町村や名前の入力（#ffQ）・条件のボタン（data-k）。
// 施設 [data-ffi]：data-k＝公式サイトに書いてある条件、data-q＝名前・市区町村など、data-no＝はっきり「しない」と書いてある条件。
// 書いていない条件は「書いていない（分からない）」として数え、押せば見られる。合わないと決めつけない。入れた文字は解析に送らない。
(function(){
  var box = document.querySelector("[data-ff]");
  if (!box) return;
  var cat = box.getAttribute("data-ff"), unit = box.getAttribute("data-unit") || "件";
  var sel = document.getElementById("ffPref"), q = document.getElementById("ffQ");
  var sum = document.getElementById("ffSum"), alt = document.getElementById("ffAlt"), clr = document.getElementById("ffClear");
  var res = document.getElementById("ffRes"), det = box.querySelector(".ux-det");
  var needPref = box.hasAttribute("data-needpref");
  var items = [].slice.call(document.querySelectorAll("[data-ffi]"));
  var btns = [].slice.call(box.querySelectorAll("button[data-k]"));
  var LBL = {};
  btns.forEach(function(b){ LBL[b.getAttribute("data-k")] = b.getAttribute("data-l") || b.textContent; });
  items.forEach(function(it){
    it._k = " " + (it.getAttribute("data-k") || "") + " ";
    it._no = " " + (it.getAttribute("data-no") || "") + " ";
    var p = it.closest("[data-pref]");
    it._p = it.getAttribute("data-pref") || (p ? p.getAttribute("data-pref") : "");
    it._q = (it.getAttribute("data-q") || it.textContent).toLowerCase();
  });
  var showUnk = false;
  function on(){ return btns.filter(function(b){ return b.getAttribute("aria-pressed") === "true"; }).map(function(b){ return b.getAttribute("data-k"); }); }
  function norm(s){ return (s || "").trim().toLowerCase().replace(/[\s　]+/g, " "); }
  // 1件の判定：0＝合う、1＝書いていない、2＝合わない（県・入力に合わないか、しないと書いてある）
  function judge(it, ks, pf, qs){
    if (pf && it._p !== pf) return 2;
    if (qs && qs.split(" ").some(function(w){ return it._q.indexOf(w) < 0; })) return 2;
    var r = 0;
    for (var i = 0; i < ks.length; i++) {
      if (it._k.indexOf(" " + ks[i] + " ") >= 0) continue;
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
    var ks = on(), pf = sel ? sel.value : "", qs = norm(q ? q.value : ""), idle = needPref && !pf && !qs;
    var c = [0, 0];
    items.forEach(function(it){
      var j = idle ? 2 : judge(it, ks, pf, qs);
      if (j < 2) c[j]++;
      it.hidden = !(j === 0 || (j === 1 && showUnk));
      it.classList.toggle("ux-unk", j === 1);
      var note = it.querySelector(".ux-unk-n");
      if (j === 1) {
        if (!note) { note = el("p", "ux-unk-n"); var b = it.querySelector(".fc-body") || it; b.insertBefore(note, b.children[1] || null); }
        note.textContent = "公式サイトに書いていない条件があります（" + ks.filter(function(k){ return it._k.indexOf(" " + k + " ") < 0; }).map(function(k){ return LBL[k]; }).join("・") + "）";
      } else if (note) note.remove();
    });
    // 中身のなくなったまとまり・見出しを隠す
    [].forEach.call(document.querySelectorAll(".fr, .emg-pref, [data-ffg]"), function(g){
      var vis = [].some.call(g.querySelectorAll("[data-ffi]"), function(it){ return !it.hidden; });
      g.hidden = !vis;
      var h = g.previousElementSibling;
      if (h && h.hasAttribute("data-ffh")) h.hidden = !vis;
      // 地域の見出しの件数を、いま見えている数に
      var sm = g.querySelector(".fr-h small");
      if (sm) sm.textContent = [].filter.call(g.querySelectorAll("[data-ffi]"), function(it){ return !it.hidden; }).length + unit;
    });
    [].forEach.call(document.querySelectorAll(".emg-region, .ux-region"), function(h){ h.hidden = !!(pf || ks.length || qs); });
    // 条件のボタン：いまの場所で1件もないものは隠す（押しているものは残す）
    btns.forEach(function(b){
      var k = b.getAttribute("data-k"), n = count([k], pf, qs)[0];
      b.hidden = !n && b.getAttribute("aria-pressed") !== "true" && !idle;
    });
    if (det) { var dn = det.querySelectorAll('button[aria-pressed="true"]').length; var sp = det.querySelector("summary span"); if (sp) sp.textContent = dn ? String(dn) : ""; }
    // まとめの行
    sum.textContent = ""; alt.textContent = "";
    if (idle) { sum.append(el("b", "", "都道府県を選ぶか、市区町村の名前を入れると並びます")); }
    else {
      sum.append(el("b", "", c[0] + unit));
      var cond = [pf].concat(qs ? ["「" + qs + "」"] : []).concat(ks.map(function(k){ return LBL[k]; })).filter(Boolean);
      if (cond.length) sum.append(el("small", "", cond.join("・") + (ks.length ? "が公式サイトに書いてある" : "")));
      if (c[1]) {
        var u = el("button", "ux-alt-b", showUnk ? "書いていない" + c[1] + unit + "を隠す" : "書いていない" + c[1] + unit + "も見る（分からない）");
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
        if (qs) { var n2 = count(ks, pf, "")[0]; if (n2) { var b2 = el("button", "ux-alt-b", "「" + qs + "」を外す（" + n2 + unit + "）"); b2.type = "button"; b2.onclick = function(){ q.value = ""; apply(true); }; alt.append(b2); } }
        if (pf) { var n3 = count(ks, "", qs)[0]; if (n3) { var b3 = el("button", "ux-alt-b", "全国で見る（" + n3 + unit + "）"); b3.type = "button"; b3.onclick = function(){ sel.value = ""; sel.dispatchEvent(new Event("change")); }; alt.append(b3); } }
      }
    }
    clr.hidden = !(ks.length || qs);
    box.classList.toggle("ux-busy", !!(ks.length || qs || pf));
    if (track && window.gtag) gtag("event", "ff_filter", {cat: cat, k: ks.join(","), pref: pf, n: c[0]});
  }
  box.addEventListener("click", function(ev){
    var b = ev.target.closest("button[data-k]");
    if (b) { b.setAttribute("aria-pressed", String(b.getAttribute("aria-pressed") !== "true")); apply(true); return; }
    if (ev.target.closest("#ffGo")) { apply(false); var t = res || document.querySelector("[data-ffi]:not([hidden])"); if (t) t.scrollIntoView({behavior: "smooth", block: "start"}); }
  });
  clr.addEventListener("click", function(){ btns.forEach(function(b){ b.setAttribute("aria-pressed", "false"); }); if (q) q.value = ""; showUnk = false; apply(true); });
  if (q) { var tm; q.addEventListener("input", function(){ clearTimeout(tm); tm = setTimeout(function(){ apply(false); }, 150); }); }
  if (!sel) prefLinks(prefGet());
  if (sel) { prefKeep(sel, function(){ apply(false); }); if (!sel.value && box.hasAttribute("data-guess")) prefGuess(sel, function(){ apply(false); }); }
  apply(false);
})();
