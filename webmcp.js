// AIエージェント向けの道具（WebMCP）。Nori 2026-11-02「Web MCPにも対応できる？」。
// 対応したブラウザ（AIエージェントの機能があるもの）のときだけ動き、ふつうのお客さまには何もしない（ga.js が読み込む）。
// 道具はすべて「見るだけ」：サイトに載せている一覧（/webmcp/data.json）をさがす、料金をくらべるページを開く。
// 会社への問い合わせ・送信はしない（フォームの送信はお客さまがボタンを押したときだけ）。
// 電話番号・口コミ・順位は返さない。データは tools/gen_webmcp.py が作る（gen_areas.py の最後）。
(function(){
  var mc = (typeof document !== "undefined" && document.modelContext) || (typeof navigator !== "undefined" && navigator.modelContext);
  if (!mc || typeof mc.registerTool !== "function") return;
  var SITE = "https://pet.shiokonbu.com";
  var PREFS = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"];
  var CATS = ["night_vet","emergency_transport","home_visit_vet","cat_vet","exotic_vet","large_facility_vet","dog_run","senior_dog_home","pet_sitter","dog_trainer","pet_hotel","mobile_grooming","pet_funeral","city_animal_office"];
  var dataP = null;
  function data(){
    if (!dataP) dataP = fetch("/webmcp/data.json").then(function(r){ if (!r.ok) throw new Error("data"); return r.json(); }).catch(function(e){ dataP = null; throw e; });
    return dataP;
  }
  function pref(s){
    if (!s) return "";
    s = String(s).trim();
    for (var i = 0; i < PREFS.length; i++) {
      var p = PREFS[i], short = p === "北海道" ? p : p.replace(/[都府県]$/, "");
      if (s === p || s === short) return p;
    }
    return null;
  }
  function out(obj){ return JSON.stringify(obj); }
  var RO = {readOnlyHint: true, consequentialHint: false};
  var tools = [
    {
      name: "list_pet_service_categories",
      description: "このサイト（ペットタクシー予約窓口）にある、ペットとのくらしの一覧のカテゴリ（夜間・救急の動物病院、往診、ドッグラン、老犬ホーム、ペットシッター、しつけ教室、ペットホテル、出張トリミング、ペット火葬・霊園、自治体の動物愛護センターなど）と件数を返します。見るだけです。",
      inputSchema: {type: "object", properties: {}},
      annotations: RO,
      execute: function(){
        return data().then(function(d){
          return out({categories: d.categories.map(function(c){ return {id: c.id, label: c.label, count: c.count, page: SITE + c.page}; }), note: d.note});
        });
      }
    },
    {
      name: "find_pet_services",
      description: "都道府県とカテゴリで、このサイトに載せている施設・会社（名前・市区町村や対応エリア・公式サイトのURL）をさがします。夜間の急病なら night_vet と emergency_transport。公式サイトで確かめたことだけを載せた一覧で、順位はありません。最新の受付時間などは必ず公式サイトで確かめるよう利用者に伝えてください。見るだけで、どこにも連絡しません。",
      inputSchema: {
        type: "object",
        properties: {
          category: {type: "string", enum: CATS, description: "カテゴリのID（list_pet_service_categories で一覧が見られます）"},
          prefecture: {type: "string", description: "都道府県（例：東京都、大阪、北海道）"},
          keyword: {type: "string", description: "市区町村名や名前の一部でさらにしぼるとき（例：世田谷区）"},
          limit: {type: "number", description: "最大件数（1〜50、ふだんは20）"}
        },
        required: ["category", "prefecture"]
      },
      annotations: RO,
      execute: function(a){
        a = a || {};
        var pf = pref(a.prefecture);
        if (!pf) return Promise.resolve(out({error: "都道府県が分かりませんでした。例：東京都、大阪府、北海道"}));
        if (CATS.indexOf(a.category) < 0) return Promise.resolve(out({error: "カテゴリが分かりませんでした。", categories: CATS}));
        var kw = a.keyword ? String(a.keyword).trim() : "";
        var lim = Math.max(1, Math.min(50, Math.floor(Number(a.limit) || 20)));
        return data().then(function(d){
          var cat = d.categories.filter(function(c){ return c.id === a.category; })[0];
          var rows = (d.items[a.category] || []).filter(function(r){
            if (r.pref !== pf) return false;
            if (!kw) return true;
            return [r.name, r.city, r.area, r.note].join(" ").indexOf(kw) >= 0;
          });
          return out({
            category: cat.label, prefecture: pf, total: rows.length,
            items: rows.slice(0, lim).map(function(r){ var o = {name: r.name, official_site: r.url}; if (r.city) o.city = r.city; if (r.area) o.area = r.area; if (r.note) o.note = r.note; return o; }),
            page: SITE + cat.page + "#pref=" + encodeURIComponent(pf),
            note: rows.length ? d.note : "この都道府県では、まだ載せていません。近くの都道府県もさがしてみてください。"
          });
        });
      }
    },
    {
      name: "open_pet_taxi_fare_comparison",
      description: "ペットタクシーの料金をくらべるフォームを開きます（都道府県を選んだ状態にします）。お迎えの場所・行き先・日時・ペットの情報は利用者が入れて、利用者が自分でボタンを押します。料金は各社の公式サイトの料金表から計算した概算で、確定料金ではありません。この道具は問い合わせを送りません。",
      inputSchema: {
        type: "object",
        properties: {prefecture: {type: "string", description: "お迎えの都道府県（例：神奈川県）"}},
        required: ["prefecture"]
      },
      annotations: {readOnlyHint: false, consequentialHint: false},
      execute: function(a){
        var pf = pref(a && a.prefecture);
        if (!pf) return Promise.resolve(out({error: "都道府県が分かりませんでした。例：東京都、大阪府、北海道"}));
        var sel = document.getElementById("pref"), form = document.getElementById("form");
        if (sel && form) {
          var ok = false;
          for (var i = 0; i < sel.options.length; i++) if (sel.options[i].value === pf) { ok = true; break; }
          if (ok) { sel.value = pf; sel.dispatchEvent(new Event("change", {bubbles: true})); }
          form.scrollIntoView({behavior: "smooth", block: "start"});
          return Promise.resolve(out({opened: true, prefecture: ok ? pf : null, next: "お迎えの場所・行き先・日時・ペットの情報を入れると、条件に合う会社と料金の目安が出ます。問い合わせは、利用者が会社を選んでボタンを押したときだけ送られます。", note: "料金は概算で、確定料金ではありません。当日の道順・渋滞・待ち時間などで変わります。"}));
        }
        return data().then(function(d){
          var url = SITE + (d.pref_pages[pf] || "/") + "#form";
          return out({opened: false, url: url, next: "このページを開くと、" + pf + "を選んだ状態のフォームが出ます。"});
        });
      }
    }
  ];
  tools.forEach(function(t){
    try { var p = mc.registerTool(t); if (p && p.catch) p.catch(function(){}); } catch (e) {}
  });
})();
