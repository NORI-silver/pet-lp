# [B] ふつうの動物病院（かかりつけ）を都道府県・市区町村ごとに。gen_hospitals.py から呼ぶ。
# Nori 2026-11-15「タクシーはやっぱり動物病院行きが結構多いかも。動物病院のページは強化したほうがいいんじゃない。もっと動物病院あるでしょ」。
# データ：tools/vet_clinics.json（各地の獣医師会が公開している会員の病院の一覧で確かめた項目だけ）。
# 守ること：電話番号・順位・おすすめなし。薄いページは作らない：病院が CITY_MIN 院以上ある市区町村だけ1ページにし、
# 足りない市区町村は県のページの中に載せる。県のページは病院が PREF_MIN 院以上の県だけ作る。
import json, os, re
from urllib.parse import quote

_D = os.path.dirname(os.path.abspath(__file__))
VC = json.load(open(os.path.join(_D, "vet_clinics.json"), encoding="utf-8"))
MUNI = {(m["pref"], m["name"]): m for m in json.load(open(os.path.join(_D, "municipalities.json"), encoding="utf-8"))}
CITY_MIN = 10
PREF_MIN = 15

ANIMAL_WORD = {"イヌ": "犬", "ネコ": "猫", "トリ": "鳥", "ウサギ": "うさぎ"}
SMALL = ("ウサギ", "ハムスター", "モルモット", "フェレット")


def _pslug():
    import gen_dogrun
    return gen_dogrun.PSLUG


def by_pref():
    out = {}
    for c in VC["clinics"]:
        out.setdefault(c["pref"], []).append(c)
    return out


def cslug(pf, city):
    m = MUNI.get((pf, city))
    return m["slug"] if m else None


def animals_txt(s):
    return "・".join(ANIMAL_WORD.get(a, a) for a in s.split("・") if a) if s else ""


def end_min(h):
    """診療時間の文字から、いちばん遅い終わりの時刻（分）。"""
    ts = [int(a) * 60 + int(b) for a, b in re.findall(r"〜(\d{1,2}):(\d{2})", h.split("（")[0])]
    return max(ts) if ts else None


def parking(c):
    m = re.search(r"駐車場(\d+)台", c["services"])
    if m: return f"{m.group(1)}台"
    x = next((x for x in c["services"].split("・") if "駐車場" in x or "パーキング" in x), "")
    return x


def svc(c):
    return "・".join(x for x in c["services"].split("・") if x and "駐車場" not in x and "パーキング" not in x)


def _site(srcname):
    """出どころが各病院の公式サイトのとき（獣医師会・市の一覧ではないとき）。"""
    return srcname == "病院の公式サイト"


def _how(srcname):
    return "に書いてある" if "公式サイト" in srcname else "に病院が登録した"


def card(e, c, srcname):
    href = c["url"] or c["src"]
    rows = [("所在地", c["addr"]), ("診療時間", c["hours"]), ("休診日", c["closed"] or ("なし（年中無休）" if "年中無休" in c["hours"] else "")),
            ("診る動物", animals_txt(c["animals"])), ("診療科目", "・".join(c.get("depts") or [])), ("駐車場", parking(c)), ("ほかにしていること", svc(c)), ("お支払い", c["pay"]), ("予約", c.get("note", ""))]
    sm = "".join(f"<small>{e(k)}：{e(v)}</small>" for k, v in rows if v)
    ck = c["checked"]
    import faccard
    at = animals_txt(c["animals"])
    fit = faccard.fit_attr(animals=faccard._kinds_in(at), only=bool(at) and "その他" not in at, animals_text=at) if at else ""
    return (f'<div class="emg-item emg-co"{fit}><a href="{e(href)}" target="_blank" rel="noopener"><b>{e(c["name"])}</b></a>{sm}'
            f'<small class="hosp-src sg-src"><a href="{e(c["src"])}" target="_blank" rel="noopener">{e(c.get("src_name") or srcname)}</a>より（{int(ck[5:7])}月{int(ck[8:10])}日に確認）</small>'
            f'<a class="emg-taxi" href="/?to={quote(c["addr"])}#form">この病院までのペットタクシーの料金をくらべる →</a></div>')


