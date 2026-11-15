// 「うちの子に合うところをさがす」（施設の一覧）。手書き。カードと選ぶ欄は tools/faccard.py が作る。
// カードの data-fit（公式サイトに書いてあること）とくらべて「この子OK／要確認／合わないかも」と理由を出し、合う順に並べかえる。
// 書いていないことは「要確認」（受けないという意味ではない）。選んだ内容はこの端末にだけ覚える（petMine）。外には送らない（解析には種類だけ）。
(function(){
  var box = document.querySelector("[data-fp]");
  if (!box) return;
  var L = {dog: "犬", cat: "猫", small: "うさぎ・小動物", bird: "鳥", exotic: "爬虫類など"};
  var SZ = [["s", 0, 10], ["m", 10, 25], ["l", 25, 200]];
  var cards = [].slice.call(document.querySelectorAll(".emg-item.fc"));
  cards.forEach(function(c, i){ c._ord = i; try { c._fit = JSON.parse(c.getAttribute("data-fit") || "{}"); } catch (e) { c._fit = {}; } });
  var sel = box.querySelector("#fp-size"), dogRow = box.querySelector(".fp-dog"), now = box.querySelector(".fp-now"), hide = box.querySelector(".fp-hide input");
  var st = {a: "", size: "", x: []};
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
      if (f.a && f.a.indexOf(st.a) >= 0) r.push(["ok", L[st.a] + "OKと公式サイトに書いてあります"]);
      else if (f.a && f.o) r.push(["ng", "公式サイトに書いてある動物は「" + (f.at || f.a.map(function(k){ return L[k]; }).join("・")) + "」です"]);
      else r.push(["unk", L[st.a] + "を受けるかは公式サイトに書いていません"]);
    }
    var dogOk = !st.a || st.a === "dog";
    if (w && dogOk && !(f.a && f.o && f.a.indexOf("dog") < 0)) {
      var lo = w[0], hi = w[1];
      if (f.kg) {
        if (lo >= f.kg) r.push(["ng", f.kg + "kgまでと公式サイトに書いてあります"]);
        else if (hi <= f.kg) r.push(["ok", f.kg + "kgまで受けると書いてあります"]);
        else r.push(["unk", f.kg + "kgまでと書いてあります。体重を確かめてください"]);
      } else if (f.s) {
        var need = SZ.filter(function(z){ return lo < z[2] && z[1] < hi; }).map(function(z){ return z[0]; });
        var all = need.every(function(k){ return f.s.indexOf(k) >= 0; }), some = need.some(function(k){ return f.s.indexOf(k) >= 0; });
        if (all) r.push(["ok", need.indexOf("l") >= 0 ? "大型犬も受けると書いてあります" : "この大きさの犬を受けると書いてあります"]);
        else if (!some) r.push(["ng", f.s.join("") === "s" ? "小型犬だけと公式サイトに書いてあります" : "この大きさは受けないと書いてあります"]);
        else r.push(["unk", "大きさによって受けられないことがあります"]);
      } else r.push(["unk", "大きさの決まりは公式サイトに書いていません"]);
    }
    if (st.x.indexOf("sen") >= 0) r.push(f.sen ? ["ok", "シニア・介護の子を受けると書いてあります"] : ["unk", "シニア・介護の子のことは書いていません"]);
    if (st.x.indexOf("pup") >= 0) r.push(f.pup ? ["ok", "子犬のクラス・幼稚園があると書いてあります"] : ["unk", "子犬向けのことは書いていません"]);
    return r;
  }
  var RANK = {ok: 0, unk: 1, ng: 2};
  function run(track){
    box.querySelectorAll(".fp-btns button").forEach(function(b){
      var g = b.parentNode.getAttribute("data-g"), v = b.getAttribute("data-v");
      b.setAttribute("aria-pressed", String(g === "a" ? st.a === v : st.x.indexOf(v) >= 0));
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
      if (!p) return;
      if (!s) { p.hidden = true; return; }
      var lab = {ok: "この子OK", unk: "要確認", ng: "合わないかも"}[s];
      var why = r.filter(function(x){ return s === "ok" || x[0] !== "ok"; }).map(function(x){ return x[1]; });
      p.className = "fc-fit " + s; p.hidden = false; p.textContent = "";
      p.appendChild(document.createTextNode((s === "ok" ? "✓ " : s === "ng" ? "× " : "？ ") + lab));
      var sm = document.createElement("small"); sm.textContent = why.join("・"); p.appendChild(sm);
      if (c.offsetParent || c.classList.contains("fc-hid")) cnt[s]++;
    });
    // 合う順に並べかえる（同じなら元の順）。選ぶのをやめたら元の順に戻す
    var parents = [];
    cards.forEach(function(c){ if (parents.indexOf(c.parentNode) < 0) parents.push(c.parentNode); });
    parents.forEach(function(par){
      var cs = cards.filter(function(c){ return c.parentNode === par; });
      var anchor = cs[cs.length - 1].nextSibling;
      cs.slice().sort(function(a, b){ return (any ? a._rank - b._rank : 0) || a._ord - b._ord; }).forEach(function(c){ par.insertBefore(c, anchor); });
    });
    now.textContent = "";
    if (any) {
      var b1 = document.createElement("b"); b1.textContent = "この子OK " + cnt.ok + "件";
      now.append(b1, "・要確認 " + cnt.unk + "件・合わないかも " + cnt.ng + "件（合う順に並べました）");
    }
    save();
    if (track && window.gtag) gtag("event", "fit_filter", {a: st.a || "", size: st.size || "", x: st.x.join(",")});
  }
  box.addEventListener("click", function(ev){
    var b = ev.target.closest(".fp-btns button"); if (!b) return;
    var g = b.parentNode.getAttribute("data-g"), v = b.getAttribute("data-v");
    if (g === "a") st.a = st.a === v ? "" : v;
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
