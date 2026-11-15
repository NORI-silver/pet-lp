// 「うちの子に合うところをさがす」（施設の一覧）。手書き。カードと選ぶ欄は tools/faccard.py が作る。
// カードの data-fit（公式サイトに書いてあること）とくらべて「この子OK／要確認／合わないかも」と理由を出し、合う順に並べかえる。
// 書いていないことは「要確認」（受けないという意味ではない）。選んだ内容はこの端末にだけ覚える（petMine）。外には送らない（解析には種類だけ）。
(function(){
  var box = document.querySelector("[data-fp]");
  if (!box) return;
  var L = {dog: "犬", cat: "猫", small: "うさぎ・小動物", bird: "鳥", exotic: "爬虫類など"};
  var SZ = [["s", 0, 10], ["m", 10, 25], ["l", 25, 200]];
  var cards = [].slice.call(document.querySelectorAll(".emg-item.fc"));
  cards.forEach(function(c, i){ c._ord = i; c._ft = "|" + (c.getAttribute("data-ft") || "") + "|"; try { c._fit = JSON.parse(c.getAttribute("data-fit") || "{}"); } catch (e) { c._fit = {}; } });
  var sel = box.querySelector("#fp-size"), dogRow = box.querySelector(".fp-dog"), now = box.querySelector(".fp-now"), hide = box.querySelector(".fp-hide input");
  var st = {a: "", size: "", x: []}, ftOn = [];
  try { var sv = JSON.parse(localStorage.getItem("petMine") || "null"); if (sv) st = {a: sv.a || "", size: sv.size || "", x: sv.x || []}; } catch (e) {}
  function save(){ try { localStorage.setItem("petMine", JSON.stringify(st)); } catch (e) {} }
  function kg(){
    if (!sel || !st.size) return null;
    var o = sel.querySelector('option[value="' + st.size + '"]');
    return o ? [parseFloat(o.getAttribute("data-lo")), parseFloat(o.getAttribute("data-hi")), o.textContent] : null;
  }
  function judge(f, w){
    var r = [];
    if (st.a) {
      if (f.a && f.a.indexOf(st.a) >= 0) r.push(["ok", L[st.a] + "OK"]);
      else if (f.a && f.o) r.push(["ng", "診る・受ける動物は" + (f.at || f.a.map(function(k){ return L[k]; }).join("・"))]);
      else r.push(["unk", L[st.a] + "は書いていない"]);
    }
    var dogOk = !st.a || st.a === "dog";
    if (w && dogOk && !(f.a && f.o && f.a.indexOf("dog") < 0)) {
      var lo = w[0], hi = w[1];
      if (f.kg) {
        if (lo >= f.kg) r.push(["ng", f.kg + "kgまで"]);
        else if (hi <= f.kg) r.push(["ok", f.kg + "kgまでOK"]);
        else r.push(["unk", f.kg + "kgまで。体重を確かめて"]);
      } else if (f.s) {
        var need = SZ.filter(function(z){ return lo < z[2] && z[1] < hi; }).map(function(z){ return z[0]; });
        var all = need.every(function(k){ return f.s.indexOf(k) >= 0; }), some = need.some(function(k){ return f.s.indexOf(k) >= 0; });
        if (all) r.push(["ok", need.indexOf("l") >= 0 ? "大型犬もOK" : "この大きさOK"]);
        else if (!some) r.push(["ng", f.s.join("") === "s" ? "小型犬だけ" : "この大きさは受けない"]);
        else r.push(["unk", "大きさで受けないことあり"]);
      } else r.push(["unk", "大きさは書いていない"]);
    }
    if (st.x.indexOf("sen") >= 0) r.push(f.sen ? ["ok", "シニアOK"] : ["unk", "シニアは書いていない"]);
    if (st.x.indexOf("pup") >= 0) r.push(f.pup ? ["ok", "子犬OK"] : ["unk", "子犬は書いていない"]);
    return r;
  }
  var RANK = {ok: 0, unk: 1, ng: 2};
  function run(track){
    box.querySelectorAll(".fp-btns button").forEach(function(b){
      var g = b.parentNode.getAttribute("data-g"), v = b.getAttribute("data-v");
      b.setAttribute("aria-pressed", String(g === "a" ? st.a === v : g === "f" ? ftOn.indexOf(v) >= 0 : st.x.indexOf(v) >= 0));
    });
    if (sel) sel.value = st.size;
    if (dogRow) dogRow.hidden = !!st.a && st.a !== "dog";
    var w = kg(), any = !!(st.a || w || st.x.length), cnt = {ok: 0, unk: 0, ng: 0};
    cards.forEach(function(c){
      var p = c.querySelector(".fc-fit"), r = any ? judge(c._fit, w) : [];
      var s = !r.length ? "" : r.some(function(x){ return x[0] === "ng"; }) ? "ng" : r.every(function(x){ return x[0] === "ok"; }) ? "ok" : "unk";
      c._rank = s ? RANK[s] : 1;
      c.classList.toggle("fc-ng", s === "ng");
      c.classList.toggle("fc-hid", s === "ng" && hide && hide.checked);
      c.classList.toggle("fc-off", !ftOn.every(function(v){ return c._ft.indexOf("|" + v + "|") >= 0; }));
      if (!p) return;
      if (!s) { p.hidden = true; return; }
      var lab = {ok: "この子OK", unk: "要確認", ng: "合わないかも"}[s];
      var why = r.filter(function(x){ return s === "ok" || x[0] !== "ok"; }).map(function(x){ return x[1]; });
      p.className = "fc-fit " + s; p.hidden = false; p.textContent = "";
      p.appendChild(document.createTextNode((s === "ok" ? "✓ " : s === "ng" ? "× " : "？ ") + lab));
      var sm = document.createElement("small"); sm.textContent = why.join("・"); p.appendChild(sm);
      if (!c.classList.contains("fc-off") && (c.offsetParent || c.classList.contains("fc-hid"))) cnt[s]++;
    });
    // 合う順に並べかえる（同じなら元の順）。選ぶのをやめたら元の順に戻す
    var parents = [];
    cards.forEach(function(c){ if (parents.indexOf(c.parentNode) < 0) parents.push(c.parentNode); });
    parents.forEach(function(par){
      var cs = cards.filter(function(c){ return c.parentNode === par; });
      var anchor = cs[cs.length - 1].nextSibling;
      cs.slice().sort(function(a, b){ return (any ? a._rank - b._rank : 0) || a._ord - b._ord; }).forEach(function(c){ par.insertBefore(c, anchor); });
    });
    heads();
    now.textContent = "";
    if (any) {
      var b1 = document.createElement("b"); b1.textContent = "OK " + cnt.ok + "件";
      now.append(b1, "・要確認 " + cnt.unk + "・合わないかも " + cnt.ng + "（合う順）");
    } else if (ftOn.length) {
      var n = cards.filter(function(c){ return !c.classList.contains("fc-off") && (c.offsetParent || !c.closest(".emg-pref[hidden]")); }).length;
      var b2 = document.createElement("b"); b2.textContent = n + "件"; now.append(b2, "（カードに書いてあることで判定）");
    }
    save();
    if (track && window.gtag) gtag("event", "fit_filter", {a: st.a || "", size: st.size || "", x: st.x.join(","), f: ftOn.join(",")});
  }
  // しぼって1件もなくなった地域は、見出しごと隠す
  function heads(){
    [].forEach.call(document.querySelectorAll(".fr"), function(r){
      var vis = [].some.call(r.querySelectorAll(".emg-item.fc"), function(c){ return !c.hidden && !/\b(fac-off|fc-hid|fc-off)\b/.test(c.className); });
      r.classList.toggle("fr-empty", !vis);
      var h = r.previousElementSibling;
      if (h && /^H[2-4]$/.test(h.tagName) && h.nextElementSibling === r) h.classList.toggle("fr-empty", !vis);
    });
  }
  box.addEventListener("input", function(){ setTimeout(heads, 0); });
  box.addEventListener("click", function(ev){
    setTimeout(heads, 0);
    var b = ev.target.closest(".fp-btns button"); if (!b) return;
    var g = b.parentNode.getAttribute("data-g"), v = b.getAttribute("data-v");
    if (g === "a") st.a = st.a === v ? "" : v;
    else if (g === "f") { var j = ftOn.indexOf(v); if (j >= 0) ftOn.splice(j, 1); else ftOn.push(v); }
    else { var i = st.x.indexOf(v); if (i >= 0) st.x.splice(i, 1); else st.x.push(v); }
    run(true);
  });
  if (sel) sel.addEventListener("change", function(){ st.size = sel.value; run(true); });
  if (hide) hide.addEventListener("change", function(){ run(false); });
  // 都道府県を切りかえたら数え直す
  document.addEventListener("change", function(ev){ if (ev.target.tagName === "SELECT" && ev.target !== sel) setTimeout(function(){ run(false); }, 0); });
  // 前に選んだ内容がこのページの欄にないときは外す
  if (st.a && !box.querySelector('[data-g="a"] [data-v="' + st.a + '"]')) st.a = "";
  if (st.size && !(sel && sel.querySelector('option[value="' + st.size + '"]'))) st.size = "";
  st.x = st.x.filter(function(v){ return box.querySelector('[data-g="x"] [data-v="' + v + '"]'); });
  run(false);
})();