def _facts(cs):
    n = len(cs)
    late = [c for c in cs if (end_min(c["hours"]) or 0) >= 19 * 60]
    latest = max((end_min(c["hours"]) or 0) for c in cs)
    small = [c for c in cs if any(a in c["animals"] for a in SMALL) or "小動物" in c["animals"]]
    bird = [c for c in cs if "トリ" in c["animals"] or "鳥" in c["animals"]]
    visit = [c for c in cs if "往診あり" in c["services"]]
    night = [c for c in cs if "夜間対応あり" in c["services"]]
    park = [c for c in cs if re.search(r"駐車場\d+台", c["services"])]
    hotel = [c for c in cs if "ホテル" in c["services"]]
    trim = [c for c in cs if "トリミング" in c["services"]]
    sun = [c for c in cs if _closed_on(c, "日")]
    return dict(n=n, late=late, latest=latest, small=small, bird=bird, park=park, hotel=hotel, trim=trim, sun=sun, visit=visit, night=night)


def _closed_on(c, d):
    if d == "祝":
        return "祝" in c["closed"]
    w = d + "曜"
    return w in c["closed"] or bool(re.search(rf"(^|[・、]){d}($|[・、])", c["closed"]))


def _week_bars(cs):
    import visual as _V
    days = ["月", "火", "水", "木", "金", "土", "日", "祝"]
    cnt = [(d + ("日" if d == "祝" else "曜日"), sum(1 for c in cs if _closed_on(c, d))) for d in days]
    rows = [(lab, k, f"{k}院") for lab, k in cnt]
    if sum(k for _, k, _ in rows) == 0: return ""
    return _V.bars(dict(title="休診日の曜日ごとの病院の数", rows=rows, max=len(cs),
                        note="休診日を書いている病院の数です。午後だけ休みの日は数えていません。休みの日は変わることがあるので、行く前に公式サイトで確かめてください。"))


def _answer(e, place, cs, srcname):
    import visual as _V
    f = _facts(cs)
    hh, mm = divmod(f["latest"], 60)
    kv = [(f"{place}の動物病院は？", (f"{srcname}で診療時間などが分かる{f['n']}院を載せています。" if _site(srcname) else f"{srcname}に載っていて、診療時間などが分かる{f['n']}院を載せています。") + "順番は町の名前の順で、おすすめ順ではありません。"),
          ("夕方は何時まで？", f"{f['n']}院のうち{len(f['late'])}院が19時かそれより遅くまで診ています（いちばん遅いのは{hh}時{mm:02d}分まで）。夜中は<a href=\"/hospital/night/\">夜間・救急の動物病院</a>へ。"),
          ("うさぎ・小鳥も診てもらえる？", f"うさぎ・ハムスター・モルモット・フェレットなどの小動物を診ると書いているのは{len(f['small'])}院、鳥は{len(f['bird'])}院です。")]
    if f["park"]:
        kv.append(("車で行ける？", f"駐車場の台数を書いている病院は{len(f['park'])}院です。台数は病院ごとのカードに書いています。"))
    if f["visit"]:
        kv.append(("家に来てもらえる（往診）？", f"往診ありと書いている病院は{len(f['visit'])}院です。条件（予約・当院の患者だけなど）は病院ごとのカードに書いています。"))
    if f["night"]:
        kv.append(("診療時間のあとも診てもらえる？", f"夜間の対応ありと書いている病院は{len(f['night'])}院です。「再診の方のみ」「当院の患者のみ」などの条件がある病院もあるので、カードで確かめてください。"))
    li = "".join(f'<li><b class="k">{e(q)}</b>{a if "<a " in a else e(a)}</li>' for q, a in kv)
    tiles = [(f"{f['n']}院", "載せている動物病院"), (f"{len(f['late'])}院", "19時以降も診ている"),
             (f"{len(f['small'])}院", "うさぎなど小動物も診る"),
             ((f"{len(f['park'])}院", "駐車場の台数を書いている") if f["park"] else (f"{len(f['visit'])}院", "往診ありと書いている"))]
    return (f'<div class="art pp-ans"><div class="answer"><h2 id="answer">{e(place)}の動物病院のポイント</h2><ul class="kv">{li}</ul></div>{_V.stats(tiles)}{_week_bars(cs)}'
            + (f'<p>ペットホテルをしている病院は{len(f["hotel"])}院、トリミングは{len(f["trim"])}院、日曜日がお休みの病院は{len(f["sun"])}院です。</p></div>' if f["hotel"] or f["trim"] else f'<p>日曜日がお休みの病院は{len(f["sun"])}院です。</p></div>'))


