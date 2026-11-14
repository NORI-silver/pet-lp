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

CSS = "<style>.emg .tbl{overflow-x:auto;max-width:100%}.pp-nav{margin:4px 0;line-height:1.9}.pp-nav span{display:inline-block;min-width:5em;font-weight:bold;margin-right:6px}.pp-nav a,.pp-nav b{margin-right:10px;white-space:nowrap}.pp-facts{margin:6px 0 10px;padding-left:1.2em}.pp-tbl th,.pp-tbl td{font-size:13px;padding:4px 6px;text-align:center;white-space:nowrap}.pp-tbl td:first-child,.pp-tbl th:first-child{text-align:left;white-space:normal;min-width:9em}.pp-ans{font-size:inherit}.pp-ans .answer{margin:0 0 14px}.pp-ans>ul{margin:0 0 14px;padding-left:1.2em;line-height:1.8}</style>"

def table_html(e, cat, rs):
    """条件を1つの表でくらべる（○＝公式サイトに書いてある、空欄＝書いていない／分からない）。"""
    cols = cat.get("table")
    if not cols: return ""
    head = "<tr><th>名前</th>" + "".join(f"<th>{e(h)}</th>" for h, _ in cols) + "</tr>"
    body = "".join("<tr><td>" + e(it["name"]) + "</td>" + "".join(f"<td>{e(f(it) or '')}</td>" for _, f in cols) + "</tr>" for it in rs)
    return ('<div class="emg-tips"><h4>条件をくらべる</h4><div class="tbl"><table class="pp-tbl"><thead>' + head + '</thead><tbody>' + body +
            '</tbody></table></div><p class="emg-tips-note">○は公式サイトにはっきり書いてあること。空欄は「しない」ではなく、公式サイトに書いていない・分からないという意味です。</p></div>')


# [B] 2026-11-14 Nori「薄い記事は撲滅させてね。全部濃い記事にして」：一覧のデータに facts（k・v・src・checked、料金は yen・min・tax）が
# ある店・施設は、県のページに「料金・条件をくらべる」表と、料金の棒を出す。公式サイトに書いてあることだけ。書いていない項目は「—」。
def _fv(it, k):
    for f in it.get("facts", []):
        if f["k"] == k: return f
    return None
def _jd(d): return f"{int(d[:4])}年{int(d[5:7])}月{int(d[8:10])}日" if d and len(d) == 10 else (d or "")
def fact_table_html(e, cat, pf, rs):
    cols = cat.get("fact_cols")
    hs = [it for it in rs if it.get("facts")]
    if not cols or not hs: return ""
    import visual as _V
    def cell(it, ks):
        vs = [f["v"] for f in (_fv(it, k) for k in ks) if f]
        return e("／".join(vs)) if vs else "—"
    unit, name = cat["unit"], cat["name"]
    rows = "".join(f'<tr><th scope="row">{e(it["name"])}</th>' + "".join(f"<td>{cell(it, ks)}</td>" for _, ks in cols) + "</tr>" for it in hs)
    pk = cat.get("price_key", "料金")
    pr = sorted([(it, _fv(it, pk)) for it in hs if (_fv(it, pk) or {}).get("yen")], key=lambda x: x[1]["yen"])
    out = f'<div class="emg-tips" style="margin-top:0"><h4>{e(pf)}の{e(name)}の料金・条件をくらべる</h4>'
    out += (f'<p>載せている{len(rs)}{e(unit)}のうち{len(hs)}{e(unit)}について、公式サイトに書いてある料金・交通費・キャンセル料などをまとめました。'
            + (f'1回の料金を書いているのは{len(pr)}{e(unit)}です。' if pr else '') + '</p>')
    if len(pr) >= 2:
        tax = {"込": "税込", "抜": "税抜"}
        out += _V.bars({"title": cat.get("price_title", "いちばん短いコースの1回の料金（公式サイトの表示どおり）"),
                        "rows": [(it["name"], f["yen"], f'{f["yen"]:,}円' + (f'／{f["min"]}分' if f.get("min") else "") + (f'（{tax[f["tax"]]}）' if f.get("tax") in tax else ""))
                                 for it, f in pr],
                        "note": "店ごとにコースの時間・税の表示がちがうので、そのまま並べています。交通費・初回の費用は別です。"})
    dates = sorted({f.get("checked", "") for it in hs for f in it["facts"]})
    srcs = "".join(f'<li><a href="{e(it["url"])}" target="_blank" rel="noopener">{e(it["name"])}の公式サイト</a></li>' for it in hs)
    out += ('<div class="tbl"><table class="pp-tbl"><thead><tr><th>名前</th>' + "".join(f"<th>{e(lab)}</th>" for lab, _ in cols) +
            f'</tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="emg-tips-note">「—」は公式サイトに書いていない・見つからなかった項目です（「しない」という意味ではありません）。{_jd(dates[-1] if dates else "")}までに公式サイトで確かめました。料金は変わることがあるので、頼む前に必ず公式サイトでご確認ください。</p>'
            f'<details><summary>確かめた公式サイト</summary><ul>{srcs}</ul></details></div>')
    return out


