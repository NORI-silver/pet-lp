# [B] SEO：情報ページ（老犬ホーム・出張トリミング・ドッグトレーナー・ペットシッター）の都道府県ごとのページ（/<カテゴリ>/<県のslug>/）。
# Nori 2026-11-02「SEOをまずは強化したいので、SEOと相性がよいものを優先」。「老犬ホーム 千葉」のような 地域×カテゴリ の検索で、
# その県の一覧だけのページが出るようにする（全国のページは1つのURLで、県の選択はブラウザの中だけだったため）。
# 中身は全国のページと同じデータ（公式サイトの情報）。県ごとの数・条件の数・よくある質問は自動で数える。順位・料金・電話番号なし。
# 1件もない県のページは作らない（全国のページに「まだ載せていません」と出る）。件数が少ない県は、同じ地方のほかの県のページへのリンクを出す。
import json, os, re
import gen_dogrun
import prefkeep

PSLUG = gen_dogrun.PSLUG

def href(cat, pf):
    return f"/{cat['slug']}/{PSLUG[pf]}/"

MIN = 2  # これより少ない県はページを作らない（1件だけのページは中身がうすいため）

# [B] 2026-11-23 網羅で県の件数が増え、県のページが重くなった（tests/info-light.test.cjs の60KB）・長すぎてさがしにくい：
# 1つの県に SPLIT 件を超えて載せる分野は、CITY_MIN 件以上ある市区町村を市のページ /<分野>/<県>/<市>/ に分け、県のページには
# 市のページへのリンクと、のこりの市区町村のカードを出す。政令市の区は市にまとめる。slug は tools/municipalities.json。
SPLIT, CITY_MIN = 150, 12
_MUNI = None
def _muni():
    global _MUNI
    if _MUNI is None:
        _MUNI = {(m["pref"], m["name"]): m["slug"] for m in json.load(open(os.path.join(os.path.dirname(__file__), "municipalities.json"), encoding="utf-8"))}
    return _MUNI
def city_of(pf, it):
    c = (it.get("city") or "").strip()
    m = re.match(r"^(.+?市)", c) or re.match(r"^(.+?[区町村])", c)
    if not m: return None
    name = m.group(1)
    return name if (pf, name) in _muni() else None
def split_pref(cat, pf, rs):
    """（市のページ {市: 施設}, 県のページに残す施設）。件数が SPLIT 以下なら分けない。"""
    if len(rs) <= cat.get("split", SPLIT): return {}, rs
    g = {}
    for it in rs:
        c = city_of(pf, it)
        if c: g.setdefault(c, []).append(it)
    cities = {c: v for c, v in g.items() if len(v) >= cat.get("city_min", CITY_MIN) and (pf, c) not in cat.get("no_city", ())}  # no_city：中身が薄くなる市（新しい薄いページは作らない。県のページに載る）
    ids = {id(x) for v in cities.values() for x in v}
    return dict(sorted(cities.items(), key=lambda kv: -len(kv[1]))), [it for it in rs if id(it) not in ids]
def chref(cat, pf, c):
    return f"{href(cat, pf)}{_muni()[(pf, c)]}/"

def by_pref(cat):
    rows = {}
    for it in cat["items"]:
        for pf in it["prefs"]:
            rows.setdefault(pf, []).append(it)
    # no_page：件数は足りても中身が薄い県（新しい薄いページは作らない。全国のページには載る）
    return {pf: rs for pf, rs in rows.items() if len(rs) >= cat.get("min", MIN) and pf not in cat.get("no_page", ())}

def urls(SITE, cat):
    out = []
    for pf, rs in by_pref(cat).items():
        out.append(f"{SITE}{href(cat, pf)}")
        out += [f"{SITE}{chref(cat, pf, c)}" for c in split_pref(cat, pf, rs)[0]]
    return out

def pref_nav(cat, e, rows, regions, cur=None):
    """全国のページ・県のページの下に出す、県のページへのリンク（地方ごと）。"""
    out = ""
    for lab, prefs in regions:
        ls = [f'<a href="{href(cat, pf)}">{e(pf)}（{len(rows[pf])}）</a>' if pf != cur else f'<b>{e(pf)}（{len(rows[pf])}）</b>' for pf in prefs if pf in rows]
        if ls: out += f'<p class="pp-nav"><span>{e(lab)}</span>{" ".join(ls)}</p>'
    # 47県のリンクは何画面も使うので折りたたむ（AGENTS.md「品質の決まり」B5、Nori 2026-11-16）
    return f'<details class="emg-tips pp-fold"><summary><b>都道府県ごとの{e(cat["name"])}</b></summary>{out}</details>'

def _region_of(pf, regions):
    for lab, prefs in regions:
        if pf in prefs: return lab, prefs
    return "", []

