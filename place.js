// 生成：tools/uikit.py（元は tools/place.js）
// 「どこで探しますか？」の入力（共通。tools/uikit.py が /place.js に書き出す。2026-11-16 Nori「県とか複数選択」「市町村とかサジェスト」）。
// 1つの入力に、都道府県・市区町村（と、ページが渡せば駅名）の候補を出す。選んだ場所は小さな札になり、いくつでも足せる（どれかに合えば出す）。
// 候補は自前のデータだけ（都道府県47・市区町村の一覧 /place-data.json・ページの施設に書いてある地名）。有料のサービスは使わない。入れた文字は解析に送らない。
(function(){
var PN = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"];
var PK = "ほっかいどう,あおもり,いわて,みやぎ,あきた,やまがた,ふくしま,いばらき,とちぎ,ぐんま,さいたま,ちば,とうきょう,かながわ,にいがた,とやま,いしかわ,ふくい,やまなし,ながの,ぎふ,しずおか,あいち,みえ,しが,きょうと,おおさか,ひょうご,なら,わかやま,とっとり,しまね,おかやま,ひろしま,やまぐち,とくしま,かがわ,えひめ,こうち,ふくおか,さが,ながさき,くまもと,おおいた,みやざき,かごしま,おきなわ".split(",");
var KEY = "petPlaces", MUNI = null, MUNI_P = null;
function kana(s){ return String(s || "").replace(/[ァ-ヶ]/g, function(c){ return String.fromCharCode(c.charCodeAt(0) - 96); }); }
function norm(s){ return kana(String(s || "").trim().toLowerCase().replace(/[\s　]+/g, "")); }
function el(t, c, x){ var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
function css(){
  if (document.getElementById("ppcss")) return;
  var s = el("style"); s.id = "ppcss";
  s.textContent = ".pp-root{flex:1 1 100%;min-width:0;width:100%}.pp{position:relative;flex:1 1 100%;min-width:0}"
  + ".pp-box{display:flex;flex-wrap:wrap;align-items:center;gap:5px;border:1px solid #d9c9bb;border-radius:12px;background:#fff;padding:6px 8px;min-height:46px;cursor:text}"
  + ".pp-box:focus-within{border-color:#e8590c;box-shadow:0 0 0 3px rgba(232,89,12,.12)}"
  + ".pp-chip{display:inline-flex;align-items:center;gap:2px;background:#fff1e6;color:#a8410a;border:1px solid #f6c9a8!important;border-radius:999px!important;padding:5px 4px 5px 11px!important;font-size:.88rem!important;font-weight:700;line-height:1.2;cursor:pointer}"
  + ".pp-chip b{font-weight:400;font-size:1rem;line-height:1;padding:0 5px;color:#c06a35}"
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
// opts：root（入れる場所）・prefs（選べる県 [[名前, 件数]]。件数0の県も出す）・extra(q)＝ページだけの候補 [{p, c|s, n}]・
// cnt(place)＝その場所の件数（なければ出さない）・onChange(places)・ph（文字の見本）・fixed（県が決まっているページの県）
window.PlacePick = function(opts){
  css();
  var places = [], act = -1, cur = [];
  var wrap = el("div", "pp"), bx = el("div", "pp-box"), inp = el("input", "pp-in"), ul = el("ul", "pp-s");
  inp.type = "search"; inp.autocomplete = "off"; inp.setAttribute("enterkeyhint", "search");
  inp.placeholder = opts.ph || "都道府県・市区町村"; inp.setAttribute("aria-label", opts.ph || "都道府県・市区町村");
  inp.setAttribute("role", "combobox"); inp.setAttribute("aria-autocomplete", "list"); inp.setAttribute("aria-expanded", "false");
  ul.id = "pp" + Math.random().toString(36).slice(2, 7); ul.setAttribute("role", "listbox"); ul.hidden = true; inp.setAttribute("aria-controls", ul.id);
  bx.appendChild(inp); wrap.append(bx, ul); opts.root.appendChild(wrap);
  bx.addEventListener("click", function(ev){ var c = ev.target.closest(".pp-chip"); if (c) { remove(+c.getAttribute("data-i")); return; } inp.focus(); });
  function paint(){
    [].slice.call(bx.querySelectorAll(".pp-chip")).forEach(function(c){ c.remove(); });
    places.forEach(function(p, i){
      var c = el("button", "pp-chip"); c.type = "button"; c.setAttribute("data-i", i);
      c.setAttribute("aria-label", label(p) + "を外す"); c.append(document.createTextNode(label(p)), el("b", "", "×"));
      bx.insertBefore(c, inp);
    });
    inp.placeholder = places.length ? "＋ほかの場所も" : (opts.ph || "都道府県・市区町村");
  }
  function save(){ try { localStorage.setItem(KEY, JSON.stringify(places.slice(0, 8))); } catch (x) {} }
  function changed(){ paint(); save(); opts.onChange(places.slice()); }
  function add(p){
    // 県をまるごと選んだら、その県の市区町村の札は外す。市区町村を選んだら、その県まるごとの札は外す
    places = places.filter(function(x){ return !same(x, p) && !(!p.c && !p.s && x.p === p.p) && !((p.c || p.s) && x.p === p.p && !x.c && !x.s); });
    if (opts.fixed && p.p !== opts.fixed) return;
    places.push(p); changed();
  }
  function remove(i){ places.splice(i, 1); changed(); inp.focus(); }
  function hide(){ ul.hidden = true; inp.setAttribute("aria-expanded", "false"); act = -1; }
  function show(){
    var t = norm(inp.value), out = [], seen = {};
    function push(p, sub){ var k = p.p + "|" + (p.c || "") + "|" + (p.s || ""); if (seen[k] || places.some(function(x){ return same(x, p); })) return; seen[k] = 1; out.push([p, sub]); }
    var prefs = opts.prefs || [];
    if (!t) {
      // 何も入れていないとき：件数の多い県（いま選べる県）を少しだけ
      if (!opts.fixed) prefs.slice().sort(function(a, b){ return b[1] - a[1]; }).slice(0, 6).forEach(function(x){ if (x[1]) push({p: x[0]}, x[1] + (opts.unit || "件")); });
      else (opts.extra ? opts.extra("") : []).slice(0, 8).forEach(function(x){ push(x, x.n ? x.n + (opts.unit || "件") : x.p); });
    } else {
      var head = function(s){ return s.indexOf(t) === 0; };
      if (!opts.fixed) prefs.forEach(function(x){ var i = PN.indexOf(x[0]), nm = norm(x[0]); if (head(nm) || head(PK[i]) || (t.length >= 2 && nm.indexOf(t) >= 0)) push({p: x[0]}, (x[1] ? x[1] + (opts.unit || "件") : "")); });
      var ex = opts.extra ? opts.extra(t) : [];
      ex.forEach(function(x){ push(x, (x.c && x.c.indexOf("（") < 0 ? x.p : "") + (x.n ? "・" + x.n + (opts.unit || "件") : "")); });
      (MUNI || []).forEach(function(m){
        if (out.length > 40) return;
        var pf = PN[m[2]];
        if (opts.fixed && pf !== opts.fixed) return;
        if (opts.prefOk && !opts.prefOk(pf)) return;
        var nm = norm(m[0]), kn = m[1];
        if (head(nm) || head(kn) || head(kn.replace(/(し|く|ちょう|まち|そん|むら)$/, "")) || (t.length >= 2 && nm.indexOf(t) >= 0)) {
          var n = opts.cnt ? opts.cnt({p: pf, c: m[0]}) : null;
          push({p: pf, c: m[0]}, pf + (n ? "・" + n + (opts.unit || "件") : ""));
        }
      });
      if (!MUNI) loadMuni(function(){ if (document.activeElement === inp) show(); });
    }
    cur = out.slice(0, 10); ul.textContent = "";
    if (!cur.length) {
      if (t) { var li = el("li", "pp-h", "候補が見つかりません。市区町村の名前で入れてください"); ul.append(li); ul.hidden = false; }
      else hide();
      return;
    }
    if (!t) ul.append(el("li", "pp-h", opts.fixed ? "この中の場所でしぼる" : "よく選ばれる都道府県"));
    cur.forEach(function(x, i){
      var li = el("li"); li.setAttribute("role", "option"); li.setAttribute("data-i", i); li.id = ul.id + "-" + i;
      li.append(el("span", "", label(x[0])), el("small", "", x[1] || ""));
      ul.append(li);
    });
    act = t ? 0 : -1; mark(); ul.hidden = false; inp.setAttribute("aria-expanded", "true");
  }
  function mark(){ [].forEach.call(ul.querySelectorAll("li[role=option]"), function(li, i){ li.setAttribute("aria-selected", i === act ? "true" : "false"); }); inp.setAttribute("aria-activedescendant", act >= 0 ? ul.id + "-" + act : ""); }
  function pick(i){ var x = cur[i]; if (!x) return; inp.value = ""; hide(); add(x[0]); if (opts.typed) opts.typed(""); }
  ul.addEventListener("mousedown", function(ev){ ev.preventDefault(); });
  ul.addEventListener("click", function(ev){ var li = ev.target.closest("li[role=option]"); if (li) pick(+li.getAttribute("data-i")); });
  inp.addEventListener("focus", function(){ loadMuni(function(){}); show(); });
  inp.addEventListener("input", function(){ show(); if (opts.typed) opts.typed(inp.value); });
  inp.addEventListener("blur", function(){ setTimeout(hide, 150); });
  inp.addEventListener("keydown", function(ev){
    if (ev.key === "ArrowDown") { act = Math.min(act + 1, cur.length - 1); mark(); ev.preventDefault(); }
    else if (ev.key === "ArrowUp") { act = Math.max(act - 1, 0); mark(); ev.preventDefault(); }
    else if (ev.key === "Enter") { if (!ul.hidden && act >= 0) { pick(act); ev.preventDefault(); } else { hide(); inp.blur(); } }
    else if (ev.key === "Escape") hide();
    else if (ev.key === "Backspace" && !inp.value && places.length) remove(places.length - 1);
  });
  return {
    get: function(){ return places.slice(); },
    text: function(){ return inp.value; },
    clearText: function(){ inp.value = ""; },
    set: function(ps, quiet){ places = (ps || []).filter(function(p){ return p && p.p && (!opts.fixed || p.p === opts.fixed); }); paint(); if (!quiet) { save(); opts.onChange(places.slice()); } },
    saved: function(){ try { return JSON.parse(localStorage.getItem(KEY) || "[]") || []; } catch (x) { return []; } },
    input: inp
  };
};
window.PlacePick.label = label;
// 県庁所在地の近い県（結果が少ないときに近くの県も出すため）
var LL = [[43.06,141.35],[40.82,140.74],[39.70,141.15],[38.27,140.87],[39.72,140.10],[38.24,140.36],[37.75,140.47],[36.34,140.45],[36.57,139.88],[36.39,139.06],[35.86,139.65],[35.61,140.12],[35.69,139.69],[35.45,139.64],[37.90,139.02],[36.70,137.21],[36.59,136.63],[36.07,136.22],[35.66,138.57],[36.65,138.18],[35.39,136.72],[34.98,138.38],[35.18,136.91],[34.73,136.51],[35.00,135.87],[35.02,135.76],[34.69,135.52],[34.69,135.18],[34.69,135.83],[34.23,135.17],[35.50,134.24],[35.47,133.05],[34.66,133.93],[34.40,132.46],[34.19,131.47],[34.07,134.56],[34.34,134.04],[33.84,132.77],[33.56,133.53],[33.61,130.42],[33.25,130.30],[32.74,129.87],[32.79,130.74],[33.24,131.61],[31.91,131.42],[31.56,130.56],[26.21,127.68]];
window.PlacePick.near = function(pf, n){
  var i = PN.indexOf(pf); if (i < 0) return [];
  var a = LL[i], d = LL.map(function(b, j){ var dx = (a[1] - b[1]) * Math.cos(a[0] * Math.PI / 180), dy = a[0] - b[0]; return [dx * dx + dy * dy, PN[j]]; });
  d.sort(function(x, y){ return x[0] - y[0]; });
  return d.slice(1, (n || 3) + 1).map(function(x){ return x[1]; });
};
})();
