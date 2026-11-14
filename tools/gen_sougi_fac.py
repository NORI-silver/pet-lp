# [B] SEO：ペット火葬場・霊園を施設1つずつのページにする（/sougi/<県>/<id>/）。試しの30施設。
# 戦略担当 2026-11-08「月間100万PVを最短で」の打ち手1（公式サイトで確かめた施設を施設ページに）。品質の関門：
#  確かめた項目が3つ以上（市区町村・できること・料金の例）・出どころ（公式サイト）と確認日を書く・週200ページまで・4週後の登録率6割を見てから広げる。
# 書くのは tools/sougi_facilities.json の値（公式サイトで確かめた名前・市区町村・できること・料金の例）と、そこから数えたことだけ。
# 電話番号・番地・順位・おすすめは書かない。書いていないこと＝「しない」ではなく「公式サイトに書いていない」。言い方はやさしく。
# 各ページに「ここまでのペットタクシー」（facility.js の facility_taxi）・問い合わせ文（copy_inquiry）・口コミの星（reviews.js）。
import json, os
import gen_dogrun, gen_sougi
import facility_cards as FC
import guides_sougi as GS

PSLUG = gen_dogrun.PSLUG
F = gen_sougi.F["facilities"]
CHECKED = gen_sougi.F["checked"]

MAX = 30  # 試しの数（4週後の登録率を見てから広げる）
SVC = [("合同火葬", "合同火葬", "ほかの子と一緒に火葬。お骨は返らないことが多い"),
       ("個別火葬", "個別火葬", "1体ずつ火葬して、お骨を返してもらえる"),
       ("立ち会い火葬", "立ち会い火葬", "家族が火葬に立ち会い、お骨を拾える"),
       ("お迎え", "お迎え", "家まで迎えに来てくれる"),
       ("訪問火葬", "訪問火葬", "火葬の車で家の近くまで来て火葬する"),
       ("霊園", "霊園", "お墓・埋葬の場所がある"),
       ("納骨堂", "納骨堂", "建物の中にお骨を納める場所がある"),
       ("納骨", "納骨", "お骨を納める・合同の供養ができる")]
TYP = [("kobetsu", "個別火葬（おまかせ）", GS.SK), ("tachiai", "立ち会い火葬", GS.ST), ("goudou", "合同火葬", GS.SG)]


def _has(f, w): return w in f.get("kinds", []) or w in f.get("services", [])


def checked(f): return f.get("checked", CHECKED)


def facts(f):
    """事実の表（項目・内容）。公式サイトに書いてあることだけ。書いていない項目は行ごと出さない。docs/facility-page.md の型。"""
    out = [("所在地", f"{f['pref']}{f['city']}")] if f.get("city") else []
    for k, lab, note in SVC:
        if _has(f, k): out.append((lab, f"あり（{note}）"))
    if f.get("price"): out.append(("料金の例", f["price"]))
    # [B] 11/14 Nori「めちゃめちゃ濃くして」：施設ページだけに出す、公式サイトで確かめた項目（{"k","v"}）
    out += [(x["k"], x["v"]) for x in f.get("more", [])]
    return out


def _n_items(f): return len(facts(f))


def pick():
    """料金の例があり、確かめた項目が多い施設を、県が偏らないように順に選ぶ。県のページがある県だけ。"""
    import gen_prefcats, gen_prefpages
    rows = gen_prefpages.by_pref(gen_prefcats.SOUGI)
    cand = {}
    for f in F:
        if f["pref"] in rows and f.get("price") and GS._prices(f["price"]) and _n_items(f) >= 5:  # 確かめた項目5つ以上（docs/facility-page.md）
            cand.setdefault(f["pref"], []).append(f)
    for v in cand.values(): v.sort(key=lambda f: -_n_items(f))
    order = sorted(cand, key=lambda p: -len(rows[p]))
    out, i = [], 0
    while len(out) < MAX and any(cand.values()):
        p = order[i % len(order)]
        if cand[p]: out.append(cand[p].pop(0))
        i += 1
    return out


# 11/14 時点の30施設を固定（項目を足しても入れかわらないように）。広げるときはここに足す。
FIXED = ['Scd0216', 'S1a0483', 'S220475', 'Sfd6400', 'S606eea', 'S48f666', 'S5299d7', 'Se1d99a', 'Se1bf8d', 'S523e5a', 'Sdcb9a8', 'S33db8a', 'S50a5de', 'S136c61', 'S57a0db', 'S0b9ae7', 'S7edcb4', 'S56057f', 'Sdbddec', 'S78a99f', 'Sa4611d', 'Sd0edb1', 'S70883b', 'See9362', 'Sf408b4', 'S495b9e', 'Saf555c', 'S11b65d', 'Sc158a2', 'S61877c']
_BYID = {f["id"]: f for f in F}
PAGES = [_BYID[i] for i in FIXED if i in _BYID]
IDS = {f["id"] for f in PAGES}


