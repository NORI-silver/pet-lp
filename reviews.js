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
    fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){
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
    }).catch(function(){ panel.textContent = "口コミを読み込めませんでした。時間をおいてもう一度お試しください。"; });
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
  var boxes = document.querySelectorAll(".emg-score[data-id]");
  if (!boxes.length) return;
  if (!("IntersectionObserver" in window)) { boxes.forEach(want); return; }
  // 口コミの欄は空のあいだ見えないので、会社の枠が画面に入ったら取り寄せる（しぼりこみで隠れている会社は取り寄せない）
  var io = new IntersectionObserver(function(es){ es.forEach(function(x){ if (x.isIntersecting && x.target.offsetParent) { io.unobserve(x.target); want(x.target.querySelector(".emg-score")); } }); }, {rootMargin: "200px"});
  boxes.forEach(function(b){ io.observe(b.parentElement); });
})();
