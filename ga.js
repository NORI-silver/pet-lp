// アクセス解析：見られたページと、よく使われる操作の数を集計する（お名前・連絡先・場所などの入力内容は送らない）。
// ID が空のときと、本番の pet.shiokonbu.com 以外（手元での確認など）では何もしない。
(function(){
  // 2つに送る（Nori 2026-11-03）：shiokonbu.com 全体（pet・hinata などのサブドメインも全部入る総合）と、pet.shiokonbu.com だけの「pet」。
  var IDS = ["G-ZYX17VBTWB", "G-3KGJ9VY12G"]; // 1つ目＝shiokonbu.com 総合（消さない）、2つ目＝pet だけ
  IDS = IDS.filter(function(x){ return x; });
  if (!IDS.length || location.hostname !== "pet.shiokonbu.com") return;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function(){ dataLayer.push(arguments); };
  gtag("js", new Date());
  // URL の受付番号・署名・見本のリンクなどは送らない。広告の印（utm_…・gclid）だけ残す（2026-11-08）
  function clean(u){
    try {
      var x = new URL(u), q = new URLSearchParams();
      x.searchParams.forEach(function(v, k){ if (/^utm_/.test(k) || k === "gclid") q.append(k, v); });
      var t = q.toString();
      return x.origin + x.pathname + (t ? "?" + t : "");
    } catch (e) { return ""; }
  }
  var opt = {page_location: clean(location.href)};
  if (document.referrer) opt.page_referrer = clean(document.referrer);
  IDS.forEach(function(id){ gtag("config", id, opt); });
  var s = document.createElement("script"); s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + IDS[0];
  document.head.appendChild(s);
  // 情報ページ（病院・ドッグランなど）からペットタクシーのフォームへ進んだ回数（2026-11-08 Nori「1と2」）。
  // data-taxi-cta のボタン（tools/taxi_cta.py）と、フォームのないページにあるフォームへのリンクを数える。入力内容は送らない
  document.addEventListener("click", function(e){
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    var cta = a.getAttribute("data-taxi-cta"), href = a.getAttribute("href") || "";
    if (!cta) { if (document.getElementById("petForm") || !/#form$/.test(href)) return; cta = "link"; }
    gtag("event", "taxi_cta", {cta: cta, from: location.pathname.split("/")[1] || "top", transport_type: "beacon"});
  }, true);
})();

// AIエージェント向けの道具（WebMCP、webmcp.js）。対応したブラウザのときだけ読み込む。見るだけで、どこにも送らない。
(function(){
  if (!(document.modelContext || navigator.modelContext) || /^\/go\//.test(location.pathname)) return;
  var s = document.createElement("script"); s.defer = true; s.src = "/webmcp.js";
  document.head.appendChild(s);
})();