def _taxi_box(e, pf, pslug):
    return (f'<div class="emg-tips" data-taxi-cta="hosp-pref"><h4>動物病院まで、ペットタクシーで行く</h4>'
            f'<p>通院・入院のお迎え・手術の日など、前もって決まっている移動は、ペットタクシーの料金をくらべて問い合わせできます（無料）。当日の依頼もできます。下の病院のカードの「この病院までの料金をくらべる」を押すと、病院の所在地が行き先に入ります。</p>'
            f'<p><a class="btn" href="/?pref={quote(pf)}#form">{e(pf)}のペットタクシーの料金をくらべる →</a></p>'
            f'<p class="emg-tips-note">表示されるのは概算で、確定料金ではありません。</p></div>')


def _sort(cs):
    return sorted(cs, key=lambda c: (re.sub(r"^.*?[区市町村]", "", c["addr"]), c["name"]))


def _ld(SITE, crumbs, url, cs, name):
    items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(crumbs)]
    cs = cs[:LD_MAX]  # 構造化データは先頭の LD_MAX 院まで（ページのスクリプトを 24KB 以内に。tests/info-light.test.cjs）
    lst = {"@context": "https://schema.org", "@type": "ItemList", "name": name, "numberOfItems": len(cs),
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "VeterinaryCare", "name": c["name"], "address": c["addr"], **({"url": c["url"]} if c["url"] else {})}} for i, c in enumerate(cs)]}
    return ('<script type="application/ld+json">\n' + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}, ensure_ascii=False, indent=1)
            + '\n</script>\n<script type="application/ld+json">\n' + json.dumps(lst, ensure_ascii=False, separators=(",", ":")) + '\n</script>')


LD_MAX = 120


def _page(ctx, title, desc, url, ld, crumb, h1small, h1, lede, inner):
    return ctx["head"](title, desc, url, ld) + f"""
<main>
<section class="area-hero" style="padding-bottom:4px;min-height:0">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト">{crumb}</nav>
    <h1>{h1}</h1>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
{inner}
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <ul class="other"><li><a href="/guide/hospital/">動物病院への通院の送迎ガイド</a></li><li><a href="/hospital/night/">夜間・救急の動物病院</a></li><li><a href="/hospital/visit/">往診の動物病院</a></li><li><a href="/hospital/cat/">猫専門の動物病院</a></li><li><a href="/hospital/exotic/">エキゾチックアニマルの動物病院</a></li></ul>
  </div>
</section>
</main>
<script src="/reviews.js" defer></script>
<script src="/hosp.js" defer></script>
""" + ctx["foot_noband"]()


NOTE = ('<p class="emg-note">当サイトとは別の病院です。{src}{how}情報を、確認日の時点で写したものです。診療時間・休診日は変わることがあるので、'
        '行く前に必ず病院の公式サイトでご確認ください。この一覧は無料の情報で、病院からお金をもらっていません。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>')


