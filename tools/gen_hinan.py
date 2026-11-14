# [B] SEO：ペットと避難（同行避難）の一覧 /hinan/ と、都道府県ごとのページ /hinan/<県>/。gen_areas.py が読み込んで使う。
# Nori 2026-11-14「シェルターとか避難所に関する記事を書いて。地域ごとも」「受け入れ可能な動物、サイズの規定とかも含めて」。
# 守ること：都道府県・市区の公式ページに書いてあることだけ（tools/hinan.json、出どころと確認日つき）。書いていないことは「書いていない」。
#   避難所の一覧は作らない（公式の一覧・地図へのリンクだけ）。電話番号は載せない。順位・おすすめなし。
#   ペットタクシーの話は、下の「前もって預け先へ移すとき」の節だけ（tools/taxi_cta.py がボタンを足す）。
# 人口の多い県から順に足す（第1弾 2026-11-14：東京都・神奈川県・大阪府・愛知県・埼玉県）。
import json, os
import gen_dogrun
import visual as V
from guides_hinan import HINAN_GUIDES, ITEMS, CHECKED, MARK, table_rows, N, N_CAGE

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
        {"k": ["s"], "h": "小型犬（10kg未満）", "items": [line(it, flag(it, "dog") + ("。" + it["cage"] if it.get("cage") else "")) for it in its]},
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
    done = [pf for _, ps in ctx["emg_regions"] for pf in ps if pf in bp]
    rest = [pf for _, ps in ctx["emg_regions"] for pf in ps if pf not in bp]
    title = "ペットの同行避難と避難所の決まり｜受け入れる動物・大型犬・ケージ（都道府県・市区ごと）｜ペットタクシー予約窓口"
    desc = (f"ペットと避難するときの「同行避難」と「同伴避難」のちがい、避難所で受け入れる動物（犬・猫・うさぎ・小鳥・爬虫類）、大型犬の扱い、ケージの決まりを、"
            f"{'・'.join(done)}の{N}の都県・市区の公式ページからまとめました。持ち出し品と、ペットを受け入れる避難所の調べ方も。")
    faq = HINAN_GUIDES[0]["faq"][:6]
    ld = _ld(SITE, url, "ペットの同行避難と避難所の決まり", desc, [("ペットタクシー予約窓口", "/"), ("ペットと避難", f"/{SLUG}/")], faq)
    stats = V.stats([(f"{N}", "確かめた都県・市区"), (f"{N_CAGE}", "ケージを持っていく・入れると書いている"),
                     (f"{sum(1 for x in ITEMS if x['flags'].get('cat') == 'yes')}", "猫を受け入れると書いている"), ("0", "体重・寸法の数字で決めている")])
    secs = "".join(f'<h3 class="emg-region">{e(pf)}</h3>' + "".join(card(e, it) for it in bp[pf]) for pf in done)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › ペットと避難</nav>
    <h1><small>同行避難・同伴避難・避難所で受け入れる動物の決まり</small>ペットと避難するとき</h1>
    <p class="lede">災害のときは、ペットを連れて避難するのが原則です（同行避難）。ただし、避難所で同じ部屋にいられるとは限らず、受け入れる動物や飼う場所は市区町村・避難所ごとに違います。都県・市区の公式ページに書いてあることを、そのまままとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    <div class="answer"><h2 id="answer">先に答え</h2>
    <ul class="kv"><li><b class="k">同行避難</b>ペットを連れて避難所などまで逃げること。同じ部屋で過ごせるという意味ではない（環境省）</li>
    <li><b class="k">同伴避難</b>避難所で飼い主がペットを飼って世話をしている状態。これも同じ部屋とは限らない（環境省）</li>
    <li><b class="k">連れて行ける動物</b>犬・猫は多くの自治体が受け入れる。うさぎ・小鳥・爬虫類は自治体で違う</li>
    <li><b class="k">大型犬</b>受け入れないと書いた自治体はなかった。ケージに入らなければリードでつなぐ市も（川崎市・大阪市）</li>
    <li><b class="k">ケージ</b>飼い主が持っていくのが基本。避難所にペット用の備蓄はないと書く市が多い</li></ul></div>
    {stats}
    <h2 id="table">自治体ごとの受け入れる動物（一覧）</h2>
    <p>○は受け入れると書いてある、△はむずかしい場合がある・一部は受け入れない、—は書いていない、です（{e(CHECKED)}に各自治体の公式ページで確認）。</p>
    {V.block(("table", table_rows()))}
    <h2 id="pref">都道府県ごとのくわしい決まり</h2>
    {_pref_links(e, done)}
    <p class="hn-none">ほかの道府県（{e("・".join(rest[:6]))}など）は、人口の多い県から順に足していきます。それまでは、お住まいの市区町村のホームページで「ペット 避難」と検索すると、受け入れの決まりが見つかることがあります。</p>
  </article></div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="emg">
      <h2 class="sh" id="list" style="scroll-margin-top:90px">都県・市区ごとの公式の決まり</h2>
      <p class="emg-free">それぞれの公式ページに書いてあることだけを載せています。書いていないことは「公式ページに書いていません（不明）」としています（「受け入れない」という意味ではありません）。</p>
      {secs}
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
    names = "・".join(it["name"] for it in its if it["kind"] == "city")
    title = f"{pf}のペット同行避難｜避難所で受け入れる動物・大型犬・ケージの決まり（{names}）｜ペットタクシー予約窓口" if names else \
            f"{pf}のペット同行避難｜避難所で受け入れる動物・大型犬・ケージの決まり｜ペットタクシー予約窓口"
    desc = (f"{pf}でペットと避難するときの決まりを、{'・'.join(it['name'] for it in its)}の公式ページからまとめました。避難所で受け入れる動物（犬・猫・うさぎ・小鳥・爬虫類）、"
            f"大型犬の扱い、ケージ・リード・ワクチン、避難所で飼う場所、受付の手続き、ペットを受け入れる避難所の調べ方。")
    faq = faq_for(pf, its)
    ld = _ld(SITE, url, f"{pf}のペット同行避難と避難所の決まり", desc,
             [("ペットタクシー予約窓口", "/"), ("ペットと避難", f"/{SLUG}/"), (pf, href(pf))], faq)
    rows = [["自治体", "犬", "大型犬", "猫", "小動物・鳥", "ケージ持参"]] + [
        [it["name"], MARK[it["flags"].get("dog")], MARK[it["flags"].get("large")], MARK[it["flags"].get("cat")],
         MARK[it["flags"].get("small") or it["flags"].get("bird")], "要" if it.get("cage_req") else "—"] for it in its]
    fit = V.block(("breeds", {"title": f"うちの子の大きさ・種類で、{pf}の決まりを見る", "rows": fit_rows(its),
                              "lead": f"{'・'.join(it['name'] for it in its)}の公式ページに書いてあることを、大きさ・種類ごとに並べました。",
                              "note": "書いていない自治体も「受け入れない」という意味ではありません。避難所ごとの決まりもあるので、お住まいの市区町村で確かめてください。"}))
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    cities = [it for it in its if it["kind"] == "city"]
    lede = (f"{pf}と{'・'.join(x['name'] for x in cities)}の公式ページに書いてある、ペットと避難するときの決まりです。" if cities else
            f"{pf}の公式ページに書いてある、ペットと避難するときの決まりです。") + \
           "避難所で受け入れる動物や飼う場所は、市区町村・避難所ごとに違います。ここにない市区町村にお住まいの方は、お住まいの市区町村のページでご確認ください。"
    pol = its[0].get("policy") or ""
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
    <div class="answer"><h2 id="answer">先に答え</h2><p>{e(pol)}</p></div>
    <h2 id="table">受け入れる動物とケージ（自治体ごと）</h2>
    <p>○は受け入れると書いてある、△はむずかしい場合がある・一部は受け入れない、—は書いていない、です（{e(CHECKED)}に確認）。</p>
    {V.block(("table", rows))}
    {fit}
    <h2 id="detail">自治体ごとのくわしい決まり</h2>
    {"".join(card(e, it) for it in its)}
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

def urls(SITE):
    return [f"{SITE}/{SLUG}/"] + [f"{SITE}{href(pf)}" for pf in by_pref()]

def write_all(ROOT, ctx):
    bp = by_pref()
    done = [pf for _, ps in ctx["emg_regions"] for pf in ps if pf in bp]
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    page = render_top(ctx)
    if "data-bf" in page: page = _bf(page)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(page)
    for pf in done:
        d = os.path.join(ROOT, SLUG, PSLUG[pf]); os.makedirs(d, exist_ok=True)
        page = _bf(render_pref(ctx, pf, bp[pf], done))
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)

def _bf(page):
    return page.replace("</head>", V.BF_CSS + "\n</head>", 1).replace("</body>", V.BF_JS + "\n</body>", 1)
