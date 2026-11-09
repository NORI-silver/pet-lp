# [B] SEO：ドッグランを施設1つずつのページにする（/dogrun/<県>/<id>/）。試しの30施設。型は docs/facility-page.md。
# 戦略担当 2026-11-09（Nori「倍のスピードで」）：火葬30の結果を待たずにドッグランも30。確かめた項目5つ以上は下げない。
# 書くのは tools/dogrun.json の値（公式ページで確かめたこと）と、そこから数えたことだけ。書いていない項目は行ごと出さない。
# 電話番号・順位・おすすめは書かない。各ページに「このドッグランまでのペットタクシー」（facility_taxi。高速道路のSA・PAは外からは入れないので付けない）。
import json, os
import gen_dogrun as G

PSLUG = G.PSLUG
CHECKED = G.CHECKED
MAX = 30


def facts(d):
    return [(lab, d[k]) for k, lab in G.FIELDS if d.get(k)]


def pick():
    cand = {}
    for d in G.RUNS:
        if len(facts(d)) >= 5 and d.get("addr"):  # 確かめた項目5つ以上・所在地あり（docs/facility-page.md）
            cand.setdefault(d["pref"], []).append(d)
    for v in cand.values(): v.sort(key=lambda d: -len(facts(d)))
    order = sorted(cand, key=lambda p: -len(G.BY[p]))
    out, i = [], 0
    while len(out) < MAX and any(cand.values()):
        p = order[i % len(order)]
        if cand[p]: out.append(cand[p].pop(0))
        i += 1
    return out


PAGES = pick()
IDS = {d["id"] for d in PAGES}


def href(d): return f"/{G.SLUG}/{PSLUG[d['pref']]}/{d['id'].lower()}/"


def _iso(ck):
    import re
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", ck)
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else ""


def _addr(d):
    a = d.get("addr", "")
    return a if a.startswith(d["pref"]) else d["pref"] + a


def _cmp(e, d):
    same = G.BY[d["pref"]][:10]
    if len(same) < 3: return ""
    body = ""
    for x in same:
        nm = e(x["name"])
        if x["id"] == d["id"]: nm = f"<b>{nm}</b>"
        elif x["id"] in IDS: nm = f'<a href="{href(x)}">{nm}</a>'
        reg = {"登録なしで使える": "いらない", "登録がいる": "いる"}.get(G.reg_tag(x), "")
        body += (f"<tr><td>{nm}</td><td>{e(x.get('city', ''))}</td><td>{e(G.KLAB[G.kind(x)])}</td><td>{e(G.fee_tag(x) or '')}</td>"
                 f"<td>{e(reg)}</td><td>{'○' if G.is_small(x) else ''}</td><td>{'○' if x.get('parking') else ''}</td></tr>")
    return (f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">{e(d["pref"])}のほかのドッグランとくらべる</h2><div class="tbl"><table class="pp-tbl cmp"><thead><tr>'
            '<th>名前</th><th>市区町村</th><th>種類</th><th>料金</th><th>利用登録</th><th>小型犬エリア</th><th>駐車場の記載</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div><p class="emg-tips-note">公式ページに書いてあることだけで作った表です。空欄は「ない」ではなく、書いていない・分からないという意味です。並びは順位ではありません。</p></div>')


def _faq(d):
    nm, q = d["name"], []
    if d.get("fee"): q.append((f"{nm}の料金はいくらですか？", f"{nm}の料金は、公式ページによると「{d['fee']}」です（{CHECKED}に確認）。"))
    if d.get("reg"): q.append((f"{nm}は利用登録がいりますか？", f"{nm}の利用登録は、公式ページによると「{d['reg']}」です。"))
    if d.get("hours"): q.append((f"{nm}は何時から使えますか？", f"{nm}の利用時間は、公式ページによると「{d['hours']}」です" + (f"。休みは「{d['closed']}」です。" if d.get("closed") else "。")))
    if d.get("size"): q.append((f"{nm}に小型犬のエリアはありますか？", f"{nm}のエリアは、公式ページによると「{d['size']}」です。"))
    return q[:4]