CSS = "<style>.pp-fold summary{cursor:pointer;padding:4px 0}.pp-fold summary b{font-size:1rem}.emg .tbl{overflow-x:auto;max-width:100%}.pp-nav{margin:4px 0;line-height:1.9}.pp-nav span{display:inline-block;min-width:5em;font-weight:bold;margin-right:6px}.pp-nav a,.pp-nav b{margin-right:10px;white-space:nowrap}.pp-facts{margin:6px 0 10px;padding-left:1.2em}.pp-tbl th,.pp-tbl td{font-size:13px;padding:4px 6px;text-align:center;white-space:nowrap}.pp-tbl td:first-child,.pp-tbl th:first-child{text-align:left;white-space:normal;min-width:9em}.pp-ans{font-size:inherit}.pp-ans .answer{margin:0 0 14px}.pp-ans>ul{margin:0 0 14px;padding-left:1.2em;line-height:1.8}</style>"

def table_html(e, cat, rs):
    """条件を1つの表でくらべる（○＝公式サイトに書いてある、空欄＝書いていない／分からない）。"""
    cols = cat.get("table")
    if not cols: return ""
    head = "<tr><th>名前</th>" + "".join(f"<th>{e(h)}</th>" for h, _ in cols) + "</tr>"
    # スマホでは1行ずつのカードにして、○の項目だけを札で見せる（縦書きのような細い列にしない。Nori 2026-11-16「統一してー」）
    def _td(h, v):
        v = v or ""
        if not v: return '<td class="pp-no"></td>'
        if v == "○": return f'<td class="pp-ok" data-l="{e(h)}">○</td>'
        return f'<td class="pp-v" data-l="{e(h)}">{e(v)}</td>'
    body = "".join('<tr><td class="pp-n">' + e(it["name"]) + "</td>" + "".join(_td(h, f(it)) for h, f in cols) + "</tr>" for it in rs)
    css = ('<style>@media (max-width:640px){.pp-tbl thead{display:none}.pp-tbl,.pp-tbl tbody{display:block}'
           '.pp-tbl tr{display:block;padding:9px 0;border-bottom:1px solid #efe0d3}.pp-tbl td{display:none;border:0!important;padding:0!important}'
           '.pp-tbl td.pp-n{display:block;font-weight:700;margin:0 0 5px}'
           '.pp-tbl td.pp-ok{display:inline-block;font-size:0!important;color:transparent;margin:0 5px 5px 0}.pp-tbl td.pp-ok::before{content:"✓ " attr(data-l);font-size:.78rem;background:#e6f4ea;color:#1e7d4f;border-radius:999px;padding:2px 9px;font-weight:700}'
           '.pp-tbl td.pp-v{display:inline-block;font-size:.78rem;color:#5f5148;margin:0 8px 5px 0}.pp-tbl td.pp-v::before{content:attr(data-l) "：";color:#8a7b70}}</style>')
    return (css + '<div class="emg-tips"><h4>条件をくらべる</h4><div class="tbl"><table class="pp-tbl"><thead>' + head + '</thead><tbody>' + body +
            '</tbody></table></div><p class="emg-tips-note">○は公式サイトにはっきり書いてあること。空欄は「しない」ではなく、公式サイトに書いていない・分からないという意味です。</p></div>')


# [B] 2026-11-14 Nori「薄い記事は撲滅させてね。全部濃い記事にして」：一覧のデータに facts（k・v・src・checked、料金は yen・min・tax）が
# ある店・施設は、県のページに「料金・条件をくらべる」表と、料金の棒を出す。公式サイトの情報だけ。書いていない項目は「—」。
def _fv(it, k):
    for f in it.get("facts", []):
        if f["k"] == k: return f
    return None
def _jd(d): return f"{int(d[:4])}年{int(d[5:7])}月{int(d[8:10])}日" if d and len(d) == 10 else (d or "")
def fact_table_html(e, cat, pf, rs):
    cols = cat.get("fact_cols")
    if not cols: return ""
    hs = [it for it in rs if any(_fv(it, k) for _, ks in cols for k in ks)]  # 表の列にない事実（うちの子に合うかの文など）だけの施設は並べない
    if not hs: return ""
    if len(hs) > 60: return ""  # 施設が多い県は、カードと同じ中身の表でページが重くなるだけ（info-light の上限。中身は各カードにある）
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
            f'<p class="emg-tips-note">「—」は分からなかった項目です（「しない」という意味ではありません）。{_jd(dates[-1] if dates else "")}時点の情報です。料金は変わることがあるので、頼む前に必ず公式サイトでご確認ください。</p>'
            f'<details><summary>出どころの公式サイト</summary><ul>{srcs}</ul></details></div>')
    return out


