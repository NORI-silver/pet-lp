// 生成ファイル（tools/gen_areas.py）。手で直さない
(function(){
  var GAS_URL = "https://script.google.com/macros/s/AKfycbyy-cTvD-t8DFGhEyA2IbFiXWoB50kl_2_97WiVdMlXec8sIbI2NVUkkyn-45VkIMc_5g/exec", memo = {}, queue = [], timer = 0;
  function el(tag, cls, text){ var x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; }
  function toggle(id, panel, btn){
    if (!panel.hidden) { panel.hidden = true; btn.setAttribute("aria-expanded", "false"); return; }
    panel.hidden = false; btn.setAttribute("aria-expanded", "true");
    if (window.gtag) gtag("event", "open_reviews", {});
    if (panel.dataset.done) return;
    panel.textContent = "口コミを読み込んでいます…";
    var body = new URLSearchParams(); body.set("kind", "reviews"); body.set("partner_id", id);
    fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){ fill(panel, j); })
      .catch(function(){ panel.textContent = "口コミを読み込めませんでした。時間をおいてもう一度お試しください。"; });
  }
  // 取り寄せた口コミを枠に入れる（書いた人・元の口コミへのリンク・並び順の説明・出どころは規約で必要）
  function fill(panel, j){
      if (!j || !j.ok || !Array.isArray(j.reviews)) throw 0;
      panel.dataset.done = "1"; panel.replaceChildren();
      panel.appendChild(el("p", "review-head", "関連度の高い順に、最大5件を表示しています（全" + j.count + "件）。"));
      j.reviews.forEach(function(v){
        var item = el("div", "review-item"), who = el("div", "review-who");
        if (v.photo) { var img = document.createElement("img"); img.src = v.photo; img.alt = ""; img.width = 28; img.height = 28; img.loading = "lazy"; img.referrerPolicy = "no-referrer"; who.appendChild(img); }
        var name = el(v.authorUrl ? "a" : "span", "", v.author || "投稿者");
        if (v.authorUrl) { name.href = v.authorUrl; name.target = "_blank"; name.rel = "noopener"; }
        who.append(name, el("small", "", "★" + v.rating + (v.when ? "・" + v.when : ""))); item.appendChild(who);
        if (v.text) item.appendChild(el("p", "", v.text));
        if (v.url) { var a = el("a", "review-link", "元の口コミ ↗"); a.href = v.url; a.target = "_blank"; a.rel = "noopener"; item.appendChild(a); } // 規約で口コミごとに必要なリンク
        panel.appendChild(item);
      });
      panel.appendChild(el("p", "partner-review-src", "Google Maps"));
  }
  // 施設の写真（最大3枚）。撮った人の名前とリンク・出どころは規約で必要。2026-11-14 Nori「施設の写真とか追加したほうがいいんじゃない？」
  // 施設カード（tools/faccard.py）は上の大きな枠に、横にスワイプして見る形で入れる（Nori 2026-11-15「写真はスワイプで複数みれるように」）。
  // PHOTO_AUTO（tools/faccard.py）が true なら、カードが画面に近づいたときに自動で取り寄せる。false なら「写真を見る」を押したときだけ
  var PHOTO_AUTO = false;
  function getPhotos(id){
    if (window.gtag) gtag("event", "open_photos", {id: id});
    var body = new URLSearchParams(); body.set("kind", "photos"); body.set("partner_id", id);
    return fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){
      if (!j || !j.ok) throw 0;
      if (!j.photos || !j.photos.length) throw "none";
      return j.photos;
    });
  }
  function credit(v){
    var cap = el("figcaption");
    (v.by || []).forEach(function(a, i){
      if (i) cap.appendChild(document.createTextNode("・"));
      var n = el(a.uri ? "a" : "span", "", a.name || "投稿者"); if (a.uri) { n.href = a.uri; n.target = "_blank"; n.rel = "noopener"; }
      cap.appendChild(n);
    });
    return cap;
  }
  function carousel(slot, ps){
    var car = el("div", "fc-car"), dots = el("div", "fc-dots");
    ps.forEach(function(v, i){
      var f = el("figure"), img = document.createElement("img");
      img.src = v.url; img.alt = ""; img.loading = "lazy"; img.referrerPolicy = "no-referrer"; if (v.w && v.h) { img.width = v.w; img.height = v.h; }
      f.appendChild(img); if ((v.by || []).length) f.appendChild(credit(v)); car.appendChild(f);
      var d = el("i"); if (!i) d.className = "on"; dots.appendChild(d);
    });
    car.addEventListener("scroll", function(){
      var k = Math.round(car.scrollLeft / Math.max(1, car.clientWidth));
      [].forEach.call(dots.children, function(d, i){ d.className = i === k ? "on" : ""; });
    }, {passive: true});
    slot.replaceChildren(car); if (ps.length > 1) slot.appendChild(dots);
    slot.appendChild(el("span", "fc-src", "写真：Google Maps"));
    slot.hidden = false;
  }
  function photos(box){
    if (!PHOTO_AUTO) return; // 「写真を見る」のボタンは出さない（Nori 2026-11-15「写真を見るはいらない」）。自動で出すときだけ写真を入れる
    if (box.nextElementSibling && box.nextElementSibling.classList.contains("fac-photos")) return;
    var id = box.dataset.id, card = box.closest(".fc"), slot = card && card.querySelector(".fc-ph");
    if (slot) {
      if (slot.dataset.go) return; slot.dataset.go = "1";
      var body = card.querySelector(".fc-acts") || card.querySelector(".fc-body") || card;
      var put = function(n){ body.insertBefore(n, body.firstChild); };
      var b = el("button", "fc-phbtn", "写真"); b.type = "button"; b.setAttribute("aria-label", "写真を見る");
      var load = function(){
        b.disabled = true; b.textContent = "読み込み中…";
        getPhotos(id).then(function(ps){ carousel(slot, ps); b.remove(); }).catch(function(e){ if (e === "none") { b.textContent = "写真なし"; return; } b.remove(); var x = el("button", "fc-phbtn", "写真をもう一度"); x.type = "button"; x.addEventListener("click", function(){ x.remove(); put(b); load(); }); put(x); });
      };
      b.addEventListener("click", load);
      put(b);
      if (PHOTO_AUTO && "IntersectionObserver" in window) {
        var io = new IntersectionObserver(function(es){ es.forEach(function(x){ if (x.isIntersecting && x.target.offsetParent) { io.disconnect(); load(); } }); }, {rootMargin: "300px"});
        io.observe(card);
      }
      return;
    }
    var w = el("div", "fac-photos"); b = el("button", "partner-review-open", "写真を見る"); b.type = "button";
    w.appendChild(b); box.parentNode.insertBefore(w, box.nextSibling);
    b.addEventListener("click", function(){
      b.disabled = true; b.textContent = "写真を読み込んでいます…";
      getPhotos(id).then(function(ps){
        var row = el("div", "fac-photo-row");
        ps.forEach(function(v){
          var f = el("figure", "fac-photo"), img = document.createElement("img");
          img.src = v.url; img.alt = ""; img.loading = "lazy"; img.referrerPolicy = "no-referrer"; if (v.w && v.h) { img.width = v.w; img.height = v.h; }
          f.appendChild(img); var cap = credit(v); if (cap.childNodes.length) f.appendChild(cap);
          row.appendChild(f);
        });
        w.replaceChildren(row, el("p", "partner-review-src", "写真：Google Maps（利用者が投稿した写真です）"));
      }).catch(function(e){ w.replaceChildren(el("p", "partner-review-src", e === "none" ? "地図サービスに写真がまだありません" : "写真を読み込めませんでした。時間をおいてもう一度お試しください")); });
    });
  }
  // 押したときだけ取り寄せる形（REVIEW_ON_CLICK）：最初は「口コミを見る」だけを出し、押したら星と本文をまとめて取り寄せる
  function lazy(box){
    var fc = box.closest(".fc-acts"), id = box.dataset.id, b = el("button", "partner-review-open", fc ? "口コミ" : "口コミを見る"), p = el("p", "partner-score"); b.type = "button";
    if (fc) { b.setAttribute("aria-label", "口コミを見る"); p.append(b); } else p.append(b, el("span", "partner-review-src", "Google Maps")); box.replaceChildren(p);
    b.addEventListener("click", function(){
      b.disabled = true; b.textContent = fc ? "読み込み中…" : "口コミを読み込んでいます…";
      if (window.gtag) gtag("event", "open_reviews", {});
      var body = new URLSearchParams(); body.set("kind", "reviews"); body.set("partner_id", id);
      fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){
        if (j && j.ok && (!(j.rating > 0) || !(j.count > 0))) throw "none"; // Googleマップに口コミがまだない（上限や不具合とは別）
        if (!j || !j.ok) throw 0;
        memo[id] = {rating: j.rating, count: j.count}; paint(box, memo[id]); if (window.__ratingSort) window.__ratingSort(box);
        var panel = box.querySelector(".review-panel"), open = box.querySelector(".partner-review-open");
        fill(panel, j); panel.hidden = false; open.setAttribute("aria-expanded", "true");
      }).catch(function(e){ if (e === "none") { box.remove(); return; } b.disabled = false; b.textContent = "口コミをもう一度"; });
    });
  }
  function paint(box, rv){
    box.replaceChildren();
    if (!rv || !(rv.rating > 0)) return; // 点数が取れないときは何も出さない（外部のページへは飛ばさない）
    var r = Math.max(0, Math.min(5, rv.rating)), score = el("p", "partner-score");
    var stars = el("span", "stars"); stars.setAttribute("aria-hidden", "true"); stars.style.setProperty("--fill", r / 5 * 100 + "%");
    score.setAttribute("aria-label", "口コミの評価 5点中" + Number(rv.rating).toFixed(1) + "点、" + rv.count + "件");
    var open = el("button", "partner-review-open", "口コミ" + rv.count + "件を見る"); open.type = "button"; open.setAttribute("aria-expanded", "false");
    score.append(stars, el("b", "", Number(rv.rating).toFixed(1)), open, el("span", "partner-review-src", "Google Maps")); // 出どころの表示（規約で必要）
    var panel = el("div", "review-panel"); panel.hidden = true;
    open.addEventListener("click", function(){ toggle(box.dataset.id, panel, open); });
    box.append(score, panel);
  }
  function flush(){
    timer = 0;
    var need = queue.filter(function(id, i, a){ return a.indexOf(id) === i && !(id in memo); }); queue = [];
    if (!need.length) return;
    need.forEach(function(id){ memo[id] = null; });
    var body = new URLSearchParams(); body.set("kind", "emg_scores"); body.set("ids", need.join(","));
    fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).catch(function(){ return null; }).then(function(j){
      var sc = (j && j.ok && j.scores) || {};
      need.forEach(function(id){ memo[id] = sc[id] || null; });
      document.querySelectorAll(".emg-score").forEach(function(b){ if (need.indexOf(b.dataset.id) >= 0) paint(b, memo[b.dataset.id]); });
    });
  }
  function want(box){
    if (box.dataset.id in memo) { if (memo[box.dataset.id]) paint(box, memo[box.dataset.id]); return; }
    queue.push(box.dataset.id); if (!timer) timer = setTimeout(flush, 300);
  }
  // 後から並べたカード（/hosp.js の病院さがし）にも「口コミ」を付ける
  window.petReviews = function(root){ root.querySelectorAll(".emg-score[data-id]").forEach(function(b){ if (!b.firstChild) lazy(b); }); };
  // 口コミの並べ替え（2026-11-28 Nori 11/26「口コミが高い順・低い順」「初期は口コミが高い順」）。
  // 並べるのは、いま読み込み済みの星だけ。星を取り寄せていないところは「未取得」として最後に、元の順のまま並べる（0点とは扱わない）。新しい取り寄せはしない。
  (function(){
    var sel = document.getElementById("ffSort"), hl = document.getElementById("hfList"), own = null;
    // 病院さがし（/hosp.js）には並び順の欄が無いので、ここで足す。カードは /hosp.js が何度も作り直す
    if (!sel && hl && hl.parentNode) { own = el("p", "ff-ord"); own.hidden = true; own.style.cssText = "margin:8px 0 4px;font-size:.85rem"; sel = el("select"); sel.id = "rsSort"; sel.setAttribute("aria-label", "表示順"); sel.style.cssText = "margin-left:6px;font-size:1rem;padding:6px"; own.append("表示順", sel); [["", "標準の並び"]].forEach(function(o){ var op = el("option", "", o[1]); op.value = o[0]; sel.appendChild(op); }); hl.parentNode.insertBefore(own, hl); }
    if (!sel || !(own || document.querySelector(".emg-score[data-id]"))) return;
    var MODE = {ratingDesc: 1, ratingAsc: 1}, note = el("p", "ff-note", "口コミの並べ替えは、星を読み込んだ施設だけが対象です。未取得の施設は最後に、もとの順で並びます。");
    note.style.cssText = "margin:4px 0 0;font-size:.8rem;color:#6b625b";
    [["ratingAsc", "口コミが低い順"], ["ratingDesc", "口コミが高い順"]].forEach(function(o){ var op = el("option", "", o[1]); op.value = o[0]; sel.insertBefore(op, sel.firstChild); });
    sel.value = "ratingDesc";
    if (own) own.appendChild(note); else if (sel.parentNode) sel.parentNode.appendChild(note);
    function cid(c){ var b = c.querySelector(".emg-score[data-id]"); return b ? b.dataset.id : ""; }
    function rate(c){ var m = memo[cid(c)]; return m && m.rating > 0 ? m.rating : 0; }
    var busy = false;
    // find.js の「もっと見る」(loadFull) は施設カードを作り直す。作り直した枠には口コミが入らないので、読み込み済みの星は戻し、ほかは「口コミ」ボタンを付ける（新しい取り寄せはしない）
    function fillBoxes(){ document.querySelectorAll(".emg-score[data-id]").forEach(function(b){ var m = memo[b.dataset.id]; if (m && m.rating > 0) { if (!b.querySelector(".stars")) paint(b, m); } else if (!b.firstChild) lazy(b); }); }
    function apply(anchor){
      var mode = sel.value; if (busy) return; busy = true;
      try {
      fillBoxes();
      if (own) own.hidden = !hl.querySelector(".hc");
      if (!MODE[mode] && !own) return;
      var cards = [].slice.call(document.querySelectorAll(".emg-item.fc[data-ffi], .ux-c.dr-card[data-ffi], #hfList .hc"));
      var top0 = anchor ? anchor.getBoundingClientRect().top : 0, act = document.activeElement, groups = [], seen = [];
      cards.forEach(function(c){ var p = c.parentNode; if (seen.indexOf(p) < 0) seen.push(p); });
      // 同じ親の中でも、見出しなどで区切られた「つづきのカード」ごとに並べる（見出しの位置は動かさない）
      seen.forEach(function(p){ var run = []; [].forEach.call(p.children, function(ch){ if (cards.indexOf(ch) >= 0) run.push(ch); else { if (run.length) groups.push([p, run, ch]); run = []; } }); if (run.length) groups.push([p, run, null]); });
      groups.forEach(function(g){
        var arr = g[1].map(function(c, i){ if (c._idx == null && c._o == null) c._o = i; return {c: c, r: rate(c), i: c._idx != null ? c._idx : c._o}; });
        arr.sort(function(a, b){ if (!MODE[mode]) return a.i - b.i; if ((a.r > 0) !== (b.r > 0)) return a.r > 0 ? -1 : 1; if (a.r !== b.r) return mode === "ratingDesc" ? b.r - a.r : a.r - b.r; return a.i - b.i; });
        var same = arr.every(function(x, i){ return x.c === g[1][i]; });
        if (!same) arr.forEach(function(x){ g[0].insertBefore(x.c, g[2]); });
        if (MODE[mode]) arr.forEach(function(x){ var u = x.c.querySelector(".rs-unk"); if (x.r > 0) { if (u) u.remove(); } else if (!u && cid(x.c)) { var s = el("span", "rs-unk", "口コミ未取得"); s.style.cssText = "display:inline-block;margin:2px 0;font-size:.75rem;color:#6b625b"; var a = x.c.querySelector(".fc-acts"); (a || x.c).appendChild(s); } });
      });
      if (act && act !== document.activeElement && document.contains(act) && act.focus) act.focus({preventScroll: true});
      if (anchor) { var d = anchor.getBoundingClientRect().top - top0; if (d) window.scrollBy(0, d); }
      } finally { busy = false; }
    }
    function clear(){ document.querySelectorAll(".rs-unk").forEach(function(u){ u.remove(); }); note.hidden = !MODE[sel.value]; }
    window.__ratingSort = function(box){ apply(box.closest(".emg-item.fc, .ux-c.dr-card") || box); };
    // find.js が並べ直したあと（しぼりこみ・並び順の変更）にもういちど口コミ順にする
    ["change", "click", "input"].forEach(function(t){ document.addEventListener(t, function(e){ if (e.target === sel) clear(); setTimeout(function(){ apply(null); }, 0); }, true); });
    window.addEventListener("load", function(){ setTimeout(function(){ apply(null); }, 0); });
    // find.js が「もっと見る」で後から足したカードや、しぼりこみで並べ直したあとにも口コミ順を保つ（動かすものが無ければ何もしない）
    if (window.MutationObserver) { var tm = 0; new MutationObserver(function(){ if (busy) return; clearTimeout(tm); tm = setTimeout(function(){ apply(null); }, 60); }).observe(document.body, {childList: true, subtree: true}); }
  })();
  var boxes = document.querySelectorAll(".emg-score[data-id]");
  if (!boxes.length) return;
  boxes.forEach(photos);
  if (true) { boxes.forEach(lazy); return; } // REVIEW_ON_CLICK（index.html と同じ値）
  if (!("IntersectionObserver" in window)) { boxes.forEach(want); return; }
  // 口コミの欄は空のあいだ見えないので、会社の枠が画面に入ったら取り寄せる（しぼりこみで隠れている会社は取り寄せない）
  var io = new IntersectionObserver(function(es){ es.forEach(function(x){ if (x.isIntersecting && x.target.offsetParent) { io.unobserve(x.target); want(x.target.querySelector(".emg-score")); } }); }, {rootMargin: "200px"});
  boxes.forEach(function(b){ io.observe(b.parentElement); });
})();
