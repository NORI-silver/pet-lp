// アクセス解析：見られたページと、よく使われる操作の数を集計する（お名前・連絡先・場所などの入力内容は送らない）。
// ID が空のときと、本番の pet.shiokonbu.com 以外（手元での確認など）では何もしない。
(function(){
  // 2つに送る（Nori 2026-11-03）：shiokonbu.com 全体（pet・hinata などのサブドメインも全部入る総合）と、pet.shiokonbu.com だけの「pet」。
  var IDS = ["G-ZYX17VBTWB", ""]; // 1つ目＝shiokonbu.com 総合（消さない）、2つ目＝pet だけ
  IDS = IDS.filter(function(x){ return x; });
  if (!IDS.length || location.hostname !== "pet.shiokonbu.com") return;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function(){ dataLayer.push(arguments); };
  gtag("js", new Date());
  IDS.forEach(function(id){ gtag("config", id); });
  var s = document.createElement("script"); s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + IDS[0];
  document.head.appendChild(s);
})();

// AIエージェント向けの道具（WebMCP、webmcp.js）。対応したブラウザのときだけ読み込む。見るだけで、どこにも送らない。
(function(){
  if (!(document.modelContext || navigator.modelContext) || /^\/go\//.test(location.pathname)) return;
  var s = document.createElement("script"); s.defer = true; s.src = "/webmcp.js";
  document.head.appendChild(s);
})();
