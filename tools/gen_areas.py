"""pet-lp のエリア別ページ・sitemap・robots・404・style.css を作る。
使い方: python3 gen_areas.py /home/claude/pet-lp
"""
import json, os, re, sys, html

ROOT = sys.argv[1]
SITE = "https://pet.shiokonbu.com"
TODAY = "2026-10-30"  # 更新日（sitemap と記事の dateModified）
PUBLISHED = "2026-10-27"  # ガイド記事の公開日

# 料金の目安（片道）。提携先ごとの料金表とエリアの対応は tools/fares.json にまとめている。
# 会社を足したら fares.json を直してこのスクリプトを実行すると、トップの料金表・フォームの概算・エリアページがまとめて変わる。
import math
FARES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fares.json"), encoding="utf-8"))
CO = FARES["companies"]
ALL_PREFS = list(FARES["areas"])
def cos_for(pref=None):
    keys = FARES["areas"][pref] if pref else [k for p in ALL_PREFS for k in FARES["areas"][p]]
    return [CO[k] for k in dict.fromkeys(keys)]
def ride(c, km):
    km = max(1, math.ceil(km)); f = c["base"]; frm = c["base_km"]
    for upto, add in c["tiers"]:
        upto = upto if upto is not None else float("inf")
        if km > frm: f += add * (min(km, upto) - frm)
        frm = upto
    return f
def total(c, km, round_trip=False):
    rf = c.get("round_flat")
    if round_trip and rf and km * 2 <= rf[0]: return rf[1] + c["pick"] + c["back"]
    return ride(c, km) * (2 if round_trip else 1) + c["pick"] + c["back"]
def yen(n): return f"{n:,}円"
# 夜間・早朝の割増（会社ごと）。料金表・エリアページ・よくある質問で同じ文を使う
def night_text(pref=None):
    parts = []
    for c in cos_for(pref):
        if c.get("night", 1) > 1 and c.get("night_hours"):
            h0, h1 = c["night_hours"]; pct = round((c["night"] - 1) * 10)
            parts.append(f"{c['label']}は、{h0}時〜朝{h1}時のお迎えで乗車料金が{pct}割増し")
        else:
            parts.append(f"{c['label']}は、夜間の割増が料金表にありません")
    return "、".join(parts) + "。"
def fare_text(km, pref=None, round_trip=False):
    v = sorted({total(c, km, round_trip) for c in cos_for(pref)})
    return yen(v[0]) + "〜" if len(v) == 1 else f"{v[0]:,}〜{yen(v[-1])}"
def fare_note(pref=None):
    cs = cos_for(pref)
    head = "片道の目安です。" + ("当サイトとやりとりのあるペットタクシーの料金表で計算した例です。" if len(cs) == 1 else f"当サイトとやりとりのあるペットタクシー{len(cs)}社の料金表で計算した例で、会社によって変わります。") + "フォームでは、候補の会社ごとに料金表から計算した目安が出ます。"
    tail = "目安には高速代・駐車場代は入っていません。確定料金（税込）は、お迎えが決まったときに引き受けた会社から、一般道の場合と高速道路を使う場合の両方をお知らせします。運賃は当日、ペットタクシーへ直接お支払いください（当サイトへのお支払いはありません）。" + "".join(c.get("pay", "") for c in cs)
    return head + "".join(c["note"] for c in cs) + FARES.get("area_note", {}).get(pref or "", "") + tail
# フォームの概算（index.html）に渡す料金データ
FARE_JS = "var FARES = " + json.dumps({k: {x: c.get(x) for x in ("label","base_km","base","tiers","pick","back","night","night_hours","round_flat","wait","shop","pick_free_km","pick_over")} for k, c in CO.items()}, ensure_ascii=False) + ";\n  var REVIEWS = " + json.dumps({c["partner_id"]: c["review_url"] for c in CO.values() if c.get("partner_id") and c.get("review_url")}, ensure_ascii=False) + ";\n  var AREA_FARES = " + json.dumps(FARES["areas"], ensure_ascii=False) + ";"

# 予約側も同じ料金データを使う（Code.gs を貼り直すときに含まれる）。
booking_path = os.path.join(ROOT, "booking", "Code.gs")
booking_src = open(booking_path, encoding="utf-8").read()
booking_src = re.sub(r"/\*SELECTION_FARES\*/.*?/\*/SELECTION_FARES\*/", lambda m: "/*SELECTION_FARES*/var SELECTION_FARES = " + json.dumps({k: {x: v for x, v in c.items() if x != "review_url"} for k, c in CO.items()}, ensure_ascii=False) + ";/*/SELECTION_FARES*/", booking_src, count=1, flags=re.S)
# 緊急タブの搬送の会社の口コミ：場所を探すことばを予約のしくみに渡す（tools/emergency.json の taxis）
_EMG_J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "emergency.json"), encoding="utf-8"))
# 搬送の会社（E01〜）と病院（H001〜。いくつかの県に載っている病院も id は1つ）
_EMG_RV = _EMG_J["taxis"] + [h for l in _EMG_J["hospitals"].values() for h in l]
booking_src = re.sub(r"/\*EMG_REVIEWS\*/.*?/\*/EMG_REVIEWS\*/", lambda m: "/*EMG_REVIEWS*/var EMG_REVIEWS = " + json.dumps({t["id"]: {"query": t["review_query"], "name": t["review_name"]} for t in _EMG_RV if t.get("review_query")}, ensure_ascii=False) + ";/*/EMG_REVIEWS*/", booking_src, count=1, flags=re.S)
# 候補カードに表示だけする会社（依頼は送れない）。tools/display_companies.py で作る
_DISP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "display_companies.json"), encoding="utf-8"))["companies"]
booking_src = re.sub(r"/\*DISPLAY_COMPANIES\*/.*?/\*/DISPLAY_COMPANIES\*/", lambda m: "/*DISPLAY_COMPANIES*/var DISPLAY_COMPANIES = " + json.dumps(_DISP, ensure_ascii=False) + ";/*/DISPLAY_COMPANIES*/", booking_src, count=1, flags=re.S)
_DCJ = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "display_companies.json"), encoding="utf-8"))
_PPTS = _DCJ.get("partner_points", {})
_PLIM = _DCJ.get("partner_limits", {})
booking_src = re.sub(r"/\*PARTNER_POINTS\*/.*?/\*/PARTNER_POINTS\*/", lambda m: "/*PARTNER_POINTS*/var PARTNER_POINTS = " + json.dumps(_PPTS, ensure_ascii=False) + ";/*/PARTNER_POINTS*/", booking_src, count=1, flags=re.S)
booking_src = re.sub(r"/\*PARTNER_LIMITS\*/.*?/\*/PARTNER_LIMITS\*/", lambda m: "/*PARTNER_LIMITS*/var PARTNER_LIMITS = " + json.dumps(_PLIM, ensure_ascii=False) + ";/*/PARTNER_LIMITS*/", booking_src, count=1, flags=re.S)
open(booking_path, "w", encoding="utf-8").write(booking_src)

src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
# トップの料金表とフォームの概算を fares.json から書き込む
# トップの料金表は全国版（Nori 2026-10-31「全国版にしよう」）：表示だけの会社を含む全国の公式の料金表（display_companies.json の fare）で、
# 乗った距離の運賃を Code.gs の displayPrice_ と同じ決まりで計算し、まんなかの会社の金額と、安い会社〜高い会社を出す
def _nat_ride(F, km):
    a, bk = F["base"]
    for t in F["tiers"]:
        lo = max(t[0], bk + 1); hi = min(km, t[1] if t[1] is not None else 10**9)
        if hi >= lo: a += -(-(hi - lo + 1) // (t[3] if len(t) > 3 else 1)) * t[2]
    if re.search("税抜|税別", F.get("tax") or "") and "税込" not in (F.get("tax") or ""): a = -(-a * 11 // 10)
    return a
_NAT = [c for c in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "display_companies.json"), encoding="utf-8"))["companies"]
        if c.get("fare") and c["fare"].get("kind", "dist") == "dist" and c["fare"].get("base")]
_NAT_PREFS = len({c["pref"] for c in _NAT})
def _nat_row(km):
    v = sorted(_nat_ride(c["fare"], km) for c in _NAT)
    mid = v[(len(v) - 1) // 2]
    return f'<div class="row"><dt>{km}km</dt><dd>{mid:,}円<br><small style="font-weight:400">{v[0]:,}〜{v[-1]:,}円</small></dd></div>'
def nat_text(km):
    v = sorted(_nat_ride(c["fare"], km) for c in _NAT)
    return f"{v[(len(v) - 1) // 2]:,}円（{v[0]:,}〜{v[-1]:,}円）"
NAT_NOTES = f"""    <p class="fare-flag"><b>確定料金ではありません。</b>上の金額は目安です。確定料金（税込）は、お迎えが決まったときに引き受けた会社からメールでお知らせします。</p>
    <p class="fare-night"><b>🌙 夜間・早朝の割増</b>上の目安は昼間の料金です。夜間・早朝の割増は、かかるかどうかも金額も会社ごとに違います。フォームの候補には、会社ごとの割増を入れた目安が出ます。</p>
    <p class="small">全国{_NAT_PREFS}都道府県・{len(_NAT)}社のペットタクシーが公式サイトにのせている料金表で、乗った距離の運賃（片道）を計算しました。大きい数字はまんなかの会社の金額で、その下は安い会社〜高い会社です。お迎え料金・待ち時間・夜間の割増・高速代・駐車場代は入っていません。フォームにお迎えの場所と行き先を入れると、来てもらえる会社ごとに、お迎え料金なども入れた目安が出ます。運賃は当日、ペットタクシーへ直接お支払いください（当サイトへのお支払いはありません）。都道府県ごとの料金の例は、<a href="/area/">全国のペットタクシー情報</a>にまとめています。</p>"""
TOP_TABLE = f"""        <h3>距離ごとの目安（全国{len(_NAT)}社の料金表から）</h3>
        <dl>
""" + "".join(f"          {_nat_row(k)}\n" for k in (5, 10, 20, 30, 50)) + f"""        </dl>
      </div>
    </div>
{NAT_NOTES}"""
src = re.sub(r"<!--FARE_TABLE-->.*?<!--/FARE_TABLE-->", lambda m: "<!--FARE_TABLE-->" + TOP_TABLE + "<!--/FARE_TABLE-->", src, count=1, flags=re.S)
EMG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "emergency.json"), encoding="utf-8"))
EMG = {"checked": EMG["checked"], "taxis": EMG["taxis"], "hospitals": EMG["hospitals"]}
src = re.sub(r"/\*EMG\*/.*?/\*/EMG\*/", lambda m: "/*EMG*/var EMG = " + json.dumps(EMG, ensure_ascii=False) + ";/*/EMG*/", src, count=1, flags=re.S)
src = re.sub(r"/\*FARES\*/.*?/\*/FARES\*/", lambda m: "/*FARES*/" + FARE_JS + "/*/FARES*/", src, count=1, flags=re.S)
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(src)
TOP_HTML = src  # 地域ページの元（下の clone_top）。src はあとで別の用途に使われるので写しておく
css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
extra_css = """
/* エリア別ページ */
.crumb{font-size:.78rem;color:var(--ink-3);padding:14px 0 0}
.crumb a{color:var(--ink-3);text-decoration:none}
.crumb a:hover{text-decoration:underline}
.area-hero{background:radial-gradient(90% 70% at 100% 0%,#ffe2cc 0%,rgba(255,226,204,0) 60%),var(--cream);padding:24px 0 56px}
.area-hero h1{font-family:var(--round);font-size:1.6rem;font-weight:800;line-height:1.4;margin:18px 0 14px}
.area-hero h1 small{display:block;font-size:.95rem;color:var(--o-d);margin-bottom:6px}
.area-hero .lede{color:var(--ink-2);margin:0 0 22px}
.prose{max-width:780px;margin:0 auto}
.prose h2{font-size:1.4rem;margin:0 0 16px}
.prose h3{font-size:1.08rem;margin:26px 0 8px}
.prose p{color:var(--ink-2)}
.terms h2{font-size:1.1rem!important;margin:30px 0 10px!important}
.terms ul{color:var(--ink-2);padding-left:1.2em}
.terms .small{font-size:.8rem;color:var(--ink-3);margin-top:30px}
.count{display:flex;gap:14px;align-items:center;background:#fff;border-radius:var(--r);padding:18px 20px;box-shadow:var(--shadow);margin:22px 0}
.count b{font-family:var(--round);font-size:2.2rem;color:var(--o-d);line-height:1}
.count span{font-size:.88rem;color:var(--ink-2);line-height:1.6}
.other{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:0;justify-content:center}
.other a{display:block;border:1px solid var(--line);border-radius:999px;padding:8px 16px;font-size:.88rem;font-weight:700;color:var(--ink);text-decoration:none;background:#fff}
.other a:hover{border-color:var(--o);color:var(--o-d)}
/* ガイド */
.art{max-width:760px;margin:0 auto}
.art h2{scroll-margin-top:90px;font-size:1.35rem;margin:44px 0 14px;padding-left:14px;border-left:5px solid var(--o);line-height:1.45}
.art p{color:var(--ink-2);margin:0 0 16px}
.art ul,.art ol{color:var(--ink-2);padding-left:1.4em;margin:0 0 18px}
.art li{margin:6px 0}
.art .tip{background:var(--o-l);border-radius:18px;padding:16px 18px;color:var(--ink);font-weight:600;margin:0 0 18px}
.art nav.art-toc::before{display:none}
.art .tip::before{content:"POINT";display:block;font-size:.72rem;letter-spacing:.12em;color:var(--o-d);font-weight:800;margin-bottom:4px}
.art .tbl{overflow-x:auto;margin:0 0 18px}
.art table{border-collapse:collapse;width:100%;font-size:.78rem;line-height:1.5;background:#fff}
.art th,.art td{border:1px solid var(--line);padding:8px 4px;text-align:center}
@media (min-width:600px){.art table{font-size:.88rem}.art th,.art td{padding:10px 8px}}
.art th{background:#f7f4f1}
.art td:last-child,.art th:last-child{background:var(--o-l);font-weight:700}
.art .btn{margin:8px 0 18px}
.art-img{margin:0 0 8px;border-radius:24px;overflow:hidden;aspect-ratio:3/2;background:var(--cream)}
.art-img img{width:100%;height:100%;object-fit:cover;display:block}
.art .emg h3.emg-h{color:#c0392b;font-size:1.05rem;margin:18px 0 6px}
.art .emg h3.emg-h:first-child{margin-top:0}
.src{font-size:.8rem;color:var(--ink-3);border-top:1px solid var(--line);margin-top:36px;padding-top:16px}
.src ul{padding-left:1.2em}
.src a{color:var(--ink-3)}
@media (min-width:760px){.art h2{font-size:1.55rem}}
@media (min-width:760px){.area-hero{padding:32px 0 80px}.area-hero h1{font-size:2.5rem}.prose h2{font-size:1.7rem}}
"""
open(os.path.join(ROOT, "style.css"), "w", encoding="utf-8").write(css.strip() + "\n" + extra_css.strip() + "\n")