def href(f): return f"/sougi/{PSLUG[f['pref']]}/{f['id'].lower()}/"


def _faq(f):
    nm, ck = f["name"], checked(f)
    q = [(f"{nm}では立ち会いの火葬ができますか？",
          f"{nm}は、公式サイトに立ち会いの火葬を書いています（{ck}に確認）。" if _has(f, "立ち会い火葬") else f"{nm}の公式サイトには、立ち会いの火葬の記載が見つかりませんでした（{ck}に確認）。"),
         (f"{nm}は家まで迎えに来てくれますか？",
          (f"{nm}は、公式サイトにお迎えを書いています（{ck}に確認）。" if _has(f, "お迎え") else "") + (f"{nm}は、火葬の車で家の近くまで来る訪問火葬も書いています。" if _has(f, "訪問火葬") else "") or
          f"{nm}の公式サイトには、お迎えの記載が見つかりませんでした（{ck}に確認）。")]
    if f.get("price"):
        q.append((f"{nm}の料金はいくらですか？", f"{nm}の公式サイトには「{f['price']}」と書いてあります（{ck}に確認）。"))
    return q


def _cmp(e, f):
    """同じ県の施設を同じ列でくらべる（順位なし・データの順）。"""
    same = [x for x in F if x["pref"] == f["pref"]][:10]
    if len(same) < 3: return ""
    def yen(x, k):
        g = GS._prices(x.get("price")); return f"{g[k]:,}円" if k in g else ""
    def mark(x, k): return "○" if _has(x, k) else ""
    body = ""
    for x in same:
        nm = e(x["name"]) if x["id"] == f["id"] else (f'<a href="{href(x)}">{e(x["name"])}</a>' if x["id"] in IDS else e(x["name"]))
        if x["id"] == f["id"]: nm = f"<b>{nm}</b>"
        body += (f"<tr><td>{nm}</td><td>{e(x['city'])}</td><td>{yen(x, 'kobetsu')}</td><td>{yen(x, 'tachiai')}</td><td>{yen(x, 'goudou')}</td>"
                 f"<td>{mark(x, '立ち会い火葬')}</td><td>{'○' if _has(x, 'お迎え') or _has(x, '訪問火葬') else ''}</td><td>{'○' if _has(x, '霊園') or _has(x, '納骨堂') else ''}</td></tr>")
    nat = "、".join(f"{lab}{n['med']}（{n['n']}か所）" for k, lab, n in TYP)
    return (f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">{e(f["pref"])}のほかのペット火葬・霊園とくらべる</h2><div class="tbl"><table class="pp-tbl cmp"><thead><tr>'
            '<th>名前</th><th>市区町村</th><th>個別（おまかせ）</th><th>立ち会い火葬</th><th>合同火葬</th><th>立ち会い</th><th>お迎え</th><th>霊園・納骨堂</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div><p class="emg-tips-note">料金は公式サイトに書いてある、猫や小型犬など「いちばん小さい区分」の金額です（全国の真ん中は {e(nat)}）。'
            '体重の区分・税込かどうか・お迎えの料金の含み方は施設ごとに違います。○は公式サイトに書いてあること、空欄は書いていない・見つからないという意味です。並びは順位ではありません。</p></div>')


