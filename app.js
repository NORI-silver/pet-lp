
/* フォーム送信先（Google Apps Script のウェブアプリURL）。空の間は送信されません。 */
var GAS_URL = "https://script.google.com/macros/s/AKfycbyy-cTvD-t8DFGhEyA2IbFiXWoB50kl_2_97WiVdMlXec8sIbI2NVUkkyn-45VkIMc_5g/exec";
/* 道のりを聞く道路データの入口（OSRM と同じ形の API）。ここ1か所で切りかえる。
   いまの公開デモは「お金をもうけない使い方だけ」が条件なので、手数料を始める前に商用で使える入口へ替える（法定表示の確認 2026-11-08） */
var ROAD_API = "https://router.project-osrm.org";
/* 口コミ（星・本文）を「押したときだけ」取り寄せる（2026-11-08 戦略担当：訪問が増えても地図サービスの費用を増やさない）。
   false のあいだは今までどおり、カードや一覧が画面に入ったら星を取り寄せる（月の上限つき）。月1万PV（または口コミの月の上限の8割）を超えたら true にして gen_areas.py を実行する */
var REVIEW_ON_CLICK = true;
/* お誘いした会社だけの見本の画面（?demo=…。Nori 2026-11-02）。その会社だけ名前と口コミつきで出し、問い合わせは送らない */
var DEMO = {tok: (function(){ try { return new URLSearchParams(location.search).get("demo") || ""; } catch (e) { return ""; } })(), ok: false, name: ""};
/* アクセス解析に操作の回数だけを送る（入力内容は送らない）。ga.js が動いていないときは何もしない */
function track(name, params){ if (window.gtag) gtag("event", name, params || {}); }
/* 計測に使う項目の名前（ペットごとの欄は pet_… にまとめる）。値は使わない */
function fieldName(el){ return String(el && (el.name || el.id) || "").replace(/^p\d+_/, "pet_").slice(0, 40); }
var formEntry = "";
/* 計測に使う会社のIDと名前（公式サイトに出ている社名だけ） */
function coInfo(c){ var co = window.CO_SITE_ && window.CO_SITE_[c.id]; return {id: c.id, company_id: c.id, company_name: String(co ? co[0] : c.label || "").slice(0, 80), bookable: c.display_only ? 0 : 1}; }
var partnersTracked = false;
var MAX_PETS = 5;
var lastSig = "", reqKey = "";
/* 前回の入力をこの端末に残す日数（日時以外をもう一度入れ直さなくてよいように） */
var SAVE_KEY = "petReq"; // 以前の版の保存先（読み込み時に消す）