# ── 地域ページ＝トップと同じページ（Nori 2026-10-31「ペットタクシー 神奈川 で検索されたページもトップと同じに」）──
# トップの index.html をそのまま写し、title・説明文・canonical・h1・リード文・構造化データだけ地域ごとに変え、
# フォームのお迎えの都道府県を最初から選んだ状態にする。地域の説明（料金の目安・主な市区・よくある質問など）は
# フォームのすぐ後ろに差し込む。トップの中身を直せば、地域ページも gen_areas.py の実行でそろう。
def clone_top(title, desc, url, ld_html, kicker, lede, pref, area_html, crumb):
    t = TOP_HTML
    t = re.sub(r"<title>.*?</title>", lambda m: f"<title>{e(title)}</title>", t, count=1, flags=re.S)
    t = re.sub(r'<meta name="description" content="[^"]*">', lambda m: f'<meta name="description" content="{e(desc)}">', t, count=1)
    t = re.sub(r'<link rel="canonical" href="[^"]*">', lambda m: f'<link rel="canonical" href="{url}">', t, count=1)
    t = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: f'<meta property="og:title" content="{e(title)}">', t, count=1)
    t = re.sub(r'<meta property="og:description" content="[^"]*">', lambda m: f'<meta property="og:description" content="{e(desc)}">', t, count=1)
    t = re.sub(r'<meta property="og:url" content="[^"]*">', lambda m: f'<meta property="og:url" content="{url}">', t, count=1)
    # 構造化データ：トップの FAQ・サービスは外し、地域のものに入れ替える（運営者・サイトの @graph は残す）
    blocks = re.findall(r'<script type="application/ld\+json">.*?</script>\n?', t, re.S)
    for b in blocks:
        if '"@graph"' not in b: t = t.replace(b, "", 1)
    t = t.replace("</head>", ld_html + "\n</head>", 1)
    # 相対パス（img/…）とロゴの「#」を、どの階層でも動く形に
    t = re.sub(r'(src|srcset|href)="img/', r'\1="/img/', t)
    t = t.replace('<a class="logo" href="#">', '<a class="logo" href="/">', 1)
    # h1 とリード文
    t = re.sub(r'(<span class="kicker">).*?(<b )', lambda m: m.group(1) + e(kicker) + " " + m.group(2), t, count=1, flags=re.S)
    t = re.sub(r'(<section class="hero">.*?<p class="lede">).*?(</p>)', lambda m: m.group(1) + e(lede) + m.group(2), t, count=1, flags=re.S)
    t = t.replace('<section class="hero">', f'<div class="wrap"><nav class="crumb" aria-label="パンくずリスト">{crumb}</nav></div>\n<section class="hero">', 1)
    # フォームのお迎えの都道府県・緊急タブの都道府県を最初から選んでおく
    t = re.sub(r'(<select id="pref"[^>]*>.*?)<option>' + re.escape(pref) + '</option>', lambda m: m.group(1) + f'<option selected>{pref}</option>', t, count=1, flags=re.S)
    t = re.sub(r'(<select id="emgPref"[^>]*>.*?)<option>' + re.escape(pref) + '</option>', lambda m: m.group(1) + f'<option selected>{pref}</option>', t, count=1, flags=re.S)
    # 地域の説明はフォームの後ろ（「使い方」の前）に
    t = t.replace('<section id="how">', area_html + '\n<section id="how">', 1)
    # エリアページ用のCSS（.crumb .prose など）を足す
    t = t.replace("</style>", extra_css.strip() + "\n</style>", 1)
    assert t.count(f"<option selected>{pref}</option>") == 2, pref
    assert f"<title>{e(title)}</title>" in t, title
    return t

AREAS = [
 dict(slug="tokyo", places=["jarmec-tokyo-taxi","jamc-shibuya-taxi"], pref="東京都", short="東京", count=17,
  title="東京のペットタクシー｜料金の目安と無料見積もり（23区の通院・高度医療センター・羽田空港）",
  desc="東京都の犬・猫のペットタクシーの空き状況と料金を無料で問い合わせ。世田谷・渋谷・足立など23区から八王子・町田まで。かかりつけの動物病院への通院、日本動物高度医療センター東京病院など専門の病院、羽田空港やお引っ越しの移動に。料金の目安を見て何社にでもまとめて問い合わせ、返事を見てから予約できます。",
  lede="23区の動物病院への通院から、お引っ越し、羽田空港への送迎まで。フォームに入れると、来てもらえる会社と料金の目安が出て、何社にでもまとめて空き状況と料金を問い合わせできます。",
  body=[
   ("東京でペットタクシーを使う理由", "東京23区は動物病院の数が多い一方、電車やバスにペットを乗せるにはキャリーに入れる決まりがあり、大型犬はそもそも乗れません。一般のタクシーも、ペット連れだと断られることがあります。ペット専用のタクシーなら、ケージや介護用のマットを積んだ車で、犬も猫もそのまま乗れます。"),
   ("犬のタクシー・猫のタクシー、東京で多い使い方", "世田谷区や目黒区から専門の動物病院への通院、お引っ越しのときの長距離移動、羽田空港からの国内線での帰省などが多い使い方です。飼い主さんが仕事で付き添えない日に、ペットだけを病院やペットホテルへ送ることもできます。"),
  ],
  cities=["世田谷区","墨田区","渋谷区","新宿区","港区","目黒区","品川区","大田区","杉並区","練馬区","江東区","江戸川区","足立区","板橋区","中野区","八王子市","町田市","府中市","調布市","立川市"],
  route=("世田谷区 → 羽田空港", 18),
  faq=[
   ("東京23区内の動物病院まで、ペットタクシーはいくらですか？", f"距離で決まることが多く、全国の会社の料金表で計算すると、5kmで{nat_text(5)}、10kmで{nat_text(10)}が片道の目安です（まんなかの会社の金額と、安い会社〜高い会社）。会社が引き受けたら、一般道の場合と高速道路を使う場合の確定料金（税込）をメールでお知らせします。"),
   ("羽田空港への送迎はできますか？", f"はい。世田谷区から羽田空港（約18km）なら{nat_text(18)}が片道の目安です。飛行機に乗せる場合は、航空会社のペット預かりの受付時間に間に合うよう、メモ欄にフライトの時刻を書いてください。"),
   ("東京で夜間や早朝のお迎えも頼めますか？", "フォームは24時間送れますが、会社への確認はメールで行うため、連絡はすべてメールです。夜間・早朝は引き受けられる会社が見つからないこともあるため、早めのご予約をおすすめします。" + night_text("東京都") + "急な体調不良で一刻を争うときは、まず動物病院に電話してください。"),
  ]),
 dict(slug="kanagawa", places=["jarmec-kawasaki-taxi","wancott-taxi"], pref="神奈川県", short="神奈川・横浜", h1="神奈川・横浜・川崎", count=5,
  title="神奈川・横浜・川崎のペットタクシー｜料金の目安と無料見積もり（通院・専門病院・羽田空港）",
  desc="横浜・川崎・相模原・藤沢など神奈川県の犬・猫のペットタクシーの空き状況と料金を無料で問い合わせ。坂の多い住宅地からの通院、日本動物高度医療センター川崎本院や都内の専門病院、羽田空港への移動に。料金の目安を見て何社にでもまとめて問い合わせ、返事を見てから予約できます。当日の依頼もできます。",
  lede="横浜・川崎から湘南エリアまで。動物病院への通院や、都内の専門病院への移動、羽田空港への送迎に。お迎えの場所を入れると、来てもらえる会社と料金の目安が出ます。",
  body=[
   ("神奈川・横浜・川崎でペットタクシーを使う理由", "横浜市や川崎市は坂道や丘の上の住宅地が多く、大型犬やシニアの子を連れて歩いたり、公共交通で移動したりするのは大変です。ペットタクシーなら玄関先まで迎えに来てくれるので、抱っこやキャリーで長く歩かせる必要がありません。"),
   ("川崎・横浜から都内への移動も", "神奈川から東京の専門病院や二次診療の動物病院へ通う方も多くいます。お迎えに来られる会社と料金の目安がフォームに出るので、気になる会社を選んで、空き状況と料金を問い合わせできます。"),
  ],
  cities=["横浜市","川崎市","相模原市","藤沢市","横須賀市","鎌倉市","茅ヶ崎市","大和市","厚木市","平塚市","海老名市","小田原市"],
  route=("横浜駅周辺 → 羽田空港", 25),
  faq=[
   ("横浜から都内の動物病院まで頼めますか？", f"はい。県をまたぐ移動にも対応しています。横浜から都内までの20〜30kmなら、20kmで{nat_text(20)}、30kmで{nat_text(30)}が片道の目安です。"),
   ("川崎市からでもペットタクシーを予約できますか？", "はい。川崎市からのお迎えも選べます。場所・日時・ペットの大きさなどの条件に合う事業者と料金の目安を表示し、その中から何社でも選んで、空き状況と料金を問い合わせできます。会社から返事が届いたら、納得してから予約できます。"),
   ("湘南エリア（藤沢・茅ヶ崎・鎌倉）でも使えますか？", "はい、お迎えの場所に入れられます。会社ごとに対応する地域が違うため、場所によってはお迎え料金が増えたり、来てもらえる会社が見つからなかったりすることがあります。日にちに余裕をもってご依頼ください。"),
   ("大型犬をスロープ付きの車で運んでもらえますか？", "フォームに体重と犬種を入れていただくと、大型犬を受けている会社だけをご案内します。スロープの有無は会社や車によって違うので、必要なときはメモ欄に書いてください。"),
  ]),
 dict(slug="chiba", places=["doggys-island-taxi"], pref="千葉県", short="千葉", count=4,
  title="千葉のペットタクシー｜料金の目安と無料見積もり（船橋・松戸の通院・成田空港）",
  desc="千葉市・船橋・松戸・柏・佐倉・成田など千葉県の犬・猫のペットタクシーの空き状況と料金を無料で問い合わせ。車を使えない日の動物病院への通院、成田空港への送迎、都内の専門病院や八街のドギーズアイランドへの移動に。料金の目安を見て何社にでもまとめて問い合わせ、返事を見てから予約できます。",
  lede="船橋・松戸・柏の住宅街から、佐倉・四街道・成田まで。動物病院への通院や成田空港への送迎に。お迎えの場所を入れると、来てもらえる会社と料金の目安が出ます。",
  body=[
   ("千葉でペットタクシーを使う理由", "千葉県は車での移動が中心の地域が多く、車を持っていないご家庭や、運転できない日には通院の手段が限られます。佐倉・四街道・富里などでは、近くに夜間の動物病院が少なく、離れた病院まで移動することもあります。ペットタクシーなら、自宅から病院まで直接送ってもらえます。"),
   ("成田空港・都内への長距離移動にも", "成田空港からの帰省やお引っ越し、都内の専門病院への通院など、長い距離の移動も多い地域です。長い距離は、会社のお見積りになることがあります。"),
  ],
  cities=["千葉市","船橋市","松戸市","柏市","市川市","浦安市","佐倉市","四街道市","成田市","八千代市","習志野市","富里市","印西市","流山市"],
  route=("船橋市 → 成田空港", 45),
  faq=[
   ("佐倉や四街道からでもペットタクシーは来てくれますか？", "お迎えの場所を入れると、来てもらえる会社が出ます。会社ごとに対応する地域が違うので、見つからないこともあります。お選びいただいた会社が難しいときは、ほかの会社へ勝手に回さず、メールでお知らせします。"),
   ("成田空港まで運んでもらえますか？", f"はい。船橋市から成田空港までの約45kmなら、{nat_text(45)}が片道の目安です。フライトの時刻をメモ欄に書いてください。"),
   ("千葉から都内の病院へ通えますか？", "はい。県をまたぐ移動にも対応しています。病院への往復なら「往復」を選んで、帰りの時刻（診察が終わるころ）を入れてください。待っていてもらうか、あらためて迎えに来てもらうかは、安いほうを引き受けた会社がご案内します。"),
  ]),
 dict(slug="saitama", places=["jsamc-tokorozawa-taxi"], pref="埼玉県", short="埼玉", count=3,
  title="埼玉のペットタクシー｜料金の目安と無料見積もり（さいたま・川口・所沢の通院）",
  desc="さいたま市・川口・越谷・所沢・川越など埼玉県の犬・猫のペットタクシーの空き状況と料金を無料で問い合わせ。所沢の日本小動物医療センターや都内の専門病院への通院、家族が付き添えない日の移動に。料金の目安を見て何社にでもまとめて問い合わせ、返事を見てから予約できます。",
  lede="さいたま市・川口から川越・所沢まで。動物病院への通院や都内の専門病院への移動に。お迎えの場所を入れると、来てもらえる会社と料金の目安が出ます。",
  body=[
   ("埼玉でペットタクシーを使う理由", "埼玉県は都内へ通う方が多く、平日の昼間は家族が付き添えないことがよくあります。ペットタクシーなら、飼い主さんが乗れない日でも、ペットだけを病院やトリミング、ペットホテルへ送ってもらえます。"),
   ("さいたま市から都内の専門病院へ", "大宮・浦和から都内の二次診療の動物病院へ通う方もいます。お迎えに来られる会社と料金の目安がフォームに出るので、気になる会社を選んで、空き状況と料金を問い合わせできます。"),
  ],
  cities=["さいたま市","川口市","越谷市","所沢市","川越市","草加市","春日部市","戸田市","上尾市","熊谷市"],
  route=("大宮駅周辺 → 新宿区", 30),
  faq=[
   ("さいたま市から都内まで頼めますか？", f"はい。大宮周辺から新宿までの約30kmなら、{nat_text(30)}が片道の目安です。"),
   ("飼い主が乗らずにペットだけ運んでもらえますか？", "フォームの「一緒に乗る人数」で「0人（ペットだけ）」を選んでください。ペットだけの送迎を受けるかは会社によるため、引き受けが決まったメールでご確認ください。"),
   ("埼玉の北部（熊谷など）でも使えますか？", "はい、お迎えの場所に入れられます。会社ごとに対応する地域が違うため、場所によってはお迎え料金が増えたり、来てもらえる会社が見つからなかったりすることがあります。日にちに余裕をもってご依頼ください。"),
  ]),
]

