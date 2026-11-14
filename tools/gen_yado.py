# [B] SEO：ペットと泊まれる宿（Nori 2026-11-14「犬と泊まれる宿網羅率低すぎ」「犬以外の動物と泊まれる宿もそれぞれあったほうがいいね」）
#  - /inu-yado/            全国の入口（先に答え・数字のタイル・都道府県の一覧・地方ごとの表）
#  - /inu-yado/<県>/       都道府県のページ（PREF_MIN 軒以上の県だけ。足りない県は全国のページの地方の表に入れる）
#  - /pet-yado/            犬以外のペット（猫・うさぎ・小鳥・フェレットなど）と泊まれる宿の入口
#  - /pet-yado/<動物>/     動物ごとのページ（ANIMAL_MIN 軒以上の動物だけ）
#  - 宿1軒ずつのページは tools/gen_facpages.py の render_inn（犬が泊まれない宿は /pet-yado/<県>/<id>/）
# データは tools/inns.json（各宿の公式サイトで確かめたことだけ。facts の k・v・src・checked）。
#   animals：泊まれる動物（dog・cat・rabbit・ferret・bird・small・reptile）、sizes：泊まれる犬の大きさの区分（s・m・l。breeds.SIZES と同じ）。
#   どちらも公式サイトの文（facts）から決めたもの。古い宿は下の OLD に書いた。
# 守ること：順位・おすすめ・電話番号は書かない。数はデータから数える（手で書かない）。宿の予約は受け付けない（公式サイトへのリンクだけ）。
import json, os, re
from urllib.parse import quote
import gen_dogrun
import visual as V

PSLUG = gen_dogrun.PSLUG
_D = os.path.dirname(os.path.abspath(__file__))
PREF_MIN = 5     # 都道府県のページを作る軒数（Nori 2026-11-14「そもそも薄い記事作らないで」。足りない県は全国のページの地方の表に入れる）
ANIMAL_MIN = 5   # 動物ごとのページを作る軒数（足りない動物は /pet-yado/ の中に載せる）
OWN_MIN = 5      # 宿1軒のページを作るのに要る、その宿だけの事実の数（系列で共通の決まりのページから写した事実は数えない）
MIN_FACTS = 5

SZ = [("s", "小型犬"), ("m", "中型犬"), ("l", "大型犬")]
AN = [("cat", "猫", "neko"), ("rabbit", "うさぎ", "usagi"), ("ferret", "フェレット", "ferret"), ("bird", "小鳥", "kotori"),
      ("small", "ハムスター・モルモットなどの小動物", "shodobutsu"), ("reptile", "爬虫類", "hachurui")]
AN_NAME = {k: n for k, n, _ in AN}
AN_SLUG = {k: s for k, _, s in AN}

# 前からある宿（2026-11-09〜）の動物と大きさ。facts の「泊まれる犬の大きさ」「猫など犬以外」の文から決めた。
OLD = {
    "i9f5d7d": (["dog"], "sml"), "ie16f09": (["dog"], "sml"), "i2c202b": (["dog", "cat"], "sml"), "iae48c8": (["dog"], "sml"),
    "i69141d": (["dog"], "sml"), "i1d5191": (["dog"], ""), "i49f672": (["dog"], "sml"), "ic8e355": (["dog"], "sml"),
    "i9ce48a": (["dog", "cat"], "sml"), "i0f6ef0": (["dog"], "sml"), "ieca203": (["dog"], "sml"), "i7bd9b9": (["dog"], "sml"),
    "i2877dd": (["dog"], "sm"), "ice983b": (["dog"], "sml"), "i467774": (["dog"], ""), "ia7d4ff": (["dog"], "sm"),
    "idd55da": (["dog", "rabbit", "bird", "small"], "sml"), "i9207c5": (["dog"], "sm"), "i7e1d70": (["dog"], ""),
    "i04799f": (["dog"], "sml"), "ie235e3": (["dog"], "sml"), "ia1549e": (["dog"], ""), "i114c96": (["dog"], "s"),
    "ie7f220": (["dog"], ""), "ic3d238": (["dog"], "s"), "i4a3e4f": (["dog"], "sml"), "i87c77e": (["dog"], "sml"),
    "i760b92": (["dog"], "sm"), "i143dea": (["dog"], "sml"), "iadaa8f": (["dog", "cat", "rabbit", "ferret", "small"], "sml"),
    "ib499e4": (["dog"], "s"), "i70a363": (["dog"], "sml"),
}


