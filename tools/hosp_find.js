// 動物病院を自分の条件でさがす（tools/hosp_find.py が prefkeep の関数と一緒に /hosp.js に書き出す）
  var box = document.getElementById("hf");
  if (!box) return;
  var sel = document.getElementById("hospPref"), csel = document.getElementById("hfCity"), list = document.getElementById("hfList"), sum = document.getElementById("hfSum");
  var SLUG = __SLUG__, LABEL = __LABEL__, AVAIL = __AVAIL__;
  var on = {}, data = null, shown = 30, firstCity = box.dataset.city || "";
  var AN = {dog: 1, cat: 1};
  // 病院の種類は「そういう病院か」なので、書いていなければ合わない（要確認には入れない）
  var STRICT = {night: 1, visit: 1, catspec: 1, exospec: 1, large: 1, h24: 1, catroom: 1, ct: 1};
  (box.dataset.preset || "").split(",").forEach(function(k){ if (k) on[k] = 1; });
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
  function openNow(r){
    if (!r.t) return false;
    var d = new Date(), m = d.getHours() * 60 + d.getMinutes(), wd = "日月火水木金土".charAt(d.getDay());
    if (r.x && (r.x.indexOf(wd) >= 0 || /不定/.test(r.x))) return false;  // 今日が休みの病院、休みが決まっていない病院は出さない
    return r.t.some(function(x){ return (m >= x[0] && m < x[1]) || (m + 1440 >= x[0] && m + 1440 < x[1]); });
  }
  function night(){ var h = new Date().getHours(); return h >= 19 || h < 8; }
  function paintBtns(){
    var av = AVAIL[sel.value] || null;
    box.querySelectorAll("button[data-v]").forEach(function(b){
      var k = b.dataset.v;
      b.setAttribute("aria-pressed", on[k] ? "true" : "false");
      // その県で1院も当てはまらないボタンは出さない（押しても0件になるだけなので）。犬・猫はいつも出す
      b.hidden = !!av && !AN[k] && !on[k] && !av[k];
    });
    box.querySelectorAll(".hf-c").forEach(function(c){
      var mo = c.querySelector(".hf-mo"); if (!mo) return;
      var rest = [].filter.call(c.querySelectorAll("button.hf-x"), function(b){ return !b.hidden; });
      mo.hidden = !rest.length || c.classList.contains("open");
      [].forEach.call(c.querySelectorAll("button.hf-x"), function(b){ if (on[b.dataset.v]) c.classList.add("open"); });
    });
    box.querySelectorAll(".hf-r").forEach(function(r){ var c = r.querySelector(".hf-c"); if (!c.querySelector("select")) r.hidden = ![].some.call(c.querySelectorAll("button[data-v]"), function(b){ return !b.hidden; }); });
  }
  function judge(r){
    // 0＝合う、1＝書いていない（要確認）、2＝合わない
    var g = 0, unk = [];
    for (var k in on) {
      if (r.y.indexOf(k) >= 0 || (k.slice(0, 2) === "d:" && r.d && r.d.indexOf(k.slice(2)) >= 0)) continue;
      if (r.no.indexOf(k) >= 0 || STRICT[k]) return [2, []];
      g = 1; unk.push(k);
    }
    return [g, unk];
  }
  function card(r, unk){
    var b = [];
    if (openNow(r)) b.push('<span class="now">いま受付時間内</span>');
    ["night", "visit", "catspec", "exospec", "large", "h24"].forEach(function(k){ if (r.y.indexOf(k) >= 0) b.push('<span>' + esc(LABEL[k]) + '</span>'); });
    for (var k in on) if (b.length < 8 && ["night", "visit", "catspec", "exospec", "large", "h24", "dog", "cat"].indexOf(k) < 0 && (r.y.indexOf(k) >= 0 || (r.d && r.d.indexOf(k.slice(2)) >= 0))) b.push('<span>' + esc(LABEL[k] || k.slice(2)) + '</span>');
    unk.forEach(function(k){ b.push('<span class="u">' + esc(LABEL[k] || k.slice(2)) + 'は不明</span>'); });
    var ex = (r.a || "").split(/[・、,\s（）()]+/).filter(function(x){ return x && !/^(犬|猫|イヌ|ネコ|犬猫)$/.test(x.trim()); }).join("・");
    var h = '<div class="hc"><a class="hc-n" href="' + esc(r.u) + '" target="_blank" rel="noopener">' + esc(r.n) + '</a>'
      + (b.length ? '<p class="hc-b">' + b.join("") + '</p>' : '')
      + ((r.ad || r.c) ? '<p class="hc-l"><i aria-hidden="true">📍</i><span>' + esc(r.ad || r.c) + '</span></p>' : '')
      + (r.h ? '<p class="hc-l"><i aria-hidden="true">🕘</i><span>' + esc(r.h) + '</span></p>' : '')
      + (r.x ? '<p class="hc-l"><i aria-hidden="true">💤</i><span>休み：' + esc(r.x) + '</span></p>' : '')
      + (r.ar ? '<p class="hc-l"><i aria-hidden="true">🏠</i><span>来てくれる地域：' + esc(r.ar) + '</span></p>' : '')
      + (ex ? '<p class="hc-l"><i aria-hidden="true">🐾</i><span>' + esc(ex) + '</span></p>' : '')
      + (r.d ? '<p class="hc-l"><i aria-hidden="true">🩺</i><span>' + esc(r.d.join("・")) + '</span></p>' : '')
      + '<div class="hc-a fc-acts">' + (r.rv ? '<div class="emg-score" data-id="' + esc(r.rv) + '"></div>' : '')
      + (r.ad && r.y.indexOf("visit") < 0 ? '<a href="/?to=' + encodeURIComponent(r.ad) + '#form" data-k="taxi">🚕 タクシー料金</a>' : '')
      + (r.pg ? '<a href="' + esc(r.pg) + '">くわしく</a>' : '')
      + '<a class="o" href="' + esc(r.u) + '" target="_blank" rel="noopener" data-k="site">公式サイト ↗</a></div></div>';
    return h;
  }
  function draw(){
    paintBtns();
    var v = sel.value;
    if (!v) { list.innerHTML = ""; sum.innerHTML = "都道府県を選ぶと、合う病院が下に並びます"; box.parentNode.classList.remove("hf-on"); return; }
    if (!data) { sum.textContent = "読み込んでいます…"; return; }
    var c = csel.value, ok = [], unk = [], far = [];
    data.forEach(function(r){
      if (c && r.c !== c && !(r.y.indexOf("visit") >= 0 && (r.vz || (r.ar || "").indexOf(c) >= 0))) return;
      var j = judge(r); if (j[0] === 2) return;
      (r.far ? far : j[0] ? unk : ok).push([r, j[1]]);
    });
    // 夜の時間に開いたときは、夜間・救急の病院を先に
    var nightFirst = night() && !on.night;
    if (nightFirst) ok.sort(function(a, b){ return (b[0].y.indexOf("night") >= 0) - (a[0].y.indexOf("night") >= 0); });
    ok.sort(function(a, b){ return openNow(b[0]) - openNow(a[0]); });  // いま受付時間内の病院を先に
    var n = ok.length, place = v + (c ? " " + c : "");
    sum.innerHTML = esc(place) + "で合う病院 " + n + "院" + (unk.length ? "<small>ほかに、書いていないので要確認 " + unk.length + "院</small>" : "") + (nightFirst && n ? "<small>いまは夜なので、夜間・救急の病院を先に並べています</small>" : "");
    var all = ok.concat(unk), html = "", i = 0;
    all.slice(0, shown).forEach(function(x){
      if (i === ok.length && unk.length) html += '<p class="hf-h">条件が公式の情報に書いていない病院（行く前に確かめてください）</p>';
      html += card(x[0], x[1]); i++;
    });
    if (!all.length) {
      html = '<div class="hf-none">' + esc(place) + "で、この条件に合う病院はまだ見つかっていません。条件を1つ外すか、市区町村を「すべて」にしてみてください。</div>";
      if (far.length) html += '<p class="hf-h">近くの県の病院</p>' + far.map(function(x){ return card(x[0], x[1]); }).join("");
    }
    list.innerHTML = html + (all.length > shown ? '<button type="button" class="hf-more">あと' + (all.length - shown) + '院を見る</button>' : '');
    box.parentNode.classList.add("hf-on");
    if (window.petReviews) window.petReviews(list);
  }
  function load(){
    data = null; draw();
    var v = sel.value; if (!v || !SLUG[v]) { fillCities([]); return; }
    fetch("/hospital/data/" + SLUG[v] + ".json").then(function(r){ return r.json(); }).then(function(j){
      if (sel.value !== v) return;
      data = j; fillCities(j); shown = 30; draw();
    }).catch(function(){ data = []; draw(); });
  }
  function fillCities(j){
    var cs = {}; j.forEach(function(r){ if (!r.far && r.c) cs[r.c] = (cs[r.c] || 0) + 1; });
    var keep = firstCity || csel.value; firstCity = "";
    csel.innerHTML = '<option value="">市区町村すべて</option>' + Object.keys(cs).sort().map(function(c){ return '<option value="' + esc(c) + '">' + esc(c) + "（" + cs[c] + "）</option>"; }).join("");
    if (keep && cs[keep]) csel.value = keep;
  }
  box.addEventListener("click", function(ev){
    var b = ev.target.closest("button"); if (!b) return;
    if (b.classList.contains("hf-mo")) { b.parentNode.classList.add("open"); b.hidden = true; return; }
    if (b.id === "hfClear") { on = {}; csel.value = ""; shown = 30; draw(); return; }
    var k = b.dataset.v; if (!k) return;
    if (on[k]) delete on[k]; else on[k] = 1;
    shown = 30; draw();
    try { window.gtag && gtag("event", "hosp_filter", {key: k, on: on[k] ? 1 : 0, pref: sel.value || "all"}); } catch (x) {}
  });
  list.addEventListener("click", function(ev){
    var m = ev.target.closest(".hf-more"); if (m) { shown += 30; draw(); return; }
    var a = ev.target.closest("a[data-k]"); if (a) try { window.gtag && gtag("event", a.dataset.k === "taxi" ? "facility_taxi" : "official_site", {cat: "hospital", from: "hosp_find"}); } catch (x) {}
  });
  csel.addEventListener("change", function(){ shown = 30; draw(); });
  if (box.dataset.pref) { sel.value = box.dataset.pref; }
  function apply(){ load(); }
  if (box.dataset.pref) { prefLinks(sel.value); sel.addEventListener("change", function(){ prefPut(sel.value); prefLinks(sel.value); apply(); }); apply(); }
  else { prefKeep(sel, apply); if (!sel.value) { draw(); prefGuess(sel, apply); } }
