# お金を取らない情報ページ「全国の公営ドッグラン」（/dogrun/ と都道府県ごとの /dogrun/<slug>/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「全部マネタイズじゃなくていい。SEO的なコンテンツでもいい」「どんどん進めて」→ 同日「内容薄すぎじゃない？SEOちゃんとやってよ」で
# 都道府県ごとのページと、各ドッグランの料金・時間・休み・エリア・登録・必要なもの・駐車場・アクセスを足した。
# 守ること：国・都道府県・市町村の公園や施設のドッグランだけ（民間は載せない）。順位・おすすめなし。電話番号なし。
# 公式ページで確かめたことだけ書く（書いていない項目は出さない）。データ：tools/dogrun.json（src は参考にした公式ページ）。
import json, os
from urllib.parse import quote
import prefkeep
from prefs import PREFS

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dogrun.json"), encoding="utf-8"))
RUNS = J["dogruns"]
NONE = J.get("none", {})
NONE_SRC = J.get("none_src", {})
CHECKED = J["checked"]

SLUG = "dogrun"
PSLUG = {x[1]: x[0] for x in PREFS}
PSLUG.update({"東京都": "tokyo", "神奈川県": "kanagawa", "埼玉県": "saitama", "千葉県": "chiba"})
BY = {}
for _d in RUNS:
    BY.setdefault(_d["pref"], []).append(_d)
TOTAL = len(RUNS)

# 項目の名前（表示の順）
FIELDS = [("addr", "所在地"), ("place", "場所"), ("hours", "利用時間"), ("season", "開いている期間"), ("closed", "休み"),
          ("fee", "料金"), ("size", "エリア（犬の大きさ）"), ("reg", "利用登録"), ("need", "必要なもの・条件"),
          ("ng", "入れない犬など"), ("limit", "連れて入れる頭数"), ("parking", "駐車場"), ("access", "アクセス"), ("note", "ご注意")]

def fee_tag(d):
    f = d.get("fee", "")
    if not f: return None
    if f.startswith("無料"): return "無料"
    if f.startswith(("利用は無料", "ドッグランは無料")): return "利用は無料"
    return "有料"

def reg_tag(d):
    r = d.get("reg", "")
    if not r: return None
    return "登録なしで使える" if r.startswith("いらない") else "登録がいる"

def tags(d):
    t = []
    f = fee_tag(d)
    if f: t.append((f, f != "有料"))
    r = reg_tag(d)
    if r: t.append((r, r == "登録なしで使える"))
    if "小型犬" in d.get("size", ""): t.append(("小型犬エリアあり", False))
    if d.get("season"): t.append(("開く期間が決まっている", False))
    if d.get("resident"): t.append(("住民向け", False))
    return t

def tags_html(e, d):
    return '<ul class="dr-tags">' + "".join(('<li class="ok">' if ok else "<li>") + e(x) + "</li>" for x, ok in tags(d)) + "</ul>"

def place_text(d):
    return d.get("addr") or d.get("place") or d.get("city", "")

def nfree(rs): return sum(1 for d in rs if fee_tag(d) in ("無料", "利用は無料"))
def nnoreg(rs): return sum(1 for d in rs if reg_tag(d) == "登録なしで使える")
def nsmall(rs): return sum(1 for d in rs if "小型犬" in d.get("size", ""))
def nvac(rs): return sum(1 for d in rs if "ワクチン" in d.get("need", ""))
def nseason(rs): return sum(1 for d in rs if d.get("season"))

def stats(rs):
    li = [("", len(rs))] + [(lab, f(rs)) for lab, f in (("利用料が無料", nfree), ("登録なしで使える", nnoreg), ("小型犬エリアあり", nsmall))]
    return '<ul class="dr-stats">' + "".join(f"<li>{lab} <b>{n}</b>か所</li>" if lab else f"<li><b>{n}</b>か所</li>" for lab, n in li if n or not lab) + "</ul>"

def href(pf):
    return f"/{SLUG}/{PSLUG[pf]}/"

