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
    if (!/^\/(hospital|dogrun|jichitai|sougi|rojin-home|dog-trainer|pet-sitter|trimming|emergency)\//.test(h)) return;
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

# 病院（条件ごと）・ドッグラン・自治体・亡くなったら のページ（select#hospPref）
LIST_JS = "<script>\n(function(){" + FN + '  var sel = document.getElementById("hospPref");' + APPLY + "  prefKeep(sel, apply);\n})();\n</script>"

# /hospital/ のように選択欄のないページ：覚えている県をリンクに付けるだけ
LINKS_JS = "<script>\n(function(){" + FN + "  prefLinks(prefGet());\n})();\n</script>"
