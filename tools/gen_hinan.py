# [B] SEO：ペットと避難（同行避難）の一覧 /hinan/ と、都道府県ごとのページ /hinan/<県>/。gen_areas.py が読み込んで使う。
# Nori 2026-11-14「シェルターとか避難所に関する記事を書いて。地域ごとも」「受け入れ可能な動物、サイズの規定とかも含めて」。
# 守ること：都道府県・市区の公式ページに書いてあることだけ（tools/hinan.json、出どころと確認日つき）。書いていないことは「書いていない」。
#   避難所の一覧は作らない（公式の一覧・地図へのリンクだけ）。電話番号は載せない。順位・おすすめなし。
#   ペットタクシーの話は、下の「前もって預け先へ移すとき」の節だけ（tools/taxi_cta.py がボタンを足す）。
# 人口の多い県から順に足す（第1弾 2026-11-14：東京都・神奈川県・大阪府・愛知県・埼玉県）。
import json, os
import gen_dogrun
import visual as V
from guides_hinan import HINAN_GUIDES, ITEMS, CHECKED, MARK, table_rows, N, N_CAGE, SIZES, BREEDS, SEIREI

SLUG = "hinan"
PSLUG = gen_dogrun.PSLUG
PUBLISHED = "2026-11-14"
MODIFIED = "2026-11-14"

FLAG_TXT = {"yes": "受け入れる", "no": "受け入れない", "hard": "むずかしい場合がある", "cond": "条件つき・一部は受け入れない", None: "書いていない"}
KINDS = [("dog", "犬"), ("large", "大型犬"), ("cat", "猫"), ("small", "うさぎ・ハムスターなど"), ("bird", "小鳥"), ("reptile", "爬虫類")]

def by_pref():
    out = {}
    for it in ITEMS:
        out.setdefault(it["pref"], []).append(it)
    return out

def href(pf):
    return f"/{SLUG}/{PSLUG[pf]}/"

# 全国の市区町村（tools/municipalities.json、Code for FUKUI の localgovjp・CC0 から。slug は読みのローマ字）
MUNI = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "municipalities.json"), encoding="utf-8"))
CSLUG = {(m["pref"], m["name"]): m["slug"] for m in MUNI}
MUNI_ORDER = {(m["pref"], m["name"]): i for i, m in enumerate(MUNI)}
CHUKAKU = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jichitai.json"), encoding="utf-8")).get("_chukaku", [])) or {
    c["city"] for c in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jichitai.json"), encoding="utf-8"))["cities"] if c["kind"] == "中核市"}
_HJ = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hinan.json"), encoding="utf-8"))
NONE = [tuple(x[:2]) for x in _HJ.get("none", [])]  # しらべたが、ペットと避難のページが見つからなかった市区町村 [県, 名前, 理由]

# 薄いページを作らない（Nori 2026-11-14「薄い記事は撲滅させてね。全部濃い記事にして」）。
# 中身の点数＝受け入れる動物・動物ごとの印・ケージ・飼う場所・大きさ／受け入れない動物・決まり2つ以上・避難所の一覧 の数（7点まで）。
# 市区町村は RICH_CITY 点以上で1ページ、足りなければ県のページの中に短く載せる。県のページは県と市区町村の合計が RICH_PREF 点以上で出す。
RICH_CITY, RICH_PREF = 5, 6
def score(it):
    return sum([bool(it.get("animals")), any(v for v in it["flags"].values()), bool(it.get("cage")), bool(it.get("place")),
                bool(it.get("size") or it.get("no")), len(it.get("rules") or []) >= 2, bool(it.get("map"))])
# Nori 2026-11-14「てか、そもそも薄い記事作らないで」：点数が足りても、書き出したあと tools/thin_gate.py で
# そのページだけの字数（ひな形の文を除く）を数え、足りないページは作らない（市区町村は県のページの中へ、県は一覧で「まだ」）。
THIN, PREF_THIN = set(), set()
def has_page(it):
    return it["kind"] == "city" and score(it) >= RICH_CITY and (it["pref"], it["name"]) not in THIN
def pref_ok(its):
    return sum(score(x) for x in its) >= RICH_PREF and its[0]["pref"] not in PREF_THIN

def href_city(it):
    return f"/{SLUG}/{PSLUG[it['pref']]}/{CSLUG[(it['pref'], it['name'])]}/"