def _load():
    p = os.path.join(_D, "inns.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def _ok(x): return x.get("ok", True) and not x.get("closed") and len(x.get("facts", [])) >= MIN_FACTS


def fact(x, k):
    for f in x.get("facts", []):
        if f["k"] == k: return f["v"]
    return ""


def animals(x):
    if x.get("animals"): return x["animals"]
    return OLD.get(x["id"], (["dog"], ""))[0]


def sizes(x):
    if "sizes" in x: return x["sizes"]
    return list(OLD.get(x["id"], ([], ""))[1])


INNS = [x for x in _load().get("inns", []) if _ok(x)]
for _x in INNS:
    _x["animals"], _x["sizes"] = animals(_x), sizes(_x)


def has_dog(x): return "dog" in x["animals"]


# 系列の共通の決まり（2軒以上が同じページを出どころにしている事実）は、その宿だけの中身として数えない。
from collections import Counter
_SRC = Counter(f["src"] for x in INNS for f in {f["src"]: f for f in x["facts"]}.values())
def own_facts(x): return sum(1 for f in x["facts"] if _SRC[f["src"]] < 2 or f["src"].rstrip("/") == x["url"].rstrip("/") or f["k"] == "所在地")
for _x in INNS:
    _x["page"] = _x.get("page", True) and own_facts(_x) >= OWN_MIN


def link(x):
    """宿の名前のリンク：1軒のページがある宿はそのページ、ない宿は公式サイト"""
    return href(x) if x["page"] else x["url"]


def href(x):
    top = "inu-yado" if has_dog(x) else "pet-yado"
    return f"/{top}/{PSLUG[x['pref']]}/{x['id'].lower()}/"


DOGS = [x for x in INNS if has_dog(x)]
BYPREF = {}
for _x in DOGS: BYPREF.setdefault(_x["pref"], []).append(_x)
PREFS = {pf for pf, xs in BYPREF.items() if len(xs) >= PREF_MIN}
OTHER = {k: [x for x in INNS if k in x["animals"]] for k, _, _ in AN}
ANIMAL_PAGES = {k for k, xs in OTHER.items() if len(xs) >= ANIMAL_MIN}


def pref_href(pf): return f"/inu-yado/{PSLUG[pf]}/" if pf in PREFS else f"/inu-yado/#{PSLUG[pf]}"


def animal_href(k): return f"/pet-yado/{AN_SLUG[k]}/" if k in ANIMAL_PAGES else f"/pet-yado/#{AN_SLUG[k]}"


def _yen(s):
    m = re.search(r"([\d,]{3,})\s*円", s or "")
    return int(m.group(1).replace(",", "")) if m else None


def _free(s): return bool(re.search(r"無料|0円|かからない|不要", s or "")) and not _yen(s)


def _run(x): return bool(fact(x, "ドッグラン")) and not re.search(r"なし|ない|ありません", fact(x, "ドッグラン"))


def _cut(s, n=70):
    s = (s or "").rstrip("。")
    return s if len(s) <= n else s[:n - 1] + "…"


def _jdate(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    return f"{m.group(1)}年{int(m.group(2))}月{int(m.group(3))}日" if m else iso


def _utm(u, camp):
    return u + ("&" if "?" in u else "?") + f"utm_source=pet.shiokonbu.com&utm_medium=referral&utm_campaign={camp}"


def size_text(x):
    s = x["sizes"]
    if not s: return ""
    if s == ["s", "m", "l"]: return "大型犬まで"
    if s == ["s", "m"]: return "中型犬まで"
    if s == ["s"]: return "小型犬"
    return "・".join(n for k, n in SZ if k in s)


CSS = """<style>
.yd-ans{background:#fff;border:2.5px solid var(--o);border-radius:22px;padding:14px 16px 6px;margin:0 0 18px;box-shadow:0 6px 18px rgba(255,106,26,.08)}
.yd-ans>h2{font-size:1.12rem;margin:0 0 8px;border:0;padding:0}
.yd-ans>h2::before{content:"先に答え";display:block;width:max-content;font-size:.72rem;letter-spacing:.08em;background:var(--o);color:#fff;border-radius:999px;padding:2px 10px;margin-bottom:8px}
.yd-ans ul{list-style:none;padding:0;margin:0 0 8px}
.yd-ans li{position:relative;padding:9px 0 9px 30px;border-top:1px dashed var(--line);line-height:1.75;font-size:.93rem}
.yd-ans li:first-child{border-top:0}
.yd-ans li::before{content:"";position:absolute;left:0;top:12px;width:20px;height:20px;border-radius:50%;background:var(--o) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fff' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12.5l4.5 4.5L19 7.5'/%3E%3C/svg%3E") center/13px no-repeat}
.yd-card{background:#fff;border:1.5px solid var(--line);border-radius:16px;padding:12px 14px 10px;margin:0}
.yd-card h3{font-size:1rem;margin:0 0 2px;line-height:1.5}
.yd-card .yd-at{font-size:.78rem;color:var(--ink-3);margin:0 0 6px}
.yd-chips{display:flex;flex-wrap:wrap;gap:5px;list-style:none;padding:0!important;margin:4px 0 8px!important}
.yd-chips li{font-size:.76rem;border-radius:999px;padding:2px 10px;background:#f3f1ee;color:#3c4043;margin:0}
.yd-chips li.ok{background:#e6f4ea;color:#1e7d4f;font-weight:700}
.yd-chips li.an{background:#fff4e0;color:#8a5300;font-weight:700}
.yd-card dl{margin:0;display:grid;grid-template-columns:5.6em 1fr;gap:3px 8px;font-size:.86rem;line-height:1.65}
.yd-card dt{color:var(--ink-3);font-size:.76rem;padding-top:2px}
.yd-card dd{margin:0}
.yd-card .yd-go{display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 0 0;font-size:.84rem;font-weight:700}
.yd-pref{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:8px 0 16px}
.yd-pref a,.yd-pref span{display:inline-block;border:1.5px solid var(--line);border-radius:999px;padding:5px 12px;background:#fff;font-weight:700;text-decoration:none;font-size:.9rem}
.yd-pref small{font-weight:400;color:var(--ink-3);margin-left:3px}
.yd-pref span{color:var(--ink-3);font-weight:400;border-style:dashed}
.yd-tbl th,.yd-tbl td{font-size:13px;padding:5px 6px;text-align:left;vertical-align:top}
.yd-tbl td:first-child{min-width:9em}
.yd-h{font-size:1.08rem;margin:22px 0 8px}
</style>"""


def card(e, x, camp="yado_cards"):
    chips = "".join(f'<li class="ok">{n}OK</li>' for k, n in SZ if k in x["sizes"])
    chips += "".join(f'<li class="an">{e(AN_NAME[k])}も</li>' if has_dog(x) else f'<li class="an">{e(AN_NAME[k])}</li>' for k in x["animals"] if k in AN_NAME)
    if _run(x): chips += "<li>ドッグラン</li>"
    rows = []
    for lab, k in (("犬の大きさ", "泊まれる犬の大きさ"), ("頭数", "犬の頭数"), ("犬の料金", "犬の宿泊料金"), ("一緒にいられる", "犬と一緒にいられる場所"), ("犬以外", "猫など犬以外")):
        v = fact(x, k)
        if v: rows.append(f"<dt>{lab}</dt><dd>{e(_cut(v))}</dd>")
    addr = fact(x, "所在地") or x["pref"] + x.get("city", "")
    return ((f'<h3><a href="{href(x)}">{e(x["name"])}</a></h3>' if x["page"] else f'<h3><a href="{e(_utm(x["url"], camp))}" target="_blank" rel="noopener" data-official="{e(x["id"])}">{e(x["name"])} ↗</a></h3>') + f'<p class="yd-at">{e(x["pref"])}{e(x.get("city", ""))}・{e(x.get("kind") or "宿")}</p>'
            f'<ul class="yd-chips">{chips}</ul><dl>{"".join(rows)}</dl>'
            f'<p class="yd-go">' + (f'<a href="{href(x)}">くわしく見る（出どころつき）</a>' if x["page"] else "") +
            f'<a href="{e(_utm(x["url"], camp))}" target="_blank" rel="noopener" data-official="{e(x["id"])}">公式サイト ↗</a>'
            f'<a href="/?to={quote(addr[:80])}#form" data-taxi-cta="yado-card">ここまでのペットタクシーの料金 →</a></p>')


def fit_keys(x):
    k = list(x["sizes"]) or ["all"]
    if "cat" in x["animals"]: k.append("cat")
    return k


def table(e, xs):
    rows = "".join(
        f'<tr><td><a href="{e(link(x))}"{"" if x["page"] else ' target="_blank" rel="noopener"'}>{e(x["name"])}</a><br><small>{e(x.get("city", "") or x["pref"])}</small></td><td>{e(size_text(x) or "―")}</td>'
        f'<td>{e(_cut(fact(x, "犬の頭数"), 30) or "―")}</td><td>{e(_cut(fact(x, "犬の宿泊料金"), 34) or "―")}</td><td>{"○" if _run(x) else ""}</td>'
        f'<td>{e("・".join(AN_NAME[k] for k in x["animals"] if k in AN_NAME))}</td></tr>' for x in xs)
    return ('<div class="tbl"><table class="pp-tbl yd-tbl"><thead><tr><th>宿</th><th>犬の大きさ</th><th>頭数</th><th>犬の料金</th><th>ドッグラン</th><th>犬以外</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p class="emg-tips-note">各宿の公式サイトに書いてあることです。「―」は公式サイトに見つからなかったもの（「しない」という意味ではありません）。並びは市町村の順で、順位ではありません。</p>')


def _ld(SITE, crumbs, items, faq):
    out = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + h} for i, (n, h) in enumerate(crumbs)]}]
    if items:
        out.append({"@context": "https://schema.org", "@type": "ItemList", "numberOfItems": len(items),
                    "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": (SITE + href(x)) if x["page"] else x["url"], "name": x["name"]} for i, x in enumerate(items)]})
    if faq:
        out.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    return '<script type="application/ld+json">\n' + json.dumps(out, ensure_ascii=False, indent=1) + "\n</script>"