def render(ctx, f):
    e, SITE = ctx["e"], ctx["SITE"]
    pf, slug, url = f["pref"], PSLUG[f["pref"]], SITE + href(f)
    nm, ck = f["name"], checked(f)
    kind = "ペット霊園" if _has(f, "霊園") else "ペット火葬場"
    can = [lab for k, lab, _ in SVC if _has(f, k)]
    tparts = [w for w, ok in (("料金", f.get("price")), ("立ち会い", _has(f, "立ち会い火葬")), ("お迎え", _has(f, "お迎え") or _has(f, "訪問火葬")), ("納骨", _has(f, "納骨") or _has(f, "納骨堂"))) if ok]
    title = f"{nm}（{f['city']}）｜{'・'.join(tparts)}｜ペットタクシー予約窓口"
    lead1 = f"{nm}は、{pf}{f['city']}の{kind}で、公式サイトに{'・'.join(can)}を書いています（{ck}に確認）。"
    pts = [lead1]
    g = GS._prices(f.get("price"))
    for k, lab, nat in TYP:
        if k in g:
            pts.append(f"{nm}の{lab}は、公式サイトの料金の例で{g[k]:,}円からです（いちばん小さい区分。全国{nat['n']}か所の真ん中は{nat['med']}）。")
    if _has(f, "お迎え") or _has(f, "訪問火葬"):
        pts.append(f"{nm}は、{'家までのお迎え' if _has(f, 'お迎え') else ''}{'・' if _has(f, 'お迎え') and _has(f, '訪問火葬') else ''}{'家の近くでの訪問火葬' if _has(f, '訪問火葬') else ''}を公式サイトに書いています。")
    pts = pts[:5]
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "ペットが亡くなったら", "item": SITE + "/sougi/"},
        {"@type": "ListItem", "position": 3, "name": f"{pf}のペット火葬・霊園", "item": f"{SITE}/sougi/{slug}/"},
        {"@type": "ListItem", "position": 4, "name": nm, "item": url}]},
      dict({"@context": "https://schema.org", "@type": "LocalBusiness", "additionalType": kind, "name": nm, "url": f["u"],
            "address": {"@type": "PostalAddress", "addressRegion": pf, "addressLocality": f["city"], "addressCountry": "JP"}},
           **({"priceRange": f["price"]} if f.get("price") else {})),
      {"@context": "https://schema.org", "@type": "WebPage", "name": nm, "url": url, "dateModified": _iso(ck), "isBasedOn": f["u"]}],
      ensure_ascii=False, indent=1) + "\n</script>"
    src = f'<a href="{e(f["u"])}" target="_blank" rel="noopener">公式サイト（{e(ck)}に確認）</a>'
    rows = "".join(f"<tr><th scope=\"row\">{e(k)}</th><td>{e(v)}</td><td>{src}</td></tr>" for k, v in facts(f))
    to = f'{nm} {pf}{f["city"]}'
    card = (f'<div class="emg-item emg-co sg-pv" data-pref="{e(pf)}"{FC.attrs(e, "sougi", f, FC.sougi_tags(f), nm, to, "この施設")}>'
            f'<a href="{e(f["u"])}" target="_blank" rel="noopener"><b>{e(nm)}の公式サイト</b></a><small>{e(pf)}{e(f["city"])}</small>'
            + (f'<div class="emg-score" data-id="{e(f["id"])}"></div>' if f.get("review_query") else "") + '</div>')
    faq_html = "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in _faq(f))
    css = "<style>.emg .tbl{overflow-x:auto;max-width:100%}.pp-tbl th,.pp-tbl td{font-size:13px;padding:5px 6px;text-align:left;vertical-align:top}.pp-tbl.cmp td,.pp-tbl.cmp th{white-space:nowrap}.pp-tbl.cmp td:first-child{white-space:normal;min-width:9em}.fac-pts{margin:6px 0 4px;padding-left:1.2em}.fac-pts li{margin:3px 0}</style>"
    return ctx["head"](title, lead1, url, ld) + css + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/sougi/">ペットが亡くなったら</a> › <a href="/sougi/{slug}/">{e(pf)}</a> › {e(nm)}</nav>
    <h1>{e(nm)}</h1>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips" style="margin-top:0"><h2 style="font-size:1.05em;margin:0 0 4px">要点</h2><ul class="fac-pts">{"".join(f"<li>{e(x)}</li>" for x in pts)}</ul></div>
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">公式サイトで確かめたこと</h2><div class="tbl"><table class="pp-tbl"><thead><tr><th>項目</th><th>内容</th><th>出どころ</th></tr></thead><tbody>{rows}</tbody></table></div></div>
      {card}
      {_cmp(e, f)}
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">よくある質問</h2><dl>{faq_html}</dl></div>
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">関連するページ</h2><ul class="other"><li><a href="/sougi/{slug}/">{e(pf)}のペット火葬・霊園と市区の受け付け</a></li><li><a href="/guide/pet-cremation-types/">ペットの火葬の種類と料金</a></li><li><a href="/guide/pet-died-first/">ペットが亡くなったら、すぐにすること</a></li><li><a href="/guide/pet-memorial/">お骨の供養と、ペット霊園・納骨堂の選び方</a></li><li><a href="/guide/farewell/">お別れの日の移動</a></li></ul></div>
      <p class="emg-free">当サイトは{e(nm)}とは別の運営で、施設からお金をもらっていません。おすすめや順位ではありません。内容は変わることがあるので、頼む前に必ず公式サイトでご確認ください。</p>
      {FC.biz(e, "ペット火葬・霊園")}
      <p class="emg-note">掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>火葬場や霊園への移動は、ペットタクシーで</h2><p>車がないとき、家族と一緒に、家の前から施設の前まで移動できます。当日の依頼もできます。</p></div>
  </div>
</section>
</main>
<script src="/reviews.js" defer></script>
{FC.SCRIPT}
""" + ctx["foot_noband"]()


def _iso(ck):
    import re
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", ck)
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else ""


def urls(SITE): return [SITE + href(f) for f in PAGES]


def write_all(ROOT, ctx):
    for f in PAGES:
        d = os.path.join(ROOT, href(f).strip("/"))
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render(ctx, f))