# ── 地域ページ（/tokyo/ や /area/osaka/）から使う一文 ──
def area_snippet(pf, e):
    rs = BY.get(pf, [])
    if not rs:
        return f'<h3>{e(pf)}のドッグラン</h3><p>{e(NONE.get(pf, "公式ページで確かめられる公営のドッグランは、まだ載せていません。"))}全国の公営ドッグランは<a href="/{SLUG}/">全国の公営ドッグランの一覧</a>にまとめています。</p>'
    names = "、".join(d["name"] for d in rs[:3])
    return (f'<h3>{e(pf)}の公営ドッグラン</h3><p>{e(pf)}には、公式ページで確かめた公営のドッグランが{len(rs)}か所あります（{e(names)}{"など" if len(rs) > 3 else ""}）。'
            f'料金・利用登録・利用時間・小型犬エリアの有無は<a href="{href(pf)}">{e(pf)}の公営ドッグラン</a>にまとめています。大型犬や何頭もいっしょで、車がないときはペットタクシーでも行けます。</p>')

# ── 共通の本文 ──
BEFORE = [
 ("利用登録がいるか", "公営のドッグランは、はじめに利用登録（WEB申請・窓口・登録会や説明会）がいるところが多いです。登録なしで使えるところもあります。市や町に住んでいる人だけが登録できるところもあります。"),
 ("持っていく書類", "多くのドッグランで、犬の鑑札（またはマイクロチップの登録証明）と、その年度の狂犬病予防注射済票が必要です。1年以内の混合ワクチン（3種や5種以上）の接種証明を求めるところもあります。"),
 ("入れない犬", "子犬（生後4か月や6か月未満など）、発情中の犬、病気やノミ・ダニのいる犬、人や犬をかむくせのある犬は、入れないことが多いです。犬種や頭数に決まりがあるところも。"),
 ("大きさのエリア", "小型犬用と中・大型犬用にエリアが分かれているところがあります。区切りは体重（8kg・10kgなど）や体高（25cm・40cm・50cmなど）で、場所ごとに違います。"),
 ("開いている日と時間", "日の出から日没まで、9時〜17時など、場所ごとに違います。開くのが土日だけ・日曜だけのところや、雪の多い地域では冬に閉めるところもあります。"),
]
BRING = ["リード（ドッグランの外では必ずつけます）", "うんち袋・ペットシーツ（ふんは持ち帰るのが基本です）", "飲み水と器、タオル",
         "登録証・鑑札・狂犬病予防注射済票（求められる場所では身につけさせます）", "混合ワクチンの接種証明の写し（求められる場所）",
         "夏は保冷グッズ、雨のあとは足をふくもの"]
MANNER = ["飼い主はいっしょに入り、犬から目を離さない。犬だけを残さない。", "入口の二重扉は、片方が閉まってから次を開ける。", "ふんは持ち帰り、おしっこは水で流す（水道がある場所）。",
          "おやつやおもちゃは、禁止のところが多いので決まりを確かめる。", "はじめての場所では、まず外から様子を見て、混んでいたら短い時間にする。", "ほかの犬とけんかになりそうなときは、すぐにリードをつけて外に出る。"]

def faq_common(e):
    rs = RUNS
    return [
      ("ドッグランを使うのに必要なものは？", f"多くの公営ドッグランで、犬の鑑札と、その年度の狂犬病予防注射済票が必要です。この一覧の{TOTAL}か所のうち{nvac(rs)}か所は、混合ワクチンの接種（証明）も条件にしています。事前の利用登録がいるところも多いので、行く前に公式ページを確かめてください。"),
      ("公営のドッグランは無料ですか？", f"この一覧の{TOTAL}か所のうち、公式ページに利用料が無料と書いてあるのは{nfree(rs)}か所です（登録料や公園の入園料・駐車料が別にかかるところを含みます）。1回200円〜500円ほどの有料のところや、登録料がかかるところもあります。"),
      ("登録なしで使えるドッグランはありますか？", f"あります。この一覧では{nnoreg(rs)}か所が、公式ページに登録はいらないと書いています。都道府県ごとのページでは「登録なしで使える」の印をつけています。"),
      ("鑑札と狂犬病予防注射済票はどこでもらえますか？", "犬の登録をすると市区町村から鑑札が、毎年の狂犬病予防注射を受けると注射済票がもらえます。くわしくは「ペットの迷子・犬の登録・引取りの窓口」のページにまとめています。"),
      ("小型犬と大型犬でエリアは分かれていますか？", f"この一覧の{TOTAL}か所のうち{nsmall(rs)}か所に、小型犬用のエリアがあります。区切りは体重や体高で、場所ごとに違います。"),
      ("冬も使えますか？", f"雪の多い地域では、冬に閉めるドッグランがあります。この一覧では{nseason(rs)}か所に、開いている期間の決まりがあります。"),
      ("民間のドッグランは載せていますか？", "このページは、国・都道府県・市町村の公園や施設にあるドッグランだけを、公式ページで確かめて載せています。民間のドッグランは載せていません。"),
      ("車がないときや、大型犬で遠くのドッグランに行くには？", "ペットタクシーで行けます。乗せられる犬の大きさや頭数は会社ごとに違います。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。"),
    ]