PAW = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="6" cy="9" r="2.2"/><circle cx="10" cy="5.5" r="2.2"/><circle cx="14" cy="5.5" r="2.2"/><circle cx="18" cy="9" r="2.2"/><path d="M12 11c-3 0-6 3.6-6 6.2 0 1.8 1.5 2.8 3 2.8 1.2 0 2-.6 3-.6s1.8.6 3 .6c1.5 0 3-1 3-2.8C18 14.6 15 11 12 11z"/></svg>'
ARROW = '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h12M11 5l5 5-5 5"/></svg>'
CHECK = '<span><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8.5l3 3 7-7"/></svg></span>'
e = html.escape

def area_links(cur=None):
    return '<ul class="other">' + ''.join(
        f'<li><a href="/{a["slug"]}/">{e(a["short"])}のペットタクシー</a></li>' for a in AREAS if a["slug"] != cur) + '<li><a href="/area/">ほかの道府県（全国）</a></li></ul>'

def head(title, desc, url, extra_ld, og_img="/img/hero.jpg", og_w=1200, og_h=900):
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="max-image-preview:large">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="ペットタクシー予約窓口">
<meta property="og:locale" content="ja_JP">
<meta property="og:image" content="{SITE}{og_img}">
<meta property="og:image:width" content="{og_w}">
<meta property="og:image:height" content="{og_h}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#ff6a1a">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
<script src="/ga.js"></script>
{extra_ld}
</head>
<body>
<header class="top">
  <div class="wrap">
    <a class="logo" href="/"><i>{PAW}</i>ペットタクシー予約窓口</a>
    <nav><a href="/#how">使い方</a><a href="/#area">エリア</a><a href="/#price">料金</a><a href="/guide/">ガイド</a><a href="/#faq">よくある質問</a></nav>
    <a class="mini" href="/#form">問い合わせる<span class="lg">（無料）</span></a>
  </div>
</header>
'''

PARTNER_BAND = '''<aside class="partner-band"><div class="wrap"><p><b>ペットタクシー会社の方へ</b>いっしょにペットと飼い主さんをお迎えしてくださる会社を探しています。</p><a href="/partner/">提携のご案内</a></div></aside>
'''

def foot(cta_href, band=True):
    return (PARTNER_BAND if band else '') + f'''<footer>
  <div class="wrap">
    <nav><a href="/">トップ</a><a href="/#how">使い方</a><a href="/#price">料金の目安</a><a href="/guide/">ペットの移動ガイド</a><a href="/#faq">よくある質問</a><a href="/emergency/">緊急のときの連絡先</a><a href="/area/">全国のペットタクシー情報</a><a href="/#policy">キャンセルについて</a><a href="/#privacy">個人情報の取り扱い</a><a href="/terms/">利用規約</a><a href="/#operator">運営者情報</a><a href="/contact/">お問い合わせ</a><a href="/partner/">提携をご希望の会社さま</a></nav>
    <nav><a href="/area/">全国</a>{''.join(f'<a href="/{a["slug"]}/">{e(a["short"])}</a>' for a in AREAS)}</nav>
    <p>ペットタクシー予約窓口</p>
    <p>&copy; 2026 ペットタクシー予約窓口</p>
  </div>
</footer>
<div class="sticky"><a class="btn" href="{cta_href}">空き状況と料金を問い合わせる（無料）</a></div>
</body>
</html>
'''

# ガイド（/guide/）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guides import GUIDES
GBY = {g["slug"]: g for g in GUIDES}

def guide_cards(slugs, cls=""):
    return f'<ul class="gcards {cls}">' + "".join(
        f'<li><a href="/guide/{s}/"><b>{e(GBY[s]["title"])}</b><span>{e(GBY[s]["lede"])}</span></a></li>' for s in slugs) + '</ul>'

for a in AREAS:
    url = f'{SITE}/{a["slug"]}/'
    cta = f'/?pref={a["pref"]}#form'
    ld = [
      {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":a["short"]+"のペットタクシー","item":url}]},
      {"@context":"https://schema.org","@type":"Service","name":a["short"]+"のペットタクシー手配","serviceType":"ペットタクシーの手配（犬のタクシー・猫のタクシー）","url":url,
       "description":a["desc"],"provider":{"@type":"Organization","@id":SITE+"/#org","name":"ペットタクシー予約窓口","url":SITE+"/"},
       "areaServed":{"@type":"AdministrativeArea","name":a["pref"]},
       "offers":{"@type":"Offer","price":"0","priceCurrency":"JPY","description":"無料（運賃は事業者へ直接お支払い）"}},
      {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":ans}} for q,ans in a["faq"]]},
    ]
    ld_html = "\n".join('<script type="application/ld+json">\n' + json.dumps(x, ensure_ascii=False, indent=1) + '\n</script>' for x in ld)
    body = "".join(f'<h2>{e(h)}</h2><p>{e(p)}</p>' if i == 0 else f'<h3>{e(h)}</h3><p>{e(p)}</p>' for i,(h,p) in enumerate(a["body"]))
    area_html = f'''<!-- 地域の説明（gen_areas.py の AREAS） -->
<section id="area-info">
  <div class="wrap prose">
    {body}
    <h3>{e(a["short"])}でよく行く病院・施設への行き方</h3>
    <p>この地域から通う方が多い専門の病院や施設への行き方・頼むときに伝えることを、施設ごとにまとめています。</p>
    {guide_cards(a["places"])}
    <h3>こんなときにも</h3>
    <ul><li><a href="/guide/discharge-transfer/">{e(GBY["discharge-transfer"]["title"])}</a></li><li><a href="/guide/nervous-pet/">{e(GBY["nervous-pet"]["title"])}</a></li><li><a href="/guide/airport-moving/">{e(GBY["airport-moving"]["title"])}</a></li><li><a href="/guide/farewell/">{e(GBY["farewell"]["title"])}</a></li></ul>
    <div class="count"><b>0<small style="font-size:.9rem">円</small></b><span>当サイトのご利用料です。当日の依頼もできます。会社から空き状況と料金の返事が届いたら、メールでお知らせします。運賃はペットタクシーへ直接お支払いください。</span></div>
  </div>
</section>

<section class="scenes">
  <div class="wrap">
    <div class="sh"><span class="eyebrow">AREA</span><h2>{e(a["short"])}の対応エリア</h2><p>{e(a["pref"])}のお迎えは、上のフォームでさがせます。下は主な市区です。引き受けられるかは、場所・日時・車の条件を見て会社が決めます。</p></div>
    <div class="area" style="background:#fff;max-width:780px;margin:0 auto"><h3>{e(a["pref"])}</h3><ul class="chips">{''.join(f'<li>{e(c)}</li>' for c in a["cities"])}</ul></div>
  </div>
</section>

<section class="price">
  <div class="wrap">
    <div class="sh"><span class="eyebrow">PRICE</span><h2>{e(a["short"])}のペットタクシー料金の目安</h2><p>お支払いはペットタクシーの運賃だけ。当サイトは無料です。</p></div>
    <div class="price-wrap">
      <div class="free"><div class="t"><b>ご利用料</b>何度使っても</div><div class="v">0<small>円</small></div></div>
      <div class="fare">
        <h3>乗る距離（道のり）ごとの目安（全国{len(_NAT)}社の料金表から）</h3>
        <dl>
{''.join(f"          {_nat_row(k)}" + chr(10) for k in (5, 10, 20, 30, 50))}        </dl>
        <h3>たとえば</h3>
        <dl><div class="row"><dt>{e(a["route"][0])}<br>（道のり約{a["route"][1]}km）</dt><dd>{nat_text(a["route"][1])}</dd></div></dl>
      </div>
    </div>
{NAT_NOTES}
  </div>
</section>

<section class="faq">
  <div class="wrap">
    <div class="sh"><span class="eyebrow">FAQ</span><h2>{e(a["short"])}のペットタクシー よくある質問</h2></div>
    <div class="faq-list">
      {''.join(f'<details><summary>{e(q)}</summary><div class="a">{e(ans)}</div></details>' for q,ans in a["faq"])}
    </div>
  </div>
</section>

<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>ほかのエリアのペットタクシー</h2></div>
    {area_links(a["slug"])}
  </div>