# [B] 2026-11-14 Nori「老犬ホームとかほかの分野の記事もこのページのように答えみたいなことからはじめて、もっと視覚的に分かりやすく」：
# 県のページのいちばん上に「先に答え」の箱（よくある質問の上の3つを、問い→答えの形で）と、数字のタイル（件数・料金の幅・「◯／◯」の数）を出す。
# 答えの文は、よくある質問と同じ（このページだけの数・名前から作った文）。のこりの質問は下の「よくある質問」に出す。構造化データは全部。
import re as _re
def answer_html(e, cat, pf, rs, faq, facts):
    import visual as _V
    n, unit = len(rs), cat["unit"]
    tiles = [(f"{n}{unit}", f"{pf}で公式サイトを確かめた{cat['name']}")]
    pk = cat.get("price_key", "料金")
    ys = sorted(f["yen"] for f in (_fv(it, pk) for it in rs) if f and f.get("yen"))
    if len(ys) >= 2: tiles.append((f"{ys[0]:,}〜{ys[-1]:,}円", cat.get("price_tile", "公式サイトに書いてある料金の幅")))
    elif ys: tiles.append((f"{ys[0]:,}円", cat.get("price_tile", "公式サイトに書いてある料金")))
    rest = []
    for f in facts:
        m = _re.match(r"^(.+?)[：:]\s*(\d+)／(\d+)$", f)
        if m and int(m.group(2)) == 0: continue  # 0件は下の表で分かるので、答えの箱には出さない
        if m and len(tiles) < 4: tiles.append((f"{m.group(2)}／{m.group(3)}", m.group(1)))
        else: rest.append(f)
    def first(a):
        m = _re.match(r"^(.+?。)(?![）」])", a)
        return m.group(1) if m else a
    kv = "".join(f'<li><b class="k">{e(q)}</b>{e(first(a))}</li>' for q, a in faq[:3])
    more = ("<ul>" + "".join(f"<li>{e(x)}</li>" for x in rest) + "</ul>") if rest else ""
    return (f'<div class="art pp-ans"><div class="answer"><h2 id="answer">先に答え</h2><ul class="kv">{kv}</ul></div>'
            f'{_V.stats(tiles)}{more}</div>')

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
    title = cat["title_fn"](pf, rs, n) if cat.get("title_fn") else f'{pf}の{cat["title_word"]}｜{n}{unit}の一覧（{cat["title_tail"]}）｜ペットタクシー予約窓口'
    desc = cat["desc_fn"](pf, rs, n) if cat.get("desc_fn") else f'{pf}の{name}を{n}{unit}、公式サイトで確かめた内容だけでまとめた無料の一覧です。' + cat["desc_tail"]
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
    if cat.get("bf_keys") and n >= 3:  # うちの子（体重・猫）でしぼる。公式サイトに書いてある受け入れの決まりだけで分け、書いていない店・施設はいつも出す
        import visual as _V
        cards = _V.breeds({"title": f"うちの子で{cat['name']}をしぼる", "lead": cat.get("bf_lead", "受け入れる動物・大きさの決まりが公式サイトに書いてあるところは、それで分けています。書いていないところは、いつも表示します。"),
                           "rows": [{"k": cat["bf_keys"](it), "raw": cat["card"](e, it)} for it in rs]})
    facts_html = ("<ul class=\"pp-facts\">" + "".join(f"<li>{e(f)}</li>" for f in facts) + "</ul>") if facts else ""
    page = ctx["head"](title, desc, url, ld) + CSS + cat.get("css", "") + f"""
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
    {answer_html(e, cat, pf, rs, faq, facts)}
    <div class="emg">
      <p class="emg-free">{e(cat.get("free", "この一覧は無料の情報です。事業者からお金をもらっていません。おすすめ順や点数順ではありません。" + ("料金は公式サイトに書いてあるものだけを、確かめた日つきで載せています。" if any(it.get("facts") for it in rs) else "料金は載せていないので、それぞれに直接おたずねください。")))}</p>
      {fact_table_html(e, cat, pf, rs)}
      {cat["extra"](e, pf) if cat.get("extra") else ""}
      {cat["fac_chips"](e, pf) + chr(10) + "      " if cat.get("fac_chips") else ""}<section class="emg-pref" data-pref="{e(pf)}"><h2 style="font-size:1.15em">{e(cat.get("list_h", name))}（{e(pf)}・{n}{e(unit)}）</h2>{cards}</section>
      {table_html(e, cat, rs)}
      {cat["extra_after"](e, pf) if cat.get("extra_after") else ""}
      {near_html}
      <div class="emg-tips"><h4>{e(cat['before_title'])}</h4><dl>{"".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in cat['before'])}</dl></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      {pref_nav(cat, e, rows, ctx["emg_regions"], cur=pf)}{chr(10) + "      " + cat["fac_biz"](e) if cat.get("fac_biz") else ""}
      <p class="emg-note">当サイトとは別の事業者です（{e(cat['checked'])}に公式サイトで確かめた情報）。内容は変わることがあるので、頼む前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>{e(cat['taxi_h'])}</h2><p>{e(cat['taxi_p'])}当日の依頼もできます。</p></div>
    <ul class="other"><li><a href="/{cat['slug']}/">{e(cat['h1'])}</a></li>{"".join(f'<li><a href="{u}">{e(t)}</a></li>' for t, u in cat['links'])}</ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{prefkeep.LINKS_JS}
{'<script src="/reviews.js" defer></script>' if cat.get('reviews') else ''}{chr(10) + '<script src="/facility.js" defer></script>' if cat.get('fac_chips') else ''}
""" + ctx["foot_noband"]()
    if 'data-bf' in page:
        import visual as _V
        page = page.replace("</head>", _V.BF_CSS + "\n</head>", 1).replace("</body>", _V.BF_JS + "\n</body>", 1)
    return page

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