# [B] 2026-11-14 Nori「老犬ホームとかほかの分野の記事もこのページのように答えみたいなことからはじめて、もっと視覚的に分かりやすく」：
# 県のページのいちばん上に「先に答え」の箱（よくある質問の上の3つを、問い→答えの形で）と、数字のタイル（件数・料金の幅・「◯／◯」の数）を出す。
# 答えの文は、よくある質問と同じ（このページだけの数・名前から作った文）。のこりの質問は下の「よくある質問」に出す。構造化データは全部。
def _before_html(cat, e, pf):
    if cat.get("before_html"): return cat["before_html"](e, pf)
    if not cat.get("before"): return ""
    dl = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in cat["before"])
    return f'<div class="emg-tips"><h4>{e(cat["before_title"])}</h4><dl>{dl}</dl></div>'

import re as _re
def answer_html(e, cat, pf, rs, faq, facts):
    import visual as _V
    n, unit = len(rs), cat["unit"]
    tiles = [(f"{n}{unit}", f"{pf}で、この一覧に載せている{cat['name']}")]
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
    return (f'<div class="art pp-ans"><div class="answer"><h2 id="answer">{e(pf)}の{e(cat["name"])}のポイント</h2><ul class="kv">{kv}</ul></div>'
            f'{_V.stats(tiles)}{more}</div>')

# [B] 2026-11-16 GSC：県のページが「料金」の検索で出てもクリックが少ない。説明文で、公式サイトに書いてあるいちばん安い1回の料金を先に答える。
def _price_lead(cat, rs):
    # 老犬ホームは月の料金で入所金などの形がまちまち、しつけは計測中なので出さない
    lab = {"trimming": "コース", "pet-sitter": "1回"}.get(cat.get("slug"))
    if not lab: return ""
    pk = cat.get("price_key", "料金")
    pr = sorted([(it, _fv(it, pk)) for it in rs if (_fv(it, pk) or {}).get("yen")], key=lambda x: x[1]["yen"])
    if not pr: return ""
    it, f = pr[0]
    tax = {"込": "（税込）", "抜": "（税抜）"}.get(f.get("tax"), "")
    mins = f"・{f['min']}分" if f.get("min") else ""
    if len(pr) == 1:
        return f'料金が公式サイトにある{it["name"]}は、{lab}{f["yen"]:,}円{tax}{mins}から。'
    return f'料金が公式サイトにある{len(pr)}{cat["unit"]}では、{it["name"]}の{lab}{f["yen"]:,}円{tax}{mins}がいちばん手ごろ。'
def _with_price(cat, rs):
    lead = _price_lead(cat, rs)
    if not lead: return cat["desc_tail"]
    return lead + "順位はつけていません。"