def faq_pref(e, pf, rs):
    q = []
    fr = [d["name"] for d in rs if fee_tag(d) in ("無料", "利用は無料")]
    if fr:
        q.append((f"{pf}で無料の公営ドッグランは？", f"公式ページに利用料が無料と書いてあるのは、{'、'.join(fr)}です（登録料や駐車料が別にかかるところもあります）。"))
    nr = [d["name"] for d in rs if reg_tag(d) == "登録なしで使える"]
    if nr:
        q.append((f"{pf}で登録なしで使える公営ドッグランは？", f"公式ページに登録はいらないと書いてあるのは、{'、'.join(nr)}です。鑑札や注射済票などの条件はあるので、行く前に確かめてください。"))
    sm = [d["name"] for d in rs if "小型犬" in d.get("size", "")]
    if sm:
        q.append((f"{pf}で小型犬エリアがあるドッグランは？", f"{'、'.join(sm)}に小型犬用のエリアがあります。区切りの体重や体高は場所ごとに違います。"))
    se = [d["name"] for d in rs if d.get("season")]
    if se:
        q.append((f"{pf}のドッグランは一年中使えますか？", f"{'、'.join(se)}は、開いている期間が決まっています。そのほかも、天気や工事・イベントで閉めることがあります。"))
    q.append((f"{pf}のドッグランへ、車がなくても行けますか？", "公共交通機関で行けるところもありますが、犬を連れて乗れるかは交通機関ごとに決まりがあります。大型犬や何頭もいっしょのときは、ペットタクシーを使う方法もあります。"))
    return q

def ld_json(objs):
    return '<script type="application/ld+json">\n' + json.dumps(objs, ensure_ascii=False, indent=1) + "\n</script>"