</section>
'''
    page = clone_top(a["title"], a["desc"], url, ld_html, f'{a.get("h1", a["short"])}のペットタクシー予約', a["lede"], a["pref"], area_html,
                     f'<a href="/">ペットタクシー予約窓口</a> › {e(a["short"])}のペットタクシー')
    os.makedirs(os.path.join(ROOT, a["slug"]), exist_ok=True)
    open(os.path.join(ROOT, a["slug"], "index.html"), "w", encoding="utf-8").write(page)

def block(b):
    if isinstance(b, str): return f"<p>{e(b)}</p>"
    k, v = b
    if k in ("ul", "ol"): return f"<{k}>" + "".join(f"<li>{e(x)}</li>" for x in v) + f"</{k}>"
    if k == "links": return '<ul>' + "".join(f'<li><a href="{e(u)}">{e(n)}</a></li>' for n, u in v) + '</ul>'
    if k == "tip": return f'<p class="tip">{e(v)}</p>'
    if k == "cta": return f'<a class="btn" href="/#form">{e(v)}{ARROW}</a>'
    if k == "table":
        h, *rows = v
        return '<div class="tbl"><table><thead><tr>' + "".join(f"<th>{e(x)}</th>" for x in h) + '</tr></thead><tbody>' + \
          "".join("<tr>" + "".join((f"<th>{e(x)}</th>" if i == 0 else f"<td>{e(x)}</td>") for i, x in enumerate(r)) + "</tr>" for r in rows) + '</tbody></table></div>'
    raise ValueError(k)

for g in GUIDES:
    url = f'{SITE}/guide/{g["slug"]}/'
    published = g.get("published", PUBLISHED)
    modified = g.get("modified", TODAY)
    caption = f'<figcaption class="small">{e(g["img_caption"])}</figcaption>' if g.get("img_caption") else ""
    checked = f'<p class="small">公式情報の確認日：{e(g["checked"])}</p>\n    ' if g.get("checked") else ""
    ld = [
      {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"ペットの移動ガイド","item":SITE+"/guide/"},
        {"@type":"ListItem","position":3,"name":g["title"],"item":url}]},
      {"@context":"https://schema.org","@type":"Article","headline":g["title"],"description":g["desc"],"url":url,
       "image":f'{SITE}/img/guide/{g["img"]}',"datePublished":published,"dateModified":modified,"inLanguage":"ja",
       "author":{"@id":SITE+"/#org"},"publisher":{"@id":SITE+"/#org"},"mainEntityOfPage":url},
    ]
    if g.get("faq"):
        ld.append({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
          {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":ans}} for q,ans in g["faq"]]})
    ld_html = "\n".join('<script type="application/ld+json">\n' + json.dumps(x, ensure_ascii=False, indent=1) + '\n</script>' for x in ld)
    if g.get("category") == "facility":
        toc = '<nav class="tip art-toc" aria-label="この記事の目次"><b>この記事で分かること</b><ol>' + "".join(
            f'<li><a href="#section-{i}">{e(h)}</a></li>' for i, (h, _) in enumerate(g["sections"], 1)) + '</ol></nav>'
        body = toc + "".join(f'<h2 id="section-{i}">{e(h)}</h2>' + "".join(block(b) for b in bs)
                              for i, (h, bs) in enumerate(g["sections"], 1))
        body += f'<p class="small">{e(g["facility_note"])}</p>'
    else:
        body = "".join(f'<h2>{e(h)}</h2>' + "".join(block(b) for b in bs) for h, bs in g["sections"])
    faq = ""
    if g.get("faq"):
        faq = '<h2>よくある質問</h2><div class="faq-list">' + "".join(f'<details><summary>{e(q)}</summary><div class="a">{e(ans)}</div></details>' for q,ans in g["faq"]) + '</div>'
    src = '<div class="src"><b>参考にした情報</b><ul>' + "".join(f'<li><a href="{e(u)}" rel="noopener" target="_blank">{e(n)}</a></li>' for n,u in g["sources"]) + '</ul><p>内容は公開日時点のものです。ルールや料金は変わることがあるため、ご利用の前に各社の案内をご確認ください。</p></div>' if g["sources"] else ""
    page = head(g["seo_title"] + "｜ペットタクシー予約窓口", g["desc"], url, ld_html, f'/img/guide/{g["img"]}', 1200, 800) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/guide/">ペットの移動ガイド</a> › {e(g["title"])}</nav>
    <h1>{e(g["title"])}</h1>
    <p class="lede">{e(g["lede"])}</p>
    <p class="small">ペットタクシー予約窓口　公開 {published.replace("-", ".")}・更新 {modified.replace("-", ".")}</p>
    <figure class="art-img"><picture><source srcset="/img/guide/{g["img"][:-4]}.webp" type="image/webp"><img src="/img/guide/{g["img"]}" alt="{e(g["img_alt"])}" width="1200" height="800" fetchpriority="high" onerror="this.closest('figure').remove()"></picture>{caption}</figure>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    {body}
    {faq}
    {checked}{src}
  </article></div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>あわせて読みたい</h2></div>
    {guide_cards(g["related"], "three")}
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>エリアごとの料金の目安と対応</h2></div>
    {area_links()}
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="last">
      <h2>大切な家族の移動に、やさしい一台を。</h2>
      <p>無料で使えます。問い合わせただけでは予約は確定しません。会社の返事を見て「この内容で予約する」を押した時点で予約が確定します。</p>
      <a class="btn center" href="/#form">空き状況と料金を問い合わせる（無料）{ARROW}</a>
    </div>
  </div>
</section>
</main>
""" + foot("/#form")
    if g.get("category") == "facility":
        page = page.replace("空き状況と料金を問い合わせる（無料）", "掲載候補を見る").replace(">問い合わせる<span class=\"lg\">（無料）</span><", ">掲載候補を見る<")
        page = page.replace("無料で使えます。問い合わせただけでは予約は確定しません。会社の返事を見て「この内容で予約する」を押した時点で予約が確定します。",
                            "現在は候補の表示のみです。すべての会社への予約依頼を停止しています。")
    os.makedirs(os.path.join(ROOT, "guide", g["slug"]), exist_ok=True)
    open(os.path.join(ROOT, "guide", g["slug"], "index.html"), "w", encoding="utf-8").write(page)

hub_url = SITE + "/guide/"
hub_ld = '<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"ペットの移動ガイド","item":hub_url}]}, ensure_ascii=False, indent=1) + '\n</script>'
hub = head("ペットの移動ガイド｜犬・猫の通院、引っ越し、空港への移動とペットタクシー｜ペットタクシー予約窓口",
  "犬や猫と一緒に移動するときの悩みと、その解決のしかたをまとめたガイドです。動物病院への通院、猫のキャリーの慣らし方、シニア・介護中の子、大型犬、引っ越しや空港への送迎まで。", hub_url, hub_ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › ペットの移動ガイド</nav>
    <h1><small>犬・猫と、安心して出かけるために</small>ペットの移動ガイド</h1>
    <p class="lede">通院、引っ越し、帰省、お別れのとき。家族の一員だからこそ、移動もその子にとって楽な方法を選んであげたい。そのためのヒントをまとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="sh"><h2>病院・施設名から移動を調べる</h2></div>
    <p>通院先や宿泊先ごとの行き方、受付・乗降場所、帰りの手配で確かめたいことをまとめました。</p>
    {guide_cards([g["slug"] for g in GUIDES if g.get("category") == "facility"])}
    <div class="sh"><h2>移動の困りごとから調べる</h2></div>
    {guide_cards([g["slug"] for g in GUIDES if g.get("category") != "facility"])}
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>エリアからさがす</h2></div>
    {area_links()}
  </div>
</section>
</main>
""" + foot("/#form")
open(os.path.join(ROOT, "guide", "index.html"), "w", encoding="utf-8").write(hub)

# 利用規約（/terms/）
from terms import TERMS, TERMS_DATE
def terms_block(v):
    if isinstance(v, tuple) and v[0] == "ul": return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in v[1]) + "</ul>"
    if isinstance(v, tuple) and v[0] == "html": return f"<p>{v[1]}</p>"
    return f"<p>{e(v)}</p>"
terms_url = SITE + "/terms/"
tp = head("利用規約｜ペットタクシー予約窓口", "ペットタクシー予約窓口（ペットタクシーの手配）の利用規約です。サービスの内容、予約の成立、料金とお支払い、キャンセル、責任の範囲などを定めています。", terms_url, "") + f"""
<main>
<section class="area-hero"><div class="wrap"><h1>利用規約</h1><p class="lede">ペットタクシー予約窓口をご利用いただく前に、お読みください。</p></div></section>
<section><div class="wrap prose terms">
{''.join(f'<h2>{e(h)}</h2>' + ''.join(terms_block(v) for v in body) for h, body in TERMS)}
<p class="small">{TERMS_DATE} 制定・2026年10月31日 改定</p>
</div></section>
</main>
""" + foot("/#form")
os.makedirs(os.path.join(ROOT, "terms"), exist_ok=True)
open(os.path.join(ROOT, "terms", "index.html"), "w", encoding="utf-8").write(tp)

# 提携規約（/partner/terms/）。本文は tools/partner_terms.py
from partner_terms import PTERMS, PTERMS_DATE
pterms_url = SITE + "/partner/terms/"
ptp = head("提携規約（ペットタクシー会社さま向け）｜ペットタクシー予約窓口", "ペットタクシー予約窓口と提携してくださるペットタクシー会社さま向けの規約です。問い合わせとお返事、予約の確定、手数料（予約が確定して送迎した分だけ）、個人情報、提携の終了などを定めています。", pterms_url, "") + f"""
<main>
<section class="area-hero"><div class="wrap"><h1>提携規約<small style="display:block;font-size:.95rem;color:var(--o-d)">ペットタクシー会社さま向け</small></h1><p class="lede">当サイトと提携してくださる会社さまとの約束です。お申し込みのあと、この規約をメールでお送りし、同意のお返事をいただいてから提携が始まります。</p></div></section>
<section><div class="wrap prose terms">
{''.join(f'<h2>{e(h)}</h2>' + ''.join(terms_block(v) for v in body) for h, body in PTERMS)}
<p class="small">{PTERMS_DATE} 制定</p>
<p><a href="/partner/">提携のご案内にもどる</a></p>
</div></section>
</main>
""" + foot("/partner/#apply", band=False)
ptp = ptp.replace('<div class="sticky"><a class="btn" href="/partner/#apply">空き状況と料金を問い合わせる（無料）</a></div>', '<div class="sticky"><a class="btn" href="/partner/#apply">提携を申し込む（無料）</a></div>')
os.makedirs(os.path.join(ROOT, "partner", "terms"), exist_ok=True)
open(os.path.join(ROOT, "partner", "terms", "index.html"), "w", encoding="utf-8").write(ptp)

# お問い合わせ（/contact/）。送り先はトップのフォームと同じ受付の仕組み（kind=contact）
gas = re.search(r'var GAS_URL = "([^"]+)"', open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()).group(1)
contact_url = SITE + "/contact/"
cp = head("お問い合わせ｜ペットタクシー予約窓口", "ペットタクシー予約窓口へのお問い合わせフォームです。ご予約やキャンセル、料金についてのご質問、ペットタクシー会社の方からの提携のご相談はこちらからどうぞ。", contact_url, "") + f"""
<main>
<section class="area-hero"><div class="wrap"><h1>お問い合わせ</h1><p class="lede">ご質問やご相談はこちらからどうぞ。お返事はメールでお送りします。</p></div></section>
<section><div class="wrap" style="max-width:640px">
<div class="form-card">
<form id="contactForm" novalidate>
  <div aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden"><label>空欄のままにしてください<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
  <div class="f"><label for="c_kind">お問い合わせの種類</label>
    <select id="c_kind" name="topic" required><option value="">選んでください</option><option>ご予約について</option><option>キャンセル・変更について</option><option>料金について</option><option>ペットタクシー会社の方（提携のご相談）</option><option>その他</option></select></div>
  <div class="f"><label for="c_name">お名前</label><input type="text" id="c_name" name="name" required autocomplete="name" placeholder="例：山田 花子"></div>
  <div class="f"><label for="c_email">メールアドレス</label><input type="email" id="c_email" name="email" required autocomplete="email" placeholder="例：hanako@example.com"></div>
  <div class="f"><label for="c_id">受付番号<span class="any">わかれば</span></label><input type="text" id="c_id" name="req_id" placeholder="例：PT00042" autocomplete="off"></div>
  <div class="f"><label for="c_msg">お問い合わせ内容</label><textarea id="c_msg" name="message" required rows="6" maxlength="2000"></textarea></div>
  <label class="agree"><input type="checkbox" id="c_agree" required><span><a href="/#privacy">個人情報の取り扱い</a>を確認し、同意します。</span></label>
  <p id="c_err" role="alert" style="display:none;color:#c0392b;font-size:.88rem"></p>
  <button class="btn" type="submit">送信する{ARROW}</button>
  <p class="form-foot">お返事まで数日いただくことがあります。急ぎのご予約の変更は、受付メールのリンクからどうぞ。</p>
</form>
<div id="c_done" style="display:none;text-align:center"><h2 style="font-size:1.2rem">お問い合わせを受け付けました</h2><p>内容を確認して、メールでお返事します。</p></div>
</div>
</div></section>
</main>
<script>
(function(){{
  var GAS_URL = "{gas}";
  var f = document.getElementById("contactForm"), err = document.getElementById("c_err");
  f.addEventListener("submit", function(e){{
    e.preventDefault(); err.style.display = "none";
    if (!f.checkValidity()) {{ var bad = f.querySelector(":invalid"); err.textContent = bad && bad.id === "c_agree" ? "確認のチェックを入れてください。" : "まだ入力されていない項目があります。"; err.style.display = "block"; if (bad) bad.focus(); return; }}
    var body = new URLSearchParams(new FormData(f)); body.append("kind", "contact");
    var btn = f.querySelector("button"); btn.disabled = true;
    fetch(GAS_URL, {{method: "POST", body: body}}).then(function(r){{ return r.json(); }}).then(function(r){{
      if (!r || !r.ok) throw 0;
      f.style.display = "none"; document.getElementById("c_done").style.display = "block";
    }}).catch(function(){{
      btn.disabled = false;
      err.textContent = "うまく送れませんでした。時間をおいてもう一度お試しください。ご予約中の方は、受付メールにご返信いただいてもかまいません。"; err.style.display = "block";
    }});
  }});
}})();
</script>
""" + foot("/#form")
os.makedirs(os.path.join(ROOT, "contact"), exist_ok=True)
open(os.path.join(ROOT, "contact", "index.html"), "w", encoding="utf-8").write(cp)

# 提携のご案内（/partner/）。受け口はお問い合わせと同じ（kind=contact, topic=提携のお申し込み）。項目は message にまとめて送る
partner_url = SITE + "/partner/"
PREFS47 = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"]
PAYS = ["現金", "クレジットカード", "電子マネー・QR決済", "請求書・振込"]
# 手数料の率はサイトに出さない（Nori 2026-11-01）。率はお申し込みのあとメールで案内する
PT_CSS = """<style>
.pt-sec{padding:56px 0}.pt-sec.alt{background:var(--cream)}
.pt-sec h2{font-size:1.4rem;font-weight:800;text-align:center;margin-bottom:10px}
.pt-sec .sub{color:var(--ink-2);text-align:center;max-width:640px;margin:0 auto 28px}
.pt-hero-cta{display:flex;flex-wrap:wrap;gap:10px;margin-top:6px}
.pt-hero-cta a{display:inline-block;padding:12px 22px;border-radius:999px;font-weight:800;text-decoration:none;font-family:var(--round)}
.pt-hero-cta .p{background:var(--o);color:#fff}.pt-hero-cta .s{background:#fff;color:var(--o-d);border:2px solid var(--o-l)}
.pt-badges{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px;padding:0;list-style:none}
.pt-badges li{background:#fff;border:1px solid var(--line);border-radius:999px;padding:4px 14px;font-size:.88rem;font-weight:700}
.pt-merits{display:grid;grid-template-columns:1fr;gap:14px;max-width:980px;margin:0 auto}
.pt-merit{background:#fff;border:1px solid var(--line);border-radius:20px;padding:20px;box-shadow:var(--shadow)}
.pt-merit svg{width:44px;height:44px;display:block;margin-bottom:10px}
.pt-merit h3{font-size:1.05rem;margin-bottom:6px}.pt-merit p{color:var(--ink-2);font-size:.94rem;margin:0}
.pt-flow{list-style:none;margin:0 auto;padding:0;max-width:760px;counter-reset:f}
.pt-flow li{position:relative;padding:0 0 26px 64px;counter-increment:f}
.pt-flow li::before{content:counter(f);position:absolute;left:0;top:0;width:44px;height:44px;border-radius:50%;background:var(--o);color:#fff;font-weight:800;font-family:var(--round);display:flex;align-items:center;justify-content:center;font-size:1.15rem}
.pt-flow li::after{content:"";position:absolute;left:21px;top:48px;bottom:4px;width:2px;background:var(--o-l)}
.pt-flow li:last-child::after{display:none}
.pt-flow .who{display:inline-block;font-size:.74rem;font-weight:800;border-radius:6px;padding:1px 8px;margin-right:6px;vertical-align:2px}
.who.c{background:#e8f3ff;color:#1b5fa8}.who.y{background:var(--o-l);color:var(--o-d)}.who.s{background:#eef7ee;color:#2f7d32}
.pt-flow h3{font-size:1.05rem;display:inline}.pt-flow p{color:var(--ink-2);font-size:.94rem;margin:6px 0 0}
.pt-flow .lock{display:inline-block;margin-top:8px;font-size:.84rem;background:#fff;border:1px dashed var(--ink-3);border-radius:10px;padding:4px 10px;color:var(--ink-2)}
.pt-money{display:grid;grid-template-columns:1fr;gap:10px;max-width:760px;margin:0 auto;align-items:center;text-align:center}
.pt-money .box{background:#fff;border:2px solid var(--line);border-radius:18px;padding:14px 10px;font-weight:800}
.pt-money .box small{display:block;font-weight:400;color:var(--ink-2);font-size:.84rem}
.pt-money .arw{color:var(--o-d);font-weight:800;font-size:.9rem;line-height:1.4}
.pt-money .arw::after{content:"↓";display:block;font-size:1.3rem}
.pt-fee{max-width:760px;margin:24px auto 0;background:#fff;border-radius:20px;border:2px solid var(--o-l);padding:22px}
.pt-fee table{width:100%;border-collapse:collapse;font-size:.95rem}
.pt-fee th,.pt-fee td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.pt-fee th{width:42%;font-weight:700}.pt-fee td b{color:var(--o-d);font-size:1.05rem}
.pt-fee .ex{margin:14px 0 0;font-size:.92rem;color:var(--ink-2)}
.pt-fee .now{margin:14px 0 0;background:var(--o-l);border-radius:12px;padding:10px 14px;font-size:.92rem}
.pt-steps{display:grid;grid-template-columns:1fr;gap:12px;max-width:980px;margin:0 auto;counter-reset:s;list-style:none;padding:0}
.pt-steps li{background:#fff;border-radius:18px;padding:18px;border:1px solid var(--line);counter-increment:s}
.pt-steps li::before{content:"STEP " counter(s);display:block;font-size:.74rem;font-weight:800;letter-spacing:.12em;color:var(--o)}
.pt-steps b{display:block;font-family:var(--round);font-size:1.02rem;margin:2px 0 4px}
.pt-steps span{color:var(--ink-2);font-size:.92rem}
.pt-need{max-width:760px;margin:0 auto;display:grid;grid-template-columns:1fr;gap:12px}
.pt-need div{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px 18px}
.pt-need h3{font-size:1rem;margin-bottom:6px}.pt-need ul{margin:0;padding-left:1.2em;color:var(--ink-2);font-size:.93rem}
.pt-faq{max-width:760px;margin:0 auto}
.pt-faq details{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 16px;margin-bottom:10px}
.pt-faq summary{font-weight:700;cursor:pointer}.pt-faq details p{color:var(--ink-2);font-size:.94rem;margin:8px 0 0}
@media (min-width:760px){.pt-merits{grid-template-columns:repeat(3,1fr)}.pt-steps{grid-template-columns:repeat(4,1fr)}.pt-need{grid-template-columns:1fr 1fr}
 .pt-money{grid-template-columns:1fr auto 1fr auto 1fr}.pt-money .arw::after{content:"→"}.pt-sec h2{font-size:1.7rem}}
</style>"""
def _ic(path):  # メリットのアイコン（線の絵）
    return '<svg viewBox="0 0 48 48" fill="none" stroke="#ff6a1a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="24" cy="24" r="22" fill="#fff1e6" stroke="none"/>' + path + '</svg>'
PT_MERITS = [
 (_ic('<path d="M15 24h18M24 15v18"/><circle cx="24" cy="24" r="12"/>'), "はじめる費用は0円", "登録料・月額料金・掲載料はいただきません。お問い合わせを受け取るのも、お返事するのも無料です。"),
 (_ic('<rect x="12" y="15" width="24" height="18" rx="3"/><path d="M12 18l12 8 12-8"/>'), "電話の対応はいりません", "お問い合わせはメールで届きます。リンクを開いて、お迎え時刻と確定料金（税込）を入れるだけでお返事できます。"),
 (_ic('<path d="M14 16h20l-7 9v8l-6 3V25z"/>'), "条件に合うお問い合わせだけ", "お迎えの都道府県・営業時間・ペットの体重や頭数・ケージなど、会社さまの条件に合うときだけ候補に出ます。"),
 (_ic('<path d="M16 32V20l8-5 8 5v12z"/><path d="M21 32v-6h6v6"/>'), "料金は会社さまが決めます", "サイトの料金は目安です。確定料金はいつも会社さまがお返事で決めます。当サイトが値引きをお願いすることはありません。"),
 (_ic('<path d="M17 25l5 5 10-11"/>'), "受けられないときは返事不要", "空いていないときや条件が合わないときは、そのままにしておいてください。お断りのご連絡もいりません。"),
 (_ic('<circle cx="19" cy="21" r="4"/><circle cx="29" cy="21" r="4"/><path d="M13 33c1-4 4-6 6-6s5 2 6 6M23 33c1-4 4-6 6-6s5 2 6 6"/>'), "決まってからつながる", "飼い主さんのお名前と連絡先は、予約が確定してからお伝えします。運賃のお支払いは、これまでどおり飼い主さんから会社さまへ直接です。"),
]
PT_FAQ = [
 ("本当に電話は使わなくていいですか？", "はい。当サイトからのご連絡は、すべてメールです。予約が確定したあと、飼い主さんとの打ち合わせで会社さまが電話を使うのは自由です。"),
 ("料金表は変えないといけませんか？", "いいえ。いまの料金表のままで大丈夫です。サイトでは会社さまの料金表から目安を計算し、「確定料金ではありません」と添えて表示します。確定料金は会社さまがお返事で決めます。"),
 ("飼い主さんが何社にも問い合わせることはありますか？", "あります。飼い主さんは1社だけに問い合わせることも、条件に合う会社にまとめて問い合わせることもできます。何社かに問い合わせたときは、届いたお返事をくらべて飼い主さんが1社を選びます。選ばれなかったときは「締め切り」のお知らせをお送りします。"),
 ("手数料はいつ、何にかかりますか？", f"予約が確定し、送迎をした1件だけにかかります。確定料金に応じた手数料を、月末にまとめてご請求する予定です。手数料の率は、お申し込みのあとメールでご案内します。お問い合わせを受け取っただけ、お返事しただけ、選ばれなかったときには一切かかりません。いまは無料です。始める日は、30日前までにメールでお知らせします（くわしくは提携規約の第8条）。"),
 ("キャンセルになったら手数料はどうなりますか？", "送迎をしなかったときは、手数料はいただきません。キャンセル料は会社さまのキャンセル規定のとおりで、キャンセル料に手数料をかけることはありません。"),
 ("ほかの予約サイトや自社の予約と一緒に使えますか？", "はい。いまの予約の受け方はそのままで、当サイトのお問い合わせを一つの窓口として足していただくイメージです。"),
 ("もう候補の一覧に名前が出ているのはなぜですか？", "当サイトでは、公式サイトに公開されている料金表と営業時間をもとに、各地の会社を候補として表示しています（問い合わせは送れない「準備中」の表示です）。載せ方の修正や、掲載をやめたいご希望は、お問い合わせからいつでもお知らせください。"),
 ("やめたいときはどうすればいいですか？", "メールでお知らせいただければ、いつでも止められます。違約金などはありません。すでに確定している予約は、最後までお願いします。"),
]
PT_NEED = [
 ("お申し込みでうかがうこと", ["会社名・屋号、ご担当者のお名前、メールアドレス", "お迎えできる都道府県・市区町村", "車の台数と種類、受けられる曜日・時間帯", "料金（料金ページのURLだけでも大丈夫です）", "お支払い方法（現金・カードなど）"]),
 ("わかればうかがうこと", ["動物取扱業の登録番号", "お持ちの事業の許可・届出（旅客の許可、貨物軽自動車運送事業の届出など）", "飼い主さんが同乗できるか、何人までか", "加入している保険（対人・対物、ペットのケガ）", "キャンセル規定・当日の依頼の締め切り"]),
]
pt_merits = "".join(f'<div class="pt-merit">{ic}<h3>{e(t)}</h3><p>{e(d)}</p></div>' for ic, t, d in PT_MERITS)
pt_faq = "".join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in PT_FAQ)
pt_need = "".join(f'<div><h3>{e(h)}</h3><ul>' + "".join(f"<li>{e(x)}</li>" for x in xs) + '</ul></div>' for h, xs in PT_NEED)
pt_ld = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in PT_FAQ]}, ensure_ascii=False) + '</script>'
pp = head("ペットタクシー会社の方へ 提携のご案内｜ペットタクシー予約窓口", "ペットタクシー会社さま向けの提携のご案内です。登録料・月額0円、電話対応なし。飼い主さんからの空き状況と料金のお問い合わせをメールでお届けし、予約が決まってからお名前と連絡先をお伝えします。", partner_url, pt_ld + PT_CSS) + f"""
<main>
<section class="area-hero"><div class="wrap"><h1>ペットタクシー会社の方へ<br>提携のご案内</h1><p class="lede">ペットタクシー予約窓口は、ペットの移動に困っている飼い主さんと、近くのペットタクシー会社さまをおつなぎするサイトです。全国で、いっしょにペットと飼い主さんをお迎えしてくださる会社さまを探しています。</p>
<ul class="pt-badges"><li>登録料・月額 0円</li><li>電話の対応なし</li><li>メールのリンクでお返事</li><li>料金は会社さまが決める</li></ul>
<div class="pt-hero-cta"><a class="p" href="#apply">提携を申し込む</a><a class="s" href="#flow">しくみを見る</a></div></div></section>

<section class="pt-sec"><div class="wrap">
<h2>提携のメリット</h2><p class="sub">いまの営業のしかたはそのままに、メールで届くお問い合わせの窓口を一つ足していただくイメージです。</p>
<div class="pt-merits">{pt_merits}</div>
</div></section>

<section class="pt-sec alt" id="flow"><div class="wrap">
<h2>お問い合わせから予約までの流れ</h2><p class="sub">飼い主さんは、空き状況と確定料金を見てから予約を決めます。会社さまのお返事だけでは予約は決まりません。</p>
<ol class="pt-flow">
<li><span class="who c">飼い主さん</span><h3>候補から会社を選んで問い合わせ</h3><p>お迎えの場所・日時・ペットの情報を入れると、条件に合う会社さまが料金の目安と一緒に並びます。飼い主さんは1社だけ、または条件に合う会社にまとめて問い合わせます。</p></li>
<li><span class="who s">当サイト</span><h3>会社さまへメールでお届け</h3><p>日時・お迎えの場所・行き先・同乗する人数・ペットの種類や体重・頭数・ケージの有無と、料金の目安をお届けします。</p><span class="lock">🔒 この段階では、飼い主さんのお名前と連絡先はお伝えしません</span></li>
<li><span class="who y">会社さま</span><h3>空いていればお返事</h3><p>メールのリンクを開き、お迎え時刻と確定料金（税込・一般道のとき／高速を使うとき）を入れて送るだけです。受けられないときは、何もしなくて大丈夫です。</p></li>
<li><span class="who c">飼い主さん</span><h3>内容を見て予約を確定</h3><p>飼い主さんが「この内容で予約する」を押した時点で予約が確定します。何社かに問い合わせたときは、くらべて1社を選びます。選ばれなかった会社さまには「締め切り」のお知らせが届きます。</p></li>
<li><span class="who y">会社さま</span><h3>飼い主さんと直接やり取りして送迎</h3><p>確定すると、飼い主さんのお名前と連絡先をメールでお知らせします。そのあとの打ち合わせ・送迎・運賃のお受け取りは、会社さまと飼い主さんで直接お願いします。</p></li>
</ol>
</div></section>

<section class="pt-sec" id="fee"><div class="wrap">
<h2>費用とお金の流れ</h2><p class="sub">当サイトが運賃をお預かりすることはありません。お金の流れはいまと同じです。</p>
<div class="pt-money" role="img" aria-label="飼い主さんは運賃を会社さまへ直接支払い、会社さまは予約が確定した送迎の分だけ手数料を月末に当サイトへ支払います">
<div class="box">飼い主さん<small>当サイトの利用は無料</small></div><div class="arw">運賃を<br>当日直接</div><div class="box">会社さま<small>これまでどおり受け取り</small></div><div class="arw">確定した分だけ<br>月末にまとめて</div><div class="box">当サイト<small>確定した送迎の分だけ手数料</small></div>
</div>
<div class="pt-fee"><table>
<tr><th>登録料・月額料金・掲載料</th><td><b>0円</b></td></tr>
<tr><th>お問い合わせの受け取り・お返事</th><td><b>0円</b>（選ばれなかったときも0円）</td></tr>
<tr><th>予約が確定し、送迎をしたとき</th><td>確定料金に応じた手数料を月末にまとめてご請求（予定）。率はお申し込みのあとメールでご案内します</td></tr>
<tr><th>キャンセルで送迎しなかったとき</th><td><b>0円</b>（キャンセル料には手数料をかけません）</td></tr>
</table>
<p class="now">いまは準備中のため、手数料はいただいていません。始める日は、30日前までにメールでお知らせします。それより前に確定した予約にさかのぼってご請求することはありません。くわしくは<a href="/partner/terms/">提携規約</a>の第8条をご覧ください。</p>
</div>
</div></section>

<section class="pt-sec alt"><div class="wrap">
<h2>提携までの4ステップ</h2>
<ol class="pt-steps">
<li><b>このページから申し込む</b><span>下のフォームに、エリア・時間帯・料金などを入れて送ってください（5分ほど）。</span></li>
<li><b>内容の確認</b><span>当サイトで公式サイトなどを拝見し、数日以内にメールでご連絡します。わからない点はメールでおたずねします。</span></li>
<li><b>提携規約に同意</b><span>手数料やご請求のしかた、個人情報の扱いなどを定めた<a href="/partner/terms/">提携規約</a>をメールでお送りします。ご確認のうえ、同意のお返事をください。</span></li>
<li><b>お問い合わせのお届け開始</b><span>候補の一覧で問い合わせできる状態になり、条件に合うお問い合わせがメールで届きはじめます。</span></li>
</ol>
</div></section>

<section class="pt-sec"><div class="wrap">
<h2>お申し込みでうかがうこと</h2><p class="sub">飼い主さんに安心してお選びいただくため、次のことをうかがいます。わからない項目は空けたままで大丈夫です。</p>
<div class="pt-need">{pt_need}</div>
</div></section>

<section class="pt-sec alt"><div class="wrap">
<h2>よくあるご質問</h2>
<div class="pt-faq">{pt_faq}</div>
<p class="sub" style="margin-top:18px">ほかにご不明な点は、<a href="/contact/">お問い合わせ</a>からお気軽にどうぞ（お返事はメールです）。</p>
</div></section>

<section class="pt-sec" id="apply"><div class="wrap" style="max-width:640px">
<h2>提携のお申し込み</h2>
<div class="form-card">
<form id="partnerForm" novalidate>
  <div aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden"><label>空欄のままにしてください<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
  <div class="f"><label for="p_co">会社名・屋号</label><input type="text" id="p_co" data-k="会社名・屋号" required autocomplete="organization"></div>
  <div class="f"><label for="p_name">ご担当者のお名前</label><input type="text" id="p_name" name="name" required autocomplete="name"></div>
  <div class="f"><label for="p_email">メールアドレス<span class="any">飼い主さんからのお問い合わせもここに届きます</span></label><input type="email" id="p_email" name="email" required autocomplete="email"></div>
  <div class="f"><span class="lbl">お迎えできる都道府県</span><div class="checks" id="p_prefs">{''.join(f'<label><input type="checkbox" value="{p}">{p}</label>' for p in PREFS47)}</div></div>
  <div class="f"><label for="p_city">お迎えできる市区町村など<span class="any">わかれば</span></label><input type="text" id="p_city" data-k="市区町村など" placeholder="例：市内全域と、となりの市まで"></div>
  <div class="f"><label for="p_car">車の台数と種類</label><input type="text" id="p_car" data-k="車" required placeholder="例：2台（ワンボックス、軽バン）"></div>
  <div class="f"><label for="p_fare">料金</label><textarea id="p_fare" data-k="料金" required rows="4" placeholder="例：初乗り5kmまで2,200円、以降1kmごとに220円、深夜2割増。料金ページがあればURLだけでも大丈夫です。"></textarea></div>
  <div class="f"><label for="p_hours">受けられる曜日・時間帯</label><input type="text" id="p_hours" data-k="受けられる時間帯" required placeholder="例：毎日 8:00〜20:00"></div>
  <div class="f"><label for="p_emg">夜間や急ぎの依頼</label><select id="p_emg" data-k="夜間・急ぎ"><option>受けていない</option><option>夜間なら受けられる</option><option>当日の依頼も受けられる</option><option>24時間受けられる</option></select></div>
  <div class="f"><span class="lbl">お支払い方法</span><div class="checks" id="p_pays">{''.join(f'<label><input type="checkbox" value="{p}">{p}</label>' for p in PAYS)}</div></div>
  <div class="f"><label for="p_reg">動物取扱業の登録番号<span class="any">わかれば</span></label><input type="text" id="p_reg" data-k="動物取扱業の登録番号" autocomplete="off"></div>
  <div class="f"><label for="p_lic">事業の許可・届出<span class="any">わかれば</span></label><select id="p_lic" data-k="事業の許可・届出"><option value="">選んでください</option><option>一般乗用旅客自動車運送事業の許可（緑ナンバー）</option><option>貨物軽自動車運送事業の届出（黒ナンバー）</option><option>両方</option><option>そのほか・わからない</option></select></div>
  <div class="f"><label for="p_ride">飼い主さんの同乗<span class="any">わかれば</span></label><input type="text" id="p_ride" data-k="飼い主さんの同乗" placeholder="例：2人まで同乗できます"></div>
  <div class="f"><label for="p_ins">加入している保険<span class="any">わかれば</span></label><input type="text" id="p_ins" data-k="保険" placeholder="例：対人・対物無制限、ペットのケガの補償あり"></div>
  <div class="f"><label for="p_cxl">キャンセル規定<span class="any">わかれば</span></label><input type="text" id="p_cxl" data-k="キャンセル規定" placeholder="例：前日まで無料、当日は基本料金の50%。URLだけでも大丈夫です"></div>
  <div class="f"><label for="p_url">ホームページ<span class="any">あれば</span></label><input type="url" id="p_url" data-k="ホームページ" placeholder="https://"></div>
  <div class="f"><label for="p_msg">ほかに伝えたいこと<span class="any">あれば</span></label><textarea id="p_msg" data-k="そのほか" rows="4" maxlength="1000"></textarea></div>
  <label class="agree"><input type="checkbox" id="p_agree" required><span><a href="/#privacy">個人情報の取り扱い</a>を確認し、同意します。提携の内容は<a href="/partner/terms/">提携規約</a>をご覧ください（同意は内容の確認のあと、メールでいただきます）。</span></label>
  <p id="p_err" role="alert" style="display:none;color:#c0392b;font-size:.88rem"></p>
  <button class="btn" type="submit">申し込む{ARROW}</button>
  <p class="form-foot">内容を確認して、数日以内にメールでご連絡します。</p>
</form>
<div id="p_done" style="display:none;text-align:center"><h2 style="font-size:1.2rem">お申し込みを受け付けました</h2><p>内容を確認して、メールでご連絡します。ありがとうございます。</p></div>
</div>
</div></section>
</main>
<script>
(function(){{
  var GAS_URL = "{gas}";
  var f = document.getElementById("partnerForm"), err = document.getElementById("p_err");
  function picked(id){{ return [].map.call(document.querySelectorAll("#" + id + " input:checked"), function(x){{ return x.value; }}); }}
  f.addEventListener("submit", function(e){{
    e.preventDefault(); err.style.display = "none";
    var bad = f.querySelector(":invalid");
    if (!bad && !picked("p_prefs").length) bad = document.querySelector("#p_prefs input");
    if (bad) {{ err.textContent = bad.id === "p_agree" ? "確認のチェックを入れてください。" : bad.type === "checkbox" ? "お迎えできる都道府県を選んでください。" : bad.type === "url" && bad.value ? "ホームページはhttps://から入れてください。" : "まだ入力されていない項目があります。"; err.style.display = "block"; bad.focus(); return; }}
    var lines = [], co = "";
    f.querySelectorAll("[data-k]").forEach(function(x){{
      if (x.id === "p_co") co = x.value.trim();
      if (x.value.trim()) lines.push("【" + x.dataset.k + "】" + x.value.trim());
      if (x.id === "p_city") lines.splice(lines.length - (x.value.trim() ? 1 : 0), 0, "【都道府県】" + picked("p_prefs").join("・"));
      if (x.id === "p_emg") lines.push("【お支払い方法】" + (picked("p_pays").join("・") || "未選択"));
    }});
    var body = new URLSearchParams();
    body.append("kind", "contact"); body.append("topic", "提携のお申し込み（" + co + "）");
    body.append("name", document.getElementById("p_name").value.trim() + "（" + co + "）");
    body.append("email", document.getElementById("p_email").value.trim());
    body.append("message", lines.join("\\n"));
    body.append("website", f.website.value);
    var btn = f.querySelector("button"); btn.disabled = true;
    fetch(GAS_URL, {{method: "POST", body: body}}).then(function(r){{ return r.json(); }}).then(function(r){{
      if (!r || !r.ok) throw 0;
      f.style.display = "none"; document.getElementById("p_done").style.display = "block";
    }}).catch(function(){{
      btn.disabled = false;
      err.textContent = "うまく送れませんでした。時間をおいてもう一度お試しください。"; err.style.display = "block";
    }});
  }});
}})();
</script>
""" + foot("/#form", band=False)
os.makedirs(os.path.join(ROOT, "partner"), exist_ok=True)
pp = pp.replace('<div class="sticky"><a class="btn" href="/#form">空き状況と料金を問い合わせる（無料）</a></div>', '<div class="sticky"><a class="btn" href="#apply">提携を申し込む（無料）</a></div>')
open(os.path.join(ROOT, "partner", "index.html"), "w", encoding="utf-8").write(pp)

# 緊急のときの連絡先（/emergency/）：トップの緊急タブと同じ tools/emergency.json から作る。県ごとの件数は数えない（近くの県の病院も入っているため）
emg_url = SITE + "/emergency/"
top_src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
emg_sel = re.search(r'<select id="emgPref">(.*?)</select>', top_src, re.S).group(1)
emg_regions = [(lab, re.findall(r'<option[^>]*>([^<]+)</option>', body)) for lab, body in re.findall(r'<optgroup label="([^"]+)">(.*?)</optgroup>', emg_sel, re.S)]
emg_tips = re.search(r'<div class="emg-tips">.*?<p class="emg-tips-note">.*?</p>\s*</div>', top_src, re.S).group(0)
def emg_company(x):
    tel = ''.join(f'<a class="emg-tel" href="tel:{t[1].replace("-", "")}">📞 {e(t[1])}{"（" + e(t[0]) + "）" if t[0] else ""}</a>' for t in x.get("tel", []))
    if not tel: tel = '<small>電話番号はリンク先の公式サイトでご確認ください。</small>'
    return (f'<div class="emg-item emg-co" data-prefs="{e(" ".join(x["prefs"]))}"><a href="{e(x["url"])}" target="_blank" rel="noopener"><b>{e(x["name"])}</b></a>'
            f'<small>対応エリア：{e(x["area"])}。{e(x["note"])}</small>{tel}'
            + (f'<div class="emg-score" data-id="{e(x["id"])}"></div>' if x.get("review_query") else '') + '</div>')
def emg_hosp(x):
    # 名前は公式サイトへのリンク。どんな病院か・所在地（公式サイトで確かめたものだけ）と、口コミの星（予約の候補カードと同じしくみ）
    meta = (f'<small class="emg-spec">{e(x["spec"])}</small>' if x.get("spec") else '') + (f'<small>所在地：{e(x["addr"])}</small>' if x.get("addr") else '')
    return (f'<div class="emg-item emg-co"><a href="{e(x["url"])}" target="_blank" rel="noopener"><b>{e(x["name"])}</b></a>'
            f'<small>{e(x["city"])}・{e(x["hours"])}</small>{meta}'
            + (f'<div class="emg-score" data-id="{e(x["id"])}"></div>' if x.get("review_query") else '') + '</div>')
emg_prefs_html = ''
for lab, prefs in emg_regions:
    emg_prefs_html += f'<h3 class="emg-region">{e(lab)}</h3>\n'
    for pf in prefs:
        hs = EMG["hospitals"].get(pf, [])
        inner = ''.join(emg_hosp(h) for h in hs) or '<p class="emg-none">この都道府県の夜間・救急の動物病院は、まだ載せていません。かかりつけの病院におたずねください。</p>'
        emg_prefs_html += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
emg_opts = '<option value="">すべての都道府県</option>' + ''.join(f'<optgroup label="{e(lab)}">' + ''.join(f'<option>{e(pf)}</option>' for pf in prefs) + '</optgroup>' for lab, prefs in emg_regions)
emg_ld = '<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"緊急のときの連絡先","item":emg_url}]}, ensure_ascii=False, indent=1) + '\n</script>'
ep = head("ペットの緊急搬送・動物救急車（緊急のペットタクシー）と夜間の動物病院｜全国の一覧｜ペットタクシー予約窓口",
  "ペットの具合が急に悪くなったときの連絡先。緊急の搬送をしている会社と、夜間・救急の動物病院を、全国47都道府県から探せます。名前と公式サイトへのリンク、受付時間をまとめた無料の一覧です。", emg_url, emg_ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › 緊急のときの連絡先</nav>
    <h1><small>ペットの具合が急に悪くなったら</small>緊急の搬送と、夜間・救急の動物病院</h1>
    <p class="lede">一刻を争う症状のときは、まずかかりつけや夜間・救急の動物病院に電話して、受け入れてもらえるか確かめてください。病院への移動の手段がないときは、緊急の搬送をしている会社に直接ご連絡ください。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。当サイトへのお申し込みやお支払いはありません。料金や受付は、それぞれの会社・病院に直接おたずねください。</p>
      <div class="f"><label for="emgPrefAll">都道府県でしぼりこむ</label><select id="emgPrefAll">{emg_opts}</select></div>
      <p class="emg-sum"><a href="/#emergency">現在地から近い病院を、車で行く時間と一緒にさがす</a></p>
      <h2 class="emg-h">緊急の搬送をしている会社</h2>
      <div id="emgTaxiAll">{''.join(emg_company(t) for t in EMG["taxis"])}</div>
      <p class="emg-none" id="emgTaxiNone" hidden>この都道府県で緊急の搬送をしている会社は、まだ載せていません。</p>
      <h2 class="emg-h">夜間・救急の動物病院</h2>
      <p class="emg-sum">夜間の病院が見つからない県には、近くの県の病院を（県名）つきで載せています。</p>
      {emg_prefs_html}
      {emg_tips}
      <p class="emg-note">当サイトとは別の会社・病院です（{e(EMG["checked"])}時点の情報）。受付時間や対応は変わることがあるので、行く前・頼む前に必ずリンク先でご確認ください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>急ぎでない移動は、予約制のペットタクシーで</h2><p>通院や退院のお迎えなど、前もって決まっている移動は、ペットタクシーを予約できます。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    {area_links()}
  </div>
</section>
</main>
<script>
(function(){{
  var sel = document.getElementById("emgPrefAll");
  sel.addEventListener("change", function(){{
    var v = sel.value, n = 0;
    document.querySelectorAll(".emg-pref").forEach(function(s){{ s.hidden = !!v && s.dataset.pref !== v; }});
    document.querySelectorAll(".emg-region").forEach(function(h){{ h.hidden = !!v; }});
    document.querySelectorAll("#emgTaxiAll .emg-co").forEach(function(d){{ var ok = !v || d.dataset.prefs.split(" ").indexOf(v) >= 0; d.hidden = !ok; if (ok) n++; }});
    document.getElementById("emgTaxiNone").hidden = n > 0;
  }});
}})();
</script>
<script src="/reviews.js" defer></script>
""" + re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))  # 緊急のページでは予約ボタンを画面下に固定しない
os.makedirs(os.path.join(ROOT, "emergency"), exist_ok=True)
open(os.path.join(ROOT, "emergency", "index.html"), "w", encoding="utf-8").write(ep)

# 4都県のほかの道府県（/area/<slug>/）と全国の一覧（/area/）。データは tools/prefs.py。
# 2026-10-31 Nori「東京、神奈川、千葉、埼玉、みたいになってるのを取っ払って」で、4都県だけと読める書き方は外した。料金の例は提携していない会社のものなので社名は出さない。
from prefs import PREFS, FARES as PREF_FARES, FARES_CHECKED
PREF_SLUG = {x[1]: x[0] for x in PREFS}
PREF_SLUG.update({a["pref"]: a["slug"] for a in AREAS})
AREA_SHORT = {a["pref"]: a["short"] for a in AREAS}
def pref_href(pf):
    return f'/{PREF_SLUG[pf]}/' if pf in AREA_SHORT else f'/area/{PREF_SLUG[pf]}/'
pref_hub_url = SITE + "/area/"
# 4都県から行き先にできる県（index.html の BOXNEAR の範囲に主な市が入るところ）。ほかの県は「4都県から◯◯へ」も書かない
NEAR_PREFS = ["茨城県", "栃木県", "群馬県", "山梨県", "長野県", "静岡県"]
NOT_YET = "お迎えの都道府県は全国から選べます。お迎えの場所を入れると、来てもらえる会社と料金の目安が出ます。"
PREF_CHECKS = [
  ("お迎えに来てもらえる場所か", "会社ごとに対応する地域が決まっていて、地域の外はお迎え料金が増えたり、受けてもらえなかったりします。", "what-is-pet-taxi"),
  ("料金の決まり方", "乗る距離の料金のほかに、お迎え料金・待ち時間の料金・夜間や早朝の割増・高速代がかかることがあります。どこまでが基本料金に入っているかは会社ごとに違います。", "what-is-pet-taxi"),
  ("ケージやキャリー", "持っていくのか、借りられるのか、なしでも乗れるのか。猫はキャリーに入れて乗るのが基本です。", "cat"),
  ("大きさと頭数", "大型犬や多頭のときは、車の広さやスロープの有無を前もって伝えておくと安心です。", "large-dog"),
  ("飼い主さんが一緒に乗るか", "ペットだけの送迎を受けるかどうかは会社によって違います。", "hospital"),
  ("支払い方法とキャンセル", "現金だけの会社もあります。払うのが乗る前か降りるときか、キャンセル料がいつからかかるかも確かめましょう。", "what-is-pet-taxi"),
]
def pref_fare_html(pf):
    rows = PREF_FARES.get(pf)
    if not rows:
        return (f'<p>{e(pf)}のペットタクシーの料金は、当サイトではまだ確かめられていません。料金は会社ごとに決まっていて、多くは乗る距離で計算します。'
                'そのほかに、お迎え料金や待ち時間の料金、夜間・早朝の割増がかかることがあります。頼む前に、どこまでが基本料金に入っているかを確かめてください。</p>')
    return ('<p>' + e(pf) + 'のペットタクシー会社が公式サイトに書いている料金の例です。同じ「基本料金」でも、含まれる距離やお迎え・待ち時間の扱いは会社ごとに違います。</p>'
            '<div class="tbl"><table><thead><tr><th>会社のある場所</th><th>乗る料金</th><th>お迎えなど</th></tr></thead><tbody>' +
            ''.join(f'<tr><th>{e(w)}</th><td>{e(f)}</td><td>{e(pk)}</td></tr>' for w, f, pk in rows) + '</tbody></table></div>'
            f'<p class="fare-flag"><b>確定料金ではありません。</b>{FARES_CHECKED}に各社の公式サイトで確かめた料金の例で、当サイトの依頼先の料金ではありません。夜間・早朝の割増や高速代は入っていません。料金は変わることがあるので、頼む前に必ず各社にご確認ください。</p>')
def other_pref(h, pf):  # 近くの県の病院は city の終わりに（◯◯県）が付いている
    m = re.search(r"（([^（）]+[都道府県])）$", h["city"])
    return bool(m) and m.group(1) != pf
def pref_hosp_html(pf):
    hs = EMG["hospitals"].get(pf, [])
    if not hs:
        return '<p class="emg-none">この都道府県の夜間・救急の動物病院は、まだ載せていません。かかりつけの病院におたずねください。</p>'
    inside = [h for h in hs if not other_pref(h, pf)]
    lead = '' if inside else f'<p class="emg-sum">{e(pf)}の中で夜間に診てもらえる病院が見つからなかったため、近くの県の病院を載せています。</p>'
    return lead + ''.join(emg_hosp(h) for h in hs)

# 県ごとのデータ（2026-11-01）：公式サイトの対応エリアにその県がある会社の数と、料金表から計算した運賃。会社名は出さない。
PREF_AIRPORT = {"北海道": "新千歳空港", "宮城県": "仙台空港", "愛知県": "中部国際空港（セントレア）や県営名古屋空港", "大阪府": "伊丹空港（大阪国際空港）や関西国際空港",
                "兵庫県": "神戸空港や伊丹空港", "広島県": "広島空港", "福岡県": "福岡空港や北九州空港", "沖縄県": "那覇空港"}
def pref_data_html(pf, short):
    key = pf if pf == "北海道" else pf[:-1]
    cs = [x for x in _DISP if key in x.get("areas", [])]
    fs = [x for x in cs if x.get("fare") and x["fare"].get("kind", "dist") == "dist" and x["fare"].get("base")]
    out = f'<h2>{e(short)}のお迎えに対応しているペットタクシー</h2>'
    if not cs:
        out += f'<p>当サイトで公式サイトを確かめた会社の中には、対応エリアに{e(pf)}を書いている会社はまだありません（{FARES_CHECKED}時点）。お迎えの場所によっては、となりの県の会社が来られることもあるので、フォームでさがしてみてください。</p>'
    else:
        out += f'<p>当サイトで公式サイトを確かめた全国の会社のうち、対応エリアに{e(pf)}を書いている会社は<b>{len(cs)}社</b>でした（{FARES_CHECKED}時点。同じチェーンのお店は1社ずつ数えています）。対応エリアは「市内だけ」「県の一部だけ」の会社もあるので、お迎えの場所で来てもらえるかは、フォームでさがすと確かめられます。</p>'
    if fs:
        rows = ""
        for km in (5, 10, 20):
            v = sorted(_nat_ride(x["fare"], km) for x in fs)
            mid = v[(len(v) - 1) // 2]
            rows += (f'<tr><th>{km}km</th><td>{mid:,}円</td><td>{v[0]:,}〜{v[-1]:,}円</td></tr>' if len(v) >= 3 else
                     f'<tr><th>{km}km</th><td colspan="2">' + "・".join(f"{x:,}円" for x in v) + '</td></tr>')
        head = '<tr><th>乗った距離</th><th>まんなかの会社</th><th>安い会社〜高い会社</th></tr>' if len(fs) >= 3 else '<tr><th>乗った距離</th><th colspan="2">各社の運賃</th></tr>'
        out += (f'<p>そのうち料金表をのせている{len(fs)}社の料金表で、乗った距離の運賃（片道）を計算すると次のとおりです。</p>'
                f'<div class="tbl"><table><thead>{head}</thead><tbody>{rows}</tbody></table></div>'
                '<p class="fare-flag"><b>確定料金ではありません。</b>お迎え料金・待ち時間・夜間や早朝の割増・高速代は入っていません。フォームにお迎えの場所と行き先を入れると、会社ごとにお迎え料金なども入れた目安が出ます。</p>')
    if pf in PREF_AIRPORT:
        out += f'<p>{e(PREF_AIRPORT[pf])}への送迎は、飛行機の預け入れの受付時間に合わせて、お迎えの時刻を決めておくことが大切です。<a href="/guide/airport-moving/">ペットと引っ越し・空港送迎</a>に、航空会社の決まりと準備をまとめています。</p>'
    out += '<p>同乗できる人数、ペットだけの送迎、ワクチン、キャンセル料、夜間の割増は会社ごとに違います。<a href="/guide/choose/">ペットタクシーの選び方（全国の会社のルールをくらべました）</a>もあわせてご覧ください。</p>'
    return out, len(cs)

for slug, pf, short, cities in PREFS:
    url = f'{SITE}/area/{slug}/'
    data_html, n_cos = pref_data_html(pf, short)
    has_fare = pf in PREF_FARES
    taxis = [t for t in EMG["taxis"] if pf in t["prefs"]]
    hs = EMG["hospitals"].get(pf, [])
    hcities = []
    for h in hs:
        c = h["city"] if other_pref(h, pf) else re.sub(r"（.*?）", "", h["city"])
        if c not in hcities: hcities.append(c)
    title = (f"{short}のペットタクシー｜対応する{n_cos}社の料金・夜間の動物病院・ペットの緊急搬送" if n_cos >= 3 else
             f"{short}のペットタクシー｜料金の例・夜間の動物病院・ペットの緊急搬送" if has_fare else f"{short}のペットタクシーの探し方｜夜間の動物病院・ペットの緊急搬送") + "｜ペットタクシー予約窓口"
    dcities = []  # 説明文用：その県の中の病院の市（政令市の区はまとめる）
    for h in hs:
        if other_pref(h, pf): continue
        c = re.sub(r"^(.+?市).+区$", r"\1", re.sub(r"（.*?）", "", h["city"]))
        if c not in dcities: dcities.append(c)
    desc = (f"{pf}（{'・'.join(cities[:3])}など）で犬・猫のペットタクシーを探す方へ。" + (f"お迎えに対応する{n_cos}社と料金の例、" if n_cos >= 2 else ("公式サイトに書かれた料金の例、" if has_fare else "料金の決まり方、")) +
            "頼む前に確かめること、" + (f"夜間・救急の動物病院（{'・'.join(dcities[:2])}など）" if dcities else ("近くの県の夜間・救急の動物病院" if hs else "夜間・救急の動物病院")) + "とペットの緊急搬送の連絡先をまとめました。")
    ld = '<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
      {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
      {"@type":"ListItem","position":2,"name":"全国のペットタクシー情報","item":pref_hub_url},
      {"@type":"ListItem","position":3,"name":short+"のペットタクシー","item":url}]}, ensure_ascii=False, indent=1) + '\n</script>'
    region = next(lab for lab, ps in emg_regions if pf in ps)
    near = [p for p in next(ps for lab, ps in emg_regions if lab == region) if p != pf]
    hosp_lead = (f"{e(pf)}の夜間・救急の動物病院として、{e('・'.join(hcities[:4]))}の病院を載せています。" if hcities else "")
    taxi_html = (''.join(emg_company(t) for t in taxis) if taxis else
                 f'<p class="emg-none">{e(pf)}で緊急の搬送をしている会社は、まだ載せていません。まずは動物病院に電話して、受け入れと行き方をご相談ください。</p>')
    last = f'''<div class="last">
      <h2>{e(pf)}からのお迎えをさがす</h2>
      <p>上のフォームにお迎えの場所と行き先を入れると、来てもらえる会社と料金の目安が出ます。無料で使えて、当日の依頼もできます（会社にメールで確認するため、お迎えは依頼から3時間以上あと）。会社から空き状況と料金の返事が届いたら、納得してから予約を確定できます。</p>
      <a class="btn center" href="#form">空き状況と料金を問い合わせる（無料）{ARROW}</a>
    </div>'''
    checks = ''.join(f'<h3>{e(h)}</h3><p>{e(t)} <a href="/guide/{g}/">{e(GBY[g]["title"])}</a></p>' for h, t, g in PREF_CHECKS)
    area_html = f'''<!-- 地域の説明（gen_areas.py の PREFS） -->
