// アクセス解析：見られたページと、よく使われる操作の数を集計する（お名前・連絡先・場所などの入力内容は送らない）。
// ID が空のときと、本番の pet.shiokonbu.com 以外（手元での確認など）では何もしない。
(function(){
  // 運営者の端末の印（2026-11-10 戦略担当）：一度 ?staff=1 で開くとこの端末を運営者と覚え、?staff=0 で解除。
  // 解析のイベントに staff=1 を付け、検索は需要の記録で「運営者」と分ける（index.html）。手元の確認でも覚える
  try {
    var st = new URLSearchParams(location.search).get("staff");
    if (st === "1") localStorage.setItem("petStaff", "1"); else if (st === "0") localStorage.removeItem("petStaff");
    window.PET_STAFF = localStorage.getItem("petStaff") === "1";
  } catch (e) { window.PET_STAFF = new URLSearchParams(location.search).get("staff") === "1"; }
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
  if (window.PET_STAFF) { gtag("set", {staff: "1"}); gtag("set", "user_properties", {staff: "1"}); opt.traffic_type = "internal"; }
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
  // 押したリンクがどの会社・施設か（集計で会社ごとに分けるため。カードの見出しか、リンクの文字）
  function nameOf(a){ var c = a.closest(".emg-item, article, li, .card, tr"), h = c && c.querySelector("b, h3, h4, strong"); return String((h ? h.textContent : a.textContent) || "").replace(/\s+/g, " ").trim().slice(0, 80); }
  // 緊急の搬送の会社の電話を押した回数（Nori 2026-11-10「すすめて！両方」）。番号は送らず、会社の名前とページだけ。
  // トップ・エリアページの緊急タブから病院・搬送の会社の公式サイトへ出た回数も official_site（cat=emergency, from=emg_tab）で数える
  document.addEventListener("click", function(e){
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    var item = a.closest(".emg-item"), name = nameOf(a);
    var from = location.pathname.split("/")[1] || "top";
    if (/^tel:/i.test(a.getAttribute("href") || "")) { gtag("event", "tel_click", {cat: "emergency", company_name: name, from: from, transport_type: "beacon"}); return; }
    if (item && !INFO.test(location.pathname) && /^https?:$/.test(a.protocol) && a.host !== location.host && !/(^|\.)google\.|goo\.gl$/.test(a.hostname))
      gtag("event", "official_site", {cat: "emergency", host: a.hostname, company_name: name, from: "emg_tab", transport_type: "beacon"});
  }, true);
  // 情報ページから施設の公式サイトへ出た回数（2026-11-08 戦略「訪問を導線に」）。facility.js が印を付けたリンク（utm_source=pet.shiokonbu.com）は facility.js が数えるので、ここでは数えない。
  // 施設のサイトには当サイトから来た印（utm）を付ける。役所のページ（jichitai）と地図・口コミのリンクには付けない。押した先の場所（ホスト名）とカテゴリだけ送る
  var INFO = /^\/(hospital|dogrun|jichitai|sougi|pet-hotel|pet-sitter|trimming|dog-trainer|rojin-home|emergency)\//, UTM = {hospital: 1, dogrun: 1, "pet-hotel": 1, trimming: 1, "rojin-home": 1, emergency: 1};
  if (INFO.test(location.pathname)) document.addEventListener("click", function(e){
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a || !/^https?:$/.test(a.protocol) || a.host === location.host || /utm_source=pet\.shiokonbu\.com/.test(a.href) || /(^|\.)google\.|goo\.gl$/.test(a.hostname)) return;
    var cat = location.pathname.split("/")[1];
    if (UTM[cat]) { try { var x = new URL(a.href); x.searchParams.set("utm_source", "pet.shiokonbu.com"); x.searchParams.set("utm_medium", "referral"); x.searchParams.set("utm_campaign", cat.replace(/-/g, "_") + "_list"); a.href = x.toString(); } catch (y) {} }
    gtag("event", "official_site", {cat: cat, host: a.hostname, company_name: nameOf(a), from: "page", transport_type: "beacon"});
  }, true);
})();

// AIエージェント向けの道具（WebMCP、webmcp.js）。対応したブラウザのときだけ読み込む。見るだけで、どこにも送らない。
(function(){
  if (!(document.modelContext || navigator.modelContext) || /^\/go\//.test(location.pathname)) return;
  var s = document.createElement("script"); s.defer = true; s.src = "/webmcp.js";
  document.head.appendChild(s);
})();
// 分野のメニュー（tools/portal.py の catbar）：いま見ている分野が画面の外なら、見える位置まで横に送る（2026-11-14）
(function(){
  function go(){var n=document.querySelector('.catbar .wrap'),a=n&&n.querySelector('[aria-current]');if(a&&a.offsetLeft+a.offsetWidth>n.clientWidth)n.scrollLeft=a.offsetLeft-20;}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go();
})();
