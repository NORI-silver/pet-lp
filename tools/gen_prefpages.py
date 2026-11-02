# [B] SEO：情報ページ（老犬ホーム・出張トリミング・ドッグトレーナー・ペットシッター）の都道府県ごとのページ（/<カテゴリ>/<県のslug>/）。
# Nori 2026-11-02「SEOをまずは強化したいので、SEOと相性がよいものを優先」。「老犬ホーム 千葉」のような 地域×カテゴリ の検索で、
# その県の一覧だけのページが出るようにする（全国のページは1つのURLで、県の選択はブラウザの中だけだったため）。
# 中身は全国のページと同じデータ（公式サイトで確かめたことだけ）。県ごとの数・条件の数・よくある質問は自動で数える。順位・料金・電話番号なし。
# 1件もない県のページは作らない（全国のページに「まだ載せていません」と出る）。件数が少ない県は、同じ地方のほかの県のページへのリンクを出す。
import json, os
import gen_dogrun
import prefkeep

PSLUG = gen_dogrun.PSLUG

def href(cat, pf):
    return f"/{cat['slug']}/{PSLUG[pf]}/"

MIN = 2  # これより少ない県はページを作らない（1件だけのページは中身がうすいため）

def by_pref(cat):
    rows = {}
    for it in cat["items"]:
        for pf in it["prefs"]:
            rows.setdefault(pf, []).append(it)
    return {pf: rs for pf, rs in rows.items() if len(rs) >= cat.get("min", MIN)}

def urls(SITE, cat):
    return [f"{SITE}{href(cat, pf)}" for pf in by_pref(cat)]

def pref_nav(cat, e, rows, regions, cur=None):
    """全国のページ・県のページの下に出す、県のページへのリンク（地方ごと）。"""
    out = ""
    for lab, prefs in regions:
        ls = [f'<a href="{href(cat, pf)}">{e(pf)}（{len(rows[pf])}）</a>' if pf != cur else f'<b>{e(pf)}（{len(rows[pf])}）</b>' for pf in prefs if pf in rows]
        if ls: out += f'<p class="pp-nav"><span>{e(lab)}</span>{" ".join(ls)}</p>'
    return f'<div class="emg-tips"><h4>都道府県ごとの{e(cat["name"])}</h4>{out}</div>'

def _region_of(pf, regions):
    for lab, prefs in regions:
        if pf in prefs: return lab, prefs
    return "", []

CSS = "<style>.pp-nav{margin:4px 0;line-height:1.9}.pp-nav span{display:inline-block;min-width:5em;font-weight:bold;margin-right:6px}.pp-nav a,.pp-nav b{margin-right:10px;white-space:nowrap}.pp-facts{margin:6px 0 10px;padding-left:1.2em}.pp-tbl th,.pp-tbl td{font-size:13px;padding:4px 6px;text-align:center;white-space:nowrap}.pp-tbl td:first-child,.pp-tbl th:first-child{text-align:left;white-space:normal;min-width:9em}</style>"

def table_html(e, cat, rs):
    """条件を1つの表でくらべる（○＝公式サイトに書いてある、空欄＝書いていない／分からない）。"""
    cols = cat.get("table")
    if not cols: return ""
    head = "<tr><th>名前</th>" + "".join(f"<th>{e(h)}</th>" for h, _ in cols) + "</tr>"
    body = "".join("<tr><td>" + e(it["name"]) + "</td>" + "".join(f"<td>{e(f(it) or '')}</td>" for _, f in cols) + "</tr>" for it in rs)
    return ('<div class="emg-tips"><h4>条件をくらべる</h4><div class="tbl"><table class="pp-tbl"><thead>' + head + '</thead><tbody>' + body +
            '</tbody></table></div><p class="emg-tips-note">○は公式サイトにはっきり書いてあること。空欄は「しない」ではなく、公式サイトに書いていない・分からないという意味です。</p></div>')