<section id="area-info" style="padding-top:8px">
  <div class="wrap"><article class="art">
    <p class="fare-flag"><b>{e(pf)}からのお迎えも、上のフォームでさがせます。</b>{NOT_YET}会社ごとに対応する地域が違うので、近くに会社が見つからないこともあります。</p>
    <p class="small">ペットタクシー予約窓口　更新 {TODAY.replace("-", ".")}</p>
    <h2>{e(short)}のペットタクシーの料金{"の例" if has_fare else ""}</h2>
    {pref_fare_html(pf)}
    <p><a href="/guide/what-is-pet-taxi/">ペットタクシーとは？電車・タクシー・マイカーとの違い</a>では、料金のしくみをくわしく説明しています。キャリーに入る小さな子なら、<a href="/guide/taxi-with-pet/">ふつうのタクシーに乗れることもあります</a>。</p>

    {data_html}

    <h2>ペットタクシーを頼む前に確かめること</h2>
    {checks}

    <h2>{e(pf)}の夜間・救急の動物病院と、緊急の搬送</h2>
    <p>一刻を争う症状のときは、まずかかりつけや夜間・救急の動物病院に電話して、受け入れてもらえるか確かめてください。{hosp_lead}</p>
    <div class="emg">
      <h3 class="emg-h">緊急の搬送をしている会社</h3>
      {taxi_html}
      <h3 class="emg-h">夜間・救急の動物病院</h3>
      {pref_hosp_html(pf)}
      <p class="emg-note">当サイトとは別の会社・病院です（{e(EMG["checked"])}時点の情報）。受付時間や対応は変わることがあるので、行く前・頼む前に必ずリンク先でご確認ください。口コミはページ上の「緊急」タブで見られます。</p>
    </div>
    <p><a href="/emergency/">全国の緊急の連絡先の一覧</a>から、現在地から近い病院も探せます。</p>
  </article></div>