def pages(ctx):
    """[(相対パス, html)] と URL の一覧。"""
    e, SITE = ctx["e"], ctx["SITE"]
    PS = _pslug()
    out, urls = [], []
    lede_c = lambda ct: f"かかりつけの病院さがし、引っ越してきたばかりのとき、いつもの病院がお休みの日に。{e(ct)}の動物病院を、診療時間・休診日・診てもらえる動物と一緒にまとめました。"
    for pf, cs in by_pref().items():
        if len(cs) < PREF_MIN: continue
        srcname = VC["sources"][pf]["name"]
        ps = PS[pf]
        cities = {}
        for c in cs: cities.setdefault(c["city"], []).append(c)
        big = {ct: v for ct, v in cities.items() if len(v) >= CITY_MIN and cslug(pf, ct)}
        # 市区町村のページ
        for ct, v in big.items():
            v = _sort(v)
            sn = {c.get("src_name") for c in v}
            csrc = sn.pop() if len(sn) == 1 and None not in sn else srcname  # その市の病院がみな同じ出どころなら、その名前
            url = f"{SITE}/hospital/{ps}/{cslug(pf, ct)}/"
            crumbs = [("ペットタクシー予約窓口", "/"), ("条件でさがす動物病院", "/hospital/"), (f"{pf}の動物病院", f"/hospital/{ps}/"), (f"{ct}の動物病院", f"/hospital/{ps}/{cslug(pf, ct)}/")]
            crumb = ' › '.join(f'<a href="{u}">{e(n)}</a>' for n, u in crumbs[:-1]) + f' › {e(ct)}'
            import gen_hospitals
            inner = (gen_hospitals.finder(ctx, "", pf, ct)
                     + f'<div class="emg hf-static"><h2 class="emg-region">{e(ct)}の動物病院 {len(v)}院（町の名前の順）</h2>'
                     + "".join(card(e, c, srcname) for c in v) + '</div>'
                     + f'<p class="lede" style="margin-top:22px">{lede_c(ct)}</p>' + _answer(e, ct, v, csrc) + _taxi_box(e, pf, ps) + NOTE.format(src=e(csrc), how=_how(csrc))
                     + f'<p class="emg-note"><a href="/hospital/{ps}/">{e(pf)}のほかの市区町村の動物病院</a>・<a href="/hospital/night/{ps}/">{e(pf)}の夜間・救急の動物病院</a></p>')
            out.append((f"hospital/{ps}/{cslug(pf, ct)}/index.html", _page(ctx,
                f"{ct}の動物病院 {len(v)}院｜診療時間・休診日・うさぎや鳥を診るか・駐車場",
                f"{pf}{ct}の動物病院{len(v)}院を、診療時間・休診日・診てもらえる動物（犬・猫・うさぎ・鳥など）・駐車場と公式サイトへのリンクで一覧にしました。19時以降も診る病院や、日曜日に開いている病院もわかります。",
                url, _ld(SITE, crumbs, url, v, f"{ct}の動物病院"), crumb, f"{e(pf)}・{len(v)}院・無料の一覧", f"{e(ct)}の動物病院",
                f"かかりつけの病院さがし、引っ越してきたばかりのとき、いつもの病院がお休みの日に。{e(ct)}の動物病院を、診療時間・休診日・診てもらえる動物と一緒にまとめました。", inner)))
            urls.append(url)
        # 県のページ
        url = f"{SITE}/hospital/{ps}/"
        crumbs = [("ペットタクシー予約窓口", "/"), ("条件でさがす動物病院", "/hospital/"), (f"{pf}の動物病院", f"/hospital/{ps}/")]
        crumb = ' › '.join(f'<a href="{u}">{e(n)}</a>' for n, u in crumbs[:-1]) + f' › {e(pf)}'
        order = sorted(cities, key=lambda ct: (MUNI.get((pf, ct), {}).get("code", "999999"), ct))
        links = "".join(f'<li><a href="/hospital/{ps}/{cslug(pf, ct)}/">{e(ct)}<small>{len(cities[ct])}院</small></a></li>' for ct in order if ct in big)
        small_secs = ""
        for ct in order:
            if ct in big: continue
            small_secs += f'<h3 class="emg-region">{e(ct)}（{len(cities[ct])}院）</h3>' + "".join(card(e, c, srcname) for c in _sort(cities[ct]))
        def scope(c):
            a = c["animals"]
            return "犬・猫・小動物・鳥など" if "トリ" in a and any(x in a for x in SMALL) else "犬・猫・小動物" if any(x in a for x in SMALL) else animals_txt(a)
        big_lists = "".join(
            f'<h3 class="emg-region"><a href="/hospital/{ps}/{cslug(pf, ct)}/">{e(ct)}の動物病院（{len(cities[ct])}院）</a></h3>'
            '<table><thead><tr><th>病院</th><th>休診日</th><th>診る動物</th></tr></thead><tbody>'
            + "".join(f'<tr><th scope="row">{e(c["name"])}<small style="display:block">{e(re.sub(r"^.*?[区市町村]", "", c["addr"].replace(pf, "", 1)).split(" ")[0])}</small></th><td>{e(c["closed"]) or "—"}</td><td>{e(scope(c))}</td></tr>' for c in _sort(cities[ct]))
            + '</tbody></table>' for ct in order if ct in big)
        rows_t = "".join(f'<tr><th scope="row">{e(ct)}</th><td>{len(cities[ct])}院</td><td>{sum(1 for c in cities[ct] if (end_min(c["hours"]) or 0) >= 1140)}院</td>'
                         f'<td>{sum(1 for c in cities[ct] if any(a in c["animals"] for a in SMALL))}院</td></tr>' for ct in order)
        import gen_hospitals
        inner = (gen_hospitals.finder(ctx, "", pf)
                 + (f'<div class="emg hf-static">{small_secs}</div>' if small_secs else '')
                 + f'<p class="lede" style="margin-top:22px">近くのかかりつけの病院をさがすときに。{e(pf)}の動物病院を、市区町村ごとに診療時間・休診日・診てもらえる動物と一緒にまとめました。</p>'
                 + _answer(e, pf, cs, srcname) + _taxi_box(e, pf, ps)
                 + (f'<div class="sh"><h2>市区町村でえらぶ</h2></div><ul class="other" style="justify-content:flex-start">{links}</ul>' if links else '')
                 + f'<div class="emg-tips"><h4>市区町村ごとの病院の数</h4><table><thead><tr><th>市区町村</th><th>病院</th><th>19時以降も</th><th>小動物も</th></tr></thead><tbody>{rows_t}</tbody></table>'
                 + '<p>まだ全部の市区町村を載せられていません。しらべたところから順に足しています。</p></div>'
                 + (f'<div class="emg-tips"><h4>市区町村ごとの病院の名前・休診日・診る動物</h4><p>診療時間・駐車場などは、それぞれの市区町村のページのカードにあります。「—」は休診日を書いていない病院です。</p>{big_lists}</div>' if big_lists else '')
                 + NOTE.format(src=e(srcname), how=_how(srcname))
                 + f'<p class="emg-note">夜中・休日に具合が悪くなったら：<a href="/hospital/night/{ps}/">{e(pf)}の夜間・救急の動物病院</a></p>')
        out.append((f"hospital/{ps}/index.html", _page(ctx,
            f"{pf}の動物病院 {len(cs)}院｜市区町村ごとに診療時間・休診日・診る動物を一覧で",
            f"{pf}の動物病院{len(cs)}院を市区町村ごとにまとめた無料の一覧です。診療時間・休診日・診てもらえる動物（犬・猫・うさぎ・鳥など）・駐車場と公式サイトへのリンクがわかります。",
            url, _ld(SITE, crumbs, url, [c for c in cs if c["city"] not in big], f"{pf}の動物病院"), crumb, f"{len(cs)}院・市区町村ごと・無料の一覧", f"{e(pf)}の動物病院",
            f"近くのかかりつけの病院をさがすときに。{e(pf)}の動物病院を、市区町村ごとに診療時間・休診日・診てもらえる動物と一緒にまとめました。", inner)))
        urls.append(url)
    return out, urls


