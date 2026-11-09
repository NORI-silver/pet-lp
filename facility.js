// [B][F] 情報ページ（ペット火葬・霊園／ペットシッター／ドッグトレーナー）の一覧のカードに付ける動き（手書き。生成の対象外）。
// Nori 2026-11-08「ペット葬儀とペットシッターとドッグトレーナーは、ペットタクシーと同じように、SEOもそうだけどマネタイズを意識して」。
// ペットタクシーの候補カード（まだ提携していない会社）と同じ形にそろえる：
//  - 公式サイトへのリンクに utm_source=pet.shiokonbu.com を付ける（当サイトから来たことが会社に見える）。押した数は解析の official_site
//  - 「問い合わせ文をつくる」：条件を入れると、公式サイトのお問い合わせ欄に貼れる文を作ってコピーする（お名前・連絡先は入れない。保存しない。送らない）
//    最後に「ペットタクシー予約窓口 pet.shiokonbu.com で見て、問い合わせました」と書く（送客が会社に伝わる）。数は copy_inquiry
//  - 条件のしぼりこみ（公式サイトに書いてあることから作ったタグだけ）。押した条件と県は facility_filter（どんな条件の人が多いか＝提携のお誘いに使う。個人の情報は送らない）
//  - 所在地の分かる施設は「ここまでのペットタクシーの料金をくらべる」（トップのフォームの行き先に入れる）。数は facility_taxi
//  - 提携した事業者（カードの data-partner="1"）は、名前の前にオレンジの丸にチェックのアイコンだけを付ける（文字は付けない）
// 問い合わせを当サイトから事業者へ送ることはしない（許可のない事業者に転送しない）。
(function(){
  function track(n, p){ if (window.gtag) gtag("event", n, p || {}); }
  var CAMP = {sougi: "sougi_cards", sitter: "sitter_cards", trainer: "trainer_cards", hosp: "hospital_pages", inn: "inn_pages", cafe: "cafe_pages"};
  var CONF = {
    sougi: {
      title: "火葬・霊園への問い合わせ文をつくる",
      lead: "入れたところだけ文に入ります。空のままでもかまいません。",
      fields: [
        ["animal", "動物の種類", "text", "例：犬（トイプードル）、猫"],
        ["weight", "体重", "text", "例：4kg"],
        ["plan", "希望の火葬", ["", "個別火葬（立ち会い）", "個別火葬（おまかせ）", "合同火葬", "まだ決めていない"]],
        ["pick", "お迎え", ["", "家まで来てほしい", "自分で連れて行く", "まだ決めていない"]],
        ["date", "希望の日にち", "text", "例：11月10日の午前"],
        ["city", "お住まいの市区町村", "text", "例：さいたま市浦和区"],
        ["memo", "そのほか", "text", "例：お骨は持ち帰りたい"]
      ],
      head: "ペットの火葬について教えてください。",
      tail: "料金と、ご都合のよい日時を教えていただけますか。"
    },
    sitter: {
      title: "ペットシッターへの問い合わせ文をつくる",
      lead: "入れたところだけ文に入ります。空のままでもかまいません。",
      fields: [
        ["animal", "動物の種類と頭数", "text", "例：猫2匹"],
        ["days", "お世話をしてほしい日", "text", "例：12月28日〜1月3日"],
        ["times", "1日の訪問", ["", "1日1回", "1日2回", "相談したい"]],
        ["care", "お世話の内容", "text", "例：ごはん・トイレ・薬"],
        ["city", "お住まいの市区町村", "text", "例：世田谷区"],
        ["meet", "打ち合わせの希望日", "text", "例：12月中旬の土日"],
        ["memo", "そのほか", "text", "例：鍵は手渡ししたい"]
      ],
      head: "ペットシッターをお願いしたいです。",
      tail: "対応していただけるかと、料金を教えていただけますか。"
    },
    trainer: {
      title: "ドッグトレーナーへの問い合わせ文をつくる",
      lead: "入れたところだけ文に入ります。空のままでもかまいません。",
      fields: [
        ["dog", "犬種と年齢", "text", "例：柴犬・1歳"],
        ["worry", "困っていること", "text", "例：散歩で引っぱる、来客にほえる"],
        ["style", "希望の形", ["", "家に来てほしい（出張）", "教室・グループに通いたい", "預かりのトレーニング", "オンライン", "まだ決めていない"]],
        ["city", "お住まいの市区町村", "text", "例：名古屋市千種区"],
        ["when", "希望の曜日・時間", "text", "例：土日の午前"],
        ["memo", "そのほか", "text", ""]
      ],
      head: "犬のトレーニングについて相談したいです。",
      tail: "受けていただけるかと、料金を教えていただけますか。"
    }
  };
  var ICON = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="currentColor"/><path d="M6.5 12.5l3.6 3.6 7.4-7.6" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var css = ".fac-act{display:flex;flex-wrap:wrap;gap:6px 8px;margin-top:8px;align-items:center}" +
    ".fac-act a.fac-site,.fac-act button{display:inline-block;border:1px solid var(--o,#e67e22);background:#fff;color:var(--o-d,#a84300);border-radius:999px;padding:6px 12px;font-size:.8rem;font-weight:700;text-decoration:none;cursor:pointer;font-family:inherit;line-height:1.3}" +
    ".fac-act a.fac-site{background:var(--o,#e67e22);color:#fff}" +
    ".fac-act a.fac-taxi{font-size:.8rem;font-weight:600}" +
    ".emg-item.fac-off{display:none}.fac-ic{display:inline-flex;vertical-align:-4px;margin-right:6px;color:var(--o,#e67e22)}" +
    ".fac-chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 4px}.fac-chips button{border:1px solid #d9cfc4;background:#fff;border-radius:999px;padding:6px 12px;font-size:.82rem;cursor:pointer;font-family:inherit;color:inherit}" +
    ".fac-chips button[aria-pressed=true]{background:var(--o-l,#fff1e3);border-color:var(--o,#e67e22);color:var(--o-d,#a84300);font-weight:700}" +
    ".fac-count{font-size:.82rem;color:var(--ink-2,#666);margin:2px 0 6px}" +
    ".fac-dlg{border:0;border-radius:16px;padding:0;max-width:min(520px,calc(100vw - 32px));width:100%;box-shadow:0 10px 40px rgba(0,0,0,.25)}" +
    ".fac-dlg::backdrop{background:rgba(0,0,0,.4)}.fac-dlg form{padding:18px 16px 16px}.fac-dlg h3{font-size:1rem;margin:0 0 4px}" +
    ".fac-dlg p{font-size:.82rem;margin:4px 0 10px;color:var(--ink-2,#555)}.fac-dlg label{display:block;font-size:.82rem;font-weight:700;margin:8px 0 2px}" +
    ".fac-dlg input,.fac-dlg select,.fac-dlg textarea{width:100%;box-sizing:border-box;font-size:16px;padding:7px 9px;border:1px solid #ccc;border-radius:8px;font-family:inherit}" +
    ".fac-dlg textarea{height:9em;font-size:14px;margin-top:4px}.fac-dlg .fac-btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}" +
    ".fac-dlg .fac-btns button,.fac-dlg .fac-btns a{flex:1 1 auto;text-align:center;border:0;border-radius:999px;padding:10px 14px;font-weight:700;font-size:.9rem;cursor:pointer;font-family:inherit;text-decoration:none}" +
    ".fac-dlg .fac-copy{background:var(--o,#e67e22);color:#fff}.fac-dlg .fac-go{background:#fff;border:1px solid var(--o,#e67e22)!important;color:var(--o-d,#a84300)}.fac-dlg .fac-x{background:#eee;color:#333}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  function siteUrl(u, cat){
    try { var x = new URL(u); x.searchParams.set("utm_source", "pet.shiokonbu.com"); x.searchParams.set("utm_medium", "referral"); x.searchParams.set("utm_campaign", CAMP[cat] || "info_cards"); return x.toString(); } catch (e) { return u; }
  }
  function prefOf(card){ var s = card.closest("[data-pref]"); return s ? s.getAttribute("data-pref") : ""; }
  function el(tag, cls, text){ var x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; }

  // ── 問い合わせ文 ──
  var vals = {}; // このページを開いているあいだだけ覚える（保存はしない）
  var dlg = null, cur = null;
  function buildText(cat, name){
    var c = CONF[cat], lines = [name ? name + " 御中" : "", "", c.head, ""];
    c.fields.forEach(function(f){ var v = (vals[cat + "." + f[0]] || "").trim(); if (v) lines.push("・" + f[1] + "：" + v); });
    lines.push("", c.tail, "", "（ペットタクシー予約窓口 pet.shiokonbu.com で見て、問い合わせました）");
    return lines.join("\n").replace(/^\n+/, "");
  }
  function copy(t, done){
    function fb(){ try { var ta = document.createElement("textarea"); ta.value = t; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select(); var ok = document.execCommand("copy"); ta.remove(); return ok; } catch (e) { return false; } }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function(){ done(true); }, function(){ done(fb()); });
    else done(fb());
  }
  function openAsk(card){
    var cat = card.getAttribute("data-cat"), c = CONF[cat]; if (!c) return;
    var name = card.getAttribute("data-name") || "", href = card.getAttribute("data-site") || "";
    cur = {card: card, cat: cat};
    if (!dlg) { dlg = el("dialog", "fac-dlg"); document.body.appendChild(dlg); }
    var f = el("form"); f.method = "dialog";
    f.appendChild(el("h3", "", c.title));
    f.appendChild(el("p", "", "あて先：" + name + "。" + c.lead + "お名前・連絡先は入れていないので、公式サイトのお問い合わせ欄に貼ったあと、ご自分で書き足してください。当サイトからは何も送りません。"));
    var ta = el("textarea"); ta.setAttribute("aria-label", "問い合わせ文");
    function sync(){ ta.value = buildText(cat, name); }
    c.fields.forEach(function(fd){
      var id = "fac_" + fd[0], lab = el("label", "", fd[1]); lab.htmlFor = id; f.appendChild(lab);
      var inp;
      if (Array.isArray(fd[2])) { inp = el("select"); fd[2].forEach(function(o){ var op = el("option", "", o || "えらんでください"); op.value = o; inp.appendChild(op); }); }
      else { inp = el("input"); inp.type = "text"; inp.placeholder = fd[3] || ""; inp.maxLength = 80; inp.autocomplete = "off"; }
      inp.id = id; inp.value = vals[cat + "." + fd[0]] || "";
      inp.addEventListener("input", function(){ vals[cat + "." + fd[0]] = inp.value; sync(); });
      inp.addEventListener("change", function(){ vals[cat + "." + fd[0]] = inp.value; sync(); });
      f.appendChild(inp);
    });
    var lab2 = el("label", "", "できあがった文（直してもかまいません）"); f.appendChild(lab2); f.appendChild(ta); sync();
    var btns = el("div", "fac-btns"), bc = el("button", "fac-copy", "文をコピーする"); bc.type = "button";
    bc.addEventListener("click", function(){
      track("copy_inquiry", {cat: cat, id: card.getAttribute("data-fid") || "", pref: prefOf(card)});
      copy(ta.value, function(ok){ bc.textContent = ok ? "コピーしました。公式サイトに貼ってください" : "コピーできませんでした。文を長押しして選んでください"; setTimeout(function(){ bc.textContent = "文をコピーする"; }, 4000); });
    });
    btns.appendChild(bc);
    if (href) { var go = el("a", "fac-go", "公式サイトを開く ↗"); go.href = siteUrl(href, cat); go.target = "_blank"; go.rel = "noopener"; go.addEventListener("click", function(){ track("official_site", {cat: cat, id: card.getAttribute("data-fid") || "", pref: prefOf(card), from: "dialog"}); }); btns.appendChild(go); }
    var bx = el("button", "fac-x", "閉じる"); bx.value = "close"; btns.appendChild(bx);
    f.appendChild(btns);
    dlg.replaceChildren(f);
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    track("open_inquiry", {cat: cat, id: card.getAttribute("data-fid") || ""});
  }

  // ── カード ──
  var cards = Array.prototype.slice.call(document.querySelectorAll(".emg-item[data-cat]"));
  if (!cards.length) return;
  cards.forEach(function(card){
    var cat = card.getAttribute("data-cat"), fid = card.getAttribute("data-fid") || "";
    var a = card.querySelector("a[href^='http']"), href = a ? a.getAttribute("href") : "";
    if (href) { card.setAttribute("data-site", href); a.href = siteUrl(href, cat); a.addEventListener("click", function(){ track("official_site", {cat: cat, id: fid, pref: prefOf(card), from: "name"}); }); }
    if (!card.getAttribute("data-name") && a) card.setAttribute("data-name", (a.textContent || "").trim());
    if (card.getAttribute("data-partner") === "1" && a) {
      var ic = el("span", "fac-ic"); ic.setAttribute("role", "img"); ic.setAttribute("aria-label", "このサイトから問い合わせできる事業者"); ic.title = "このサイトから問い合わせできる事業者"; ic.innerHTML = ICON;
      var b = a.querySelector("b") || a; b.insertBefore(ic, b.firstChild);
    }
    var row = el("div", "fac-act");
    if (href) { var s = el("a", "fac-site", "公式サイトを見る ↗"); s.href = siteUrl(href, cat); s.target = "_blank"; s.rel = "noopener"; s.addEventListener("click", function(){ track("official_site", {cat: cat, id: fid, pref: prefOf(card), from: "button"}); }); row.appendChild(s); }
    if (CONF[cat]) { var q = el("button", "", "問い合わせ文をつくる"); q.type = "button"; q.addEventListener("click", function(){ openAsk(card); }); row.appendChild(q); }
    var to = card.getAttribute("data-to");
    if (to) {
      var t = el("a", "fac-taxi", (card.getAttribute("data-to-label") || "ここ") + "までのペットタクシーの料金をくらべる →");
      var pf = prefOf(card);
      t.href = "/?" + (pf ? "pref=" + encodeURIComponent(pf) + "&" : "") + "to=" + encodeURIComponent(to) + "#form";
      t.addEventListener("click", function(){ track("facility_taxi", {cat: cat, id: fid, pref: pf}); });
      row.appendChild(t);
    }
    card.appendChild(row);
  });

  // ── 条件でしぼりこむ ──（data-tags は公式サイトに書いてあることから作ったもの。空＝書いていない・分からない）
  var box = document.querySelector("[data-fac-chips]");
  if (!box) return;
  var cat0 = cards[0].getAttribute("data-cat"), on = {};
  var labels = (box.getAttribute("data-fac-chips") || "").split("|").filter(Boolean);
  var chips = el("div", "fac-chips"), cnt = el("p", "fac-count");
  chips.setAttribute("role", "group"); chips.setAttribute("aria-label", "条件でしぼりこむ");
  function tagsOf(c){ return "|" + (c.getAttribute("data-tags") || "") + "|"; }
  function apply(){
    var keys = Object.keys(on).filter(function(k){ return on[k]; }), n = 0;
    cards.forEach(function(c){
      var ok = keys.every(function(k){ return tagsOf(c).indexOf("|" + k + "|") >= 0; });
      c.classList.toggle("fac-off", !ok);
      var sec = c.closest(".emg-pref");
      if (ok && (!sec || !sec.hidden)) n++;
    });
    cnt.textContent = keys.length ? "条件に合うのは " + n + " 件です（公式サイトに書いてあることだけで判定。書いていない所は外れます）。" : "";
  }
  labels.forEach(function(lab){
    var b = el("button", "", lab); b.type = "button"; b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", function(){
      on[lab] = !on[lab]; b.setAttribute("aria-pressed", on[lab] ? "true" : "false"); apply();
      if (on[lab]) { var sel = document.getElementById("hospPref"); track("facility_filter", {cat: cat0, tag: lab, pref: box.getAttribute("data-pref") || (sel ? sel.value : "")}); }
    });
    chips.appendChild(b);
  });
  box.appendChild(chips); box.appendChild(cnt);
  var sel = document.getElementById("hospPref"); if (sel) sel.addEventListener("change", function(){ setTimeout(apply, 0); });
})();