(function(){
  var form = document.getElementById("petForm");
  var err = document.getElementById("err");
  var petsBox = document.getElementById("pets");
  var countSel = document.getElementById("petCount");
  var $ = function(id){ return document.getElementById(id); };

  var routeDetails = null, quoteCards = [], chosenQuote = null, chosenPicks = [], quoteSeq = 0, sending = false; // chosenPicks：複数社に依頼するとき選んだ会社
  var quoteLegs = null, chosenGo = null, chosenBack = null; // 往復を行き・帰りで別の会社に頼むとき
  var quoteTimer = 0, quoteRefreshTimer = 0;
  function clearPartners(){
    quoteSeq++; quoteCards = []; chosenQuote = null; chosenPicks = []; quoteLegs = null; chosenGo = null; chosenBack = null;
    $("partnerResults").hidden = true; $("partnerCards").replaceChildren(); $("partnerRest").replaceChildren(); $("partnerRestBtn").hidden = true; restOpen = false;
    $("legSplit").hidden = true; $("legGo").replaceChildren(); $("legBack").replaceChildren();
    $("sendSelected").hidden = true; $("taxiBox").hidden = true;
    clearTimeout(quoteTimer); clearTimeout(quoteRefreshTimer);
    quotesLoaded = false; syncContact();
  }
  function conditionsChanged(event){
    if (["name","tel","email","notes","agree","website","partnerSort","partnerDist"].indexOf(event.target.id || event.target.name) >= 0) return; // 並び順を変えても、候補は取り直さない
    clearPartners(); queuePartners();
    if (!$("partnerNeed").hidden) showNeed(); // 出ている一覧は、入れたらすぐ減らす
  }
  form.addEventListener("input", conditionsChanged);
  form.addEventListener("change", conditionsChanged);
  function queuePartners(){
    clearTimeout(quoteTimer);
    if (sending) return;
    drawTaxis();
    if (partnerBlock() === "") showLoading(); // 条件がそろっていれば、待つあいだもすぐ「探しています」を出す
    quoteTimer = setTimeout(loadPartners, 650);
  }
  function showLoading(){
    $("partnerResults").hidden = false; $("partnerCards").replaceChildren(); $("partnerRest").replaceChildren(); $("partnerRestBtn").hidden = true;
    $("partnerStatus").innerHTML = '<span class="partner-loading"><span class="spin" aria-hidden="true"></span><span>ぴったりの事業者を選んでいます…<small>条件に合う会社と料金の目安を調べています。10秒ほどかかることがあります。</small></span></span>';
  }
  // カードを出せない理由。"fields"＝入っていない項目がある、"time"＝お迎えが近すぎる・帰りが行きより前、""＝そろっている
  function partnerBlock(){
    if (!GAS_URL) return "off";
    // 問い合わせできる会社がいない県は、場所・日時・ペットの種類と体重だけで候補を出す（2026-11-08「少なくする」）
    var lite = !prefOpen();
    var required = ["pref","pickup","dropoff","date","hour","minute","petCount"].concat(lite ? [] : ["riders","luggage"]);
    if (required.some(function(id){return !$(id).value || !$(id).checkValidity();})) return "fields";
    if (!petsBox.children.length || Array.prototype.some.call(petsBox.querySelectorAll("input,select"),function(el){return !(lite && el.closest(".opt-lite")) && !el.checkValidity();})) return "fields";
    var fd = new FormData(form), at = new Date(fd.get("date") + "T" + fd.get("hour") + ":" + fd.get("minute") + ":00+09:00");
    if (!fd.get("trip")) return "fields";
    if (fd.get("trip") === "往復") {
      if (["retDate","retHour","retMinute","retPickup","retDropoff"].some(function(id){return !$(id).checkValidity();})) return "fields";
      if (!(new Date(fd.get("ret_date") + "T" + fd.get("ret_hour") + ":" + fd.get("ret_minute") + ":00+09:00") > at)) return "time";
    }
    if (!(at > new Date(Date.now() + MIN_LEAD_H * 3600e3))) return "time";
    return "";
  }
  // 入っていない項目：名前（ラベル）と欄。ラジオは1つにまとめる
  function fieldName(el){
    var lb = el.labels && el.labels[0] && !el.labels[0].contains(el) ? el.labels[0] : null, f = el.closest(".f");
    if (!lb && f) lb = f.querySelector("label[for], .lbl");
    var t = lb ? lb.cloneNode(true) : null;
    if (t) t.querySelectorAll(".any, .need").forEach(function(x){ x.remove(); });
    var name = (t ? t.textContent : el.getAttribute("aria-label") || "").trim();
    var pet = el.closest(".pet"), many = petsBox.querySelectorAll(".pet").length > 1;
    return pet && many ? pet.querySelector(".pet-h b").textContent + "の" + name : name;
  }
  function missingFields(before){
    var seen = {}, out = [];
    Array.prototype.forEach.call(form.querySelectorAll("input,select,textarea"), function(el){
      if (el.name === "website" || el.disabled || el.checkValidity()) return;
      if (before && !(el.compareDocumentPosition(before) & Node.DOCUMENT_POSITION_FOLLOWING)) return;
      var name = fieldName(el);
      if (!name || seen[name]) return;
      seen[name] = 1; out.push({el: el, name: name});
    });
    return out;
  }
  // その欄までスクロールして、選びやすいようにする
  function jumpTo(el){
    var target = el.type === "radio" ? el.closest(".seg") || el : el;
    target.scrollIntoView({block: "center", behavior: "smooth"});
    try { el.focus({preventScroll: true}); } catch (e) { el.focus(); }
  }
  function markMissing(list){
    list.forEach(function(x){ (x.el.type === "radio" ? x.el.closest(".seg") || x.el : x.el).classList.add("missing"); });
  }
  function needButtons(list){
    var box = document.createElement("div"); box.className = "need-list";
    list.forEach(function(x){
      var b = document.createElement("button"); b.type = "button"; b.textContent = x.name;
      b.addEventListener("click", function(){ jumpTo(x.el); });
      box.appendChild(b);
    });
    return box;
  }
  form.addEventListener("input", function(e){ var t = e.target.type === "radio" ? e.target.closest(".seg") : e.target; if (t) t.classList.remove("missing"); });
  form.addEventListener("change", function(e){ var t = e.target.type === "radio" ? e.target.closest(".seg") : e.target; if (t) t.classList.remove("missing"); });
  // 事業者のカードを出すのに足りない項目を、カードの場所に出す（入力を始めてから）
  function showNeed(){
    var box = $("partnerNeed"), list = missingFields($("partnerResults"));
    var started = ["pickup","dropoff","date"].some(function(id){ return $(id).value; }) || Array.prototype.some.call(petsBox.querySelectorAll("input[name$=_weight]"), function(el){ return el.value; });
    box.hidden = !started || !list.length;
    if (box.hidden) return;
    box.replaceChildren(document.createTextNode("事業者と料金を出すには、あと次の項目を入れてください（押すとその場所へ移ります）。"), needButtons(list));
  }
  function loadPartners(){
    quotesLoaded = false; syncOpenNote();
    showNeed();
    if (sending) return;
    var block = partnerBlock();
    if (block === "fields" || block === "off") { $("partnerResults").hidden = true; syncContact(); return; }
    if (block === "time") {
      $("partnerResults").hidden = false; $("partnerCards").replaceChildren(); $("partnerRest").replaceChildren(); $("partnerRestBtn").hidden = true;
      $("partnerStatus").textContent = "お迎えは、いまから" + MIN_LEAD_H + "時間後より先の日時を選んでください（往復のときは、帰りを行きより後に）。";
      return;
    }
    if (!routeDetails) { showLoading(); return; } // 道のりを調べ終わったら、もう一度呼ばれる
    var searchSeq = ++quoteSeq, search = requestPayload().body;
    ["name","tel","email","notes","contact","website","pets","breed","age","sex","est_fare","est_fare_text"].forEach(function(k){search.delete(k);});
    search.set("kind", "quotes"); if (DEMO.tok) search.set("demo", DEMO.tok); if (window.PET_STAFF) search.set("staff", "1"); // 運営者の動作確認は需要の記録で分ける（ga.js）
    // 入力を減らした県では、たずねていない項目をいちばん広く探せる値で調べる（1人・手荷物・ケージはどちらでも・介護なし）
    if (!prefOpen()) [["riders","1人"],["luggage","手荷物くらい"],["cage","どれでも"],["care","不要"]].forEach(function(d){ if (!search.get(d[0])) search.set(d[0], d[1]); });
    showLoading();
    fetch(GAS_URL,{method:"POST",body:search}).then(function(res){return res.json();}).then(function(result){
      if (searchSeq !== quoteSeq || sending) return;
      if (!result || !result.ok || result.selection_version !== 1 || !Array.isArray(result.cards)) throw new Error("quotes");
      quoteLegs = result.legs || null; scoresReady = result.scores === 1; // 予約のしくみが新しい版のときだけ星をまとめて取り寄せる
      paintPartners(result.cards);
      // 戦略の数字（2026-11-08）：候補を出した回数・問い合わせできる会社が1社以上出た回数。1ページで1回だけ数える
      if (!partnersTracked) { var nb = result.cards.filter(function(c){ return !c.display_only; }).length; partnersTracked = true; track("view_partners", {count: result.cards.length, bookable: nb, pref: $("pref").value}); if (nb) track("view_bookable", {count: nb, pref: $("pref").value}); }
      quoteRefreshTimer = setTimeout(function(){clearPartners();queuePartners();}, 14*60000);
    }).catch(function(){
      if (searchSeq !== quoteSeq || sending) return;
      $("partnerStatus").textContent = "候補を確認できませんでした。少し待っても表示されない場合は、日時や条件を入れ直してください。依頼は送信されていません。";
    });
  }
  // 口コミ本文：押したときだけ取り寄せる（毎回取り寄せ、保存しない）
  function toggleReviews(id, panel, btn){
    if (!panel.hidden) { panel.hidden = true; btn.setAttribute("aria-expanded", "false"); return; }
    panel.hidden = false; btn.setAttribute("aria-expanded", "true");
    track("open_reviews");
    if (panel.dataset.done) return;
    panel.textContent = "口コミを読み込んでいます…";
    var body = new URLSearchParams(); body.set("kind", "reviews"); body.set("partner_id", id); if (DEMO.tok) body.set("demo", DEMO.tok);
    fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){ fillReviews(panel, j); })
      .catch(function(){ panel.textContent = "口コミを読み込めませんでした。時間をおいてもう一度お試しください。"; });
  }
  // 取り寄せた口コミを枠に入れる（書いた人・元の口コミへのリンク・並び順の説明・出どころは規約で必要）
  function fillReviews(panel, j){
      if (!j || !j.ok || !Array.isArray(j.reviews)) throw 0;
      panel.dataset.done = "1"; panel.replaceChildren();
      var head = document.createElement("p"); head.className = "review-head";
      head.textContent = "関連度の高い順に、最大5件を表示しています（全" + j.count + "件）。";
      panel.appendChild(head);
      j.reviews.forEach(function(v){
        var item = document.createElement("div"); item.className = "review-item";
        var who = document.createElement("div"); who.className = "review-who";
        if (v.photo) { var img = document.createElement("img"); img.src = v.photo; img.alt = ""; img.width = 28; img.height = 28; img.loading = "lazy"; img.referrerPolicy = "no-referrer"; who.appendChild(img); }
        var name = document.createElement(v.authorUrl ? "a" : "span"); name.textContent = v.author || "投稿者";
        if (v.authorUrl) { name.href = v.authorUrl; name.target = "_blank"; name.rel = "noopener"; }
        var meta = document.createElement("small"); meta.textContent = "★" + v.rating + (v.when ? "・" + v.when : "");
        who.append(name, meta); item.appendChild(who);
        if (v.text) { var t = document.createElement("p"); t.textContent = v.text; item.appendChild(t); }
        if (v.url) { var a = document.createElement("a"); a.className = "review-link"; a.href = v.url; a.target = "_blank"; a.rel = "noopener"; a.textContent = "元の口コミ ↗"; item.appendChild(a); } // 規約で口コミごとに必要なリンク。目立たないよう小さく、別のタブで開く
        panel.appendChild(item);
      });
      var src = document.createElement("p"); src.className = "partner-review-src"; src.textContent = "Google Maps"; panel.appendChild(src);
  }
  // 押したときだけ取り寄せる形（REVIEW_ON_CLICK）：「口コミを見る」を押したら星と本文をまとめて取り寄せる。
  // save(rv) は星を覚えておく関数（並べ直しても消えないように）
  function lazyReviews(id, save){
    var holder = document.createElement("div"), p = document.createElement("p"), b = document.createElement("button"), src = document.createElement("span");
    p.className = "partner-score"; b.type = "button"; b.className = "partner-review-open"; b.textContent = "口コミを見る";
    src.className = "partner-review-src"; src.textContent = "Google Maps"; p.append(b, src); holder.appendChild(p);
    b.addEventListener("click", function(){
      b.disabled = true; b.textContent = "口コミを読み込んでいます…"; track("open_reviews");
      var body = new URLSearchParams(); body.set("kind", "reviews"); body.set("partner_id", id); if (DEMO.tok) body.set("demo", DEMO.tok);
      fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){
        if (j && j.ok && !(j.rating > 0)) throw "none"; // Googleマップに口コミがまだない（上限や不具合とは別）
        if (!j || !j.ok) throw 0;
        var rv = {rating: j.rating, count: j.count}; save(rv);
        // 星の行（出どころの表示「Google Maps」は規約で必要）と、取り寄せた口コミを開いた枠
        var score = document.createElement("p"); score.className = "partner-score";
        var stars = document.createElement("span"); stars.className = "stars"; stars.setAttribute("aria-hidden", "true");
        stars.style.setProperty("--fill", Math.max(0, Math.min(5, rv.rating)) / 5 * 100 + "%");
        var num = document.createElement("b"); num.textContent = Number(rv.rating).toFixed(1);
        score.setAttribute("aria-label", "口コミの評価 5点中" + Number(rv.rating).toFixed(1) + "点、" + rv.count + "件");
        var open = document.createElement("button"); open.type = "button"; open.className = "partner-review-open"; open.textContent = "口コミ" + rv.count + "件を見る";
        var src2 = document.createElement("span"); src2.className = "partner-review-src"; src2.textContent = "Google Maps";
        score.append(stars, num, open, src2);
        var panel = document.createElement("div"); panel.className = "review-panel";
        open.addEventListener("click", function(){ toggleReviews(id, panel, open); });
        holder.replaceChildren(score, panel); fillReviews(panel, j); open.setAttribute("aria-expanded", "true");
      }).catch(function(e){ save(null); var n = document.createElement("p"); n.className = "partner-review-src"; n.textContent = e === "none" ? "Googleマップの口コミはまだありません" : "口コミを読み込めませんでした。時間をおいてもう一度お試しください"; holder.replaceChildren(n); });
    });
    return holder;
  }
  // 問い合わせできる会社がいる都道府県（tools/gen_areas.py が booking/Code.gs の OPEN_PARTNERS から作る）。県を選んだ時点で知らせる（2026-11-08 飼い主目線のレビュー #1）
  /*OPEN_PREFS*/var OPEN_PREFS = ["京都", "兵庫", "北海道", "千葉", "和歌山", "埼玉", "大阪", "奈良", "広島", "東京", "滋賀", "神奈川", "福岡"];/*/OPEN_PREFS*/
  /*AREA_PREFS*/var AREA_PREFS = ["三重", "京都", "佐賀", "兵庫", "北海道", "千葉", "和歌山", "埼玉", "大阪", "奈良", "宮城", "山梨", "岐阜", "岩手", "広島", "徳島", "愛知", "東京", "栃木", "滋賀", "石川", "神奈川", "福岡", "群馬", "茨城", "長崎", "静岡"];/*/AREA_PREFS*/
  // 会社が見つかっていない県は、選ぶ前に分かるよう「（候補なし）」を付ける（値は県名のまま）
  function markPrefs(){
    if (!AREA_PREFS.length) return;
    Array.prototype.forEach.call($("pref").options, function(o){
      if (!o.value || AREA_PREFS.indexOf(shortPref(o.value)) >= 0) return;
      var v = o.value; o.value = v; o.textContent = v + "（候補なし）";
    });
  }
  markPrefs();
  var quotesLoaded = false; // いま出ている候補がサーバーから届いたものか
  function shortPref(v){ return String(v || "").replace(/[都府県]$/, ""); }
  function prefOpen(){ var v = $("pref").value; return !v || DEMO.ok || OPEN_PREFS.indexOf(shortPref(v)) >= 0; }
  // ご連絡先は、送れる会社がいるときだけ出す（いないのに電話番号まで入れさせない）
  function syncContact(){
    var bookable = quoteCards.some(function(c){ return !c.display_only; }) || !!(quoteLegs && quoteLegs.go && quoteLegs.go.some(function(c){ return !c.display_only; }));
    if (quotesLoaded) lastBookable = bookable;
    var shown = quotesLoaded ? bookable : prefOpen() || lastBookable; // 調べ直しているあいだは、前の結果のまま（欄が消えたり出たりしないように）
    $("contactBox").hidden = !shown;
    syncLite(!prefOpen() && !shown);
    if (shown && !prefOpen()) $("openNote").hidden = true; // ほかの県の会社が、お迎えか行き先の近くにいるとき
    var none = $("contactNone");
    if (!shown && quotesLoaded) {
      if (!none) { none = document.createElement("p"); none.id = "contactNone"; none.className = "contact-none"; $("contactBox").parentNode.insertBefore(none, $("contactBox")); }
      none.textContent = "この条件では、いまこのサイトから問い合わせできる会社がないため、ご連絡先の入力はいりません。料金の目安をくらべて、気になる会社には公式サイトから直接おたずねください。";
      none.hidden = false;
    } else if (none) none.hidden = true;
  }
  // 入力を減らすとき：たずねない欄を隠して、入っていなくても先へ進めるようにする（送れる会社が出たら元に戻す）
  function syncLite(lite){
    form.classList.toggle("lite", lite);
    form.querySelectorAll(".opt-lite input, .opt-lite select, .opt-lite textarea").forEach(function(el){ el.disabled = lite; });
  }
  function syncOpenNote(){
    var v = $("pref").value, n = $("openNote");
    n.hidden = prefOpen();
    if (!n.hidden) n.textContent = v + "では、いまこのサイトから問い合わせできる会社はまだありません。お迎えの場所・日時と、ペットの種類・体重を入れると、会社の候補と料金の目安、公式サイトへのリンクをご覧いただけます（ご連絡先の入力はいりません）。";
    syncContact();
  }
  var lastBookable = false;
  $("pref").addEventListener("change", function(){ lastBookable = false; syncOpenNote(); });
  // 名前を伏せた会社に「会社A・B…」の目印を付けて、くらべやすくする（2026-11-08 レビュー #4）
  // まだ提携していない会社も、社名と公式サイトへのリンクを出す（Nori 2026-11-08「すすめていいよ」）。問い合わせはできないまま。社名が分からない会社だけ「会社A・B…」の目印
  /*NO_FEE*/var NO_FEE = {"nowait": ["D4adf70b"], "nojam": ["D2644ea0", "D66c4625", "Df31960d"]};/*/NO_FEE*/
  /*CO_SITE*/var CO_SITE = {"De5faaf3": ["COCOタク 杉並店", "https://pet-taxi-tokyo-suginami.com/"], "De33f4b4": ["COCOタク 東京世田谷店", "https://petcocotaxi-setagaya.com/"], "D2644ea0": ["COCOタク 東京中央店", "https://tc-cocotaxi.com/"], "Ddc3e31e": ["COCOタク 東京墨田店", "https://cocotaxi-pet-tokyo-sumida.com/"], "Df5f495f": ["COCOタク 東京多摩店", "https://coco-pet-taxi-tokyo-tama.com/"], "D400f012": ["COCOタク 東京小平店", "https://www.cocotaxi-sawan.com/"], "D3f74ac5": ["COCOタク 東京荒川店", "https://pet-taxi-adachi.com/"], "D0e1ab9c": ["COCOタク 東京足立店", "https://cocotaxiadachi.com/"], "D57763aa": ["COCOタク 武蔵野店", "https://coco-taxi-musashino.com/"], "D98b1024": ["COCOタク 渋谷店", "https://cocotaku-shibuya.com/"], "De308905": ["COCOタク 練馬杉並店", "https://cocotaku-nerima-suginami.com/"], "D45d6d56": ["COCOタク 西東京店", "https://cocotaxi.tokyo/"], "Db508c4d": ["COCOタク 足立中央本町店", "https://pet-cocotaxi-katusika.com/"], "Dbcd4199": ["COCOタク 青山店", "https://cocotaku.com/"], "D3661eb1": ["PETTA東京（ペッタ）", "https://www.petta-tokyo.com/"], "D1e44e13": ["cocoタク 大田・田園調布店", "https://coco-taxi.com/"], "D355c31f": ["サポっ人 中目黒店", "https://seikatsunosupport.com/pettaxi/"], "D7c32399": ["ペットタクシー こうのとり（AirLine Haneda）", "https://airline-haneda.com/taxi/"], "D0d1c8b4": ["ペットタクシー ワンネス", "https://oneness-taxi.com/"], "D692c9a6": ["ペットタクシー ワンハウス", "https://onehouse.jp/"], "D7922e74": ["ペトタクファインド", "https://pettaxi-find.com/chiba/"], "D72ab934": ["COCOタク 川崎店", "https://www.growing-group.co.jp/"], "D789b979": ["COCOタク 横浜店", "https://cocotaxi-yokohama.com/"], "Dfc12ca3": ["COCOタク 横浜港北店", "https://cocotaxi-yokohama-kouhoku.com/"], "Da1ed552": ["COCOタク 横浜磯子店", "https://pet-taxi-yokohama-isogo.com/"], "Dbf4a40c": ["COCOタク 湘南平塚店", "https://coco-taxi-shonan-hiratuka.com/"], "D0d611b0": ["COCOタク 湘南店", "https://www.cocotaku-shonan.com/"], "Dd6859ef": ["COCOタク 神奈川中央店", "https://coco-pettaxi-kanagawa-chuo.com/"], "D3cc975b": ["COCOタク 神奈川北店", "https://cocotaxi-wans.com/"], "D227d031": ["COCOタク 西湘秦野店", "https://pet-taxi-cocotaku-hadano.com/"], "De65cb2d": ["Legolas House（レゴラスハウス）", "https://www.legolashouse.com/"], "D945f580": ["ikimono care（イキモノケア）", "https://www.ikimonocare.com/"], "D5598693": ["ふわふわペットタクシー", "https://pet-yokohama.com/"], "D5604536": ["やこうDogはうす", "https://yakodoghouse.com/"], "Dc7b4703": ["わんにゃんハイヤー Angel Buggy", "https://www.angel-buggy.com/"], "D68f9d95": ["ペットタクシー Animals", "https://h12150825.wixsite.com/taxi-animals"], "D8da1ced": ["ペットタクシー わんだにゃー", "https://wan.da-nya.com/"], "Daed391e": ["ペットタクシー シアンシャ 厚木店", "https://chienchat.jp/atsugi/"], "D0437ae3": ["ペットタクシー シアンシャ 鎌倉店", "https://chienchat.jp/kamakura/"], "D5f32b1e": ["三和交通 ペットタクシー", "https://www.sanwakoutsu.co.jp/special/pet/"], "Daf1e25b": ["湘南Dog Life College（ペットタクシー）", "https://www.shonan-dog-college.jp/taxi"], "D0b50c1a": ["湘南ペットハイヤー", "https://www.shonan-web.com/sub6.html"], "D06b72ea": ["鎌倉ペットタクシー", "https://pets-taxi.net/ja/kamakurapettaxi"], "D40a4aa0": ["COCOタク さいたま南店", "https://cocotaxi-saitama.com/"], "Dfcb8480": ["COCOタク 埼玉川越店", "https://pet-taxi-saitama-kawagoe.jp/"], "D853ae97": ["COCOタク 埼玉春日部店", "https://pet-taxi-kasukabe.com/"], "D83f23cc": ["COCOタク 川口店", "https://cocokawaguchi.com/"], "D2a4caa6": ["COCOタク 練馬店", "https://pet-taxi-nerima.com/"], "D3cc1cce": ["ペットケア151A", "https://petcare-151a.com/pettaxi.html"], "Dcfbfbf2": ["COCOタク 船橋店", "https://cocotaku-funabashi.moe/"], "De3f35f2": ["コインペットタクシー シエロ", "https://pettaxi.jp/"], "D3c85024": ["ペットタクシー パールのしっぽ", "https://pearlno-shippo.com/"], "Dedcfcd2": ["動物苑（ペット送迎）", "https://www.pet594.com/pet-transport/"], "Dc28c19e": ["ワンワンハウス（ペットタクシー）", "https://wan-wan-house.com/pet-taxi/"], "Dc05105b": ["COCOタク 新札幌店", "https://pet-taxi-sc.com/"], "Db405639": ["D-RIDE（ペットタクシー）", "https://d-ride.jp/pettaxi.html"], "D44948b6": ["ぺトタク（札幌・小樽）", "https://pet-tax.com/"], "D13b7c6f": ["ペット専用タクシー aiai", "https://pet-taxi-aiai.com/"], "D1f53c72": ["COCOタク岩手盛岡店", "https://cocomorioka.iwate.jp/"], "D18363bd": ["COCOタク 仙台店", "https://pet-taxi-sendai.com/"], "D4adf70b": ["PETRIP", "https://petrip.co.jp/"], "D30e1838": ["ニャンワンクラブ（ペットタクシー）", "https://nyanwan.jp/"], "D1132ff9": ["冨士タクシー（ペットタクシー）", "https://www.fuji-taxinet.jp/service/pet-taxi.php"], "Da40f372": ["ペットタクシー With☆（ウィズ）", "https://pet-taxi.sakura.ne.jp/"], "Dd472236": ["ペットタクシー COCOタク静岡", "https://cocotaxi-shizuoka.com/"], "Dc2d8672": ["COCOタク 三河豊田店", "https://pet-taxi-aichi-mikawa.com/"], "D7d26cb4": ["COCOタク 名古屋尾張店", "https://pet-taxi-nagoya-owari.com/"], "D6c3b09b": ["COCOタク 愛知稲沢店", "https://cocotaku-inazawa-aichi.com/"], "D611ee5f": ["COCOタク 知多武豊店", "https://pet-taxi-aichi-chita-taketoyo.com/"], "Df997a81": ["COCOタク 穂の国店", "https://pet-taxi-aicih-toyohashi-honokuni.com/"], "D44cfd16": ["HAPPY WITH（ペットタクシー）", "https://happywith.pet/pettaxi/"], "D1834601": ["ZEROペットタクシー", "https://zero808.co.jp/pettaxi/"], "D7f0d2a2": ["COCOタク 京都店", "https://pet-taxi-kyoto.com/"], "Dc9d8a2b": ["PetTAXI24", "https://j-pettaxi.com/"], "D25bac67": ["ペットサポート てんりん", "https://ten-rin.jp/"], "Dfc6c94f": ["木谷わんわんタクシー", "https://kitani11taxi.com/"], "D7d574bf": ["ARC（アルク）Pet Taxi & Pet Sitter", "https://pet-arc.com/"], "D436a86d": ["COCOタク 南大阪店", "https://coco-taxi-minami-osaka.com/"], "D7d5e5d1": ["COCOタク 大阪・東住吉店", "https://pet-cocotaku-higashi-sumiyoshi.com/"], "D9895b9b": ["COCOタク 大阪柏原店", "https://cocotaxi-kashiwara.com/"], "D3413153": ["COCOタク 守口店", "https://coco-taxi-osaka-moriguchi.com/"], "D713b363": ["COCOタク 新大阪店", "https://pet-taxi-coco-taku-shin-osaka.com/"], "D91cc62f": ["COCOタク 東大阪店", "https://cocotaku-higashiosaka.com/"], "Db8bafea": ["Comasuke（コマスケ）", "https://comasuke.com/"], "D6125f28": ["DOG HAIR STUDIO KEN（ペットタクシー）", "https://doghairstudioken.jp/"], "D01478c8": ["アイアールサービス（ペットタクシー）", "https://www.i-and-r.com/pettaxi.html"], "Da9518d0": ["キャリーワン", "https://carry-one.net/"], "D66c4625": ["ペットタクシー アイボウ（相棒）", "https://www.aibou.com/"], "D874b316": ["ペットタクシー マイファミリー", "https://my-family-takatsuki.com/"], "D1c2a5e3": ["ミントペットタクシー", "https://www.vet-system.jp/"], "D09687f4": ["COCOタク 神戸西店", "https://cocotaxi-kobewest.com/"], "D9f338ec": ["ペットタクシー アニマルプラス", "https://animal-plus.p-kit.com/"], "D72024d3": ["ラッキーペットサービス", "https://lucky-pettaxi.jimdosite.com/"], "D154d458": ["COCOタク ならまち店", "https://pet-taxi-nara.com/"], "D0a999a3": ["ペットタクシー COCOタク奈良", "https://pet-coco-taxi-nara.com/"], "D225080e": ["ペッタク（PETTAXI）", "https://pettaku.com/"], "D678e01f": ["ペットタクシー 響", "https://pettaxihibiki.hp.peraichi.com/"], "D7c41c5f": ["トップスター（ペットタクシー）", "https://www.topstar-tokushima.com/pettaxi"], "Db726555": ["COCOタク 北九州小倉店", "https://pet-taxi-kitakyusyu-kokuraten.com/"], "D0ec95b6": ["COCOタク 福岡東店", "https://cocotakufukuokahigashi.com/"], "Df71b3ed": ["COCOタク 福岡空港店", "https://pet-taxi-fukuoka-airport.com/"], "Dfad4b87": ["COCOタク 福岡筑紫野店", "https://coco-taxi-fukuoka-chikushino.com/"], "Df31960d": ["ペットタクシー Happy", "https://www.pet-taxi-happy.jp/"], "Db28bc5b": ["福岡わんわんエクスプレス", "https://wanwan.pet/"], "D7847612": ["福岡ペットタクシー HAKAタク", "https://pettaxi-hakataku.wepage.com/"], "Db9067d3": ["COCOタク 長崎店", "https://pet-taxi-nagasaki.com/"], "P002": ["ペットエクスプレス", "https://pettaxi.tokyo/"], "P003": ["くりき", "https://pet-kuriki.com/"]};/*/CO_SITE*/
  window.CO_SITE_ = CO_SITE; // 計測（coInfo）からも社名を引けるように
  // 公式サイトへのリンクに、当サイトから来たことの印を付ける（アクセス解析を入れている会社に見える）
  function siteUrl(u){
    try { var x = new URL(u); x.searchParams.set("utm_source", "pet.shiokonbu.com"); x.searchParams.set("utm_medium", "referral"); x.searchParams.set("utm_campaign", "pet_taxi_cards"); return x.toString(); } catch (e) { return u; }
  }
  // 入力した条件から、公式サイトに貼れる問い合わせ文を作る（お名前・連絡先は入れない）
  function askText(){
    var fd = new FormData(form), g = function(k){ return String(fd.get(k) || "").trim(); };
    var when = function(d, h, m){ if (!d) return ""; var a = d.split("-"); return Number(a[0]) + "年" + Number(a[1]) + "月" + Number(a[2]) + "日 " + Number(h) + ":" + m; };
    var lines = ["ペットタクシーの空き状況と料金を教えてください。", ""];
    lines.push("・お迎えの日時：" + when(g("date"), g("hour"), g("minute")));
    lines.push("・お迎えの場所：" + g("pickup"));
    if (form.querySelector("input[name=via_on]:checked") && form.querySelector("input[name=via_on]:checked").value === "あり" && g("via")) lines.push("・経由地：" + g("via"));
    lines.push("・行き先：" + g("dropoff"));
    if (g("trip") === "往復") lines.push("・往復（帰りのお迎え：" + when(g("ret_date"), g("ret_hour"), g("ret_minute")) + (($("retOther") || {}).checked && $("retPickup").value.trim() ? "、" + $("retPickup").value.trim() + " → " + $("retDropoff").value.trim() : "") + "）");
    else lines.push("・片道");
    readPets().forEach(function(pt, i){ lines.push("・" + petLine(pt, i)); });
    if (g("riders")) lines.push("・一緒に乗る人数：" + g("riders"));
    if (/^0/.test(g("riders"))) { if (g("hand_from")) lines.push("・お迎えで渡す人：" + g("hand_from")); if (g("hand_to")) lines.push("・行き先で受け取る人：" + g("hand_to")); }
    if (g("luggage")) lines.push("・荷物：" + g("luggage"));
    lines.push("", "（ペットタクシー予約窓口 pet.shiokonbu.com で見て、問い合わせました）");
    return lines.join("\n");
  }
  function copyAsk(btn, card){
    var t = askText(), done = function(ok){
      btn.textContent = ok ? "コピーしました。公式サイトのお問い合わせ欄に貼ってください" : "コピーできませんでした";
      setTimeout(function(){ btn.textContent = "問い合わせ文をコピー"; }, 4000);
    };
    var ci = coInfo(card); ci.cat = "taxi"; track("copy_inquiry", ci);
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function(){ done(true); }, function(){ done(fallback()); });
    else done(fallback());
    function fallback(){ try { var ta = document.createElement("textarea"); ta.value = t; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select(); var ok = document.execCommand("copy"); ta.remove(); return ok; } catch (e) { return false; } }
  }
  function letterAnon(lists){
    var tags = {}, n = 0; // 同じ会社は、往復の行き・帰りの一覧でも同じ目印
    lists.forEach(function(list){ (list || []).forEach(function(c){
      if (!c.anon || c.anonTag || c.site) return;
      var co = CO_SITE[c.id];
      if (co) { c.label = co[0]; c.site = co[1]; return; }
      if (!tags[c.id]) { var i = n++; tags[c.id] = i < 26 ? String.fromCharCode(65 + i) : String(i + 1); }
      c.anonTag = tags[c.id]; c.label = "会社" + c.anonTag + "（" + String(c.label).replace(/の会社$/, "") + "）";
    }); });
  }
  function paintPartners(cards){
    letterAnon([cards, quoteLegs && quoteLegs.go, quoteLegs && quoteLegs.back]);
    quotesLoaded = true; quoteCards = cards; $("partnerCards").replaceChildren();
    $("partnerResults").hidden = false;
    var ready = cards.filter(function(c){ return !c.display_only; }).length, later = cards.length - ready;
    // できることを先に書く（2026-11-11 飼い主目線のレビュー N2）。コピーの説明はカードごとではなくここで1回（N3）
    var copyable = cards.some(function(c){ return c.display_only && c.site; });
    var copyNote = copyable ? (ready ? "印のない会社は" : "") + "「問い合わせ文をコピー」を押すと、入力した条件をそのまま公式サイトのお問い合わせ欄に貼れます。" : "";
    if (cards.length) $("partnerStatus").textContent = !ready ? cards.length + "社が見つかりました。各社の料金の目安と公式サイトをご覧いただけます（このサイトから問い合わせできる会社は、まだありません）。" + copyNote
      : (later ? "このサイトから問い合わせできる会社：" + ready + "社（社名の横にオレンジのチェック）。ほかの" + later + "社は、料金の目安と公式サイトをご覧いただけます。" : cards.length + "社が候補です。") + (ready >= 2 ? "会社を選ぶか、下の「全社に問い合わせる」でまとめて送れます。" : "問い合わせたい会社を選んでください。") + copyNote;
    else $("partnerStatus").innerHTML = '<span class="partner-empty"><b>条件に合う事業者が見つかりませんでした</b>お迎えの日時・場所、一緒に乗る人数、ペットの条件（大きさ・ケージなど）を変えると、見つかることがあります。問い合わせは送信されていません。</span>';
    $("partnerSortBox").hidden = cards.length < 2;
    var hasDist = cards.some(function(c){ return !!c.shop; }); // 予約のしくみが古い版のあいだはお店の位置が来ないので、距離のしぼり込みを出さない
    $("partnerDist").parentNode.hidden = !hasDist; if (!hasDist) $("partnerDist").value = "";
    chosenPicks = chosenPicks.filter(function(c){ return cards.some(function(x){ return x.id === c.id && !x.display_only; }); }).map(function(c){ return cards.filter(function(x){ return x.id === c.id; })[0]; });
    chosenQuote = chosenPicks[0] || null; showPickButton();
    drawCards();
    paintLegs();
    syncContact();
    loadScores();
    loadRoads();
    // 自動更新では入力中のフォーカスやスクロール位置を動かさない。
  }
  // 並べ替え（Nori 2026-10-31「価格の安い・高い順、口コミが高い・低い順」、2026-11-01「お店からお迎えまでの距離が短い順で表示」＝デフォルト）
  // 料金が出ない会社・口コミの点数がない会社は、どの並び順でも後ろ。同じなら元の順
  var scoresReady = false, scoreMemo = {}; // 口コミの星：このページを開いているあいだだけ覚える（保存はしない）
  if (REVIEW_ON_CLICK) $("partnerSort").querySelectorAll('option[value^="review"]').forEach(function(o){ o.remove(); }); // 星をまとめて取り寄せないので、口コミの並び順は出さない
  function withScore(c){ return Object.prototype.hasOwnProperty.call(scoreMemo, c.id) ? Object.assign({}, c, {review: scoreMemo[c.id]}) : c; }
  // お店からの距離でしぼる（Nori 2026-11-01「フィルターにも事業所との距離」）。お店の場所が分からない会社も外す。選んだ会社は外さない
  function distOk(c, leg){
    var max = Number($("partnerDist").value || 0);
    if (!max || chosenPicks.some(function(x){ return x.id === c.id; })) return true;
    var km = roadOf(c, leg);
    if (km === undefined) return true; // 道のりを調べている途中の会社はまだ外さない
    return km != null && km <= max; // お店の場所が分からない・道のりが取れない会社は外す
  }
  function sortCards(list, leg){
    var mode = $("partnerSort").value || "dist_asc";
    var key = function(c){ return mode.indexOf("price") === 0 ? (c.price && c.price.amount != null ? c.price.amount : null) : mode.indexOf("dist") === 0 ? (roadOf(c, leg) != null ? roadOf(c, leg) : null) : (c.review && c.review.rating > 0 ? c.review.rating : null); };
    list = list.filter(function(c){ return distOk(c, leg); });
    var down = /_desc$/.test(mode);
    return list.map(withScore).map(function(c, i){ return {c: c, i: i, k: key(c)}; }).sort(function(a, b){
      if ((a.c.display_only ? 1 : 0) !== (b.c.display_only ? 1 : 0)) return a.c.display_only ? 1 : -1; // 予約を依頼できる会社を先に
      if ((a.k == null) !== (b.k == null)) return a.k == null ? 1 : -1;
      if (a.k != null && a.k !== b.k) return down ? b.k - a.k : a.k - b.k;
      if (mode.indexOf("review") === 0 && a.k != null) { var n = (b.c.review.count || 0) - (a.c.review.count || 0); if (n) return down ? n : -n; }
      return a.i - b.i;
    }).map(function(x){ return x.c; });
  }
  // 最初は上の3社だけ。残りはボタンを押すと開く（Nori 2026-10-31「表示はトップ3社。あとは折りたたみ」）
  var TOP_CARDS = 3, restOpen = false;
  function drawCards(){
    // 口コミの点数が出ている会社がないときは、口コミの並び順を出さない（見えない点数で並べ替えないため。2026-11-09 矛盾の点検）
    var hasScore = quoteCards.some(function(c){ var v = withScore(c).review; return v && v.rating > 0; });
    $("partnerSort").querySelectorAll('option[value^="review"]').forEach(function(o){ o.hidden = o.disabled = !hasScore; });
    if (!hasScore && /^review/.test($("partnerSort").value)) $("partnerSort").value = "dist_asc";
    $("partnerCards").replaceChildren(); $("partnerRest").replaceChildren();
    var list = sortCards(quoteCards, ""), rest = list.length - TOP_CARDS, cut = quoteCards.length - list.length;
    $("partnerDistNote").hidden = !cut;
    $("partnerDistNote").textContent = !cut ? "" : "候補" + quoteCards.length + "社のうち、お店からの車の道のりが" + $("partnerDist").value + "km以内は" + list.length + "社です" + (list.length ? "（お店の場所が分からない会社も外しています）。" : "。距離を広げてください。");
    list.forEach(function(card, i){ $(i < TOP_CARDS ? "partnerCards" : "partnerRest").appendChild(buildCard(card, "")); });
    $("partnerRestBtn").hidden = rest <= 0;
    $("partnerRest").hidden = rest <= 0 || !restOpen;
    $("partnerRestBtn").setAttribute("aria-expanded", restOpen ? "true" : "false");
    $("partnerRestBtn").textContent = restOpen ? "ほかの会社をたたむ ▴" : "ほかの" + rest + "社も見る ▾";
    showAllButton();
  }
  $("partnerRestBtn").addEventListener("click", function(){
    restOpen = !restOpen; if (restOpen) track("open_more_partners");
    drawCards();
  });
  $("partnerSort").addEventListener("change", function(){
    track("sort_partners", {mode: $("partnerSort").value});
    drawCards();
    if (!chosenGo && !chosenBack) paintLegs();
  });
  $("partnerDist").addEventListener("change", function(){
    track("filter_partners_distance", {km: $("partnerDist").value || "all"});
    drawCards();
    if (!chosenGo && !chosenBack) paintLegs();
  });
  // お店→お迎えの場所の車の道のり（Nori 2026-11-01「直線で出すのやめて。クルマでの最短ルートでだして」）
  // 道路データにまとめて1回で聞く（お迎えの場所ごと、最大90社ずつ）。このページを開いているあいだだけ覚える。取れなければ null
  var roadMemo = {}, roadBusy = {};
  function roadKey(shop, at){ return shop[0].toFixed(4) + "," + shop[1].toFixed(4) + ">" + at.lat.toFixed(5) + "," + at.lng.toFixed(5); }
  function pickupAt(leg){ var d = routeDetails || {}; return leg === "back" ? d.backFrom : d.from; }
  function roadOf(card, leg){ // 数値＝km／null＝分からない／undefined＝調べている途中
    var at = pickupAt(leg);
    if (!card.shop || !at) return null;
    var k = roadKey(card.shop, at);
    return Object.prototype.hasOwnProperty.call(roadMemo, k) ? roadMemo[k] : roadBusy[k] ? undefined : null;
  }
  function loadRoads(){
    var points = {};
    [[quoteCards, ""], [quoteLegs && quoteLegs.go || [], "go"], [quoteLegs && quoteLegs.back || [], "back"]].forEach(function(g){
      var at = pickupAt(g[1]);
      if (!at) return;
      g[0].forEach(function(c){
        if (!c.shop) return;
        var k = roadKey(c.shop, at);
        if (Object.prototype.hasOwnProperty.call(roadMemo, k) || roadBusy[k]) return;
        var pk = at.lat.toFixed(5) + "," + at.lng.toFixed(5);
        (points[pk] = points[pk] || {at: at, shops: {}}).shops[k] = c.shop;
      });
    });
    Object.keys(points).forEach(function(pk){
      var g = points[pk], keys = Object.keys(g.shops); // お迎えの場所は約100mの細かさに丸めて送る（お客さまの位置を細かく出さない）
      for (var i = 0; i < keys.length; i += 90) (function(part){
        part.forEach(function(k){ roadBusy[k] = 1; });
        var cs = [{lat: Math.round(g.at.lat * 1000) / 1000, lng: Math.round(g.at.lng * 1000) / 1000}].concat(part.map(function(k){ return {lat: g.shops[k][0], lng: g.shops[k][1]}; }));
        var src = part.map(function(k, j){ return j + 1; }).join(";");
        fetch(ROAD_API + "/table/v1/driving/" + cs.map(function(c){ return c.lng.toFixed(5) + "," + c.lat.toFixed(5); }).join(";") + "?sources=" + src + "&destinations=0&annotations=distance")
          .then(function(r){ return r.json(); })
          .then(function(j){ var ok = j && j.code === "Ok" && j.distances; part.forEach(function(k, n){ var m = ok && j.distances[n] && j.distances[n][0]; roadMemo[k] = m != null && isFinite(m) ? Math.round(m / 100) / 10 : null; }); })
          .catch(function(){ part.forEach(function(k){ roadMemo[k] = null; }); })
          .then(function(){ part.forEach(function(k){ delete roadBusy[k]; }); redrawSoft(); });
      })(keys.slice(i, i + 90));
    });
    if (Object.keys(points).length) redrawSoft();
  }
  // 口コミや詳しい情報を開いている途中なら、並べ直さない（次に並び順を変えたときに反映）
  function redrawSoft(){
    if (sending) return;
    var open = $("partnerResults").querySelector("#partnerCards .review-panel:not([hidden]),#partnerCards details[open],#partnerRest .review-panel:not([hidden]),#partnerRest details[open]");
    if (!open) drawCards();
    if (!chosenGo && !chosenBack && !$("legSplit").querySelector(".review-panel:not([hidden]),details[open]")) paintLegs();
  }
  // 口コミの星は、カードを出したあとにまとめて取り寄せる（まだ取り寄せていない会社だけ）
  function loadScores(){
    var all = quoteCards.concat(quoteLegs && quoteLegs.go || [], quoteLegs && quoteLegs.back || []);
    if (!scoresReady || REVIEW_ON_CLICK) return; // 押したときだけ取り寄せる形のときは、まとめては取り寄せない
    var ids = all.map(function(c){ return c.id; }).filter(function(id, i, a){ return id && a.indexOf(id) === i && !Object.prototype.hasOwnProperty.call(scoreMemo, id); });
    if (!ids.length) return;
    var seq = quoteSeq, body = new URLSearchParams(); body.set("kind", "scores"); body.set("ids", ids.join(",")); if (DEMO.tok) body.set("demo", DEMO.tok);
    fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){
      if (!j || !j.ok) return;
      ids.forEach(function(id){ scoreMemo[id] = (j.scores || {})[id] || null; });
      if (seq !== quoteSeq || sending) return;
      var open = $("partnerResults").querySelector("#partnerCards .review-panel:not([hidden]),#partnerCards details[open],#partnerRest .review-panel:not([hidden]),#partnerRest details[open]");
      if (!open) drawCards(); // 口コミや詳しい情報を開いている途中なら、並べ直さない（次に並び順を変えたときに反映）
      if (!chosenGo && !chosenBack && !$("legSplit").querySelector(".review-panel:not([hidden]),details[open]")) paintLegs();
    }).catch(function(){});
  }
  // 事業者のカード1枚。leg は ""（ふつう）／"go"（往復の行きだけ）／"back"（帰りだけ）
  function buildCard(card, leg){
      var article = document.createElement("article"); article.className = "partner-card";
      function text(tag, value, cls){ var el = document.createElement(tag); el.textContent = value; if (cls) el.className = cls; article.appendChild(el); return el; }
      var h4 = text("h4", card.label);
      // 問い合わせできる（提携している）会社には、名前の横にアイコンだけ付ける（Nori 2026-11-08「アイコンをつけて目立つように。文字はいらない」）
      if (!card.display_only) { article.classList.add("partner-open"); var ic = document.createElement("span"); ic.className = "open-icon"; ic.setAttribute("role", "img"); ic.setAttribute("aria-label", "このサイトから問い合わせできる会社"); ic.title = "このサイトから問い合わせできる会社"; ic.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="currentColor"/><path d="M6.5 12.5l3.6 3.6 7.4-7.6" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'; h4.prepend(ic); }
      if (card.demo) { var bd = document.createElement("span"); bd.className = "demo-badge"; bd.textContent = "提携（見本）"; h4.appendChild(bd); }
      // お店からお迎えの場所までの車の道のり（道路データで調べる。直線距離は出さない。Nori 2026-11-01）
      if ("shop" in card) { var road = roadOf(card, leg);
        text("p", !card.shop ? "お店の場所は確認中です" : road === undefined ? "お店からの道のりを調べています…" : road == null ? "お店からの道のりは調べられませんでした" : "お店からお迎えの場所まで 車で" + road.toFixed(1) + "km", "partner-dist"); }
      var rv = card.review;
      if (rv && rv.rating > 0) {
        // 口コミの点数は規約上、出どころ（Google マップ）の表示が必要
        var score = document.createElement("p"); score.className = "partner-score";
        var stars = document.createElement("span"); stars.className = "stars"; stars.setAttribute("aria-hidden", "true");
        stars.style.setProperty("--fill", Math.max(0, Math.min(5, rv.rating)) / 5 * 100 + "%");
        var num = document.createElement("b"); num.textContent = Number(rv.rating).toFixed(1);
        score.setAttribute("aria-label", "口コミの評価 5点中" + Number(rv.rating).toFixed(1) + "点、" + rv.count + "件");
        // 口コミの件数を押すと、このページの中で口コミを読める（出どころの表示「Google Maps」は規約で必要。訳さずそのまま出す）
        var open = document.createElement("button"); open.type = "button"; open.className = "partner-review-open";
        open.textContent = "口コミ" + rv.count + "件を見る";
        var src = document.createElement("span"); src.className = "partner-review-src"; src.textContent = "Google Maps";
        score.append(stars, num, open, src);
        article.appendChild(score);
        var panel = document.createElement("div"); panel.className = "review-panel"; panel.hidden = true; article.appendChild(panel);
        open.addEventListener("click", function(){ toggleReviews(card.id, panel, open); });
      } else if (REVIEW_ON_CLICK && card.id && !card.anon && !Object.prototype.hasOwnProperty.call(scoreMemo, card.id)) {
        article.appendChild(lazyReviews(card.id, function(v){ scoreMemo[card.id] = v; })); // 社名を伏せた会社は口コミを返さないので出さない
      } // 点数が取れないときは何も出さない（外部の口コミページへは飛ばさない。Nori 2026-10-31）
      // アピールポイント（公式サイトに書いてあることだけ。Nori 2026-10-31）
      // 条件のタグ（同乗の人数・頭数・お支払いの決まり。灰色。Nori 2026-11-01）
      if ((card.points && card.points.length) || (card.limits && card.limits.length)) {
        var pts = document.createElement("ul"); pts.className = "partner-points"; pts.setAttribute("aria-label", "公式サイトに書いてある特長と条件");
        (card.points || []).forEach(function(x){ var li = document.createElement("li"); li.textContent = x; pts.appendChild(li); });
        (card.limits || []).forEach(function(x){ var li = document.createElement("li"); li.className = "lim"; li.textContent = x; pts.appendChild(li); });
        article.appendChild(pts);
      }
      // 料金（概算見積もり）。口コミと料金のほかの詳しい情報は、最初はたたんでおく（Nori 2026-10-31）
      var price = text("p", roundYenText(card.price.text), "partner-price");
      var tripName = leg ? "片道" : (form.querySelector("input[name=trip]:checked") || {}).value || "片道";
      var cap = document.createElement("small"); cap.textContent = card.price.amount == null ? (routeDetails && Math.max(routeDetails.km || 0, routeDetails.highKm || 0) > 250 ? "長距離のため、お見積もり" : "料金表が未登録のため、お見積もり") : "一般道・" + tripName + "の概算見積もり" + (card.price.taxUnknown ? (card.price.incompleteFees ? "（税の扱いは確認中・未確認の費用は別途）" : "（税の扱いは確認中）") : card.price.incompleteFees ? "（税込・未確認の費用は別途）" : "（税込）"); price.appendChild(cap);
      if (card.price.local && card.price.local.nightExtra) text("p", "夜間・早朝の割増 " + yen(card.price.local.nightExtra) + "を含む", "partner-surcharge");
      // 概算の注意は料金のすぐ下に太字の1行（上のまとめの注意と合わせて「目立つ形」。2026-11-08 レビュー #2 でカードを短く）
      var caution = text("p", card.price.amount == null ? "確定料金は会社からお知らせします" : "概算です。確定料金ではありません", "partner-caution");
      // 往復の待ち時間は当日の実際の時間で精算（Nori 2026-11-09「最終的な支払いは変動する可能性があるというのをユーザーにも」）
      // 当日の道路事情でも変わる（Nori 2026-11-09「実際に当日の道路事情などで料金は変わる可能性もある」）
      // 当てはまらない会社には出さない（Nori 2026-11-09「当てはまらない会社は対象外」）：渋滞でも追加料金なしの会社は道路事情、待機料金なしの会社は待ち時間
      var jam = NO_FEE.nojam.indexOf(card.id) < 0 && !(card.points || []).some(function(x){ return /渋滞でも追加料金なし/.test(x); });
      var wait = tripName === "往復" && NO_FEE.nowait.indexOf(card.id) < 0;
      // カードでは概算の注意と同じ行に短く（くわしくはフォームの往復の欄・フォームの下・FAQ。2026-11-11 レビュー N3）
      if (jam || wait) { var wsp = document.createElement("span"); wsp.className = "partner-wait"; wsp.textContent = "。" + (wait && jam ? "当日の待ち時間・道路事情で変わることがあります" : wait ? "待ち時間は当日の実際の時間で精算します" : "当日の道路事情で変わることがあります"); caution.appendChild(wsp); }
      // 車・お支払いは、たたまずに出す（Nori 2026-11-08「支払い方法とかできるものは全部出しておいたほうが」）
      // 分からない項目（「まだ確認中です」）は行ごと出さない。お客さまが選んだ動物を乗せられるかの「確認中」だけは残す（2026-11-08 レビュー #3）
      var carText = String(card.car || "").replace(/(^|。)[^。]*(車の詳細|対応エリア)は?[^。]*確認中です[。）)]?/g, "$1").replace(/（対応エリアは確認中です）/g, "").replace(/^。+/, "").trim();
      if (carText) text("p", carText, "partner-info");
      if (card.payment && !/確認中/.test(card.payment)) text("p", /^お支払い/.test(card.payment) ? card.payment : "お支払い：" + card.payment, "partner-info");
      var more = document.createElement("details"); more.className = "partner-more";
      var ms = document.createElement("summary"); ms.textContent = "料金の内訳を見る"; more.appendChild(ms);
      article.appendChild(more);
      function add(tag, value, cls){ var el = document.createElement(tag); el.textContent = value; if (cls) el.className = cls; more.appendChild(el); return el; }
      // 「引き受けるときに会社が確かめること」（card.check）は、会社あての問い合わせメールにだけ出す。お客さまのカードには出さない（Nori 2026-11-08「ユーザに見せるべき？」）
      // 内訳は小さな文字の1行にして、押すと開く
      function breakdown(title, value, cls){
        var box = document.createElement("details"); box.className = "price-details" + (cls ? " " + cls : "");
        var summary = document.createElement("summary"); summary.textContent = title; box.appendChild(summary);
        var list = document.createElement("dl");
        [["乗車運賃",value.ride],["迎車代",value.pickup,value.pickupUnknown],["回送代",value.returnFee,value.returnUnknown],["夜間・早朝の割増",value.nightExtra],["待機料金",value.wait],["概算の端数調整",value.rounding]].forEach(function(row){
          var dt = document.createElement("dt"), dd = document.createElement("dd"); dt.textContent=row[0]; dd.textContent=row[2]?(row[1]?yen(row[1])+"〜（追加分は要確認）":"要確認（合計に未算入）"):yen(row[1]); list.appendChild(dt); list.appendChild(dd);
        });
        box.appendChild(list); more.appendChild(box);
      }
      if (card.price.fixed) { if (card.price.planNote) add("p",roundYenText(card.price.planNote),"partner-note"); }
      else if (card.price.local) {
        var lp = card.price.local, fy = function(v, unknown){ return v ? yen(v) + (unknown ? "〜" : "") : unknown ? "要確認" : "0円"; };
        breakdown("迎車 " + fy(lp.pickup, lp.pickupUnknown) + "・回送 " + fy(lp.returnFee, lp.returnUnknown) + (lp.pickupUnknown || lp.returnUnknown ? "（追加分は要確認）" : "を含む"), lp);
        if (card.price.highway) breakdown("高速利用時 " + yen(card.price.highway.amount) + (card.price.highway.pickupUnknown || card.price.highway.returnUnknown ? "〜" : "") + " ＋ 通行料の実費", card.price.highway, "hw");
        else add("p", "高速利用時：経路・通行料を含めてお見積もり", "partner-note");
        if (card.price.pickupNote) add("p",roundYenText(card.price.pickupNote),"partner-note");
        if (card.price.routeNote) add("p",roundYenText(card.price.routeNote),"partner-note");
        if (card.price.planNote) add("p",roundYenText(card.price.planNote),"partner-note");
      }
      if (card.price.night && !(card.price.local && card.price.local.nightExtra)) add("p",roundYenText(card.price.night),"partner-note");
      add("p", (card.price.amount == null ? "" : card.price.fixed ? "公式サイトの定額をもとにした概算です。" : "公式サイトの料金表をもとにした概算です。") + (card.price.fixed && card.price.tollIncluded ? "" : card.price.fixed ? "駐車場代は別途実費です。" : "通行料・駐車場代は別途実費です。"), "partner-note");
      // 表示だけの会社（準備中）。予約の依頼はできない（サーバーでも断る）
      if (card.display_only) {
        article.classList.add("partner-later");
        if (card.site) { // 公式サイトへ（別のタブ）。空き状況と料金は会社に直接おたずねいただく
          var sp = document.createElement("p"); sp.className = "partner-site";
          // 入力した内容をむだにしないよう、そのまま貼れる問い合わせ文をコピーできる。文の最後に当サイトから来たことを書く（送客が会社に伝わる。Nori 2026-11-08）
          var cp = document.createElement("button"); cp.type = "button"; cp.className = "copy-ask"; cp.textContent = "問い合わせ文をコピー";
          cp.addEventListener("click", function(){ copyAsk(cp, card); });
          var sa = document.createElement("a"); sa.href = siteUrl(card.site); sa.target = "_blank"; sa.rel = "noopener"; sa.textContent = "公式サイトを見る ↗";
          sa.addEventListener("click", function(){ var o = coInfo(card); o.cat = "taxi"; o.from = "card"; try { o.host = new URL(sa.href).hostname; } catch (e) {} track("official_site", o); }); // 会社ごとの遷移数（Nori 2026-11-10）
          sp.append(cp, sa); article.appendChild(sp);
        }
        if (!card.site) text("p", "このサイトからは、まだ問い合わせできません", "partner-later-note"); // コピーの説明は一覧の上で1回（2026-11-11 レビュー N3） // 大きな灰色のボタンはやめて1行に（2026-11-08 レビュー #2）
        return article;
      }
      var btn = document.createElement("button"); btn.type = "button"; btn.className = "btn";
      var legName = leg === "go" ? "行き" : leg === "back" ? "帰り" : "";
      // 複数社を選べる（Nori 2026-10-31）。押すたびに選ぶ・外す。送るのは下の「選んだ◯社に…」ボタン
      var on = !leg && chosenPicks.some(function(c){ return c.id === card.id; });
      if (on) { article.classList.add("picked"); btn.classList.add("pick-on"); }
      btn.textContent = legName ? legName + "をこの事業者にする" : on ? "✓ 問い合わせ先に入れました（押すと外す）" : "この会社に問い合わせる"; btn.setAttribute("aria-label", legName ? legName + "を" + card.label + "にする" : card.label + (on ? "を問い合わせ先から外す" : "を問い合わせ先に入れる"));
      if (!leg) btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.addEventListener("click", function(){ if (sending) return; if (leg) return pickLeg(leg, card, article); togglePick(card); });
      article.addEventListener("click", function(event){ if (!event.target.closest("button,a,details,.review-panel")) btn.click(); });
      article.appendChild(btn); return article;
  }
  // 見本の画面：上にお知らせを出し、その会社の都道府県を選んだ状態にする
  if (DEMO.tok && GAS_URL) {
    var demoBody = new URLSearchParams(); demoBody.set("kind", "demo"); demoBody.set("demo", DEMO.tok);
    fetch(GAS_URL, {method: "POST", body: demoBody}).then(function(r){ return r.json(); }).then(function(j){
      if (!j || !j.ok) return;
      DEMO.ok = true; DEMO.name = j.name || ""; syncOpenNote();
      var box = document.createElement("div"); box.className = "demo-banner"; box.setAttribute("role", "note");
      var b = document.createElement("b"); b.textContent = DEMO.name + "さま向けの見本の画面です";
      box.append(b, document.createTextNode("ご提携いただいたときの見え方をお試しいただけます。" + (j.pref ? j.pref + "の" : "貴社の対応エリアの") + "お迎えの場所と日時を入れると、貴社が社名と口コミつきで、問い合わせできる会社として一番上に出ます（日時が貴社の営業時間の外だと出ません）。ほかの会社は、提携していないため口コミを出さず、当サイトから問い合わせも送れません。この画面から問い合わせを送っても、どこにも届きません。"));
      var f = $("petForm"); f.parentNode.insertBefore(box, f);
      if (j.pref && $("pref") && [].some.call($("pref").options, function(o){ return o.value === j.pref; }) && !$("pref").value) { setSelect($("pref"), j.pref); }
      if (typeof queuePartners === "function") queuePartners();
    }).catch(function(){});
  }
  function demoSent(){
    var box = $("demoDone");
    if (!box) { box = document.createElement("div"); box.id = "demoDone"; box.className = "demo-done"; box.setAttribute("role", "status"); $("sendSelected").parentNode.insertBefore(box, $("sendSelected")); }
    box.replaceChildren();
    var b = document.createElement("b"); b.textContent = "見本の画面なので、問い合わせは送っていません";
    var a = document.createElement("a"); a.href = "/partner/#screens"; a.textContent = "届くメールとお返事の画面の見本を見る";
    box.append(b, document.createTextNode("ご提携後は、ここで選ばれた会社さまに「空き状況と料金のお問い合わせ」のメールが届きます（飼い主さんのお名前と連絡先は、予約が確定するまで伏せます）。確定料金を入れてお返事いただき、飼い主さんが「この内容で予約する」を押すと予約が確定します。"), document.createElement("br"), a);
    box.scrollIntoView({block: "center", behavior: "smooth"});
  }
  function togglePick(card){
    chosenGo = null; chosenBack = null;
    var i = chosenPicks.map(function(c){ return c.id; }).indexOf(card.id);
    if (i >= 0) chosenPicks.splice(i, 1);
    else { chosenPicks.push(card); track("pick_company", coInfo(card)); }
    $("err").textContent = "";
    chosenQuote = chosenPicks[0] || null;
    drawCards(); showPickButton();
  }
  // 問い合わせる会社の数に上限はない（Nori 2026-11-01「最大5社の上限はなくていい」）
  function showPickButton(){
    var b = $("sendSelected"), n = chosenPicks.length;
    b.hidden = !n;
    if (n) b.textContent = (n === 1 ? chosenPicks[0].label + "に" : "選んだ" + n + "社に") + "空き状況と料金を問い合わせる（無料）";
    showAllButton();
  }
  // 「全社に問い合わせる」（Nori 2026-11-01「選択してSubmitと、すべてSubmitとできるように」）
  // 送り先は、いま表示している候補のうち問い合わせできる会社（準備中の会社と、距離でしぼって外した会社は入れない）
  function allTargets(){ return sortCards(quoteCards, "").filter(function(c){ return !c.display_only; }); }
  function showAllButton(){
    var b = $("sendAll"), n = allTargets().length;
    b.hidden = n < 2 || sending;
    if (n >= 2) b.textContent = "条件に合う全" + n + "社に問い合わせる（無料）";
  }
  // 会社を選んだら、次にすること（ご連絡先を入れて送る）を画面の下に出す（2026-11-08 CVR）。送るボタンが見えたら隠す
  (function(){
    var bar = $("pickBar"), send = $("sendSelected"), sendSeen = false, formSeen = true;
    function sync(){
      var on = !send.hidden && !send.disabled && !sendSeen && formSeen && !sending && form.style.display !== "none";
      bar.hidden = !on;
      if (on) $("pickBarGo").textContent = contactMiss() ? "次へ：ご連絡先 ↓" : "問い合わせへ ↓";
      if (on) $("pickBarTxt").textContent = !chosenPicks.length && chosenGo && chosenBack ? "行きと帰りの会社を選んでいます" : chosenPicks.length > 1 ? chosenPicks.length + "社を選んでいます" : chosenPicks.length ? "選択中：" + chosenPicks[0].label : "会社を選んでいます";
    }
    new MutationObserver(sync).observe(send, {attributes: true, attributeFilter: ["hidden", "disabled"], childList: true, characterData: true, subtree: true});
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function(es){ sendSeen = es[0].isIntersecting; sync(); }).observe(send);
      new IntersectionObserver(function(es){ formSeen = es[0].isIntersecting; sync(); }).observe(form);
    }
    function contactMiss(){ return ["name", "email", "tel", "agree"].map(function(id){ return $(id); }).filter(function(el){ return !el.checkValidity(); })[0]; }
    form.addEventListener("change", sync);
    $("pickBarGo").addEventListener("click", function(){
      var miss = contactMiss();
      track("pick_bar_next", {filled: miss ? 0 : 1});
      if (miss) jumpTo(miss); else send.scrollIntoView({block: "center", behavior: "smooth"});
    });
  })();
  $("sendAll").addEventListener("click", function(){
    if (sending) return;
    var all = allTargets();
    if (all.length < 2) return;
    var ok = window.confirm("条件に合う" + all.length + "社すべてに、空き状況と料金を問い合わせます。\n\n・お名前とご連絡先は、予約を確定するまで会社には伝わりません。\n・返事を見て、予約するかどうかを決められます（予約しなければ何もしなくて大丈夫です）。\n\n送ってよろしいですか？");
    track("send_all_confirm", {count: all.length, ok: ok ? 1 : 0});
    if (!ok) return;
    chosenGo = null; chosenBack = null;
    chosenPicks = all.slice(); chosenQuote = chosenPicks[0];
    drawCards(); showPickButton();
    form.requestSubmit();
  });
  // 往復のとき：行きと帰りをそれぞれ別の会社に頼むための片道の候補（Nori 2026-10-31）
  function paintLegs(){
    var on = !!(quoteLegs && quoteLegs.go && quoteLegs.back && quoteLegs.go.length && quoteLegs.back.length);
    $("legSplit").hidden = !on;
    $("legGo").replaceChildren(); $("legBack").replaceChildren();
    if (!on) return;
    sortCards(quoteLegs.go, "go").forEach(function(c){ $("legGo").appendChild(buildCard(c, "go")); });
    sortCards(quoteLegs.back, "back").forEach(function(c){ $("legBack").appendChild(buildCard(c, "back")); });
    chosenGo = null; chosenBack = null; showLegPick();
  }
  function showLegPick(){
    $("legPick").textContent = "行き：" + (chosenGo ? chosenGo.label : "まだ選んでいません") + "／帰り：" + (chosenBack ? chosenBack.label : "まだ選んでいません");
  }
  function pickLeg(leg, card, article){
    if (leg === "go") chosenGo = card; else chosenBack = card;
    var pi = coInfo(card); pi.leg = leg; track("pick_company", pi);
    chosenQuote = null; chosenPicks = []; drawCards();
    Array.prototype.forEach.call(article.parentNode.children, function(a){ a.classList.toggle("picked", a === article); });
    showLegPick();
    if (!(chosenGo && chosenBack)) { $("sendSelected").hidden = true; return; }
    $("sendSelected").hidden = false;
    $("sendSelected").textContent = "行き：" + chosenGo.label + "／帰り：" + chosenBack.label + "に空き状況と料金を問い合わせる（無料）";
    form.requestSubmit();
  }
  $("legToggle").addEventListener("click", function(){
    var open = $("legBox").hidden;
    $("legBox").hidden = !open; this.setAttribute("aria-expanded", String(open));
    if (!open) { chosenGo = null; chosenBack = null; showLegPick(); $("sendSelected").hidden = !chosenQuote; Array.prototype.forEach.call(document.querySelectorAll("#legBox .picked"), function(a){ a.classList.remove("picked"); }); }
  });

  var today = new Date(); today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
  $("date").min = today.toISOString().slice(0,10);

  // エリアページから来たとき（?pref=東京都）は、お迎えの都府県を選んでおく
  var qs = new URLSearchParams(location.search);
  function setSelect(el, v){
    if (v && Array.prototype.some.call(el.options, function(o){ return o.value === v; })) el.value = v;
  }
  setSelect($("pref"), qs.get("pref"));
  // [B] 病院の一覧などから来たとき（?to=病院の所在地）は、行き先に入れておく（2026-11-08「この病院までのペットタクシー」の導線）
  var qTo = (qs.get("to") || "").trim().slice(0, 80);
  if (qTo && !$("dropoff").value) $("dropoff").value = qTo;

  // 入力欄が見えている間は下部の固定ボタンを隠す
  var sticky = document.querySelector(".sticky");
  if ("IntersectionObserver" in window) {
    // ヒーローのボタンかフォームが見えている間は隠す
    var seen = {};
    var io = new IntersectionObserver(function(es){
      es.forEach(function(x){ seen[x.target.id || "hero"] = x.isIntersecting; });
      sticky.style.visibility = (seen.hero || seen.form) ? "hidden" : "visible";
    });
    io.observe(document.querySelector(".hero .btn")); io.observe($("form"));
  }

  // 経由地（ありを選んだときだけ入力欄を出す）
  function syncVia(){
    var on = form.querySelector("input[name=via_on]:checked").value === "あり";
    $("viaBox").hidden = !on;
    $("via").required = on;
    if (on && !$("via").value) $("via").focus();
  }
  form.querySelectorAll("input[name=via_on]").forEach(function(r){ r.addEventListener("change", syncVia); });

  // 往復のときの帰り（帰りの日時と場所。待つか迎えに来るかは会社が安いほうで決める）
  $("retHour").innerHTML = $("hour").innerHTML;
  $("retMinute").innerHTML = $("minute").innerHTML;

  // 過去の日時は選べないようにする（日本時間で、いまより前の時・分を選べなくする。帰りは行きのお迎えより前を選べなくする）
  var MIN_LEAD_H = 3; // 会社にメールで確認する都合で、お迎えはお申し込みから3時間後以降（各社の決まりではない）
  function jstNow(){ var d = new Date(Date.now() + (9 + MIN_LEAD_H) * 3600e3); return {date: d.toISOString().slice(0, 10), h: d.getUTCHours(), m: d.getUTCMinutes()}; }
  function limitTime(dateId, hourId, minId, base){
    var d = $(dateId), hs = $(hourId), ms = $(minId);
    d.min = base.date;
    var same = d.value === base.date, before = d.value && d.value < base.date;
    Array.prototype.forEach.call(hs.options, function(o){ if (o.value) o.disabled = before || (same && Number(o.value) < base.h); });
    var sameHour = same && Number(hs.value) === base.h;
    Array.prototype.forEach.call(ms.options, function(o){ if (o.value) o.disabled = before || (same && Number(hs.value) < base.h) || (sameHour && Number(o.value) <= base.m); });
    [hs, ms].forEach(function(el){ if (el.selectedOptions[0] && el.selectedOptions[0].disabled) el.value = ""; });
  }
  function limitTimes(){
    var now = jstNow();
    limitTime("date", "hour", "minute", now);
    var go = $("date").value && $("hour").value && $("minute").value ? {date: $("date").value, h: Number($("hour").value), m: Number($("minute").value)} : now;
    if ($("retDate").value && $("retDate").value < go.date) $("retDate").value = go.date;
    limitTime("retDate", "retHour", "retMinute", go);
  }
  ["date","hour","minute","retDate","retHour"].forEach(function(id){ $(id).addEventListener("change", limitTimes); });
  setInterval(limitTimes, 60000);
  limitTimes();
  function syncTrip(){
    var t = (form.querySelector("input[name=trip]:checked") || {}).value || "";
    var later = t === "往復";
    $("retBox").hidden = !later;
    ["retDate","retHour","retMinute"].forEach(function(id){ $(id).required = later; });
    if (later && !$("retDate").value) $("retDate").value = $("date").value;
    var other = later && $("retOther").checked;
    var to = $("dropoff").value.trim(), from = $("pickup").value.trim();
    // 変えるを押したときは、行きの逆向きを入れておいて、そこから直してもらう
    if (other && $("retPlaces").hidden) {
      if (!$("retPickup").value) $("retPickup").value = to;
      if (!$("retDropoff").value) $("retDropoff").value = from;
    }
    $("retPlaces").hidden = !other;
    $("retPickup").required = other; $("retDropoff").required = other;
    $("retRoute").hidden = other;
    $("retRoute").textContent = "帰りは、" + (to ? "「" + to + "」" : "行き先") + "でお迎えして、" + (from ? "「" + from + "」" : "お迎えの場所") + "までお送りします。";
    limitTimes();
  }
  form.querySelectorAll("input[name=trip]").forEach(function(r){ r.addEventListener("change", syncTrip); });
  ["retOther","pickup","dropoff","date"].forEach(function(id){ $(id).addEventListener("change", syncTrip); });

  // ペットの入力欄（頭数を選ぶと、その数だけカードを出す）
  function seg(name, items, req){
    return '<div class="seg">' + items.map(function(it, i){
      return '<label><input type="radio" name="' + name + '" value="' + it[0] + '"' + (req && i === 0 ? ' required' : '') + '><span>' + it[1] + '</span></label>';
    }).join('') + '</div>';
  }
  // 介護が必要なときに出す選択肢（会社によって受けられるかが変わるもの）
  var CARE_OPTS = ["歩けない（抱っこで運ぶ）", "寝たきり（担架やマットで運ぶ）", "階段で運び出す（エレベーターなし）", "酸素や点滴などの医療機器がある", "カートやバギーごと乗りたい"];
  function syncPetCard(card){
    var sp = card.querySelector("input[name$=_species]:checked"), care = card.querySelector("input[name$=_care]:checked");
    card.querySelector(".rabies").hidden = !!sp && sp.value !== "犬"; // 狂犬病の予防注射は犬だけ
    card.querySelector(".care-box").hidden = !care || care.value !== "必要";
    // 「その他」のときは、どんな動物かを選んでもらう（会社によって乗せられる動物が違う）
    var other = !!sp && sp.value === "その他", kind = card.querySelector(".kind-box");
    kind.hidden = !other; kind.querySelector("select").required = other;
    card.querySelector(".breed-lbl").textContent = other ? "くわしい種類" : "犬種・猫種";
  }
  // 犬・猫のほかの動物（ここで選んだものが「種類」として届く）
  var KINDS = [["うさぎ","うさぎ"],["フェレット","フェレット"],["ハムスター・モルモットなどの小動物","ハムスター・モルモットなど"],["鳥","鳥（インコ・文鳥など）"],["爬虫類・両生類","爬虫類・両生類（カメ・ヘビなど）"],["魚","魚（熱帯魚・金魚など）"],["そのほかの動物","そのほかの動物"]];
  function petCard(n){
    var k = "p" + n;
    var el = document.createElement("div");
    el.className = "pet";
    el.dataset.key = k;
    el.innerHTML =
      '<div class="pet-h"><b></b></div>' +
      '<div class="f"><span class="lbl">種類<span class="need">必須</span></span>' + seg(k + "_species", [["犬","わんちゃん"],["猫","ねこちゃん"],["その他","そのほかの動物"]], true) +
        '<div class="kind-box" hidden><label for="' + k + '_kind" class="lbl" style="margin-top:10px;font-weight:700">どんな動物ですか？<span class="need">必須</span></label><select id="' + k + '_kind" name="' + k + '_kind"><option value="">選んでください</option>' +
        KINDS.map(function(o){ return '<option value="' + o[0] + '">' + o[1] + '</option>'; }).join('') + '</select>' +
        '<p style="margin:6px 0 0;font-size:.8rem;color:var(--ink-3)">乗せられる動物は会社ごとに違います。乗せられると公式サイトに書いてある会社を先に出します。</p></div></div>' +
      '<div class="two">' +
        '<div class="f opt-lite"><label for="' + k + '_breed"><span class="breed-lbl">犬種・猫種</span><span class="any">わかれば</span></label><div class="cb"><input type="text" id="' + k + '_breed" name="' + k + '_breed" class="breed" placeholder="選ぶか、入力してしぼりこみ" autocomplete="off" role="combobox" aria-expanded="false" aria-autocomplete="list"><ul class="cb-list" role="listbox" hidden></ul></div></div>' +
        '<div class="f"><label for="' + k + '_weight">体重（kg）<span class="need">必須</span></label><input type="number" id="' + k + '_weight" name="' + k + '_weight" min="0.01" max="120" step="any" inputmode="decimal" placeholder="例：8（小さな子は 0.3 など）" required></div>' +
        '<div class="f opt-lite"><label for="' + k + '_age">年齢<span class="any">わかれば</span></label><input type="number" id="' + k + '_age" name="' + k + '_age" min="0" max="40" inputmode="numeric" placeholder="例：12"></div>' +
        '<div class="f opt-lite"><span class="lbl">性別<span class="any">わかれば</span></span>' + seg(k + "_sex", [["オス","男の子"],["メス","女の子"]], false) + '</div>' +
      '</div>' +
      '<div class="f opt-lite"><span class="lbl">ケージ・キャリー<span class="need">必須</span></span>' + seg(k + "_cage", [["持ち込む","持っていく"],["なし","なしで乗りたい"],["借りたい","借りたい"],["どれでも","あり・なし どちらでもいい"]], true) + '</div>' +
      '<div class="f opt-lite"><span class="lbl">予防接種<span class="any">済んでいるものにチェック</span></span><div class="chks">' +
        '<label class="chk"><input type="checkbox" name="' + k + '_vac" value="1"> 混合ワクチン</label>' +
        '<label class="chk rabies"><input type="checkbox" name="' + k + '_rabies" value="1"> 狂犬病の予防注射</label></div></div>' +
      '<div class="f opt-lite"><span class="lbl">介護は必要ですか？<span class="need">必須</span></span>' + seg(k + "_care", [["不要","いらない"],["必要","必要（歩くのがつらい等）"]], true) +
        '<div class="care-box" hidden><span class="lbl">どんな手助けが必要ですか？<span class="any">あてはまるものすべて</span></span><div class="chks">' +
        CARE_OPTS.map(function(c){ return '<label class="chk"><input type="checkbox" name="' + k + '_care_need" value="' + c + '"> ' + c + '</label>'; }).join('') + '</div>' +
        '<label for="' + k + '_care_note" class="lbl" style="margin-top:6px">くわしいこと<span class="any">わかれば</span></label><input type="text" id="' + k + '_care_note" name="' + k + '_care_note" maxlength="200" placeholder="例：後ろ足が立たない。3階でエレベーターなし"></div></div>';
    return el;
  }
  // 入力済みのカードは残したまま、数だけ増やす・減らす
  function setPetCount(n){
    n = Math.max(0, Math.min(MAX_PETS, Number(n) || 0));
    var cards = petsBox.querySelectorAll(".pet");
    for (var i = cards.length; i > n; i--) cards[i - 1].remove();
    for (var j = cards.length; j < n; j++) petsBox.appendChild(petCard(j + 1));
    petsBox.querySelectorAll(".pet").forEach(function(c, i){
      c.querySelector(".pet-h b").textContent = n > 1 ? (i + 1) + "匹目" : "ペットの情報";
    });
    $("petHint").hidden = n > 0;
    if (form.classList.contains("lite")) petsBox.querySelectorAll(".opt-lite input, .opt-lite select").forEach(function(el){ el.disabled = true; });
  }
  countSel.addEventListener("change", function(){ setPetCount(countSel.value); });
  setPetCount(countSel.value); // 最初から1匹分の欄を出す（いちばん多い1匹なら、頭数を選ぶ手間がいらない）
  // 「ペットだけで乗る」：人数は0人にして、渡す人・受け取る人をたずねる
  function syncOnly(){
    var on = $("petOnly").checked;
    $("onlyBox").hidden = !on; $("ridersF").hidden = on;
    $("handFrom").required = on; $("handTo").required = on;
    if (on) $("riders").value = "0人（ペットだけ）";
    else if (/^0/.test($("riders").value)) $("riders").value = "";
  }
  $("petOnly").addEventListener("change", function(){ syncOnly(); $("riders").dispatchEvent(new Event("change", {bubbles: true})); });
  $("riders").addEventListener("change", function(){ if (/^0/.test($("riders").value) && !$("petOnly").checked) { $("petOnly").checked = true; syncOnly(); } });

  // ── 犬種・猫種：一覧から選ぶか、入力するとしぼりこみ（一覧にない種類はそのまま入力できる）──
  var BREEDS = {
    "犬": ["ミックス（雑種）|ざっしゅ","トイ・プードル","チワワ","柴犬|しばいぬ","豆柴|まめしば","ミニチュア・ダックスフンド","カニーンヘン・ダックスフンド","ポメラニアン","ミニチュア・シュナウザー","ヨークシャー・テリア","フレンチ・ブルドッグ","マルチーズ","シー・ズー","パピヨン","ゴールデン・レトリーバー","ラブラドール・レトリーバー","ウェルシュ・コーギー・ペンブローク","ジャック・ラッセル・テリア","パグ","キャバリア・キング・チャールズ・スパニエル","ミニチュア・ピンシャー","ビション・フリーゼ","ボーダー・コリー","シェットランド・シープドッグ","ペキニーズ","イタリアン・グレーハウンド","ボストン・テリア","ビーグル","ウエスト・ハイランド・ホワイト・テリア","アメリカン・コッカー・スパニエル","狆|ちん","日本スピッツ|にほん","秋田犬|あきたいぬ","甲斐犬|かいけん","北海道犬|ほっかいどういぬ","紀州犬|きしゅういぬ","四国犬|しこくけん","シベリアン・ハスキー","サモエド","バーニーズ・マウンテン・ドッグ","グレート・ピレニーズ","セント・バーナード","グレート・デーン","ドーベルマン","ジャーマン・シェパード・ドッグ","ボクサー","ブルドッグ","スタンダード・プードル","ミディアム・プードル","ボルゾイ","ウィペット"],
    "猫": ["ミックス（雑種）|ざっしゅ","スコティッシュ・フォールド","マンチカン","ラグドール","ブリティッシュ・ショートヘア","アメリカン・ショートヘア","ノルウェージャン・フォレスト・キャット","メインクーン","ロシアンブルー","ベンガル","エキゾチック・ショートヘア","ペルシャ","ヒマラヤン","ミヌエット","サイベリアン","アビシニアン","ソマリ","シャム","シンガプーラ","ラガマフィン","バーマン","トンキニーズ","セルカーク・レックス","デボン・レックス","スフィンクス","ターキッシュアンゴラ","エジプシャン・マウ","オリエンタル"],
    "その他": ["うさぎ","フェレット","モルモット","ハムスター","チンチラ","ハリネズミ","デグー","リス","インコ","オウム","文鳥|ぶんちょう","カナリア","カメ","トカゲ","ヘビ","カエル","熱帯魚","金魚","メダカ"]
  };
  // ひらがな・カタカナ、「・」や空白、全角・半角の違いを気にせずしぼりこむ
  function norm(t){
    return String(t || "").normalize("NFKC").toLowerCase()
      .replace(/[ぁ-ゖ]/g, function(c){ return String.fromCharCode(c.charCodeAt(0) + 0x60); })
      .replace(/[・･\s\-ー（）()]/g, "");
  }
  function breedList(card){
    var sp = card.querySelector("input[name$=_species]:checked");
    return BREEDS[sp ? sp.value : "犬"].concat(sp ? [] : BREEDS["猫"].slice(1));
  }
  function openList(inp){
    var card = inp.closest(".pet"), ul = inp.parentNode.querySelector(".cb-list"), q = norm(inp.value);
    var items = breedList(card).filter(function(b){ return !q || norm(b).indexOf(q) >= 0; });
    ul.innerHTML = items.length ? items.map(function(b){ return '<li role="option">' + b.split("|")[0] + '</li>'; }).join("")
      : '<li class="none">一覧にありません。このまま入力してください</li>';
    ul.hidden = false; inp.setAttribute("aria-expanded", "true");
  }
  function closeList(inp){
    var ul = inp.parentNode.querySelector(".cb-list");
    ul.hidden = true; inp.setAttribute("aria-expanded", "false");
  }
  petsBox.addEventListener("focusin", function(e){ if (e.target.classList.contains("breed")) openList(e.target); });
  petsBox.addEventListener("input", function(e){ if (e.target.classList.contains("breed")) openList(e.target); });
  petsBox.addEventListener("focusout", function(e){
    if (e.target.classList.contains("breed")) { var t = e.target; setTimeout(function(){ closeList(t); }, 150); }
  });
  // 選んだら入力欄に入れる（スマホでもタップ1回で決まるよう mousedown で拾う）
  petsBox.addEventListener("mousedown", function(e){
    var li = e.target.closest(".cb-list li");
    if (!li || li.classList.contains("none")) return;
    e.preventDefault();
    var inp = li.closest(".cb").querySelector(".breed");
    inp.value = li.textContent; closeList(inp);
  });
  petsBox.addEventListener("keydown", function(e){
    if (!e.target.classList.contains("breed")) return;
    var ul = e.target.parentNode.querySelector(".cb-list");
    if (ul.hidden) return;
    var lis = Array.prototype.slice.call(ul.querySelectorAll("li:not(.none)")), i = lis.findIndex(function(l){ return l.classList.contains("on"); });
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); if (!lis.length) return;
      if (i >= 0) lis[i].classList.remove("on");
      i = e.key === "ArrowDown" ? Math.min(lis.length - 1, i + 1) : Math.max(0, i - 1);
      lis[i].classList.add("on"); lis[i].scrollIntoView({block:"nearest"});
    } else if (e.key === "Enter" && i >= 0) {
      e.preventDefault(); e.target.value = lis[i].textContent; closeList(e.target);
    } else if (e.key === "Escape") closeList(e.target);
  });
  // 種類を変えたら、合わない犬種・猫種は消す
  petsBox.addEventListener("change", function(e){
    if (/_(species|care)$/.test(e.target.name)) syncPetCard(e.target.closest(".pet"));
    if (!/_species$/.test(e.target.name)) return;
    var card = e.target.closest(".pet"), inp = card.querySelector(".breed");
    var names = function(l){ return l.map(function(b){ return b.split("|")[0]; }); };
    if (inp.value && names(breedList(card)).indexOf(inp.value) < 0 && Object.keys(BREEDS).some(function(k){ return names(BREEDS[k]).indexOf(inp.value) >= 0; })) inp.value = "";
  });


  function readPets(){
    var fd = new FormData(form);
    return Array.prototype.map.call(petsBox.querySelectorAll(".pet"), function(c){
      var k = c.dataset.key, g = function(f){ return String(fd.get(k + "_" + f) || "").trim(); };
      var care = g("care"), dog = !g("species") || g("species") === "犬";
      return { species:g("species") === "その他" && g("kind") ? g("kind") : g("species"), breed:g("breed"), weight:g("weight"), age:g("age"), sex:g("sex"), cage:g("cage"), care:care,
        vaccine: g("vac") ? "済" : "", rabies: dog && g("rabies") ? "済" : "",
        care_need: care === "必要" ? fd.getAll(k + "_care_need").map(String) : [], care_note: care === "必要" ? g("care_note") : "" };
    });
  }
  function petLine(p, i){
    return (i + 1) + "匹目：" + [p.species, p.breed, p.weight ? p.weight + "kg" : "", p.age ? p.age + "歳" : "", p.sex,
      ({"持ち込む":"ケージ持ち込み","なし":"ケージなし希望","借りたい":"ケージを借りたい","どれでも":"ケージはあり・なしどちらでも"})[p.cage] || p.cage,
      p.vaccine ? "混合ワクチン済み" : "", p.rabies ? "狂犬病予防注射済み" : "",
      p.care === "必要" ? "介助必要" + ((p.care_need || []).length || p.care_note ? "（" + (p.care_need || []).concat(p.care_note ? [p.care_note] : []).join("／") + "）" : "") : p.care ? "介助いらない" : ""].filter(String).join("・");
  }


  // ── ふつうのタクシー（Nori 2026-11-01「犬種や猫種によっては普通のタクシーも使える。対応してるところのみにしぼって」）──
  // ペット同乗を公式サイトに書いている会社だけ（tools/regular_taxis.json）。ご案内だけで、問い合わせの送り先にはしない。
  // 出すのは、犬・猫が1〜2匹、全員10kgまででケージを持っていく、飼い主さんが一緒に乗る、お迎えの住所が会社の地域のとき。
  // Nori 2026-11-02「公開」。止めるときは REGULAR_TAXI_ON を false にする。
  var REGULAR_TAXI_ON = true;
  /*TAXIS*/var TAXIS = {"checked": "2026-11-02", "taxis": [{"id": "mk-sapporo", "name": "札幌MKタクシー", "pref": "北海道", "cities": ["札幌市"], "area_label": "札幌市", "rule": "小型のペットで、扉の閉まったケージに全身が入っていれば一緒に乗れます（顔も出さない・車内ではケージから出さない・毛布でくるむだけは不可）。", "fare": {"base_km": 1.05, "base": 540, "add_m": 302, "pick": 200, "resv": 0, "night": 1.2}, "url": "https://www.mk-group.co.jp/sapporo/"}, {"id": "mk-nagoya", "name": "名古屋MKタクシー", "pref": "愛知県", "cities": ["名古屋市"], "area_label": "名古屋市", "rule": "小型のペットで、扉の閉まったケージに全身が入っていれば一緒に乗れます（顔も出さない・車内ではケージから出さない・毛布でくるむだけは不可）。", "fare": {"base_km": 0.91, "base": 470, "add_m": 247, "pick": 200, "resv": 200, "night": 1.2}, "url": "https://www.mk-group.co.jp/nagoya/"}, {"id": "mk-shiga", "name": "滋賀MKタクシー", "pref": "滋賀県", "cities": ["大津市", "草津市", "守山市", "栗東市", "野洲市"], "area_label": "大津・湖南", "rule": "小型のペットで、扉の閉まったケージに全身が入っていれば一緒に乗れます（顔も出さない・車内ではケージから出さない・毛布でくるむだけは不可）。", "fare": {"base_km": 0.9, "base": 480, "add_m": 227, "pick": 0, "resv": 0, "night": 1.2}, "url": "https://www.mk-group.co.jp/shiga/"}, {"id": "mk-kyoto", "name": "京都MKタクシー", "pref": "京都府", "cities": ["京都市"], "area_label": "京都市", "rule": "小型のペットで、扉の閉まったケージに全身が入っていれば一緒に乗れます（顔も出さない・車内ではケージから出さない・毛布でくるむだけは不可）。", "fare": {"base_km": 0.9, "base": 470, "add_m": 271, "pick": 300, "resv": 500, "night": 1.2}, "url": "https://www.mk-group.co.jp/kyoto/"}, {"id": "mk-osaka", "name": "大阪MKタクシー", "pref": "大阪府", "cities": ["大阪市"], "area_label": "大阪市", "rule": "小型のペットで、扉の閉まったケージに全身が入っていれば一緒に乗れます（顔も出さない・車内ではケージから出さない・毛布でくるむだけは不可）。", "fare": {"base_km": 0.969, "base": 500, "add_m": 231, "pick": 300, "resv": 0, "night": 1.2}, "url": "https://www.mk-group.co.jp/osaka/"}, {"id": "mk-kobe", "name": "神戸MKタクシー", "pref": "兵庫県", "cities": ["神戸市"], "area_label": "神戸市", "rule": "小型のペットで、扉の閉まったケージに全身が入っていれば一緒に乗れます（顔も出さない・車内ではケージから出さない・毛布でくるむだけは不可）。", "fare": {"base_km": 0.836, "base": 480, "add_m": 232, "pick": 300, "resv": 500, "night": 1.2}, "url": "https://www.mk-group.co.jp/kobe/"}, {"id": "mk-fukuoka", "name": "福岡MKタクシー", "pref": "福岡県", "cities": ["福岡市"], "area_label": "福岡市", "rule": "小型のペットで、扉の閉まったケージに全身が入っていれば一緒に乗れます（顔も出さない・車内ではケージから出さない・毛布でくるむだけは不可）。", "fare": {"base_km": 1.1, "base": 600, "add_m": 287, "pick": 300, "resv": 300, "night": 1.2}, "url": "https://www.mk-group.co.jp/fukuoka/"}, {"id": "mk-okinawa", "name": "沖縄MKタクシー", "pref": "沖縄県", "cities": ["那覇市"], "area_label": "那覇市", "rule": "小型のペットで、扉の閉まったケージに全身が入っていれば一緒に乗れます（顔も出さない・車内ではケージから出さない・毛布でくるむだけは不可）。", "fare": {"base_km": 1.65, "base": 650, "add_m": 350, "pick": 300, "resv": 300, "night": 1.2}, "url": "https://www.mk-group.co.jp/okinawa/"}, {"id": "daiwa-tokyo", "name": "大和自動車交通", "pref": "東京都", "cities": ["千代田区", "中央区", "港区", "新宿区", "文京区", "台東区", "墨田区", "江東区", "品川区", "目黒区", "大田区", "世田谷区", "渋谷区", "中野区", "杉並区", "豊島区", "北区", "荒川区", "板橋区", "練馬区", "足立区", "葛飾区", "江戸川区", "武蔵野市", "三鷹市"], "area_label": "東京23区・武蔵野市・三鷹市", "rule": "膝にのせられるくらいのケージなら、そのまま一緒に乗れます。予約のときに、ペットと乗ることを伝えてください。", "fare": {"base_km": 1.0, "base": 500, "add_m": 232, "pick": 500, "resv": 500, "night": 1.2}, "url": "https://www.daiwaj.com/service/taxi"}, {"id": "kanachu-kenou", "name": "神奈中タクシー", "pref": "神奈川県", "cities": ["藤沢市", "茅ヶ崎市", "平塚市", "伊勢原市", "秦野市", "相模原市", "大和市", "座間市", "海老名市", "綾瀬市", "厚木市", "寒川町"], "area_label": "神奈川県の県央・湘南（藤沢・相模原・厚木など）", "rule": "ケージや容器に入れて、ふたを閉めた状態なら一緒に乗れます（タオルで包む・抱っこのままは断られることがあります）。", "fare": {"base_km": 1.0, "base": 500, "add_m": 223, "pick": 500, "resv": 0, "night": 1.2}, "url": "https://kanachu-taxi.co.jp/"}]};/*/TAXIS*/
  function taxiFit(){
    if (!REGULAR_TAXI_ON || !TAXIS.taxis.length) return false;
    if (/^0/.test($("riders").value || "")) return false;
    var pets = readPets();
    if (!pets.length || pets.length > 2) return false;
    return pets.every(function(p){ var w = Number(p.weight); return (p.species === "犬" || p.species === "猫") && p.weight !== "" && isFinite(w) && w > 0 && w <= 10 && p.cage === "持ち込む"; });
  }
  function taxiMeter(f, km, night){
    var m = km <= f.base_km ? f.base : f.base + Math.ceil((km - f.base_km) * 1000 / f.add_m) * 100;
    return Math.round((night ? m * f.night : m) + f.pick + f.resv);
  }
  function drawTaxis(){
    var box = $("taxiBox"); box.hidden = true; $("taxiList").replaceChildren();
    if (!routeDetails || partnerBlock() !== "" || !taxiFit()) return;
    var addr = $("pickup").value || "", pref = $("pref").value;
    var list = TAXIS.taxis.filter(function(t){ return t.pref === pref && t.cities.some(function(c){ return addr.indexOf(c) >= 0; }); });
    if (!list.length) return;
    var fd = new FormData(form), later = fd.get("trip") === "往復";
    var isNight = function(h){ if (h == null || h === "") return false; h = Number(h); return h >= 22 || h < 5; };
    var yen = function(n){ return (Math.round(n / 100) * 100).toLocaleString("ja-JP") + "円"; };
    list.forEach(function(t){
      var el = document.createElement("div"); el.className = "taxi-card";
      var go = taxiMeter(t.fare, routeDetails.km, isNight(fd.get("hour")));
      var back = later ? taxiMeter(t.fare, routeDetails.backKm, isNight(fd.get("ret_hour"))) : 0;
      var h = document.createElement("h4"); h.textContent = t.name; el.appendChild(h);
      var area = document.createElement("p"); area.className = "taxi-area"; area.textContent = "お迎えの地域：" + t.area_label; el.appendChild(area);
      var rule = document.createElement("p"); rule.className = "taxi-rule"; rule.textContent = t.rule; el.appendChild(rule);
      var fare = document.createElement("p"); fare.className = "taxi-fare";
      fare.innerHTML = "運賃の目安 <b></b><small>概算です（確定料金ではありません）</small>";
      fare.querySelector("b").textContent = later ? "行き " + yen(go) + "・帰り " + yen(back) : "片道 " + yen(go);
      el.appendChild(fare);
      var a = document.createElement("a"); a.className = "taxi-link"; a.href = t.url; a.target = "_blank"; a.rel = "noopener";
      a.textContent = "公式サイトで予約のしかたを見る ↗"; el.appendChild(a);
      $("taxiList").appendChild(el);
    });
    $("taxiNote").textContent = "運賃の目安は、各社の公式サイトの運賃（メーター）で道のりから計算し、呼んだときの迎車料金と時間指定の料金を足して100円単位にまるめたものです（夜22時〜朝5時は2割増）。渋滞や道順で実際の運賃は変わり、有料道路の料金は別です。各社の情報は" + TAXIS.checked.replace(/^(\d+)-0?(\d+)-0?(\d+)$/, "$1年$2月$3日") + "に確認しました。";
    box.hidden = false;
  }

  // ── 概算料金（お迎え場所 → 経由地 → 行き先 の距離から計算）──
  // 提携先ごとの料金表と、都県ごとの依頼先。tools/fares.json から gen_areas.py が書き込む（ここは手で直さない）。
  /*FARES*/var FARES = {"petexpress": {"label": "東京・世田谷の会社", "base_km": 5, "base": 2200, "tiers": [[100, 220], [200, 165], [null, 110]], "pick": 330, "back": 330, "night": 1.2, "night_hours": [18, 8], "round_flat": null, "wait": {"30": 660, "60": 1320, "120": 2640}, "shop": [35.6339, 139.6697], "pick_free_km": 3, "pick_over": 220}, "kuriki": {"label": "千葉・松戸の会社", "base_km": 4, "base": 1800, "tiers": [[100, 200], [200, 150], [null, 100]], "pick": 0, "back": 0, "night": 1.0, "night_hours": null, "round_flat": [10, 3300], "wait": {"30": 0, "60": 500, "120": 1500}, "shop": null, "pick_free_km": null, "pick_over": null}};
  var AREA_FARES = {"東京都": ["petexpress", "kuriki"], "神奈川県": ["petexpress", "kuriki"], "千葉県": ["kuriki"], "埼玉県": ["petexpress", "kuriki"]};/*/FARES*/
  // 実際の料金が目安を超えないよう、上限側で計算する（道のりは直線の1.5倍、1km単位で切り上げ、最後に100円単位で切り上げ）
  var ROAD = 1.5;
  var est = $("est"), geoCache = {}, pickedPlace = {}, estSeq = 0, lastKm = 0, lastKmHigh = 0, lastFare = "", lastFareNum = 0;
  // 料金の目安は100円単位にまるめて出す（Nori 2026-11-01「1円単位まで出さない方がいい」）。並び替えは計算どおりの金額で行う
  function yen(n){ return (n >= 100 ? Math.round(n / 100) * 100 : n).toLocaleString("ja-JP") + "円"; }
  function roundYenText(s){ return String(s == null ? "" : s).replace(/(\d{1,3}(?:,\d{3})+|\d+)円/g, function(m, d){ return yen(Number(d.replace(/,/g, ""))); }); }
  // 場所の検索は4都県の中だけで探す（遠くの同じ名前の場所を拾わないように）。選んだ都県の中の候補を優先する
  // 全国のお迎えも入れられる（Nori 2026-10-31「全国にして。絞らないで」）。予約の依頼は全社準備中のため送れない（Code.gs の CONFIG.SHOW_ALL_CANDIDATES）
  // 1都3県だけに戻すときは false にする
  var ALL_JAPAN = true;
  var BOXJP = [20, 122, 46, 154]; // 緊急タブの場所の欄は全国で探す
  var BOX4 = ALL_JAPAN ? BOXJP : [34.85, 138.6, 36.35, 140.95];
  var BOXNEAR = ALL_JAPAN ? BOXJP : [34.5, 137.4, 37.3, 141.2]; // 行き先・経由地・帰りの場所は、4都県のまわり（茨城・栃木・群馬・山梨・静岡など）も入れられる
  var PREF_NAMES = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"];
  var PREF_HEAD = new RegExp("^(" + PREF_NAMES.join("|") + ")");
  function boxOf(w){ return w === true ? BOXJP : w === "near" ? BOXNEAR : BOX4; }
  // 端末の位置：まず速い方法（Wi-Fiなど・数分以内に調べた位置も使う）で読み、だめなときだけ時間のかかるGPSで読み直す
  function getPos(ok, ng){
    navigator.geolocation.getCurrentPosition(ok, function(e){
      if (e.code === 1) { ng(e); return; } // 許可されなかったときは読み直さない
      navigator.geolocation.getCurrentPosition(ok, ng, {enableHighAccuracy: true, timeout: 12000, maximumAge: 0});
    }, {enableHighAccuracy: false, timeout: 5000, maximumAge: 300000});
  }
  // お迎えの都道府県の並び順（Nori 2026-10-31「ユーザの所在地に合わせて近いところが上に。あとは北海道から順に」）
  // 近い順の元：エリアページなどで選ばれている都道府県 → 位置の利用がすでに許可されていれば端末の位置 → 通信の情報からの大まかな地域。
  // 許可の確認は新しく出さない。分からないときは北海道から順のまま。選んでいる値は変えない
  var PREF_LL = [[43.06,141.35],[40.82,140.74],[39.70,141.15],[38.27,140.87],[39.72,140.10],[38.24,140.36],[37.75,140.47],[36.34,140.45],[36.57,139.88],[36.39,139.06],[35.86,139.65],[35.61,140.12],[35.69,139.69],[35.45,139.64],[37.90,139.02],[36.70,137.21],[36.59,136.63],[36.07,136.22],[35.66,138.57],[36.65,138.18],[35.39,136.72],[34.98,138.38],[35.18,136.91],[34.73,136.51],[35.00,135.87],[35.02,135.76],[34.69,135.52],[34.69,135.18],[34.69,135.83],[34.23,135.17],[35.50,134.24],[35.47,133.05],[34.66,133.93],[34.40,132.46],[34.19,131.47],[34.07,134.56],[34.34,134.04],[33.84,132.77],[33.56,133.53],[33.61,130.42],[33.25,130.30],[32.74,129.87],[32.79,130.74],[33.24,131.61],[31.91,131.42],[31.56,130.56],[26.21,127.68]];
  var PREF_NEAR_N = 6; // 上に出す数（その都道府県を含む）
  function llDist(a, b){ var dy = a[0] - b[0], dx = (a[1] - b[1]) * Math.cos((a[0] + b[0]) * Math.PI / 360); return dx * dx + dy * dy; }
  function prefAt(lat, lng){
    var best = -1, bd = Infinity;
    PREF_LL.forEach(function(p, i){ var d = llDist([lat, lng], p); if (d < bd) { bd = d; best = i; } });
    return best >= 0 && bd < 4 ? PREF_NAMES[best] : ""; // 日本の外（2度より遠い）なら使わない
  }
  function sortPrefs(base){
    var sel = $("pref"), i0 = PREF_NAMES.indexOf(base);
    if (!sel || i0 < 0) return;
    if (document.activeElement === sel) { sel.addEventListener("blur", function(){ sortPrefs(base); }, {once: true}); return; }
    var have = {}; Array.prototype.forEach.call(sel.querySelectorAll("option"), function(o){ if (o.value) have[o.value] = 1; });
    var near = PREF_NAMES.filter(function(n){ return have[n]; }).sort(function(a, b){
      return llDist(PREF_LL[PREF_NAMES.indexOf(a)], PREF_LL[i0]) - llDist(PREF_LL[PREF_NAMES.indexOf(b)], PREF_LL[i0]);
    }).slice(0, PREF_NEAR_N);
    var rest = PREF_NAMES.filter(function(n){ return have[n] && near.indexOf(n) < 0; });
    if (!rest.length) near.sort(function(a, b){ return PREF_NAMES.indexOf(a) - PREF_NAMES.indexOf(b); });
    var v = sel.value, h = '<option value="">選んでください</option>';
    function opts(list){ return list.map(function(n){ return "<option>" + n + "</option>"; }).join(""); }
    h += rest.length ? '<optgroup label="近くの都道府県">' + opts(near) + '</optgroup><optgroup label="そのほか（北海道から順）">' + opts(rest) + '</optgroup>' : opts(near);
    sel.innerHTML = h; sel.value = v; markPrefs();
  }
  (function(){
    if ($("pref").value) { sortPrefs($("pref").value); return; }
    function byNet(){
      var ac = window.AbortController ? new AbortController() : null, t = ac && setTimeout(function(){ ac.abort(); }, 4000);
      fetch("https://get.geojs.io/v1/ip/geo.json", ac ? {signal: ac.signal} : {}).then(function(r){ return r.json(); }).then(function(d){
        clearTimeout(t);
        if (d && d.country_code === "JP" && !$("pref").value) sortPrefs(prefAt(+d.latitude, +d.longitude));
      }).catch(function(){});
    }
    if (navigator.permissions && navigator.geolocation) {
      navigator.permissions.query({name: "geolocation"}).then(function(s){
        if (s.state !== "granted") { byNet(); return; }
        navigator.geolocation.getCurrentPosition(function(pos){ if (!$("pref").value) sortPrefs(prefAt(pos.coords.latitude, pos.coords.longitude)); }, byNet, {enableHighAccuracy: false, timeout: 5000, maximumAge: 600000});
      }, byNet);
    } else byNet();
  })();
  // 位置を住所の文字に直す（待ちすぎないよう6秒で打ち切る）
  function reverseOsm(c, zoom){
    var ac = window.AbortController ? new AbortController() : null, t = ac && setTimeout(function(){ ac.abort(); }, 6000);
    return fetch("https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=" + zoom + "&accept-language=ja&lat=" + c.lat.toFixed(6) + "&lon=" + c.lng.toFixed(6), ac ? {signal: ac.signal} : {})
      .then(function(r){ clearTimeout(t); return r.json(); });
  }
  var PREF_BOX = {"東京都": [35.48, 138.9, 35.9, 139.93], "神奈川県": [35.12, 138.9, 35.68, 139.8], "千葉県": [34.88, 139.73, 36.11, 140.9], "埼玉県": [35.74, 138.7, 36.29, 139.91]};
  function inBox(c, b){ return c && c.lat >= b[0] && c.lat <= b[2] && c.lng >= b[1] && c.lng <= b[3]; }
  function pickIn(list, box){
    var pb = PREF_BOX[$("pref").value];
    return list.filter(function(c){ return pb && inBox(c, pb); })[0] || list.filter(function(c){ return inBox(c, BOX4); })[0] || (box && list.filter(function(c){ return inBox(c, box); })[0]) || null;
  }
  // 住所の検索はあいまいに当てはめるので（「東京駅」で各地の「〇〇東」が出る）、入れた住所と頭から一致するものだけ使う
  var KNUM = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10};
  function normAddr(t){
    return String(t).replace(/[\s　]/g, "").replace(/[０-９]/g, function(d){ return String.fromCharCode(d.charCodeAt(0) - 0xFEE0); })
      .replace(/[ヶヵが]/g, "ケ").replace(/([一二三四五六七八九十]+)丁目/g, function(m, k){
        var n = 0, cur = 0; k.split("").forEach(function(ch){ var v = KNUM[ch]; if (v === 10) { cur = (cur || 1) * 10; } else { cur += v; } }); n = cur; return n + "丁目"; });
  }
  function addrMatch(q, title){
    var a = normAddr(q), t = normAddr(title), t2 = t.replace(PREF_HEAD, "");
    var ok = function(x){ var m = x.match(/^.*?[区市町村]/); return m && (a.indexOf(x) === 0 || (x.indexOf(a) === 0 && a.length >= m[0].length)); };
    return ok(t) || (t2 !== t && ok(t2));
  }
  function looksAddress(q){ return /[区市町村郡]|丁目|番地|\d|[０-９]/.test(q); }
  function gsi(q){
    return fetch("https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + encodeURIComponent(q))
      .then(function(r){ return r.json(); })
      .then(function(a){
        return pickIn((a || []).filter(function(x){ return addrMatch(q, (x.properties || {}).title || ""); })
          .map(function(x){ var c = x.geometry.coordinates; return {lng: c[0], lat: c[1]}; }));
      })
      .catch(function(){ return null; });
  }
  // 駅・公園・病院などの名前は、地図データの検索で探す（4都県の範囲だけ）
  function placeMatch(q, result){
    if (!/空港/.test(q)) return true;
    function airportName(t){return normAddr(t).replace(/東京国際空港/g,"羽田空港").replace(/成田国際空港/g,"成田空港").replace(PREF_HEAD,"");}
    var query = airportName(q).match(/.*?空港/);
    var airport = result.category === "aeroway" || result.class === "aeroway" || /^(aerodrome|terminal)$/.test(result.type || "");
    return !!(airport && query && airportName(result.display_name || result.name || "").indexOf(query[0]) >= 0);
  }
  function osm(q, box){
    var b = box || BOX4;
    return fetch("https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&countrycodes=jp&accept-language=ja&bounded=1&viewbox=" +
        [b[1], b[2], b[3], b[0]].join(",") + "&q=" + encodeURIComponent(q))
      .then(function(r){ return r.json(); })
      .then(function(a){ return pickIn((a || []).filter(function(x){return placeMatch(q,x);}).map(function(x){ return {lng: Number(x.lon), lat: Number(x.lat)}; }), box); })
      .catch(function(){ return null; });
  }
  function geocode(q, near){
    q = q.trim();
    if (!q) return Promise.resolve(null);
    if (pickedPlace[q]) return Promise.resolve(pickedPlace[q]); // 候補から選んだ場所は、その位置をそのまま使う
    var pref = $("pref").value;
    var key = (!pref || PREF_HEAD.test(q) || /^(東京|神奈川|千葉|埼玉|大阪|京都)/.test(q) ? "" : pref) + q;
    if (key in geoCache && (geoCache[key] || !near)) return Promise.resolve(geoCache[key]);
    if (near && ("~" + key) in geoCache) return Promise.resolve(geoCache["~" + key]);
    // 順に試して、最初に見つかったものを使う
    var tries = looksAddress(q) ? [[gsi, key], [gsi, q], [osm, key], [osm, q]] : [[osm, q], [osm, key], [gsi, q], [gsi, key]];
    var seen = {};
    tries = tries.filter(function(t){ var k = t[0] === gsi ? "g" + t[1] : "o" + t[1]; if (seen[k]) return false; return seen[k] = true; });
    var p = Promise.resolve(null);
    tries.forEach(function(t){ p = p.then(function(c){ return c || t[0](t[1]); }); });
    // 行き先などは、4都県で見つからなければ、まわりの県まで広げて探す（施設の名前は大手の地図の検索も使う）
    if (near) p = p.then(function(c){ return c || googleText(q, "near").then(function(l){ return (l[0] || {}).c || null; }); })
      .then(function(c){ return c || osm(q, BOXNEAR); });
    return p.then(function(c){ return geoCache[(near ? "~" : "") + key] = c; });
  }
  // 位置から都県を調べる（市区町村コードの頭2桁）。4都県の外なら "out"、調べられなければ null
  var PREF_CD = ALL_JAPAN ? {} : {"13": "東京都", "14": "神奈川県", "12": "千葉県", "11": "埼玉県"}, prefCache = {};
  if (ALL_JAPAN) PREF_NAMES.forEach(function(n, i){ PREF_CD[(i < 9 ? "0" : "") + (i + 1)] = n; });
  function prefOf(c){
    var k = c.lat.toFixed(4) + "," + c.lng.toFixed(4);
    if (k in prefCache) return Promise.resolve(prefCache[k]);
    return fetch("https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress?lat=" + c.lat.toFixed(6) + "&lon=" + c.lng.toFixed(6))
      .then(function(r){ return r.json(); })
      .then(function(j){ var cd = j && j.results && String(j.results.muniCd || ""); return prefCache[k] = cd ? (PREF_CD[cd.slice(0, 2)] || "out") : null; })
      .catch(function(){ return null; });
  }
  function kmBetween(a, b){
    var R = 6371, t = Math.PI / 180, dLat = (b.lat - a.lat) * t, dLng = (b.lng - a.lng) * t;
    var h = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(a.lat*t) * Math.cos(b.lat*t) * Math.sin(dLng/2) * Math.sin(dLng/2);
    return 2 * R * Math.asin(Math.sqrt(h));
  }
  function ride(c, km){
    var f = c.base, from = c.base_km;
    c.tiers.forEach(function(t){ var to = t[0] == null ? Infinity : t[0]; if (km > from) { f += t[1] * (Math.min(km, to) - from); } from = to; });
    return f;
  }
  // 1社ぶんの目安（夜間割増・往復を含む）
  // お店からの距離で迎車・回送を出す（3km超の単価が非公開の会社は高めに見る）
  function pickFee(c, base, at){
    if (!c.shop || !at) return base;
    var km = Math.ceil(kmBetween({lat:c.shop[0], lng:c.shop[1]}, at) * ROAD);
    return base + Math.max(0, km - (c.pick_free_km || 0)) * (c.pick_over || 0);
  }
  // from＝最初に乗る場所、to＝最後に降りる場所（迎車・回送の計算用）
  function fareOf(c, km, round, night, from, to){
    var pb = pickFee(c, c.pick, from) + pickFee(c, c.back, to);
    if (round && c.round_flat && km * 2 <= c.round_flat[0]) return c.round_flat[1] + pb; // 「往復10kmまで」は行きと帰りの合計で見る
    var r = ride(c, km);
    if (night && c.night > 1) r = Math.ceil(r * c.night / 10) * 10;
    return r * (round ? 2 : 1) + pb;
  }
  // 夜間・早朝の割増は会社ごとの時間帯で判定（night_hours = [何時から, 朝何時まで]）
  function isNightFor(c, hourId){
    var v = $(hourId).value, h = Number(v), nh = c.night_hours;
    return v !== "" && !!nh && c.night > 1 && (h >= nh[0] || h < nh[1]);
  }
  // ── 道のり（道路データで調べる。取れないときは直線×ROADで代わりに計算）──
  // 道路データの経路は高速道路も使う。高速の区間の長さを数えて、一般道だけで行くときは
  // その区間を1.15倍の道のり・1kmあたり1分長くかかるとみて出す（一般道のほうが高めに出る）
  var ROUTER = ROAD_API + "/route/v1/driving/", routeCache = {};
  var HW_NAME = /高速|自動車道|有料道路|首都高|アクアライン/;
  function routeOf(cs){
    var url = ROUTER + cs.map(function(c){ return c.lng.toFixed(5) + "," + c.lat.toFixed(5); }).join(";") + "?overview=full&geometries=geojson&steps=true";
    if (url in routeCache) return Promise.resolve(routeCache[url]);
    return fetch(url).then(function(r){ return r.json(); }).then(function(j){
      var rt = j && j.code === "Ok" && j.routes && j.routes[0];
      if (!rt) return routeCache[url] = null;
      var hw = 0;
      (rt.legs || []).forEach(function(leg){
        var prevHw = false;
        (leg.steps || []).forEach(function(st){
          var cls = ((st.intersections || [])[0] || {}).classes || [];
          var on = HW_NAME.test(st.name || "") || HW_NAME.test(st.ref || "") || cls.indexOf("motorway") >= 0 || (!st.name && prevHw && st.distance < 3000);
          if (on) hw += st.distance;
          prevHw = on;
        });
      });
      return routeCache[url] = {km: rt.distance / 1000, min: rt.duration / 60, hw: hw / 1000, line: rt.geometry.coordinates};
    }).catch(function(){ return routeCache[url] = null; }); // 失敗も覚えて、同じ道のりを何度も聞かない
  }
  function localOf(rt){ return rt && {km: rt.km + rt.hw * 0.15, min: rt.min + rt.hw * 1.0, line: rt.line}; }
  function straightKm(list){
    var d = 0;
    for (var i = 1; i < list.length; i++) d += kmBetween(list[i-1], list[i]) * ROAD;
    return d;
  }
  // 料金に使う距離。道のりは少しだけ長めに見て1km単位で切り上げ
  function kmOf(rt, list){ return Math.max(1, Math.ceil(rt ? rt.km * 1.05 : straightKm(list))); }

  // ── 地図（ルートを線で表示。地図の部品は使うときだけ読み込む）──
  var mapLib = null, mlLib = null, estMap = null;
  // 地図は、地名や店の名前を消し駅の名前だけ残した、見やすい色の地図（OpenFreeMap の Positron をもとに色を変える）。WebGL が使えないときは、淡色の地理院地図で出す
  var MAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
  function loadMapLib(){
    if (mapLib) return mapLib;
    var css = document.createElement("link"); css.rel = "stylesheet"; css.href = "/lib/leaflet.css"; document.head.appendChild(css);
    return mapLib = new Promise(function(ok, ng){
      var js = document.createElement("script"); js.src = "/lib/leaflet.js"; js.onload = function(){ ok(window.L); }; js.onerror = ng;
      document.head.appendChild(js);
    });
  }
  function loadML(){
    if (mlLib) return mlLib;
    var css = document.createElement("link"); css.rel = "stylesheet"; css.href = "/lib/maplibre-gl.css"; document.head.appendChild(css);
    return mlLib = new Promise(function(ok, ng){
      var js = document.createElement("script"); js.src = "/lib/maplibre-gl.js"; js.onload = function(){ window.maplibregl ? ok(window.maplibregl) : ng(); }; js.onerror = ng;
      document.head.appendChild(js);
    });
  }
  function canWebGL(){
    try { var c = document.createElement("canvas"); return !!(window.WebGLRenderingContext && (c.getContext("webgl") || c.getContext("experimental-webgl"))); } catch (e) { return false; }
  }
  function pinEl(i, n){
    var last = i === n - 1, d = document.createElement("div");
    d.className = "est-pin " + (i === 0 ? "" : last ? "to" : "via");
    d.innerHTML = "<b>" + (i === 0 ? "迎" : last ? "着" : "経") + "</b>";
    return d;
  }
  // 地図の色（グレーの地に白い道、緑の公園、青い川、点線の線路）
  function tintMap(map){
    var set = function(id, k, v){ if (map.getLayer(id)) map.setPaintProperty(id, k, v); };
    set("background", "background-color", "#eef0f2");
    set("landuse_residential", "fill-color", "#eceef1");
    set("park", "fill-color", "#cdebd3");
    set("landcover_wood", "fill-color", "#d3ecd6");
    set("water", "fill-color", "#a9d3f5");
    set("waterway", "line-color", "#a9d3f5");
    set("building", "fill-color", "#e1e4e8"); set("building", "fill-outline-color", "#d4d8dd");
    set("highway_minor", "line-color", "#ffffff"); set("highway_minor", "line-opacity", 1);
    set("highway_path", "line-color", "#f8f9fa");
    ["highway_major_casing", "highway_motorway_casing", "highway_motorway_bridge_casing", "tunnel_motorway_casing"].forEach(function(id){ set(id, "line-color", "#c4c9d0"); });
    ["highway_motorway_inner", "highway_motorway_bridge_inner"].forEach(function(id){ set(id, "line-color", "#fbd38a"); });
    set("highway_major_inner", "line-color", "#ffffff");
    ["railway", "railway_transit", "railway_service"].forEach(function(id){ set(id, "line-color", "#a3a9b1"); });
    if (map.getLayer("railway")) map.setLayerZoomRange("railway", 9, 24);
    if (map.getLayer("railway_dashline")) map.setLayerZoomRange("railway_dashline", 9, 24);
    if (map.getSource("openmaptiles")) map.addLayer({id: "station-name", type: "symbol", source: "openmaptiles", "source-layer": "poi", minzoom: 12,
      filter: ["all", ["==", ["get", "class"], "railway"], ["==", ["get", "subclass"], "station"]],
      layout: {"text-field": ["coalesce", ["get", "name:ja"], ["get", "name"]], "text-font": ["Noto Sans Regular"], "text-size": 12, "text-max-width": 8},
      paint: {"text-color": "#4b5563", "text-halo-color": "#ffffff", "text-halo-width": 1.5}});
  }
  function midOf(line){
    var tot = 0, seg = [];
    for (var i = 1; i < line.length; i++) { var d = Math.hypot(line[i][0] - line[i-1][0], line[i][1] - line[i-1][1]); seg.push(d); tot += d; }
    for (var j = 0, run = 0; j < seg.length; j++) {
      if (run + seg[j] >= tot / 2) { var t = seg[j] ? (tot / 2 - run) / seg[j] : 0, a = line[j], b = line[j + 1]; return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]; }
      run += seg[j];
    }
    return line[Math.floor(line.length / 2)];
  }
  function timeTag(min){
    var m = Math.max(5, Math.ceil(min / 5) * 5), d = document.createElement("div");
    d.className = "est-time";
    d.textContent = "🚗 " + (m >= 60 ? Math.floor(m / 60) + "時間" + (m % 60 ? m % 60 + "分" : "") : m + "分");
    return d;
  }
  function clearMap(){ if (estMap) { try { estMap.remove(); } catch (e) {} estMap = null; } }
  function drawMap(el, local, plain, stops){
    if (!canWebGL()) { drawLeaflet(el, local, plain, stops); return; }
    var line = local ? local.line : stops.map(function(c){ return [c.lng, c.lat]; });
    loadML().then(function(ml){
      if (!el.isConnected) return;
      clearMap();
      var lo = [Infinity, Infinity], hi = [-Infinity, -Infinity];
      line.concat(stops.map(function(c){ return [c.lng, c.lat]; })).forEach(function(p){
        lo = [Math.min(lo[0], p[0]), Math.min(lo[1], p[1])]; hi = [Math.max(hi[0], p[0]), Math.max(hi[1], p[1])];
      });
      var failed = false, map = estMap = new ml.Map({container: el, style: MAP_STYLE, bounds: [lo, hi],
        fitBoundsOptions: {padding: {top: 90, bottom: 30, left: 30, right: 30}, maxZoom: 16},
        attributionControl: {compact: true}, dragRotate: false, pitchWithRotate: false, touchPitch: false, cooperativeGestures: true,
        locale: {"CooperativeGesturesHandler.WindowsHelpText": "Ctrl キーを押しながらスクロールで拡大・縮小", "CooperativeGesturesHandler.MacHelpText": "⌘ キーを押しながらスクロールで拡大・縮小",
          "CooperativeGesturesHandler.MobileHelpText": "2本の指で地図を動かせます", "NavigationControl.ZoomIn": "拡大", "NavigationControl.ZoomOut": "縮小"}});
      map.touchZoomRotate.disableRotation();
      map.addControl(new ml.NavigationControl({showCompass: false}), "top-left");
      // 地図が読めないとき（地図の配信が止まっているなど）は、地理院地図に切り替える
      map.on("error", function(e){
        if (failed || map.isStyleLoaded()) return;
        failed = true; if (estMap === map) { clearMap(); drawLeaflet(el, local, plain, stops); }
      });
      map.on("load", function(){
        // 地名・道路名などの文字は消し、駅の名前だけ出す。道・線路・公園・川は見分けやすい色にする
        map.getStyle().layers.forEach(function(l){ if (l.type === "symbol") map.setLayoutProperty(l.id, "visibility", "none"); });
        tintMap(map);
        map.addSource("route", {type: "geojson", data: {type: "Feature", geometry: {type: "LineString", coordinates: line}}});
        map.addLayer({id: "route-casing", type: "line", source: "route", layout: {"line-cap": "round", "line-join": "round"}, paint: {"line-color": "#1559c4", "line-width": 9}});
        map.addLayer({id: "route", type: "line", source: "route", layout: {"line-cap": "round", "line-join": "round"}, paint: {"line-color": "#3b82f6", "line-width": 6}});
      });
      // ルートの線の上に、車での時間をふきだしで出す
      if (local) new ml.Marker({element: timeTag((plain || local).min), anchor: "bottom"}).setLngLat(midOf(line)).addTo(map);
      // 地図の部品が目印の要素を動かす（transform を上書きする）ので、外側の箱に入れて渡す
      stops.forEach(function(c, i){ var w = document.createElement("div"); w.appendChild(pinEl(i, stops.length)); new ml.Marker({element: w, anchor: "bottom", offset: [0, -4]}).setLngLat([c.lng, c.lat]).addTo(map); });
    }).catch(function(){ drawLeaflet(el, local, plain, stops); });
  }
  function drawLeaflet(el, local, plain, stops){
    loadMapLib().then(function(L){
      if (!el.isConnected) return;
      clearMap();
      estMap = L.map(el, {attributionControl: false, scrollWheelZoom: false, dragging: !L.Browser.mobile, tap: false});
      L.control.attribution({prefix: false}).addAttribution('<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル</a>／経路 &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>').addTo(estMap);
      L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png", {maxZoom: 18}).addTo(estMap);
      var ll = function(line){ return line.map(function(p){ return [p[1], p[0]]; }); };
      var group = [];
      if (local) {
        L.polyline(ll(local.line), {color: "#1559c4", weight: 9, opacity: .95}).addTo(estMap); // 白いふちで、地図の上でも線が見えやすいように
        group.push(L.polyline(ll(local.line), {color: "#3b82f6", weight: 6, opacity: 1}).addTo(estMap));
        var mid = midOf(local.line);
        L.marker([mid[1], mid[0]], {icon: L.divIcon({className: "", html: '<div style="position:absolute;transform:translate(-50%,-100%)">' + timeTag((plain || local).min).outerHTML + '</div>', iconSize: [0, 0]}), keyboard: false, interactive: false}).addTo(estMap);
      }
      stops.forEach(function(c, i){
        var icon = L.divIcon({className: "", html: pinEl(i, stops.length).outerHTML, iconSize: [30, 30], iconAnchor: [15, 30]});
        group.push(L.marker([c.lat, c.lng], {icon: icon, keyboard: false}).addTo(estMap));
      });
      estMap.fitBounds(L.featureGroup(group).getBounds(), {paddingTopLeft: [24, 84], paddingBottomRight: [24, 24]}); // 右上の距離の表示とピンが重ならないよう上をあける
    }).catch(function(){ el.remove(); });
  }

  function showEstimate(){
    routeDetails = null; clearPartners();
    if (partnerBlock() === "") showLoading(); // 道のりを調べるあいだも「探しています」を出す
    var seq = ++estSeq;
    lastKm = 0; lastKmHigh = 0; lastFare = ""; lastFareNum = 0; // 計算が終わるまでは前の目安を送らない
    var viaOn = form.querySelector("input[name=via_on]:checked").value === "あり";
    var trip = (form.querySelector("input[name=trip]:checked") || {}).value || "片道";
    var later = trip === "往復";
    var retOther = later && $("retOther").checked && $("retPickup").value.trim() && $("retDropoff").value.trim();
    var pts = [$("pickup").value].concat(viaOn ? [$("via").value] : [], [$("dropoff").value]);
    var rpts = retOther ? [$("retPickup").value, $("retDropoff").value] : [];
    if (!$("pickup").value.trim() || !$("dropoff").value.trim()) { est.hidden = true; lastKm = 0; lastKmHigh = 0; lastFare = ""; lastFareNum = 0; return; }
    Promise.all(pts.concat(rpts).map(function(q, i){ return geocode(q, i > 0); })).then(function(cs){
      if (seq !== estSeq) return;
      est.hidden = false;
      if (cs.some(function(c){ return !c; })) {
        lastKm = 0; lastKmHigh = 0; lastFare = ""; lastFareNum = 0;
        $("partnerResults").hidden = true; est.innerHTML = '<div class="t">ルートの地図</div><p>場所を確かめてください。見つからない場所があります。候補から選ぶか、「〇〇市〇〇1丁目」のように住所で入れると計算できます。<a href="#price">距離ごとの目安</a>もご覧ください。</p>';
        return;
      }
      var go = cs.slice(0, pts.length), back = retOther ? cs.slice(pts.length) : go.slice().reverse();
      est.innerHTML = '<div class="t">ルートの地図</div><p>道のりを調べています…</p>';
      // お迎えの都県は、選んだ欄よりお迎えの場所を優先する（依頼する会社は都県で決まるため）。食い違ったら欄を直して知らせる
      prefOf(cs[0]).then(function(pp){
        if (seq !== estSeq) return;
        if (pp === "out") {
          lastKm = 0; lastKmHigh = 0; lastFare = ""; lastFareNum = 0;
          $("partnerResults").hidden = true; est.innerHTML = '<div class="t">ルートの地図</div><p>場所を確かめてください。お迎えの場所が、対応エリアの外のようです。</p>';
          return;
        }
        if (pp && pp !== $("pref").value) {
          var was = $("pref").value;
          setSelect($("pref"), pp);
          var fx = $("prefFix");
          fx.textContent = "お迎えの場所が" + pp + "のようなので、お迎えの都道府県を" + (was ? "「" + was + "」から" : "") + "「" + pp + "」に直しました。違うときは、お迎えの場所をくわしく入れてください。";
          fx.hidden = false;
          estNow();
          return;
        }
        Promise.all([routeOf(go), routeOf(back)]).then(function(r2){
          var rs = [localOf(r2[0]), r2[0], localOf(r2[1]), r2[1]];
          if (seq !== estSeq) return;
          render(cs, go, back, rs);
        });
      });
    });
    function render(cs, go, back, rs){
      var a = go[0], b = go[go.length-1], ra = back[0], rb = back[back.length-1];
      var kmL = kmOf(rs[0],go), kmL2 = kmOf(rs[2],back);
      var kmH = kmOf(rs[1],go), kmH2 = kmOf(rs[3],back);
      if (Math.max(kmL,kmL2)>3000) { // 場所の取り違えだけを止める（前は250kmで、東京→広島のような長距離の依頼が候補ごと出なかった。2026-11-08 ペッタク）
        $("partnerResults").hidden = true; est.innerHTML = '<p>場所を確かめてください。距離がうまく計算できませんでした。</p>'; return;
      }
      var hasHigh = !!(rs[1] && rs[1].hw >= 1 || later && rs[3] && rs[3].hw >= 1);
      routeDetails = {km:kmL,backKm:kmL2,highKm:hasHigh?kmH:null,highBackKm:hasHigh?kmH2:null,
        from:{lat:a.lat,lng:a.lng},to:{lat:b.lat,lng:b.lng},backFrom:{lat:ra.lat,lng:ra.lng},backTo:{lat:rb.lat,lng:rb.lng},
        routeEstimated:!rs[0],localEstimated:hasHigh};
      lastKm = later ? kmL+kmL2 : kmL; lastKmHigh = hasHigh ? (later ? kmH+kmH2 : kmH) : 0;
      lastFare = ""; lastFareNum = 0;
      // 地図の右上に、行きの道のりと所要時間を出す（一般道。高速を使える道なら高速ありも）
      var mins = function(m){ m = Math.max(5, Math.ceil(m / 5) * 5); return m >= 60 ? Math.floor(m / 60) + "時間" + (m % 60 ? m % 60 + "分" : "") : m + "分"; };
      var km1 = function(k){ return (Math.round(k * 10) / 10).toFixed(1); };
      var info = rs[0] ? '<div><span>一般道</span><b>' + km1(rs[0].km) + 'km・' + mins(rs[0].min) + '</b></div>' +
          (rs[1] && rs[1].hw >= 1 ? '<div><span>高速あり</span><b>' + km1(rs[1].km) + 'km・' + mins(rs[1].min) + '</b></div>' : '')
        : '<div><span>道のり</span><b>' + kmL + 'km</b></div>';
      est.innerHTML = '<div class="est-wrap"><div class="est-map" id="estMap" role="img" aria-label="お迎え場所から行き先までの地図"></div>' +
        '<div class="est-info"><small>' + (later ? "行き" : "片道") + 'の目安</small>' + info + '</div></div>' +
        '<div class="est-legend"><span><i></i>お迎え</span>' + (go.length > 2 ? '<span><i class="via"></i>経由地</span>' : '') + '<span><i class="to"></i>行き先</span><span>時間は道の混み具合で変わります</span></div>';
      drawMap($("estMap"), rs[1], rs[0], go); // 線は実際の道のり、ふきだしの時間は右上の「一般道」とそろえる
      queuePartners();
    }
  }

  // 入力を変えたら、前の結果はすぐ消して、手が止まってから計算し直す（遅れて届いた前の結果は estSeq で捨てる）
  var estTimer = 0;
  function estSoon(){
    routeDetails = null; clearPartners();
    if (partnerBlock() === "") showLoading();
    clearTimeout(estTimer); estSeq++;
    lastKm = 0; lastKmHigh = 0; lastFare = ""; lastFareNum = 0;
    if (!est.hidden) est.innerHTML = '<p>入力に合わせて地図を更新しています…</p>';
    estTimer = setTimeout(showEstimate, 1000);
  }
  function estNow(){ clearTimeout(estTimer); showEstimate(); }
  $("pickup").addEventListener("input", function(){ $("prefFix").hidden = true; });
  $("pref").addEventListener("change", function(e){ if (e.isTrusted) $("prefFix").hidden = true; });
  ["pickup","via","dropoff","retPickup","retDropoff"].forEach(function(id){
    $(id).addEventListener("input", estSoon);
    $(id).addEventListener("change", estNow);
  });
  ["pref","date","hour","minute","retDate","retHour","retMinute","retOther"].forEach(function(id){ $(id).addEventListener("change", estNow); });
  form.querySelectorAll("input[name=trip],input[name=via_on]").forEach(function(r){ r.addEventListener("change", estNow); });

  // ── 前回の内容を入れる（日時以外）──
  var TEXT = ["pickup","via","dropoff","name","tel","email","notes","hand_from","hand_to"];
  function setRadio(name, v){
    var r = form.querySelector('input[name="' + name + '"][value="' + String(v || "").replace(/"/g, "") + '"]');
    if (r) r.checked = true;
  }
  function fill(o){
    setSelect($("pref"), o.pref);
    TEXT.forEach(function(k){ if (o[k] != null) $(k).value = String(o[k]); });
    setRadio("via_on", o.via ? "あり" : "なし"); syncVia();
    setRadio("trip", o.trip && o.trip !== "片道" ? "往復" : o.trip); // 以前の「往復（病院で待機）」も往復に
    // 再依頼リンク（受付の仕組み）からは return_pickup / return_dropoff で届く。行きの逆と同じなら「変える」にしない
    if (o.return_pickup || o.return_dropoff) {
      o.ret_other = (o.return_pickup || "") !== (o.dropoff || "") || (o.return_dropoff || "") !== (o.pickup || "");
      o.ret_pickup = o.return_pickup; o.ret_dropoff = o.return_dropoff;
    }
    $("retOther").checked = !!o.ret_other; $("retPickup").value = o.ret_pickup || ""; $("retDropoff").value = o.ret_dropoff || "";
    syncTrip();
    setSelect($("riders"), o.riders);
    $("petOnly").checked = /^0/.test(o.riders || ""); $("handFrom").value = o.hand_from || ""; $("handTo").value = o.hand_to || ""; syncOnly();
    setSelect($("luggage"), o.luggage);
    var pets = o.pets || o.pets_json || [];
    if (typeof pets === "string") { try { pets = JSON.parse(pets); } catch (e) { pets = []; } }
    if (!Array.isArray(pets)) pets = [];
    var n = pets.length || Number(o.pet_count) || 0;
    if (n) { countSel.value = String(Math.min(n, MAX_PETS)); setPetCount(countSel.value); }
    showEstimate();
    petsBox.querySelectorAll(".pet").forEach(function(c, i){
      var p = pets[i]; if (!p) return;
      var k = c.dataset.key;
      ["breed","weight","age"].forEach(function(f){ if (p[f] != null) $(k + "_" + f).value = p[f]; });
      var old = {"持っている":"持ち込む","持っていない":"借りたい"};
      if (old[p.cage]) p.cage = old[p.cage];
      if (p.species && !/^(犬|猫|その他)$/.test(p.species)) { $(k + "_kind").value = p.species; p = Object.assign({}, p, {species:"その他"}); }
      ["species","sex","cage","care"].forEach(function(f){ setRadio(k + "_" + f, p[f]); });
      c.querySelector("input[name$=_vac]").checked = p.vaccine === "済";
      c.querySelector("input[name$=_rabies]").checked = p.rabies === "済";
      c.querySelectorAll("input[name$=_care_need]").forEach(function(x){ x.checked = (p.care_need || []).indexOf(x.value) >= 0; });
      if (p.care_note != null) $(k + "_care_note").value = p.care_note;
      syncPetCard(c);
    });
  }
  function collect(){
    var fd = new FormData(form), o = { pets: readPets(), pet_count: countSel.value };
    ["pref","trip","riders","luggage"].forEach(function(k){ o[k] = String(fd.get(k) || ""); });
    TEXT.forEach(function(k){ o[k] = String(fd.get(k) || "").trim(); });
    if (form.querySelector("input[name=via_on]:checked").value !== "あり") o.via = "";
    o.ret_other = o.trip === "往復" && $("retOther").checked;
    o.ret_pickup = o.ret_other ? $("retPickup").value.trim() : "";
    o.ret_dropoff = o.ret_other ? $("retDropoff").value.trim() : "";
    return o;
  }
  function showRestore(msg){
    $("restoreMsg").textContent = msg;
    $("restore").style.display = "block";
  }
  $("restoreClear").addEventListener("click", function(){
    form.reset(); setPetCount(countSel.value); syncVia(); syncTrip();
    $("restore").style.display = "none";
  });
  // お詫びメールの「日時だけ変えてもう一度」リンク（?r=受付番号&k=署名）
  var rid = qs.get("r"), rk = qs.get("k");
  if (rid && rk && GAS_URL) {
    fetch(GAS_URL + "?a=prefill&id=" + encodeURIComponent(rid) + "&k=" + encodeURIComponent(rk))
      .then(function(res){ return res.json(); })
      .then(function(o){
        if (!o || !o.ok) throw 0;
        fill(o);
        showRestore("前回のご依頼（受付番号 " + rid + "）の内容を入れておきました。日時を選び直して送ってください。");
        $("date").focus({preventScroll:true});
      })
      .catch(function(){});
  }
  // ── 緊急タブ：tools/emergency.json から gen_areas.py が書き込む（ここは手で直さない）。電話番号は出さず、各社・各病院の公式サイトへのリンクだけ ──
  /*EMG*/var EMG = {"checked": "2026年10月31日", "taxis": [{"id": "E01", "name": "動物救急車", "prefs": ["東京都", "神奈川県"], "area": "東京・大田区（田園調布）から30kmほど。東京・神奈川が中心", "note": "平日・休日・夜間も搬送。予約制", "url": "https://j-119.com/", "review_query": "動物救急車 大田区", "review_name": "動物救急車"}, {"id": "E02", "name": "ペットドクターカー", "prefs": ["東京都", "埼玉県", "神奈川県"], "area": "東京23区と周辺の市、埼玉南部、川崎北部", "note": "夜間に獣医師が車で来て、車の中で診察・処置をするサービス（電話受付 20時〜翌3時）", "url": "https://petdoctorcar.net/", "tel": [["", "080-7288-8283"]], "review_query": "ペットドクターカー", "review_name": "ペットドクターカー"}, {"id": "E03", "name": "三和交通 ペットタクシー", "prefs": ["神奈川県", "東京都", "埼玉県"], "area": "横浜市北部、東京の多摩地域の一部、埼玉の和光・朝霞・志木・新座・富士見など", "note": "急な体調不良の「ペット119番」に対応", "url": "https://www.sanwakoutsu.co.jp/special/pet/"}, {"id": "E04", "name": "ペットタクシー Animals", "prefs": ["神奈川県"], "area": "横浜市港南区の会社。神奈川が中心", "note": "深夜の救急搬送に対応（営業時間外は相談）", "url": "https://h12150825.wixsite.com/taxi-animals", "tel": [["受付 8時〜20時（時間外は相談）", "0120-792-046"]], "review_query": "ペットタクシー Animals 横浜市港南区", "review_name": "Animals"}, {"id": "E05", "name": "コインペットタクシー シエロ", "prefs": ["千葉県", "東京都", "埼玉県"], "area": "千葉の松戸・市川・流山・柏、東京の葛飾・江戸川・足立など、埼玉の八潮・三郷", "note": "緊急・救急に対応（夜間・深夜・早朝は別料金）", "url": "https://pettaxi.jp/", "tel": [["", "080-8097-7181"]], "review_query": "コインペットタクシー シエロ", "review_name": "シエロ"}, {"id": "E06", "name": "ペットタクシー パールのしっぽ", "prefs": ["千葉県"], "area": "千葉市が中心", "note": "営業時間外でも緊急のときは相談可。早朝・深夜の緊急搬送に対応", "url": "https://pearlno-shippo.com/", "tel": [["", "070-2382-1122"]], "review_query": "ペットタクシー パールのしっぽ 千葉市", "review_name": "パールのしっぽ"}, {"id": "E07", "name": "COCOタク さいたま南店", "prefs": ["埼玉県", "東京都"], "area": "さいたま市が中心。埼玉南部と東京の一部", "note": "24時間・年中無休。夜間の送迎にも対応", "url": "https://cocotaxi-saitama.com/", "tel": [["", "070-9173-4611"]], "review_query": "ペットタクシー COCOタク さいたま南店", "review_name": ["COCO", "さいたま"]}, {"id": "E08", "name": "COCOタク 埼玉川越店", "prefs": ["埼玉県"], "area": "川越市が中心。所沢・入間・狭山・飯能・熊谷など", "note": "急な体調不良や夜間の緊急に対応（20時〜朝8時はLINEで受付）", "url": "https://pet-taxi-saitama-kawagoe.jp/", "tel": [["20時〜朝8時は公式LINEで受付", "070-8599-1424"]], "review_query": "ペットタクシー COCOタク 埼玉川越店", "review_name": ["COCO", "川越"]}, {"id": "E09", "name": "COCOタク 埼玉春日部", "prefs": ["埼玉県", "千葉県"], "area": "春日部市が中心。越谷・久喜など、千葉の野田・柏・流山", "note": "救急病院への送迎に24時間対応（できる限り）", "url": "https://pet-taxi-kasukabe.com/", "tel": [["", "080-4132-5022"]], "review_query": "ペットタクシー COCOタク 埼玉春日部", "review_name": ["COCO", "春日部"]}, {"id": "E10", "name": "ペットレスキュー", "prefs": ["大阪府", "京都府", "兵庫県", "奈良県", "滋賀県"], "area": "大阪・京都・兵庫・奈良・滋賀が中心", "note": "ペット専門の夜間救急搬送（20時〜翌5時・年中無休）", "url": "https://yakan-pet-rescue.com/", "tel": [["", "080-1101-7385"]], "review_query": "ペットレスキュー 夜間救急搬送", "review_name": "ペットレスキュー"}, {"id": "E11", "name": "名鉄タクシー 夜間救急搬送サービス", "prefs": ["愛知県"], "area": "名古屋市と近郊・尾張地区", "note": "名古屋夜間動物救急センターへの搬送（21時〜翌2時）。先にセンターへ電話して受け入れを確認してから頼む仕組み", "url": "https://prtimes.jp/main/html/rd/p/000000450.000089084.html", "tel": [["名古屋エリアの配車センター", "0570-085255"], ["尾張地区の配車センター", "0586-73-5166"]]}, {"id": "E12", "name": "ペット専用タクシー aiai", "prefs": ["北海道"], "area": "札幌市白石区の会社。札幌と北海道全域", "note": "24時間・年中無休。体調が悪くてすぐ病院へ行きたいときも相談できる（21時〜翌9時は割増）", "url": "https://pet-taxi-aiai.com/", "tel": [["", "080-4509-0999"]], "review_query": "ペット専用タクシー aiai 札幌市白石区", "review_name": "aiai"}, {"id": "E13", "name": "ペットタクシー COCOタク仙台東店", "prefs": ["宮城県"], "area": "仙台・名取・利府・多賀城・塩竈・富谷など宮城県", "note": "24時間・365日予約を受け付け。急な体調不良で病院へ行くときも相談できる（深夜・早朝は割増）", "url": "https://cocotaxi-sendai-higashi.com/", "tel": [["", "0120-176-636"], ["", "070-5059-1122"]], "review_query": "ペットタクシー COCOタク 仙台東店", "review_name": ["COCO", "仙台東"]}, {"id": "E14", "name": "ペットタクシー COCOタク長岡", "prefs": ["新潟県"], "area": "長岡を中心に見附・三条・燕・小千谷・魚沼・新潟市など新潟県全域", "note": "24時間・365日予約制。すぐ病院へ連れて行きたいときも相談できる（21時〜5時は割増）", "url": "https://pet-taxi-niigata-nagaoka.com/", "tel": [["", "080-7116-3909"]], "review_query": "ペットタクシー COCOタク長岡", "review_name": ["COCO", "長岡"]}, {"id": "E15", "name": "ZEROペットタクシー", "prefs": ["滋賀県"], "area": "栗東市の会社。栗東・守山・草津など滋賀県", "note": "電話受付24時間。夜間の緊急の動物病院への移動に対応", "url": "https://zero808.co.jp/pettaxi/", "tel": [["", "077-599-1182"]], "review_query": "ZEROペットタクシー 栗東市", "review_name": "ZERO"}, {"id": "E16", "name": "ペットタクシー Comasuke（コマスケ）", "prefs": ["大阪府", "京都府"], "area": "茨木・高槻・豊中・吹田・大阪市・堺など大阪府と、京都市・宇治・亀岡など京都府", "note": "夜間の救急送迎に対応（電話は24時間。夜間は折り返しのことあり。21時〜7時は割増）", "url": "https://comasuke.com/", "tel": [["", "050-8893-1378"]], "review_query": "ペットタクシー Comasuke 茨木", "review_name": "Comasuke"}, {"id": "E18", "name": "ペットタクシー マイファミリー", "prefs": ["大阪府"], "area": "高槻市の会社。北大阪（吹田・摂津・茨木・高槻）が中心", "note": "24時間・年中無休。緊急時にも対応", "url": "https://my-family-takatsuki.com/", "tel": [["", "080-7311-1288"]], "review_query": "ペットタクシー マイファミリー 高槻市", "review_name": "マイファミリー"}, {"id": "E19", "name": "ペットサポートてんりん", "prefs": ["京都府"], "area": "京都市東山区の会社。京都市（京都駅・七条から10km以内はお迎え無料）と近畿", "note": "夜間の急病にも、車が空いていれば対応（電話受付は9時〜21時と案内。21時〜翌9時は25%増し）", "url": "https://ten-rin.jp/service/taxi/", "tel": [["", "080-4296-4932"]], "review_query": "ペットサポートてんりん 京都市東山区", "review_name": "てんりん"}, {"id": "E20", "name": "ペットタクシー COCOタク ならまち店", "prefs": ["奈良県", "和歌山県", "大阪府", "京都府", "兵庫県", "滋賀県"], "area": "奈良市の会社。奈良・大阪・兵庫・京都・滋賀・和歌山など近畿", "note": "24時間・365日予約制。すぐ病院へ連れて行きたいときも相談できる（21時〜5時は割増）", "url": "https://pet-taxi-nara.com/", "tel": [["", "0120-51-6987"]], "review_query": "ペットタクシー COCOタク ならまち店", "review_name": ["COCO", "ならまち"]}, {"id": "E21", "name": "ペッタク（PETTAXI）", "prefs": ["広島県"], "area": "広島市安芸区の会社。広島周辺から全国へ・全国から広島周辺への長距離も", "note": "通院・夜間・緊急時にも対応", "url": "https://pettaku.com/", "tel": [["", "090-3373-5559"]], "review_query": "ペッタク ペットタクシー 広島市安芸区", "review_name": "ペッタク"}, {"id": "E22", "name": "福岡わんわんエクスプレス", "prefs": ["福岡県", "佐賀県"], "area": "福岡市中央区の会社。福岡県と、佐賀・熊本・山口など100kmほどまで", "note": "緊急のときはできる限り対応。電話はドライバー直通で、夜間・運転中は出られないことあり", "url": "https://wanwan.pet/", "tel": [["", "090-9074-1123"]], "review_query": "福岡わんわんエクスプレス", "review_name": "わんわんエクスプレス"}, {"id": "E23", "name": "福岡ペットタクシー HAKAタク", "prefs": ["福岡県"], "area": "福岡市博多区の会社。福岡市内と大野城・春日・志免など", "note": "急な体調不良は24時間365日対応（LINEは24時間受付）", "url": "https://pettaxi-hakataku.wepage.com/", "tel": [["電話は平日9時〜19時", "090-3876-1122"]], "review_query": "福岡ペットタクシー HAKAタク", "review_name": "HAKA"}, {"id": "E24", "name": "ペットタクシー COCOタク福岡空港店", "prefs": ["福岡県"], "area": "糟屋郡篠栗町の会社。福岡県全域", "note": "24時間体制で、突然の連絡にも対応（21時〜5時は割増）", "url": "https://pet-taxi-fukuoka-airport.com/", "tel": [["", "0120-675-950"]], "review_query": "ペットタクシー COCOタク 福岡空港店", "review_name": ["COCO", "福岡空港"]}, {"id": "E25", "name": "東京ペット救急車（なごみ）", "prefs": ["東京都", "千葉県"], "area": "東京23区と、千葉の市川・本八幡", "note": "24時間対応。夜間の動物病院へのペットの救急搬送", "url": "https://www.nagomipro.net/", "tel": [["", "090-3687-0331"]], "review_query": "東京ペット救急車 なごみ", "review_name": "ペット救急車"}, {"id": "E26", "name": "ペットタクシー シアンシャ 厚木店", "prefs": ["神奈川県"], "area": "厚木・伊勢原・海老名・愛甲郡", "note": "24時間365日。緊急時や早朝・深夜の送迎にも対応", "url": "https://chienchat.jp/atsugi/", "tel": [["", "070-1394-1380"]], "review_query": "ペットタクシー シアンシャ 厚木", "review_name": ["シアンシャ", "厚木"]}, {"id": "E27", "name": "ペットタクシー シアンシャ 鎌倉店", "prefs": ["神奈川県"], "area": "鎌倉・逗子・葉山が中心（藤沢・茅ヶ崎なども）", "note": "24時間365日。緊急時や早朝・深夜の送迎にも対応", "url": "https://chienchat.jp/kamakura/", "tel": [["", "090-3895-2719"]], "review_query": "ペットタクシー シアンシャ 鎌倉", "review_name": ["シアンシャ", "鎌倉"]}, {"id": "E28", "name": "ペトタクファインド", "prefs": ["千葉県"], "area": "千葉県全域（県外の長距離は相談）", "note": "365日。夜間・早朝の緊急通院のプランあり（21時〜7時は夜間料金）", "url": "https://pettaxi-find.com/chiba/", "tel": [["", "050-5574-5210"]], "review_query": "ペトタクファインド", "review_name": "ペトタクファインド"}], "hospitals": {"北海道": [{"name": "札幌夜間動物病院", "city": "札幌市西区", "hours": "平日19時〜翌6時（日・祝は14時から）", "url": "https://www.sapporo1299.net/", "ll": [43.07408, 141.30598], "id": "H001", "review_query": "札幌夜間動物病院 札幌市西区", "review_name": "札幌夜間動物病院", "addr": "北海道札幌市西区二十四軒4条5丁目9-3 北海道獣医師会館1F", "spec": "夜間専門の病院。救命救急・集中治療に対応"}, {"name": "アネス動物病院 札幌円山動物麻酔センター", "city": "札幌市中央区", "hours": "月〜金 20時〜翌2時", "url": "https://anes-amc.com/medical-night/", "ll": [43.05288, 141.3279], "id": "H002", "review_query": "アネス動物病院 札幌円山動物麻酔センター 札幌市中央区", "review_name": ["アネス動物病院", "札幌円山動物麻酔センター"], "addr": "北海道札幌市中央区南4条西20丁目1-18", "spec": "犬猫の動物麻酔センターが行う夜間診療"}, {"name": "ペテモどうぶつ医療センター 札幌月寒", "city": "札幌市豊平区", "hours": "救急受付 21時〜24時・5時〜9時", "url": "https://mc.aeonpet.com/sapporotsukisamu/er/", "ll": [43.03135, 141.38007], "ll_city": true, "id": "H003", "review_query": "ペテモどうぶつ医療センター 札幌月寒 札幌市豊平区", "review_name": ["ペテモどうぶつ医療センター", "札幌月寒"], "addr": "北海道札幌市豊平区月寒東3条11丁目1-22 BRANCH札幌月寒内", "spec": "動物医療センターの夜間救急外来"}, {"name": "北海道大学動物医療センター（夜間休日診療）", "city": "札幌市北区", "hours": "平日17時〜24時", "url": "https://www.vetmed.hokudai.ac.jp/VMTH/owner/nightandweekendandholidayservice/", "ll": [43.08241, 141.33611], "id": "H004", "review_query": "北海道大学動物医療センター 札幌市北区", "review_name": "北海道大学動物医療センター", "addr": "北海道札幌市北区北19条西10丁目", "spec": "大学の動物医療センターの夜間休日診療（犬・猫のみ）"}, {"name": "江別白樺通りアニマルクリニック 夜間救急外来", "city": "江別市", "hours": "20時〜23時（火〜木は休み）", "url": "https://ebetsu.lifemate-vh.com/night/", "ll": [43.09671, 141.51425], "id": "H005", "review_query": "江別白樺通りアニマルクリニック 江別市", "review_name": "江別白樺通りアニマルクリニック", "addr": "北海道江別市野幌屯田町37-28", "spec": "一般診療の病院の夜間救急外来（犬・猫）"}], "青森県": [{"name": "協同組合 仙台獣医師会 夜間救急動物病院", "city": "仙台市宮城野区（宮城県）", "hours": "21時〜翌5時", "url": "https://www.svet.jp/yakan/", "ll": [38.26736, 140.91367], "id": "H006", "review_query": "仙台獣医師会 夜間救急動物病院 仙台市宮城野区", "review_name": ["仙台獣医師会", "夜間救急動物病院"], "addr": "宮城県仙台市宮城野区苦竹1丁目2-51", "spec": "仙台獣医師会の夜間救急病院（犬・猫。小鳥不可）"}], "岩手県": [{"name": "協同組合 仙台獣医師会 夜間救急動物病院", "city": "仙台市宮城野区（宮城県）", "hours": "21時〜翌5時", "url": "https://www.svet.jp/yakan/", "ll": [38.26736, 140.91367], "id": "H006", "review_query": "仙台獣医師会 夜間救急動物病院 仙台市宮城野区", "review_name": ["仙台獣医師会", "夜間救急動物病院"], "addr": "宮城県仙台市宮城野区苦竹1丁目2-51", "spec": "仙台獣医師会の夜間救急病院（犬・猫。小鳥不可）"}], "宮城県": [{"name": "協同組合 仙台獣医師会 夜間救急動物病院", "city": "仙台市宮城野区", "hours": "21時〜翌5時", "url": "https://www.svet.jp/yakan/", "ll": [38.26736, 140.91367], "id": "H006", "review_query": "仙台獣医師会 夜間救急動物病院 仙台市宮城野区", "review_name": ["仙台獣医師会", "夜間救急動物病院"], "addr": "宮城県仙台市宮城野区苦竹1丁目2-51", "spec": "仙台獣医師会の夜間救急病院（犬・猫。小鳥不可）"}, {"name": "長町南動物病院 夜間救急", "city": "仙台市太白区", "hours": "19時〜23時（当分の間、かかりつけの方だけ）", "url": "https://www.nagamachiminami-ah.com/", "ll": [38.22312, 140.87697], "id": "H007", "review_query": "長町南動物病院 仙台市太白区", "review_name": "長町南動物病院", "addr": "宮城県仙台市太白区長町南3丁目8-28", "spec": "一般診療の病院。夜間救急はかかりつけの方に限る"}], "秋田県": [{"name": "協同組合 仙台獣医師会 夜間救急動物病院", "city": "仙台市宮城野区（宮城県）", "hours": "21時〜翌5時", "url": "https://www.svet.jp/yakan/", "ll": [38.26736, 140.91367], "id": "H006", "review_query": "仙台獣医師会 夜間救急動物病院 仙台市宮城野区", "review_name": ["仙台獣医師会", "夜間救急動物病院"], "addr": "宮城県仙台市宮城野区苦竹1丁目2-51", "spec": "仙台獣医師会の夜間救急病院（犬・猫。小鳥不可）"}], "山形県": [{"name": "協同組合 仙台獣医師会 夜間救急動物病院", "city": "仙台市宮城野区（宮城県）", "hours": "21時〜翌5時", "url": "https://www.svet.jp/yakan/", "ll": [38.26736, 140.91367], "id": "H006", "review_query": "仙台獣医師会 夜間救急動物病院 仙台市宮城野区", "review_name": ["仙台獣医師会", "夜間救急動物病院"], "addr": "宮城県仙台市宮城野区苦竹1丁目2-51", "spec": "仙台獣医師会の夜間救急病院（犬・猫。小鳥不可）"}, {"name": "動物夜間急患センター新潟", "city": "新潟市中央区（新潟県）", "hours": "21時〜翌1時", "url": "https://anecniigata.com/", "ll": [37.91086, 139.06779], "id": "H008", "review_query": "動物夜間急患センター新潟 新潟市中央区", "review_name": "動物夜間急患センター新潟", "addr": "新潟県新潟市中央区笹口2-13-4 国際ペットワールド専門学校 1階", "spec": "市内の動物病院が協力して運営する夜間専門の病院"}], "福島県": [{"name": "ふくしま夜間救急動物病院", "city": "郡山市", "hours": "平日21時〜24時（土日は休み）", "url": "http://www2.tbb.t-com.ne.jp/fukushimaneah/", "ll": [37.40642, 140.33827], "id": "H009", "review_query": "ふくしま夜間救急動物病院 郡山市", "review_name": "ふくしま夜間救急動物病院", "addr": "福島県郡山市大槻町菅田53-3", "spec": "夜間救急の病院（犬・猫以外は電話で確認）"}, {"name": "協同組合 仙台獣医師会 夜間救急動物病院", "city": "仙台市宮城野区（宮城県）", "hours": "21時〜翌5時", "url": "https://www.svet.jp/yakan/", "ll": [38.26736, 140.91367], "id": "H006", "review_query": "仙台獣医師会 夜間救急動物病院 仙台市宮城野区", "review_name": ["仙台獣医師会", "夜間救急動物病院"], "addr": "宮城県仙台市宮城野区苦竹1丁目2-51", "spec": "仙台獣医師会の夜間救急病院（犬・猫。小鳥不可）"}], "茨城県": [{"name": "つくば夜間動物病院", "city": "つくば市", "hours": "20時〜翌2時30分", "url": "https://tsukubayakan.com/", "ll": [36.01747, 140.0643], "id": "H010", "review_query": "つくば夜間動物病院 つくば市", "review_name": "つくば夜間動物病院", "addr": "茨城県つくば市みどりの東6-5-102", "spec": "夜間の救急を年中無休で診る病院（犬・猫のみ）"}, {"name": "水戸夜間動物救急センター", "city": "水戸市", "hours": "20時〜翌2時30分（休診日あり）", "url": "https://tsukubayakan.com/access/mito/", "ll": [36.34537, 140.45821], "id": "H011", "review_query": "水戸夜間動物救急センター 水戸市", "review_name": "水戸夜間動物救急センター", "addr": "茨城県水戸市笠原町103-18", "spec": "夜間専門の救急センター（犬・猫）"}, {"name": "つくば動物高度医療センター", "city": "つくば市", "hours": "24時間（日中は紹介制）", "url": "https://tsukuba-aach.com/", "ll": [36.08361, 140.07638], "ll_city": true, "id": "H012", "review_query": "つくば動物高度医療センター つくば市", "review_name": "つくば動物高度医療センター", "addr": "茨城県つくば市市之台116-1", "spec": "24時間の高度医療センター。夜間・休診日は救急対応"}], "栃木県": [{"name": "宇都宮夜間どうぶつ病院", "city": "宇都宮市", "hours": "21時〜翌2時（水・木曜は休み）", "url": "https://www.utsunomiya-er-ah.com/", "ll": [36.56889, 139.88873], "id": "H013", "review_query": "宇都宮夜間どうぶつ病院 宇都宮市", "review_name": "宇都宮夜間どうぶつ病院", "addr": "栃木県宇都宮市大曽1丁目6-17", "spec": "夜間救急専門の病院（うさぎは内容により相談）"}, {"name": "宇都宮白沢動物病院 夜間診療", "city": "宇都宮市", "hours": "20時30分〜翌0時30分（予約制）", "url": "https://utsunomiya-ah.com/night/", "ll": [36.62519, 139.93155], "id": "H014", "review_query": "宇都宮白沢動物病院 宇都宮市", "review_name": "宇都宮白沢動物病院", "addr": "栃木県宇都宮市白沢町594-38", "spec": "日中も診療する病院の夜間診療（エキゾチックは電話相談）"}, {"name": "しもつけVETセンター 夜間救急科", "city": "下野市", "hours": "20時〜翌7時", "url": "https://www.tochigi-svc.com/", "ll": [36.37463, 139.84604], "id": "H015", "review_query": "しもつけVETセンター 下野市", "review_name": "しもつけVETセンター", "addr": "栃木県下野市駅東5丁目2-1", "spec": "一般・専門診療の病院の夜間救急科"}, {"name": "小山夜間救急 あかりの森どうぶつ病院", "city": "小山市", "hours": "受付 20時〜翌4時", "url": "https://vets-tree.co.jp/night/", "ll": [36.3003, 139.78601], "id": "H016", "review_query": "小山夜間救急 あかりの森どうぶつ病院 小山市", "review_name": ["小山夜間救急", "あかりの森どうぶつ病院"], "addr": "栃木県小山市外城168番地4", "spec": "年中無休の夜間診療を行う病院（犬・猫）"}], "群馬県": [{"name": "群馬夜間救急動物病院", "city": "前橋市", "hours": "21時〜24時", "url": "https://gunma-neah.com/", "ll": [36.3865, 139.03256], "id": "H017", "review_query": "群馬夜間救急動物病院 前橋市", "review_name": "群馬夜間救急動物病院", "addr": "群馬県前橋市元総社町107-2（群馬動物専門学校敷地内）", "spec": "獣医師会員有志が運営する夜間救急病院（犬・猫のみ）"}, {"name": "伊勢崎動物医療センター 夜間救急診療", "city": "伊勢崎市", "hours": "23時〜翌5時", "url": "https://i-ac.jp/night-emergency/", "ll": [36.31086, 139.16269], "id": "H018", "review_query": "伊勢崎動物医療センター 伊勢崎市", "review_name": "伊勢崎動物医療センター", "addr": "群馬県伊勢崎市田中町889-8", "spec": "専門医による二次診療病院の夜間救急診療"}, {"name": "さいとう動物病院 富岡総合医療センター", "city": "富岡市", "hours": "夜間救急", "url": "https://saitovet.com/medical/emergency/", "ll": [36.26236, 138.90161], "id": "H019", "review_query": "さいとう動物病院 富岡総合医療センター 富岡市", "review_name": ["さいとう動物病院", "富岡総合医療センター"], "addr": "群馬県富岡市富岡3058-1", "spec": "CT・MRI対応の総合医療センターの夜間救急"}], "埼玉県": [{"name": "夜間救急動物病院 さいたま大宮 SONAC", "city": "さいたま市大宮区", "hours": "電話受付 20時〜翌0時30分", "url": "https://www.sonac.co.jp/", "ll": [35.90629, 139.61769], "id": "H020", "review_query": "夜間救急動物病院 さいたま大宮 SONAC さいたま市大宮区", "review_name": ["夜間救急動物病院", "さいたま大宮", "SONAC"], "addr": "埼玉県さいたま市大宮区桜木町2-289-2 大宮国際動物専門学校1階", "spec": "獣医師会会員有志が設立した夜間の救急病院"}, {"name": "どうぶつの総合病院 専門医療＆救急センター", "city": "川口市", "hours": "救急 9時〜翌1時", "url": "https://vsec.jp/mp/yakan_1", "ll": [35.86374, 139.7343], "id": "H021", "review_query": "どうぶつの総合病院 専門医療＆救急センター 川口市", "review_name": ["どうぶつの総合病院", "専門医療＆救急センター"], "addr": "埼玉県川口市石神815", "spec": "専門医療・救急センターの救急・夜間診療（犬・猫）"}, {"name": "ミライノ動物病院 夜間救急", "city": "草加市", "hours": "19時〜翌1時30分（犬・猫）", "url": "https://milainoanimal.jp/yakan/", "ll": [35.81498, 139.7881], "id": "H022", "review_query": "ミライノ動物病院 草加市", "review_name": "ミライノ動物病院", "addr": "埼玉県草加市谷塚上町575-6", "spec": "犬・猫中心の一般診療の病院の夜間救急診療"}, {"name": "日本小動物医療センター 夜間救急", "city": "所沢市", "hours": "夜間救急（2026年11月6日から、金曜の夜は外来を休み）", "url": "https://jsamc.jp/services/yakan.html", "ll": [35.79282, 139.51305], "id": "H023", "review_query": "日本小動物医療センター 所沢市", "review_name": "日本小動物医療センター", "addr": "埼玉県所沢市東所沢和田1丁目10番4号", "spec": "夜間救急診療と二次診療のみを行う医療センター"}, {"name": "久喜夜間救急どうぶつ病院", "city": "久喜市", "hours": "19時30分〜翌2時", "url": "https://kuki-er-ah.com/", "ll": [36.06616, 139.68288], "id": "H024", "review_query": "久喜夜間救急どうぶつ病院 久喜市", "review_name": "久喜夜間救急どうぶつ病院", "addr": "埼玉県久喜市久喜東2丁目11-11", "spec": "夜間救急専門の病院（犬・猫。うさぎは内容により相談）"}, {"name": "熊谷夜間救急動物病院", "city": "熊谷市", "hours": "19時〜翌5時（犬・猫）", "url": "https://www.kumagaya-er.com/", "ll": [36.15354, 139.41466], "id": "H025", "review_query": "熊谷夜間救急動物病院 熊谷市", "review_name": "熊谷夜間救急動物病院", "addr": "埼玉県熊谷市上之3988-7", "spec": "夜間救急の病院。翌日はかかりつけ医へ引き継ぐ"}], "千葉県": [{"name": "ペテモどうぶつ医療センター幕張新都心", "city": "千葉市美浜区", "hours": "20時〜翌8時", "url": "https://mc.aeonpet.com/makuharishin/", "ll": [35.65609, 140.02652], "id": "H026", "review_query": "ペテモどうぶつ医療センター幕張新都心 千葉市美浜区", "review_name": "ペテモどうぶつ医療センター幕張新都心", "addr": "千葉県千葉市美浜区豊砂1-8 イオンモール幕張新都心1F", "spec": "動物医療センター。夜間救急・夜間診療に対応"}, {"name": "JPB動物医療センター千葉", "city": "千葉市緑区", "hours": "夜間救急", "url": "https://jpbvet.com/", "ll": [35.54283, 140.18152], "id": "H027", "review_query": "JPB動物医療センター千葉 千葉市緑区", "review_name": "JPB動物医療センター千葉", "addr": "千葉県千葉市緑区誉田町1-789-3", "spec": "一般診療の動物医療センター。夜間救急も行う"}, {"name": "京葉夜間どうぶつ病院", "city": "八千代市", "hours": "20時〜翌2時30分", "url": "https://kettlevet.com/", "ll": [35.72271, 140.07999], "id": "H028", "review_query": "京葉夜間どうぶつ病院 八千代市", "review_name": "京葉夜間どうぶつ病院", "addr": "千葉県八千代市大和田新田103-34", "spec": "夜間専門の救急病院（犬・猫）"}, {"name": "柏流山夜間どうぶつ病院", "city": "柏市", "hours": "20時30分〜翌1時（日・月曜は休み）", "url": "https://kn-yakan.com/", "ll": [35.89881, 139.91882], "id": "H029", "review_query": "柏流山夜間どうぶつ病院 柏市", "review_name": "柏流山夜間どうぶつ病院", "addr": "千葉県柏市西原2丁目6-35", "spec": "夜間の動物病院（犬・猫・ウサギ）"}, {"name": "とうかつ夜間どうぶつ病院", "city": "柏市", "hours": "夜間救急", "url": "https://www.tokatu4699.com/", "ll": [35.86751, 139.97594], "id": "H030", "review_query": "とうかつ夜間どうぶつ病院 柏市", "review_name": "とうかつ夜間どうぶつ病院", "addr": "千葉県柏市北柏1-10-14", "spec": "東葛獣医師会が運営する夜間病院（犬・猫専用）"}, {"name": "千葉どうぶつ総合病院", "city": "流山市", "hours": "救急 24時間", "url": "https://www.chiba-ah.com/clinical-services/emergency-services/", "ll": [35.83779, 139.90875], "id": "H031", "review_query": "千葉どうぶつ総合病院 流山市", "review_name": "千葉どうぶつ総合病院", "addr": "千葉県流山市南流山1-21-8", "spec": "24時間の救急診療体制をもつ総合病院"}, {"name": "千葉動物医療センター", "city": "袖ケ浦市", "hours": "24時間", "url": "https://99chiba.com/", "ll": [35.4204, 139.9592], "id": "H032", "review_query": "千葉動物医療センター 袖ケ浦市", "review_name": "千葉動物医療センター", "addr": "千葉県袖ケ浦市神納1150番地", "spec": "祝日も24時間診療の医療センター。夜間救急に対応"}], "東京都": [{"name": "港区動物救急医療センター 芝アニマルクリニック", "city": "港区", "hours": "24時間", "url": "https://shiba-animalclinic.com/", "ll": [35.65661, 139.75111], "id": "H033", "review_query": "港区動物救急医療センター 芝アニマルクリニック 港区", "review_name": ["港区動物救急医療センター", "芝アニマルクリニック"], "addr": "東京都港区芝公園2-2-11 グランデイ芝公園 1階", "spec": "24時間の救急医療センター（魚類・昆虫以外）"}, {"name": "ライフメイト動物医療センター文京", "city": "文京区", "hours": "24時間受付", "url": "https://er-animal.jp/er_bunkyo/", "ll": [35.72126, 139.7533], "id": "H034", "review_query": "ライフメイト動物医療センター文京 文京区", "review_name": "ライフメイト動物医療センター文京", "addr": "東京都文京区白山1-37-11 白山カトウビル1", "spec": "高度医療を行う救急・二次診療病院。24時間受付"}, {"name": "夜間救急動物病院 目黒", "city": "目黒区", "hours": "20時〜翌5時", "url": "https://www.yakan-99.com/", "ll": [35.62181, 139.6828], "id": "H035", "review_query": "夜間救急動物病院 目黒 目黒区", "review_name": ["夜間救急動物病院", "目黒"], "addr": "東京都目黒区碑文谷4丁目15-15 フジビル", "spec": "夜間救急の動物病院"}, {"name": "TRVA動物医療センター", "city": "世田谷区", "hours": "20時〜翌6時", "url": "https://trva.jp/emergency/", "ll": [35.62598, 139.64288], "id": "H036", "review_query": "TRVA動物医療センター 世田谷区", "review_name": "TRVA動物医療センター", "addr": "東京都世田谷区深沢8-19-12 泉美ビル2F", "spec": "動物医療センターの年中無休の夜間救急（犬・猫）"}, {"name": "杉並動物夜間救急医療センター", "city": "杉並区", "hours": "電話受付 20時〜翌2時", "url": "https://ah.aeonpet.com/tokyo-yakan-emergency/", "ll": [35.70003, 139.59439], "id": "H037", "review_query": "杉並動物夜間救急医療センター 杉並区", "review_name": "杉並動物夜間救急医療センター", "addr": "東京都杉並区松庵2-19-15", "spec": "夜間救急の医療センター（犬・猫。超大型犬は不可）"}, {"name": "ライフメイト動物救急センター練馬", "city": "練馬区", "hours": "24時間受付", "url": "https://er-animal.jp/er_nerima/", "ll": [35.73892, 139.58713], "id": "H038", "review_query": "ライフメイト動物救急センター練馬 練馬区", "review_name": "ライフメイト動物救急センター練馬", "addr": "東京都練馬区石神井台6-1-7", "spec": "高度医療を行う救急・二次診療病院"}, {"name": "ペテモどうぶつ医療センター ひがし東京", "city": "江東区", "hours": "19時〜翌7時", "url": "https://mc.aeonpet.com/higashi-tokyo/", "ll": [35.69505, 139.83098], "id": "H039", "review_query": "ペテモどうぶつ医療センター ひがし東京 江東区", "review_name": ["ペテモ", "ひがし東京"], "addr": "東京都江東区亀戸6-38-11 ノビールメンテ・ウエダビル1階", "spec": "年中無休の夜間診療を行う動物医療センター"}, {"name": "武蔵野動物・救急救命センター", "city": "武蔵野市", "hours": "20時〜翌9時（予約制）", "url": "http://center99.intellectual-japan.com/index.html", "ll": [35.71778, 139.56612], "ll_city": true, "id": "H040", "review_query": "武蔵野動物・救急救命センター 武蔵野市", "review_name": "武蔵野動物・救急救命センター", "addr": "東京都武蔵野市中町2-6-4", "spec": "三鷹獣医科グループ併設の24時間看護の救急救命センター"}, {"name": "ライフメイト動物医療センター府中", "city": "府中市", "hours": "24時間受付", "url": "https://er-animal.jp/er_fuchu/", "ll": [35.67334, 139.48625], "id": "H041", "review_query": "ライフメイト動物医療センター府中 府中市", "review_name": "ライフメイト動物医療センター府中", "addr": "東京都府中市緑町1-17-1 S・R・K 1F", "spec": "高度医療を行う救急・二次診療病院。24時間受付"}, {"name": "サムズアップアニマルケアセンター", "city": "立川市", "hours": "夜間 19時30分〜翌9時", "url": "https://samsupvets.jp/", "ll": [35.71389, 139.40778], "id": "H042", "review_query": "サムズアップアニマルケアセンター 立川市", "review_name": "サムズアップアニマルケアセンター", "addr": "東京都立川市泉町935番27 COMMONS TACHIKAWA TACHIHI", "spec": "24時間体制の病院。夜間救急に対応（犬・猫）"}, {"name": "ライフメイト動物救命救急センター八王子", "city": "八王子市", "hours": "24時間受付", "url": "https://er-animal.jp/er_hachioji/", "ll": [35.61138, 139.37566], "id": "H043", "review_query": "ライフメイト動物救命救急センター八王子 八王子市", "review_name": "ライフメイト動物救命救急センター八王子", "addr": "東京都八王子市南大沢4-7-2 ヤマザキ動物看護大学内", "spec": "高度医療と救命救急を行う救急・二次診療病院"}], "神奈川県": [{"name": "DVMsどうぶつ医療センター横浜", "city": "横浜市神奈川区", "hours": "20時〜翌3時", "url": "https://yokohama-dvms.com/", "ll": [35.47106, 139.61861], "id": "H044", "review_query": "DVMsどうぶつ医療センター横浜 横浜市神奈川区", "review_name": "DVMsどうぶつ医療センター横浜", "addr": "神奈川県横浜市神奈川区沢渡2-2 第二泉ビル2F", "spec": "救急と二次診療のセンターをもつ動物病院"}, {"name": "横浜動物救急診療センター VECCS横浜", "city": "横浜市南区", "hours": "24時間", "url": "https://veccs-yokohama.jp/", "ll": [35.44007, 139.62268], "id": "H045", "review_query": "横浜動物救急診療センター VECCS横浜 横浜市南区", "review_name": ["横浜動物救急診療センター", "VECCS横浜"], "addr": "神奈川県横浜市南区前里町1丁目25番地 2階", "spec": "24時間年中無休の救急診療センター（犬・猫中心）"}, {"name": "アニマルメディカルセンター", "city": "川崎市中原区", "hours": "24時間", "url": "https://amc-japan.com/", "ll": [35.57629, 139.65578], "id": "H046", "review_query": "アニマルメディカルセンター 川崎市中原区", "review_name": "アニマルメディカルセンター", "addr": "神奈川県川崎市中原区新丸子東2-890-10", "spec": "24時間365日の救急・一般・二次診療（犬猫ほか小動物）"}, {"name": "川崎市獣医師会 夜間動物病院", "city": "川崎市高津区", "hours": "21時〜24時（診療日が限られています）", "url": "https://kvma9950.com/", "ll": [35.61205, 139.61171], "id": "H047", "review_query": "川崎市獣医師会 夜間動物病院 川崎市高津区", "review_name": ["川崎市獣医師会", "夜間動物病院"], "addr": "神奈川県川崎市高津区久地2-5-8 日本動物高度医療センター内", "spec": "川崎市獣医師会が運営する夜間動物病院"}, {"name": "ペテモどうぶつ医療センター相模原", "city": "相模原市南区", "hours": "21時〜翌8時", "url": "https://mc.aeonpet.com/sagamihara/", "ll": [35.55427, 139.41968], "id": "H048", "review_query": "ペテモどうぶつ医療センター相模原 相模原市南区", "review_name": "ペテモどうぶつ医療センター相模原", "addr": "神奈川県相模原市南区古淵3-11-3", "spec": "夜間診療・緊急医療を行う動物医療センター"}, {"name": "藤沢夜間救急動物病院", "city": "藤沢市", "hours": "19時〜翌8時30分", "url": "https://www.fujisawa-vet-er.com/", "ll": [35.36426, 139.4536], "id": "H049", "review_query": "藤沢夜間救急動物病院 藤沢市", "review_name": "藤沢夜間救急動物病院", "addr": "神奈川県藤沢市大庭5425-9", "spec": "年中無休の夜間救急病院（犬・猫・小動物）"}, {"name": "横須賀夜間救急動物病院", "city": "横須賀市", "hours": "21時〜翌5時（犬・猫）", "url": "https://yokosukayakan.jimdofree.com/", "ll": [35.25454, 139.68549], "id": "H050", "review_query": "横須賀夜間救急動物病院 横須賀市", "review_name": "横須賀夜間救急動物病院", "addr": "神奈川県横須賀市根岸町5丁目16-1", "spec": "年中無休で夜間専門の救急病院（犬・猫専門）"}, {"name": "夜間救急動物医療センター NEAMeC", "city": "平塚市", "hours": "21時〜翌6時", "url": "https://www.neamec.com/", "ll": [35.33522, 139.34958], "ll_city": true, "id": "H051", "review_query": "夜間救急動物医療センター NEAMeC 平塚市", "review_name": ["夜間救急動物医療センター", "NEAMeC"], "addr": "神奈川県平塚市片岡21-1", "spec": "神奈川県獣医師会会員による共同の夜間救急病院"}], "新潟県": [{"name": "動物夜間急患センター新潟", "city": "新潟市中央区", "hours": "21時〜翌1時", "url": "https://anecniigata.com/", "ll": [37.91086, 139.06779], "id": "H008", "review_query": "動物夜間急患センター新潟 新潟市中央区", "review_name": "動物夜間急患センター新潟", "addr": "新潟県新潟市中央区笹口2-13-4 国際ペットワールド専門学校 1階", "spec": "市内の動物病院が協力して運営する夜間専門の病院"}], "富山県": [{"name": "富山県獣医師会 夜間診療（当番制）", "city": "富山県内（日替わりの当番病院）", "hours": "平日 受付20時〜22時", "url": "https://www.toyamavet.or.jp/vet_09.html", "id": "H052", "spec": "獣医師会の当番制夜間診療。応急的な診療（主に犬・猫）"}, {"name": "北陸よつや動物医療センター", "city": "高岡市", "hours": "時間外 20時〜23時など", "url": "https://yotsuya-ah.jp/medical", "ll": [36.76192, 137.00169], "id": "H053", "review_query": "北陸よつや動物医療センター 高岡市", "review_name": "北陸よつや動物医療センター", "addr": "富山県高岡市四屋260", "spec": "一般・専門診療の病院。夜間救急は電話で相談（犬猫ほか）"}, {"name": "チェルシーアニマルクリニック 夜間診療", "city": "富山市", "hours": "19時〜21時（月・水・木・金）", "url": "https://chelsea-animal.com/emergency/", "ll": [36.71078, 137.24854], "id": "H054", "review_query": "チェルシーアニマルクリニック 富山市", "review_name": "チェルシーアニマルクリニック", "addr": "富山県富山市上飯野25", "spec": "一般診療の病院の夜間診療（犬・猫のみ）"}], "石川県": [{"name": "かなざわ夜間救急動物病院", "city": "金沢市", "hours": "21時〜翌2時（不定休）", "url": "https://kanazawa-yakan.com/", "ll": [36.54578, 136.64198], "id": "H055", "review_query": "かなざわ夜間救急動物病院 金沢市", "review_name": "かなざわ夜間救急動物病院", "addr": "石川県金沢市泉3丁目1-12", "spec": "夜間の急な体調不良に対応する救急専門の病院"}], "福井県": [{"name": "かなざわ夜間救急動物病院", "city": "金沢市（石川県）", "hours": "21時〜翌2時（不定休）", "url": "https://kanazawa-yakan.com/", "ll": [36.54578, 136.64198], "id": "H055", "review_query": "かなざわ夜間救急動物病院 金沢市", "review_name": "かなざわ夜間救急動物病院", "addr": "石川県金沢市泉3丁目1-12", "spec": "夜間の急な体調不良に対応する救急専門の病院"}, {"name": "京都夜間動物救急センター", "city": "京都市南区（京都府）", "hours": "21時30分〜翌2時", "url": "https://kyoto99.net/", "ll": [34.97076, 135.75053], "id": "H056", "review_query": "京都夜間動物救急センター 京都市南区", "review_name": "京都夜間動物救急センター", "addr": "京都府京都市南区上鳥羽仏現寺町11番地 京都動物愛護センター内", "spec": "京都市獣医師会が運営する夜間救急センター"}], "山梨県": [{"name": "ノア動物病院 城東センター病院", "city": "甲府市", "hours": "23時まで緊急対応", "url": "https://noah-vet.co.jp/flow", "ll": [35.65986, 138.57889], "id": "H057", "review_query": "ノア動物病院 城東センター病院 甲府市", "review_name": ["ノア動物病院", "城東センター病院"], "addr": "山梨県甲府市城東3-4-15", "spec": "動物病院グループのセンター病院。夜間救急に対応"}, {"name": "きらら動物病院 千塚分院", "city": "甲府市", "hours": "22時まで夜間対応", "url": "https://www.kirara-vet-chizuka.com/", "ll": [35.68272, 138.53888], "id": "H058", "review_query": "きらら動物病院 千塚分院 甲府市", "review_name": ["きらら動物病院", "千塚分院"], "addr": "山梨県甲府市千塚3-1-11", "spec": "一般診療の病院。夜10時まで時間外対応（小型犬・猫）"}], "長野県": [{"name": "長野夜間どうぶつ病院", "city": "千曲市", "hours": "19時30分〜翌0時30分（平日）", "url": "https://naganoyakan-ah.com/", "ll": [36.53395, 138.10092], "id": "H059", "review_query": "長野夜間どうぶつ病院 千曲市", "review_name": "長野夜間どうぶつ病院", "addr": "長野県千曲市稲荷山214-6（稲荷山どうぶつ病院内）", "spec": "夜間専門の病院（犬・猫・うさぎ・フェレット）"}, {"name": "佐久・軽井沢夜間どうぶつ病院", "city": "佐久市", "hours": "21時〜24時（月〜金）", "url": "https://sakukaruizawa-yakan.com/", "ll": [36.27703, 138.46593], "id": "H060", "review_query": "佐久・軽井沢夜間どうぶつ病院 佐久市", "review_name": "佐久・軽井沢夜間どうぶつ病院", "addr": "長野県佐久市佐久平駅東21-2 佐久平プレイスビル 1F-A", "spec": "夜間の緊急に対応する動物病院"}, {"name": "こやま動物病院 夜間救急診療", "city": "長野市", "hours": "19時〜23時（日・火・祝は休み）", "url": "https://koyama-ah.jp/annai/", "ll": [36.56809, 138.20052], "id": "H061", "review_query": "こやま動物病院 長野市", "review_name": "こやま動物病院", "addr": "長野県長野市松代町松代716-9", "spec": "一般診療の病院の夜間診療（犬猫ほか小動物）"}], "岐阜県": [{"name": "岐阜県獣医師会 夜間救急動物病院", "city": "岐阜市", "hours": "21時〜翌1時", "url": "https://www.gifuyakan.jp/", "ll": [35.38555, 136.76309], "id": "H062", "review_query": "岐阜県獣医師会 夜間救急動物病院 岐阜市", "review_name": ["岐阜県獣医師会", "夜間救急動物病院"], "addr": "岐阜県岐阜市西川手6丁目41番地", "spec": "岐阜県獣医師会の夜間救急病院（犬・猫）"}], "静岡県": [{"name": "静岡市夜間救急動物病院", "city": "静岡市駿河区", "hours": "21時〜翌1時", "url": "https://shizuoka-neah.com/", "ll": [34.95179, 138.41538], "id": "H063", "review_query": "静岡市夜間救急動物病院 静岡市駿河区", "review_name": "静岡市夜間救急動物病院", "addr": "静岡県静岡市駿河区宮竹2丁目1-1", "spec": "静岡市獣医師会の会員が設立した夜間救急病院"}, {"name": "浜松夜間救急動物病院", "city": "浜松市中央区", "hours": "夜間救急", "url": "http://hamamatsu-aer.jp/", "ll": [34.69917, 137.72301], "id": "H064", "review_query": "浜松夜間救急動物病院 浜松市中央区", "review_name": "浜松夜間救急動物病院", "addr": "静岡県浜松市中央区東伊場2-1-9", "spec": "夜間専門の救急病院（犬・猫。他は電話で確認）"}, {"name": "VCJ動物医療センター駿河病院", "city": "御殿場市", "hours": "24時間", "url": "https://vcj-sulga.com/", "ll": [35.30869, 138.9346], "id": "H065", "review_query": "VCJ動物医療センター駿河病院 御殿場市", "review_name": "VCJ動物医療センター駿河病院", "addr": "静岡県御殿場市東田中1078-1", "spec": "24時間体制・完全看護の病院。救急診療に対応"}], "愛知県": [{"name": "名古屋夜間動物救急センター", "city": "名古屋市中区", "hours": "21時〜翌2時", "url": "https://nagoyavet.jp/hospital_yakan.php", "ll": [35.16861, 136.91028], "ll_city": true, "id": "H066", "review_query": "名古屋夜間動物救急センター 名古屋市中区", "review_name": "名古屋夜間動物救急センター", "spec": "名古屋市獣医師会が運営する夜間救急センター"}, {"name": "名古屋西動物夜間救急医療センター", "city": "名古屋市西区", "hours": "受付 21時〜23時", "url": "https://ah.aeonpet.com/nagoya-yakan-emergency/", "ll": [35.2261, 136.8864], "id": "H067", "review_query": "名古屋西動物夜間救急医療センター 名古屋市西区", "review_name": "名古屋西動物夜間救急医療センター", "addr": "愛知県名古屋市西区玉池町3", "spec": "夜間救急の医療センター（犬・猫のみ。超大型犬は不可）"}, {"name": "もりやま犬と猫の病院", "city": "名古屋市守山区", "hours": "24時間", "url": "https://moriyama1299.com/night/", "ll": [35.24085, 137.00902], "id": "H068", "review_query": "もりやま犬と猫の病院 名古屋市守山区", "review_name": "もりやま犬と猫の病院", "addr": "愛知県名古屋市守山区深沢2-101", "spec": "24時間救急に対応する犬と猫の病院"}, {"name": "こざわ犬猫病院 夜間緊急診療", "city": "名古屋市千種区", "hours": "20時〜翌9時", "url": "https://www.anicare.net/", "ll": [35.17179, 136.93924], "id": "H069", "review_query": "こざわ犬猫病院 名古屋市千種区", "review_name": "こざわ犬猫病院", "addr": "愛知県名古屋市千種区内山2丁目14-14", "spec": "年中無休で夜間救急に対応する犬猫病院"}, {"name": "あいち犬猫医療センター", "city": "安城市", "hours": "夜間 20時〜翌8時", "url": "https://www.sugiuravet.com/ems/", "ll": [34.97687, 137.08435], "id": "H070", "review_query": "あいち犬猫医療センター 安城市", "review_name": "あいち犬猫医療センター", "addr": "愛知県安城市今池町3丁目5-10", "spec": "年中無休・24時間診療の犬と猫の病院"}, {"name": "ハート動物クリニック 犬猫医療センター", "city": "豊橋市", "hours": "20時30分〜24時", "url": "https://heart-ac.com/service/", "ll": [34.75699, 137.39282], "id": "H071", "review_query": "ハート動物クリニック 犬猫医療センター 豊橋市", "review_name": ["ハート動物クリニック", "犬猫医療センター"], "addr": "愛知県豊橋市前田南町1丁目7-13", "spec": "一般診療の犬猫医療センター。緊急は電話で受付"}], "三重県": [{"name": "名古屋夜間動物救急センター", "city": "名古屋市中区（愛知県）", "hours": "21時〜翌2時", "url": "https://nagoyavet.jp/hospital_yakan.php", "ll": [35.16861, 136.91028], "ll_city": true, "id": "H066", "review_query": "名古屋夜間動物救急センター 名古屋市中区", "review_name": "名古屋夜間動物救急センター", "spec": "名古屋市獣医師会が運営する夜間救急センター"}, {"name": "大阪どうぶつ夜間急病センター", "city": "大阪市東成区（大阪府）", "hours": "21時〜翌5時", "url": "https://doubutsuyakan.jp/", "ll": [34.67583, 135.53412], "id": "H072", "review_query": "大阪どうぶつ夜間急病センター 大阪市東成区", "review_name": "大阪どうぶつ夜間急病センター", "addr": "大阪府大阪市東成区中道3丁目8-15", "spec": "大阪市獣医師会有志が作った夜間救急病院"}], "滋賀県": [{"name": "長浜どうぶつ病院", "city": "長浜市", "hours": "夜間の急患は22時ごろまでできる限り（先に電話。木・日・祝は通院中の患者だけ21時まで）", "url": "https://nagahama-ah.com/", "ll": [35.3812, 136.2696], "ll_city": true, "addr": "滋賀県長浜市祇園町23-1", "spec": "犬・猫の一般の動物病院。夜間の急患にもできる限り対応", "id": "H073", "review_query": "長浜どうぶつ病院 長浜市", "review_name": "長浜どうぶつ病院"}, {"name": "京都夜間動物救急センター", "city": "京都市南区（京都府）", "hours": "21時30分〜翌2時", "url": "https://kyoto99.net/", "ll": [34.97076, 135.75053], "id": "H056", "review_query": "京都夜間動物救急センター 京都市南区", "review_name": "京都夜間動物救急センター", "addr": "京都府京都市南区上鳥羽仏現寺町11番地 京都動物愛護センター内", "spec": "京都市獣医師会が運営する夜間救急センター"}, {"name": "大阪・北摂夜間救急どうぶつ病院", "city": "箕面市（大阪府）", "hours": "21時〜翌6時", "url": "https://heah.jp/", "ll": [34.82455, 135.49243], "id": "H074", "review_query": "大阪・北摂夜間救急どうぶつ病院 箕面市", "review_name": "大阪・北摂夜間救急どうぶつ病院", "addr": "大阪府箕面市船場東2-3-55", "spec": "年中無休の夜間救急病院（犬・猫）。CT・MRI完備"}], "京都府": [{"name": "京都夜間動物救急センター", "city": "京都市南区", "hours": "21時30分〜翌2時", "url": "https://kyoto99.net/", "ll": [34.97076, 135.75053], "id": "H056", "review_query": "京都夜間動物救急センター 京都市南区", "review_name": "京都夜間動物救急センター", "addr": "京都府京都市南区上鳥羽仏現寺町11番地 京都動物愛護センター内", "spec": "京都市獣医師会が運営する夜間救急センター"}, {"name": "京都夜間どうぶつ診療所", "city": "久世郡久御山町", "hours": "20時〜24時", "url": "http://nac-kyoto.com/", "ll": [34.87467, 135.74927], "id": "H075", "review_query": "京都夜間どうぶつ診療所 久世郡久御山町", "review_name": "京都夜間どうぶつ診療所", "addr": "京都府久世郡久御山町佐山西ノ口10-1 日本ファミリービル 1F", "spec": "夜間専門の動物診療所（犬・猫以外は問い合わせ）"}, {"name": "右京動物病院 夜間救急", "city": "京都市右京区", "hours": "平日19時〜22時", "url": "https://www.ukyo-ah.com/service/night/", "ll": [35.01709, 135.70956], "id": "H076", "review_query": "右京動物病院 京都市右京区", "review_name": "右京動物病院", "addr": "京都府京都市右京区太秦京ノ道町12-2", "spec": "一般診療の病院の夜間救急外来（本院のみ）"}], "大阪府": [{"name": "大阪どうぶつ夜間急病センター", "city": "大阪市東成区", "hours": "21時〜翌5時", "url": "https://doubutsuyakan.jp/", "ll": [34.67583, 135.53412], "id": "H072", "review_query": "大阪どうぶつ夜間急病センター 大阪市東成区", "review_name": "大阪どうぶつ夜間急病センター", "addr": "大阪府大阪市東成区中道3丁目8-15", "spec": "大阪市獣医師会有志が作った夜間救急病院"}, {"name": "大阪夜間ペットクリニック", "city": "大阪市東成区", "hours": "20時〜翌3時", "url": "https://osaka-pet911.com/", "ll": [34.67, 135.54111], "ll_city": true, "id": "H077", "review_query": "大阪夜間ペットクリニック 大阪市東成区", "review_name": "大阪夜間ペットクリニック", "addr": "大阪府大阪市東成区大今里南6-2-6", "spec": "夜間救急の動物病院（犬・猫）"}, {"name": "大阪・北摂夜間救急どうぶつ病院", "city": "箕面市", "hours": "21時〜翌6時", "url": "https://heah.jp/", "ll": [34.82455, 135.49243], "id": "H074", "review_query": "大阪・北摂夜間救急どうぶつ病院 箕面市", "review_name": "大阪・北摂夜間救急どうぶつ病院", "addr": "大阪府箕面市船場東2-3-55", "spec": "年中無休の夜間救急病院（犬・猫）。CT・MRI完備"}, {"name": "堺動物夜間救急クリニック", "city": "堺市中区", "hours": "21時〜翌2時（木曜は休み）", "url": "https://ah.aeonpet.com/sakai-yakan-emergency/", "ll": [34.54332, 135.51131], "id": "H078", "review_query": "堺動物夜間救急クリニック 堺市中区", "review_name": "堺動物夜間救急クリニック", "addr": "大阪府堺市中区学園町2-6", "spec": "夜間救急のクリニック（超大型犬は不可）"}, {"name": "大阪守口夜間どうぶつ診療所", "city": "守口市", "hours": "19時〜24時（水・日・祝は休み）", "url": "https://osaka-moriguchi-yakan-ah.jp/", "ll": [34.73583, 135.56168], "ll_city": true, "id": "H079", "review_query": "大阪守口夜間どうぶつ診療所 守口市", "review_name": "大阪守口夜間どうぶつ診療所", "addr": "大阪府守口市浜町二丁目1-21 フィル・パーク守口市浜町 1階", "spec": "夜間診療専門の病院（犬・猫。他の小動物は相談）"}, {"name": "りんくう動物救急医療協会（大阪公立大学 獣医臨床センター 夜間診療科）", "city": "泉佐野市", "hours": "21時〜翌4時30分（土曜は休み）", "url": "https://www.raema.or.jp/", "ll": [34.41449, 135.2954], "id": "H080", "review_query": "りんくう動物救急医療協会 泉佐野市", "review_name": "りんくう動物救急医療協会", "addr": "大阪府泉佐野市りんくう往来北1番地の58 大阪公立大学獣医学部附属獣医臨床センター", "spec": "大学の獣医臨床センターの夜間診療科（犬・猫が基本）"}, {"name": "BARK夜間救急往診動物病院（獣医師が家に来る往診）", "city": "大阪市など", "hours": "20時〜翌5時", "url": "https://barkdoctors.co.jp/", "id": "H081", "spec": "獣医師が自宅に来る往診専門の夜間病院（大阪・兵庫）"}], "兵庫県": [{"name": "神戸夜間動物救急センター", "city": "神戸市西区", "hours": "21時〜翌9時", "url": "https://www.kobe-naec.com/", "ll": [34.67864, 134.9928], "id": "H082", "review_query": "神戸夜間動物救急センター 神戸市西区", "review_name": "神戸夜間動物救急センター", "addr": "兵庫県神戸市西区玉津町今津364-24", "spec": "年中無休で夜間救急専門の病院（犬・猫）"}, {"name": "兵庫ペット医療センター 尼崎本院", "city": "尼崎市", "hours": "19時〜23時", "url": "https://www.hyogopet.com/info/night.html", "ll": [34.73333, 135.40639], "ll_city": true, "id": "H083", "review_query": "兵庫ペット医療センター 尼崎本院 尼崎市", "review_name": ["兵庫ペット医療センター", "尼崎本院"], "addr": "兵庫県尼崎市立花町3丁目1-5", "spec": "CT・MRIのある医療センターの夜間診療（犬・猫）"}, {"name": "大蔵海岸ペットクリニック", "city": "明石市", "hours": "21時〜23時（予約制）", "url": "https://okurakaigan-vet.com/", "ll": [34.64624, 135.00661], "id": "H084", "review_query": "大蔵海岸ペットクリニック 明石市", "review_name": "大蔵海岸ペットクリニック", "addr": "兵庫県明石市大蔵町24-24", "spec": "夜間診察を設け、救急・集中治療に力を入れる病院"}, {"name": "エルザ動物医療センター 夜間救急診療", "city": "姫路市", "hours": "21時〜23時", "url": "https://www.elsa-hp.com/medicalcare/nighttime/", "ll": [34.84174, 134.65063], "id": "H085", "review_query": "エルザ動物医療センター 姫路市", "review_name": "エルザ動物医療センター", "addr": "兵庫県姫路市下手野1-110-1", "spec": "エルザ動物病院グループの夜間救急診療"}, {"name": "BARK夜間救急往診動物病院（獣医師が家に来る往診）", "city": "神戸市など", "hours": "20時〜翌5時", "url": "https://barkdoctors.co.jp/", "id": "H081", "spec": "獣医師が自宅に来る往診専門の夜間病院（大阪・兵庫）"}], "奈良県": [{"name": "奈良動物医療センター", "city": "奈良市", "hours": "24時間（夜間・早朝 19時〜翌9時）", "url": "https://nara-amc.com/medical/emergency/", "ll": [34.70695, 135.75035], "id": "H086", "review_query": "奈良動物医療センター 奈良市", "review_name": "奈良動物医療センター", "addr": "奈良県奈良市鶴舞東町2-6", "spec": "24時間体制で救急に対応する動物医療センター"}], "和歌山県": [{"name": "りんくう動物救急医療協会（大阪公立大学 獣医臨床センター 夜間診療科）", "city": "泉佐野市（大阪府）", "hours": "21時〜翌4時30分（土曜は休み）", "url": "https://www.raema.or.jp/", "ll": [34.41449, 135.2954], "id": "H080", "review_query": "りんくう動物救急医療協会 泉佐野市", "review_name": "りんくう動物救急医療協会", "addr": "大阪府泉佐野市りんくう往来北1番地の58 大阪公立大学獣医学部附属獣医臨床センター", "spec": "大学の獣医臨床センターの夜間診療科（犬・猫が基本）"}, {"name": "大阪どうぶつ夜間急病センター", "city": "大阪市東成区（大阪府）", "hours": "21時〜翌5時", "url": "https://doubutsuyakan.jp/", "ll": [34.67583, 135.53412], "id": "H072", "review_query": "大阪どうぶつ夜間急病センター 大阪市東成区", "review_name": "大阪どうぶつ夜間急病センター", "addr": "大阪府大阪市東成区中道3丁目8-15", "spec": "大阪市獣医師会有志が作った夜間救急病院"}], "鳥取県": [{"name": "岡山夜間どうぶつ救急病院", "city": "岡山市南区（岡山県）", "hours": "21時〜翌5時", "url": "https://okayama-yakan.jp/", "ll": [34.59974, 133.91957], "ll_city": true, "id": "H088", "review_query": "岡山夜間どうぶつ救急病院 岡山市南区", "review_name": "岡山夜間どうぶつ救急病院", "addr": "岡山県岡山市南区福浜町1-27（永原動物病院内）", "spec": "中国・四国地方の動物を診る夜間救急病院"}], "島根県": [{"name": "広島夜間救急動物病院", "city": "広島市東区（広島県）", "hours": "21時〜翌1時", "url": "https://hiroshimayakan.com/", "ll": [34.40394, 132.50493], "id": "H089", "review_query": "広島夜間救急動物病院 広島市東区", "review_name": "広島夜間救急動物病院", "addr": "広島県広島市東区温品2-8-40 大崎ビル", "spec": "広島県獣医師会賛同会員が運営する夜間救急病院"}, {"name": "岡山夜間どうぶつ救急病院", "city": "岡山市南区（岡山県）", "hours": "21時〜翌5時", "url": "https://okayama-yakan.jp/", "ll": [34.59974, 133.91957], "ll_city": true, "id": "H088", "review_query": "岡山夜間どうぶつ救急病院 岡山市南区", "review_name": "岡山夜間どうぶつ救急病院", "addr": "岡山県岡山市南区福浜町1-27（永原動物病院内）", "spec": "中国・四国地方の動物を診る夜間救急病院"}], "岡山県": [{"name": "岡山夜間どうぶつ救急病院", "city": "岡山市南区", "hours": "21時〜翌5時", "url": "https://okayama-yakan.jp/", "ll": [34.59974, 133.91957], "ll_city": true, "id": "H088", "review_query": "岡山夜間どうぶつ救急病院 岡山市南区", "review_name": "岡山夜間どうぶつ救急病院", "addr": "岡山県岡山市南区福浜町1-27（永原動物病院内）", "spec": "中国・四国地方の動物を診る夜間救急病院"}, {"name": "倉敷夜間ペットクリニック", "city": "倉敷市", "hours": "21時〜24時", "url": "http://www.stemvets.com/file/YORUtantou.html", "ll": [34.58929, 133.74179], "id": "H090", "review_query": "倉敷夜間ペットクリニック 倉敷市", "review_name": "倉敷夜間ペットクリニック", "spec": "日中も診療する病院の夜間救急（エキゾチックは要確認）"}], "広島県": [{"name": "広島夜間救急動物病院", "city": "広島市東区", "hours": "21時〜翌1時", "url": "https://hiroshimayakan.com/", "ll": [34.40394, 132.50493], "id": "H089", "review_query": "広島夜間救急動物病院 広島市東区", "review_name": "広島夜間救急動物病院", "addr": "広島県広島市東区温品2-8-40 大崎ビル", "spec": "広島県獣医師会賛同会員が運営する夜間救急病院"}, {"name": "konomi動物病院", "city": "広島市東区", "hours": "19時30分〜23時30分", "url": "https://konomiah.com/jikangai.html", "ll": [34.41341, 132.50869], "id": "H091", "review_query": "konomi動物病院 広島市東区", "review_name": "konomi動物病院", "addr": "広島県広島市東区温品5-2-4", "spec": "一般診療の病院の時間外診察（犬・猫・ウサギのみ）"}], "山口県": [{"name": "竹田動物病院 夜間救急診療", "city": "岩国市", "hours": "月〜金 19時30分〜22時", "url": "http://ww52.tiki.ne.jp/~tamc/", "ll": [34.0911, 132.00166], "id": "H092", "review_query": "竹田動物病院 岩国市", "review_name": "竹田動物病院", "addr": "山口県岩国市周東町西長野153番地5", "spec": "地域の一般診療の病院の夜間救急診療（犬猫ほか小動物）"}, {"name": "北九州夜間救急動物病院", "city": "北九州市八幡東区（福岡県）", "hours": "21時〜24時", "url": "https://kitakyu-vet.com/night/", "ll": [33.86986, 130.7999], "id": "H093", "review_query": "北九州夜間救急動物病院 北九州市八幡東区", "review_name": "北九州夜間救急動物病院", "addr": "福岡県北九州市八幡東区東田1丁目3-6", "spec": "北九州市獣医師会の夜間病院（犬・猫以外は問い合わせ）"}, {"name": "広島夜間救急動物病院", "city": "広島市東区（広島県）", "hours": "21時〜翌1時", "url": "https://hiroshimayakan.com/", "ll": [34.40394, 132.50493], "id": "H089", "review_query": "広島夜間救急動物病院 広島市東区", "review_name": "広島夜間救急動物病院", "addr": "広島県広島市東区温品2-8-40 大崎ビル", "spec": "広島県獣医師会賛同会員が運営する夜間救急病院"}], "徳島県": [{"name": "おおしま動物病院", "city": "板野郡藍住町", "hours": "20時以降の夜間救急（院長がいない日は不可。先に電話。初めての方は現金1万円を先に預ける）", "url": "https://www.oshima-ah.com/%E5%A4%9C%E9%96%93%E6%95%91%E6%80%A5", "ll": [34.1272, 134.495], "ll_city": true, "addr": "", "spec": "犬・猫の動物病院。夜間救急を受け付け", "id": "H094", "review_query": "おおしま動物病院 板野郡藍住町", "review_name": "おおしま動物病院"}, {"name": "香川県獣医師会 夜間当番動物病院（当番制）", "city": "香川県内（香川県）", "hours": "20時〜23時", "url": "https://www.kagawaken-vet.jp/dutydoc2.html", "id": "H095", "spec": "獣医師会の当番制夜間病院。応急的な一次診療のみ"}, {"name": "神戸夜間動物救急センター", "city": "神戸市西区（兵庫県）", "hours": "21時〜翌9時", "url": "https://www.kobe-naec.com/", "ll": [34.67864, 134.9928], "id": "H082", "review_query": "神戸夜間動物救急センター 神戸市西区", "review_name": "神戸夜間動物救急センター", "addr": "兵庫県神戸市西区玉津町今津364-24", "spec": "年中無休で夜間救急専門の病院（犬・猫）"}], "香川県": [{"name": "香川県獣医師会 夜間当番動物病院（当番制）", "city": "香川県内（日替わりの当番病院）", "hours": "20時〜23時", "url": "https://www.kagawaken-vet.jp/dutydoc2.html", "id": "H095", "spec": "獣医師会の当番制夜間病院。応急的な一次診療のみ"}], "愛媛県": [{"name": "VET'S-えひめ 夜間応急診療（当番制）", "city": "松山市周辺（日替わりの当番病院）", "hours": "20時〜23時", "url": "https://ehime-vets.jp/", "id": "H096", "spec": "愛媛県開業獣医師会の当番制の夜間応急診療"}], "高知県": [{"name": "高知県獣医師会 夜間診療（当番制）", "city": "高知県内（日替わりの当番病院）", "hours": "20時〜23時", "url": "https://www.kochikenjuishikai.or.jp/article/archives/8", "id": "H097", "spec": "獣医師会の当番制夜間診療。応急的な一次診療（犬・猫）"}], "福岡県": [{"name": "福岡夜間救急動物病院", "city": "福岡市博多区", "hours": "20時〜翌5時", "url": "https://pet99.net/", "ll": [33.56677, 130.4608], "id": "H098", "review_query": "福岡夜間救急動物病院 福岡市博多区", "review_name": "福岡夜間救急動物病院", "addr": "福岡県福岡市博多区月隈5丁目2-40", "spec": "獣医師が共同出資した夜間専門の病院（犬・猫）"}, {"name": "北九州夜間救急動物病院", "city": "北九州市八幡東区", "hours": "21時〜24時", "url": "https://kitakyu-vet.com/night/", "ll": [33.86986, 130.7999], "id": "H093", "review_query": "北九州夜間救急動物病院 北九州市八幡東区", "review_name": "北九州夜間救急動物病院", "addr": "福岡県北九州市八幡東区東田1丁目3-6", "spec": "北九州市獣医師会の夜間病院（犬・猫以外は問い合わせ）"}], "佐賀県": [{"name": "福岡夜間救急動物病院", "city": "福岡市博多区（福岡県）", "hours": "20時〜翌5時", "url": "https://pet99.net/", "ll": [33.56677, 130.4608], "id": "H098", "review_query": "福岡夜間救急動物病院 福岡市博多区", "review_name": "福岡夜間救急動物病院", "addr": "福岡県福岡市博多区月隈5丁目2-40", "spec": "獣医師が共同出資した夜間専門の病院（犬・猫）"}], "長崎県": [{"name": "福岡夜間救急動物病院", "city": "福岡市博多区（福岡県）", "hours": "20時〜翌5時", "url": "https://pet99.net/", "ll": [33.56677, 130.4608], "id": "H098", "review_query": "福岡夜間救急動物病院 福岡市博多区", "review_name": "福岡夜間救急動物病院", "addr": "福岡県福岡市博多区月隈5丁目2-40", "spec": "獣医師が共同出資した夜間専門の病院（犬・猫）"}], "熊本県": [{"name": "一二三ペットクリニック 夜間診療", "city": "熊本市東区", "hours": "20時〜24時（月曜は休み）", "url": "https://hifumi-petclinic.com/", "ll": [32.82284, 130.76012], "id": "H099", "review_query": "一二三ペットクリニック 熊本市東区", "review_name": "一二三ペットクリニック", "addr": "熊本県熊本市東区下南部3-12-9", "spec": "夜間診療に対応する病院（犬・猫・エキゾチック）"}, {"name": "きらてとあにまるほすぴたる", "city": "熊本市南区", "hours": "夜間救急", "url": "https://k1r4t3t0animalhospital.jp/", "ll": [32.76257, 130.67871], "id": "H100", "review_query": "きらてとあにまるほすぴたる 熊本市南区", "review_name": "きらてとあにまるほすぴたる", "addr": "熊本県熊本市南区島町4丁目10-21", "spec": "時間外・夜間救急診療も行う動物病院"}], "大分県": [{"name": "大分動物夜間診療（獣医師が家に来る往診）", "city": "大分市", "hours": "受付 19時〜翌6時", "url": "https://animal.oita.jp/", "id": "H101", "spec": "獣医師が自宅に来る夜間往診（エキゾチック中心）"}], "宮崎県": [{"name": "大塚どうぶつ病院", "city": "宮崎市", "hours": "時間外・夜間も診療（受け入れはその時の状況しだい。先に電話）", "url": "https://o-vet.com/guidance/", "ll": [31.9077, 131.4202], "ll_city": true, "addr": "宮崎県宮崎市大塚町池ノ内1152-3", "spec": "犬・猫の地域の動物病院。救急医療も行い、夜間も対応", "id": "H102", "review_query": "大塚どうぶつ病院 宮崎市", "review_name": "大塚どうぶつ病院"}, {"name": "鹿児島大学 共同獣医学部附属動物病院 夜間診療", "city": "鹿児島市（鹿児島県）", "hours": "平日19時〜翌6時（予約制）", "url": "https://www.vet.kagoshima-u.ac.jp/KUVTH/service/night-visit/", "ll": [31.57258, 130.54646], "id": "H103", "review_query": "鹿児島大学 共同獣医学部附属動物病院 鹿児島市", "review_name": ["鹿児島大学", "共同獣医学部附属動物病院"], "addr": "鹿児島県鹿児島市郡元一丁目21番24号", "spec": "大学の動物病院の夜間診療。完全予約制（犬・猫のみ）"}], "鹿児島県": [{"name": "鹿児島大学 共同獣医学部附属動物病院 夜間診療", "city": "鹿児島市", "hours": "平日19時〜翌6時（予約制）", "url": "https://www.vet.kagoshima-u.ac.jp/KUVTH/service/night-visit/", "ll": [31.57258, 130.54646], "id": "H103", "review_query": "鹿児島大学 共同獣医学部附属動物病院 鹿児島市", "review_name": ["鹿児島大学", "共同獣医学部附属動物病院"], "addr": "鹿児島県鹿児島市郡元一丁目21番24号", "spec": "大学の動物病院の夜間診療。完全予約制（犬・猫のみ）"}, {"name": "鹿児島地区獣医師会 夜間当番動物病院（当番制）", "city": "鹿児島市（日替わりの当番病院）", "hours": "土日祝 19時〜23時", "url": "https://kagoshima-vet.com/veterinarian/", "id": "H104", "spec": "鹿児島県獣医師会の案内する夜間当番の動物病院"}], "沖縄県": [{"name": "沖縄夜間動物病院", "city": "那覇市", "hours": "19時〜翌3時（月〜金）", "url": "https://okinawa-yakan-ah.com/", "ll": [26.21237, 127.67911], "id": "H105", "review_query": "沖縄夜間動物病院 那覇市", "review_name": "沖縄夜間動物病院", "addr": "沖縄県那覇市仲井真124-1", "spec": "平日の夜間・時間外の救急診療を行う病院"}, {"name": "動物病院なは 夜間救急医療センター", "city": "島尻郡南風原町", "hours": "20時〜翌3時（木・金曜は休み）", "url": "https://naha-ah.com/night", "ll": [26.20502, 127.72308], "id": "H106", "review_query": "動物病院なは 夜間救急医療センター 島尻郡南風原町", "review_name": ["動物病院なは", "夜間救急医療センター"], "addr": "沖縄県島尻郡南風原町新川64", "spec": "動物病院の夜間救急医療センター（エキゾチックは要確認）"}]}};/*/EMG*/
  (function(){
    var tabs = $("modeTabs"), box = $("emgBox");
    tabs.hidden = false;
    $("emgNote").textContent = "当サイトとは別の会社・病院です（" + EMG.checked + "時点の情報）。受付時間や対応は変わることがあるので、行く前・頼む前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、お問い合わせからお知らせください。急ぎでなければ、「空き状況・料金の問い合わせ」タブからお問い合わせください（お迎えは依頼から3時間以上あと）。車で行く時間と道のりは、OpenStreetMap の道路データ（© OpenStreetMap contributors）で計算しています。";
    // 病院：名前は公式サイトへのリンク。どんな病院か・所在地（公式サイトで確かめたものだけ）と口コミの星も出す（リンクの中にリンクは置けないので枠は div）
    function item(x, sub){
      var d = document.createElement("div"), a = document.createElement("a");
      d.className = "emg-item emg-co";
      a.href = x.url; a.target = "_blank"; a.rel = "noopener";
      a.innerHTML = "<b></b>"; a.querySelector("b").textContent = x.name;
      a.addEventListener("click", function(){ track("emergency_link", {link_text: x.name, link_url: x.url}); });
      d.appendChild(a);
      var sm = document.createElement("small"); sm.textContent = sub; d.appendChild(sm);
      if (x.spec) { var sp = document.createElement("small"); sp.className = "emg-spec"; sp.textContent = x.spec; d.appendChild(sp); }
      if (x.addr) { var ad = document.createElement("small"); ad.textContent = "所在地：" + x.addr; d.appendChild(ad); }
      if (x.review_query) { var sc = document.createElement("div"); sc.className = "emg-score"; sc.dataset.id = x.id; d.appendChild(sc); }
      // [B] この病院までのペットタクシーの料金をくらべる（行き先に所在地を入れてフォームへ）
      if (x.addr) { var tx = document.createElement("a"); tx.className = "emg-taxi"; tx.href = "/?to=" + encodeURIComponent(x.addr) + "#form"; tx.textContent = "この病院までのペットタクシーの料金をくらべる →"; d.appendChild(tx); }
      return d;
    }
    // 搬送の会社：名前は公式サイトへのリンク、電話番号はタップで電話できるように（リンクの中にリンクは置けないので枠は div）
    function company(x){
      var d = document.createElement("div"), a = document.createElement("a");
      d.className = "emg-item emg-co";
      a.href = x.url; a.target = "_blank"; a.rel = "noopener";
      a.innerHTML = "<b></b>"; a.querySelector("b").textContent = x.name;
      d.appendChild(a);
      var sm = document.createElement("small"); sm.textContent = "対応エリア：" + x.area + "。" + x.note; d.appendChild(sm);
      (x.tel || []).forEach(function(t){
        var c = document.createElement("a");
        c.className = "emg-tel"; c.href = "tel:" + t[1].replace(/-/g, "");
        c.textContent = "📞 " + t[1] + (t[0] ? "（" + t[0] + "）" : "");
        d.appendChild(c);
      });
      if (!(x.tel || []).length) { var no = document.createElement("small"); no.textContent = "電話番号はリンク先の公式サイトでご確認ください。"; d.appendChild(no); }
      if (x.review_query) { var sc = document.createElement("div"); sc.className = "emg-score"; sc.dataset.id = x.id; sc.dataset.q = x.review_query; d.appendChild(sc); }
      return d;
    }
    // 搬送の会社と病院の口コミ（星・件数・本文）：予約の候補カードと同じしくみ。緊急タブを開いているときだけ、画面に出てきた会社・病院のぶんを取り寄せる
    // 点数は保存しない（このページを開いているあいだだけ覚えて、同じ会社を何度も聞かない）
    var emgScoreMemo = {};
    function paintScore(el, rv){
      el.replaceChildren();
      if (rv && rv.rating > 0) {
        var score = document.createElement("p"); score.className = "partner-score";
        var stars = document.createElement("span"); stars.className = "stars"; stars.setAttribute("aria-hidden", "true");
        stars.style.setProperty("--fill", Math.max(0, Math.min(5, rv.rating)) / 5 * 100 + "%");
        var num = document.createElement("b"); num.textContent = Number(rv.rating).toFixed(1);
        score.setAttribute("aria-label", "口コミの評価 5点中" + Number(rv.rating).toFixed(1) + "点、" + rv.count + "件");
        var open = document.createElement("button"); open.type = "button"; open.className = "partner-review-open";
        open.textContent = "口コミ" + rv.count + "件を見る";
        var src = document.createElement("span"); src.className = "partner-review-src"; src.textContent = "Google Maps"; // 出どころの表示（規約で必要）
        score.append(stars, num, open, src);
        var panel = document.createElement("div"); panel.className = "review-panel"; panel.hidden = true;
        open.addEventListener("click", function(){ toggleReviews(el.dataset.id, panel, open); });
        el.append(score, panel);
      } // 点数が取れないときは何も出さない（外部の口コミページへは飛ばさない）
    }
    var emgQueue = [], emgTimer = 0;
    function emgFlush(){
      emgTimer = 0;
      var need = emgQueue.filter(function(id, i, a){ return a.indexOf(id) === i && !(id in emgScoreMemo); }); emgQueue = [];
      for (var i = 0; i < need.length; i += 12) (function(ids){ // 1回に12件まで
        ids.forEach(function(id){ emgScoreMemo[id] = null; }); // 取り寄せ中に同じところをもう一度聞かない
        var body = new URLSearchParams(); body.set("kind", "emg_scores"); body.set("ids", ids.join(","));
        fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).catch(function(){ return null; }).then(function(j){
          var sc = (j && j.ok && j.scores) || {};
          ids.forEach(function(id){ emgScoreMemo[id] = sc[id] || null; });
          box.querySelectorAll(".emg-score").forEach(function(el){ if (ids.indexOf(el.dataset.id) >= 0) paintScore(el, emgScoreMemo[el.dataset.id]); });
        });
      })(need.slice(i, i + 12));
    }
    function emgWant(el){
      if (el.dataset.id in emgScoreMemo) { paintScore(el, emgScoreMemo[el.dataset.id]); return; }
      emgQueue.push(el.dataset.id); if (!emgTimer) emgTimer = setTimeout(emgFlush, 300);
    }
    // 口コミの欄は空のあいだ見えないので、会社・病院の枠が画面に入ったら取り寄せる（一覧が長いときに全部は聞かない）
    var emgIO = "IntersectionObserver" in window ? new IntersectionObserver(function(es){
      es.forEach(function(x){ if (x.isIntersecting && x.target.offsetParent) { emgIO.unobserve(x.target); var el = x.target.querySelector(".emg-score"); if (el) emgWant(el); } });
    }, {rootMargin: "200px"}) : null;
    function emgScores(){
      if (box.hidden) return;
      box.querySelectorAll(".emg-score[data-id]").forEach(function(el){
        if (el.dataset.seen) return; el.dataset.seen = "1";
        if (REVIEW_ON_CLICK) { var id = el.dataset.id; if (id in emgScoreMemo) paintScore(el, emgScoreMemo[id]); else el.replaceChildren(lazyReviews(id, function(v){ emgScoreMemo[id] = v; })); return; }
        if (emgIO) emgIO.observe(el.parentElement); else emgWant(el);
      });
    }
    // 都道府県で見せる（場所が入っていないとき）
    function show(p){
      var h = $("emgHosp"), t = $("emgTaxi");
      h.innerHTML = ""; t.innerHTML = ""; $("emgSum").hidden = true;
      (EMG.hospitals[p] || []).forEach(function(x){ h.appendChild(item(x, x.city + "・" + x.hours)); });
      if (/（.+[都道府県]）/.test(h.textContent)) h.insertAdjacentHTML("afterbegin", '<p class="emg-none">近くの県の病院もあわせて載せています。ほかの県の病院は、場所のあとに（ ）で県名を書いています。</p>');
      if (!h.children.length) h.innerHTML = '<p class="emg-none">この地域の夜間の動物病院は、まだ載せていません。かかりつけの病院にご相談ください。</p>';
      showTaxi(p);
    }
    function showTaxi(p){
      var t = $("emgTaxi");
      t.innerHTML = "";
      EMG.taxis.filter(function(x){ return x.prefs.indexOf(p) >= 0; }).forEach(function(x){ t.appendChild(company(x)); });
      if (!t.children.length) t.innerHTML = '<p class="emg-none">この地域で緊急の搬送をしている会社は、まだ見つけられていません。病院に移動の方法も相談してみてください。</p>';
      emgScores();
    }

    // ── 現在地から近い順：半径（直線）でしぼり、車で行く時間を道路データで調べる ──
    var PREF47 = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"];
    // 一覧の病院を1つずつに（近くの県として何度も載っている病院は1回だけ）
    var ALL = [], seenH = {};
    Object.keys(EMG.hospitals).forEach(function(p){
      EMG.hospitals[p].forEach(function(x){
        var k = x.name + "|" + x.url;
        if (seenH[k] || !x.ll) return;
        seenH[k] = 1;
        var m = x.city.match(/（(.+?[都道府県])）/);
        ALL.push({x: x, c: {lat: x.ll[0], lng: x.ll[1]}, city: !!x.ll_city, where: m ? m[1] + x.city.replace(/（.*?）/g, "") : (x.city.indexOf(p) === 0 ? "" : p) + x.city});
      });
    });
    var here = null, nearSeq = 0, inp = $("emgWhere"), say = function(t, ng){ var m = $("emgMsg"); m.textContent = t; m.className = "geo-msg" + (ng ? " ng" : ""); };
    function kmNow(){ var r = document.querySelector('input[name="emg_km"]:checked'); return r ? Number(r.value) : 20; }
    function km1(n){ return (Math.round(n * 10) / 10).toFixed(1) + "km"; }
    // 位置から都道府県（市区町村コードの頭2桁）
    function prefAt(c){
      return fetch("https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress?lat=" + c.lat.toFixed(6) + "&lon=" + c.lng.toFixed(6))
        .then(function(r){ return r.json(); })
        .then(function(j){ var cd = j && j.results && String(j.results.muniCd || ""); return cd ? PREF47[Number(cd.slice(0, 2)) - 1] || null : null; })
        .catch(function(){ return null; });
    }
    // 車で行く時間（1回の問い合わせで全部の病院ぶん）。取れなければ null
    function driveTimes(from, list){
      if (!list.length) return Promise.resolve([]);
      var cs = [from].concat(list.map(function(e){ return e.c; }));
      return fetch(ROAD_API + "/table/v1/driving/" + cs.map(function(c){ return c.lng.toFixed(5) + "," + c.lat.toFixed(5); }).join(";") + "?sources=0&annotations=duration,distance")
        .then(function(r){ return r.json(); })
        .then(function(j){
          if (!j || j.code !== "Ok") return null;
          return list.map(function(e, i){ var d = j.durations[0][i + 1], m = j.distances && j.distances[0][i + 1]; return d == null ? null : {min: Math.max(1, Math.round(d / 60)), km: m / 1000}; });
        })
        .catch(function(){ return null; });
    }
    function showNear(){
      if (!here) return;
      var my = ++nearSeq, R = kmNow(), h = $("emgHosp"), sum = $("emgSum");
      var list = ALL.map(function(e){ return {e: e, d: kmBetween(here, e.c)}; }).sort(function(a, b){ return a.d - b.d; });
      var inR = list.filter(function(x){ return x.d <= R; }).slice(0, 60);
      var shown = inR.length ? inR : list.slice(0, 3);
      sum.hidden = false;
      sum.textContent = inR.length ? "現在地から半径" + R + "kmの中に" + inR.length + "件あります。車で行く時間を調べています…"
        : "現在地から半径" + R + "kmの中には、載せている夜間の病院がありません。いちばん近い" + shown.length + "件を出しています（範囲を広げることもできます）。";
      function draw(times){
        h.innerHTML = "";
        var rows = shown.map(function(x, i){ return {x: x, t: times && times[i]}; });
        if (times) rows.sort(function(a, b){ return (a.t ? a.t.min : 1e9) - (b.t ? b.t.min : 1e9) || a.x.d - b.x.d; });
        rows.forEach(function(r){
          var e = r.x.e, a = item(e.x, (e.where || e.x.city) + "・" + e.x.hours), tag = document.createElement("span");
          tag.className = "emg-dist";
          // 番地まで確かめられなかった病院は、市区町村の中心からの目安だと書く
          tag.textContent = (r.t ? "🚗 車で" + (e.city ? "約" : "") + r.t.min + "分（道のり" + km1(r.t.km) + "）" : "直線で" + (e.city ? "約" : "") + km1(r.x.d)) + (e.city ? "・市区町村の中心からの目安" : "");
          a.insertBefore(tag, a.querySelector(".emg-score")); h.appendChild(a);
        });
        emgScores();
      }
      draw(null);
      driveTimes(here, shown.map(function(x){ return x.e; })).then(function(times){
        if (my !== nearSeq) return;
        if (times) draw(times);
        if (inR.length) sum.textContent = "現在地から半径" + R + "kmの中に" + inR.length + "件あります（" + (times ? "車で行く時間が短い順" : "近い順") + "）。" +
          (times ? "時間は道路が空いているときの目安で、混み具合によって長くなります。" : "車で行く時間は調べられませんでした。距離は直線で出しています。");
      });
      // 当番制・往診のように決まった場所がないものは、距離を出さずにその県のぶんを添える
      function byPref(p){
        if (!p) return;
        setSelect($("emgPref"), p); showTaxi(p);
        var mob = (EMG.hospitals[p] || []).filter(function(x){ return !x.ll; });
        if (!mob.length) return;
        var w = document.createElement("div");
        w.innerHTML = '<p class="emg-none">当番制・往診（決まった場所がないので、距離は出していません）</p>';
        mob.forEach(function(x){ w.appendChild(item(x, x.city + "・" + x.hours)); });
        h.appendChild(w);
        drawn = w; emgScores();
      }
      var drawn = null, redraw = draw;
      draw = function(t){ redraw(t); if (drawn) h.appendChild(drawn); };
      if (here.pref) byPref(here.pref);
      else prefAt(here).then(function(p){ if (my !== nearSeq) return; here.pref = p; byPref(p); });
    }
    function setHere(c){ here = c ? {lat: c.lat, lng: c.lng} : null; if (here) showNear(); else show($("emgPref").value); }
    // 書かれた場所を位置にする（全国。候補から選んだ場所はその位置）
    var whereCache = {};
    function findWhere(q){
      if (pickedPlace[q]) return Promise.resolve(pickedPlace[q]);
      if (q in whereCache) return Promise.resolve(whereCache[q]);
      var byAddr = gsiList(q, true).then(function(l){ var n = normAddr(q).replace(/付近$/, ""); return (l.filter(function(x){ var t = normAddr(x.label); return t.indexOf(n) === 0 || n.indexOf(t) === 0; })[0] || {}).c || null; });
      var byName = function(){ return photon(q, true).then(function(l){ return (l[0] || {}).c || null; }); };
      var p = looksAddress(q) ? byAddr.then(function(c){ return c || byName(); }) : byName().then(function(c){ return c || byAddr; });
      return p.then(function(c){ return whereCache[q] = c; });
    }
    var whereSeq = 0;
    function onWhere(){
      var q = inp.value.trim(), my = ++whereSeq;
      if (!q) { say(""); setHere(null); return; }
      if (pickedPlace[q] === null) return; // 候補の位置を取り寄せ中（届いたらもう一度呼ばれる）
      if (pickedPlace[q]) { say(""); setHere(pickedPlace[q]); return; }
      say("場所を調べています…");
      findWhere(q.replace(/付近$/, "")).then(function(c){
        if (my !== whereSeq) return;
        if (!c) { say("場所が見つかりませんでした。候補から選ぶか、市区町村や住所で入れてください。", true); return; }
        say(""); setHere(c);
      });
    }
    inp.addEventListener("change", onWhere);
    inp.addEventListener("keydown", function(e){ if (e.key === "Enter" && !e.isComposing && $("emgWhereList").hidden) { e.preventDefault(); inp.blur(); } });
    $("emgKm").addEventListener("change", showNear);
    // 「現在地を入れる」：押して許可されたときだけ端末の位置を読み、住所の文字にして欄に入れる（位置はどこにも送らない）
    if (navigator.geolocation) {
      var gb = $("emgGeo");
      gb.hidden = false;
      gb.addEventListener("click", function(){
        gb.disabled = true; say("現在地を調べています…");
        getPos(function(pos){
          var c = {lat: pos.coords.latitude, lng: pos.coords.longitude};
          reverseOsm(c, 16)
            .catch(function(){ return null; })
            .then(function(j){
              var a = (j && j.address) || {}, code = String(a["ISO3166-2-lvl4"] || "").match(/^JP-(\d\d)$/), pref = code ? PREF47[Number(code[1]) - 1] : (a.province || a.state || "");
              var parts = [];
              [a.city, a.town, a.village, a.city_district, a.suburb, a.quarter, a.neighbourhood].forEach(function(x){
                if (!x || parts.join("").indexOf(x) >= 0) return;
                if (parts.length && x.indexOf(parts[parts.length - 1]) === 0) parts.pop();
                parts.push(x);
              });
              var text = parts.length ? pref + parts.join("") + "付近" : "現在地（" + c.lat.toFixed(4) + ", " + c.lng.toFixed(4) + "）";
              pickedPlace[text] = c; // 距離は端末の位置そのままで計算する
              inp.value = text; inp.classList.remove("picked");
              gb.disabled = false; ++whereSeq;
              say("入れました。違うときは書きかえてください。");
              setHere({lat: c.lat, lng: c.lng, pref: code ? pref : null});
            });
        }, function(e){
          gb.disabled = false;
          say(e.code === 1 ? "位置情報が許可されませんでした。使うときはブラウザの設定で許可するか、場所を入力してください。" : "現在地がわかりませんでした。場所を入力してください。", true);
        });
      });
    }
    function setMode(m){
      if (m === "emg" && box.hidden) track("emergency_open");
      tabs.querySelectorAll("button").forEach(function(b){ b.setAttribute("aria-selected", String(b.dataset.mode === m)); });
      box.hidden = m !== "emg";
      if (m === "emg") emgScores();
      document.querySelector(".form-sec .form-card").hidden = m === "emg";
      // 緊急タブでは、予約の見出しと、その下の予約の案内（頼み方・料金・よくある質問など）を隠して、緊急の情報だけにする
      var sh = document.querySelector(".form-sec .sh"), after = false;
      if (sh) sh.hidden = m === "emg";
      document.querySelectorAll("main > section").forEach(function(sec){
        if (after) sec.hidden = m === "emg";
        if (sec.id === "form") after = true;
      });
    }
    tabs.addEventListener("click", function(e){ var b = e.target.closest("button"); if (b) setMode(b.dataset.mode); });
    // 都道府県を選びなおしたら、場所の欄は空にして都道府県の一覧に戻す
    // 選んだ都道府県は、病院・ドッグランなどのページと共通で覚えておく（tools/prefkeep.py の petInfoPref。Nori 2026-11-02「一度選んだらユーザーが変更するまで固定」）
    $("emgPref").addEventListener("change", function(){ track("emergency_pref", {pref: this.value}); try { localStorage.setItem("petInfoPref", this.value); } catch (x) {} inp.value = ""; say(""); ++whereSeq; here = null; ++nearSeq; show(this.value); });
    // トップでは覚えている県を、エリアページではそのページの県を最初に出す
    (function(){
      var p = null;
      if (location.pathname === "/") { try { p = localStorage.getItem("petInfoPref"); } catch (x) {} }
      if (p && [].some.call($("emgPref").options, function(o){ return o.value === p; })) setSelect($("emgPref"), p);
      show($("emgPref").value || "東京都");
    })();
    if (location.hash === "#emergency") setMode("emg");
    // 右上の「空き状況と料金を問い合わせる」：ふつうのタブに戻す（Nori 2026-11-01 予約と見積もりを分けない）
    document.querySelectorAll("[data-cta]").forEach(function(a){
      a.addEventListener("click", function(){ setMode("normal"); track("header_cta", {}); });
    });
  })();

  // いまいる場所：ボタンを押して許可されたときだけ端末の位置を読み、住所の文字にしてお迎えの場所に入れる（位置そのものは送らない）
  (function(){
    var btn = $("geoBtn"), msg = $("geoMsg");
    if (!navigator.geolocation) return;
    btn.hidden = false;
    var PREF_CODE = {"JP-13": "東京都", "JP-14": "神奈川県", "JP-12": "千葉県", "JP-11": "埼玉県"};
    if (ALL_JAPAN) PREF_NAMES.forEach(function(n, i){ PREF_CODE["JP-" + (i < 9 ? "0" : "") + (i + 1)] = n; });
    function say(t, ng){ msg.textContent = t; msg.className = "geo-msg" + (ng ? " ng" : ""); }
    btn.addEventListener("click", function(){
      btn.disabled = true; say("いまいる場所を調べています…");
      getPos(function(pos){
        var c = {lat: pos.coords.latitude, lng: pos.coords.longitude};
        if (!inBox(c, BOX4)) { btn.disabled = false; say("いまいる場所は、対応エリアの外のようです。お迎えの場所を入力してください。", true); return; }
        say("住所に直しています…");
        reverseOsm(c, 18)
          .then(function(j){
            var a = (j && j.address) || {}, pref = PREF_CODE[a["ISO3166-2-lvl4"]] || a.province || a.state || "";
            if (!PREF_CODE[a["ISO3166-2-lvl4"]] && (ALL_JAPAN ? PREF_NAMES : ["東京都","神奈川県","千葉県","埼玉県"]).indexOf(pref) < 0) throw 0;
            var parts = [];
            [a.city, a.town, a.village, a.city_district, a.suburb, a.quarter, a.neighbourhood].forEach(function(x){
              if (!x || parts.join("").indexOf(x) >= 0) return;
              if (parts.length && x.indexOf(parts[parts.length - 1]) === 0) parts.pop(); // 「神南」→「神南一丁目」は詳しいほうだけ
              parts.push(x);
            });
            if (!parts.length) throw 0;
            var text = pref + parts.join("") + (a.house_number ? a.house_number : "") + "付近";
            geoCache[text] = pickedPlace[text] = c; // 距離の計算は、端末の位置そのままで行う
            setSelect($("pref"), pref); $("pref").dispatchEvent(new Event("change"));
            $("pickup").value = text; $("pickup").dispatchEvent(new Event("change"));
            btn.disabled = false; say("入れました。建物の名前や目印があれば書き足してください。");
          })
          .catch(function(){ btn.disabled = false; say("住所に直せませんでした。お迎えの場所を入力してください。", true); });
      }, function(e){
        btn.disabled = false;
        say(e.code === 1 ? "位置情報が許可されませんでした。使うときはブラウザの設定で許可するか、お迎えの場所を入力してください。" : "いまいる場所がわかりませんでした。お迎えの場所を入力してください。", true);
      });
    });
  })();

  // 以前の版でブラウザに残した入力は使わないので消しておく
  try { localStorage.removeItem(SAVE_KEY); } catch (e) {}

  // 場所の候補：送ったことのある場所を、この端末のブラウザの中だけに覚えて、入力欄の候補に出す（自動では入れない）
  var HIST_KEY = "petPlaces", HIST_MAX = 10;
  function readHist(){ try { var h = JSON.parse(localStorage.getItem(HIST_KEY) || "[]"); return Array.isArray(h) ? h : []; } catch (e) { return []; } }
  function showHist(){ $("histClear").hidden = !readHist().length; }
  function addHist(list){
    var h = readHist();
    list.forEach(function(v){ v = String(v || "").trim(); if (!v) return; h = h.filter(function(x){ return x !== v; }); h.unshift(v); });
    try { localStorage.setItem(HIST_KEY, JSON.stringify(h.slice(0, HIST_MAX))); } catch (e) {}
    showHist();
  }
  $("histClear").addEventListener("click", function(){ try { localStorage.removeItem(HIST_KEY); } catch (e) {} showHist(); });
  showHist();

  // ── 場所の候補：入力すると、駅・施設・住所の候補を出す（4都県の中だけ）。送ったことのある場所も上に出す ──
  // 候補の取り寄せは suggestPlaces だけ。別の地図サービスに替えるときは、ここだけ差し替える
  function photon(q, wide){
    var bx = boxOf(wide);
    return fetch("https://photon.komoot.io/api/?limit=8&lang=default&bbox=" + [bx[1], bx[0], bx[3], bx[2]].join(",") + "&q=" + encodeURIComponent(q))
      .then(function(r){ return r.json(); })
      .then(function(j){
        return ((j && j.features) || []).map(function(f){
          var g = f.properties || {}, c = f.geometry.coordinates;
          var area = [g.state, g.city, g.district, g.locality].filter(function(x, i, a){ return x && a.indexOf(x) === i; }).join("");
          var addr = (g.street || "") + (g.housenumber || "");
          var name = g.name || addr;
          if (!name) return null;
          // 地図データの駅名は「東京」のように「駅」がないので付ける
          if (/^(railway|public_transport)$/.test(g.osm_key) && /^(station|halt|stop_area)$/.test(g.osm_value) && !/駅$/.test(name)) name += "駅";
          return {label: name, sub: area + (g.name && addr ? addr : ""), area: g.city || g.district || "", c: {lat: c[1], lng: c[0]}};
        }).filter(function(x){ return x && inBox(x.c, bx); });
      })
      .catch(function(){ return []; });
  }
  function gsiList(q, wide){
    return fetch("https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + encodeURIComponent(q))
      .then(function(r){ return r.json(); })
      .then(function(a){
        return (a || []).slice(0, 30).map(function(x){
          var c = x.geometry.coordinates, t = (x.properties || {}).title || "";
          return {label: t, sub: "住所", c: {lat: c[1], lng: c[0]}};
        }).filter(function(x){ return x.label && (wide ? inBox(x.c, boxOf(wide)) : /^(東京都|神奈川県|千葉県|埼玉県)/.test(x.label) && inBox(x.c, BOX4)); }).slice(0, 5);
      })
      .catch(function(){ return []; });
  }
  // 主な駅は改札口・出口まで、空港はターミナルまで候補に出す（駅の出口の位置は駅の位置、ターミナルはそれぞれの位置）
  // 名前: [読み, 緯度, 経度, 区市町村, [出口…]]。空港の出口は [名前, 緯度, 経度]
  var STATION_EXITS = {
    "東京": ["とうきょう", 35.6812, 139.7671, "千代田区", ["丸の内北口","丸の内中央口","丸の内南口","八重洲北口","八重洲中央口","八重洲南口","日本橋口"]],
    "有楽町": ["ゆうらくちょう", 35.6750, 139.7630, "千代田区", ["中央口","京橋口","日比谷口"]],
    "新橋": ["しんばし", 35.6662, 139.7583, "港区", ["汐留口","銀座口","烏森口","日比谷口"]],
    "浜松町": ["はままつちょう", 35.6554, 139.7571, "港区", ["北口","南口"]],
    "品川": ["しながわ", 35.6285, 139.7388, "港区", ["高輪口","港南口"]],
    "大崎": ["おおさき", 35.6197, 139.7286, "品川区", ["北改札","南改札"]],
    "五反田": ["ごたんだ", 35.6260, 139.7236, "品川区", ["東口","西口"]],
    "目黒": ["めぐろ", 35.6337, 139.7158, "品川区", ["東口","西口"]],
    "恵比寿": ["えびす", 35.6467, 139.7101, "渋谷区", ["東口","西口"]],
    "渋谷": ["しぶや", 35.6580, 139.7016, "渋谷区", ["ハチ公口","南口","東口","西口","新南改札"]],
    "原宿": ["はらじゅく", 35.6702, 139.7027, "渋谷区", ["表参道口","竹下口"]],
    "代々木": ["よよぎ", 35.6830, 139.7020, "渋谷区", ["東口","西口","北口"]],
    "新宿": ["しんじゅく", 35.6896, 139.7006, "新宿区", ["東口","西口","南口","東南口","新南改札"]],
    "高田馬場": ["たかだのばば", 35.7126, 139.7038, "新宿区", ["早稲田口","戸山口"]],
    "池袋": ["いけぶくろ", 35.7295, 139.7109, "豊島区", ["東口","西口","北口"]],
    "大塚": ["おおつか", 35.7317, 139.7286, "豊島区", ["北口","南口"]],
    "日暮里": ["にっぽり", 35.7281, 139.7710, "荒川区", ["北改札","南改札"]],
    "上野": ["うえの", 35.7138, 139.7773, "台東区", ["中央改札","公園口","浅草口","不忍口","入谷口"]],
    "御徒町": ["おかちまち", 35.7075, 139.7748, "台東区", ["北口","南口"]],
    "秋葉原": ["あきはばら", 35.6984, 139.7731, "千代田区", ["電気街口","昭和通り口","中央改札"]],
    "神田": ["かんだ", 35.6918, 139.7709, "千代田区", ["北口","南口","東口","西口"]],
    "飯田橋": ["いいだばし", 35.7020, 139.7450, "千代田区", ["東口","西口"]],
    "四ツ谷": ["よつや", 35.6860, 139.7302, "新宿区", ["麹町口","赤坂口","四ツ谷口"]],
    "中野": ["なかの", 35.7056, 139.6657, "中野区", ["北口","南口"]],
    "吉祥寺": ["きちじょうじ", 35.7031, 139.5798, "武蔵野市", ["北口","南口"]],
    "三鷹": ["みたか", 35.7027, 139.5609, "三鷹市", ["北口","南口"]],
    "立川": ["たちかわ", 35.6980, 139.4137, "立川市", ["北口","南口"]],
    "八王子": ["はちおうじ", 35.6556, 139.3389, "八王子市", ["北口","南口"]],
    "町田": ["まちだ", 35.5423, 139.4455, "町田市", ["中央口","ターミナル口"]],
    "二子玉川": ["ふたこたまがわ", 35.6115, 139.6268, "世田谷区", ["東口","西口"]],
    "自由が丘": ["じゆうがおか", 35.6076, 139.6688, "目黒区", ["正面口","南口"]],
    "下北沢": ["しもきたざわ", 35.6614, 139.6680, "世田谷区", ["東口","西口","南西口"]],
    "錦糸町": ["きんしちょう", 35.6969, 139.8140, "墨田区", ["北口","南口"]],
    "北千住": ["きたせんじゅ", 35.7493, 139.8048, "足立区", ["東口","西口"]],
    "赤羽": ["あかばね", 35.7779, 139.7209, "北区", ["東口","西口"]],
    "蒲田": ["かまた", 35.5626, 139.7161, "大田区", ["東口","西口"]],
    "川崎": ["かわさき", 35.5313, 139.6969, "川崎市川崎区", ["東口","西口"]],
    "武蔵小杉": ["むさしこすぎ", 35.5764, 139.6597, "川崎市中原区", ["北口","南口","横須賀線口"]],
    "横浜": ["よこはま", 35.4658, 139.6223, "横浜市西区", ["東口","西口","きた東口","きた西口"]],
    "新横浜": ["しんよこはま", 35.5068, 139.6175, "横浜市港北区", ["北口","篠原口"]],
    "藤沢": ["ふじさわ", 35.3389, 139.4874, "藤沢市", ["北口","南口"]],
    "大船": ["おおふな", 35.3540, 139.5310, "鎌倉市", ["東口","西口"]],
    "鎌倉": ["かまくら", 35.3190, 139.5505, "鎌倉市", ["東口","西口"]],
    "小田原": ["おだわら", 35.2564, 139.1554, "小田原市", ["東口","西口"]],
    "大宮": ["おおみや", 35.9064, 139.6238, "さいたま市大宮区", ["東口","西口"]],
    "浦和": ["うらわ", 35.8587, 139.6574, "さいたま市浦和区", ["東口","西口"]],
    "川口": ["かわぐち", 35.8018, 139.7173, "川口市", ["東口","西口"]],
    "川越": ["かわごえ", 35.9073, 139.4826, "川越市", ["東口","西口"]],
    "所沢": ["ところざわ", 35.7872, 139.4730, "所沢市", ["東口","西口"]],
    "千葉": ["ちば", 35.6130, 140.1135, "千葉市中央区", ["東口","西口"]],
    "船橋": ["ふなばし", 35.7017, 139.9853, "船橋市", ["北口","南口"]],
    "津田沼": ["つだぬま", 35.6912, 140.0204, "習志野市", ["北口","南口"]],
    "海浜幕張": ["かいひんまくはり", 35.6485, 140.0420, "千葉市美浜区", ["北口","南口"]],
    "舞浜": ["まいはま", 35.6363, 139.8838, "浦安市", ["北口","南口"]],
    "松戸": ["まつど", 35.7843, 139.9006, "松戸市", ["東口","西口"]],
    "柏": ["かしわ", 35.8620, 139.9711, "柏市", ["東口","西口"]],
    "羽田空港": ["はねだくうこう", 0, 0, "大田区", [["第1ターミナル", 35.5490, 139.7840],["第2ターミナル", 35.5505, 139.7880],["第3ターミナル", 35.5440, 139.7690]]],
    "成田空港": ["なりたくうこう", 0, 0, "成田市", [["第1ターミナル", 35.7647, 140.3864],["第2ターミナル", 35.7727, 140.3929],["第3ターミナル", 35.7768, 140.3958]]]
  };
  // ひらがなで入れてもしぼりこめるように、出口の言葉の読みも持つ（長い言葉から先に置きかえる）
  var KANA = {"八重洲":"やえす","丸の内":"まるのうち","日本橋":"にほんばし","ハチ公":"はちこう","高輪":"たかなわ","港南":"こうなん","電気街":"でんきがい","昭和通り":"しょうわどおり",
    "汐留":"しおどめ","銀座":"ぎんざ","烏森":"からすもり","日比谷":"ひびや","京橋":"きょうばし","表参道":"おもてさんどう","竹下":"たけした","早稲田":"わせだ","戸山":"とやま",
    "麹町":"こうじまち","赤坂":"あかさか","四ツ谷":"よつや","横須賀線":"よこすかせん","篠原":"しのはら","正面":"しょうめん","南西":"なんせい",
    "公園":"こうえん","浅草":"あさくさ","不忍":"しのばず","入谷":"いりや","中央":"ちゅうおう","新南":"しんみなみ","東南":"とうなん","きた":"きた",
    "東":"ひがし","西":"にし","南":"みなみ","北":"きた","改札":"かいさつ","口":"ぐち","第":"だい"};
  function kana(t){ Object.keys(KANA).forEach(function(k){ t = t.split(k).join(KANA[k]); }); return norm(t); }
  function stationExits(q){
    var n = norm(q).replace(/駅|エキ/, ""), out = [];
    Object.keys(STATION_EXITS).forEach(function(st){
      var d = STATION_EXITS[st], head = [norm(st), norm(d[0])].filter(function(h){ return n.indexOf(h) === 0; })[0];
      if (head == null && n.length >= 2 && (norm(st).indexOf(n) === 0 || norm(d[0]).indexOf(n) === 0)) head = n; // 「羽田」→羽田空港 のように途中まででも
      if (head == null) return;
      var rest = n.slice(head.length), air = /空港$/.test(st);
      d[4].forEach(function(ex){
        var name = air ? ex[0] : ex, k = kana(name);
        if (rest && norm(name).indexOf(rest) < 0 && k.indexOf(rest) < 0 && k.indexOf(rest.replace(/クチ$/, "グチ")) < 0) return;
        out.push({label: st + (air ? " " : "駅 ") + name, sub: d[3] + (air ? "・空港のターミナル" : "・駅の出口"), area: d[3],
          c: air ? {lat: ex[1], lng: ex[2]} : {lat: d[1], lng: d[2]}});
      });
    });
    return out.slice(0, 8);
  }
  // 大手の地図サービスの候補（ブラウザ用のキー。このサイトからしか使えないように制限してある）。
  // 空のとき・エラーや回数の上限で使えないときは、その場で無料の候補に切り替える
  var PLACES_KEY = "AIzaSyDq6ZmPburL0C8lqSdOggncPQ66EBdcxjg";
  var gOff = !PLACES_KEY, gSession = "";
  function gToken(){ return gSession || (gSession = window.crypto && crypto.randomUUID ? crypto.randomUUID() : Date.now() + "-" + Math.random().toString(36).slice(2)); }
  function gArea(t){ var m = String(t || "").replace(/^日本、?/, "").match(/^(?:東京都|神奈川県|千葉県|埼玉県)?(.+?[市区町村])/); return m ? m[1].replace(/^(.+?市)(.+区)$/, "$1$2") : ""; }
  function google(q, wide){
    if (gOff) return Promise.resolve(null);
    var bx = boxOf(wide);
    return fetch("https://places.googleapis.com/v1/places:autocomplete", {method: "POST",
        headers: {"Content-Type": "application/json", "X-Goog-Api-Key": PLACES_KEY},
        body: JSON.stringify({input: q, sessionToken: gToken(), languageCode: "ja", regionCode: "jp", includedRegionCodes: ["jp"],
          locationRestriction: {rectangle: {low: {latitude: bx[0], longitude: bx[1]}, high: {latitude: bx[2], longitude: bx[3]}}}})})
      .then(function(r){ if (!r.ok) throw r.status; return r.json(); })
      .then(function(j){
        return ((j && j.suggestions) || []).map(function(s){ return s.placePrediction; }).filter(Boolean).map(function(p){
          var f = p.structuredFormat || {}, main = (f.mainText || {}).text || (p.text || {}).text || "", sub = ((f.secondaryText || {}).text || "").replace(/^日本、?/, "");
          return {label: main, sub: sub, area: gArea(sub), gid: p.placeId, google: true};
        }).filter(function(x){ return x.label && x.gid; });
      })
      .catch(function(){ gOff = true; return null; });
  }
  // 「幕張 動物病院」のような一般的なことばでは名前の候補が少ないので、そのときだけ施設をことばで探して足す（位置も一緒に届く）
  var tOff = !PLACES_KEY;
  function googleText(q, wide){
    if (tOff) return Promise.resolve([]);
    var bx = boxOf(wide);
    return fetch("https://places.googleapis.com/v1/places:searchText", {method: "POST",
        headers: {"Content-Type": "application/json", "X-Goog-Api-Key": PLACES_KEY, "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location"},
        body: JSON.stringify({textQuery: q, languageCode: "ja", regionCode: "jp", pageSize: 6,
          locationRestriction: {rectangle: {low: {latitude: bx[0], longitude: bx[1]}, high: {latitude: bx[2], longitude: bx[3]}}}})})
      .then(function(r){ if (!r.ok) throw r.status; return r.json(); })
      .then(function(j){
        return ((j && j.places) || []).map(function(p){
          var sub = String(p.formattedAddress || "").replace(/^日本、?/, "").replace(/^〒\d{3}-?\d{4}\s*/, ""), c = p.location && {lat: p.location.latitude, lng: p.location.longitude};
          return {label: (p.displayName || {}).text || "", sub: sub, area: gArea(sub), c: c, gid: p.id, google: true};
        }).filter(function(x){ return x.label && inBox(x.c, bx); });
      })
      .catch(function(){ tOff = true; return []; });
  }
  // 選んだ候補の位置を調べる（選んだときの1回だけ）
  function googlePlace(id, wide){
    var t = gSession; gSession = "";
    return fetch("https://places.googleapis.com/v1/places/" + encodeURIComponent(id) + "?languageCode=ja" + (t ? "&sessionToken=" + encodeURIComponent(t) : ""),
        {headers: {"X-Goog-Api-Key": PLACES_KEY, "X-Goog-FieldMask": "location"}})
      .then(function(r){ if (!r.ok) throw r.status; return r.json(); })
      .then(function(j){ var c = j && j.location && {lat: j.location.latitude, lng: j.location.longitude}; return inBox(c, boxOf(wide)) ? c : null; })
      .catch(function(){ return null; });
  }
  var suggCache = {};
  function suggestPlaces(q, wide){
    var ck = String(wide) + q;
    if (ck in suggCache) return Promise.resolve(suggCache[ck]);
    return google(q, wide).then(function(g){
      if (!g) return freePlaces(q, wide);
      var list = g.slice(0, 1).concat(stationExits(q), g.slice(1));
      if (list.length >= 3) return suggCache[ck] = list.slice(0, 10); // 駅そのものの次に出口
      return googleText(q, wide).then(function(t){
        var seen = {};
        list.forEach(function(x){ seen[x.gid || x.label] = 1; });
        return suggCache[ck] = list.concat(t.filter(function(x){ return !seen[x.gid]; })).slice(0, 10);
      });
    });
  }
  function freePlaces(q, wide){
    var jobs = [photon(q, wide).then(function(list){ return list.slice(0, 1).concat(stationExits(q), list.slice(1)); })]; // 駅そのものの次に出口
    if (looksAddress(q)) jobs.unshift(gsiList(q, wide));
    return Promise.all(jobs).then(function(rs){
      var seen = {}, out = [];
      rs.forEach(function(list){ list.forEach(function(x){ var k = x.label + "|" + x.sub; if (!seen[k]) { seen[k] = 1; out.push(x); } }); });
      // 選んだ都県の中の候補を先に
      var pb = wide !== true && PREF_BOX[$("pref").value];
      if (pb) out.sort(function(a, b){ return (inBox(b.c, pb) ? 1 : 0) - (inBox(a.c, pb) ? 1 : 0); });
      return suggCache[String(wide) + q] = out.slice(0, 10);
    });
  }
  // 入力欄に入れる文字：施設や駅は「名前（区市町村）」、住所はそのまま
  function placeText(x){ return x.area && x.label.indexOf(x.area) < 0 && x.sub !== "住所" ? x.label + "（" + x.area + "）" : x.label; }
  function esc(t){ return String(t).replace(/[&<>"]/g, function(ch){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[ch]; }); }
  ["pickup","via","dropoff","retPickup","retDropoff","emgWhere"].forEach(function(id){
    var wide = id === "emgWhere" ? true : id === "pickup" ? false : "near"; // 緊急タブ：全国。お迎え：4都県。行き先など：4都県のまわりまで
    var inp = $(id), wrap = document.createElement("div"), ul = document.createElement("ul"), items = [], seq = 0, timer = 0;
    wrap.className = "cb"; ul.className = "cb-list"; ul.setAttribute("role", "listbox"); ul.id = id + "List"; ul.hidden = true;
    inp.parentNode.insertBefore(wrap, inp); wrap.appendChild(inp); wrap.appendChild(ul);
    var note = document.createElement("p"); note.className = "place-note"; note.hidden = true;
    wrap.parentNode.insertBefore(note, wrap.nextSibling);
    inp.setAttribute("role", "combobox"); inp.setAttribute("aria-autocomplete", "list"); inp.setAttribute("aria-expanded", "false"); inp.setAttribute("aria-controls", ul.id);
    function close(){ ul.hidden = true; inp.setAttribute("aria-expanded", "false"); }
    function draw(list, loading){
      items = list;
      var html = list.map(function(x, i){
        return '<li role="option" data-i="' + i + '"' + (x.hist ? ' class="hist"' : '') + '><b>' + esc(x.label) + '</b>' + (x.sub ? '<small>' + esc(x.sub) + '</small>' : '') + '</li>';
      }).join("");
      if (loading) html += '<li class="none">候補を探しています…</li>';
      else if (list.some(function(x){ return x.google; })) html += '<li class="none g-attr" aria-hidden="true">Google Maps</li>'; // 候補の提供元の表示（決まりで必要）
      else if (!list.length && inp.value.trim().length >= 2) html = '<li class="none">候補が見つかりません。このまま入力するか、住所で入れてください</li>';
      ul.innerHTML = html;
      ul.hidden = !html; inp.setAttribute("aria-expanded", String(!!html));
    }
    function histFor(q){
      var n = norm(q);
      if (wide === true) return [];
      return readHist().filter(function(v){ return !n || norm(v).indexOf(n) >= 0; }).slice(0, q ? 3 : 5).map(function(v){ return {label: v, sub: "前に使った場所", hist: true}; });
    }
    function update(){
      var q = inp.value.trim(), my = ++seq, hist = histFor(q);
      clearTimeout(timer);
      if (q.length < 2) { draw((id === "pickup" && !$("geoBtn").hidden ? [{label: "📍 いまいる場所を入れる", sub: "この端末の位置情報を使います", geo: true}] : []).concat(hist)); return; }
      draw(hist, true);
      timer = setTimeout(function(){
        suggestPlaces(q, wide).then(function(list){
          if (my !== seq || document.activeElement !== inp) return;
          draw(hist.concat(list.filter(function(x){ return hist.every(function(h){ return h.label !== placeText(x); }); })));
        });
      }, 350);
    }
    function pick(i){
      var x = items[i];
      if (!x) return;
      if (x.geo) { close(); $("geoBtn").click(); return; }
      var text = x.hist ? x.label : placeText(x); seq++;
      inp.value = text; close();
      var done = function(c){
        if (c) pickedPlace[text] = c;
        if (inp.value !== text) return; // 待つあいだに書きかえられたら何もしない
        check(); inp.dispatchEvent(new Event("change", {bubbles: true}));
      };
      if (x.gid && !x.c) {
        pickedPlace[text] = null; check();
        googlePlace(x.gid, wide)
          .then(function(c){ return c || googleText(x.label + " " + x.sub, wide).then(function(l){ return (l[0] || {}).c || null; }); }) // 位置が取れなかったら、名前と住所で探し直す
          .then(function(c){ if (!c) delete pickedPlace[text]; done(c); });
      }
      else done(x.c);
    }
    // 打ち間違い防止：候補から選んでいない場所には、ひとこと添える（そのままでも送れる）
    function check(){
      if (wide === true) return; // 緊急タブは、見つからないときに欄の下でお知らせする
      var v = inp.value.trim(), ok = !v || v in pickedPlace || readHist().indexOf(v) >= 0;
      inp.classList.toggle("picked", !!v && ok);
      note.hidden = ok;
      note.textContent = ok ? "" : "候補から選ぶと、場所をより正しく伝えられます（このままでも大丈夫です）。";
    }
    inp.addEventListener("focus", function(){ if (!pickedPlace[inp.value.trim()]) update(); }); // 候補から選んだあとは、もう一度一覧を開かない
    inp.addEventListener("input", update);
    inp.addEventListener("blur", function(){ seq++; setTimeout(function(){ close(); check(); }, 150); });
    inp.addEventListener("input", function(){ inp.classList.remove("picked"); note.hidden = true; });
    inp.addEventListener("change", check);
    // スマホでもタップ1回で決まるよう mousedown で拾う
    ul.addEventListener("mousedown", function(e){
      var li = e.target.closest("li[data-i]");
      if (!li) return;
      e.preventDefault(); pick(Number(li.dataset.i));
    });
    inp.addEventListener("keydown", function(e){
      if (ul.hidden) return;
      var lis = Array.prototype.slice.call(ul.querySelectorAll("li[data-i]")), i = lis.findIndex(function(l){ return l.classList.contains("on"); });
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault(); if (!lis.length) return;
        if (i >= 0) lis[i].classList.remove("on");
        i = e.key === "ArrowDown" ? Math.min(lis.length - 1, i + 1) : Math.max(0, i - 1);
        lis[i].classList.add("on"); lis[i].scrollIntoView({block: "nearest"});
      } else if (e.key === "Enter" && lis.length) { e.preventDefault(); pick(Number(lis[Math.max(0, i)].dataset.i)); } // Enterでいちばん上の候補を入れる
      else if (e.key === "Escape") close();
    });
  });

  function requestPayload(split){
    var fd = new FormData(form);
    var when = fd.get("date") + "T" + fd.get("hour") + ":" + fd.get("minute");
    var trip = String(fd.get("trip") || "");
    var retWhen = trip === "往復" ? fd.get("ret_date") + "T" + fd.get("ret_hour") + ":" + fd.get("ret_minute") : "";
    var body = new URLSearchParams();
    ["website","pref","pickup","dropoff","trip","riders","luggage","name","tel","email"].forEach(function(k){ body.append(k, fd.get(k) || ""); });
    var o = collect();
    body.append("via", o.via);
    body.append("contact", "メール");
    body.append("datetime", when);

    var pets = o.pets, many = pets.length > 1;
    var count = {};
    pets.forEach(function(p){ count[p.species] = (count[p.species] || 0) + 1; });
    // 受付の仕組み（Code.gs）が読む項目。2匹以上のときは、まとめた値と pets（1行1匹）を送る
    body.append("species", many ? Object.keys(count).map(function(s){ return s + count[s] + "匹"; }).join("・") : pets[0].species);
    body.append("breed", many ? "" : pets[0].breed);
    body.append("weight", String(Math.max.apply(null, pets.map(function(p){ return Number(p.weight) || 0; }))));
    body.append("age", many ? "" : pets[0].age);
    body.append("sex", many ? "" : pets[0].sex);
    body.append("cage", ["借りたい","なし","持ち込む","どれでも"].filter(function(v){ return pets.some(function(p){ return p.cage === v; }); }).join("・"));
    body.append("care", pets.some(function(p){ return p.care === "必要"; }) ? "必要" : "不要");
    body.append("pet_count", String(pets.length));
    body.append("pets", pets.map(petLine).join("\n"));
    body.append("pets_json", JSON.stringify(pets));
    // 帰りの情報。受付の仕組みが専用の項目を読めるようになるまでは、メモにも書いて会社に伝わるようにする
    var back = "";
    if (trip === "往復") {
      body.append("return_datetime", retWhen);
      var rFrom = o.ret_other ? o.ret_pickup : o.dropoff, rTo = o.ret_other ? o.ret_dropoff : o.pickup;
      body.append("return_pickup", rFrom);
      body.append("return_dropoff", rTo);
      back = "【帰り】" + retWhen.replace("T", " ") + "に「" + rFrom + "」でお迎え →「" + rTo + "」まで";
    }
    // ペットだけで乗るときの渡す人・受け取る人は、メモの先頭に書いて会社に伝える
    var only = /^0/.test(o.riders) ? "【ペットだけで乗る】お迎えで渡す人：" + (o.hand_from || "未記入") + "／行き先で受け取る人：" + (o.hand_to || "未記入") : "";
    body.append("notes", [only, split ? "" : back, o.notes].filter(String).join("\n")); // 行き・帰りを別の会社に頼むときは、それぞれの会社に自分の区間だけ伝える
    body.append("est_km", lastKm ? String(lastKm) : "");
    body.append("est_km_highway", lastKmHigh ? String(lastKmHigh) : "");
    body.append("est_fare", lastFareNum ? String(lastFareNum) : "");
    body.append("est_fare_text", lastFare); // フォームに出したとおりの表示（例：11,300〜13,900円）

    body.append("route_details", JSON.stringify(routeDetails));
    return {body:body,o:o};
  }

  form.addEventListener("submit", function(e){
    e.preventDefault();
    if (sending) return;
    if (DEMO.ok && (chosenPicks.length || chosenGo || chosenBack)) { demoSent(); return; } // 見本の画面では送らない
    err.style.display = "none";
    function fail(msg, el){
      track("form_error", {field_name: el ? fieldName(el) : "none"}); // 止まった項目の名前だけ（中身は送らない）
      err.textContent = msg; err.style.display = "block";
      if (el) jumpTo(el);
    }
    if (!form.checkValidity()) {
      var miss = missingFields(null);
      if (!miss.length) return fail("まだ入力されていない項目があります。");
      markMissing(miss);
      if (miss.length === 1 && miss[0].el.id === "agree") return fail("確認のチェックを入れてください。", miss[0].el);
      fail("まだ入力されていない項目があります（押すとその場所へ移ります）。", miss[0].el);
      err.appendChild(needButtons(miss));
      return;
    }
    var fd = new FormData(form);
    var when = fd.get("date") + "T" + fd.get("hour") + ":" + fd.get("minute");
    var at = new Date(when + ":00+09:00");
    if (!(at > new Date(Date.now() + MIN_LEAD_H * 3600e3))) return fail("お迎えは、いまから" + MIN_LEAD_H + "時間後より先の日時を選んでください。", $("hour"));
    var trip = String(fd.get("trip") || ""), retWhen = "";
    if (trip === "往復") {
      retWhen = fd.get("ret_date") + "T" + fd.get("ret_hour") + ":" + fd.get("ret_minute");
      if (!(new Date(retWhen + ":00+09:00") > at)) return fail("帰りのお迎え日時は、行きのお迎えより後にしてください。", $("retHour"));
    }
    if (!GAS_URL) return fail("ただいまフォームを準備中です。少し時間をおいてお試しください。");
    // お迎えの場所と都県が食い違ったまま送らない（依頼する会社は都県で決まる）
    var pq = $("pickup").value.trim(), pv = $("pref").value;
    var pc = geoCache[(!pv || /^(東京|神奈川|千葉|埼玉)/.test(pq) ? "" : pv) + pq];
    var pp = pc && prefCache[pc.lat.toFixed(4) + "," + pc.lng.toFixed(4)];
    if (pp === "out") return fail("お迎えの場所が、対応エリアの外のようです。お迎えの場所を確かめてください。", $("pickup"));
    if (pp && pp !== pv) {
      setSelect($("pref"), pp); estNow();
      return fail("お迎えの場所が" + pp + "のようなので、お迎えの都道府県を「" + pp + "」に直しました。料金の目安を確かめてから、もう一度送信してください。", $("pref"));
    }

    var splitPick = !chosenQuote && trip === "往復" && chosenGo && chosenBack;
    if (!chosenQuote && !splitPick) { queuePartners(); return; }
    if (!routeDetails) return fail("料金の目安を計算しています。計算が終わるまでお待ちください。", $("pickup"));
    var payload = requestPayload(splitPick), body = payload.body, o = payload.o;
    var first = splitPick ? chosenGo : chosenQuote;
    var picks = splitPick ? [] : chosenPicks.slice();
    if (picks.some(function(c){ return Date.now() >= c.expires; }) || Date.now() >= first.expires || (splitPick && Date.now() >= chosenBack.expires)) { clearPartners(); queuePartners(); return fail("候補を更新しています。表示されたら、もう一度事業者を選んでください。"); }
    body.append("partner_id", first.id);
    body.append("quote_token", first.token);
    body.append("quote_expires", String(first.expires));
    if (!splitPick) {
      body.append("picks", JSON.stringify(picks.map(function(c){ return {id: c.id, token: c.token, expires: c.expires}; })));
    }
    if (splitPick) {
      body.append("split", "1");
      body.append("back_partner_id", chosenBack.id);
      body.append("back_quote_token", chosenBack.token);
      body.append("back_quote_expires", String(chosenBack.expires));
    }
    var selectedLabel = splitPick ? "行きは" + chosenGo.label + "、帰りは" + chosenBack.label : picks.map(function(c){ return c.label; }).join("、");
    // 同じ内容の送り直しで二重受付にならないよう、入力が変わらないかぎり同じ合言葉（req_key）を使う
    var identity = new URLSearchParams(body); ["quote_token","quote_expires","back_quote_token","back_quote_expires","picks"].forEach(function(k){ identity.delete(k); });
    var sig = identity.toString();
    if (sig !== lastSig) { lastSig = sig; reqKey = Date.now().toString(36) + Math.random().toString(36).slice(2, 10); }
    body.append("req_key", reqKey);

    var btn = $("sendSelected");
    var label = btn.textContent;
    clearTimeout(quoteTimer); clearTimeout(quoteRefreshTimer);
    quoteSeq++; sending = true; form.inert = true; $("sendAll").hidden = true;
    btn.disabled = true;
    btn.textContent = "選んだ会社へ問い合わせています…";
    function retry(msg){
      sending = false; form.inert = false;
      if (btn.isConnected) { btn.disabled = false; btn.textContent = label; }
      showAllButton();
      fail(msg);
    }
    // 受付の仕組みが保存できたと返してきたときだけ、完了画面にする
    var sendInfo = {companies: splitPick ? 2 : picks.length, split: splitPick ? 1 : 0, trip: trip === "往復" ? "round" : "one_way", pref: $("pref").value};
    track("inquiry_submit", sendInfo);
    fetch(GAS_URL, {method:"POST", body: body})
      .then(function(res){ return res.json(); })
      .then(function(r){
        if (!r || !r.ok) {
          var e = String(r && r.error || "");
          track("inquiry_fail", {reason: e.slice(0, 40) || "unknown"});
          if (e.indexOf("selection_") === 0 || e === "missing") { clearPartners(); retry("候補を更新しています。表示されたら、もう一度事業者を選んでください。"); queuePartners(); return; }
          if (e === "area") return retry("お迎えの場所が対応エリアの外のようです。お迎えの場所を確かめてください。");
          if (e === "datetime") return retry("お迎えの日時が近すぎるか、読み取れませんでした。いまから3時間後より先の日時を選び直してください。");
          return retry("受け付けできませんでした。入力内容はそのまま残っています。少し時間をおいて、もう一度送ってください。");
        }
        form.inert = false; sending = false;
        $("thanksPartner").textContent = selectedLabel;
        $("thanksFirst").textContent = picks.length > 1 ? "（届くたびにお送りします。くらべて1社を選んでください）" : "";
        if (r.id) { $("thanks-id").querySelector("b").textContent = r.back_id ? r.id + "（行き）・" + r.back_id + "（帰り）" : r.id; $("thanks-id").style.display = "block"; }
        addHist([o.pickup, o.via, o.dropoff, o.ret_pickup, o.ret_dropoff]);
        form.style.display = "none";
        $("thanks").style.display = "block";
        $("thanks").scrollIntoView({block:"start", behavior:"smooth"}); // 完了の知らせが画面の外にならないように
        track("generate_lead", sendInfo);
        // どの会社に問い合わせたか（会社ごとに1件。会社名とIDだけで、お客さまの情報は送らない）
        (splitPick ? [chosenGo, chosenBack] : picks).forEach(function(c){ var ci = coInfo(c); ci.pref = sendInfo.pref; track("lead_company", ci); });
      })
      .catch(function(){
        retry("受け付けできたか確認できませんでした。数分たっても受付メールが届かなければ、同じ事業者を選んで、もう一度問い合わせてください。入力内容はそのまま残っています。");
      });
  });
  // 「問い合わせる」ボタンは、説明を飛ばして入力欄（ご利用の流れの箱）へ（2026-11-08 レビュー #5）
  function toFormStart(smooth){ var fc = $("emgBox").hidden && document.querySelector("#form .form-card") || $("form"); fc.scrollIntoView({block: "start", behavior: smooth ? "smooth" : "auto"}); }
  document.addEventListener("click", function(e){
    var a = e.target.closest && e.target.closest('a[href="#form"]');
    if (!a) return;
    e.preventDefault(); toFormStart(true);
    formEntry = "cta"; track("form_cta", {cta: a.getAttribute("data-cta") || (a.closest(".sticky") ? "sticky" : a.closest("nav") ? "nav" : "body")});
    try { history.replaceState(null, "", "#form"); } catch (x) {}
  });
  if (location.hash === "#form") setTimeout(function(){ toFormStart(false); }, 0);
  // フォームの動きの計測（Nori 2026-11-08「フォームに入力した・サブミットした・フォームのページに来た・どこから来た」）。
  // 送るのは項目の名前と回数だけ。お名前・連絡先・場所・メモなどの入力した中身は送らない
  (function(){
    var page = location.pathname === "/" ? "top" : /^\/(tokyo|kanagawa|saitama|chiba|area)\//.test(location.pathname) ? "area" : "other";
    var from = (function(){ try { if (!document.referrer) return "direct"; var r = new URL(document.referrer); return r.hostname === location.hostname ? r.pathname : "external"; } catch (x) { return "unknown"; } })();
    var base = {page_type: page, from_page: from};
    if (location.hash === "#form") formEntry = "link";
    var card = document.querySelector("#form .form-card") || form, seen = false;
    function viewed(){ if (seen) return; seen = true; var p = {entry: formEntry || "scroll"}; for (var k in base) p[k] = base[k]; track("form_view", p); }
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function(es){ if (es[0].isIntersecting) { io.disconnect(); viewed(); } }, {threshold: 0.2});
      io.observe(card);
    }
    var begun = false, done = {};
    function field(e){
      var el = e.target, n = fieldName(el);
      if (!/^(INPUT|SELECT|TEXTAREA)$/.test(el.tagName) || !n || n === "website") return; // 迷惑投稿よけの隠し欄は数えない
      if (!begun) { begun = true; viewed(); var p = {field_name: n}; for (var k in base) p[k] = base[k]; track("form_input_start", p); }
      if (e.type === "change" && !done[n]) { done[n] = 1; track("form_field", {field_name: n}); }
    }
    form.addEventListener("focusin", field);
    form.addEventListener("change", field);
  })();
  syncOpenNote(); // 地域ページ・前回の入力で県が入っているとき
})();