CSS = """<style>
.hn-card{background:#fff;border:1.5px solid var(--line);border-radius:18px;padding:14px 16px 8px;margin:0 0 14px}
.hn-card h3{margin:0 0 8px;font-size:1.08rem}
.hn-card dl{margin:0;display:grid;grid-template-columns:1fr;gap:2px 0}
.hn-card dt{font-size:.74rem;font-weight:700;color:var(--ink-3);margin-top:8px}
.hn-card dd{margin:0;line-height:1.75;font-size:.92rem}
.hn-card ul{margin:2px 0 0;padding-left:1.2em;line-height:1.75;font-size:.92rem}
.hn-flags{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0!important;margin:4px 0 0!important}
.hn-flags li{font-size:.78rem;border-radius:999px;padding:2px 10px;background:#f3f1ee;color:#3c4043}
.hn-flags li.yes{background:#e6f4ea;color:#1e7d4f}.hn-flags li.no{background:#fde8e6;color:#b3261e}
.hn-flags li.hard,.hn-flags li.cond{background:#fff4e0;color:#8a5300}
.hn-src{font-size:.74rem;color:var(--ink-3);margin:10px 0 4px;line-height:1.6}
.hn-src a{color:var(--ink-3)}
.hn-pref{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:8px 0 16px}
.hn-pref a{display:inline-block;border:1.5px solid var(--line);border-radius:999px;padding:6px 14px;background:#fff;font-weight:700;text-decoration:none}
.hn-none{font-size:.84rem;color:var(--ink-3);line-height:1.7}
</style>"""

def _flags(e, it):
    return '<ul class="hn-flags">' + "".join(
        f'<li class="{it["flags"].get(k) or "unk"}">{e(lab)}：{e(FLAG_TXT[it["flags"].get(k)])}</li>' for k, lab in KINDS) + "</ul>"

def card(e, it):
    def row(t, v):
        return f"<dt>{e(t)}</dt><dd>{e(v)}</dd>" if v else f'<dt>{e(t)}</dt><dd class="hn-none">公式ページに書いていません（不明）</dd>'
    rules = ("<dt>そのほかの決まり・備え</dt><dd><ul>" + "".join(f"<li>{e(r)}</li>" for r in it["rules"]) + "</ul></dd>") if it.get("rules") else ""
    links = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></li>' for t, u in it["links"])
    mp = (f'<dt>避難所の場所</dt><dd><a href="{e(it["map"][1])}" target="_blank" rel="noopener">{e(it["map"][0])}</a></dd>' if it.get("map")
          else '<dt>避難所の場所</dt><dd class="hn-none">ペットを受け入れる避難所の一覧・地図は、確かめたページにはありませんでした。お住まいの市区町村のページでご確認ください。</dd>')
    return (f'<section class="hn-card" id="{e(it["name"])}"><h3>{e(it["name"])}</h3>{_flags(e, it)}<dl>'
            + row("考え方", it.get("policy")) + row("受け入れる動物", it.get("animals"))
            + (row("受け入れない・むずかしい動物", it["no"]) if it.get("no") else "")
            + row("大きさの決まり", it.get("size")) + row("ケージ・リード", it.get("cage")) + row("避難所で飼う場所", it.get("place"))
            + rules + mp + "</dl>"
            + f'<p class="hn-src">出どころ（{e(CHECKED)}に確認）：</p><ul class="hn-src">{links}</ul></section>')

def fit_rows(its):
    """県のページの「うちの子で見る」：大きさ・種類ごとに、その県の自治体の記載をならべる"""
    def line(it, txt): return f"{it['name']}：{txt}"
    def large(it):
        f = it["flags"].get("large")
        if it.get("size"): return it["size"]
        if f == "yes": return "受け入れると書いている"
        return "大型犬・大きさについては書いていない（市区町村・避難所に確かめる）"
    def small(it):
        fs, fb = it["flags"].get("small"), it["flags"].get("bird")
        if fs in ("yes",) or fb in ("yes",): return it.get("animals") or "受け入れると書いている"
        if fs or fb: return FLAG_TXT[fs or fb] + (f"（{it['no']}）" if it.get("no") else "")
        return "書いていない（市区町村・避難所に確かめる）"
    def flag(it, k):
        return FLAG_TXT[it["flags"].get(k)] + ("" if it["flags"].get(k) else "（市区町村・避難所に確かめる）")
    return [
        {"k": ["s"], "h": "小型犬（10kg未満）", "items": [line(it, flag(it, "dog")) for it in its]},
        {"k": ["m", "l"], "h": "中型犬・大型犬（10kg以上）", "items": [line(it, large(it)) for it in its]},
        {"k": ["cat"], "h": "猫", "items": [line(it, flag(it, "cat")) for it in its]},
        {"k": ["all"], "tag": "ほかの動物", "h": "うさぎ・ハムスター・小鳥・爬虫類", "items": [line(it, small(it)) for it in its]},
    ]

