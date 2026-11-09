# [B] SEO：施設1つずつのページ（docs/facility-page.md の型）。試しの30施設ずつ。
#  - 夜間・救急の動物病院：/hospital/night/<県>/<id>/（データ tools/night_hospital_facts.json。病院の一覧は tools/emergency.json）
#  - 犬と泊まれる宿（新しい分野）：/inu-yado/ と /inu-yado/<県>/<id>/（データ tools/inns.json）
# 戦略担当 2026-11-09（Nori「倍のスピードで」）：検索数を測り終えるのを待たずに、宿と夜間病院の30施設ずつを並行で施設ページに。判定は公開から2週間後。
# 守ること：公式サイトで確かめた項目が5つ以上の施設だけ。書くのはデータの facts（k・v・src・checked）と、そこから数えたことだけ。
# 電話番号・個人名・順位・「おすすめ」は書かない。書いていない項目は行ごと出さない（「不明」と書かない）。
# 宿は予約・申し込みの受付をしない（公式サイトへのリンクだけ）。「手配」「代理」などの言葉は使わない。
import json, os, re
from urllib.parse import quote
import gen_dogrun
import facility_cards as FC

PSLUG = gen_dogrun.PSLUG
_D = os.path.dirname(os.path.abspath(__file__))
MIN_FACTS = 5


def _load(fn):
    p = os.path.join(_D, fn)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


EMG = _load("emergency.json")
HF = _load("night_hospital_facts.json")
INN = _load("inns.json")


def _ok(x): return x.get("ok", True) and not x.get("closed") and len(x.get("facts", [])) >= MIN_FACTS


HOSPS = [x for x in HF.get("items", []) if _ok(x)]
INNS = [x for x in INN.get("inns", []) if _ok(x)]
HIDS = {x["id"] for x in HOSPS}


def fact(x, k):
    for f in x.get("facts", []):
        if f["k"] == k: return f["v"]
    return ""


def _jdate(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    return f"{m.group(1)}年{int(m.group(2))}月{int(m.group(3))}日" if m else iso


def _latest(x): return max((f.get("checked", "") for f in x["facts"]), default="")


# ---- 夜間・救急の動物病院 ----
H_KEYS = ["所在地", "受付時間", "休診日", "対象の動物", "来院前の連絡", "夜間の料金", "診療の内容", "支払い方法", "駐車場", "最寄り駅"]
I_KEYS = ["所在地", "泊まれる犬の大きさ", "犬の頭数", "犬の宿泊料金", "犬と一緒にいられる場所", "必要なもの", "ドッグラン", "猫など犬以外",
          "チェックイン・チェックアウト", "アクセス", "部屋数・部屋の種類"]


def hhref(x): return f"/hospital/night/{PSLUG[x['pref']]}/{x['id'].lower()}/"


def ihref(x): return f"/inu-yado/{PSLUG[x['pref']]}/{x['id'].lower()}/"


def _rows(e, x, keys):
    fs = sorted(x["facts"], key=lambda f: keys.index(f["k"]) if f["k"] in keys else 99)
    return "".join(f'<tr><th scope="row">{e(f["k"])}</th><td>{e(f["v"])}</td><td><a href="{e(f["src"])}" target="_blank" rel="noopener">公式サイト（{e(_jdate(f["checked"]))}に確認）</a></td></tr>' for f in fs)


def _sent(nm, k, v, ck):
    """事実の1行を、施設名を主語にした1文にする（AIに引用されやすい形。docs/facility-page.md）。"""
    v = v.rstrip("。")
    return f"{nm}の公式サイトには、{k}について「{v}」と書いてあります。"


CSS = ("<style>.emg .tbl{overflow-x:auto;max-width:100%}.pp-tbl th,.pp-tbl td{font-size:13px;padding:5px 6px;text-align:left;vertical-align:top}"
       ".pp-tbl.cmp td,.pp-tbl.cmp th{white-space:nowrap}.pp-tbl.cmp td:first-child{white-space:normal;min-width:9em}.fac-pts{margin:6px 0 4px;padding-left:1.2em}.fac-pts li{margin:3px 0}</style>")


def _page(ctx, *, title, desc, url, crumbs, nm, pts, rows, card, cmp, faq, related, note, cta, ld_main, src_url, ck_iso):
    e, SITE = ctx["e"], ctx["SITE"]
    ld = '<script type="application/ld+json">\n' + json.dumps([
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + h} for i, (n, h) in enumerate(crumbs + [(nm, url[len(SITE):])])]},
        dict({"@context": "https://schema.org"}, **ld_main),
        {"@context": "https://schema.org", "@type": "WebPage", "name": nm, "url": url, "dateModified": ck_iso, "isBasedOn": src_url}],
        ensure_ascii=False, indent=1) + "\n</script>"
    crumb = " › ".join(f'<a href="{h}">{e(n)}</a>' for n, h in crumbs) + f" › {e(nm)}"
    faq_html = "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in faq)
    rel = "".join(f'<li><a href="{h}">{e(n)}</a></li>' for n, h in related)
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト">{crumb}</nav>
    <h1>{e(nm)}</h1>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips" style="margin-top:0"><h2 style="font-size:1.05em;margin:0 0 4px">要点</h2><ul class="fac-pts">{"".join(f"<li>{e(p)}</li>" for p in pts)}</ul></div>
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">公式サイトで確かめたこと</h2><div class="tbl"><table class="pp-tbl"><thead><tr><th>項目</th><th>内容</th><th>出どころ</th></tr></thead><tbody>{rows}</tbody></table></div><p class="emg-tips-note">書いていない項目は、公式サイトに見つからなかったものです（「しない」という意味ではありません）。</p></div>
      {card}
      {cmp}
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">よくある質問</h2><dl>{faq_html}</dl></div>
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">関連するページ</h2><ul class="other">{rel}</ul></div>
      <p class="emg-free">{note}</p>
      <p class="emg-note">掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh">{cta}</div>
  </div>