def _names(xs, n=4):
    s = "・".join(x["name"] for x in xs[:n])
    return s + (f"など{len(xs)}軒" if len(xs) > n else "")


def _fees(xs):
    return sorted(y for y in (_yen(fact(x, "犬の宿泊料金")) for x in xs) if y)


def _wrap(ctx, title, desc, url, ld, crumb_html, h1, small, lede, body, cta=True):
    e = ctx["e"]
    taxi = ('<section style="padding-top:0"><div class="wrap"><div class="sh"><h2>宿までの移動は、ペットタクシーで</h2>'
            '<p>車がないとき、大きな犬や何頭もいるときは、家の前から宿の前までペットタクシーで移動できます。遠い宿は、会社によって長い距離に対応していないことがあります。</p>'
            '<a class="btn" href="/#form" data-taxi-cta="yado-bottom">ペットタクシーの料金をくらべる（無料）</a></div></div></section>') if cta else ""
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト">{crumb_html}</nav>
    <h1>{f"<small>{e(small)}</small>" if small else ""}{e(h1)}</h1>
    <p class="lede">{lede}</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
{body}
      <p class="emg-free">当サイトは宿とは別の運営で、宿からお金をもらっていません。並びは地域の順で、順位やおすすめではありません。当サイトでは宿の予約は受け付けていません。条件や料金は変わることがあるので、予約の前に必ず各宿の公式サイトでご確認ください。</p>
      <p class="emg-note">掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
{taxi}
</main>
<script src="/facility.js" defer></script>
""" + ctx["foot_noband"]()


TIPS = [("予約の前に確かめること", "泊まれる犬の大きさ（体重の上限）と頭数、犬の料金、ワクチンなどの証明書、犬が入れる場所（客室だけか、食事処やロビーも入れるか）。同じ宿でも部屋のタイプで条件が変わることがあります。"),
        ("持っていくもの", "ワクチン接種や狂犬病予防注射の証明書（写しや写真でよい宿もあります）、いつものごはんと食器、トイレシーツ、ケージやクレート、マナーベルトやマナーパンツ。"),
        ("移動のこと", "長い時間の車は、1〜2時間ごとに休憩を。サービスエリアのドッグランで体を動かす時間をとると、犬も落ち着きます。")]


def _faq_html(e, faq): return "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)


def _fit(e, title, lead, xs):
    rows = [{"k": fit_keys(x), "raw": f'<div class="emg-item yd-card" data-pref="{e(x["pref"])}">{card(e, x)}</div>'} for x in xs]
    return V.block(("breeds", {"title": title, "lead": lead, "rows": rows, "names": True,
                               "note": "犬の大きさの区分は、公式サイトの「小型犬・中型犬・大型犬」や体重の上限の文から当てはめたものです。体重の上限は宿ごとに違う（10kg・20kg・25kgなど）ので、カードの文と公式サイトでご確認ください。"}))


def render_pref(ctx, pf):
    e, SITE = ctx["e"], ctx["SITE"]
    xs = sorted(BYPREF[pf], key=lambda x: (x.get("city", ""), x["name"]))
    n = len(xs); url = f"{SITE}/inu-yado/{PSLUG[pf]}/"
    big = [x for x in xs if "l" in x["sizes"]]; cats = [x for x in xs if "cat" in x["animals"]]
    oth = [x for x in xs if set(x["animals"]) - {"dog", "cat"}]
    runs = [x for x in xs if _run(x)]; fees = _fees(xs)
    cities = list(dict.fromkeys(x.get("city", "") for x in xs if x.get("city")))
    ans = [f"{pf}で犬と泊まれる宿は、当サイトで公式サイトを確かめた{n}軒です（{'・'.join(cities[:5])}{'など' if len(cities) > 5 else ''}）。"]
    ans.append(f"大型犬も泊まれると公式サイトに書いているのは{len(big)}軒：{_names(big)}。" if big else "大型犬も泊まれると公式サイトに書いている宿は、確かめた中にはありませんでした。")
    if cats: ans.append(f"猫も一緒に泊まれるのは{len(cats)}軒：{_names(cats)}。")
    if oth: ans.append(f"うさぎなど犬・猫以外の動物も泊まれるのは{len(oth)}軒：{_names(oth)}。")
    if fees: ans.append(f"犬の宿泊料金が書いてある{len(fees)}軒では、1頭1泊{fees[0]:,}円〜{fees[-1]:,}円（いちばん安い区分。税込・税抜は宿ごと）。")
    tiles = [(f"{n}軒", "公式サイトで確かめた宿"), (f"{len(big)}軒", "大型犬も泊まれる"), (f"{len(runs)}軒", "ドッグランがある")]
    if cats: tiles.append((f"{len(cats)}軒", "猫も泊まれる"))
    faq = []
    if big: faq.append((f"{pf}で大型犬と泊まれる宿は？", f"公式サイトに大型犬も泊まれると書いているのは、{_names(big, 6)}です。頭数や体重の上限は宿ごとに違います。"))
    faq.append((f"{pf}で猫と泊まれる宿は？", f"確かめた{n}軒のうち、猫も泊まれると書いているのは{_names(cats, 6)}です。" if cats else f"確かめた{n}軒には、猫も泊まれると書いている宿はありませんでした。全国の猫と泊まれる宿は「猫と泊まれる宿」のページにまとめています。"))
    if fees: faq.append((f"{pf}の宿の犬の宿泊料金はいくらくらい？", f"犬の料金を書いている{len(fees)}軒では、1頭1泊のいちばん安い区分で{fees[0]:,}円〜{fees[-1]:,}円でした。大きさや頭数で変わる宿が多く、無料の宿もあります。"))
    vac = sum(1 for x in xs if re.search(r"ワクチン|狂犬病", fact(x, "必要なもの")))
    faq.append(("ワクチンの証明書は要りますか？", f"{n}軒のうち{vac}軒が、狂犬病予防注射や混合ワクチンの証明を求めると公式サイトに書いています。写しや写真でよい宿もあります。"))
    reg = next((lab for lab, ps in ctx["emg_regions"] if pf in ps), "")
    near = [p for lab, ps in ctx["emg_regions"] if lab == reg for p in ps if p != pf and p in BYPREF]
    near_html = "".join(f'<li><a href="{pref_href(p)}">{e(p)}<small>{len(BYPREF[p])}軒</small></a></li>' for p in near)
    rel = [(f"{pf}のドッグラン", f"/dogrun/{PSLUG[pf]}/"), (f"{pf}の夜間・救急の動物病院", f"/hospital/night/{PSLUG[pf]}/")]
    rel = [(a, h) for a, h in rel if os.path.exists(os.path.join(_D, "..", h.strip("/"), "index.html"))]
    rel += [("全国の犬と泊まれる宿", "/inu-yado/"), ("猫・うさぎなど犬以外と泊まれる宿", "/pet-yado/"), ("犬と一緒に入れるカフェ・ランチ", "/inu-cafe/")]
    body = (f'<div class="yd-ans"><h2>{e(pf)}で犬と泊まれる宿は{n}軒</h2><ul>{"".join(f"<li>{e(a)}</li>" for a in ans)}</ul></div>'
            + V.stats(tiles)
            + _fit(e, f"うちの子の大きさで、{pf}の宿を見る", f"{pf}の{n}軒を、泊まれる犬の大きさ（小型犬・中型犬・大型犬）と猫でしぼれます。犬種を選ぶと、その犬種の体重に合う宿だけが残ります。", xs)
            + f'<h2 class="yd-h">{e(pf)}の{n}軒をくらべる</h2>' + table(e, xs)
            + f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">よくある質問</h2><dl>{_faq_html(e, faq)}</dl></div>'
            + '<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">犬と泊まれる宿のえらび方</h2>' + "".join(f'<h4>{e(a)}</h4><p style="font-size:.9rem;margin:4px 0 10px">{e(b)}</p>' for a, b in TIPS) + "</div>"
            + (f'<h2 class="yd-h">{e(reg)}のほかの県</h2><ul class="yd-pref">{near_html}</ul>' if near_html else "")
            + '<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">関連するページ</h2><ul class="other">' + "".join(f'<li><a href="{h}">{e(a)}</a></li>' for a, h in rel) + "</ul></div>")
    title = f"{pf}の犬と泊まれる宿{n}軒｜大型犬・頭数・犬の料金をくらべる｜ペットのくらし窓口"
    desc = f"{pf}で犬と泊まれる旅館・ホテル・コテージ{n}軒を、各宿の公式サイトで確かめた犬の大きさ・頭数・犬の宿泊料金・ドッグラン・必要なものでくらべられます。" + (f"大型犬OKは{len(big)}軒。" if big else "") + (f"猫もOKは{len(cats)}軒。" if cats else "")
    crumbs = [("ペットのくらし窓口", "/"), ("犬と泊まれる宿", "/inu-yado/"), (pf, f"/inu-yado/{PSLUG[pf]}/")]
    ld = _ld(SITE, crumbs, xs, faq)
    crumb = f'<a href="/">ペットのくらし窓口</a> › <a href="/inu-yado/">犬と泊まれる宿</a> › {e(pf)}'
    ck = max((f.get("checked", "") for x in xs for f in x["facts"]), default="")
    lede = f"{e(pf)}で犬と一緒に泊まれる宿を、各宿の公式サイトに書いてあることだけでまとめました（{e(_jdate(ck))}までに確認）。大きさ・頭数・料金・犬が入れる場所は宿ごとに大きく違うので、うちの子に合う宿をくらべてから公式サイトで予約してください。"
    return _wrap(ctx, title, desc, url, ld, crumb, f"{pf}の犬と泊まれる宿", f"公式サイトで確かめた{n}軒", lede, body)


def render_hub(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    xs = DOGS; n = len(xs); url = SITE + "/inu-yado/"
    npf = len(BYPREF)
    big = [x for x in xs if "l" in x["sizes"]]; cats = [x for x in xs if "cat" in x["animals"]]
    runs = [x for x in xs if _run(x)]; fees = _fees(xs)
    vac = sum(1 for x in xs if re.search(r"ワクチン|狂犬病", fact(x, "必要なもの")))
    top = sorted(BYPREF.items(), key=lambda kv: -len(kv[1]))[:5]
    ans = [f"当サイトで公式サイトを確かめた、犬と泊まれる宿は{n}軒（{npf}都道府県）です。多いのは" + "・".join(f"{p}（{len(v)}軒）" for p, v in top) + "。",
           f"大型犬も泊まれると書いているのは{len(big)}軒、猫も一緒に泊まれるのは{len(cats)}軒です。",
           f"{vac}軒が狂犬病予防注射や混合ワクチンの証明を求めています。予約の前に証明書を用意しておくと安心です。"]
    if fees:
        med = fees[(len(fees) - 1) // 2]
        ans.append(f"犬の宿泊料金を書いている{len(fees)}軒では、1頭1泊のいちばん安い区分の真ん中が{med:,}円（{fees[0]:,}円〜{fees[-1]:,}円）でした。")
    tiles = [(f"{n}軒", "公式サイトで確かめた宿"), (f"{npf}", "都道府県"), (f"{len(big)}軒", "大型犬も泊まれる"), (f"{len(cats)}軒", "猫も泊まれる"), (f"{len(runs)}軒", "ドッグランがある")]
    bars = V.bars({"title": "泊まれる犬の大きさ（公式サイトに書いてある宿の数）", "max": n,
                   "rows": [(lab, sum(1 for x in xs if k in x["sizes"]), f"{sum(1 for x in xs if k in x['sizes'])}軒") for k, lab in SZ],
                   "note": f"{n}軒のうち、大きさを書いている宿を数えました。1軒が複数の大きさに入ります。"})
    chips = ""
    sec = ""
    for lab, prefs in ctx["emg_regions"]:
        lis = ""
        rows = []
        for pf in prefs:
            k = len(BYPREF.get(pf, []))
            if pf in PREFS: lis += f'<li><a href="/inu-yado/{PSLUG[pf]}/">{e(pf)}<small>{k}軒</small></a></li>'
            elif k: lis += f'<li><a href="#{PSLUG[pf]}">{e(pf)}<small>{k}軒</small></a></li>'; rows += sorted(BYPREF[pf], key=lambda x: x.get("city", ""))
            else: lis += f'<li><span>{e(pf)}<small>しらべ中</small></span></li>'
        chips += f'<h3 class="emg-region">{e(lab)}</h3><ul class="yd-pref">{lis}</ul>'
        if rows:
            ids = {}
            for x in rows: ids.setdefault(x["pref"], x)
            anchors = "".join(f'<span id="{PSLUG[p]}"></span>' for p in ids)
            sec += f'{anchors}<h3 class="yd-h">{e(lab)}（{len({x["pref"] for x in rows})}県・{len(rows)}軒）</h3>' + table(e, rows)
    faq = [("犬と泊まれる宿はどうやってさがす？", "都道府県のページで、泊まれる犬の大きさ（小型犬・中型犬・大型犬）や猫でしぼれます。犬種を選ぶと体重に合う宿だけが残ります。"),
           ("大型犬と泊まれる宿は多い？", f"確かめた{n}軒のうち{len(big)}軒が、大型犬も泊まれると書いています。体重の上限（25kg・40kgなど）や頭数の決まりは宿ごとに違います。"),
           ("猫やうさぎと泊まれる宿は？", f"猫も泊まれる宿は{len(cats)}軒です。うさぎ・フェレット・小鳥などは「犬以外と泊まれる宿」のページにまとめています。"),
           ("ワクチンの証明書は必要？", f"{n}軒のうち{vac}軒が証明を求めると書いています。1年以内の狂犬病予防注射と、混合ワクチン（多くは5種以上）の証明が多いです。")]
    body = (f'<div class="yd-ans"><h2>犬と泊まれる宿は、全国で{n}軒を確かめました</h2><ul>{"".join(f"<li>{e(a)}</li>" for a in ans)}</ul></div>'
            + V.stats(tiles) + bars
            + f'<h2 class="yd-h">都道府県からさがす</h2><p class="emg-tips-note">{PREF_MIN}軒以上の県は県のページで、うちの子の大きさでしぼって見られます。それより少ない県は、このページの下の地方の表に入れています。</p>{chips}'
            + '<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">犬以外のペットと泊まれる宿</h2><ul class="yd-pref">'
            + "".join(f'<li><a href="{animal_href(k)}">{e(nm)}<small>{len(OTHER[k])}軒</small></a></li>' for k, nm, _ in AN if OTHER[k]) + "</ul></div>"
            + (f'<h2 class="yd-h">県のページがまだない県の宿</h2>{sec}' if sec else "")
            + f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">よくある質問</h2><dl>{_faq_html(e, faq)}</dl></div>'
            + '<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">犬と泊まれる宿のえらび方</h2>' + "".join(f'<h4>{e(a)}</h4><p style="font-size:.9rem;margin:4px 0 10px">{e(b)}</p>' for a, b in TIPS) + "</div>")
    title = f"犬と泊まれる宿 全国{n}軒｜都道府県別・大型犬OK・猫もOKを公式サイトで確認｜ペットのくらし窓口"
    desc = f"犬と泊まれる旅館・ホテル・コテージを全国{npf}都道府県・{n}軒、各宿の公式サイトで確かめた犬の大きさ・頭数・犬の宿泊料金・必要なものでくらべられる無料の一覧。大型犬OK{len(big)}軒、猫もOK{len(cats)}軒。"
    crumbs = [("ペットのくらし窓口", "/"), ("犬と泊まれる宿", "/inu-yado/")]
    ld = _ld(SITE, crumbs, [x for x in xs if x["pref"] not in PREFS][:100], faq)
    lede = "犬と一緒に泊まれる旅館・ホテル・コテージを、各宿の公式サイトに書いてあることだけでまとめました。予約サイトやまとめ記事は使っていません。確かめた宿から順に増やしています。"
    return _wrap(ctx, title, desc, url, ld, '<a href="/">ペットのくらし窓口</a> › 犬と泊まれる宿', "犬と泊まれる宿", f"全国{npf}都道府県・{n}軒", lede, body)


ANIMAL_TIPS = {
    "cat": [("猫と泊まるときに確かめること", "猫を受け入れる部屋が決まっているか、ケージやキャリーの中で過ごす決まりがあるか、猫砂・トイレを持っていくか、混合ワクチンの証明が要るか。"),
            ("猫は移動と環境の変化が苦手", "いつものキャリーに、家のにおいのついたタオルを入れて。着いたらまず部屋の中の危ない場所（すき間・窓）を確かめましょう。")],
    "rabbit": [("うさぎと泊まるときに確かめること", "ケージ（サークル）を持っていくか、部屋で放してよいか、床やコードをかじらない工夫。暑さ・寒さに弱いので、車と部屋の温度に気をつけて。")],
    "ferret": [("フェレットと泊まるときに確かめること", "ケージの持ち込みと、部屋で放してよいか。狭いすき間に入りこむので、部屋を確かめてから出しましょう。")],
    "bird": [("小鳥と泊まるときに確かめること", "鳥かごに入れたままか、放してよいか。温度の変化と、ほかの動物の声やにおいに気をつけて。")],
    "small": [("小動物と泊まるときに確かめること", "ケージの持ち込みと大きさ。温度の変化に弱いので、移動のあいだも温度を保てるように。")],
    "reptile": [("爬虫類と泊まるときに確かめること", "ケースの持ち込みと保温（電源）の使い方。においや逃げ出しに気をつけて。")],
}


def render_animal(ctx, k):
    e, SITE = ctx["e"], ctx["SITE"]
    nm = AN_NAME[k]; xs = sorted(OTHER[k], key=lambda x: (PREF_ORDER(ctx, x["pref"]), x.get("city", ""))); n = len(xs)
    url = f"{SITE}/pet-yado/{AN_SLUG[k]}/"
    prefs = list(dict.fromkeys(x["pref"] for x in xs))
    ans = [f"{nm}と一緒に泊まれると公式サイトに書いている宿は、確かめた中で{n}軒（{'・'.join(prefs[:6])}{'など' if len(prefs) > 6 else ''}）です。",
           "犬と泊まれる宿でも、" + nm + "は泊まれないことが多いので、予約の前に必ず宿に確かめてください。"]
    rooms = [x for x in xs if re.search(nm[:2] + r"|部屋|ルーム", fact(x, "猫など犬以外"))]
    if rooms: ans.append(f"{nm}の泊まれる部屋が決まっている宿もあります（{_names(rooms, 3)}）。")
    cards = "".join(f'<div class="emg-item yd-card" data-pref="{e(x["pref"])}">{card(e, x, "petyado_cards")}</div>' for x in xs)
    faq = [(f"{nm}と泊まれる宿はどこ？", f"当サイトで公式サイトを確かめた中では、{_names(xs, 6)}です。"),
           (f"犬と泊まれる宿なら{nm}も泊まれる？", f"泊まれるとはかぎりません。犬だけと書いている宿も多いので、{nm}と泊まれるか、部屋のタイプとあわせて宿に確かめてください。")]
    body = (f'<div class="yd-ans"><h2>{e(nm)}と泊まれる宿は{n}軒</h2><ul>{"".join(f"<li>{e(a)}</li>" for a in ans)}</ul></div>'
            + V.stats([(f"{n}軒", f"{nm}と泊まれる宿"), (f"{len(prefs)}", "都道府県"), (f"{sum(1 for x in xs if has_dog(x))}軒", "犬も泊まれる")])
            + f'<h2 class="yd-h">{e(nm)}と泊まれる{n}軒</h2><div class="bf-cards" style="display:grid;gap:10px">{cards}</div>'
            + f'<h2 class="yd-h">くらべる</h2>' + table(e, xs)
            + "".join(f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">{e(a)}</h2><p style="font-size:.9rem;margin:4px 0 10px">{e(b)}</p></div>' for a, b in ANIMAL_TIPS.get(k, []))
            + f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">よくある質問</h2><dl>{_faq_html(e, faq)}</dl></div>'
            + '<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">関連するページ</h2><ul class="other"><li><a href="/pet-yado/">犬以外のペットと泊まれる宿</a></li><li><a href="/inu-yado/">犬と泊まれる宿</a></li><li><a href="/guide/small-animals/">うさぎ・小動物の移動</a></li></ul></div>')
    title = f"{nm}と泊まれる宿{n}軒｜公式サイトで確かめた条件をくらべる｜ペットのくらし窓口"
    desc = f"{nm}と一緒に泊まれる旅館・ホテル・コテージ{n}軒を、各宿の公式サイトで確かめた条件（泊まれる部屋・ケージ・料金・必要なもの）でまとめた無料の一覧です。"
    crumbs = [("ペットのくらし窓口", "/"), ("犬以外のペットと泊まれる宿", "/pet-yado/"), (f"{nm}と泊まれる宿", f"/pet-yado/{AN_SLUG[k]}/")]
    crumb = f'<a href="/">ペットのくらし窓口</a> › <a href="/pet-yado/">犬以外のペットと泊まれる宿</a> › {e(nm)}'
    lede = f"{e(nm)}と一緒に泊まれる宿を、各宿の公式サイトに「{e(nm)}も泊まれる」と書いてあるものだけでまとめました。書いていない宿は入れていません。"
    return _wrap(ctx, title, desc, url, _ld(SITE, crumbs, xs, faq), crumb, f"{nm}と泊まれる宿", f"公式サイトで確かめた{n}軒", lede, body)


def PREF_ORDER(ctx, pf):
    i = 0
    for _, ps in ctx["emg_regions"]:
        for p in ps:
            if p == pf: return i
            i += 1
    return 99


def render_pethub(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = SITE + "/pet-yado/"
    allx = [x for x in INNS if set(x["animals"]) - {"dog"}]
    n = len(allx)
    ans = [f"犬以外のペットとも泊まれると公式サイトに書いている宿は、確かめた中で{n}軒です。"
           + "・".join(f"{AN_NAME[k]}{len(OTHER[k])}軒" for k, _, _ in AN if OTHER[k]) + "。",
           "犬と泊まれる宿の多くは「犬のみ」です。猫・うさぎ・小鳥などは、泊まれると書いてある宿をえらび、部屋のタイプも確かめてください。"]
    sec = ""
    for k, nm, slug in AN:
        xs = OTHER[k]
        if not xs: continue
        more = f'<p class="yd-go"><a href="/pet-yado/{slug}/">{e(nm)}と泊まれる宿のページへ（{len(xs)}軒）→</a></p>' if k in ANIMAL_PAGES else ""
        cards = "".join(f'<div class="emg-item yd-card" data-pref="{e(x["pref"])}">{card(e, x, "petyado_cards")}</div>' for x in xs[:6 if k in ANIMAL_PAGES else 99])
        sec += f'<h2 class="yd-h" id="{slug}">{e(nm)}と泊まれる宿（{len(xs)}軒）</h2>{more}<div style="display:grid;gap:10px">{cards}</div>{more}'
    faq = [("犬と泊まれる宿なら、猫やうさぎも泊まれる？", "泊まれるとはかぎりません。「犬のみ」と書いている宿が多いので、公式サイトか宿に確かめてください。"),
           ("猫と泊まるときに用意するものは？", "キャリー、猫砂とトイレ、いつものごはん。混合ワクチンの証明を求める宿もあります。")]
    body = (f'<div class="yd-ans"><h2>犬以外のペットと泊まれる宿は{n}軒</h2><ul>{"".join(f"<li>{e(a)}</li>" for a in ans)}</ul></div>'
            + V.stats([(f"{len(OTHER[k])}軒", f"{nm}と泊まれる") for k, nm, _ in AN if OTHER[k]])
            + sec
            + f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">よくある質問</h2><dl>{_faq_html(e, faq)}</dl></div>'
            + '<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">関連するページ</h2><ul class="other"><li><a href="/inu-yado/">犬と泊まれる宿</a></li><li><a href="/pet-hotel/">ペットホテル（預かり）</a></li><li><a href="/pet-sitter/">ペットシッター</a></li></ul></div>')
    title = f"猫・うさぎ・小鳥・フェレットと泊まれる宿{n}軒｜犬以外のペットOKの宿｜ペットのくらし窓口"
    desc = f"猫・うさぎ・フェレット・小鳥など、犬以外のペットと一緒に泊まれる宿{n}軒を、各宿の公式サイトで確かめた条件でまとめました。" + "・".join(f"{AN_NAME[k]}{len(OTHER[k])}軒" for k, _, _ in AN if OTHER[k]) + "。"
    crumbs = [("ペットのくらし窓口", "/"), ("犬以外のペットと泊まれる宿", "/pet-yado/")]
    lede = "猫・うさぎ・フェレット・小鳥など、犬以外のペットと一緒に泊まれる宿を、公式サイトに「泊まれる」と書いてあるものだけでまとめました。"
    return _wrap(ctx, title, desc, url, _ld(SITE, crumbs, allx, faq), '<a href="/">ペットのくらし窓口</a> › 犬以外のペットと泊まれる宿',
                 "猫・うさぎ・小鳥などと泊まれる宿", "犬以外のペットOK", lede, body)


def urls(SITE):
    out = [SITE + "/inu-yado/"] + [f"{SITE}/inu-yado/{PSLUG[pf]}/" for pf in sorted(PREFS, key=lambda p: PSLUG[p])]
    if any(OTHER.values()): out.append(SITE + "/pet-yado/")
    out += [f"{SITE}/pet-yado/{AN_SLUG[k]}/" for k in sorted(ANIMAL_PAGES)]
    return out


def _bf(page):
    return page.replace("</head>", V.BF_CSS + "\n</head>", 1).replace("</body>", V.BF_JS + "\n</body>", 1) if "data-bf" in page else page


def write_all(ROOT, ctx):
    def w(path, html):
        d = os.path.join(ROOT, path.strip("/")); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(_bf(html))
    if DOGS: w("/inu-yado/", render_hub(ctx))
    for pf in PREFS: w(f"/inu-yado/{PSLUG[pf]}/", render_pref(ctx, pf))
    if any(OTHER.values()): w("/pet-yado/", render_pethub(ctx))
    for k in ANIMAL_PAGES: w(f"/pet-yado/{AN_SLUG[k]}/", render_animal(ctx, k))
