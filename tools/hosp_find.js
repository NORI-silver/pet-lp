// 動物病院を自分の条件でさがす（tools/hosp_find.py が prefkeep の関数と一緒に /hosp.js に書き出す）
// 最初に見えるのは「地域・動物・診療ニーズ」の3つ。ほかは「詳しい条件で絞り込む」の中（Nori 2026-11-15 の依頼書）
  var box = document.getElementById("hf");
  if (!box) return;
  var sel = document.getElementById("hospPref"), csel = document.getElementById("hfCity"), q = document.getElementById("hfQ"),
      dl = document.getElementById("hfCities"), det = document.getElementById("hfDet"), detN = document.getElementById("hfDetN"),
      list = document.getElementById("hfList"), sum = document.getElementById("hfSum");
  var SLUG = __SLUG__, LABEL = __LABEL__, NEAR = __NEAR__, av = null;
  var NEED = {night: ["night"], sunhol: ["sun", "hol"], h24: ["h24"], visit: ["visit"], spec: ["spec"]};
  var NEEDL = {night: "夜間・救急", sunhol: "日曜・祝日", h24: "24時間", visit: "往診", spec: "専門診療"};
  // 病院の種類は「そういう病院か」なので、書いていなければ合わない（要確認には入れない）
  var STRICT = {night: 1, visit: 1, catspec: 1, exospec: 1, large: 1, h24: 1, catroom: 1, ct: 1, spec: 1};
  var FEAT = [["night", "夜間・救急"], ["h24", "24時間"], ["visit", "往診"], ["catspec", "猫専門"], ["exospec", "うさぎ・鳥などの専門"], ["large", "大型犬の設備"],
              ["sun", "日曜診療"], ["hol", "祝日診療"], ["late", "19時以降も"], ["park", "駐車場あり"], ["card", "カード可"]];
  var on = {}, need = NEED[box.dataset.preset] ? box.dataset.preset : "", data = null, near = {}, shown = 30, firstCity = box.dataset.city || "";
  if (box.dataset.preset && !NEED[box.dataset.preset]) on[box.dataset.preset] = 1;
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
  function night(){ var h = new Date().getHours(); return h >= 19 || h < 8; }
  function keys(){ var k = Object.keys(on); (NEED[need] || []).forEach(function(x){ if (k.indexOf(x) < 0) k.push(x); }); return k; }
  function has(r, k){
    if (k === "spec") return ["catspec", "exospec", "large"].some(function(x){ return r.y.indexOf(x) >= 0; }) || !!(r.d && r.d.length);
    if (k.slice(0, 2) === "d:") return !!(r.d && r.d.indexOf(k.slice(2)) >= 0);
    return r.y.indexOf(k) >= 0;
  }
  function judge(r, ks){
    // 0＝合う、1＝書いていない（要確認）、2＝合わない
    var g = 0, unk = [];
    for (var i = 0; i < ks.length; i++) {
      var k = ks[i];
      if (has(r, k)) continue;
      if (r.no.indexOf(k) >= 0 || STRICT[k]) return [2, []];
      g = 1; unk.push(k);
    }
    return [g, unk];
  }
  function place(r){
    var t = (q.value || "").trim(), c = csel.value;
    var visitOk = function(x){ return r.y.indexOf("visit") >= 0 && (r.vz || (r.ar || "").indexOf(x) >= 0); };
    if (c && r.c !== c && !visitOk(c)) return false;
    if (t && !c) { var hay = [r.n, r.c, r.ad, r.st, r.ar].join(" "); if (hay.indexOf(t) < 0 && !visitOk(t)) return false; }
    return true;
  }
  function paintBtns(){
    box.querySelectorAll("button[data-v]").forEach(function(b){
      var k = b.dataset.v;
      b.setAttribute("aria-pressed", on[k] ? "true" : "false");
      // その県で1院も当てはまらないボタンは出さない（押しても0件になるだけなので）。犬・猫はいつも出す
      b.hidden = !!av && k !== "dog" && k !== "cat" && !on[k] && !av[k];
      if (on[k] && b.classList.contains("hf-x")) b.parentNode.classList.add("open");
    });
    var sos = box.querySelector(".hf-sos"); if (sos) sos.hidden = need === "night";
    box.querySelectorAll("button[data-need]").forEach(function(b){ b.setAttribute("aria-pressed", b.dataset.need === need ? "true" : "false"); });
    box.querySelectorAll(".hf-det .hf-r").forEach(function(r){ r.hidden = ![].some.call(r.querySelectorAll("button[data-v]"), function(b){ return !b.hidden; }); });
    var n = Object.keys(on).filter(function(k){ return !box.querySelector('.hf-det button[data-v="' + k + '"]') ? false : true; }).length;
    detN.textContent = n ? n : "";
  }
  // カードのイメージ写真（無料の写真素材。本物の病院の写真ではないので「イメージ」と書き、alt は空）。となりが同じ写真にならないよう順番に回す
  // カードの写真（使ってよいと確かめた写真だけ。tools/cardphoto.py と同じ形）。ない病院は共通の枠（Nori 2026-11-16）
  function picHtml(r){
    if (!r.ph) return '<div class="cs-ph cs-ph0"' + (r.rv ? ' data-gph="' + esc(r.rv) + '"' : '') + ' aria-hidden="true"></div>';
    var ps = r.ph[0], im = ps.map(function(p, i){ return '<img src="' + esc(p) + '" alt="' + esc(r.n) + 'の写真' + (i + 1) + '" width="520" height="347" loading="lazy" decoding="async">'; }).join("");
    return '<div class="cs-ph"><div class="cs-ph-s">' + im + '</div>' + (ps.length > 1 ? '<span class="cs-ph-n" aria-hidden="true">📷 ' + ps.length + '</span>' : '') + (r.ph[1] ? '<small class="cs-ph-c">' + esc(r.ph[1]) + '</small>' : '') + '</div>';
  }
  function card(r, unk){
    var b = [];
    if (r.a) b.push('<span>' + esc(r.a.length > 22 ? r.a.slice(0, 22) + "…" : r.a) + '</span>');
    FEAT.forEach(function(f){ if (f[0] === "late" && r.y.indexOf("night") >= 0) return; if (b.length < 6 && r.y.indexOf(f[0]) >= 0) b.push('<span>' + esc(f[1]) + '</span>'); });
    keys().forEach(function(k){ if (k.slice(0, 2) === "d:" && has(r, k)) b.push('<span>' + esc(k.slice(2)) + '</span>'); });
    unk.forEach(function(k){ b.push('<span class="u">' + esc(LABEL[k] || NEEDL[k] || k.slice(2)) + 'は不明</span>'); });
    var top = r.tel ? '<a href="tel:' + esc(r.tel) + '" data-k="tel" data-ga>📞 電話する</a>' : '<a href="' + esc(r.u) + '" target="_blank" rel="noopener" data-k="site" data-ga>公式サイト ↗</a>';
    var route = r.ad ? '<a class="l" href="https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(r.ad) + '" target="_blank" rel="noopener" data-k="route">📍 経路を見る</a>' : '';
    var sub = [];
    if (r.tel) sub.push('<a href="' + esc(r.u) + '" target="_blank" rel="noopener" data-k="site" data-ga>公式サイト</a>');
    if (r.pg) sub.push('<a href="' + esc(r.pg) + '">診療内容の詳細</a>');
    if (r.ad && r.y.indexOf("visit") < 0) sub.push('<a href="/?to=' + encodeURIComponent(r.ad) + '#form" data-k="taxi" data-ga>🚕 ペットタクシーの料金</a>');
    return '<div class="hc">' + picHtml(r) + '<a class="hc-n" href="' + esc(r.pg || r.u) + '"' + (r.pg ? '' : ' target="_blank" rel="noopener"') + '>' + esc(r.n) + '</a>'
      + (b.length ? '<p class="hc-b">' + b.join("") + '</p>' : '')
      + ((r.ad || r.c) ? '<p class="hc-l"><i aria-hidden="true">📍</i><span>' + esc(r.ad || r.c) + '</span></p>' : '')
      + (r.h ? '<p class="hc-l"><i aria-hidden="true">🕘</i><span>診療時間：' + esc(r.h) + '</span></p>' : '')
      + (r.x ? '<p class="hc-l"><i aria-hidden="true">💤</i><span>休診：' + esc(r.x) + '</span></p>' : '')
      + (r.ar ? '<p class="hc-l"><i aria-hidden="true">🏠</i><span>来てくれる地域：' + esc(r.ar) + '</span></p>' : '')
      + '<div class="hc-a2">' + top + route + '</div>'
      + '<div class="hc-a fc-acts">' + (r.rv ? '<div class="emg-score" data-id="' + esc(r.rv) + '"></div>' : '') + sub.join("") + '</div></div>';
  }
  function match(arr, ks, usePlace){
    var ok = [], unk = [];
    arr.forEach(function(r){
      if (usePlace && !place(r)) return;
      var j = judge(r, ks); if (j[0] === 2) return;
      (j[0] ? unk : ok).push([r, j[1]]);
    });
    return [ok, unk];
  }
  function draw(){
    paintBtns();
    var v = sel.value;
    if (!v) { list.innerHTML = ""; sum.innerHTML = "都道府県を選ぶと、合う病院が下に並びます"; box.parentNode.classList.remove("hf-on"); return; }
    if (!data) { sum.textContent = "読み込んでいます…"; return; }
    var ks = keys(), m = match(data.filter(function(r){ return !r.far; }), ks, true), ok = m[0], unk = m[1];
    // 夜の時間に開いたときは、夜間・救急の病院を先に（受付中とは言い切らない）
    var nightFirst = night() && need !== "night";
    if (nightFirst) ok.sort(function(a, b){ return (b[0].y.indexOf("night") >= 0) - (a[0].y.indexOf("night") >= 0); });
    var t = (q.value || "").trim(), pl = v + (csel.value ? " " + csel.value : t ? "「" + t + "」" : "");
    sum.innerHTML = esc(pl) + "で合う病院 " + ok.length + "院" + (unk.length ? "<small>ほかに、公式の情報に書いていないので要確認 " + unk.length + "院</small>" : "")
      + (nightFirst && ok.some(function(x){ return x[0].y.indexOf("night") >= 0; }) ? "<small>夜の時間なので、夜間・救急の病院を先に並べています</small>" : "");
    var all = ok.concat(unk), html = ""; pic = 0;
    all.slice(0, shown).forEach(function(x, i){
      if (i === ok.length && unk.length) html += '<p class="hf-h">条件が公式の情報に書いていない病院（行く前に確かめてください）</p>';
      html += card(x[0], x[1]);
    });
    if (all.length > shown) html += '<button type="button" class="hf-more">あと' + (all.length - shown) + '院を見る</button>';
    if (!ok.length) {
      // 0件のとき：どの条件を外せば何院見つかるか
      var alt = [];
      ks.forEach(function(k){
        var rest = ks.filter(function(x){ return x !== k; }), n = match(data.filter(function(r){ return !r.far; }), rest, true)[0].length;
        if (n) alt.push('<button type="button" data-drop="' + esc(k) + '">「' + esc(LABEL[k] || NEEDL[k] || (NEEDL[need] && NEED[need].indexOf(k) >= 0 ? NEEDL[need] : k.slice(2))) + '」を外す（' + n + '院）</button>');
      });
      if (csel.value || t) { var n2 = match(data.filter(function(r){ return !r.far; }), ks, false)[0].length; if (n2) alt.push('<button type="button" data-drop="place">' + esc(v) + 'の全体で見る（' + n2 + '院）</button>'); }
      alt.push('<a href="/emergency/#pref=' + encodeURIComponent(v) + '">緊急のときの連絡先</a>');
      html = '<div class="hf-none">' + esc(pl) + "で、この条件に合う病院はまだ見つかっていません。<div class=\"hf-alt\">" + alt.join("") + "</div></div>" + html;
    }
    // 少ないとき（3院まで）は、近くの県の病院も
    if (ok.length < 3) {
      var nb = [];
      (NEAR[v] || []).forEach(function(p){ if (near[p]) match(near[p].filter(function(r){ return !r.far; }), ks, false)[0].forEach(function(x){ nb.push([x[0], p]); }); });
      data.filter(function(r){ return r.far; }).forEach(function(r){ if (!judge(r, ks)[0]) nb.push([r, ""]); });
      if (nb.length) html += '<p class="hf-h">近くの県の病院</p>' + nb.slice(0, 8).map(function(x){ return card(x[0], []); }).join("");
      else if (!Object.keys(near).length) loadNear(v);
    }
    list.innerHTML = html;
    box.parentNode.classList.add("hf-on");
    if (window.petReviews) window.petReviews(list);
  }
  function loadNear(v){
    if (loadNear.v === v) return; loadNear.v = v;
    Promise.all((NEAR[v] || []).map(function(p){ return SLUG[p] ? fetch("/hospital/data/" + SLUG[p] + ".json").then(function(r){ return r.json(); }).then(function(j){ near[p] = j; }).catch(function(){}) : null; }))
      .then(function(){ if (sel.value === v) draw(); });
  }
  function load(){
    data = null; av = null; near = {}; loadNear.v = ""; draw();
    var v = sel.value; if (!v || !SLUG[v]) { fillCities([]); return; }
    fetch("/hospital/data/" + SLUG[v] + ".json").then(function(r){ return r.json(); }).then(function(j){
      if (sel.value !== v) return;
      data = j; av = {};  // その県のデータで1院以上に当てはまる条件
      j.forEach(function(r){ if (!r.far) { r.y.forEach(function(k){ av[k] = 1; }); (r.d || []).forEach(function(d){ av["d:" + d] = 1; }); } });
      fillCities(j); shown = 30; draw();
    }).catch(function(){ data = []; draw(); });
  }
  function fillCities(j){
    var cs = {}; j.forEach(function(r){ if (!r.far && r.c) cs[r.c] = (cs[r.c] || 0) + 1; });
    var keep = firstCity || csel.value; firstCity = "";
    var names = Object.keys(cs).sort();
    csel.innerHTML = '<option value="">市区町村すべて</option>' + names.map(function(c){ return '<option value="' + esc(c) + '">' + esc(c) + "</option>"; }).join("");
    dl.innerHTML = names.map(function(c){ return '<option value="' + esc(c) + '">'; }).join("");
    if (keep && cs[keep]) { csel.value = keep; q.value = keep; } else if (!cs[q.value]) { csel.value = ""; }
  }
  function onQ(){ var t = (q.value || "").trim(); csel.value = [].some.call(csel.options, function(o){ return o.value && o.value === t; }) ? t : ""; shown = 30; draw(); }
  q.addEventListener("input", onQ);
  box.addEventListener("click", function(ev){
    var b = ev.target.closest("button, a[data-sos]"); if (!b) return;
    if (b.dataset.sos !== undefined) { ev.preventDefault(); need = "night"; draw(); list.scrollIntoView({behavior: "smooth"}); try { window.gtag && gtag("event", "hosp_sos", {pref: sel.value || "all"}); } catch (x) {} return; }
    if (b.classList.contains("hf-mo")) { b.parentNode.classList.add("open"); return; }
    if (b.id === "hfGo") { list.scrollIntoView({behavior: "smooth"}); return; }
    if (b.id === "hfClear") { on = {}; need = ""; csel.value = ""; q.value = ""; shown = 30; draw(); return; }
    if (b.dataset.need !== undefined) {
      need = b.dataset.need;
      if (need === "spec") det.open = true;  // 専門診療は、診療科目などを選べるように開く
      shown = 30; draw();
      try { window.gtag && gtag("event", "hosp_filter", {key: "need:" + (need || "none"), on: 1, pref: sel.value || "all"}); } catch (x) {}
      return;
    }
    var k = b.dataset.v; if (!k) return;
    if (on[k]) delete on[k]; else on[k] = 1;
    shown = 30; draw();
    try { window.gtag && gtag("event", "hosp_filter", {key: k, on: on[k] ? 1 : 0, pref: sel.value || "all"}); } catch (x) {}
  });
  list.addEventListener("click", function(ev){
    var m = ev.target.closest(".hf-more"); if (m) { shown += 30; draw(); return; }
    var d = ev.target.closest("button[data-drop]");
    if (d) { var k = d.dataset.drop; if (k === "place") { csel.value = ""; q.value = ""; } else if (on[k]) delete on[k]; else need = ""; draw(); return; }
    // 公式サイト・電話・タクシー・経路はここだけで数える（ga.js は data-ga のリンクを数えない）。会社ごとに集計できるよう病院名と行き先のホストも送る（2026-11-16）
    var a = ev.target.closest("a[data-k]"), c = a && a.closest(".hc"), nm = c && c.querySelector(".hc-n");
    if (a) try { window.gtag && gtag("event", {taxi: "facility_taxi", tel: "tel_click", route: "hosp_route"}[a.dataset.k] || "official_site", {cat: "hospital", from: "hosp_find", company_name: nm ? nm.textContent.trim().slice(0, 80) : "", host: a.dataset.k === "site" ? a.hostname : "", pref: sel.value || "", transport_type: "beacon"}); } catch (x) {}
  });
  if (box.dataset.pref) { sel.value = box.dataset.pref; }
  function apply(){ load(); }
  if (box.dataset.pref) { prefLinks(sel.value); sel.addEventListener("change", function(){ prefPut(sel.value); prefLinks(sel.value); q.value = ""; apply(); }); apply(); }
  else { prefKeep(sel, function(){ q.value = ""; apply(); }); if (!sel.value) { draw(); prefGuess(sel, apply); } }