def faq_for(pf, its):
    out = []
    for it in its:
        nm = it["name"]
        a = it.get("animals")
        out.append((f"{nm}の避難所には、どんな動物を連れて行けますか？",
                    (f"{nm}の公式ページには「{a}」と書いてあります。" if a else f"{nm}の公式ページには、受け入れる動物の種類は書いてありません。")
                    + (f"{it['no']}" if it.get("no") else "") + "避難所ごとの決まりや災害の状況で変わることがあるので、確かめてください。"))
        sz = it.get("size")
        if sz:
            out.append((f"{nm}の避難所に大型犬は入れますか？", f"{nm}の公式ページには「{sz}」と書いてあります。"))
    return out[:8]

def _ld(SITE, url, title, desc, crumbs, faq):
    items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(crumbs)]
    d = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items},
         {"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "datePublished": PUBLISHED,
          "dateModified": MODIFIED, "mainEntityOfPage": url, "inLanguage": "ja",
          "author": {"@type": "Organization", "name": "ペットタクシー予約窓口", "url": SITE + "/"},
          "publisher": {"@type": "Organization", "name": "ペットタクシー予約窓口", "url": SITE + "/"}}]
    if faq:
        d.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    return '<script type="application/ld+json">\n' + json.dumps(d, ensure_ascii=False, indent=1) + "\n</script>"

def _taxi(e, where=""):
    # tools/taxi_cta.py がこの節（見出しに「ペットタクシー」）の後ろに、その県のフォームへのボタンを足す
    return f"""<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>台風の前などに、預け先へ移すとき（ペットタクシー）</h2><p>前もって分かる災害では、早めに親せきの家やペットホテルへ移っておくと、ペットにも家族にも負担が少なくなります。車がないときは、ペットタクシーで移る方法もあります（災害のさなかは道路や車の状況で動けないことがあります）。</p></div>
  </div>
</section>"""

def _guides(e):
    return '<ul class="other">' + "".join(f'<li><a href="/guide/{e(g["slug"])}/">{e(g["title"])}</a></li>' for g in HINAN_GUIDES) + "</ul>"

def _pref_links(e, done, cur=None):
    return '<ul class="hn-pref">' + "".join(
        (f'<li><a href="{href(pf)}"' + (' aria-current="page"' if pf == cur else "") + f'>{e(pf)}</a></li>') for pf in done) + "</ul>"