def hub_links(e):
    """/hospital/ のいちばん上に出す「地域でさがす」。"""
    PS = _pslug()
    bp = {pf: cs for pf, cs in by_pref().items() if len(cs) >= PREF_MIN}
    if not bp: return ""
    li = "".join(f'<li><a href="/hospital/{PS[pf]}/">{e(pf)}の動物病院<small>{len(cs)}院</small></a></li>' for pf, cs in bp.items())
    return (f'<div class="sh" style="margin-top:8px"><h2>地域でさがす（ふつうの動物病院）</h2><p>診療時間・休診日・診てもらえる動物を、市区町村ごとにまとめています。順に地域を足しています。</p></div>'
            f'<ul class="other" style="justify-content:flex-start">{li}</ul>')


def urls(SITE):
    PS = _pslug()
    out = []
    for pf, cs in by_pref().items():
        if len(cs) < PREF_MIN: continue
        cities = {}
        for c in cs: cities.setdefault(c["city"], []).append(c)
        out += [f"{SITE}/hospital/{PS[pf]}/{cslug(pf, ct)}/" for ct, v in cities.items() if len(v) >= CITY_MIN and cslug(pf, ct)]
        out.append(f"{SITE}/hospital/{PS[pf]}/")
    return out


def write_all(ROOT, ctx):
    for rel, html in pages(ctx)[0]:
        p = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(html)
