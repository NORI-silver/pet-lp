"""都道府県の選択を、ページを移っても保つ（Nori 2026-11-02「都道府県は一度選んだらユーザーが変更するまで固定」）。

病院・ドッグラン・自治体の窓口・亡くなったら・緊急の連絡先のページで使う。
- 選んだ都道府県はブラウザに覚えておき（localStorage の petInfoPref）、ほかのページを開いても同じ県にする。
- URL の #pref=◯◯ があればそれを優先し、それも覚える（エリアページからのリンクなど）。
- ブラウザに保存できないときのために、これらのページへのリンクにも #pref=◯◯ を付けておく。
- トップの緊急タブ（index.html の emgPref）も同じ petInfoPref を読み書きする。
"""

# function 定義だけ。各ページは prefKeep(select要素, 絞り込みの関数) を呼ぶ。
FN = r"""
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
"""

APPLY = r"""
  function apply(){
    var v = sel.value;
    document.querySelectorAll(".emg-pref").forEach(function(s){ s.hidden = !!v && s.dataset.pref !== v; });
    document.querySelectorAll(".emg-region").forEach(function(h){ h.hidden = !!v; });
  }
"""

# はじめての人（#pref= も覚えた県もない）には、いる場所に近い県を最初から選んでおく。
# 位置の利用がすでに許可されていれば端末の位置、なければ通信の情報からの大まかな地域。新しく許可は求めない。覚えはしない。
# 全国の一覧で北海道から並ぶと、自分の県まで長くスクロールして離れてしまうため（2026-11-12 Nori「サイト内離脱してるんだったらそれはヒントだ。改善して」。緊急のページと同じしくみ）
import os as _os, re as _re
_top = open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "index.html"), encoding="utf-8").read()
_PN = _re.search(r"var PREF_NAMES = (\[[^\]]*\]);", _top).group(1)
_PL = _re.search(r"var PREF_LL = (\[\[.*?\]\]);", _top).group(1)
GUESS = r"""
function prefGuess(sel, apply){
  if (sel.value) return;
  var NAMES = """ + _PN + """, LL = """ + _PL + r""";
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
"""

# 病院（条件ごと）・ドッグラン・自治体・亡くなったら のページ（select#hospPref）
LIST_JS = "<script>\n(function(){" + FN + GUESS + '  var sel = document.getElementById("hospPref");' + APPLY + "  prefKeep(sel, apply);\n  prefGuess(sel, apply);\n})();\n</script>"

# /hospital/ のように選択欄のないページ：覚えている県をリンクに付けるだけ
LINKS_JS = "<script>\n(function(){" + FN + "  prefLinks(prefGet());\n})();\n</script>"
