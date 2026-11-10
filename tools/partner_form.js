(function(){
  var GAS_URL = "__GAS__";
  var PLACES_KEY = "__PKEY__";
  var PREFS = __PREFS__, PREF_LL = __PREFLL__;
  var f = document.getElementById("partnerForm"), err = document.getElementById("p_err");
  function $(id){ return document.getElementById(id); }
  function picked(id){ return [].map.call(document.querySelectorAll("#" + id + " input:checked"), function(x){ return x.value; }); }
  function shown(x){ return !x.closest("[hidden]"); }
  // ボタンで選ぶ欄（.pt-one）の値は、選んだボタンの文字
  function val(x){ if (!x) return ""; if (x.classList.contains("pt-one")) { var c = x.querySelector("input:checked"); return c ? c.value : ""; } return String(x.value || "").trim(); }
  function sync(){
    f.querySelectorAll("[data-if]").forEach(function(d){ d.hidden = d.dataset.v.split("|").indexOf(val($(d.dataset.if))) < 0; });
  }
  f.addEventListener("change", sync); sync();
  // 数字の欄（.pt-q）は「3000円で 5kmまで」のように1行にまとめる
  function rowText(q){
    var out = [];
    q.querySelectorAll("input[type=number],select,.pt-one").forEach(function(x){
      var v = val(x);
      if (v) out.push(x.tagName === "INPUT" ? (x.dataset.p || "") + v + (x.dataset.u || "") : v);
    });
    return out.join(" ");
  }
  // ── お店の場所：住所や店名から候補を出して選ぶ（位置はお迎えの範囲の判定に使う）
  var shop = null, timer = 0, list = $("p_shopList"), inp = $("p_shop");
  function km(a, b){ var r = Math.PI / 180, x = (b[1] - a[1]) * r * Math.cos((a[0] + b[0]) / 2 * r), y = (b[0] - a[0]) * r; return Math.sqrt(x * x + y * y) * 6371; }
  function prefOf(t){ var m = String(t || "").replace(/^日本、?/, "").replace(/^〒\d{3}-?\d{4}\s*/, "").match(/^(北海道|東京都|大阪府|京都府|.{2,3}県)/); return m && PREFS.indexOf(m[1]) >= 0 ? m[1] : ""; }
  function pick(p){
    shop = p; inp.value = p.addr; list.hidden = true;
    $("p_shopOk").hidden = false; $("p_shopOk").textContent = "✓ " + p.addr;
    drawPrefs(true);
  }
  // 住所から位置を調べる（候補を選ばなくても、入れた住所のいちばん近い候補を使う）
  function lookup(q){
    return fetch("https://places.googleapis.com/v1/places:searchText", {method: "POST",
        headers: {"Content-Type": "application/json", "X-Goog-Api-Key": PLACES_KEY, "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"},
        body: JSON.stringify({textQuery: q, languageCode: "ja", regionCode: "jp", pageSize: 5})})
      .then(function(r){ return r.ok ? r.json() : {}; }).then(function(j){
        return ((j && j.places) || []).filter(function(p){ return p.location; }).map(function(p){
          var addr = String(p.formattedAddress || "").replace(/^日本、?/, "").replace(/^〒\d{3}-?\d{4}\s*/, "");
          return {addr: addr, ll: [p.location.latitude, p.location.longitude], pref: prefOf(addr)};
        }).filter(function(p){ return p.addr; });
      }).catch(function(){ return []; });
  }
  inp.addEventListener("input", function(){
    shop = null; $("p_shopOk").hidden = true; clearTimeout(timer);
    var q = inp.value.trim();
    if (q.length < 4 || !PLACES_KEY) { list.hidden = true; return; }
    timer = setTimeout(function(){
      lookup(q).then(function(ps){
        if (inp.value.trim() !== q) return;
        list.innerHTML = "";
        ps.forEach(function(p){ var li = document.createElement("li"); li.textContent = p.addr; li.addEventListener("mousedown", function(e){ e.preventDefault(); pick(p); }); list.appendChild(li); });
        if (ps.length) { var a = document.createElement("small"); a.className = "attr"; a.textContent = "Google Maps"; list.appendChild(a); }
        list.hidden = !ps.length;
      });
    }, 400);
  });
  inp.addEventListener("blur", function(){
    setTimeout(function(){ list.hidden = true; }, 150);
    var q = inp.value.trim();
    if (!shop && q.length >= 4 && PLACES_KEY) lookup(q).then(function(ps){ if (!shop && ps[0] && inp.value.trim() === q) { shop = ps[0]; $("p_shopOk").hidden = false; $("p_shopOk").textContent = "✓ " + ps[0].addr; drawPrefs(true); } });
  });
  // ── お迎えできる都道府県：お店の県と、範囲の中に県庁所在地が入る県（＋25km）を自動で選ぶ。近い順に10県をボタンで出し、残りは「ほかの都道府県」
  var RANGE = {"お店から10kmまで": 10, "20kmまで": 20, "30kmまで": 30, "50kmまで": 50, "80kmまで": 80, "もっと遠くても行く": 150};
  function chip(p, on){ return '<label><input type="checkbox" value="' + p + '"' + (on ? " checked" : "") + '><span>' + p + '</span></label>'; }
  function drawPrefs(auto){
    var near = $("p_prefs"), more = $("p_prefs2"), on = {};
    picked("p_prefs").concat(picked("p_prefs2")).forEach(function(p){ on[p] = 1; });
    if (!shop) { near.innerHTML = '<small style="color:var(--ink-3)">お店を選ぶと、近くの都道府県がここに出ます</small>'; return; }
    var r = RANGE[val($("p_radius"))] || 0;
    var order = PREFS.map(function(p, i){ return {p: p, d: km(shop.ll, PREF_LL[i])}; }).sort(function(a, b){ return a.d - b.d; });
    if (auto) { on = {}; if (shop.pref) on[shop.pref] = 1; if (r) order.forEach(function(o){ if (o.d <= r + 25) on[o.p] = 1; }); }
    near.innerHTML = order.slice(0, 10).map(function(o){ return chip(o.p, on[o.p]); }).join("");
    more.innerHTML = order.slice(10).sort(function(a, b){ return PREFS.indexOf(a.p) - PREFS.indexOf(b.p); }).map(function(o){ return chip(o.p, on[o.p]); }).join("");
  }
  $("p_radius").addEventListener("change", function(){ drawPrefs(true); });
  drawPrefs(false);
  function prefsAll(){ var a = picked("p_prefs").concat(picked("p_prefs2")); return PREFS.filter(function(p){ return a.indexOf(p) >= 0; }); }
  function prefsText(){ var on = prefsAll(); return on.length >= 30 ? (on.length === 47 ? "全国47都道府県" : "全国（" + PREFS.filter(function(p){ return on.indexOf(p) < 0; }).join("・") + "を除く" + on.length + "都道府県）") : on.join("・"); }
  // 受けられる時間 →「月・火・水 8:00〜20:00」のように1行（予約のしくみが時刻を読む）
  function hoursText(){
    var d = picked("p_days"), t = val($("p_allday")) === "24時間" ? "0:00〜24:00" : $("p_from").value + ":00〜" + $("p_to").value + ":00";
    return (d.length === 8 ? "毎日" : d.join("・")) + " " + t;
  }
  function missing(){
    var bad = [].filter.call(f.querySelectorAll("input:invalid,textarea:invalid"), shown)[0];
    if (bad) return bad;
    if (!inp.value.trim()) return inp;
    // 必ず答えていただくのは、エリア・時間・料金のうかがい方（と、料金をここで入力するときの料金の欄）だけ。ほかは、わかるところだけ
    var REQ = ["p_radius", "p_allday", "p_faremode"];
    var one = [].filter.call(f.querySelectorAll(".pt-one[data-req]"), function(x){ return shown(x) && !val(x) && (REQ.indexOf(x.id) >= 0 || x.closest(".pt-fare")); })[0];
    if (one) return one;
    if (!prefsAll().length) return $("p_prefs");
    if (!picked("p_days").length) return $("p_days");
    if (!picked("p_animals").length) return $("p_animals");
    var qs = [].filter.call(f.querySelectorAll(".pt-q"), shown);
    for (var i = 0; i < qs.length; i++) {
      var x = [].filter.call(qs[i].querySelectorAll("input[type=number]"), function(y){ return !y.dataset.opt && !y.value.trim(); })[0];
      if (x) return x;
    }
    return null;
  }
  var WHY = {p_shop: "車が出発するお店・事業所の住所を入れてください。", p_prefs: "お迎えできる都道府県を選んでください。", p_days: "受けられる曜日を選んでください。", p_cartype: "車の種類を選んでください。", p_animals: "乗せられる動物を選んでください。", p_agree: "確認のチェックを入れてください。"};
  f.addEventListener("submit", function(e){
    e.preventDefault(); err.style.display = "none";
    f.querySelectorAll(".missing").forEach(function(x){ x.classList.remove("missing"); });
    var bad = missing();
    if (bad) {
      err.textContent = WHY[bad.id] || (bad.type === "url" && bad.value ? "URLはhttps://から入れてください。" : "まだ選ばれていない項目があります（赤い枠のところ）。");
      err.style.display = "block"; bad.classList.add("missing");
      (bad.scrollIntoView ? bad.scrollIntoView({block: "center"}) : 0); if (bad.focus) bad.focus(); return;
    }
    var lines = [], co = $("p_co").value.trim(), apply = {};
    function put(k, v){ if (v) { lines.push("【" + k + "】" + v); apply[k] = v; } }
    f.querySelectorAll("[data-k]").forEach(function(x){
      if (!shown(x) || (x.parentNode.closest && x.parentNode.closest(".pt-q")) || x.id === "p_prefs" || x.id === "p_days" || x.id === "p_allday" || x.id === "p_cars" || x.id === "p_cartype" || x.id === "p_carother") return;
      put(x.dataset.k, x.classList.contains("checks") ? picked(x.id).join("・") : x.classList.contains("pt-q") ? rowText(x) : val(x));
    });
    put("都道府県", prefsText());
    put("受けられる時間帯", hoursText());
    var models = picked("p_cartype").concat($("p_carother").value.trim() ? [$("p_carother").value.trim()] : []);
    put("車", [val($("p_cars")), models.join("、")].filter(String).join("（") + (val($("p_cars")) && models.length ? "）" : ""));
    apply["都道府県の一覧"] = prefsAll().join("・");
    if (shop) apply["お店の位置"] = shop.ll.map(function(v){ return v.toFixed(4); }).join(",");
    apply["お店の住所"] = inp.value.trim();
    var body = new URLSearchParams();
    body.append("kind", "contact"); body.append("topic", "提携のお申し込み（" + co + "）");
    body.append("name", $("p_name").value.trim() + "（" + co + "）");
    body.append("email", $("p_email").value.trim());
    body.append("message", lines.join("\n"));
    body.append("apply", JSON.stringify(apply));
    body.append("website", f.website.value);
    var btn = f.querySelector("button"); btn.disabled = true;
    fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(r){
      if (!r || !r.ok) throw 0;
      f.style.display = "none"; $("p_done").style.display = "block";
    }).catch(function(){
      btn.disabled = false;
      err.textContent = "うまく送れませんでした。時間をおいてもう一度お試しください。"; err.style.display = "block";
    });
  });
})();