def render_top(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    bp = by_pref()
    done = [pf for _, ps in ctx["emg_regions"] for pf in ps if pf in bp and pref_ok(bp[pf])]
    rest = [pf for _, ps in ctx["emg_regions"] for pf in ps if pf not in done]
    title = "ペットの同行避難と避難所の決まり｜受け入れる動物・大型犬・ケージ（都道府県・市区ごと）｜ペットタクシー予約窓口"
    desc = (f"ペットと避難するときの「同行避難」と「同伴避難」のちがい、避難所で受け入れる動物（犬・猫・うさぎ・小鳥・爬虫類）、大型犬の扱い、ケージの決まりを、"
            f"{len(done)}都道府県・{N}の自治体の公式ページからまとめました。")
    faq = HINAN_GUIDES[0]["faq"][:6]
    ld = _ld(SITE, url, "ペットの同行避難と避難所の決まり", desc, [("ペットタクシー予約窓口", "/"), ("ペットと避難", f"/{SLUG}/")], faq)
    stats = V.stats([(f"{N}", "確かめた都道府県・市区"), (f"{N_CAGE}", "ケージを持っていく・入れると書いている"),
                     (f"{sum(1 for x in ITEMS if x['flags'].get('cat') == 'yes')}", "猫を受け入れると書いている")])
    pref_rows = [["都道府県", "確かめた自治体", "犬", "猫", "ケージ持参"]] + [
        [pf, str(len(bp[pf])), str(sum(1 for x in bp[pf] if x["flags"].get("dog") == "yes")),
         str(sum(1 for x in bp[pf] if x["flags"].get("cat") == "yes")), str(sum(1 for x in bp[pf] if x.get("cage_req")))] for pf in done]
    rest_txt = (f'<p class="hn-none">{e("・".join(rest))}は、ペットと避難の決まりを書いた公式ページが見つからなかったか、まだ確かめていません。お住まいの市区町村のホームページで「ペット 避難」と検索すると、受け入れの決まりが見つかることがあります。</p>' if rest else "")
    summ = "".join(f'<h3 class="emg-region"><a href="{href(pf)}">{e(pf)}のペット同行避難 →</a></h3><p class="hn-none">{e("・".join(it["name"] for it in bp[pf]))}の公式ページに書いてある、受け入れる動物・大きさ・ケージ・飼う場所と、避難所の調べ方。</p>' for pf in done)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › ペットと避難</nav>
    <h1><small>同行避難・同伴避難・避難所で受け入れる動物の決まり</small>ペットと避難するとき</h1>
    <p class="lede">災害のときは、ペットを連れて避難するのが原則です（同行避難）。ただし、避難所で同じ部屋にいられるとは限らず、受け入れる動物や飼う場所は市区町村・避難所ごとに違います。都道府県・市区の公式ページに書いてあることを、そのまままとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    <div class="answer"><h2 id="answer">ペットと避難するときのポイント</h2>
    <ul class="kv"><li><b class="k">同行避難</b>ペットを連れて避難所などまで逃げること。同じ部屋で過ごせるという意味ではない（環境省）</li>
    <li><b class="k">同伴避難</b>避難所で飼い主がペットを飼って世話をしている状態。これも同じ部屋とは限らない（環境省）</li>
    <li><b class="k">連れて行ける動物</b>犬・猫は多くの自治体が受け入れる。うさぎ・小鳥・爬虫類は自治体で違う</li>
    <li><b class="k">大型犬</b>はっきり書いた自治体は少なく、「小型」「小動物」に限る市が多い。ケージに入らなければリードでつなぐ、と書く市も（川崎市・大阪市）。預け先も決めておく</li>
    <li><b class="k">ケージ</b>飼い主が持っていくのが基本。避難所にペット用の備蓄はないと書く市が多い</li></ul></div>
    {finder(e, [p for _, ps in ctx["emg_regions"] for p in ps])}
    {stats}
    <h2 id="pref">都道府県ごとのくわしい決まり</h2>
    {_pref_links(e, done)}
    {rest_txt}
    <h2 id="table">都道府県ごとの確かめた自治体の数</h2>
    <p>「犬」「猫」は、受け入れると公式ページに書いてある自治体の数です。書いていない自治体も「受け入れない」という意味ではありません（{e(CHECKED)}に確認）。</p>
    {V.block(("table", pref_rows))}
    <h2 id="seirei">政令指定都市の受け入れる動物</h2>
    <p>○は受け入れると書いてある、△はむずかしい場合がある・一部は受け入れない、—は書いていない、です。ほかの市区町村は都道府県ごとのページにあります。</p>
    {V.block(("table", table_rows(SEIREI)))}
  </article></div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="emg">
      <h2 class="sh" id="list" style="scroll-margin-top:90px">都道府県ごとのページ</h2>
      <p class="emg-free">それぞれの公式ページに書いてあることだけを載せています。書いていないことは「公式ページに書いていません（不明）」としています（「受け入れない」という意味ではありません）。</p>
      {summ}
      <div class="emg-tips" id="faq"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">{e(CHECKED)}に各自治体の公式ページで確かめた情報です。避難所の決まりは変わることがあり、災害の状況や避難所ごとにも違います。必ずリンク先と、お住まいの市区町村でご確認ください。誤りは<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>くわしい記事</h2><p>避難のしかたと、日ごろの備えを記事でまとめています。</p></div>
    {_guides(e)}
    <div class="sh"><h2>ほかの窓口の案内</h2><p>はぐれたときの届け出先や、預け先もまとめています。</p></div>
    <ul class="other"><li><a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="/guide/lost-pet/">ペットが迷子になったら</a></li><li><a href="/pet-hotel/">大型犬OK・猫専用のペットホテル</a></li><li><a href="/hospital/night/">夜間・救急の動物病院</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li></ul>
  </div>
</section>
{_taxi(e)}
</main>
""" + ctx["foot_noband"]()

def render_pref(ctx, pf, its, done):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}{href(pf)}"
    prefs_it = [it for it in its if it["kind"] == "pref"]
    allc = sorted([it for it in its if it["kind"] == "city"], key=lambda x: MUNI_ORDER.get((pf, x["name"]), 9999))
    cities = [x for x in allc if has_page(x)]
    small = [x for x in allc if not has_page(x)]
    big = [x for x in allc if x["name"] in SEIREI or x["name"] in CHUKAKU]
    head_names = "・".join(x["name"] for x in (big or allc)[:3])
    title = (f"{pf}のペット同行避難｜市区町村ごとの避難所の決まり（{head_names}など）｜ペットタクシー予約窓口" if allc else
             f"{pf}のペット同行避難｜避難所で受け入れる動物・大型犬・ケージの決まり｜ペットタクシー予約窓口")
    desc = (f"{pf}でペットと避難するときの決まりを、{pf}と{len(allc)}の市区町村の公式ページからまとめました。避難所で受け入れる動物（犬・猫・うさぎ・小鳥・爬虫類）、"
            f"大型犬の扱い、ケージ・リード、避難所で飼う場所、受付の手続き、ペットを受け入れる避難所の調べ方。" if allc else
            f"{pf}でペットと避難するときの決まりを、{pf}の公式ページからまとめました。避難所で受け入れる動物、大型犬の扱い、ケージ・リード、避難所で飼う場所、ペットを受け入れる避難所の調べ方。")
    faq = faq_for(pf, prefs_it + big[:3] if big else prefs_it + allc[:3])
    ld = _ld(SITE, url, f"{pf}のペット同行避難と避難所の決まり", desc,
             [("ペットタクシー予約窓口", "/"), ("ペットと避難", f"/{SLUG}/"), (pf, href(pf))], faq)
    show = prefs_it + allc
    rows = [["自治体", "犬", "大型犬", "猫", "小動物・鳥", "爬虫類", "ケージ持参"]] + [
        [it["name"], MARK[it["flags"].get("dog")], MARK[it["flags"].get("large")], MARK[it["flags"].get("cat")],
         MARK[it["flags"].get("small") or it["flags"].get("bird")], MARK[it["flags"].get("reptile")], "要" if it.get("cage_req") else "—"] for it in show]
    fit_its = prefs_it + (big or allc)[:10]
    fit = V.block(("breeds", {"title": f"うちの子の大きさ・種類で、{pf}の決まりを見る", "rows": fit_rows(fit_its), "sizes": SIZES, "breeds": BREEDS,
                              "lead": f"{'・'.join(it['name'] for it in fit_its)}の公式ページに書いてあることを、大きさ・種類ごとに並べました。"
                                      + ("ほかの市区町村は、下のそれぞれのページで見られます。" if len(allc) > len(fit_its) - len(prefs_it) else ""),
                              "note": "書いていない自治体も「受け入れない」という意味ではありません。避難所ごとの決まりもあるので、お住まいの市区町村で確かめてください。"}))
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    lede = (f"{pf}と{len(allc)}の市区町村の公式ページに書いてある、ペットと避難するときの決まりです。" if allc else
            f"{pf}の公式ページに書いてある、ペットと避難するときの決まりです。") + "避難所で受け入れる動物や飼う場所は、市区町村・避難所ごとに違います。"
    pol = (prefs_it[0].get("policy") if prefs_it else None) or (allc[0].get("policy") if allc else "") or ""
    city_links = ('<ul class="hn-pref">' + "".join(f'<li><a href="{href_city(it)}">{e(it["name"])}</a></li>' for it in cities) + "</ul>") if cities else ""
    nf = [n for (p_, n) in NONE if p_ == pf]
    rest = [m["name"] for m in MUNI if m["pref"] == pf and m["name"] not in {x["name"] for x in allc} and m["name"] not in nf]
    cov = ""
    if nf:
        cov += f'<p class="hn-none">{e("・".join(nf))}は、ペットと避難について書いた公式ページが見つかりませんでした（{e(CHECKED)}にしらべました）。避難所の決まりは、それぞれの市町村の防災の担当にご確認ください。</p>'
    if rest:
        cov += f'<p class="hn-none">{e("・".join(rest))}は、まだ確かめていません。順に足していきます。</p>'
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{SLUG}/">ペットと避難</a> › {e(pf)}</nav>
    <h1><small>避難所で受け入れる動物・大型犬・ケージの決まり</small>{e(pf)}のペット同行避難</h1>
    <p class="lede">{e(lede)}</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    <div class="answer"><h2 id="answer">{e(pf)}のペットと避難のポイント</h2><p>{e(pol)}</p></div>
    {finder(e, [p for _, ps in ctx["emg_regions"] for p in ps], pf)}
    {('<h2 id="city">市区町村ごとのページ</h2>' + city_links) if cities else ""}
    {cov}
    <h2 id="table">受け入れる動物とケージ（自治体ごと）</h2>
    <p>○は受け入れると書いてある、△はむずかしい場合がある・一部は受け入れない、—は書いていない、です（{e(CHECKED)}に確認）。</p>
    {V.block(("table", rows))}
    {fit}
    {('<h2 id="detail">' + e(pf) + 'の決まり</h2>' + "".join(card(e, it) for it in prefs_it)) if prefs_it else ""}
    {('<h2 id="more">ほかの市区町村の決まり</h2>' + "".join(card(e, it) for it in small)) if small else ""}
    <h2 id="faq">よくある質問</h2>
    <dl class="emg-tips">{faq_html}</dl>
    <p class="emg-note">{e(CHECKED)}に各自治体の公式ページで確かめた情報です。避難所の決まりは変わることがあり、災害の状況や避難所ごとにも違います。必ずリンク先でご確認ください。誤りは<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
  </article></div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>くわしい記事</h2><p>同行避難と同伴避難のちがい、持ち出し品のリストなど。</p></div>
    {_guides(e)}
    <div class="sh"><h2>ほかの都道府県</h2><p>ほかの都道府県の決まりも、公式ページからまとめています。</p></div>
    {_pref_links(e, done, pf)}
    <ul class="other"><li><a href="/{SLUG}/">ペットと避難するとき（全国の一覧）</a></li><li><a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="/guide/lost-pet/">ペットが迷子になったら</a></li></ul>
  </div>
</section>
{_taxi(e, pf)}
</main>
""" + ctx["foot_noband"]()

def _answer(it):
    """市区町村のページの「ポイント」：受け入れる動物・大型犬・ケージを一文ずつ"""
    f = it["flags"]
    acc = [lab for k, lab in KINDS if f.get(k) == "yes" and k != "large"]
    out = []
    if it.get("policy"): out.append(it["policy"])
    out.append(("受け入れると書いてある動物：" + "・".join(acc) + "。") if acc else "受け入れる動物の種類は、公式ページに書いていません（不明）。")
    cnd = [lab for k, lab in KINDS if f.get(k) in ("cond", "hard") and k != "large"]
    if cnd: out.append("条件つき・むずかしい場合があると書いてある動物：" + "・".join(cnd) + (f"（{it['no']}）" if it.get("no") else "") + "。")
    ng = [lab for k, lab in KINDS if f.get(k) == "no" and k != "large"]
    if ng: out.append("受け入れないと書いてある動物：" + "・".join(ng) + "。")
    out.append("大型犬：" + (it.get("size") or FLAG_TXT[f.get("large")] + ("（避難所に確かめる）" if not f.get("large") else "")) )
    out.append("ケージ・キャリー：" + ("持っていく、またはケージの中で飼うと書いてある。" if it.get("cage_req") else (it.get("cage") or "公式ページに決まりは書いていません。")))
    return out

def render_city(ctx, pf, it, sibs, done):
    e, SITE = ctx["e"], ctx["SITE"]
    nm = it["name"]
    url = f"{SITE}{href_city(it)}"
    title = f"{nm}のペット同行避難｜避難所で受け入れる動物・大型犬・ケージ（{pf}）｜ペットタクシー予約窓口"
    acc = [lab for k, lab in KINDS if it["flags"].get(k) == "yes" and k != "large"]
    desc = (f"{pf}{nm}でペットと避難するときの決まりを、{nm}の公式ページからまとめました。"
            + (f"避難所で受け入れると書いてある動物（{'・'.join(acc)}）、" if acc else "避難所で受け入れる動物、")
            + "大型犬の扱い、ケージ・リード、避難所で飼う場所、ペットを受け入れる避難所の調べ方。")
    faq = faq_for(pf, [it])
    ld = _ld(SITE, url, f"{nm}のペット同行避難と避難所の決まり", desc,
             [("ペットタクシー予約窓口", "/"), ("ペットと避難", f"/{SLUG}/"), (pf, href(pf)), (nm, href_city(it))], faq)
    # 市区町村のページは体重と猫だけで選ぶ（決まりは犬種では変わらない。犬種名の一覧で本文をふくらませない。2026-11-14 薄いページの担当から）
    fit = V.block(("breeds", {"title": f"うちの子の大きさ・種類で、{nm}の決まりを見る", "rows": fit_rows([it]), "sizes": SIZES, "names": False,
                              "lead": f"{nm}の公式ページに書いてあることを、大きさ・種類ごとに並べました。",
                              "note": "書いていないことも「受け入れない」という意味ではありません。避難所ごとの決まりもあるので、市区町村や避難所で確かめてください。"}))
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    ans = "".join(f"<li>{e(x)}</li>" for x in _answer(it))
    others = [x for x in sibs if x is not it]
    sib = ('<ul class="hn-pref">' + "".join(f'<li><a href="{href_city(x)}">{e(x["name"])}</a></li>' for x in others) + "</ul>") if others else ""
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{SLUG}/">ペットと避難</a> › <a href="{href(pf)}">{e(pf)}</a> › {e(nm)}</nav>
    <h1><small>避難所で受け入れる動物・大型犬・ケージの決まり</small>{e(nm)}のペット同行避難</h1>
    <p class="lede">{e(nm)}（{e(pf)}）の公式ページに書いてある、ペットと避難するときの決まりです。書いていないことは「不明」としています（「受け入れない」という意味ではありません）。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    <div class="answer"><h2 id="answer">{e(nm)}のペットと避難のポイント</h2><ul>{ans}</ul></div>
    {fit}
    <h2 id="detail">{e(nm)}のくわしい決まり</h2>
    {card(e, it)}
    <h2 id="faq">よくある質問</h2>
    <dl class="emg-tips">{faq_html}</dl>
    <p class="emg-note">{e(CHECKED)}に{e(nm)}の公式ページで確かめた情報です。避難所の決まりは変わることがあり、災害の状況や避難所ごとにも違います。必ずリンク先でご確認ください。誤りは<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
  </article></div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>{e(pf)}のほかの市区町村</h2><p>{e(pf)}の決まりと、ほかの市区町村の決まりです。</p></div>
    <ul class="other"><li><a href="{href(pf)}">{e(pf)}のペット同行避難（県の決まりと一覧）</a></li></ul>
    {sib}
    <div class="sh"><h2>くわしい記事</h2><p>同行避難と同伴避難のちがい、持ち出し品のリストなど。</p></div>
    {_guides(e)}
    <ul class="other"><li><a href="/{SLUG}/">ペットと避難するとき（全国の一覧）</a></li><li><a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="/guide/lost-pet/">ペットが迷子になったら</a></li></ul>
  </div>
</section>
{_taxi(e, pf)}
</main>
""" + ctx["foot_noband"]()

def urls(SITE):
    bp = by_pref()
    ok = [pf for pf in bp if pref_ok(bp[pf])]
    return [f"{SITE}/{SLUG}/"] + [f"{SITE}{href(pf)}" for pf in ok] + [f"{SITE}{href_city(it)}" for pf in ok for it in bp[pf] if has_page(it)]

def write_all(ROOT, ctx):
    try:
        import thin_gate as TG
    except ImportError:
        TG = None
    for _ in range(4):
        _write(ROOT, ctx)
        if not TG: break
        mine = [p for p in TG.all_pages(ROOT) if p.startswith(f"/{SLUG}/") and p != f"/{SLUG}/"]
        n = TG.measure(ROOT, TG.all_pages(ROOT))
        low = [p for p in mine if n.get(p, 0) < TG.MIN_CHARS]
        if not low: break
        rev_p = {PSLUG[pf]: pf for pf in PSLUG}
        rev_c = {(PSLUG[pf], CSLUG[(pf, nm)]): (pf, nm) for (pf, nm) in CSLUG if pf in PSLUG}
        for p in low:
            parts = [x for x in p.split("/") if x]
            if len(parts) == 3 and (parts[1], parts[2]) in rev_c: THIN.add(rev_c[(parts[1], parts[2])])
            elif len(parts) == 2 and parts[1] in rev_p: PREF_THIN.add(rev_p[parts[1]])
    write_finder(ROOT)

def _write(ROOT, ctx):
    bp = by_pref()
    done = [pf for _, ps in ctx["emg_regions"] for pf in ps if pf in bp and pref_ok(bp[pf])]
    import shutil
    for d in os.listdir(os.path.join(ROOT, SLUG)) if os.path.isdir(os.path.join(ROOT, SLUG)) else []:
        if os.path.isdir(os.path.join(ROOT, SLUG, d)): shutil.rmtree(os.path.join(ROOT, SLUG, d))  # 前の作り直しの残り（薄くて外したページ）を消す
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    page = render_top(ctx)
    if "data-bf" in page: page = _bf(page)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(page)
    for pf in done:
        d = os.path.join(ROOT, SLUG, PSLUG[pf]); os.makedirs(d, exist_ok=True)
        page = _bf(render_pref(ctx, pf, bp[pf], done))
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)
        cities = sorted([x for x in bp[pf] if has_page(x)], key=lambda x: MUNI_ORDER.get((pf, x["name"]), 9999))
        for it in cities:
            cd = os.path.join(ROOT, SLUG, PSLUG[pf], CSLUG[(pf, it["name"])]); os.makedirs(cd, exist_ok=True)
            open(os.path.join(cd, "index.html"), "w", encoding="utf-8").write(_bf(render_city(ctx, pf, it, cities, done)))

def _bf(page):
    return page.replace("</head>", V.BF_CSS + "\n</head>", 1).replace("</body>", V.BF_JS + "\n</body>", 1)

# [B] Nori 2026-11-14「地域でフィルターして連絡できるようにしたほうがいいんじゃない？もしくはリンク貼ってそっちに飛ばすとか」：
# 都道府県 → 市区町村をえらぶと、全国1,741の市区町村のどれでも、当サイトのページ（あれば）か、確かめた公式ページ、
# なければその市区町村の公式サイトへ案内する。一覧は /hinan/munis.json（ページの重さに入れない。えらんだときだけ読む）。電話番号は出さない。
def write_finder(ROOT):
    bp = by_pref()
    have = {(it["pref"], it["name"]): it for its in bp.values() for it in its if it["kind"] == "city"}
    pref_page = {pf for pf in bp if pref_ok(bp[pf])}
    nf = set(NONE)
    out = {}
    for m in MUNI:
        pf, nm, top = m["pref"], m["name"], m.get("url") or ""
        it = have.get((pf, nm))
        if it and has_page(it) and pf in pref_page: row = [nm, "page", href_city(it), top]
        elif it and pf in pref_page: row = [nm, "card", href(pf) + "#" + nm, top]
        elif it: row = [nm, "link", it["links"][0][1], top, it["links"][0][0]]
        elif (pf, nm) in nf: row = [nm, "none", "", top]
        else: row = [nm, "todo", "", top]
        out.setdefault(pf, []).append(row)
    open(os.path.join(ROOT, SLUG, "munis.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))

FINDER_CSS = """<style>
.hn-find{background:#fff;border:2px solid var(--accent,#e8590c);border-radius:18px;padding:14px 16px;margin:12px 0 18px}
.hn-find h2{font-size:1.05rem;margin:0 0 8px}
.hn-find .row{display:flex;flex-wrap:wrap;gap:8px}
.hn-find select{flex:1 1 140px;min-width:0;font-size:1rem;padding:10px;border:1.5px solid var(--line);border-radius:12px;background:#fff}
.hn-find .out{margin-top:10px;line-height:1.8;font-size:.95rem}
.hn-find .out a{font-weight:700}
</style>"""

def finder(e, prefs, pf=None):
    opts = "".join(f'<option{" selected" if p == pf else ""}>{e(p)}</option>' for p in prefs)
    return FINDER_CSS + f"""<div class="hn-find" id="find"><h2>お住まいの市区町村の決まりをさがす</h2>
<p style="margin:0 0 8px;font-size:.9rem">全国の市区町村から、当サイトでまとめた決まりか、市区町村の公式サイトへご案内します。</p>
<div class="row"><select id="hnP" aria-label="都道府県"><option value="">都道府県をえらぶ</option>{opts}</select>
<select id="hnM" aria-label="市区町村" disabled><option value="">市区町村をえらぶ</option></select></div>
<div class="out" id="hnO" aria-live="polite"></div></div>
<script>(function(){{var P=document.getElementById('hnP'),M=document.getElementById('hnM'),O=document.getElementById('hnO'),D=null;
function esc(s){{return String(s).replace(/[&<>"]/g,function(c){{return{{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]}})}}
function fill(){{M.innerHTML='<option value="">市区町村をえらぶ</option>';O.innerHTML='';var L=D&&D[P.value]||[];L.forEach(function(r,i){{var o=document.createElement('option');o.value=i;o.textContent=r[0];M.appendChild(o)}});M.disabled=!L.length}}
function load(cb){{if(D)return cb();fetch('/{SLUG}/munis.json').then(function(r){{return r.json()}}).then(function(j){{D=j;cb()}}).catch(function(){{O.textContent='読み込めませんでした。時間をおいてお試しください。'}})}}
P.addEventListener('change',function(){{load(fill)}});if(P.value)load(fill);
M.addEventListener('change',function(){{var r=(D[P.value]||[])[M.value];if(!r){{O.innerHTML='';return}}var n=esc(r[0]),top=r[3]?'<a href="'+esc(r[3])+'" target="_blank" rel="noopener">'+n+'の公式サイト ↗</a>':'',h='';
if(r[1]=='page')h='<a href="'+esc(r[2])+'">'+n+'のペットと避難の決まりを見る</a>';
else if(r[1]=='card')h='<a href="'+esc(r[2])+'">'+n+'の決まり（'+esc(P.value)+'のページの中）を見る</a>';
else if(r[1]=='link')h=n+'の公式ページ：<a href="'+esc(r[2])+'" target="_blank" rel="noopener">'+esc(r[4]||'ペットと避難')+' ↗</a>';
else if(r[1]=='none')h=n+'の公式サイトには、ペットと避難について書いたページが見つかりませんでした。'+top+'の防災のページか、お問い合わせ（防災・危機管理の担当）でご確認ください。';
else h=n+'は、まだ当サイトで確かめていません。'+top+'で「ペット 避難」とさがすか、お問い合わせ（防災・危機管理の担当）でご確認ください。';
O.innerHTML=h;try{{gtag('event','hinan_find',{{pref:P.value,status:r[1]}})}}catch(e){{}}}})}})();</script>"""