</section>
</main>
<script src="/reviews.js" defer></script>
{FC.SCRIPT}
""" + ctx["foot_noband"]()


def _addr(x): return fact(x, "所在地") or f"{x['pref']}{x.get('city', '')}"


def _taxi_btn(e, x, label):
    a = _addr(x)
    return f'<a class="emg-taxi" href="/?to={quote(a[:80])}#form">この{label}までのペットタクシーの料金をくらべる →</a>'


def _card(e, cat, x, label, review_id=""):
    to = _addr(x)
    return (f'<div class="emg-item emg-co" data-pref="{e(x["pref"])}"{FC.attrs(e, cat, x, [], x["name"], to, "この" + label)}>'
            f'<a href="{e(x["url"])}" target="_blank" rel="noopener"><b>{e(x["name"])}の公式サイト</b></a><small>{e(x["pref"])}{e(x.get("city", ""))}</small>'
            + (f'<div class="emg-score" data-id="{e(review_id)}"></div>' if review_id else "") + _taxi_btn(e, x, label) + '</div>')


def _emg_row(x):
    for v in EMG.get("hospitals", {}).values():
        for h in v:
            if h.get("id") == x["id"]: return h
    return {}


def render_hosp(ctx, x):
    e, SITE = ctx["e"], ctx["SITE"]
    pf, slug, nm = x["pref"], PSLUG[x["pref"]], x["name"]
    ck_iso = _latest(x); ck = _jdate(ck_iso)
    url = SITE + hhref(x)
    hours = fact(x, "受付時間")
    tparts = [w for w, k in (("受付時間", "受付時間"), ("休診日", "休診日"), ("料金", "夜間の料金"), ("行き方", "最寄り駅")) if fact(x, k)]
    title = f"{nm}（{x.get('city', '')}）｜夜間・救急の{'・'.join(tparts)}｜ペットタクシー予約窓口"
    lead = f"{nm}は、{pf}{x.get('city', '')}の夜間・救急の動物病院です" + (f"。受付時間は「{hours.rstrip('。')}」です（公式サイト、{ck}に確認）。" if hours else f"（公式サイト、{ck}に確認）。")
    pts = [lead] + [_sent(nm, k, fact(x, k), ck) for k in ("休診日", "対象の動物", "来院前の連絡", "夜間の料金") if fact(x, k)]
    pts = pts[:5]
    emg = _emg_row(x)
    same = [h for h in EMG["hospitals"].get(pf, []) if h.get("url")][:10]
    cmp = ""
    if len(same) >= 3:
        body = ""
        for h in same:
            n = e(h["name"])
            if h.get("id") == x["id"]: n = f"<b>{n}</b>"
            elif h.get("id") in HIDS: n = f'<a href="{hhref(next(y for y in HOSPS if y["id"] == h["id"]))}">{n}</a>'
            body += f"<tr><td>{n}</td><td>{e(h.get('city', ''))}</td><td>{e(h.get('hours', ''))}</td></tr>"
        cmp = (f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">{e(pf)}のほかの夜間・救急の動物病院とくらべる</h2><div class="tbl"><table class="pp-tbl cmp">'
               f'<thead><tr><th>名前</th><th>市区町村</th><th>受付時間</th></tr></thead><tbody>{body}</tbody></table></div>'
               f'<p class="emg-tips-note">受付時間は各病院の公式サイトに書いてある時間です。並びは順位ではありません。全部の病院は<a href="/hospital/night/{slug}/">{e(pf)}の夜間・救急の動物病院</a>にあります。</p></div>')
    faq = []
    if hours: faq.append((f"{nm}は何時に受け付けていますか？", f"{nm}の公式サイトには「{hours.rstrip('。')}」と書いてあります（{ck}に確認）。"))
    if fact(x, "来院前の連絡"): faq.append((f"{nm}に行く前に電話は必要ですか？", f"{nm}の公式サイトには「{fact(x, '来院前の連絡').rstrip('。')}」と書いてあります。夜間の病院は手術中などで受け入れられないこともあるので、行く前に電話で確かめてください。"))
    if fact(x, "対象の動物"): faq.append((f"{nm}では犬と猫以外も診てもらえますか？", f"{nm}の公式サイトには「{fact(x, '対象の動物').rstrip('。')}」と書いてあります（{ck}に確認）。"))
    if fact(x, "駐車場"): faq.append((f"{nm}に駐車場はありますか？", f"{nm}の公式サイトには「{fact(x, '駐車場').rstrip('。')}」と書いてあります。"))
    faq = faq[:4]
    ld_main = {"@type": "VeterinaryCare", "name": nm, "url": x["url"],
               "address": dict({"@type": "PostalAddress", "addressRegion": pf, "addressCountry": "JP"},
                               **({"addressLocality": x["city"]} if x.get("city") else {}), **({"streetAddress": fact(x, "所在地")} if fact(x, "所在地") else {}))}
    rid = emg.get("id") if emg.get("review_query") else ""
    return _page(ctx, title=title, desc=lead, url=url,
                 crumbs=[("ペットタクシー予約窓口", "/"), ("条件でさがす動物病院", "/hospital/"), ("夜間・救急", "/hospital/night/"), (pf, f"/hospital/night/{slug}/")],
                 nm=nm, pts=pts, rows=_rows(e, x, H_KEYS), card=_card(e, "hosp", x, "病院", rid), cmp=cmp, faq=faq,
                 related=[(f"{pf}の夜間・救急の動物病院", f"/hospital/night/{slug}/"), ("夜間・救急の動物病院（全国）", "/hospital/night/"),
                          ("緊急の連絡先・搬送の会社", "/emergency/"), ("ペットを病院へ連れて行くときの移動", "/guide/hospital/")],
                 note=f"当サイトは{e(nm)}とは別の運営で、病院からお金をもらっていません。おすすめや順位ではありません。受付時間や受け入れは変わることがあるので、行く前に必ず病院に電話で確かめてください。",
                 cta="<h2>急ぎでない通院は、ペットタクシーで</h2><p>夜間の急病で移動の手段がないときは、<a href=\"/emergency/\">緊急の搬送をしている会社</a>に直接ご連絡ください。再診や検査など急ぎでない通院は、ペットタクシーを前もって頼めます（お迎えは依頼から3時間以上あと）。</p>",
                 ld_main=ld_main, src_url=x["url"], ck_iso=ck_iso)


# ---- 犬と泊まれる宿 ----
REGIONS = None


def _region(ctx, pf):
    for lab, prefs in ctx["emg_regions"]:
        if pf in prefs: return lab
    return ""


def render_inn(ctx, x):
    e, SITE = ctx["e"], ctx["SITE"]
    pf, slug, nm = x["pref"], PSLUG[x["pref"]], x["name"]
    ck_iso = _latest(x); ck = _jdate(ck_iso)
    url = SITE + ihref(x)
    kind = x.get("kind") or "宿"
    tparts = [w for w, k in (("犬の大きさ", "泊まれる犬の大きさ"), ("頭数", "犬の頭数"), ("料金", "犬の宿泊料金"), ("ドッグラン", "ドッグラン")) if fact(x, k)]
    title = f"{nm}（{pf}{x.get('city', '')}）｜犬と泊まれる{kind}の{'・'.join(tparts)}｜ペットタクシー予約窓口"
    lead = f"{nm}は、{pf}{x.get('city', '')}にある、犬と泊まれる{kind}です（公式サイト、{ck}に確認）。"
    pts = [lead] + [_sent(nm, k, fact(x, k), ck) for k in ("泊まれる犬の大きさ", "犬の頭数", "犬の宿泊料金", "必要なもの") if fact(x, k)]
    pts = pts[:5]
    reg = _region(ctx, pf)
    same = [y for y in INNS if _region(ctx, y["pref"]) == reg]
    if len(same) < 3: same = INNS
    body = ""
    for y in same[:10]:
        n = e(y["name"])
        n = f"<b>{n}</b>" if y is x else f'<a href="{ihref(y)}">{n}</a>'
        body += (f"<tr><td>{n}</td><td>{e(y['pref'])}{e(y.get('city', ''))}</td><td>{e(fact(y, '泊まれる犬の大きさ'))}</td><td>{e(fact(y, '犬の頭数'))}</td>"
                 f"<td>{e(fact(y, '犬の宿泊料金'))}</td><td>{'○' if fact(y, 'ドッグラン') and not re.search('なし|ない|ありません', fact(y, 'ドッグラン')) else ''}</td></tr>")
    cmp = (f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">{e(reg or "ほか")}の犬と泊まれる宿とくらべる</h2><div class="tbl"><table class="pp-tbl cmp">'
           f'<thead><tr><th>名前</th><th>場所</th><th>犬の大きさ</th><th>頭数</th><th>犬の料金</th><th>ドッグラン</th></tr></thead><tbody>{body}</tbody></table></div>'
           '<p class="emg-tips-note">各宿の公式サイトに書いてあることです。空欄は公式サイトに見つからなかったもの。並びは順位ではありません。<a href="/inu-yado/">全部の宿の一覧</a></p></div>')
    faq = []
    if fact(x, "泊まれる犬の大きさ"): faq.append((f"{nm}には大型犬も泊まれますか？", f"{nm}の公式サイトには「{fact(x, '泊まれる犬の大きさ').rstrip('。')}」と書いてあります（{ck}に確認）。"))
    if fact(x, "犬の頭数"): faq.append((f"{nm}には犬を何頭まで連れて行けますか？", f"{nm}の公式サイトには「{fact(x, '犬の頭数').rstrip('。')}」と書いてあります。"))
    if fact(x, "犬の宿泊料金"): faq.append((f"{nm}の犬の宿泊料金はいくらですか？", f"{nm}の公式サイトには「{fact(x, '犬の宿泊料金').rstrip('。')}」と書いてあります（{ck}に確認）。"))
    if fact(x, "必要なもの"): faq.append((f"{nm}に泊まるときに必要なものは？", f"{nm}の公式サイトには「{fact(x, '必要なもの').rstrip('。')}」と書いてあります。"))
    faq = faq[:4]
    ld_main = {"@type": "LodgingBusiness", "additionalType": "犬と泊まれる宿", "name": nm, "url": x["url"], "petsAllowed": True,
               "address": dict({"@type": "PostalAddress", "addressRegion": pf, "addressCountry": "JP"},
                               **({"addressLocality": x["city"]} if x.get("city") else {}), **({"streetAddress": fact(x, "所在地")} if fact(x, "所在地") else {}))}
    desc = lead + (pts[1] if len(pts) > 1 else "")
    if len(desc) > 150: desc = lead
    return _page(ctx, title=title, desc=desc, url=url,
                 crumbs=[("ペットタクシー予約窓口", "/"), ("犬と泊まれる宿", "/inu-yado/")],
                 nm=nm, pts=pts, rows=_rows(e, x, I_KEYS), card=_card(e, "inn", x, "宿"), cmp=cmp, faq=faq,
                 related=[("犬と泊まれる宿の一覧", "/inu-yado/")] + [(n, h) for n, h in ((f"{pf}のドッグラン", f"/dogrun/{slug}/"), (f"{pf}の夜間・救急の動物病院", f"/hospital/night/{slug}/"))
                          if os.path.exists(os.path.join(_D, "..", h.strip("/"), "index.html"))] + [("長い距離のペットの移動", "/guide/long-distance/")],
                 note=f"当サイトは{e(nm)}とは別の運営で、宿からお金をもらっていません。おすすめや順位ではありません。当サイトでは宿の予約は受け付けていません。犬の条件や料金は変わることがあるので、予約の前に必ず公式サイトか宿でご確認ください。",
                 cta="<h2>宿までの移動は、ペットタクシーで</h2><p>車がないとき、大きな犬や何頭もいるときは、家の前から宿の前までペットタクシーで移動できます。遠い宿は、会社によって長い距離に対応していないことがあります。</p>",
                 ld_main=ld_main, src_url=x["url"], ck_iso=ck_iso)


def _med(v):
    v = sorted(v); return v[(len(v) - 1) // 2] if v else None


def _yen(s):
    m = re.search(r"([\d,]{3,})\s*円", s or "")
    return int(m.group(1).replace(",", "")) if m else None


def render_inn_hub(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = SITE + "/inu-yado/"
    n = len(INNS)
    big = sum(1 for x in INNS if re.search(r"大型", fact(x, "泊まれる犬の大きさ")) and not re.search(r"大型犬(は|不可|NG)|不可", fact(x, "泊まれる犬の大きさ")))
    vac = sum(1 for x in INNS if re.search(r"ワクチン|狂犬病", fact(x, "必要なもの")))
    run = sum(1 for x in INNS if fact(x, "ドッグラン") and not re.search("なし|ない|ありません", fact(x, "ドッグラン")))
    fees = [y for y in (_yen(fact(x, "犬の宿泊料金")) for x in INNS) if y]
    med = _med(fees)
    sm = [f"載せている{n}軒のうち、公式サイトに大型犬も泊まれると書いているのは{big}軒です。",
          f"ワクチン接種や狂犬病予防注射の証明を求めると書いているのは{vac}軒です。",
          f"敷地にドッグランがあると書いているのは{run}軒です。"]
    if med: sm.append(f"犬の宿泊料金が書いてある{len(fees)}軒の、1頭1泊のいちばん安い区分の真ん中は{med:,}円です（税込・税抜は宿ごとに違います）。")
    by = {}
    for x in INNS: by.setdefault(_region(ctx, x["pref"]), []).append(x)
    sec = ""
    for lab, prefs in ctx["emg_regions"]:
        if lab not in by: continue
        rows = "".join(f'<tr><td><a href="{ihref(x)}">{e(x["name"])}</a></td><td>{e(x["pref"])}{e(x.get("city", ""))}</td><td>{e(fact(x, "泊まれる犬の大きさ"))}</td>'
                       f'<td>{e(fact(x, "犬の頭数"))}</td><td>{e(fact(x, "犬の宿泊料金"))}</td></tr>' for x in by[lab])
        sec += (f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">{e(lab)}（{len(by[lab])}軒）</h2><div class="tbl"><table class="pp-tbl cmp">'
                f'<thead><tr><th>名前</th><th>場所</th><th>犬の大きさ</th><th>頭数</th><th>犬の料金</th></tr></thead><tbody>{rows}</tbody></table></div></div>')
    title = f"犬と泊まれる宿 {n}軒｜犬の大きさ・頭数・料金を公式サイトで確かめた一覧｜ペットタクシー予約窓口"
    desc = f"犬と泊まれる旅館・ホテル・ペンションを、公式サイトで確かめた犬の大きさ・頭数・犬の宿泊料金・必要なものと一緒にまとめた無料の一覧です（{n}軒、出どころと確認日つき）。"
    ld = '<script type="application/ld+json">\n' + json.dumps([
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "犬と泊まれる宿", "item": url}]},
        {"@context": "https://schema.org", "@type": "ItemList", "name": "犬と泊まれる宿", "numberOfItems": n,
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + ihref(x), "name": x["name"]} for i, x in enumerate(INNS)]}],
        ensure_ascii=False, indent=1) + "\n</script>"
    tips = [("予約の前に確かめること", "泊まれる犬の大きさ（体重の上限）と頭数、犬の料金、ワクチンなどの証明書、犬が入れる場所（客室だけか、食事処やロビーも入れるか）。宿によって大きく違います。"),
            ("持っていくもの", "ワクチン接種や狂犬病予防注射の証明書（写しや写真でよい宿もあります）、いつものごはんと食器、トイレシーツ、ケージやクレート、マナーベルトやマナーパンツ。"),
            ("移動のこと", "長い時間の車は、1〜2時間ごとに休憩を。車がないときは<a href=\"/#form\">ペットタクシー</a>で家の前から宿の前まで移動できます。遠い宿は、長い距離に対応している会社をさがしてください。")]
    tip_html = "".join(f"<h4>{e(a)}</h4><p style=\"font-size:.9rem;margin:4px 0 10px\">{b}</p>" for a, b in tips)
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › 犬と泊まれる宿</nav>
    <h1>犬と泊まれる宿</h1>
    <p class="lede">犬と一緒に泊まれる旅館・ホテル・ペンションを、各宿の公式サイトで確かめた条件（犬の大きさ・頭数・料金・必要なもの）と一緒にまとめました。いまは{n}軒で、確かめた宿から順に増やしています。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips" style="margin-top:0"><h2 style="font-size:1.05em;margin:0 0 4px">数えて分かったこと</h2><ul class="fac-pts">{"".join(f"<li>{e(s)}</li>" for s in sm)}</ul></div>
      {sec}
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">犬と泊まれる宿のえらび方</h2>{tip_html}</div>
      <p class="emg-free">当サイトは宿とは別の運営で、宿からお金をもらっていません。並びは地方ごとで、順位やおすすめではありません。当サイトでは宿の予約は受け付けていません。予約の前に必ず各宿の公式サイトでご確認ください。</p>
      <p class="emg-note">掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
</main>
""" + ctx["foot_noband"]()


def urls(SITE):
    return ([SITE + hhref(x) for x in HOSPS] + ([SITE + "/inu-yado/"] if INNS else []) + [SITE + ihref(x) for x in INNS])


def write_all(ROOT, ctx):
    def w(path, html):
        d = os.path.join(ROOT, path.strip("/")); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
    for x in HOSPS: w(hhref(x), render_hosp(ctx, x))
    if INNS:
        w("/inu-yado/", render_inn_hub(ctx))
        for x in INNS: w(ihref(x), render_inn(ctx, x))
