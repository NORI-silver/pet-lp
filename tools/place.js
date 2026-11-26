// 「どこで探しますか？」の入力（共通。tools/uikit.py が /place.js に書き出す。2026-11-16 Nori「県とか複数選択」「市町村とかサジェスト」）。
// 県のボックスと市区町村のボックスの2つに分ける（2026-11-24 Nori「県と市町村は分けた方がいいんじゃない。ボックス。」）。
// 県はいくつでも選べる。市区町村は、県が選ばれていればその県のものだけ、選ばれていなければ全国から候補を出し、選ぶとその県も選んだことになる。
// 候補は自前のデータだけ（都道府県47・市区町村の一覧 /place-data.json・ページが渡す駅や区）。有料のサービスは使わない。入れた文字は解析に送らない。
(function(){
var PN = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"];
var KEY = "petPlaces", MUNI = null, MUNI_P = null;
function kana(s){ return String(s || "").replace(/[ァ-ヶ]/g, function(c){ return String.fromCharCode(c.charCodeAt(0) - 96); }); }
function norm(s){ return kana(String(s || "").trim().toLowerCase().replace(/[\s　]+/g, "")); }
function el(t, c, x){ var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
function css(){
  if (document.getElementById("ppcss")) return;
  var s = el("style"); s.id = "ppcss";
  s.textContent = ".pp-root{flex:1 1 100%;min-width:0;width:100%}.pp{position:relative;flex:1 1 100%;min-width:0}"
  + ".pp2{display:flex;flex-direction:column;gap:6px;width:100%}.pp-f{position:relative;min-width:0}"
  + ".pp-box{display:flex;flex-wrap:wrap;align-items:center;gap:5px;border:1px solid #d9c9bb;border-radius:12px;background:#fff;padding:6px 8px;min-height:46px;cursor:text}"
  + ".pp-box:focus-within{border-color:#e8590c;box-shadow:0 0 0 3px rgba(232,89,12,.12)}"
  + ".pp-chip{display:inline-flex;align-items:center;gap:2px;background:#fff1e6;color:#a8410a;border:1px solid #f6c9a8!important;border-radius:999px!important;padding:5px 4px 5px 11px!important;font-size:.88rem!important;font-weight:700;line-height:1.2;cursor:pointer}"
  + ".pp-pick{width:100%;min-height:46px;border:1px solid #d9c9bb;border-radius:12px;padding:8px 12px;background:#fff;color:#2b2622;font:inherit;cursor:pointer}.pp-pref:has(.pp-pick) .pp-box{min-height:0;padding:0;border:0;background:none;box-shadow:none}.pp-pref .pp-box:has(.pp-chip){margin-bottom:5px}"
  + ".pp-chip b{font-weight:400;font-size:1rem;line-height:1;padding:0 5px;color:#c06a35}"
  + ".pp-lock{cursor:default;padding-right:11px!important}"
  + ".pp-in{flex:1 1 7em;min-width:6em;border:0!important;outline:0;padding:6px 2px!important;font-size:.98rem!important;background:transparent;box-shadow:none!important}"
  + ".pp-s{position:absolute;left:0;right:0;top:calc(100% + 4px);z-index:30;margin:0;padding:4px;list-style:none;background:#fff;border:1px solid #e3d3c6;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.12);max-height:60vh;overflow:auto}"
  + ".pp-s[hidden]{display:none}"
  + ".pp-s li{display:flex;justify-content:space-between;gap:8px;padding:10px 10px;border-radius:8px;font-size:.95rem;color:#2b2622;cursor:pointer}"
  + ".pp-s li[aria-selected=true],.pp-s li:hover{background:#fff4ec}"
  + ".pp-s li small{color:#6b5f56;font-size:.78rem;white-space:nowrap;align-self:center}"
  + ".pp-s li.pp-h{cursor:default;background:none;font-size:.76rem;color:#7a6a5e;font-weight:700;padding:6px 10px 2px}";
  document.head.appendChild(s);
}
function loadMuni(cb){
  if (MUNI) return cb();
  if (MUNI_P) return MUNI_P.push(cb);
  MUNI_P = [cb];
  fetch("/place-data.json").then(function(r){ return r.json(); }).then(function(d){ MUNI = d; }).catch(function(){ MUNI = []; })
  .then(function(){ var q = MUNI_P; MUNI_P = null; q.forEach(function(f){ f(); }); });
}
// 場所の文字（札の表示・保存用）
function label(p){ return p.c || p.s || p.p; }
function same(a, b){ return a.p === b.p && (a.c || "") === (b.c || "") && (a.s || "") === (b.s || ""); }
// opts：root（入れる場所）・prefs（選べる県 [[名前, 件数]]。件数0の県も出す）・extra(q)＝市区町村のボックスだけの候補 [{p, c|s, n}]・
// cnt(place)＝その場所の件数（なければ出さない）・onChange(places)・ph（文字の見本。「都道府県・」で始まれば県の分を分ける）・
// fixed（県が決まっているページの県。県のボックスはその県に固定）・home（県のページの県。県のボックスの最初の値。端末への保存・onChange はしない）
window.PlacePick = function(opts){
  css();
  var places = opts.home ? [{p: opts.home}] : [], uid = "pp" + Math.random().toString(36).slice(2, 7);
  var phAll = opts.ph || "都道府県・市区町村", phCity = phAll.replace(/^都道府県・/, "");
  var wrap = el("div", "pp pp2");
  opts.root.appendChild(wrap);
  function save(){ try { localStorage.setItem(KEY, JSON.stringify(places.slice(0, 8))); } catch (x) {} }
  function changed(){ paint(); save(); opts.onChange(places.slice()); }
  function add(p){
    // 県をまるごと選んだら、その県の市区町村の札は外す。市区町村を選んだら、その県まるごとの札は外す
    places = places.filter(function(x){ return !same(x, p) && !(!p.c && !p.s && x.p === p.p) && !((p.c || p.s) && x.p === p.p && !x.c && !x.s); });
    if (opts.fixed && p.p !== opts.fixed) return;
    places.push(p); changed();
  }
  function activePrefs(){ var out = []; places.forEach(function(p){ if (out.indexOf(p.p) < 0) out.push(p.p); }); return out; }
  // 県のボックスに出す札：県まるごとの札と、市区町村から決まった県（押すとその県の場所を全部外す）
  function prefEntries(){
    var out = [];
    places.forEach(function(p){
      if (out.some(function(e){ return e.p === p.p; })) return;
      out.push({p: p.p, own: !p.c && !p.s});
    });
    return out;
  }
  function makeField(kind){
    var f = {kind: kind, act: -1, cur: []};
    var fw = el("div", kind === "pref" ? "pp-f pp-pref" : "pp-f pp-city"), bx = el("div", "pp-box"), ul = el("ul", "pp-s");
    f.bx = bx; f.ul = ul;
    ul.id = uid + kind; ul.setAttribute("role", "listbox"); ul.hidden = true;
    if (kind === "pref" && opts.fixed) {
      var lk = el("span", "pp-chip pp-lock", opts.fixed); bx.appendChild(lk); fw.append(bx);
      f.inp = null;
    } else if (kind === "pref") {
      var menu = el("select", "pp-pick");
      menu.setAttribute("aria-label", "都道府県を選ぶ");
      menu.appendChild(el("option"));
      menu.options[0].value = "";
      menu.options[0].disabled = true;
      var rows = opts.prefs || [];
      PN.forEach(function(p){
        var row = rows.find(function(x){ return x[0] === p; });
        if (row) { var o = el("option", "", p); o.value = p; menu.appendChild(o); }
      });
      menu.addEventListener("change", function(){
        var p = menu.value;
        if (p) { if (opts.home && p !== opts.home) places = []; add({p: p}); }
      });
      f.menu = menu;
      fw.append(bx, menu);
    } else {
      var inp = el("input", "pp-in");
      inp.type = "search"; inp.autocomplete = "off"; inp.setAttribute("enterkeyhint", "search");
      inp.setAttribute("role", "combobox"); inp.setAttribute("aria-autocomplete", "list"); inp.setAttribute("aria-expanded", "false");
      inp.setAttribute("aria-controls", ul.id);
      inp.placeholder = phCity;
      inp.setAttribute("aria-label", phCity);
      f.inp = inp; bx.appendChild(inp);
      fw.append(bx, ul);
      bx.addEventListener("click", function(ev){ if (!ev.target.closest(".pp-chip")) inp.focus(); });
      ul.addEventListener("mousedown", function(ev){ ev.preventDefault(); });
      ul.addEventListener("click", function(ev){ var li = ev.target.closest("li[role=option]"); if (li) pick(f, +li.getAttribute("data-i")); });
      inp.addEventListener("focus", function(){ if (kind === "city") loadMuni(function(){}); show(f); });
      inp.addEventListener("input", function(){ show(f); if (opts.typed) opts.typed(inp.value); });
      inp.addEventListener("blur", function(){ setTimeout(function(){ close(f); }, 150); });
      inp.addEventListener("keydown", function(ev){
        if (ev.key === "ArrowDown") { f.act = Math.min(f.act + 1, f.cur.length - 1); mark(f); ev.preventDefault(); }
        else if (ev.key === "ArrowUp") { f.act = Math.max(f.act - 1, 0); mark(f); ev.preventDefault(); }
        else if (ev.key === "Enter") { if (!ul.hidden && f.act >= 0) { pick(f, f.act); ev.preventDefault(); } else { close(f); inp.blur(); } }
        else if (ev.key === "Escape") close(f);
        else if (ev.key === "Backspace" && !inp.value) backChip(f);
      });
    }
    bx.addEventListener("click", function(ev){
      var c = ev.target.closest(".pp-chip"); if (!c || c.classList.contains("pp-lock")) return;
      if (kind === "pref") removePref(c.getAttribute("data-p"), c.getAttribute("data-own") === "1");
      else removePlace(+c.getAttribute("data-i"));
      if (f.inp) f.inp.focus(); else if (f.menu) f.menu.focus();
    });
    wrap.appendChild(fw);
    return f;
  }
  var fPref = makeField("pref"), fCity = makeField("city");
  function paint(){
    // 県のボックス
    [].slice.call(fPref.bx.querySelectorAll(".pp-chip:not(.pp-lock)")).forEach(function(c){ c.remove(); });
    if (!opts.fixed) {
      prefEntries().forEach(function(e){
        var c = el("button", "pp-chip"); c.type = "button"; c.setAttribute("data-p", e.p); c.setAttribute("data-own", e.own ? "1" : "");
        c.setAttribute("aria-label", e.p + "を外す"); c.append(document.createTextNode(e.p), el("b", "", "×"));
        fPref.bx.appendChild(c);
      });
      fPref.menu.options[0].textContent = places.length ? "＋ほかの都道府県を選ぶ" : "都道府県を選ぶ";
      fPref.menu.selectedIndex = 0;
    }
    // 市区町村のボックス
    [].slice.call(fCity.bx.querySelectorAll(".pp-chip")).forEach(function(c){ c.remove(); });
    var hasCity = false;
    places.forEach(function(p, i){
      if (!p.c && !p.s) return;
      hasCity = true;
      var c = el("button", "pp-chip"); c.type = "button"; c.setAttribute("data-i", i);
      c.setAttribute("aria-label", label(p) + "を外す"); c.append(document.createTextNode(label(p)), el("b", "", "×"));
      fCity.bx.insertBefore(c, fCity.inp);
    });
    fCity.inp.placeholder = hasCity ? "＋ほかの場所も" : phCity;
  }
  function removePlace(i){ places.splice(i, 1); changed(); }
  function removePref(pf, own){
    places = places.filter(function(x){ return own ? !(x.p === pf && !x.c && !x.s) : x.p !== pf; });
    changed();
  }
  function backChip(f){
    if (f.kind === "city") { for (var i = places.length - 1; i >= 0; i--) if (places[i].c || places[i].s) { removePlace(i); return; } }
  }
  function hide(f){ f.ul.hidden = true; if (f.inp) f.inp.setAttribute("aria-expanded", "false"); f.act = -1; }
  function close(f){ var o = !f.ul.hidden; hide(f); if (o && f.inp && f.inp.value && opts.typed) opts.typed(f.inp.value); }
  function mark(f){ [].forEach.call(f.ul.querySelectorAll("li[role=option]"), function(li, i){ li.setAttribute("aria-selected", i === f.act ? "true" : "false"); }); if (f.inp) f.inp.setAttribute("aria-activedescendant", f.act >= 0 ? f.ul.id + "-" + f.act : ""); }
  function pick(f, i){ var x = f.cur[i]; if (!x) return; f.inp.value = ""; hide(f); add(x[0]); if (opts.typed) opts.typed(""); }
  function show(f){
    var inp = f.inp; if (!inp) return;
    var t = norm(inp.value), out = [], seen = {};
    function push(p, sub){ var k = p.p + "|" + (p.c || "") + "|" + (p.s || ""); if (seen[k] || places.some(function(x){ return same(x, p); })) return; seen[k] = 1; out.push([p, sub]); }
    var head = function(s){ return s.indexOf(t) === 0; };
      var act = activePrefs();
      var okPf = function(pf){
        if (opts.fixed) return pf === opts.fixed;
        if (opts.prefOk && !opts.prefOk(pf)) return false;
        return !act.length || act.indexOf(pf) >= 0;
      };
      var ex = opts.extra ? opts.extra(t) : [];
      ex.forEach(function(x){ if (okPf(x.p)) push(x, (x.c && x.c.indexOf("（") < 0 ? x.p : "") + (x.n ? "・" + x.n + (opts.unit || "件") : "")); });
      if (t) {
        (MUNI || []).forEach(function(m){
          if (out.length > 40) return;
          var pf = PN[m[2]];
          if (!okPf(pf)) return;
          var nm = norm(m[0]), kn = m[1];
          if (head(nm) || head(kn) || head(kn.replace(/(し|く|ちょう|まち|そん|むら)$/, "")) || (t.length >= 2 && nm.indexOf(t) >= 0)) {
            var n = opts.cnt ? opts.cnt({p: pf, c: m[0]}) : null;
            push({p: pf, c: m[0]}, pf + (n ? "・" + n + (opts.unit || "件") : ""));
          }
        });
        if (!MUNI) loadMuni(function(){ if (document.activeElement === inp) show(f); });
      }
    f.cur = out.slice(0, 10); f.ul.textContent = "";
    if (!f.cur.length) {
      if (t) { var li = el("li", "pp-h", "候補が見つかりません。市区町村の名前で入れてください"); f.ul.append(li); f.ul.hidden = false; }
      else hide(f);
      return;
    }
    if (!t) f.ul.append(el("li", "pp-h", "この中の場所でしぼる"));
    f.cur.forEach(function(x, i){
      var li = el("li"); li.setAttribute("role", "option"); li.setAttribute("data-i", i); li.id = f.ul.id + "-" + i;
      li.append(el("span", "", label(x[0])), el("small", "", x[1] || ""));
      f.ul.append(li);
    });
    f.act = t ? 0 : -1; mark(f); f.ul.hidden = false; inp.setAttribute("aria-expanded", "true");
  }
  paint();
  return {
    get: function(){ return places.slice(); },
    text: function(){ return [fPref.inp, fCity.inp].map(function(i){ return i ? i.value.trim() : ""; }).filter(Boolean).join(" "); },
    open: function(){ return [fPref, fCity].some(function(f){ return !f.ul.hidden && f.cur.length > 0; }); },
    clearText: function(){ [fPref.inp, fCity.inp].forEach(function(i){ if (i) i.value = ""; }); },
    set: function(ps, quiet){ places = (ps || []).filter(function(p){ return p && p.p && (!opts.fixed || p.p === opts.fixed); }); paint(); if (!quiet) { save(); opts.onChange(places.slice()); } },
    saved: function(){ try { return JSON.parse(localStorage.getItem(KEY) || "[]") || []; } catch (x) { return []; } },
    input: fPref.inp || fCity.inp
  };
};
window.PlacePick.label = label;
// ページに施設用の絞り込みがない場合も、同じ分野の全国検索へ移れる。
document.querySelectorAll("[data-pref-nav]").forEach(function(root){
  css();
  var menu = el("select", "pp-pick");
  menu.setAttribute("aria-label", "都道府県を選ぶ");
  var placeholder = el("option", "", "都道府県を選ぶ");
  placeholder.value = ""; placeholder.disabled = true; menu.appendChild(placeholder);
  PN.forEach(function(p){ var o = el("option", "", p); o.value = p; menu.appendChild(o); });
  menu.selectedIndex = 0;
  menu.addEventListener("change", function(){
    if (!menu.value) return;
    try { localStorage.setItem(KEY, JSON.stringify([{p: menu.value}])); } catch (x) {}
    location.href = "/" + root.dataset.prefNav + "/#pref=" + encodeURIComponent(menu.value);
  });
  root.appendChild(menu);
});

// 県庁所在地の近い県（結果が少ないときに近くの県も出すため）
var LL = __LL__;
window.PlacePick.near = function(pf, n){
  var i = PN.indexOf(pf); if (i < 0) return [];
  var a = LL[i], d = LL.map(function(b, j){ var dx = (a[1] - b[1]) * Math.cos(a[0] * Math.PI / 180), dy = a[0] - b[0]; return [dx * dx + dy * dy, PN[j]]; });
  d.sort(function(x, y){ return x[0] - y[0]; });
  return d.slice(1, (n || 3) + 1).map(function(x){ return x[1]; });
};
})();