</section>

<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>{e(region)}のペットタクシー情報</h2></div>
    <ul class="other">{"".join(f'<li><a href="{pref_href(p)}">{e(AREA_SHORT.get(p) or next(x[2] for x in PREFS if x[1] == p))}</a></li>' for p in near)}<li><a href="/area/">全国の一覧</a></li></ul>
    {last}
  </div>
</section>
'''
    area_html = re.sub(r'<div class="emg-score" data-id="[^"]*"></div>', "", area_html)  # 口コミはトップの緊急タブの仕組みで見る（二重に読み込まない）
    lede = f"{pf}（{'・'.join(cities[:4])}など）で、犬や猫の移動の手段を探している方へ。フォームに入力すると、条件に合う事業者と料金の目安が見られます。急ぐときの連絡先は「緊急」タブにまとめています。"
    page = clone_top(title, desc, url, ld, f"{short}のペットタクシー", lede, pf, area_html,
                     f'<a href="/">ペットタクシー予約窓口</a> › <a href="/area/">全国のペットタクシー情報</a> › {e(short)}')
    os.makedirs(os.path.join(ROOT, "area", slug), exist_ok=True)
    open(os.path.join(ROOT, "area", slug, "index.html"), "w", encoding="utf-8").write(page)

hub_ld2 = '<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"全国のペットタクシー情報","item":pref_hub_url}]}, ensure_ascii=False, indent=1) + '\n</script>'
hub_regions = ""
for lab, ps in emg_regions:
    lis = "".join(f'<li><a href="{pref_href(p)}">{e(AREA_SHORT.get(p) or next(x[2] for x in PREFS if x[1] == p))}</a></li>' for p in ps)
    hub_regions += f'<h3 class="emg-region" style="text-align:center">{e(lab)}</h3><ul class="other">{lis}</ul>'
ph = head("全国のペットタクシー情報｜都道府県ごとの料金の例・夜間の動物病院｜ペットタクシー予約窓口",
  "47都道府県ごとに、ペットタクシーの料金の例や頼む前に確かめること、夜間・救急の動物病院とペットの緊急搬送の連絡先をまとめました。", pref_hub_url, hub_ld2) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › 全国のペットタクシー情報</nav>
    <h1><small>都道府県からさがす</small>全国のペットタクシー情報</h1>
    <p class="lede">犬や猫の移動にペットタクシーを考えている方へ。都道府県ごとに、料金の例、頼む前に確かめること、夜間・救急の動物病院と緊急の搬送の連絡先をまとめています。</p>
    <p class="fare-flag"><b>お迎えの場所から会社をさがせます。</b>{NOT_YET}会社ごとに対応する地域が違うので、近くに会社が見つからないこともあります。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">{hub_regions}</div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>ペットの移動ガイド</h2></div>
    {guide_cards(["what-is-pet-taxi", "taxi-with-pet", "hospital"])}
  </div>
</section>
</main>
""" + foot("/#form")
os.makedirs(os.path.join(ROOT, "area"), exist_ok=True)
open(os.path.join(ROOT, "area", "index.html"), "w", encoding="utf-8").write(ph)

# 緊急の搬送の会社の口コミ（/emergency/ と /area/）：トップの緊急タブ・予約の候補カードと同じ見せ方。星と件数を出し、口コミはページの中で開く。
# 外部の口コミページへのリンクは出さない（Nori 2026-10-31）。画面に入った会社のぶんだけ取り寄せる（取り寄せの回数を抑えるため）
GAS = re.search(r'var GAS_URL = "([^"]+)"', top_src).group(1)
open(os.path.join(ROOT, "reviews.js"), "w", encoding="utf-8").write("""// 生成ファイル（tools/gen_areas.py）。手で直さない
(function(){
  var GAS_URL = %s, memo = {}, queue = [], timer = 0;
  function el(tag, cls, text){ var x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; }
  function toggle(id, panel, btn){
    if (!panel.hidden) { panel.hidden = true; btn.setAttribute("aria-expanded", "false"); return; }
    panel.hidden = false; btn.setAttribute("aria-expanded", "true");
    if (window.gtag) gtag("event", "open_reviews", {});
    if (panel.dataset.done) return;
    panel.textContent = "口コミを読み込んでいます…";
    var body = new URLSearchParams(); body.set("kind", "reviews"); body.set("partner_id", id);
    fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){
      if (!j || !j.ok || !Array.isArray(j.reviews)) throw 0;
      panel.dataset.done = "1"; panel.replaceChildren();
      panel.appendChild(el("p", "review-head", "関連度の高い順に、最大5件を表示しています（全" + j.count + "件）。"));
      j.reviews.forEach(function(v){
        var item = el("div", "review-item"), who = el("div", "review-who");
        if (v.photo) { var img = document.createElement("img"); img.src = v.photo; img.alt = ""; img.width = 28; img.height = 28; img.loading = "lazy"; img.referrerPolicy = "no-referrer"; who.appendChild(img); }
        var name = el(v.authorUrl ? "a" : "span", "", v.author || "投稿者");
        if (v.authorUrl) { name.href = v.authorUrl; name.target = "_blank"; name.rel = "noopener"; }
        who.append(name, el("small", "", "★" + v.rating + (v.when ? "・" + v.when : ""))); item.appendChild(who);
        if (v.text) item.appendChild(el("p", "", v.text));
        if (v.url) { var a = el("a", "review-link", "元の口コミ ↗"); a.href = v.url; a.target = "_blank"; a.rel = "noopener"; item.appendChild(a); } // 規約で口コミごとに必要なリンク
        panel.appendChild(item);
      });
      panel.appendChild(el("p", "partner-review-src", "Google Maps"));
    }).catch(function(){ panel.textContent = "口コミを読み込めませんでした。時間をおいてもう一度お試しください。"; });
  }
  function paint(box, rv){
    box.replaceChildren();
    if (!rv || !(rv.rating > 0)) return; // 点数が取れないときは何も出さない（外部のページへは飛ばさない）
    var r = Math.max(0, Math.min(5, rv.rating)), score = el("p", "partner-score");
    var stars = el("span", "stars"); stars.setAttribute("aria-hidden", "true"); stars.style.setProperty("--fill", r / 5 * 100 + "%%");
    score.setAttribute("aria-label", "口コミの評価 5点中" + Number(rv.rating).toFixed(1) + "点、" + rv.count + "件");
    var open = el("button", "partner-review-open", "口コミ" + rv.count + "件を見る"); open.type = "button"; open.setAttribute("aria-expanded", "false");
    score.append(stars, el("b", "", Number(rv.rating).toFixed(1)), open, el("span", "partner-review-src", "Google Maps")); // 出どころの表示（規約で必要）
    var panel = el("div", "review-panel"); panel.hidden = true;
    open.addEventListener("click", function(){ toggle(box.dataset.id, panel, open); });
    box.append(score, panel);
  }
  function flush(){
    timer = 0;
    var need = queue.filter(function(id, i, a){ return a.indexOf(id) === i && !(id in memo); }); queue = [];
    if (!need.length) return;
    need.forEach(function(id){ memo[id] = null; });
    var body = new URLSearchParams(); body.set("kind", "emg_scores"); body.set("ids", need.join(","));
    fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).catch(function(){ return null; }).then(function(j){
      var sc = (j && j.ok && j.scores) || {};
      need.forEach(function(id){ memo[id] = sc[id] || null; });
      document.querySelectorAll(".emg-score").forEach(function(b){ if (need.indexOf(b.dataset.id) >= 0) paint(b, memo[b.dataset.id]); });
    });
  }
  function want(box){
    if (box.dataset.id in memo) { if (memo[box.dataset.id]) paint(box, memo[box.dataset.id]); return; }
    queue.push(box.dataset.id); if (!timer) timer = setTimeout(flush, 300);
  }
  var boxes = document.querySelectorAll(".emg-score[data-id]");
  if (!boxes.length) return;
  if (!("IntersectionObserver" in window)) { boxes.forEach(want); return; }
  // 口コミの欄は空のあいだ見えないので、会社の枠が画面に入ったら取り寄せる（しぼりこみで隠れている会社は取り寄せない）
  var io = new IntersectionObserver(function(es){ es.forEach(function(x){ if (x.isIntersecting && x.target.offsetParent) { io.unobserve(x.target); want(x.target.querySelector(".emg-score")); } }); }, {rootMargin: "200px"});
  boxes.forEach(function(b){ io.observe(b.parentElement); });
})();
""" % json.dumps(GAS))

# sitemap / robots / 404
urls = [SITE + "/"] + [f'{SITE}/{a["slug"]}/' for a in AREAS] + [hub_url] + [f'{SITE}/guide/{g["slug"]}/' for g in GUIDES] + [emg_url, pref_hub_url] + [f'{SITE}/area/{x[0]}/' for x in PREFS] + [terms_url, contact_url, partner_url, pterms_url]
guide_modified = {f'{SITE}/guide/{g["slug"]}/': g.get("modified", TODAY) for g in GUIDES}
guide_modified[hub_url] = "2026-10-31"
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  "".join(f'  <url><loc>{u}</loc><lastmod>{guide_modified.get(u, TODAY)}</lastmod></url>\n' for u in urls) + '</urlset>\n')
open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\nDisallow: /tools/\nDisallow: /booking/\nDisallow: /docs/\n\nSitemap: {SITE}/sitemap.xml\n")
nf = head("ページが見つかりません｜ペットタクシー予約窓口", "お探しのページは見つかりませんでした。", SITE + "/404.html", '<meta name="robots" content="noindex">') + f'''
<main><section class="area-hero"><div class="wrap" style="text-align:center">
<h1>ページが見つかりませんでした</h1><p class="lede">URLが変わったか、削除された可能性があります。</p>
<a class="btn center" href="/">トップページへ{ARROW}</a></div></section>
<section><div class="wrap"><div class="sh"><h2>エリアからさがす</h2></div>{area_links()}</div></section></main>
''' + foot("/#form")
open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(nf)
print("ok", len(AREAS), "areas,", len(PREFS), "prefs")