def render_pref(ctx, cat, pf, rows, city=None):
    e, SITE = ctx["e"], ctx["SITE"]
    cities, rest = split_pref(cat, pf, rows[pf])
    if city:
        rs = cities[city]; show = rs; cities = {}
    else:
        rs = rows[pf]; show = rest
    n = len(rs)
    url = SITE + (chref(cat, pf, city) if city else href(cat, pf))
    place = city or pf
    name, unit = (cat["name_fn"](pf) if cat.get("name_fn") else cat["name"]), cat["unit"]
    facts = [f for f in cat["facts"](rs) if f and not re.search(r"：\d+／\d+$", f)]  # 「猫も受ける施設：3／5」のような運営側の集計は出さない（2026-11-16 スマホ点検）
    lab, rprefs = _region_of(pf, ctx["emg_regions"])
    near = [p for p in rprefs if p != pf and p in rows]
    near_html = ""
    if near:
        near_html = (f'<p>{e(lab)}のほかの県：' + "、".join(f'<a href="{href(cat, p)}">{e(p)}の{e(name)}（{len(rows[p])}{e(unit)}）</a>' for p in near) + '</p>')
    if city:
        sib = [c for c in split_pref(cat, pf, rows[pf])[0] if c != city]
        near_html = (f'<p><a href="{href(cat, pf)}">{e(pf)}の{e(name)}（{len(rows[pf])}{e(unit)}）</a>' + ("・同じ県の市：" + "、".join(f'<a href="{chref(cat, pf, c)}">{e(c)}</a>' for c in sib) if sib else "") + '</p>')
    city_links = ""
    if cities:
        city_links = (f'<div class="emg-tips pp-cities"><h2 style="font-size:1.05em;margin:0 0 6px">市区町村からさがす</h2><p class="pp-nav">' +
                      " ".join(f'<a href="{chref(cat, pf, c)}">{e(c)}（{len(v)}）</a>' for c, v in cities.items()) +
                      f'</p><p class="emg-tips-note">上の市区町村は、それぞれのページに載せています。下は{e(pf)}のほかの市区町村です。</p></div>')
    title = cat["title_fn"](place, rs, n) if cat.get("title_fn") else f'{place}の{cat["title_word"]}｜{n}{unit}の一覧（{cat["title_tail"]}）｜ペットタクシー予約窓口'
    desc = cat["desc_fn"](place, rs, n) if cat.get("desc_fn") else f'{place}の{name}を{n}{unit}、公式サイトの情報をもとにまとめた無料の一覧です。' + _with_price(cat, rs)
    seo = cat.get("pref_overrides", {}).get(pf, {}) if not city else {}
    if seo.get("title"): title = seo["title"]
    if seo.get("desc"): desc = seo["desc"]
    faq = cat["faq"](place, rs, n)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": cat["h1"], "item": f'{SITE}/{cat["slug"]}/'},
        {"@type": "ListItem", "position": 3, "name": f"{pf}の{name}", "item": SITE + href(cat, pf)}] + ([{"@type": "ListItem", "position": 4, "name": f"{place}の{name}", "item": url}] if city else [])},
      {"@context": "https://schema.org", "@type": "ItemList", "name": f"{place}の{name}", "numberOfItems": len(show),
       "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": it["name"], "url": it["url"]} for i, it in enumerate(show[:100])]},  # 100件まで（構造化データのスクリプトが24KBを超えないように）
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, separators=(",", ":")) + "\n</script>"
    cards = "".join(cat["card"](e, it) for it in show)
    import faccard as _FC
    if cat.get("bf_keys") and n >= 3 and cat["slug"] not in _FC.DIRS:  # 施設カードの分野は「うちの子に合うところをさがす」（tools/faccard.py）にまとめた  # うちの子（体重・猫）でしぼる。公式サイトに書いてある受け入れの決まりだけで分け、書いていない店・施設はいつも出す
        import visual as _V
        cards = _V.breeds({"title": f"うちの子で{cat['name']}をしぼる", "lead": cat.get("bf_lead", "受け入れる動物・大きさの決まりが公式サイトに書いてあるところは、それで分けています。書いていないところは、いつも表示します。"),
                           "rows": [{"k": cat["bf_keys"](it), "raw": cat["card"](e, it)} for it in show]})
    facts_html = ("<ul class=\"pp-facts\">" + "".join(f"<li>{e(f)}</li>" for f in facts) + "</ul>") if facts else ""
    page = ctx["head"](title, desc, url, ld) + CSS + cat.get("css", "") + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{cat['slug']}/">{e(cat['h1'])}</a> › {(f'<a href="{href(cat, pf)}">{e(pf)}</a> › {e(city)}' if city else e(pf))}</nav>
    <h1><small>{n}{e(unit)}・公式サイトの情報をもとに</small>{e(place)}の{e(name)}</h1>
    <p class="lede">{e(cat['lede'](place, n))}</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">{e(cat.get("free", "この一覧は無料の情報です。事業者からお金をもらっていません。おすすめ順や点数順ではありません。" + ("料金は公式サイトに書いてあるものだけを、情報の時点つきで載せています。" if any(it.get("facts") for it in rs) else "料金は載せていないので、それぞれに直接おたずねください。")))}</p>
      {seo["section"] + chr(10) + "      " if seo.get("section") else ""}{cat["extra"](e, pf) if cat.get("extra") else ""}{city_links}
      {cat["fac_chips"](e, pf) + chr(10) + "      " if cat.get("fac_chips") else ""}<section class="emg-pref" data-pref="{e(pf)}"><h2 style="font-size:1.15em">{e(cat.get("list_h", name))}（{e(place)}・{len(show)}{e(unit)}{'・ほかの市区町村' if cities else ''}）</h2>{cards}</section>
      {answer_html(e, cat, place, rs, faq, facts)}
      {table_html(e, cat, show)}
      {fact_table_html(e, cat, place, show)}
      {cat["extra_after"](e, pf) if cat.get("extra_after") else ""}
      {near_html}
      {_before_html(cat, e, pf)}
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      {pref_nav(cat, e, rows, ctx["emg_regions"], cur=pf)}{chr(10) + "      " + cat["fac_biz"](e) if cat.get("fac_biz") else ""}
      <p class="emg-note">当サイトとは別の事業者です（{e(cat['checked'])}時点の情報）。内容は変わることがあるので、頼む前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
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
        for c in split_pref(cat, pf, rows[pf])[0]:
            cd = os.path.join(d, _muni()[(pf, c)])
            os.makedirs(cd, exist_ok=True)
            open(os.path.join(cd, "index.html"), "w", encoding="utf-8").write(render_pref(ctx, cat, pf, rows, city=c))

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
    return f'<h3>{e(pf)}のペットのサービス</h3><p>載せている一覧：' + "、".join(ls) + '。</p>'
