# お金を取らない情報ページ「全国の公営ドッグラン」（/dogrun/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「全部マネタイズじゃなくていい。SEO的なコンテンツでもいい」「どんどん進めて」。
# 守ること：国・都道府県・市町村の公園や動物愛護センターのドッグランだけ（民間は載せない）。順位・おすすめなし。電話番号なし。
# 公式ページで確かめたことだけ書く。データ：tools/dogrun.json。
import json, os

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dogrun.json"), encoding="utf-8"))

SLUG = "dogrun"
TITLE = "全国の公営ドッグラン｜都道府県でさがせる公園のドッグラン一覧（利用登録・ルールの目安つき）｜ペットタクシー予約窓口"
DESC = "国営・都道府県営・市町村の公園や動物愛護センターにある公営のドッグランを、都道府県ごとにまとめた無料の一覧です。公式ページへのリンクと、利用登録・狂犬病予防注射済票・ワクチン証明など、使う前に確かめたいことをまとめました。"

BEFORE = [
 ("利用登録がいるか", "公営のドッグランは、はじめに利用登録（WEB申請や登録会・説明会）がいるところが多いです。登録なしで使えるところもあります。"),
 ("持っていくもの", "多くのドッグランで、犬の鑑札と狂犬病予防注射済票（その年度のもの）が必要です。混合ワクチンの接種証明を求めるところもあります。"),
 ("入れない犬", "子犬（生後の日数に決まりがあるところ）、発情中の犬、病気の犬、人や犬をかむくせのある犬などは、入れないことが多いです。犬種や頭数に決まりがあるところも。"),
 ("大きさのエリア", "小型犬用と中・大型犬用にエリアが分かれているところがあります。体重や体高の区切りは場所ごとに違います。"),
 ("飼い主のマナー", "飼い主は必ず一緒に入り、犬から目を離さない。ふんは持ち帰る。ドッグランの外では引き綱をつける。"),
]

def _card(e, d):
    sub = e(d["city"]) if d.get("city") else ""
    note = f'<small>{e(d["note"])}</small>' if d.get("note") else ""
    return (f'<div class="emg-item emg-co"><a href="{e(d["url"])}" target="_blank" rel="noopener"><b>{e(d["name"])}</b></a>'
            + (f"<small>{sub}</small>" if sub else "") + note + "</div>")

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    rows = {}
    for d in J["dogruns"]:
        rows.setdefault(d["pref"], []).append(d)
    total = len(J["dogruns"])
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            ds = rows.get(pf, [])
            inner = "".join(_card(e, d) for d in ds) or f'<p class="emg-none">{e(pf)}の公営のドッグランは、まだ載せていません。見つけしだい足します。市町村のサイトで「ドッグラン」と検索すると見つかることがあります。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    faq = [
      ("ドッグランを使うのに必要なものは？", "多くの公営ドッグランで、犬の鑑札と狂犬病予防注射済票が必要です。混合ワクチンの接種証明や、事前の利用登録を求めるところもあります。行く前に公式ページで確かめてください。"),
      ("公営のドッグランは無料ですか？", "無料のところが多いですが、有料のところや、公園の駐車場が有料のところもあります。場所ごとに公式ページでご確認ください。"),
      ("犬の登録や狂犬病の予防注射はどこでしますか？", "お住まいの市区町村です。くわしくは「ペットの迷子・犬の登録・引取りの窓口」のページにまとめています。"),
    ]
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "全国の公営ドッグラン", "item": url}]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, indent=1) + "\n</script>"
    return ctx["head"](TITLE, DESC, url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › 全国の公営ドッグラン</nav>
    <h1><small>全国{total}か所・都道府県でしぼりこめます</small>全国の公営ドッグラン</h1>
    <p class="lede">思いきり走らせてあげたい。でも、どこにあるの？　国・都道府県・市町村の公園や動物愛護センターにある公営のドッグランを、都道府県ごとにまとめました。使う前に確かめたいことも一緒にどうぞ。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。公営（国・都道府県・市町村）のドッグランだけを載せていて、民間のドッグランは載せていません。順番は都道府県ごとで、おすすめ順ではありません。</p>
      <div class="emg-tips" style="margin-top:0"><h4>ドッグランに行く前に確かめること</h4><dl>{before}</dl>
      <p class="emg-tips-note">決まりは場所ごとに違います。ここに書いたのは多くのドッグランに共通する目安です。必ずリンク先の公式ページでご確認ください。</p></div>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">{e(J["checked"])}に公式ページで確かめた情報です。工事やイベント、天気で閉まることがあり、利用の方法も変わることがあるので、行く前に必ずリンク先でご確認ください。掲載の内容の誤りや、載せてほしい公営のドッグランは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>大型犬や多頭で、遠くのドッグランへ</h2><p>車がないとき、大型犬や何頭もいっしょのときは、ペットタクシーを予約できます（乗せられる犬の大きさや頭数は会社ごとに違います）。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    <ul class="other"><li><a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="/hospital/">条件でさがす動物病院</a></li><li><a href="/guide/large-dog/">大型犬の移動のガイド</a></li><li><a href="/guide/multi-pet/">多頭で乗れるペットタクシー</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
<script>
(function(){{
  var sel = document.getElementById("hospPref");
  function apply(){{
    var v = sel.value;
    document.querySelectorAll(".emg-pref").forEach(function(s){{ s.hidden = !!v && s.dataset.pref !== v; }});
    document.querySelectorAll(".emg-region").forEach(function(h){{ h.hidden = !!v; }});
  }}
  sel.addEventListener("change", apply);
  var m = location.hash.match(/^#pref=(.+)$/);
  if (m) {{ try {{ sel.value = decodeURIComponent(m[1]); apply(); }} catch (x) {{}} }}
}})();
</script>
""" + ctx["foot_noband"]()

def urls(SITE):
    return [f"{SITE}/{SLUG}/"]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))
