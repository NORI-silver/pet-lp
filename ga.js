// アクセス解析：見られたページと、よく使われる操作の数を集計する（お名前・連絡先・場所などの入力内容は送らない）。
// ID が空のときと、本番の pet.shiokonbu.com 以外（手元での確認など）では何もしない。
(function(){
  var ID = "";
  if (!ID || location.hostname !== "pet.shiokonbu.com") return;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function(){ dataLayer.push(arguments); };
  gtag("js", new Date());
  gtag("config", ID);
  var s = document.createElement("script"); s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
  document.head.appendChild(s);
})();