def render(ctx, d):
    e, SITE = ctx["e"], ctx["SITE"]
    pf, slug, url, nm = d["pref"], PSLUG[d["pref"]], SITE + href(d), d["name"]
    k = G.kind(d)
    kname = {"公営": "公営のドッグラン", "民間": "お店・施設のドッグラン", "高速道路": "高速道路のSA・PAのドッグラン"}[k]
    tparts = [w for w, f in (("料金", "fee"), ("利用時間", "hours"), ("登録", "reg"), ("行き方", "access")) if d.get(f)]
    title = f"{nm}（{d.get('city', '')}）｜{'・'.join(tparts)}｜ペットタクシー予約窓口"
    lead1 = f"{nm}は、{pf}{d.get('city', '')}にある{kname}です（{CHECKED}に公式ページで確認）。"
    pts = [lead1]
    if d.get("fee"): pts.append(f"{nm}の料金は「{d['fee']}」です。")
    if d.get("hours"): pts.append(f"{nm}の利用時間は「{d['hours']}」です。")
    if d.get("reg"): pts.append(f"{nm}の利用登録は「{d['reg']}」です。")
    if d.get("size"): pts.append(f"{nm}のエリアは「{d['size']}」です。")
    pts = pts[:5]
    srcs = [d["url"]] + [u for u in d.get("src", []) if u != d["url"]]
    src_html = "、".join(f'<a href="{e(u)}" target="_blank" rel="noopener">公式ページ{"" if i == 0 else i + 1}</a>' for i, u in enumerate(srcs)) + f"（{e(CHECKED)}に確認）"
    rows = "".join(f'<tr><th scope="row">{e(lab)}</th><td>{e(v)}</td></tr>' for lab, v in facts(d))
    pt = "Park" if k == "公営" else "Place"
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "全国のドッグラン", "item": f"{SITE}/{G.SLUG}/"},
        {"@type": "ListItem", "position": 3, "name": f"{pf}のドッグラン", "item": f"{SITE}/{G.SLUG}/{slug}/"},
        {"@type": "ListItem", "position": 4, "name": nm, "item": url}]},
      {"@context": "https://schema.org", "@type": pt, "additionalType": "ドッグラン", "name": nm, "url": d["url"],
       "address": {"@type": "PostalAddress", "addressRegion": pf, "streetAddress": d.get("addr", ""), "addressCountry": "JP"}},
      {"@context": "https://schema.org", "@type": "WebPage", "name": nm, "url": url, "dateModified": _iso(CHECKED), "isBasedOn": d["url"]}],
      ensure_ascii=False, indent=1) + "\n</script>"
    taxi = ""
    if k != "高速道路":
        taxi = (f'<p style="margin:10px 0"><a class="btn" data-taxi-fac="1" href="/?pref={e(pf)}&amp;to={e(_addr(d))}#form" '
                f'onclick="if(window.gtag)gtag(\'event\',\'facility_taxi\',{{cat:\'dogrun\',id:\'{e(d["id"])}\',pref:\'{e(pf)}\'}})">このドッグランまでのペットタクシーの料金をくらべる →</a></p>'
                '<p class="emg-tips-note">大型犬や何頭もいっしょのときに。料金は各社の公式サイトの料金表をもとに計算した概算で、確定料金ではありません。</p>')
    faq_html = "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in _faq(d))
    css = ("<style>.emg .tbl{overflow-x:auto;max-width:100%}.pp-tbl th,.pp-tbl td{font-size:13px;padding:5px 6px;text-align:left;vertical-align:top}"
           ".pp-tbl.cmp td,.pp-tbl.cmp th{white-space:nowrap}.pp-tbl.cmp td:first-child{white-space:normal;min-width:9em}.fac-pts{margin:6px 0 4px;padding-left:1.2em}.fac-pts li{margin:3px 0}</style>")
    return ctx["head"](title, lead1, url, ld) + css + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{G.SLUG}/">全国のドッグラン</a> › <a href="/{G.SLUG}/{slug}/">{e(pf)}</a> › {e(nm)}</nav>
    <h1>{e(nm)}</h1>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips" style="margin-top:0"><h2 style="font-size:1.05em;margin:0 0 4px">要点</h2><ul class="fac-pts">{"".join(f"<li>{e(x)}</li>" for x in pts)}</ul></div>
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">公式ページで確かめたこと</h2><div class="tbl"><table class="pp-tbl"><thead><tr><th>項目</th><th>内容</th></tr></thead><tbody>{rows}</tbody></table></div>
      <p class="emg-tips-note">出どころ：{src_html}。書いていない項目は載せていません。変わることがあるので、出かける前に必ず公式ページでご確認ください。</p></div>
      {taxi}
      {_cmp(e, d)}
      {f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">よくある質問</h2><dl>{faq_html}</dl></div>' if faq_html else ''}
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">関連するページ</h2><ul class="other"><li><a href="/{G.SLUG}/{slug}/">{e(pf)}のドッグラン</a></li><li><a href="/{G.SLUG}/">全国のドッグラン</a></li><li><a href="/guide/large-dog/">大型犬の移動ガイド</a></li><li><a href="/hospital/night/{slug}/">{e(pf)}の夜間・救急の動物病院</a></li></ul></div>
      <p class="emg-free">当サイトは{e(nm)}とは別の運営で、お金をもらっていません。おすすめや順位ではありません。</p>
      <p class="emg-note">掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
</main>
""" + ctx["foot_noband"]()


def urls(SITE): return [SITE + href(d) for d in PAGES]


def write_all(ROOT, ctx):
    for d in PAGES:
        p = os.path.join(ROOT, href(d).strip("/"))
        os.makedirs(p, exist_ok=True)
        open(os.path.join(p, "index.html"), "w", encoding="utf-8").write(render(ctx, d))
