// 写真が2枚以上のカードに、ドット（いま何枚目か）と左右の矢印（横にスワイプできる合図）を付ける。写真は全体のまま、切らない。
(function(){
  function dec(s){
    if (s.dataset.cd || s.children.length < 2) return;
    s.dataset.cd = 1;
    var w = document.createElement("div"), d = document.createElement("div"), n = s.children.length, i;
    w.className = "cs-ph-w"; s.parentNode.insertBefore(w, s); w.appendChild(s);
    d.className = "cs-ph-d"; d.setAttribute("aria-hidden", "true");
    for (i = 0; i < n; i++) d.appendChild(document.createElement("i"));
    function b(c, l, t){ var e = document.createElement("button"); e.type = "button"; e.className = "cs-ph-a " + c; e.setAttribute("aria-label", l); e.textContent = t;
      e.addEventListener("click", function(){ s.scrollBy({left: (c === "r" ? 1 : -1) * s.clientWidth, behavior: "smooth"}); }); return e; }
    w.appendChild(b("l", "前の写真", "‹")); w.appendChild(b("r", "次の写真", "›")); w.appendChild(d);
    function u(){ var k = Math.round(s.scrollLeft / s.clientWidth), j; for (j = 0; j < n; j++) d.children[j].className = j === k ? "on" : "";
      w.className = "cs-ph-w" + (k <= 0 ? " f" : "") + (k >= n - 1 ? " e" : ""); }
    s.addEventListener("scroll", u, {passive: true}); u();
  }
  // 全国ページの写真（data-p="…/T003_5" ＝ _1〜_5 の5枚）。ここで同じ作りの並びを入れる（ドット・矢印は下の dec が付ける）。
  function fill(p){
    var m = /^(.*_)([1-5])$/.exec(p.getAttribute("data-p")), s = p.querySelector(".cs-ph-s"), c = p.parentNode.querySelector(".ux-c-n"), nm = c ? c.textContent.trim() : "", n, k, i, a, e;
    p.removeAttribute("data-p"); if (!m || !s) return; n = +m[2];
    for (k = 1; k <= n; k++) { i = document.createElement("i"); i.className = "cs-ph-i";
      for (a = 0; a < 2; a++) { e = document.createElement("img"); e.src = m[1] + k + ".webp"; e.loading = "lazy"; e.decoding = "async";
        if (a === 0) { e.className = "b"; e.alt = ""; e.setAttribute("aria-hidden", "true"); } else e.alt = nm + "の写真" + k;
        i.appendChild(e); }
      s.appendChild(i); }
    if (n > 1) { e = document.createElement("span"); e.className = "cs-ph-n"; e.setAttribute("aria-hidden", "true"); e.textContent = "📷 " + n; s.parentNode.insertBefore(e, s.nextSibling); }
  }
  function all(){ [].forEach.call(document.querySelectorAll(".cs-ph[data-p]"), fill); [].forEach.call(document.querySelectorAll(".cs-ph-s"), dec); }
  all();
  try { new MutationObserver(all).observe(document.documentElement, {childList: true, subtree: true}); } catch (x) {}
})();
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
    if (!a || a.hasAttribute("data-ga")) return; // data-ga＝hosp.js・facility.js が自分で数えるリンク（二重に数えない。2026-11-16）
    var cta = a.getAttribute("data-taxi-cta"), href = a.getAttribute("href") || "";
    if (!cta) { if (document.getElementById("petForm") || !/#form$/.test(href)) return; cta = "link"; }
    gtag("event", "taxi_cta", {cta: cta, from: location.pathname.split("/")[1] || "top", transport_type: "beacon"});
  }, true);
  // 押したリンクがどの会社・施設か（集計で会社ごとに分けるため。カードの見出しか、リンクの文字）
  // 新しいカード（.ux-c＝ドッグランなど、.jc-card＝迷子の窓口、.fc＝施設、.hc＝病院）も見る。いちばん近い枠の名前を使う（2026-11-16）
  function nameOf(a){ var c = a.closest(".hc, .ux-c, .jc-card, .fc, .emg-item, .card, li, tr, article"), h = c && c.querySelector(".hc-n, .ux-c-n, .fc-name, .jc-hd b, b, h3, h4, strong"); return String((h ? h.textContent : a.textContent) || "").replace(/\s+/g, " ").replace(/\s*↗$/, "").trim().slice(0, 80); }
  // 緊急の搬送の会社の電話を押した回数（Nori 2026-11-10「すすめて！両方」）。番号は送らず、会社の名前とページだけ。
  // トップ・エリアページの緊急タブから病院・搬送の会社の公式サイトへ出た回数も official_site（cat=emergency, from=emg_tab）で数える
  document.addEventListener("click", function(e){
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a || a.hasAttribute("data-ga")) return;
    var item = a.closest(".emg-item"), name = nameOf(a);
    var from = location.pathname.split("/")[1] || "top";
    if (/^tel:/i.test(a.getAttribute("href") || "")) { gtag("event", "tel_click", {cat: INFO.test(location.pathname) ? from : "emergency", company_name: name, from: from, transport_type: "beacon"}); return; }
    if (item && !INFO.test(location.pathname) && /^https?:$/.test(a.protocol) && a.host !== location.host && !/(^|\.)google\.|goo\.gl$/.test(a.hostname))
      gtag("event", "official_site", {cat: "emergency", host: a.hostname, company_name: name, from: "emg_tab", transport_type: "beacon"});
  }, true);
  // 情報ページから施設の公式サイトへ出た回数（2026-11-08 戦略「訪問を導線に」）。facility.js・hosp.js が自分で数えるリンクには data-ga が付いているので、ここでは数えない。
  // 施設のサイトには当サイトから来た印（utm）を付ける。役所のページ（jichitai）と地図・口コミのリンクには付けない。押した先の場所（ホスト名）とカテゴリだけ送る
  // 2026-11-16 計測漏れの点検：犬と泊まれる宿・カフェ・譲渡（保護団体・譲渡の窓口）も施設の公式サイトとして数える。
  // それ以外のページ（ガイド・避難など）から外のサイトへ出たリンクは outbound_link（送客には数えない）で数える。
  var INFO = /^\/(hospital|dogrun|jichitai|sougi|pet-hotel|pet-sitter|trimming|dog-trainer|rojin-home|emergency|inu-yado|pet-yado|inu-cafe|joto)\//, UTM = {hospital: 1, dogrun: 1, "pet-hotel": 1, trimming: 1, "rojin-home": 1, emergency: 1, "inu-yado": 1, "pet-yado": 1, "inu-cafe": 1};
  document.addEventListener("click", function(e){
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a || !/^https?:$/.test(a.protocol) || a.host === location.host || /(^|\.)google\.|goo\.gl$/.test(a.hostname)) return;
    var cat = location.pathname.split("/")[1];
    // 宿のカードのようにページに最初から utm が付いたリンクも数える（前は utm 付き＝facility.js が数える、として飛ばしていたため宿の送客が0だった。2026-11-16）
    if (UTM[cat] && INFO.test(location.pathname) && !/utm_source=pet\.shiokonbu\.com/.test(a.href)) { try { var x = new URL(a.href); x.searchParams.set("utm_source", "pet.shiokonbu.com"); x.searchParams.set("utm_medium", "referral"); x.searchParams.set("utm_campaign", cat.replace(/-/g, "_") + "_list"); a.href = x.toString(); } catch (y) {} }
    if (a.hasAttribute("data-ga")) return;
    if (INFO.test(location.pathname)) { gtag("event", "official_site", {cat: cat, host: a.hostname, company_name: nameOf(a), from: "page", transport_type: "beacon"}); return; }
    // フォームのあるページ（トップ・エリア・市区）は候補カード（app.js）と緊急タブ（上）で数えている
    if (document.getElementById("petForm") || a.closest(".emg-item")) return;
    gtag("event", "outbound_link", {cat: cat || "top", host: a.hostname, from: "page", transport_type: "beacon"});
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
