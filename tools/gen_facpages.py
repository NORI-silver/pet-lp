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
import gen_yado as Y

PSLUG = gen_dogrun.PSLUG
_D = os.path.dirname(os.path.abspath(__file__))
MIN_FACTS = 5


def _load(fn):
    p = os.path.join(_D, fn)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


EMG = _load("emergency.json")
HF = _load("night_hospital_facts.json")
INN = _load("inns.json")
CAFE = _load("cafes.json")


def _ok(x): return x.get("ok", True) and not x.get("closed") and len(x.get("facts", [])) >= MIN_FACTS


HOSPS = [x for x in HF.get("items", []) if _ok(x)]
INNS = Y.INNS  # 動物・大きさ（animals・sizes）は gen_yado が足す
HIDS = {x["id"] for x in HOSPS}


def fact(x, k):
    for f in x.get("facts", []):
        if f["k"] == k: return f["v"]
    return ""


CAFES = [x for x in CAFE.get("cafes", []) if _ok(x) and fact(x, "犬と入れる席")]


def _jdate(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    return f"{m.group(1)}年{int(m.group(2))}月{int(m.group(3))}日" if m else iso


def _latest(x): return max((f.get("checked", "") for f in x["facts"]), default="")


# ---- 夜間・救急の動物病院 ----
H_KEYS = ["所在地", "受付時間", "休診日", "対象の動物", "来院前の連絡", "夜間の料金", "診療の内容", "設備", "支払い方法", "駐車場", "最寄り駅"]
I_KEYS = ["所在地", "泊まれる犬の大きさ", "犬の頭数", "犬の宿泊料金", "犬と一緒にいられる場所", "必要なもの", "ドッグラン", "猫など犬以外",
          "チェックイン・チェックアウト", "アクセス", "部屋数・部屋の種類"]


def hhref(x): return f"/hospital/night/{PSLUG[x['pref']]}/{x['id'].lower()}/"


C_KEYS = ["所在地", "犬と入れる席", "犬の大きさ", "犬の頭数", "犬のルール", "犬用メニュー", "営業時間", "定休日", "予約", "アクセス"]


def chref(x): return f"/inu-cafe/{PSLUG[x['pref']]}/{x['id'].lower()}/"


def ihref(x): return Y.href(x)


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
    # [B] 11/14 Nori「ユーザが何を求めていて、それにたいするアンサーがあるのか」：「病院名 料金」の検索が多いので、
    # 公式サイトの夜間の料金が短く書けるときは題名と説明文に入れる（数字は公式サイトのまま）。
    fee = fact(x, "夜間の料金").rstrip("。") if fact(x, "夜間の料金") else ""
    if fee and len(fee) <= 22 and re.search(r"\d", fee):
        t2 = f"{nm}（{x.get('city', '')}）｜{fee if fee.startswith('夜間') else '夜間の' + fee}・{'・'.join(w for w in tparts if w != '料金')}｜ペットタクシー予約窓口"
        if len(t2) <= 68: title = t2
    lead = f"{nm}は、{pf}{x.get('city', '')}の夜間・救急の動物病院です" + (f"。受付時間は「{hours.rstrip('。')}」です（公式サイト、{ck}に確認）。" if hours else f"（公式サイト、{ck}に確認）。")
    pts = [lead] + [_sent(nm, k, fact(x, k), ck) for k in ("休診日", "対象の動物", "来院前の連絡", "夜間の料金", "費用の目安") if fact(x, k)]
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
    # 「病院名 料金」「病院名 夜間 何時まで」の検索に先に答える（公式サイトの文のまま）
    if fact(x, "夜間の料金") or fact(x, "費用の目安"):
        a = "".join(f"「{fact(x, k).rstrip('。')}」" for k in ("夜間の料金", "費用の目安") if fact(x, k))
        faq.append((f"{nm}の夜間の料金はいくらですか？", f"{nm}の公式サイトには{a}と書いてあります（{ck}に確認）。検査・処置・入院で変わるので、くわしくは電話で確かめてください。"))
    if fact(x, "支払い方法"): faq.append((f"{nm}ではカードで払えますか？", f"{nm}の公式サイトには「{fact(x, '支払い方法').rstrip('。')}」と書いてあります。"))
    if hours: faq.append((f"{nm}は何時に受け付けていますか？", f"{nm}の公式サイトには「{hours.rstrip('。')}」と書いてあります（{ck}に確認）。"))
    if fact(x, "来院前の連絡"): faq.append((f"{nm}に行く前に電話は必要ですか？", f"{nm}の公式サイトには「{fact(x, '来院前の連絡').rstrip('。')}」と書いてあります。夜間の病院は手術中などで受け入れられないこともあるので、行く前に電話で確かめてください。"))
    if fact(x, "対象の動物"): faq.append((f"{nm}では犬と猫以外も診てもらえますか？", f"{nm}の公式サイトには「{fact(x, '対象の動物').rstrip('。')}」と書いてあります（{ck}に確認）。"))
    if fact(x, "駐車場"): faq.append((f"{nm}に駐車場はありますか？", f"{nm}の公式サイトには「{fact(x, '駐車場').rstrip('。')}」と書いてあります。"))
    if fact(x, "最寄り駅"): faq.append((f"{nm}へは電車で行けますか？", f"{nm}の公式サイトには「{fact(x, '最寄り駅').rstrip('。')}」と書いてあります。"))
    faq = faq[:7]
    ld_main = {"@type": "VeterinaryCare", "name": nm, "url": x["url"],
               "address": dict({"@type": "PostalAddress", "addressRegion": pf, "addressCountry": "JP"},
                               **({"addressLocality": x["city"]} if x.get("city") else {}), **({"streetAddress": fact(x, "所在地")} if fact(x, "所在地") else {}))}
    rid = emg.get("id") if emg.get("review_query") else ""
    hdesc = lead + (f"夜間の料金は「{fee}」。" if fee else "") + (f"{fact(x, '来院前の連絡').rstrip('。')}。" if fact(x, "来院前の連絡") else "")
    if len(hdesc) > 160: hdesc = lead
    return _page(ctx, title=title, desc=hdesc, url=url,
                 crumbs=[("ペットタクシー予約窓口", "/"), ("条件でさがす動物病院", "/hospital/"), ("夜間・救急", "/hospital/night/"), (pf, f"/hospital/night/{slug}/")],
                 nm=nm, pts=pts, rows=_rows(e, x, H_KEYS), card=_card(e, "hosp", x, "病院", rid), cmp=cmp, faq=faq,
                 related=[(f"{pf}の夜間・救急の動物病院", f"/hospital/night/{slug}/"), ("夜間・救急の動物病院（全国）", "/hospital/night/"),
                          ("緊急の連絡先・搬送の会社", "/emergency/"), ("ペットを病院へ連れて行くときの移動", "/guide/hospital/")],
                 note=f"当サイトは{e(nm)}とは別の運営で、病院からお金をもらっていません。おすすめや順位ではありません。受付時間や受け入れは変わることがあるので、行く前に必ず病院に電話で確かめてください。",
                 cta="<h2>急ぎでない通院は、ペットタクシーで</h2><p>再診や検査など急ぎでない通院は、ペットタクシーを前もって頼めます。夜間の急病で移動の手段がないときは、下の「緊急の連絡先・搬送の会社」から搬送の会社に直接ご連絡ください。</p>",
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
    dog = Y.has_dog(x)
    oth = [Y.AN_NAME[k] for k in x["animals"] if k in Y.AN_NAME]
    with_ = "犬" if dog else (oth[0] if oth else "ペット")
    tparts = [w for w, k in (("犬の大きさ", "泊まれる犬の大きさ"), ("頭数", "犬の頭数"), ("料金", "犬の宿泊料金"), ("ドッグラン", "ドッグラン")) if fact(x, k)]
    title = f"{nm}（{pf}{x.get('city', '')}）｜{with_}と泊まれる{kind}の{'・'.join(tparts) or '条件'}｜ペットのくらし窓口"
    if len(title) > 60: title = f"{nm}（{x.get('city', '') or pf}）｜{with_}と泊まれる{kind}｜ペットのくらし窓口"
    lead = f"{nm}は、{pf}{x.get('city', '')}にある、{with_}と泊まれる{kind}です（公式サイト、{ck}に確認）。" + (f"{'・'.join(oth)}も泊まれると書いています。" if dog and oth else "")
    pts = [lead] + [_sent(nm, k, fact(x, k), ck) for k in ("泊まれる犬の大きさ", "犬の頭数", "犬の宿泊料金", "猫など犬以外", "必要なもの") if fact(x, k)]
    pts = pts[:5]
    same = [y for y in INNS if y["pref"] == pf and Y.has_dog(y) == dog]
    if len(same) < 3:
        reg = _region(ctx, pf); same = [y for y in INNS if _region(ctx, y["pref"]) == reg]
    same = [x] + [y for y in same if y is not x][:9]
    cmp = (f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">{e(pf if same[-1]["pref"] == pf else "近く")}の宿とくらべる</h2>' + Y.table(e, same)
           + f'<p class="emg-tips-note"><a href="{Y.pref_href(pf) if dog else "/pet-yado/"}">{e(pf + "の犬と泊まれる宿" if dog else "犬以外のペットと泊まれる宿")}をもっと見る</a></p></div>')
    faq = []
    if fact(x, "泊まれる犬の大きさ"): faq.append((f"{nm}には大型犬も泊まれますか？", f"{nm}の公式サイトには「{fact(x, '泊まれる犬の大きさ').rstrip('。')}」と書いてあります（{ck}に確認）。"))
    if fact(x, "犬の頭数"): faq.append((f"{nm}には犬を何頭まで連れて行けますか？", f"{nm}の公式サイトには「{fact(x, '犬の頭数').rstrip('。')}」と書いてあります。"))
    if fact(x, "犬の宿泊料金"): faq.append((f"{nm}の犬の宿泊料金はいくらですか？", f"{nm}の公式サイトには「{fact(x, '犬の宿泊料金').rstrip('。')}」と書いてあります（{ck}に確認）。"))
    if fact(x, "猫など犬以外"): faq.append((f"{nm}には猫など犬以外のペットも泊まれますか？", f"{nm}の公式サイトには「{fact(x, '猫など犬以外').rstrip('。')}」と書いてあります。"))
    if fact(x, "必要なもの"): faq.append((f"{nm}に泊まるときに必要なものは？", f"{nm}の公式サイトには「{fact(x, '必要なもの').rstrip('。')}」と書いてあります。"))
    faq = faq[:4]
    ld_main = {"@type": "LodgingBusiness", "additionalType": f"{with_}と泊まれる宿", "name": nm, "url": x["url"], "petsAllowed": True,
               "address": dict({"@type": "PostalAddress", "addressRegion": pf, "addressCountry": "JP"},
                               **({"addressLocality": x["city"]} if x.get("city") else {}), **({"streetAddress": fact(x, "所在地")} if fact(x, "所在地") else {}))}
    desc = lead + (pts[1] if len(pts) > 1 else "")
    if len(desc) > 150: desc = lead
    crumbs = ([("ペットのくらし窓口", "/"), ("犬と泊まれる宿", "/inu-yado/")] + ([(pf, Y.pref_href(pf))] if pf in Y.PREFS else [])) if dog else \
             [("ペットのくらし窓口", "/"), ("犬以外のペットと泊まれる宿", "/pet-yado/")]
    rel = ([(f"{pf}の犬と泊まれる宿", Y.pref_href(pf))] if dog and pf in Y.PREFS else []) + [("犬と泊まれる宿の一覧", "/inu-yado/")]
    rel += [(f"{a}と泊まれる宿", Y.animal_href(k)) for k, a, _ in Y.AN if k in x["animals"]]
    rel += [(n, h) for n, h in ((f"{pf}のドッグラン", f"/dogrun/{slug}/"), (f"{pf}の夜間・救急の動物病院", f"/hospital/night/{slug}/"))
            if os.path.exists(os.path.join(_D, "..", h.strip("/"), "index.html"))] + [("長い距離のペットの移動", "/guide/long-distance/")]
    return _page(ctx, title=title, desc=desc, url=url, crumbs=crumbs,
                 nm=nm, pts=pts, rows=_rows(e, x, I_KEYS), card=_card(e, "inn", x, "宿"), cmp=Y.CSS + cmp, faq=faq, related=rel,
                 note=f"当サイトは{e(nm)}とは別の運営で、宿からお金をもらっていません。おすすめや順位ではありません。当サイトでは宿の予約は受け付けていません。ペットの条件や料金は変わることがあるので、予約の前に必ず公式サイトか宿でご確認ください。",
                 cta="<h2>宿までの移動は、ペットタクシーで</h2><p>車がないとき、大きな犬や何頭もいるときは、家の前から宿の前までペットタクシーで移動できます。遠い宿は、会社によって長い距離に対応していないことがあります。</p>",
                 ld_main=ld_main, src_url=x["url"], ck_iso=ck_iso)


def _med(v):
    v = sorted(v); return v[(len(v) - 1) // 2] if v else None


def _yen(s):
    m = re.search(r"([\d,]{3,})\s*円", s or "")
    return int(m.group(1).replace(",", "")) if m else None


# ---- 犬と一緒に入れるカフェ・ランチ（同伴できるお店。犬と触れ合うカフェではない） ----
def render_cafe(ctx, x):
    e, SITE = ctx["e"], ctx["SITE"]
    pf, slug, nm = x["pref"], PSLUG[x["pref"]], x["name"]
    ck_iso = _latest(x); ck = _jdate(ck_iso)
    url = SITE + chref(x)
    kind = x.get("kind") or "お店"
    seat = fact(x, "犬と入れる席")
    tparts = [w for w, k in (("入れる席", "犬と入れる席"), ("犬の大きさ", "犬の大きさ"), ("ルール", "犬のルール"), ("犬用メニュー", "犬用メニュー")) if fact(x, k)]
    title = f"{nm}（{pf}{x.get('city', '')}）｜犬と一緒に入れる{kind}の{'・'.join(tparts)}｜ペットタクシー予約窓口"
    if len(title) > 60: title = f"{nm}（{x.get('city', '') or pf}）｜犬と入れる{kind}の条件｜ペットタクシー予約窓口"
    lead = f"{nm}は、{pf}{x.get('city', '')}にある、犬と一緒に入れる（同伴できる）{kind}です。犬と入れる席は「{seat.rstrip('。')}」と公式サイトに書いてあります（{ck}に確認）。"
    pts = [lead] + [_sent(nm, k, fact(x, k), ck) for k in ("犬の大きさ", "犬の頭数", "犬のルール", "犬用メニュー") if fact(x, k)]
    pts = pts[:5]
    same = [y for y in CAFES if y["pref"] == pf]
    if len(same) < 3: same = [y for y in CAFES if _region(ctx, y["pref"]) == _region(ctx, pf)]
    if len(same) < 3: same = CAFES
    body = ""
    for y in same[:10]:
        n = e(y["name"])
        n = f"<b>{n}</b>" if y is x else f'<a href="{chref(y)}">{n}</a>'
        body += (f"<tr><td>{n}</td><td>{e(y['pref'])}{e(y.get('city', ''))}</td><td>{e(fact(y, '犬と入れる席'))}</td><td>{e(fact(y, '犬の大きさ'))}</td>"
                 f"<td>{'○' if fact(y, '犬用メニュー') and not re.search('なし|ない|ありません', fact(y, '犬用メニュー')) else ''}</td></tr>")
    cmp = (f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">近くの犬と入れるお店とくらべる</h2><div class="tbl"><table class="pp-tbl cmp">'
           f'<thead><tr><th>名前</th><th>場所</th><th>犬と入れる席</th><th>犬の大きさ</th><th>犬用メニュー</th></tr></thead><tbody>{body}</tbody></table></div>'
           '<p class="emg-tips-note">各店の公式サイトに書いてあることです。空欄は公式サイトに見つからなかったもの。並びは順位ではありません。<a href="/inu-cafe/">全部のお店の一覧</a></p></div>')
    faq = [(f"{nm}は店内に犬と入れますか？", f"{nm}の公式サイトには、犬と入れる席について「{seat.rstrip('。')}」と書いてあります（{ck}に確認）。")]
    if fact(x, "犬の大きさ"): faq.append((f"{nm}に大型犬は入れますか？", f"{nm}の公式サイトには「{fact(x, '犬の大きさ').rstrip('。')}」と書いてあります。"))
    if fact(x, "犬のルール"): faq.append((f"{nm}で犬について決まりはありますか？", f"{nm}の公式サイトには「{fact(x, '犬のルール').rstrip('。')}」と書いてあります。"))
    if fact(x, "犬用メニュー"): faq.append((f"{nm}に犬用のメニューはありますか？", f"{nm}の公式サイトには「{fact(x, '犬用メニュー').rstrip('。')}」と書いてあります。"))
    ld_main = {"@type": "Restaurant" if kind == "レストラン" else "CafeOrCoffeeShop", "name": nm, "url": x["url"],
               "address": dict({"@type": "PostalAddress", "addressRegion": pf, "addressCountry": "JP"},
                               **({"addressLocality": x["city"]} if x.get("city") else {}), **({"streetAddress": fact(x, "所在地")} if fact(x, "所在地") else {}))}
    desc = lead if len(lead) <= 150 else lead[:148] + "…"
    return _page(ctx, title=title, desc=desc, url=url,
                 crumbs=[("ペットタクシー予約窓口", "/"), ("犬と一緒に入れるカフェ・ランチ", "/inu-cafe/")],
                 nm=nm, pts=pts, rows=_rows(e, x, C_KEYS), card=_card(e, "cafe", x, "お店"), cmp=cmp, faq=faq[:4],
                 related=[("犬と一緒に入れるカフェ・ランチの一覧", "/inu-cafe/")] + [(n, h) for n, h in ((f"{pf}のドッグラン", f"/dogrun/{slug}/"),)
                          if os.path.exists(os.path.join(_D, "..", h.strip("/"), "index.html"))] + [("犬と泊まれる宿", "/inu-yado/")],
                 note=f"当サイトは{e(nm)}とは別の運営で、お店からお金をもらっていません。おすすめや順位ではありません。当サイトでは予約は受け付けていません。犬の条件や営業時間は変わることがあるので、行く前に必ず公式サイトかお店でご確認ください。",
                 cta="<h2>お店までの移動は、ペットタクシーで</h2><p>車がないとき、大きな犬や何頭もいるときは、家の前からお店の前までペットタクシーで移動できます。</p>",
                 ld_main=ld_main, src_url=x["url"], ck_iso=ck_iso)


def render_cafe_hub(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = SITE + "/inu-cafe/"
    n = len(CAFES)
    inside = sum(1 for x in CAFES if re.search("店内", fact(x, "犬と入れる席")) and not re.search("テラス(席)?のみ|テラスだけ", fact(x, "犬と入れる席")))
    terrace = sum(1 for x in CAFES if re.search("テラス(席)?のみ|テラスだけ", fact(x, "犬と入れる席")))
    big = sum(1 for x in CAFES if re.search("大型", fact(x, "犬の大きさ")) and not re.search("不可|NG|お断り|小型犬のみ", fact(x, "犬の大きさ")))
    menu = sum(1 for x in CAFES if fact(x, "犬用メニュー") and not re.search("なし|ない|ありません", fact(x, "犬用メニュー")))
    belt = sum(1 for x in CAFES if re.search("マナーベルト|マナーパンツ|おむつ|オムツ", fact(x, "犬のルール")))
    sm = [f"載せている{n}店のうち、公式サイトに店内で犬と一緒に座れると書いているのは{inside}店、テラス席だけと書いているのは{terrace}店です。",
          f"大型犬も入れると書いているのは{big}店です。",
          f"犬用メニューがあると書いているのは{menu}店、マナーベルトやおむつを求めると書いているのは{belt}店です。"]
    by = {}
    for x in CAFES: by.setdefault(_region(ctx, x["pref"]), []).append(x)
    sec = ""
    for lab, prefs in ctx["emg_regions"]:
        if lab not in by: continue
        rows = "".join(f'<tr><td><a href="{chref(x)}">{e(x["name"])}</a></td><td>{e(x["pref"])}{e(x.get("city", ""))}</td><td>{e(fact(x, "犬と入れる席"))}</td>'
                       f'<td>{e(fact(x, "犬の大きさ"))}</td></tr>' for x in by[lab])
        sec += (f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">{e(lab)}（{len(by[lab])}店）</h2><div class="tbl"><table class="pp-tbl cmp">'
                f'<thead><tr><th>名前</th><th>場所</th><th>犬と入れる席</th><th>犬の大きさ</th></tr></thead><tbody>{rows}</tbody></table></div></div>')
    title = f"犬と一緒に入れるカフェ・ランチ {n}店｜店内OK・テラス・大型犬の条件を公式サイトで確かめた一覧｜ペットタクシー予約窓口"
    desc = f"愛犬と一緒に入れる（同伴できる）カフェ・レストランを、公式サイトで確かめた条件（店内かテラスか・犬の大きさ・決まり・犬用メニュー）と一緒にまとめた無料の一覧です（{n}店、出どころと確認日つき）。"
    ld = '<script type="application/ld+json">\n' + json.dumps([
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "犬と一緒に入れるカフェ・ランチ", "item": url}]},
        {"@context": "https://schema.org", "@type": "ItemList", "name": "犬と一緒に入れるカフェ・ランチ", "numberOfItems": n,
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + chref(x), "name": x["name"]} for i, x in enumerate(CAFES)]}],
        ensure_ascii=False, indent=1) + "\n</script>"
    tips = [("行く前に確かめること", "犬と入れるのが店内か、テラス席だけか。犬の大きさや頭数の決まり、混む時間の入店の制限、予約がいるか。季節や天気でテラスが使えない日もあります。"),
            ("よくある決まり", "リードを短く持つ、椅子やテーブルに乗せない、マナーベルトやおむつ、トイレをすませてから入る、など。お店ごとに違うので公式サイトで確かめてください。")]
    tip_html = "".join(f"<h4>{e(a)}</h4><p style=\"font-size:.9rem;margin:4px 0 10px\">{b}</p>" for a, b in tips)
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › 犬と一緒に入れるカフェ・ランチ</nav>
    <h1>犬と一緒に入れるカフェ・ランチ</h1>
    <p class="lede">愛犬と一緒に入れる（同伴できる）カフェとレストランを、各店の公式サイトで確かめた条件と一緒にまとめました。犬と触れ合えるカフェ（お店の犬がいるカフェ）の一覧ではありません。いまは{n}店で、確かめたお店から順に増やしています。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips" style="margin-top:0"><h2 style="font-size:1.05em;margin:0 0 4px">数えて分かったこと</h2><ul class="fac-pts">{"".join(f"<li>{e(t)}</li>" for t in sm)}</ul></div>
      {sec}
      <div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">犬と入れるお店のえらび方</h2>{tip_html}</div>
      <p class="emg-free">当サイトはお店とは別の運営で、お店からお金をもらっていません。並びは地方ごとで、順位やおすすめではありません。当サイトでは予約は受け付けていません。行く前に必ず各店の公式サイトでご確認ください。</p>
      <p class="emg-note">掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>お店までの移動は、ペットタクシーで</h2><p>車がないとき、大きな犬や何頭もいるときは、家の前からお店の前までペットタクシーで移動できます。</p></div>
  </div>
</section>
</main>
""" + ctx["foot_noband"]()


def urls(SITE):
    return ([SITE + hhref(x) for x in HOSPS] + Y.urls(SITE) + [SITE + ihref(x) for x in INNS if x.get("page", True)]
            + ([SITE + "/inu-cafe/"] if CAFES else []) + [SITE + chref(x) for x in CAFES])


def write_all(ROOT, ctx):
    def w(path, html):
        d = os.path.join(ROOT, path.strip("/")); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
    for x in HOSPS: w(hhref(x), render_hosp(ctx, x))
    Y.write_all(ROOT, ctx)
    for x in INNS:
        if x.get("page", True): w(ihref(x), render_inn(ctx, x))
    if CAFES:
        w("/inu-cafe/", render_cafe_hub(ctx))
        for x in CAFES: w(chref(x), render_cafe(ctx, x))