def faq_ld(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

def crumbs(SITE, items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}

def guide_html(e):
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    bring = "".join(f"<li>{e(x)}</li>" for x in BRING)
    manner = "".join(f"<li>{e(x)}</li>" for x in MANNER)
    return f'''<div class="emg-tips"><h4>ドッグランに行く前に確かめること</h4><dl>{before}</dl>
<p class="emg-tips-note">決まりは場所ごとに違います。ここに書いたのは多くのドッグランに共通する目安です。必ずリンク先の公式ページでご確認ください。</p></div>
<div class="emg-tips"><h4>持っていくもの</h4><ul>{bring}</ul></div>
<div class="emg-tips"><h4>はじめてでも安心な使い方とマナー</h4><ul>{manner}</ul>
<p class="emg-tips-note">夏の昼間は地面が熱くなります。朝や夕方の涼しい時間に、水を飲ませながら短めに遊ばせてあげてください。</p></div>'''

# ── 全国のページ（/dogrun/） ──
def render_hub(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    npref = len(BY)
    title = f"全国の公営ドッグラン{TOTAL}か所｜都道府県別・無料や登録なしもわかる一覧｜ペットタクシー予約窓口"
    desc = (f"国営・都道府県営・市町村の公園などにある公営のドッグラン{TOTAL}か所を、{npref}都道府県ごとにまとめた無料の一覧です。"
            "料金・利用登録・利用時間・小型犬エリア・駐車場を公式ページで確かめて載せています。持ち物やマナーも。")
    grid = ""
    for lab, prefs in ctx["emg_regions"]:
        cells = "".join((f'<li><a href="{href(pf)}">{e(pf)}<small>{len(BY[pf])}か所</small></a></li>' if pf in BY
                         else f'<li><span>{e(pf)}<small>—</small></span></li>') for pf in prefs)
        grid += f'<h3 class="dr-region">{e(lab)}</h3><ul class="dr-prefs">{cells}</ul>\n'
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            rs = BY.get(pf, [])
            if rs:
                inner = "".join(f'<div class="dr-row"><a href="{href(pf)}#{d["id"]}">{e(d["name"])}</a><small>{e(d.get("city", ""))}</small>{tags_html(e, d)}</div>' for d in rs)
                inner += f'<p class="emg-all"><a href="{href(pf)}">{e(pf)}の公営ドッグラン（料金・時間・登録のくわしい表）</a></p>'
            else:
                inner = f'<p class="emg-none">{e(NONE.get(pf, "まだ載せていません。"))}見つけしだい足します。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    faq = faq_common(e)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    ld = ld_json([
        crumbs(SITE, [("ペットタクシー予約窓口", SITE + "/"), ("全国の公営ドッグラン", url)]),
        {"@context": "https://schema.org", "@type": "ItemList", "name": "都道府県別の公営ドッグラン", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": f"{pf}の公営ドッグラン", "url": SITE + href(pf)} for i, pf in enumerate(p for _, ps in ctx["emg_regions"] for p in ps if p in BY)]},
        faq_ld(faq)])
    return ctx["head"](title, desc, url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › 全国の公営ドッグラン</nav>
    <h1><small>{npref}都道府県・{TOTAL}か所</small>全国の公営ドッグラン</h1>
    <p class="lede">思いきり走らせてあげたい。でも、どこにあるの？　国・都道府県・市町村の公園や施設にある公営のドッグランを、料金・利用登録・利用時間・エリアの区分つきで都道府県ごとにまとめました。</p>
    {stats(RUNS)}
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。公営（国・都道府県・市町村）のドッグランだけを、公式ページで確かめて載せています。民間のドッグランは載せていません。順番は都道府県ごとで、おすすめ順ではありません。</p>
      <h2 class="emg-h">都道府県からさがす</h2>
      {grid}
      {guide_html(e)}
      <h2 class="emg-h">全国の公営ドッグランの一覧</h2>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">{e(CHECKED)}に公式ページで確かめた情報です。工事やイベント、天気で閉まることがあり、利用の方法も変わることがあるので、行く前に必ずリンク先でご確認ください。掲載の内容の誤りや、載せてほしい公営のドッグランは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
{taxi_band(e)}
</main>
{prefkeep.LIST_JS}
""" + ctx["foot_noband"]()

def taxi_band(e, pf=None, pref_href=None):
    area = f'<li><a href="{pref_href(pf)}">{e(pf)}のペットタクシー</a></li>' if pf and pref_href else ""
    jich = f'/jichitai/#pref={quote(pf)}' if pf else "/jichitai/"
    night = f'/hospital/night/#pref={quote(pf)}' if pf else "/hospital/night/"
    return f'''<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>大型犬や多頭で、遠くのドッグランへ</h2><p>車がないとき、大型犬や何頭もいっしょのときは、ペットタクシーを予約できます（乗せられる犬の大きさや頭数は会社ごとに違います）。各社の公式サイトの料金表から計算した概算で、料金をくらべられます。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    <ul class="other">{area}<li><a href="/#form">ペットタクシーの料金をくらべる（無料）</a></li><li><a href="{jich}">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="{night}">夜間・救急の動物病院</a></li><li><a href="/guide/large-dog/">大型犬の移動のガイド</a></li><li><a href="/guide/multi-pet/">多頭で乗れるペットタクシー</a></li></ul>
  </div>
</section>'''

# ── 都道府県のページ（/dogrun/<slug>/） ──
def card(e, d):
    rows = "".join(f"<dt>{e(lab)}</dt><dd>{e(d[k])}</dd>" for k, lab in FIELDS if d.get(k))
    srcs = [u for u in d.get("src", []) if u != d["url"]]
    more = ("<small>あわせて確かめたページ：" + "、".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{i + 1}</a>' for i, u in enumerate(srcs)) + "</small>") if srcs else ""
    return (f'<section class="dr-card" id="{d["id"]}"><h2>{e(d["name"])}</h2><p class="dr-city">{e(d["pref"])}{e(d.get("city", ""))}</p>{tags_html(e, d)}'
            f'<dl>{rows}</dl><p class="dr-links"><a href="{e(d["url"])}" target="_blank" rel="noopener">公式ページで最新の情報を見る ↗</a>{more}</p></section>')

def render_pref(ctx, pf, rs):
    e, SITE = ctx["e"], ctx["SITE"]
    url = SITE + href(pf)
    n = len(rs)
    cities = []
    for d in rs:
        c = d.get("city", "")
        if c and c not in cities: cities.append(c)
    ctext = "・".join(cities[:3])
    title = f"{pf}の公営ドッグラン{n}か所｜無料・登録・利用時間の一覧" + (f"（{ctext}）" if ctext and len(ctext) <= 14 else "") + "｜ペットタクシー予約窓口"
    names = "、".join(d["name"] for d in rs[:2])
    desc = (f"{pf}にある公営のドッグラン{n}か所（{names}{'など' if n > 2 else ''}）を、公式ページで確かめた料金・利用登録・利用時間・"
            f"エリアの区分・駐車場つきでまとめました。利用料が無料は{nfree(rs)}か所。行く前に確かめることも。")
    if len(desc) > 160: desc = desc[:158] + "。"
    table = "".join(f'<tr><td><a href="#{d["id"]}">{e(d["name"])}</a></td><td>{e(d.get("city", ""))}</td><td>{e(fee_tag(d) or "—")}</td><td>{e({"登録なしで使える": "いらない", "登録がいる": "いる"}.get(reg_tag(d), "—"))}</td></tr>' for d in rs)
    cards = "".join(card(e, d) for d in rs)
    faq = faq_pref(e, pf, rs)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    # 同じ地方のほかの県
    region = next((ps for _, ps in ctx["emg_regions"] if pf in ps), [])
    near = "".join(f'<li><a href="{href(p)}">{e(p)}の公営ドッグラン</a></li>' for p in region if p != pf and p in BY)
    items = [{"@type": "ListItem", "position": i + 1, "url": f"{url}#{d['id']}", "name": d["name"]} for i, d in enumerate(rs)]
    ld = ld_json([
        crumbs(SITE, [("ペットタクシー予約窓口", SITE + "/"), ("全国の公営ドッグラン", f"{SITE}/{SLUG}/"), (f"{pf}の公営ドッグラン", url)]),
        {"@context": "https://schema.org", "@type": "ItemList", "name": f"{pf}の公営ドッグラン", "numberOfItems": n, "itemListElement": items},
        faq_ld(faq)])
    pref_href = ctx["pref_href"]
    return ctx["head"](title, desc, url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{SLUG}/">全国の公営ドッグラン</a> › {e(pf)}</nav>
    <h1><small>{n}か所・公式ページで確かめた情報</small>{e(pf)}の公営ドッグラン</h1>
    <p class="lede">{e(pf)}の公園や施設にある公営のドッグランを、料金・利用登録・利用時間・エリアの区分・駐車場つきでまとめました。行く前に、それぞれの公式ページで最新の情報を確かめてください。</p>
    {stats(rs)}
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    <p class="emg-free">この一覧は無料の情報です。公営（国・都道府県・市町村）のドッグランだけを載せていて、民間のドッグランは載せていません。順番はおすすめ順ではありません。書いていない項目は、公式ページに書いていなかったものです。</p>
    <div class="tbl"><table class="dr-tbl"><thead><tr><th>ドッグラン</th><th>市町村</th><th>料金</th><th>登録</th></tr></thead><tbody>{table}</tbody></table></div>
    {cards}
    {guide_html(e)}
    <div class="emg-tips"><h4>{e(pf)}のドッグラン よくある質問</h4><dl>{faq_html}</dl></div>
    <p class="emg-note">{e(CHECKED)}に公式ページで確かめた情報です。工事やイベント、天気で閉まることがあり、利用の方法や料金も変わることがあるので、行く前に必ずリンク先でご確認ください。掲載の内容の誤りや、載せてほしい公営のドッグランは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    <h2>ほかの地域の公営ドッグラン</h2>
    <ul class="other">{near}<li><a href="/{SLUG}/">全国の公営ドッグラン（都道府県の一覧）</a></li></ul>
  </article></div>
</section>
{taxi_band(e, pf, pref_href)}
</main>
{prefkeep.LINKS_JS}
""" + ctx["foot_noband"]()

def urls(SITE):
    return [f"{SITE}/{SLUG}/"] + [SITE + href(pf) for pf in BY]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render_hub(ctx))
    for pf, rs in BY.items():
        d = os.path.join(ROOT, SLUG, PSLUG[pf])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render_pref(ctx, pf, rs))