def render_pref(ctx, cat, pf, rows):
    e, SITE = ctx["e"], ctx["SITE"]
    rs = rows[pf]
    n = len(rs)
    url = SITE + href(cat, pf)
    name, unit = cat["name"], cat["unit"]
    facts = [f for f in cat["facts"](rs) if f]
    lab, rprefs = _region_of(pf, ctx["emg_regions"])
    near = [p for p in rprefs if p != pf and p in rows]
    near_html = ""
    if near:
        near_html = (f'<p>{e(lab)}のほかの県：' + "、".join(f'<a href="{href(cat, p)}">{e(p)}の{e(name)}（{len(rows[p])}{e(unit)}）</a>' for p in near) + '</p>')
    title = f'{pf}の{cat["title_word"]}｜{n}{unit}の一覧（{cat["title_tail"]}）｜ペットタクシー予約窓口'
    desc = f'{pf}の{name}を{n}{unit}、公式サイトで確かめた内容だけでまとめた無料の一覧です。' + cat["desc_tail"]
    faq = cat["faq"](pf, rs, n)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": cat["h1"], "item": f'{SITE}/{cat["slug"]}/'},
        {"@type": "ListItem", "position": 3, "name": f"{pf}の{name}", "item": url}]},
      {"@context": "https://schema.org", "@type": "ItemList", "name": f"{pf}の{name}", "numberOfItems": n,
       "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": it["name"], "url": it["url"]} for i, it in enumerate(rs)]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, indent=1) + "\n</script>"
    cards = "".join(cat["card"](e, it) for it in rs)
    facts_html = ("<ul class=\"pp-facts\">" + "".join(f"<li>{e(f)}</li>" for f in facts) + "</ul>") if facts else ""
    return ctx["head"](title, desc, url, ld) + CSS + cat.get("css", "") + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{cat['slug']}/">{e(cat['h1'])}</a> › {e(pf)}</nav>
    <h1><small>{n}{e(unit)}・公式サイトで確かめた内容だけ</small>{e(pf)}の{e(name)}</h1>
    <p class="lede">{e(cat['lede'](pf, n))}</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">{e(cat.get("free", "この一覧は無料の情報です。事業者からお金をもらっていません。おすすめ順や点数順ではありません。料金は載せていないので、それぞれに直接おたずねください。"))}</p>
      {f'<div class="emg-tips" style="margin-top:0"><h4>{e(pf)}の{e(name)}のようす</h4>{facts_html}</div>' if facts_html else ''}
      {cat["extra"](e, pf) if cat.get("extra") else ""}
      <section class="emg-pref" data-pref="{e(pf)}"><h2 style="font-size:1.15em">{e(cat.get("list_h", name))}（{e(pf)}・{n}{e(unit)}）</h2>{cards}</section>
      {table_html(e, cat, rs)}
      {near_html}
      <div class="emg-tips"><h4>{e(cat['before_title'])}</h4><dl>{"".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in cat['before'])}</dl></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      {pref_nav(cat, e, rows, ctx["emg_regions"], cur=pf)}
      <p class="emg-note">当サイトとは別の事業者です（{e(cat['checked'])}に公式サイトで確かめた情報）。内容は変わることがあるので、頼む前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>{e(cat['taxi_h'])}</h2><p>{e(cat['taxi_p'])}当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    <ul class="other"><li><a href="/{cat['slug']}/">{e(cat['h1'])}</a></li>{"".join(f'<li><a href="{u}">{e(t)}</a></li>' for t, u in cat['links'])}</ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{prefkeep.LINKS_JS}
{'<script src="/reviews.js" defer></script>' if cat.get('reviews') else ''}
""" + ctx["foot_noband"]()

def write_all(ROOT, ctx, cat):
    rows = by_pref(cat)
    for pf in rows:
        d = os.path.join(ROOT, cat["slug"], PSLUG[pf])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render_pref(ctx, cat, pf, rows))

def link_national(ROOT, ctx, cat):
    """全国のページの県の見出しを県のページへのリンクにし、県のページの一覧を足す。"""
    import re
    e = ctx["e"]
    rows = by_pref(cat)
    p = os.path.join(ROOT, cat["slug"], "index.html")
    h = open(p, encoding="utf-8").read()
    def rep(m):
        pf = m.group(1)
        if pf not in rows: return m.group(0)
        return f'<section class="emg-pref" data-pref="{pf}"><h4><a href="{href(cat, pf)}">{pf}の{e(cat["name"])}（{len(rows[pf])}）</a></h4>'
    h = re.sub(r'<section class="emg-pref" data-pref="([^"]+)"><h4>[^<]+</h4>', rep, h)
    h = h.replace('<div class="emg-tips"', CSS + pref_nav(cat, e, rows, ctx["emg_regions"]) + '<div class="emg-tips"', 1)
    open(p, "w", encoding="utf-8").write(h)

def area_snippet(pf, e, cats):
    """地域ページ（/tokyo/・/area/<slug>/）から、その県の情報ページへのリンク。"""
    ls = []
    for cat in cats:
        rows = by_pref(cat)
        if pf in rows:
            ls.append(f'<a href="{href(cat, pf)}">{e(pf)}の{e(cat["name"])}（{len(rows[pf])}{e(cat["unit"])}）</a>')
    if not ls: return ""
    return f'<h3>{e(pf)}のペットのサービス</h3><p>公式サイトで確かめた一覧：' + "、".join(ls) + '。</p>'
