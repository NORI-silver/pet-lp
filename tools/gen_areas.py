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
    tail = "目安には高速代・駐車場代は入っていません。確定料金（税込）は、問い合わせた会社から、空き状況と一緒に、一般道の場合と高速道路を使う場合の両方をお知らせします。運賃は当日、ペットタクシーへ直接お支払いください（当サイトへのお支払いはありません）。" + "".join(c.get("pay", "") for c in cs)
    return head + "".join(c["note"] for c in cs) + FARES.get("area_note", {}).get(pref or "", "") + tail
# フォームの概算（index.html）に渡す料金データ
FARE_JS = "var FARES = " + json.dumps({k: {x: c.get(x) for x in ("label","base_km","base","tiers","pick","back","night","night_hours","round_flat","wait","shop","pick_free_km","pick_over")} for k, c in CO.items()}, ensure_ascii=False) + ";\n  var AREA_FARES = " + json.dumps(FARES["areas"], ensure_ascii=False) + ";"

# 予約側も同じ料金データを使う（Code.gs を貼り直すときに含まれる）。
booking_path = os.path.join(ROOT, "booking", "Code.gs")
booking_src = open(booking_path, encoding="utf-8").read()
booking_src = re.sub(r"/\*SELECTION_FARES\*/.*?/\*/SELECTION_FARES\*/", lambda m: "/*SELECTION_FARES*/var SELECTION_FARES = " + json.dumps({k: {x: v for x, v in c.items() if x != "review_url"} for k, c in CO.items()}, ensure_ascii=False) + ";/*/SELECTION_FARES*/", booking_src, count=1, flags=re.S)
# 緊急タブの搬送の会社の口コミ：場所を探すことばを予約のしくみに渡す（tools/emergency.json の taxis）
_EMG_J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "emergency.json"), encoding="utf-8"))
# 搬送の会社（E01〜）と病院（H001〜。いくつかの県に載っている病院も id は1つ）
_EMG_RV = _EMG_J["taxis"] + [h for l in _EMG_J["hospitals"].values() for h in l]
# 条件でさがす動物病院（/hospital/、tools/hospitals.json）の往診・猫専門の病院も同じしくみで口コミを出す
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_hospitals
from page_images import GUIDE_ALT, AREA_ALT, area_key
import prefkeep
import gen_dogrun
import gen_rojin
import gen_prefpages
import gen_trainers
import gen_sitters
import gen_grooming
import gen_prefcats
import gen_hotels
import gen_sougi
_EMG_RV = _EMG_RV + gen_hospitals.review_rows() + gen_rojin.review_rows() + gen_trainers.review_rows() + gen_sougi.review_rows()
booking_src = re.sub(r"/\*EMG_REVIEWS\*/.*?/\*/EMG_REVIEWS\*/", lambda m: "/*EMG_REVIEWS*/var EMG_REVIEWS = " + json.dumps({t["id"]: {"query": t["review_query"], "name": t["review_name"]} for t in _EMG_RV if t.get("review_query")}, ensure_ascii=False) + ";/*/EMG_REVIEWS*/", booking_src, count=1, flags=re.S)
# 候補カードに表示だけする会社（依頼は送れない）。tools/display_companies.py で作る
_DISP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "display_companies.json"), encoding="utf-8"))["companies"]
booking_src = re.sub(r"/\*DISPLAY_COMPANIES\*/.*?/\*/DISPLAY_COMPANIES\*/", lambda m: "/*DISPLAY_COMPANIES*/var DISPLAY_COMPANIES = " + json.dumps(_DISP, ensure_ascii=False) + ";/*/DISPLAY_COMPANIES*/", booking_src, count=1, flags=re.S)
def _ncos(k): return len([x for x in _DISP if k in x.get("areas", [])])
def _ccos(k, stem): return len([x for x in _DISP if k in x.get("areas", []) and stem in (x.get("area_text") or "")])
def _n24(k): return len([x for x in _DISP if k in x.get("areas", []) and x.get("hours") == "0-24"])
def _nbig(k): return len([x for x in _DISP if k in x.get("areas", []) and any("大型犬" in t for t in (x.get("points") or []) + (x.get("limits") or []))])
# [B] SEO 11/13：タイトルの「車がなくても、大きな子も動物病院へ」（Nori 11/12）に答えるよくある質問。数は display_companies.json から毎回数える
def big_faq(short, pf, k):
    from prefs import FARES_CHECKED
    n, b = _ncos(k), _nbig(k)
    if not n: return None
    q = f"{short}で、車がなくても大型犬を動物病院へ連れて行けますか？"
    if b:
        return (q, f"{pf}のお迎えに対応している{n}社のうち、公式サイトに大型犬も乗せられると書いている会社は{b}社でした（{FARES_CHECKED}時点）。電車にはキャリーに入る小さな子しか乗れませんが、ペットタクシーなら車がなくても、大きな子と一緒に動物病院へ行けます。乗せられる頭数や一緒に乗れる人数は会社ごとに違うので、候補の会社の条件と公式サイトで確かめてください。")
    return (q, f"{pf}のお迎えに対応している{n}社の中に、公式サイトに大型犬を乗せられるとはっきり書いている会社はまだ見つかっていません（{FARES_CHECKED}時点）。書いていなくても乗せてもらえることがあるので、フォームにペットの種類と体重を入れてさがし、候補の会社の公式サイトで確かめてください。")
# [B] SEO 11/13：市のページ（Nori「今日初めて、全部」。「ペットタクシー 川崎」などで県のページが20〜30位のため、市の名前で検索された人に市のページを用意する）
# 市ごとに、よく行く区間（道のりは地図の車の道のりのおおよそ）と、そこへ行く人が多い理由を手で書く。会社の数は display_companies.json から毎回数える。
CITIES = [
  dict(slug="yokohama", path="/kanagawa/yokohama/", pref="神奈川県", key="神奈川", city="横浜市", stems=["横浜"], parent=("/kanagawa/", "神奈川"),
    wards="青葉区・港北区・戸塚区・磯子区など18区",
    why="横浜市は18区あり、青葉区や戸塚区から横浜駅のまわりや川崎市の専門の動物病院へ通うと、20km前後の移動になることもあります。坂の多い住宅地も多く、大きな子を抱えてバス停まで歩くのは大変です。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。羽田空港への送迎や、市内・県外へのお引っ越しの移動にも使われます。",
    routes=[("横浜駅 → 黄金町（中区の夜間・救急の動物病院のあたり）", 3), ("横浜駅 → 川崎市高津区（日本動物高度医療センターのあたり）", 22), ("横浜駅 → 羽田空港", 25)],
    guides=["veccs-yokohama-taxi", "dvms-yokohama-taxi", "jarmec-kawasaki-taxi", "wancott-taxi"]),
  dict(slug="kawasaki", path="/kanagawa/kawasaki/", pref="神奈川県", key="神奈川", city="川崎市", stems=["川崎"], parent=("/kanagawa/", "神奈川"),
    wards="川崎区・中原区・高津区・宮前区・麻生区など7区",
    why="川崎市は南北に長く、麻生区や宮前区から川崎駅のまわりへ出るだけでも20km近くになることがあります。高津区には、二次診療（かかりつけの病院から紹介されて行く専門の病院）の大きな動物病院があり、市の外から通う人もいます。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。羽田空港が近く、空港への送迎にも使われます。",
    routes=[("川崎駅 → 羽田空港", 10), ("武蔵小杉 → 高津区（日本動物高度医療センターのあたり）", 7), ("川崎駅 → 横浜駅", 15)],
    guides=["jarmec-kawasaki-taxi", "dvms-yokohama-taxi", "veccs-yokohama-taxi"]),
  dict(slug="saitama-shi", path="/saitama/saitama-shi/", pref="埼玉県", key="埼玉", city="さいたま市", stems=["さいたま"], parent=("/saitama/", "埼玉"),
    wards="大宮区・浦和区・見沼区・岩槻区など10区",
    why="さいたま市の中の通院のほか、所沢など県の西にある専門の動物病院や、東京都内の病院へ通うときに使われます。大宮から所沢までは25kmほどあり、電車を乗りかえると時間もかかります。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。羽田空港・成田空港への送迎や、お引っ越しの移動にも使われます。",
    routes=[("大宮駅 → 浦和駅", 10), ("大宮駅 → 所沢市（日本小動物医療センターのあたり）", 25), ("大宮駅 → 羽田空港", 50)],
    guides=["jsamc-tokorozawa-taxi", "jarmec-tokyo-taxi"]),
  dict(slug="chiba-shi", path="/chiba/chiba-shi/", pref="千葉県", key="千葉", city="千葉市", stems=["千葉市"], parent=("/chiba/", "千葉"),
    wards="中央区・花見川区・稲毛区・若葉区・緑区・美浜区の6区",
    why="千葉市の中の通院のほか、船橋や東京都内の専門の動物病院へ通うときに使われます。若葉区や緑区は駅から離れた住宅地も多く、車がないと通院が大変です。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。成田空港・羽田空港への送迎や、お引っ越しの移動にも使われます。",
    routes=[("千葉駅 → 船橋駅", 20), ("千葉駅 → 成田空港", 40), ("千葉駅 → 羽田空港", 45)],
    guides=["airport-moving", "jarmec-tokyo-taxi"]),
  dict(slug="funabashi", path="/chiba/funabashi/", pref="千葉県", key="千葉", city="船橋市", stems=["船橋"], parent=("/chiba/", "千葉"),
    wards="船橋駅・西船橋・北習志野・津田沼のまわりなど",
    why="船橋市の中の通院のほか、市川・松戸・千葉市や東京都内の専門の動物病院へ通うときに使われます。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。東京の東側への移動が多く、成田空港・羽田空港への送迎や、お引っ越しの移動にも使われます。",
    routes=[("船橋駅 → 千葉駅", 20), ("船橋駅 → 足立区（日本動物高度医療センター東京病院のあたり）", 22), ("船橋駅 → 成田空港", 40)],
    guides=["jarmec-tokyo-taxi", "airport-moving"]),
  dict(slug="sapporo", path="/area/hokkaido/sapporo/", pref="北海道", key="北海道", city="札幌市", stems=["札幌"], parent=("/area/hokkaido/", "北海道"),
    wards="中央区・北区・東区・白石区・手稲区など10区",
    why="札幌市は10区あり、手稲区や清田区から中央区・北区の専門の動物病院へ通うと、10km以上の移動になることもあります。冬は雪道で、ペットを連れて歩いたりバスや地下鉄を待ったりするのが大変な日もあります。地下鉄や電車にはキャリーに入る子しか乗れず、大型犬は乗れません。新千歳空港への送迎や、お引っ越しの移動にも使われます。",
    routes=[("札幌駅 → 手稲区", 12), ("札幌駅 → 江別市", 20), ("札幌駅 → 新千歳空港", 50)],
    guides=["airport-moving", "large-dog"]),
  dict(slug="fukuoka-shi", path="/area/fukuoka/fukuoka-shi/", pref="福岡県", key="福岡", city="福岡市", stems=["福岡市"], parent=("/area/fukuoka/", "福岡"),
    wards="博多区・中央区・東区・早良区・西区など7区",
    why="福岡市の中の通院のほか、西区や早良区から博多・天神のまわりの専門の動物病院へ通うときに使われます。地下鉄や電車にはキャリーに入る子しか乗れず、大型犬は乗れません。福岡空港は博多駅から近く、空港への送迎や、お引っ越しの移動にも使われます。",
    routes=[("博多駅 → 福岡空港", 5), ("天神 → 糸島市", 25), ("博多駅 → 宗像市", 35)],
    guides=["airport-moving", "large-dog"]),
]
def city_links(pf):
    cs = [c for c in CITIES if c["pref"] == pf]
    if not cs: return ""
    return (f'<h3>{e(pf)}の市ごとのペットタクシー</h3><ul>' + "".join(f'<li><a href="{c["path"]}">{e(c["city"])}のペットタクシー（よく行く区間の料金の目安）</a></li>' for c in cs) + '</ul>')
def _nsame(k): return len([x for x in _DISP if k in x.get("areas", []) and x.get("lead_days") == 0])
def _nhosp(pf): return len(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "emergency.json"), encoding="utf-8"))["hospitals"].get(pf, []))
_DCJ = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "display_companies.json"), encoding="utf-8"))
_PPTS = _DCJ.get("partner_points", {})
_PLIM = _DCJ.get("partner_limits", {})
booking_src = re.sub(r"/\*PARTNER_POINTS\*/.*?/\*/PARTNER_POINTS\*/", lambda m: "/*PARTNER_POINTS*/var PARTNER_POINTS = " + json.dumps(_PPTS, ensure_ascii=False) + ";/*/PARTNER_POINTS*/", booking_src, count=1, flags=re.S)
booking_src = re.sub(r"/\*PARTNER_LIMITS\*/.*?/\*/PARTNER_LIMITS\*/", lambda m: "/*PARTNER_LIMITS*/var PARTNER_LIMITS = " + json.dumps(_PLIM, ensure_ascii=False) + ";/*/PARTNER_LIMITS*/", booking_src, count=1, flags=re.S)
# 提携規約の版（改定日＋本文の指紋）。同意のページ（booking/Code.gs の agreePage_）が、どの版に同意したかを記録する
import hashlib as _hl
from partner_terms import PTERMS as _PT, PTERMS_REVISED as _PTR
PTERMS_HASH = _hl.sha256(json.dumps(_PT, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
booking_src = re.sub(r"/\*PTERMS_VER\*/.*?/\*/PTERMS_VER\*/", lambda m: "/*PTERMS_VER*/var PTERMS_VER = " + json.dumps({"revised": _PTR, "hash": PTERMS_HASH}, ensure_ascii=False) + ";/*/PTERMS_VER*/", booking_src, count=1, flags=re.S)
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
def _r100(n): return int((n + 50) // 100 * 100)  # お客さまに見せる概算は100円単位（AGENTS.md「料金は目安」）
def _nat_row(km):
    v = sorted(_r100(_nat_ride(c["fare"], km)) for c in _NAT)
    mid = v[(len(v) - 1) // 2]
    return f'<div class="row"><dt>{km}km</dt><dd>{mid:,}円<br><small style="font-weight:400">{v[0]:,}〜{v[-1]:,}円</small></dd></div>'
def nat_text(km):
    v = sorted(_r100(_nat_ride(c["fare"], km)) for c in _NAT)
    return f"{v[(len(v) - 1) // 2]:,}円（{v[0]:,}〜{v[-1]:,}円）"
NAT_NOTES = f"""    <p class="fare-flag"><b>確定料金ではありません。</b>上の金額は目安です。確定料金（税込）は、問い合わせた会社から、空き状況と一緒にメールでお知らせします。</p>
    <p class="fare-night"><b>🌙 夜間・早朝の割増</b>上の目安は昼間の料金です。夜間・早朝の割増は、かかるかどうかも金額も会社ごとに違います。フォームの候補には、会社ごとの割増を入れた目安が出ます。</p>
    <p class="small">全国{_NAT_PREFS}都道府県・{len(_NAT)}社のペットタクシーが公式サイトにのせている料金表で、乗った距離の運賃（片道）を計算しました。大きい数字はまんなかの会社の金額で、その下は安い会社〜高い会社です。お迎え料金・待ち時間・夜間の割増・高速代・駐車場代は入っていません。フォームにお迎えの場所と行き先を入れると、来てもらえる会社ごとに、お迎え料金なども入れた目安が出ます。運賃は当日、ペットタクシーへ直接お支払いください（当サイトへのお支払いはありません）。都道府県ごとの料金の例は、<a href="/area/">全国のペットタクシー情報</a>に、距離ごと・都道府県ごとの運賃とお迎え料金・夜間割増のつけ方の数は<a href="/guide/pet-taxi-fare-survey/">全国のペットタクシー料金しらべ</a>にまとめています。</p>"""
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
TAXIS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "regular_taxis.json"), encoding="utf-8"))  # ふつうのタクシー（ご案内だけ）
TAXIS = {"checked": TAXIS["checked"], "taxis": [{k: t[k] for k in ("id", "name", "pref", "cities", "area_label", "rule", "fare", "url")} for t in TAXIS["taxis"]]}
src = re.sub(r"/\*TAXIS\*/.*?/\*/TAXIS\*/", lambda m: "/*TAXIS*/var TAXIS = " + json.dumps(TAXIS, ensure_ascii=False) + ";/*/TAXIS*/", src, count=1, flags=re.S)
# 問い合わせできる会社（booking/Code.gs の OPEN_PARTNERS）の対応する都道府県。フォームで県を選んだ時点で「まだ問い合わせできる会社がない」を知らせる（2026-11-08）
def _open_prefs():
    gs = open(os.path.join(ROOT, "booking", "Code.gs"), encoding="utf-8").read()
    m = re.search(r"OPEN_PARTNERS:\s*\{([^}]*)\}", gs)
    ids = re.findall(r"'[^']*'\s*:\s*'([^']+)'", m.group(1)) if m else []
    return sorted({a for x in _DISP if x.get("id") in ids for a in x.get("areas", [])})
# [B] SEO 11/10 Nori「今提携が完了してるエリアを重点的に改善して」：問い合わせを受け付けている会社（OPEN_PARTNERS）のお店がある都道府県では、
# エリアページの題名・説明文・リード文に「この会社に問い合わせできる」を出す。お店のあたりの名前は公式サイトの対応エリアの書き方から。
_OPEN_LABEL = {"D13b7c6f": ("北海道", "札幌"), "D225080e": ("広島県", "広島"), "De308905": ("東京都", "練馬区・杉並区"), "D0ec95b6": ("福岡県", "福岡市東区")}
def _open_local():
    gs = open(os.path.join(ROOT, "booking", "Code.gs"), encoding="utf-8").read()
    m = re.search(r"OPEN_PARTNERS:\s*\{([^}]*)\}", gs)
    out = {}
    for i in (re.findall(r"'[^']*'\s*:\s*'([^']+)'", m.group(1)) if m else []):
        if i in _OPEN_LABEL:
            pf, lab = _OPEN_LABEL[i]
            out.setdefault(pf, []).append((next(x["name"] for x in _DISP if x["id"] == i), lab))
    return out
OPEN_LOCAL = _open_local()
def open_lead(pf):
    cs = OPEN_LOCAL.get(pf)
    if not cs: return ""
    return f"{pf}では、" + "・".join(f"{n}（{l}）" for n, l in cs) + "に、このページのフォームから空き状況と料金を無料で問い合わせできます。"
src = re.sub(r"/\*OPEN_PREFS\*/.*?/\*/OPEN_PREFS\*/", lambda m: "/*OPEN_PREFS*/var OPEN_PREFS = " + json.dumps(_open_prefs(), ensure_ascii=False) + ";/*/OPEN_PREFS*/", src, count=1, flags=re.S)
def _co_site():
    out = {x["id"]: [x["name"], x["url"]] for x in _DISP if x.get("url")}
    # 提携先シートの準備中の会社（P002 など）は、tools/fares.json の名前と出典（公式サイト）から
    for v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fares.json"), encoding="utf-8"))["companies"].values():
        if not isinstance(v, dict) or not v.get("partner_id"): continue
        u = re.match(r"(https?://[^/\s]+/)", v.get("出典", ""))
        if u: out[v["partner_id"]] = [re.sub(r"（[^）]*）$", "", v["名前"]), u.group(1)]
    return out
# まだ提携していない会社の社名と公式サイト（候補カードで名前を伏せた会社に出す。Nori 2026-11-08「すすめていいよ」）
# 当日の精算の注意を出さない会社（Nori 2026-11-09「当てはまらない会社は対象外」）：待機料金なし（wait.yen が0）と、渋滞でも追加料金なし
def _no_fee():
    gs = open(os.path.join(ROOT, "booking", "Code.gs"), encoding="utf-8").read()
    m = re.search(r"OPEN_PARTNERS:\s*\{([^}]*)\}", gs)
    alias = {}
    for p, d in (re.findall(r"'([^']+)'\s*:\s*'([^']+)'", m.group(1)) if m else []): alias.setdefault(d, []).append(p)
    def ids(x): return [x["id"]] + alias.get(x["id"], [])
    nowait = sorted(i for x in _DISP if ((x.get("fare") or {}).get("wait") or {}).get("yen") == 0 for i in ids(x))
    nojam = sorted(i for x in _DISP if "渋滞でも追加料金なし" in (x.get("points") or []) for i in ids(x))
    return {"nowait": nowait, "nojam": nojam}
src = re.sub(r"/\*NO_FEE\*/.*?/\*/NO_FEE\*/", lambda m: "/*NO_FEE*/var NO_FEE = " + json.dumps(_no_fee(), ensure_ascii=False) + ";/*/NO_FEE*/", src, count=1, flags=re.S)
src = re.sub(r"/\*CO_SITE\*/.*?/\*/CO_SITE\*/", lambda m: "/*CO_SITE*/var CO_SITE = " + json.dumps(_co_site(), ensure_ascii=False) + ";/*/CO_SITE*/", src, count=1, flags=re.S)
# 会社が見つかっている都道府県（お迎えの都道府県の選択欄で、いない県に「（候補なし）」を付ける）
src = re.sub(r"/\*AREA_PREFS\*/.*?/\*/AREA_PREFS\*/", lambda m: "/*AREA_PREFS*/var AREA_PREFS = " + json.dumps(sorted({a for x in _DISP for a in x.get("areas", [])} | {"東京", "神奈川", "埼玉", "千葉"}), ensure_ascii=False) + ";/*/AREA_PREFS*/", src, count=1, flags=re.S)
src = re.sub(r"/\*FARES\*/.*?/\*/FARES\*/", lambda m: "/*FARES*/" + FARE_JS + "/*/FARES*/", src, count=1, flags=re.S)
# [B] 2026-11-08 トップに「都道府県ごとのペットタクシーの数」（全国の会社を公式サイトで確かめた数。トップだけに出し、地域ページの写しでは外す）
def _nat_stats():
    from prefs import PREFS as _P
    full = {"東京": ("東京都", "/tokyo/"), "神奈川": ("神奈川県", "/kanagawa/"), "埼玉": ("埼玉県", "/saitama/"), "千葉": ("千葉県", "/chiba/")}
    for slug, name, *_ in _P: full.setdefault(name if name == "北海道" else name[:-1], (name, f"/area/{slug}/"))
    keys = sorted({a for x in _DISP for a in x.get("areas", [])}, key=lambda k: (-_ncos(k), full.get(k, ("", "~"))[1]))
    rows = ""
    for k in keys:
        n = _ncos(k)
        if n < 3 or k not in full: continue
        fs = sorted(_r100(_nat_ride(c["fare"], 5)) for c in _NAT if k in c.get("areas", []))
        mid = f"{fs[(len(fs) - 1) // 2]:,}円" if fs else "—"
        nm, u = full[k]
        rows += f'<tr><td><a href="{u}">{nm}</a></td><td>{n}社</td><td>{_n24(k)}社</td><td>{_nsame(k)}社</td><td>{mid}</td></tr>'
    npref = len({a for x in _DISP for a in x.get("areas", [])})
    return (f'<!--NAT_STATS--><div class="tbl" style="margin-top:18px"><h3 style="font-size:1.05rem;margin:0 0 8px">都道府県ごとのペットタクシーの数（全国{len(_DISP)}社・{npref}都道府県）</h3>'
            '<table><thead><tr><th>お迎えの都道府県</th><th>来てくれる会社</th><th>24時間受付</th><th>当日も受ける</th><th>5kmの運賃の目安</th></tr></thead><tbody>' + rows +
            '</tbody></table><p class="small">当サイトが公式サイトで確かめた会社の数です（2026年11月時点、3社以上の都道府県）。「当日も受ける」は公式サイトや会社の返事にはっきり書いてある会社だけ。運賃の目安は、各社の公式サイトの料金表をもとに計算した概算のまんなかの会社の金額で、お迎え料金・夜間の割増・待ち時間は入っていません。確定料金ではありません。<a href="/guide/pet-taxi-fare-survey/">全国のペットタクシー料金しらべ（距離ごと・都道府県ごと・お迎え料金・夜間割増）</a></p></div><!--/NAT_STATS-->')
src = re.sub(r"\s*<!--NAT_STATS-->.*?<!--/NAT_STATS-->", "", src, flags=re.S)
src = src.replace('<a href="/area/">全国47都道府県のペットタクシー情報を見る</a></p>', '<a href="/area/">全国47都道府県のペットタクシー情報を見る</a></p>\n    ' + _nat_stats(), 1)
# 数字の帯：会社が見つかった都道府県の数だけを出す（「47都道府県から選べます」は会社のいない県もあるので誤解のもと。法定表示の確認 2026-11-08）
_npref = len({a for x in _DISP for a in x.get("areas", [])})
src = re.sub(r'<div class="stat"><div class="n">[0-9]+<small>都道府県</small></div><div class="l">[^<]*(?:<br>[^<]*)?</div></div>',
             f'<div class="stat"><div class="n">{_npref}<small>都道府県</small></div><div class="l">{len(_DISP)}社から<br>さがせます</div></div>', src, count=1)
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(src)
TOP_HTML = src  # 地域ページの元（下の clone_top）。src はあとで別の用途に使われるので写しておく
# 地域ページは全部トップの写しで、ページの下の大きなプログラム（フォーム・料金の計算・緊急タブのデータ）も同じ。
# 地域ページではそれを /app.js に分けて読み込む（2ページ目からはブラウザに残った写しを使うので速く開ける）
import hashlib
from urllib.parse import quote
_APP_M = max(re.finditer(r"<script>(.*?)</script>", TOP_HTML, re.S), key=lambda m: len(m.group(1)))
APP_JS = _APP_M.group(1)
open(os.path.join(ROOT, "app.js"), "w", encoding="utf-8").write(APP_JS)
APP_TAG = '<script src="/app.js?v=' + hashlib.sha1(APP_JS.encode("utf-8")).hexdigest()[:10] + '"></script>'
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
/* ドッグラン（tools/gen_dogrun.py） */
.dr-stats{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:14px 0 0}
.dr-stats li{background:#fff;border-radius:14px;padding:8px 14px;font-size:.86rem;color:var(--ink-2);box-shadow:0 2px 8px rgba(28,26,24,.06)}
.dr-stats b{font-size:1.15rem;color:var(--o-d);margin-right:2px}
.dr-prefs{display:grid;grid-template-columns:repeat(auto-fill,minmax(132px,1fr));gap:8px;list-style:none;padding:0;margin:8px 0 0}
.dr-prefs a,.dr-prefs span{display:flex;justify-content:space-between;align-items:center;border:1px solid var(--line);border-radius:12px;padding:9px 12px;font-size:.9rem;font-weight:700;color:var(--ink);text-decoration:none;background:#fff}
.dr-prefs a:hover{border-color:var(--o);color:var(--o-d)}
.dr-prefs small{font-weight:400;color:var(--ink-3);font-size:.78rem}
.dr-prefs span{color:var(--ink-3);font-weight:400}
.dr-region{font-size:1rem;margin:20px 0 0}
.dr-tags,.art .dr-tags{display:flex;flex-wrap:wrap;gap:5px;list-style:none;padding:0;margin:6px 0 0}
.dr-tags li{font-size:.74rem;font-weight:700;border-radius:999px;padding:2px 10px;background:#f7f4f1;color:var(--ink-2)}
.dr-tags li.ok{background:var(--o-l);color:var(--o-d)}
.dr-card{background:#fff;border:1.5px solid var(--line);border-radius:20px;padding:18px 18px 8px;margin:0 0 18px;scroll-margin-top:90px}
.art .dr-card h2{margin:0 0 4px;font-size:1.2rem;border-left:0;padding-left:0}
.art .dr-card h3{margin:0 0 4px;font-size:1.15rem}
.dr-tbl td small{color:var(--ink-3)}
.art .emg-pref h3 small{font-weight:400;font-size:.8rem;color:var(--ink-3)}
.dr-card .dr-city{font-size:.84rem;color:var(--ink-3);margin:0}
.dr-card dl{margin:12px 0 0;display:grid;grid-template-columns:1fr;gap:0}
.dr-card dt{font-size:.78rem;font-weight:800;color:var(--ink-3);margin-top:10px}
.dr-card dd{margin:2px 0 0;font-size:.9rem;line-height:1.7;color:var(--ink)}
@media (min-width:600px){.dr-card dl{grid-template-columns:9em 1fr}.dr-card dt{margin:0;padding:8px 0;border-top:1px solid var(--line)}.dr-card dd{margin:0;padding:8px 0;border-top:1px solid var(--line)}}
.dr-card .dr-links{font-size:.84rem;margin:12px 0 8px}
.dr-card .dr-links small{display:block;color:var(--ink-3);font-size:.76rem;margin-top:4px;word-break:break-all}
.dr-card .dr-links small a{color:var(--ink-3)}
.art .dr-tbl td,.art .dr-tbl th{text-align:left;padding:8px 6px}
.art .dr-tbl td:last-child,.art .dr-tbl th:last-child{background:transparent;font-weight:400}
.art .dr-tbl th:last-child{background:#f7f4f1;font-weight:700}
.art .dr-tbl td:nth-child(n+3),.art .dr-tbl th:nth-child(n+3){white-space:nowrap}
.art .dr-cmp td:nth-child(n),.art .dr-cmp th:nth-child(n){white-space:normal}
.art .dr-cmp tbody th{background:#f7f4f1;white-space:nowrap}
.dr-row{border-top:1px solid var(--line);padding:10px 2px}
.dr-row a{font-weight:700}
.dr-row small{color:var(--ink-3);margin-left:6px}
.taxi-cta{margin:4px 0 18px}
.taxi-cta .btn,.taxi-top .btn{font-size:.95rem;padding:13px 20px;max-width:100%;white-space:normal;text-align:center}
.taxi-cta small,.taxi-top small{display:block;color:var(--ink-3);font-size:.78rem;line-height:1.6;margin-top:6px}
.taxi-top-sec{padding:0 0 8px}
.taxi-top{background:var(--o-l);border-radius:18px;padding:14px 16px}
.taxi-top p{margin:0 0 10px;font-size:.88rem;line-height:1.7;color:var(--ink)}
.taxi-top p b{display:block;font-size:.98rem;color:var(--o-d)}
"""
open(os.path.join(ROOT, "style.css"), "w", encoding="utf-8").write(css.strip() + "\n" + extra_css.strip() + "\n")

# ── 地域ページ＝トップと同じページ（Nori 2026-10-31「ペットタクシー 神奈川 で検索されたページもトップと同じに」）──
# トップの index.html をそのまま写し、title・説明文・canonical・h1・リード文・構造化データだけ地域ごとに変え、
# フォームのお迎えの都道府県を最初から選んだ状態にする。地域の説明（料金の目安・主な市区・よくある質問など）は
# フォームのすぐ後ろに差し込む。トップの中身を直せば、地域ページも gen_areas.py の実行でそろう。
# [B] SEO 11/12：題名・説明文は、多くの飼い主さんに共通する悩みと「あきらめずに済むこと」を先に（Nori「ペインポイントとなんの断念を解決するものなのかをマスに共通するもので」）。
# ほかの悩み（タクシーに断られる・介護の子など）は各記事の題名で受ける。
PAIN_T = "車がなくても、大きな子も動物病院へ"
def pain_desc(where):
    return f"車がない、大型犬で電車に乗れない、抱っこして通うのがつらい。そんなときも通院をあきらめなくて大丈夫です。{where}で犬・猫を乗せてくれるペットタクシーの料金の目安を、お迎えの場所を入れて無料でしらべられます。"
def clone_top(title, desc, url, ld_html, kicker, lede, pref, area_html, crumb):
    t = re.sub(r"\s*<!--NAT_STATS-->.*?<!--/NAT_STATS-->", "", TOP_HTML, flags=re.S)
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
    # トップ（全国の入口）へ、「ペットタクシー」全体のことばでリンクする（トップとエリアページの役割を分ける）
    to_top = '<div class="wrap"><p class="to-top">ほかの都道府県の会社もふくめてさがすときは、<a href="/">全国のペットタクシーの料金をくらべる</a>ページへ。</p></div>'
    t = t.replace('<section id="how">', area_html + '\n' + to_top + '\n<section id="how">', 1)
    # エリアページ用のCSS（.crumb .prose など）を足す
    t = t.replace("</style>", extra_css.strip() + "\n</style>", 1)
    # いちばん上の写真だけ、そのページの写真があれば置きかえる（tools/page_images.py）
    k = area_key(url.replace(SITE, ""))
    if k and os.path.exists(os.path.join(ROOT, "img", "area", k + ".jpg")):
        t = t.replace('href="/img/hero.webp"', f'href="/img/area/{k}.webp"', 1)
        t = t.replace(f'content="{SITE}/img/hero.jpg"', f'content="{SITE}/img/area/{k}.jpg"', 1)
        t = re.sub(r'<meta property="og:image:alt" content="[^"]*">', lambda m: f'<meta property="og:image:alt" content="{e(AREA_ALT.get(k, ""))}">', t, count=1)
        t = re.sub(r'<source srcset="/img/hero\.webp" type="image/webp"><img src="/img/hero\.jpg" alt="[^"]*"',
                   lambda m: f'<source srcset="/img/area/{k}.webp" type="image/webp"><img src="/img/area/{k}.jpg" alt="{e(AREA_ALT.get(k, ""))}"', t, count=1)
    t = t.replace(_APP_M.group(0), APP_TAG, 1)
    assert t.count(f"<option selected>{pref}</option>") == 2, pref
    assert f"<title>{e(title)}</title>" in t, title
    return t

AREAS = [
 dict(slug="tokyo", places=["jarmec-tokyo-taxi","trva-yakan-taxi","jamc-shibuya-taxi"], pref="東京都", short="東京", count=17,
  # [B] SEO 11/10：「ペットタクシー」で40位。提携先（練馬杉並店）に問い合わせできることを題名に（OPEN_LOCAL から。いなくなれば前の形）
  title=(f"東京のペットタクシー｜{PAIN_T}。{'・'.join(l.replace('区・', '・') for _, l in OPEN_LOCAL['東京都'])}の会社に空き状況と料金を無料で問い合わせ" if OPEN_LOCAL.get("東京都") else
         f"東京のペットタクシー｜{PAIN_T}。料金の目安を無料でしらべる（23区・多摩）") + "｜ペットタクシー予約窓口",
  desc=pain_desc("東京都（23区・多摩）"),
  lede="23区の動物病院への通院から、お引っ越し、羽田空港への送迎まで。フォームに入れると、来てもらえる会社と料金の目安が出て、何社にでもまとめて空き状況と料金を問い合わせできます。",
  body=[
   ("東京でペットタクシーを使う理由", "東京23区は動物病院の数が多い一方、電車やバスにペットを乗せるにはキャリーに入れる決まりがあり、大型犬はそもそも乗れません。一般のタクシーも、ペット連れだと断られることがあります。ペット専用のタクシーなら、ケージや介護用のマットを積んだ車で、犬も猫もそのまま乗れます。"),
   ("多摩地域（八王子・町田・府中・調布・立川・三鷹）から", f"多摩地域は23区より動物病院どうしの距離が長く、専門の病院や23区の二次診療の病院まで10〜20km以上になることもあります。東京都のお迎えに対応している{_ncos('東京')}社のうち、公式サイトの対応エリアに「多摩」と書いている会社は{_ccos('東京','多摩')}社、「三鷹」は{_ccos('東京','三鷹')}社、「武蔵野」は{_ccos('東京','武蔵野')}社、「調布」は{_ccos('東京','調布')}社でした（「23区」と書いている会社は{_ccos('東京','23区')}社）。10kmで{nat_text(10)}、20kmで{nat_text(20)}が片道の目安です（各社の公式サイトの料金表をもとに計算した概算で、確定料金ではありません）。"),
   ("犬のタクシー・猫のタクシー、東京で多い使い方", "世田谷区や目黒区から専門の動物病院への通院、お引っ越しのときの長距離移動、羽田空港からの国内線での帰省などが多い使い方です。飼い主さんが仕事で付き添えない日に、ペットだけを病院やペットホテルへ送ることもできます。"),
  ],
  cities=["世田谷区","墨田区","渋谷区","新宿区","港区","目黒区","品川区","大田区","杉並区","練馬区","江東区","江戸川区","足立区","板橋区","中野区","八王子市","町田市","府中市","調布市","立川市"],
  route=("世田谷区 → 羽田空港", 18),
  faq=[
   ("東京23区内の動物病院まで、ペットタクシーはいくらですか？", f"距離で決まることが多く、全国の会社の料金表で計算すると、5kmで{nat_text(5)}、10kmで{nat_text(10)}が片道の目安です（まんなかの会社の金額と、安い会社〜高い会社）。会社からの返事で、一般道の場合と高速道路を使う場合の確定料金（税込）をメールでお知らせします。"),
   ("八王子・町田など多摩地域からも頼めますか？", "はい。多摩地域の市町村もお迎えの場所に入れられます。会社ごとに来てくれる地域が違い、23区だけの会社や、市の名前まで書いていない会社もあるので、お迎えの場所をフォームに入れて、来てもらえる会社と料金の目安を確かめてください。お店から遠いとお迎えの料金が増えることがあります。"),
   ("羽田空港への送迎はできますか？", f"はい。世田谷区から羽田空港（約18km）なら{nat_text(18)}が片道の目安です。飛行機に乗せる場合は、航空会社のペット預かりの受付時間に間に合うよう、メモ欄にフライトの時刻を書いてください。"),
   ("東京で夜間や早朝のお迎えも頼めますか？", "フォームは24時間送れますが、会社への確認はメールで行うため、連絡はすべてメールです。夜間・早朝は引き受けられる会社が見つからないこともあるため、早めのご予約をおすすめします。" + night_text("東京都") + "急な体調不良で一刻を争うときは、まず動物病院に電話してください。"),
  ]),
 dict(slug="kanagawa", places=["jarmec-kawasaki-taxi","dvms-yokohama-taxi","wancott-taxi"], pref="神奈川県", short="神奈川・横浜", h1="神奈川・横浜・川崎", count=5,
  # [B] SEO 11/9：84表示・0クリック（16.7位。ペットタクシー・タクシー 犬連れ・ペットタクシー 川崎）。数と料金の答えを先に出す。
  # [B] SEO 11/10：「ペットタクシー 川崎」11表示・20位、「ペットタクシー 神奈川」28位。題名の先に横浜・川崎を出す
  title=f"神奈川・横浜・川崎のペットタクシー｜{PAIN_T}。料金の目安を無料でしらべる",
  desc=pain_desc("神奈川県（横浜・川崎・相模原など）"),
  lede="横浜・川崎から湘南エリアまで。動物病院への通院や、都内の専門病院への移動、羽田空港への送迎に。お迎えの場所を入れると、来てもらえる会社と料金の目安が出ます。",
  body=[
   ("神奈川・横浜・川崎でペットタクシーを使う理由", "横浜市や川崎市は坂道や丘の上の住宅地が多く、大型犬やシニアの子を連れて歩いたり、公共交通で移動したりするのは大変です。ペットタクシーなら玄関先まで迎えに来てくれるので、抱っこやキャリーで長く歩かせる必要がありません。"),
   ("横浜市内（18区）の通院・移動", f"横浜市は鶴見区・神奈川区・西区・中区・南区・港南区・保土ケ谷区・旭区・磯子区・金沢区・港北区・緑区・青葉区・都筑区・戸塚区・栄区・泉区・瀬谷区の18区があり、区をまたいでかかりつけや専門の動物病院へ通う方も多い地域です。神奈川県のお迎えに対応している{_ncos('神奈川')}社のうち、公式サイトの対応エリアに「横浜」と書いている会社は{_ccos('神奈川','横浜')}社でした。区の中や隣の区への5kmの移動で{nat_text(5)}、区をまたぐ10kmで{nat_text(10)}が片道の目安です（各社の公式サイトの料金表をもとに計算した概算で、確定料金ではありません）。"),
   ("川崎市（7区）の通院・移動", f"川崎市は川崎区・幸区・中原区・高津区・宮前区・多摩区・麻生区の7区です。神奈川県のお迎えに対応している{_ncos('神奈川')}社のうち、公式サイトの対応エリアに「川崎」と書いている会社は{_ccos('神奈川','川崎')}社、そのうち24時間受け付けている会社は{len([x for x in _DISP if '神奈川' in x.get('areas', []) and '川崎' in (x.get('area_text') or '') and x.get('hours') == '0-24'])}社でした。高津区久地には日本動物高度医療センター川崎本院があり、夜間・救急の病院は中原区（24時間）と高津区（川崎市獣医師会の夜間の病院、診療日が限られます）にあります。区の中や隣の区への5kmの移動で{nat_text(5)}、市の南北をまたぐ15kmで{nat_text(15)}が片道の目安です（各社の公式サイトの料金表をもとに計算した概算で、確定料金ではありません）。"),
   ("川崎・横浜から都内への移動も", "神奈川から東京の専門病院や二次診療の動物病院へ通う方も多くいます。お迎えに来られる会社と料金の目安がフォームに出るので、気になる会社を選んで、空き状況と料金を問い合わせできます。"),
  ],
  cities=["横浜市","川崎市","相模原市","藤沢市","横須賀市","鎌倉市","茅ヶ崎市","大和市","厚木市","平塚市","海老名市","小田原市"],
  route=("横浜駅周辺 → 羽田空港", 25),
  faq=[
   ("横浜・川崎に来てくれるペットタクシーは何社ありますか？", f"神奈川県のお迎えに対応している{_ncos('神奈川')}社のうち、公式サイトの対応エリアに「横浜」と書いている会社が{_ccos('神奈川','横浜')}社、「川崎」と書いている会社が{_ccos('神奈川','川崎')}社ありました。地名を書いていない会社が来てくれることもあるので、お迎えの場所をフォームに入れて確かめてください。"),
   ("神奈川で夜間に診てもらえる動物病院はありますか？", f"横浜・川崎・相模原・藤沢・横須賀などの夜間・救急の動物病院を{_nhosp('神奈川県')}件載せています。受付時間は病院ごとに違うので、行く前に電話で受け入れてもらえるか確かめてください。このページの「緊急」タブや、夜間・救急の動物病院の一覧からさがせます。"),
   ("横浜市の港北区・青葉区・戸塚区などからも頼めますか？", "はい。横浜市18区のどこからでもお迎えの場所に入れられます。会社ごとに来てくれる地域が違い、区の名前まで書いていない会社も多いので、お迎えの場所をフォームに入れて、来てもらえる会社と料金の目安を確かめてください。"),
   ("横浜から都内の動物病院まで頼めますか？", f"はい。県をまたぐ移動にも対応しています。横浜から都内までの20〜30kmなら、20kmで{nat_text(20)}、30kmで{nat_text(30)}が片道の目安です。"),
   ("川崎市からでもペットタクシーを予約できますか？", "はい。川崎市からのお迎えも選べます。場所・日時・ペットの大きさなどの条件に合う事業者と料金の目安を表示し、その中から何社でも選んで、空き状況と料金を問い合わせできます。会社から返事が届いたら、納得してから予約できます。"),
   ("湘南エリア（藤沢・茅ヶ崎・鎌倉）でも使えますか？", "はい、お迎えの場所に入れられます。会社ごとに対応する地域が違うため、場所によってはお迎え料金が増えたり、来てもらえる会社が見つからなかったりすることがあります。日にちに余裕をもってご依頼ください。"),
   ("大型犬をスロープ付きの車で運んでもらえますか？", "フォームに体重と犬種を入れていただくと、大型犬を受けている会社だけをご案内します。スロープの有無は会社や車によって違うので、必要なときはメモ欄に書いてください。"),
  ]),
 dict(slug="chiba", places=["doggys-island-taxi"], pref="千葉県", short="千葉", count=4,
  # [B] SEO 11/8：14表示・0クリック（7.8位）。数・24時間・当日・料金の答えを先に出す。
  title=f"千葉のペットタクシー｜{PAIN_T}。料金の目安を無料でしらべる（船橋・松戸・成田空港）",
  desc=pain_desc("千葉県（千葉・船橋・松戸など）"),
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
   ("千葉から都内の病院へ通えますか？", "はい。県をまたぐ移動にも対応しています。病院への往復なら「往復」を選んで、帰りの時刻（診察が終わるころ）を入れてください。待っていてもらうか、あらためて迎えに来てもらうかは、安いほうを会社が返事でご案内します。"),
  ]),
 dict(slug="saitama", places=["jsamc-tokorozawa-taxi"], pref="埼玉県", short="埼玉", count=3,
  # [B] SEO 11/8：16表示・0クリック（7.8位）。数・24時間・当日・料金の答えを先に出す。
  title=f"埼玉のペットタクシー｜{PAIN_T}。料金の目安を無料でしらべる（さいたま・川口・所沢）",
  desc=pain_desc("埼玉県（さいたま・川口・所沢など）"),
  lede="さいたま市・川口から川越・所沢まで。動物病院への通院や都内の専門病院への移動に。お迎えの場所を入れると、来てもらえる会社と料金の目安が出ます。",
  body=[
   ("埼玉でペットタクシーを使う理由", "埼玉県は都内へ通う方が多く、平日の昼間は家族が付き添えないことがよくあります。ペットタクシーなら、飼い主さんが乗れない日でも、ペットだけを病院やトリミング、ペットホテルへ送ってもらえます。"),
   ("川口・戸田・朝霞・和光・所沢など、都内に近い南部から", f"埼玉県のお迎えに対応している{_ncos('埼玉')}社のうち、公式サイトの対応エリアに「川口」と書いている会社は{_ccos('埼玉','川口')}社、「朝霞」は{_ccos('埼玉','朝霞')}社、「和光」は{_ccos('埼玉','和光')}社、「所沢」は{_ccos('埼玉','所沢')}社でした（市の名前まで書いていない会社もあります）。かかりつけへの5kmで{nat_text(5)}、都内の病院まで15kmで{nat_text(15)}が片道の目安です（各社の公式サイトの料金表をもとに計算した概算で、確定料金ではありません）。"),
   ("さいたま市から都内の専門病院へ", "大宮・浦和から都内の二次診療の動物病院へ通う方もいます。お迎えに来られる会社と料金の目安がフォームに出るので、気になる会社を選んで、空き状況と料金を問い合わせできます。"),
  ],
  cities=["さいたま市","川口市","越谷市","所沢市","川越市","草加市","春日部市","戸田市","上尾市","熊谷市"],
  route=("大宮駅周辺 → 新宿区", 30),
  faq=[
   ("さいたま市から都内まで頼めますか？", f"はい。大宮周辺から新宿までの約30kmなら、{nat_text(30)}が片道の目安です。"),
   ("飼い主が乗らずにペットだけ運んでもらえますか？", "フォームの「一緒に乗る人数」で「0人（ペットだけ）」を選んでください。ペットだけの送迎を受けるかは会社によるため、会社からの返事のメールでご確認ください。"),
   ("埼玉の北部（熊谷など）でも使えますか？", "はい、お迎えの場所に入れられます。会社ごとに対応する地域が違うため、場所によってはお迎え料金が増えたり、来てもらえる会社が見つからなかったりすることがあります。日にちに余裕をもってご依頼ください。"),
  ]),
]
# 4都県に共通で足すよくある質問（数は display_companies.json・emergency.json から毎回数える）
for _a in AREAS:
    _k = _a["pref"].rstrip("都県")
    _bf = big_faq(_a['short'].split('・')[0], _a["pref"], _k)
    if _bf: _a["faq"].append(_bf)
    _a["faq"].append((f"{_a['short'].split('・')[0]}で当日でもペットタクシーを頼めますか？",
        f"{_a['pref']}のお迎えに対応している{_ncos(_k)}社のうち、公式サイトや会社からの返事に当日も受けると書いてある会社は{_nsame(_k)}社です。お迎えが今日のときは、この中から空いていて間に合う会社だけが候補に出ます。会社にメールで確認してから決まるしくみなので、お迎えの時刻は、いまから3時間以上あとで選んでください。"))
    if _a["slug"] != "kanagawa":
        _a["faq"].append((f"{_a['short'].split('・')[0]}で夜間に診てもらえる動物病院はありますか？",
            f"{_a['pref']}の夜間・救急の動物病院を{_nhosp(_a['pref'])}件載せています。受付時間は病院ごとに違うので、行く前に電話で受け入れてもらえるか確かめてください。このページの「緊急」タブや、夜間・救急の動物病院の一覧からさがせます。"))

PAW = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="6" cy="9" r="2.2"/><circle cx="10" cy="5.5" r="2.2"/><circle cx="14" cy="5.5" r="2.2"/><circle cx="18" cy="9" r="2.2"/><path d="M12 11c-3 0-6 3.6-6 6.2 0 1.8 1.5 2.8 3 2.8 1.2 0 2-.6 3-.6s1.8.6 3 .6c1.5 0 3-1 3-2.8C18 14.6 15 11 12 11z"/></svg>'
ARROW = '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h12M11 5l5 5-5 5"/></svg>'
CHECK = '<span><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8.5l3 3 7-7"/></svg></span>'
e = html.escape

# [B] SEO 11/13 Nori「全部やって」：市のページ（CITIES）もここから全部のガイド・エリアページにつなぐ
# [B] SEO 11/10 Nori「提携が完了してるエリア」「大阪名古屋…飼い主が多いところも」：ガイド・エリアページからのリンクに、大きな県と提携先のある県を足す
KEY_PREF_LINKS = [("osaka", "大阪"), ("aichi", "愛知・名古屋"), ("fukuoka", "福岡"), ("hokkaido", "北海道・札幌"), ("hiroshima", "広島"), ("hyogo", "兵庫・神戸")]
def area_links(cur=None, more=False):
    return '<ul class="other">' + ''.join(
        f'<li><a href="/{a["slug"]}/">{e(a["short"])}のペットタクシー</a></li>' for a in AREAS if a["slug"] != cur) + ''.join(
        f'<li><a href="/area/{s_}/">{e(n_)}のペットタクシー</a></li>' for s_, n_ in (KEY_PREF_LINKS if more else [])) + ''.join(
        f'<li><a href="{c["path"]}">{e(c["city"])}のペットタクシー</a></li>' for c in (CITIES if more else []) if c["path"] != f"/{cur}/") + '<li><a href="/area/">ほかの道府県（全国）</a></li></ul>'

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
    <nav><a href="/#how">使い方</a><a href="/#area">エリア</a><a href="/#form">料金をくらべる</a><a href="/guide/">ガイド</a><a href="/#faq">よくある質問</a></nav>
    <a class="mini" href="/#form">問い合わせる<span class="lg">（無料）</span></a>
  </div>
</header>
'''

PARTNER_BAND = '''<aside class="partner-band"><div class="wrap"><p><b>ペットタクシー会社の方へ</b>いっしょにペットと飼い主さんをお迎えしてくださる会社を探しています。</p><a href="/partner/">提携のご案内</a></div></aside>
'''

def foot(cta_href, band=True):
    return (PARTNER_BAND if band else '') + f'''<footer>
  <div class="wrap">
    <nav><a href="/">トップ</a><a href="/#how">使い方</a><a href="/#price">料金の目安</a><a href="/guide/">ペットの移動ガイド</a><a href="/#faq">よくある質問</a><a href="/emergency/">緊急のときの連絡先</a><a href="/hospital/">条件でさがす動物病院</a><a href="/jichitai/">迷子・犬の登録の窓口</a><a href="/dogrun/">全国のドッグラン</a><a href="/rojin-home/">老犬ホーム・老猫ホーム</a><a href="/dog-trainer/">ドッグトレーナー・しつけ教室</a><a href="/pet-sitter/">ペットシッター</a><a href="/trimming/">出張トリミング</a><a href="/pet-hotel/">大型犬OK・猫専用のペットホテル</a><a href="/sougi/">ペットが亡くなったら</a><a href="/area/">全国のペットタクシー情報</a><a href="/#policy">キャンセルについて</a><a href="/#privacy">個人情報の取り扱い</a><a href="/terms/">利用規約</a><a href="/#operator">運営者情報</a><a href="/contact/">お問い合わせ</a><a href="/partner/">提携をご希望の会社さま</a></nav>
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

from prefs import FARES_CHECKED
def _night_txt(F):
    n = (F or {}).get("night")
    if not F: return "—"
    if not n: return "料金表にない"
    if n.get("unknown"): return f"{n['from']}時〜{n['to']}時（金額は書いていない）"
    if "flat" in n: return f"{n['from']}時〜{n['to']}時は{n['flat']:,}円"
    if "rate" in n: return f"{n['from']}時〜{n['to']}時は{round(n['rate']*10)}割増" if n['rate'] * 10 == round(n['rate'] * 10) else f"{n['from']}時〜{n['to']}時は{round(n['rate']*100)}%増"
    if "bands" in n:
        ys = [b[2] for b in n["bands"]]
        return f"時間帯で{min(ys):,}〜{max(ys):,}円"
    return "—"
def _pick_txt(F):
    q = (F or {}).get("pick")
    if not F: return "—"
    if not q: return "料金表にない"
    if q.get("per"):
        t = f"1kmごとに{q['per']:,}円"
        if q.get("freeWithin"): t = f"{q['freeWithin']}kmまで無料、そのあと" + t
        if q.get("km") and q.get("yen"): t = f"{q['km']}kmまで{q['yen']:,}円、そのあと" + t
        return t
    if q.get("yen") == 0: return "無料"
    if q.get("yen"): return f"{q['yen']:,}円" + ("（変わることあり）" if q.get("unsure") else "")
    return "—"
def pref_company_table(pf, short, cs, cities=()):
    key = pf if pf == "北海道" else pf[:-1]
    if not cs: return ""
    pts = {}
    for c in cs:
        for t in c.get("points", []): pts[t] = pts.get(t, 0) + 1
    want = [("24時間受付", "24時間受け付けている"), ("当日予約可", "当日の予約も受ける"), ("カード払い可", "カードで払える"), ("大型犬OK", "大型犬に対応している"), ("前日までキャンセル無料", "前日までキャンセル無料の")]
    summ = "・".join(f"{lab}会社が{pts[k]}社" for k, lab in want if pts.get(k))
    rows = []
    for c in cs:
        F = c.get("fare") if c.get("fare") and c["fare"].get("kind", "dist") == "dist" and c["fare"].get("base") else None
        h = c.get("hours") or ""
        ht = "24時間" if h == "0-24" else (h.replace("-", "時〜") + "時" if h else "—")
        r5 = f"{_nat_ride(F, 5):,}円" if F else "お見積もり"
        home = "都内" if c["pref"] == pf and pf.endswith("都") else "府内" if c["pref"] == pf and pf.endswith("府") else ("道内" if c["pref"] == pf and pf == "北海道" else ("県内" if c["pref"] == pf else c["pref"]))
        rows.append((0 if c["pref"] == pf else 1, _nat_ride(F, 5) if F else 10**9, f'<tr><td>{e(home)}</td><td>{e(c.get("area_text") or "")}</td><td>{e(ht)}</td><td>{e(r5)}</td><td>{e(_pick_txt(F))}</td><td>{e(_night_txt(F))}</td></tr>'))
    rows.sort(key=lambda r: (r[0], r[1]))
    out = f'<h2>{e(short)}に来てくれるペットタクシー{len(cs)}社の、対応エリアと料金のしくみ</h2>'
    out += f'<p>{e(pf)}のお迎えに対応している{len(cs)}社について、公式サイトに書かれている対応エリア・受付時間・料金のしくみを1社ずつ並べました。お住まいの市や区が書かれている会社があるか、夜の割増がどう決まっているかを、問い合わせる前の参考にしてください。</p>'
    if summ:
        out += f'<p>公式サイトに書いている内容を数えると、{e(summ)}でした（書いていない会社が、できないとは限りません）。</p>'
    cm = []
    for c in cities:
        stem = re.sub(r"(市|区|町|村)$", "", c)
        if stem == "港" or stem == key: stem = c  # 「港」は空港、「大阪」は大阪府にも当たるので、市・区まで入れて数える
        n = sum(1 for x in cs if stem in (x.get("area_text") or ""))
        if n: cm.append((n, stem))
    if cm:
        whole = sum(1 for x in cs if re.search(key + r"(全域|全県|県内全域|府内全域|都内全域|全体)|全域|一円", x.get("area_text") or ""))
        out += (f'<p>対応エリアに地名が書かれている会社を数えると、' + "・".join(f"{st}が{n}社" for n, st in sorted(cm, key=lambda t: -t[0])) + 'でした。'
                + (f'このほか「全域」「◯◯一円」のように広く書いている会社が{whole}社あります。' if whole else '')
                + '地名が書かれていなくても来てもらえることがあるので、お迎えの場所はフォームで確かめてください。</p>')
    out += ('<div class="tbl"><table><thead><tr><th>お店の場所</th><th>対応エリア（公式サイトの書き方）</th><th>受付</th><th>5kmの運賃</th><th>お迎え料金</th><th>夜間・早朝</th></tr></thead><tbody>'
            + "".join(r[2] for r in rows) + '</tbody></table></div>')
    out += f'<p class="fare-flag"><b>確定料金ではありません。</b>{FARES_CHECKED}時点で各社の公式サイトを読んでまとめたもので、会社名は出していません。5kmの運賃は料金表から計算した片道の金額で、お迎え料金・待ち時間・高速代は入っていません。料金や対応エリアは変わることがあるので、フォームで候補を出すと、会社名と、お迎えの場所に合わせた目安を確かめられます。</p>'
    return out

for a in AREAS:
    url = f'{SITE}/{a["slug"]}/'
    cta = f'/?pref={a["pref"]}#form'
    ld = [
      {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":a["short"]+"のペットタクシー","item":url}]},
      {"@context":"https://schema.org","@type":"Service","name":a["short"]+"のペットタクシー検索","serviceType":"ペットタクシーの検索と問い合わせ（犬のタクシー・猫のタクシー）","url":url,
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
    <div class="sh"><span class="eyebrow">AREA</span><h2>{e(a["short"])}の対応エリア</h2><p>{e(a["pref"])}のお迎えは、上のフォームでさがせます。下は主な市区です。空いているかどうかは、場所・日時・車の条件を見て会社がお返事します。</p></div>
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

<section id="area-companies">
  <div class="wrap prose">
    {pref_company_table(a["pref"], a["short"], [x for x in _DISP if a["pref"][:-1] in x.get("areas", [])], a["cities"])}
    {city_links(a["pref"])}
    <h3>{e(a["pref"])}の夜間・救急の動物病院</h3>
    <p>夜や休日に具合が悪くなったときのために、{e(a["pref"])}の夜間・救急の動物病院を受付時間つきで<a href="/hospital/night/#pref={quote(a["pref"])}">夜間・救急の動物病院の一覧</a>にまとめています。往診専門の動物病院（家まで来てくれる獣医さん）は<a href="/hospital/visit/#pref={quote(a["pref"])}">往診の一覧</a>、猫だけを診る病院は<a href="/hospital/cat/#pref={quote(a["pref"])}">猫専門の動物病院</a>にあります。</p>
    {gen_dogrun.area_snippet(a["pref"], e)}
    {gen_prefpages.area_snippet(a["pref"], e, [gen_prefcats.NIGHT, gen_prefcats.SOUGI, gen_rojin.CAT, gen_trainers.CAT, gen_sitters.CAT, gen_grooming.CAT, gen_hotels.CAT])}
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
    {area_links(a["slug"], more=True)}
  </div>
</section>
'''
    page = clone_top(a["title"], a["desc"], url, ld_html, f'{a.get("h1", a["short"])}のペットタクシー予約', open_lead(a["pref"]) + a["lede"], a["pref"], area_html,
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
    # 写真はその記事だけのもの（tools/page_images.py）。届いていなければ写真の枠を出さない
    own = f'{g["slug"]}.jpg'
    has_img = os.path.exists(os.path.join(ROOT, "img", "guide", own))
    img_alt = g["img_alt"] if g.get("img") == own else GUIDE_ALT.get(g["slug"], "")
    og_img, og_w, og_h = (f'/img/guide/{own}', 1200, 800) if has_img else ("/img/hero.jpg", 1200, 900)
    fig = (f'<figure class="art-img"><picture><source srcset="/img/guide/{own[:-4]}.webp" type="image/webp"><img src="/img/guide/{own}" alt="{e(img_alt)}" width="1200" height="800" fetchpriority="high" onerror="this.closest(\'figure\').remove()"></picture>{caption}</figure>'
           if has_img else "")
    checked = f'<p class="small">公式情報の確認日：{e(g["checked"])}</p>\n    ' if g.get("checked") else ""
    ld = [
      {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"ペットの移動ガイド","item":SITE+"/guide/"},
        {"@type":"ListItem","position":3,"name":g["title"],"item":url}]},
      {"@context":"https://schema.org","@type":"Article","headline":g["title"],"description":g["desc"],"url":url,
       "image":SITE + og_img,"datePublished":published,"dateModified":modified,"inLanguage":"ja",
       "author":{"@id":SITE+"/#org"},"publisher":{"@id":SITE+"/#org"},"mainEntityOfPage":url},
    ]
    if g.get("dataset"):  # [B] AIO 11/9：独自データ記事は Dataset としても伝える（引用されやすく）
        ld.append({"@context":"https://schema.org","@type":"Dataset","name":g["title"],"description":g["desc"],"url":url,"inLanguage":"ja",
          "creator":{"@id":SITE+"/#org"},"dateModified":modified,"spatialCoverage":"日本",
          "variableMeasured":g["dataset"]})
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
    page = head(g["seo_title"] + "｜ペットタクシー予約窓口", g["desc"], url, ld_html, og_img, og_w, og_h) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/guide/">ペットの移動ガイド</a> › {e(g["title"])}</nav>
    <h1>{e(g["title"])}</h1>
    <p class="lede">{e(g["lede"])}</p>
    <div class="hero-fare"><b>あなたのルートで、ペットタクシー各社の料金をくらべられます</b><span>お迎えの場所と行き先を入れると、来てもらえる会社ごとの料金の目安が並びます。公式サイトの料金表から計算した概算で、確定料金ではありません。</span><a class="btn" href="/#form" data-cta="guide-fare" style="margin-top:10px">ペットタクシーの料金をくらべる（無料）</a></div>
    <p class="small">ペットタクシー予約窓口　公開 {published.replace("-", ".")}・更新 {modified.replace("-", ".")}</p>
    {fig}
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
    {area_links(more=True)}
    <p class="small" style="margin-top:10px">{'<a href="/guide/pet-taxi-fare-survey/">全国のペットタクシー料金しらべ（距離ごと・都道府県ごとの運賃、お迎え料金・夜間割増）</a>' if g["slug"] != "pet-taxi-fare-survey" else '<a href="/area/">全国のペットタクシー情報（都道府県ごと）</a>'}</p>
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
                            "現在は候補の表示のみです。すべての会社への問い合わせを停止しています。")
    os.makedirs(os.path.join(ROOT, "guide", g["slug"]), exist_ok=True)
    open(os.path.join(ROOT, "guide", g["slug"], "index.html"), "w", encoding="utf-8").write(page)

hub_url = SITE + "/guide/"
# はじめての人が知りたい基本の記事（選び方・料金・当日・ペットだけ）を先に（2026-11-08 飼い主目線のレビュー #9）
_BASIC = ["what-is-pet-taxi", "choose", "fare", "same-day", "pet-only", "taxi-with-pet"]
def _basic_first(slugs): return [x for x in _BASIC if x in slugs] + [x for x in slugs if x not in _BASIC]
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
    <div class="sh"><h2>はじめての方へ・移動の困りごとから調べる</h2></div>
    {guide_cards(_basic_first([g["slug"] for g in GUIDES if g.get("category") not in ("facility", "procedure", "care")]))}
    <div class="sh"><h2>病院・施設名から移動を調べる</h2></div>
    <p>通院先や宿泊先ごとの行き方、受付・乗降場所、帰りの車で確かめたいことをまとめました。</p>
    {guide_cards([g["slug"] for g in GUIDES if g.get("category") == "facility"])}
    <div class="sh"><h2>迷子・犬の登録・引っ越しの手続き</h2></div>
    <p>迷子になったとき、迷子を保護したとき、犬の登録、引っ越し、飼えなくなったときの相談先。全国の窓口は<a href="/jichitai/">迷子・犬の登録・引取りの窓口</a>の一覧から。</p>
    {guide_cards([g["slug"] for g in GUIDES if g.get("category") == "procedure"])}
    <div class="sh"><h2>老犬ホーム・ドッグトレーナー・ペットシッターのえらび方</h2></div>
    <p>預ける・頼む前に知っておきたいこと。全国の一覧は<a href="/rojin-home/">老犬ホーム・老猫ホーム</a>、<a href="/dog-trainer/">ドッグトレーナー・しつけ教室</a>、<a href="/pet-sitter/">ペットシッター</a>、<a href="/trimming/">出張トリミング</a>、<a href="/pet-hotel/">大型犬OK・猫専用のペットホテル</a>から。</p>
    {guide_cards([g["slug"] for g in GUIDES if g.get("category") == "care"])}
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
from terms import TERMS, TERMS_DATE, TERMS_REVISED
def terms_block(v):
    if isinstance(v, tuple) and v[0] == "ul": return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in v[1]) + "</ul>"
    if isinstance(v, tuple) and v[0] == "html": return f"<p>{v[1]}</p>"
    return f"<p>{e(v)}</p>"
terms_url = SITE + "/terms/"
tp = head("利用規約｜ペットタクシー予約窓口", "ペットタクシー予約窓口（ペットタクシーの検索と問い合わせ）の利用規約です。サービスの内容、予約の成立、料金とお支払い、キャンセル、責任の範囲などを定めています。", terms_url, "") + f"""
<main>
<section class="area-hero"><div class="wrap"><h1>利用規約</h1><p class="lede">ペットタクシー予約窓口をご利用いただく前に、お読みください。</p></div></section>
<section><div class="wrap prose terms">
{''.join(f'<h2>{e(h)}</h2>' + ''.join(terms_block(v) for v in body) for h, body in TERMS)}
<p class="small">{TERMS_DATE} 制定・{TERMS_REVISED} 改定</p>
</div></section>
</main>
""" + foot("/#form")
os.makedirs(os.path.join(ROOT, "terms"), exist_ok=True)
open(os.path.join(ROOT, "terms", "index.html"), "w", encoding="utf-8").write(tp)

# 提携規約（/partner/terms/）。本文は tools/partner_terms.py
from partner_terms import PTERMS, PTERMS_DATE, PTERMS_REVISED
pterms_url = SITE + "/partner/terms/"
ptp = head("提携規約（ペットタクシー会社さま向け）｜ペットタクシー予約窓口", "ペットタクシー予約窓口と提携してくださるペットタクシー会社さま向けの規約です。問い合わせとお返事、予約の確定、手数料（当面はいただきません）、個人情報、提携の終了などを定めています。", pterms_url, "") + f"""
<main>
<section class="area-hero"><div class="wrap"><h1>提携規約<small style="display:block;font-size:.95rem;color:var(--o-d)">ペットタクシー会社さま向け</small></h1><p class="lede">当サイトと提携してくださる会社さまとの約束です。同意のお手続きは、あらためてメールでご案内します。</p></div></section>
<section><div class="wrap prose terms">
{''.join(f'<h2>{e(h)}</h2>' + ''.join(terms_block(v) for v in body) for h, body in PTERMS)}
<p class="small">{PTERMS_DATE} 制定・{PTERMS_REVISED} 改定（版の番号 {PTERMS_HASH}）</p>
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
# 手数料の率はサイトに出さない（Nori 2026-11-01）。当面は手数料なしで提携する（Nori 2026-11-02）
PT_CSS = """<style>
.pt-shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:28px;max-width:720px;margin:0 auto}
.pt-shots figure{margin:0}.pt-shots .ph{border:8px solid #1c1a18;border-radius:30px;overflow:auto;max-height:560px;background:#fff;max-width:320px;margin:0 auto;-webkit-overflow-scrolling:touch}
.pt-shots img{display:block;width:100%;height:auto}
.pt-shots figcaption{font-size:.92rem;color:var(--ink-2);margin:14px auto 0;max-width:320px}.pt-shots figcaption b{display:block;color:var(--ink);font-size:1rem;margin-bottom:2px}
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
.pt-form .group-h{margin-top:8px}
.pt-q{display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px;font-size:.92rem}
.pt-q>span{display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
.pt-q input[type=number]{width:76px;min-height:42px;padding:8px 10px}
.pt-form input[type=url]{width:100%;font:inherit;font-size:16px;padding:14px 16px;border:1.5px solid var(--line);border-radius:14px;background:#fbfaf9;min-height:52px}
.pt-q select{width:auto;max-width:100%;min-height:42px;padding:8px 36px 8px 12px}
.pt-sub{margin:-8px 0 18px;padding:12px 14px;border-left:3px solid var(--o-l);background:#fffaf5;border-radius:0 12px 12px 0}
.pt-sub .pt-q+.pt-q,.pt-sub .pt-q+small{margin-top:10px}.pt-sub small{display:block;font-size:.8rem;color:var(--ink-3)}
.pt-sub b{display:block;font-size:.82rem;color:var(--ink-2);margin:10px 0 4px}.pt-sub b:first-child{margin-top:0}
.pt-form .seg{gap:6px}.pt-form .seg span{padding:8px 14px;font-size:.88rem}
.pt-form .seg.missing span{border-color:#c0392b}
.pt-ac{position:relative}.pt-ac ul{position:absolute;z-index:5;left:0;right:0;top:100%;margin:4px 0 0;padding:4px 0;list-style:none;background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);max-height:260px;overflow:auto}
.pt-ac li{padding:10px 14px;cursor:pointer;font-size:.92rem}.pt-ac li:hover,.pt-ac li[aria-selected=true]{background:var(--o-l)}
.pt-ac .ok{display:block;margin-top:6px;font-size:.84rem;color:#2f7d32}.pt-ac small.attr{display:block;text-align:right;font-size:.7rem;color:var(--ink-3);padding:2px 10px}
.pt-time{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:8px}.pt-time select{width:auto;min-height:42px;padding:8px 32px 8px 12px}
.pt-prefs-more summary{cursor:pointer;font-size:.86rem;color:var(--o-d);margin-top:8px}
.pt-more{margin:18px 0;border:1px dashed var(--line);border-radius:14px;padding:10px 14px}.pt-more>summary{cursor:pointer;font-weight:700}
.pt-more[open]>summary{margin-bottom:12px}
.pt-combo small{display:block;font-size:.82rem;color:var(--ink-3)}.pt-combo b{display:block;font-size:.86rem;margin:12px 0 6px}.pt-combo .pt-sub{margin:8px 0 0}
.pt-note{font-size:.84rem;color:var(--ink-2);background:#fffaf5;border-radius:12px;padding:8px 12px;margin:-4px 0 14px}
</style>"""
def _ic(path):  # メリットのアイコン（線の絵）
    return '<svg viewBox="0 0 48 48" fill="none" stroke="#ff6a1a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="24" cy="24" r="22" fill="#fff1e6" stroke="none"/>' + path + '</svg>'
PT_MERITS = [
 (_ic('<path d="M15 24h18M24 15v18"/><circle cx="24" cy="24" r="12"/>'), "はじめる費用は0円", "登録料・月額料金・掲載料はいただきません。お問い合わせを受け取るのも、お返事するのも無料です。"),
 (_ic('<rect x="12" y="15" width="24" height="18" rx="3"/><path d="M12 18l12 8 12-8"/>'), "電話の対応はいりません", "お問い合わせはメールで届きます。リンクを開いて、確定料金（税込）を入れるだけでお返事できます。日時は飼い主さんの希望のままです。"),
 (_ic('<path d="M14 16h20l-7 9v8l-6 3V25z"/>'), "条件に合うお問い合わせだけ届きます", "お迎えできるエリア・乗せられる動物・送迎できる時間・ペットの体重や頭数・ケージなど、会社さまの条件に合うお問い合わせだけをお届けします。たとえば犬・猫だけの会社さまに、うさぎや鳥のお問い合わせは届きません。"),
 (_ic('<path d="M16 32V20l8-5 8 5v12z"/><path d="M21 32v-6h6v6"/>'), "料金は会社さまが決めます", "サイトの料金は目安です。確定料金はいつも会社さまがお返事で決めます。当サイトが値引きをお願いすることはありません。"),
 (_ic('<path d="M17 25l5 5 10-11"/>'), "受けられないときは返事不要", "空いていないときや条件が合わないときは、そのままにしておいてください。お断りのご連絡もいりません。"),
 (_ic('<circle cx="19" cy="21" r="4"/><circle cx="29" cy="21" r="4"/><path d="M13 33c1-4 4-6 6-6s5 2 6 6M23 33c1-4 4-6 6-6s5 2 6 6"/>'), "決まってからつながる", "飼い主さんのお名前と連絡先は、予約が確定してからお伝えします。運賃のお支払いは、これまでどおり飼い主さんから会社さまへ直接です。"),
]
PT_FAQ = [
 ("本当に電話は使わなくていいですか？", "はい。当サイトからのご連絡は、すべてメールです。予約が確定したあと、飼い主さんとの打ち合わせで会社さまが電話を使うのは自由です。"),
 ("料金表は変えないといけませんか？", "いいえ。いまの料金表のままで大丈夫です。サイトでは会社さまの料金表から目安を計算し、「確定料金ではありません」と添えて表示します。確定料金は会社さまがお返事で決めます。"),
 ("飼い主さんが何社にも問い合わせることはありますか？", "あります。飼い主さんは1社だけに問い合わせることも、条件に合う会社にまとめて問い合わせることもできます。何社かに問い合わせたときは、届いたお返事をくらべて飼い主さんが1社を選びます。選ばれなかったときは「締め切り」のお知らせをお送りします。"),
 ("手数料はかかりますか？", "当面、手数料はいただきません。登録料・月額料金・掲載料もかかりません。将来いただくことにした場合は、予約が確定して送迎をした分だけにかけ、率と始める日を30日前までにメールでお知らせします。お問い合わせを受け取っただけ、お返事しただけ、選ばれなかったときにはかかりません。ご了承いただけないときは、違約金なしで提携をやめられます。"),
 ("キャンセルになったら手数料はどうなりますか？", "いまは手数料はいただいていません。将来いただくことになった場合も、送迎をしなかったときはかかりません。キャンセル料は会社さまのキャンセル規定のとおりで、キャンセル料に手数料をかけることはありません。なお、送迎があったかどうかは、送迎のあとに飼い主さんにも確かめ、月末のご報告と照らし合わせます（提携規約の第9条）。"),
 ("条件に合わないお問い合わせが届くことはありますか？", "お申し込みでうかがった条件（お迎えできるエリア、乗せられる動物、送迎できる時間、大型犬の体重や頭数、同乗の人数、ケージ）に合わないお問い合わせはお届けしません。たとえば犬・猫だけの会社さまにうさぎのお問い合わせは届かず、エリアの外のお問い合わせも届きません。条件がまだ分からない項目があるときは、メールに「引き受ける前にご確認ください」と書いてお届けしますので、できないときはお受けにならないでください。条件はメールでいつでも変えられます。"),
 ("ほかの予約サイトや自社の予約と一緒に使えますか？", "はい。いまの予約の受け方はそのままで、当サイトのお問い合わせを一つの窓口として足していただくイメージです。"),
 ("いまの候補の一覧で、会社さまはどう見えていますか？", "当サイトでは、公式サイトに公開されている料金表と営業時間をもとに、各地の会社を候補として表示しています。提携していない会社さまは、社名と公式サイトへのリンク、料金の目安を載せています（口コミは出さず、お店の場所はおおまかにしています）。飼い主さんは当サイトから問い合わせを送れないため、公式サイトで直接お問い合わせいただく形です。提携いただくと、社名の横に印が付き、地図サービスの口コミ（星と本文）も表示され、飼い主さんが当サイトから空き状況と料金を問い合わせできるようになります。載せ方の修正や、掲載をやめたいご希望は、お問い合わせからいつでもお知らせください。"),
 ("やめたいときはどうすればいいですか？", "メールでお知らせいただければ、いつでも止められます。違約金などはありません。すでに確定している予約は、最後までお願いします。"),
]

# 提携の申し込みフォーム（Nori 2026-11-08「料金が税込みかとか、あとから聞かなくていいように」）。
# 候補カードの料金の計算（booking/Code.gs の displayPrice_）に要る項目をそろえて、選ぶ形で聞く
# 選ぶ欄はタップ1回で選べるボタン（Nori 2026-11-10「回答の手間をできるだけ減らす」）。値は選んだボタンの文字
def pt_sel(i, k, opts, req=True, ph=""):
    return (f'<div class="seg pt-one" id="{i}" data-k="{e(k)}"' + (' data-req="1"' if req else '') + ' role="radiogroup">'
            + "".join(f'<label><input type="radio" name="{i}" value="{e(x)}"><span>{e(x)}</span></label>' for x in opts) + '</div>')
def pt_chk(i, k, opts):
    return (f'<div class="checks seg" id="{i}" data-k="{e(k)}">'
            + "".join(f'<label><input type="checkbox" value="{e(x)}"><span>{e(x)}</span></label>' for x in opts) + '</div>')
def pt_n(before="", after="", opt=False):
    return (f'<span>{e(before)}<input type="number" min="0" step="any" inputmode="decimal" data-p="{e(before)}" data-u="{e(after)}"'
            + (' data-opt="1"' if opt else '') + f' aria-label="{e(before + "◯" + after)}">{e(after)}</span>')
def pt_q(k, *parts, opt=False):
    return f'<div class="pt-q" data-k="{e(k)}"' + (' data-opt="1"' if opt else '') + '>' + "".join(parts) + '</div>'
def pt_if(sel_id, vals, inner):
    return f'<div class="pt-sub" data-if="{sel_id}" data-v="{e("|".join(vals))}" hidden>{inner}</div>'
def pt_f(label, inner, note="", lid=""):
    return (f'<div class="f">' + (f'<label for="{lid}">' if lid else '<span class="lbl">') + e(label)
            + (f'<span class="any">{e(note)}</span>' if note else '') + ('</label>' if lid else '</span>') + inner + '</div>')
PT_LEG = ["かからない", "定額", "距離で決まる", "市区町村ごとに決まっている"]
def pt_leg(i, k, extra=()):
    return (pt_sel(i, k, list(extra) + PT_LEG)
            + pt_if(i, ["定額"], pt_q(k + "（定額）", pt_n("", "円")))
            + pt_if(i, ["距離で決まる"], pt_q(k + "（距離）", pt_n("", "kmまで無料、", opt=True), pt_n("その先 ", "kmごとに"), pt_n("", "円")) + '<small>無料の距離がなければ空けたままで大丈夫です。</small>')
            + pt_if(i, ["市区町村ごとに決まっている"], f'<textarea data-k="{e(k)}（市区町村ごと）" rows="3" maxlength="400" placeholder="例：安芸区 1,000円、広島市内 2,000円、そのほか 1kmごとに100円"></textarea>'))
PT_FARE_DETAIL = "".join([
  pt_f("料金の金額は", pt_sel("p_tax", "税込・税別", ["税込", "税別（消費税を足していただく金額）"]), "", "p_tax"),
  pt_f("料金の決め方", pt_sel("p_kind", "料金の決め方", ["距離で決まる", "時間で決まる", "エリア・区間ごとの定額", "毎回お見積もり"])
    + pt_if("p_kind", ["距離で決まる"],
        '<b>基本料金（初乗り）</b>' + pt_q("基本料金", pt_n("", "円で"), pt_n("", "kmまで"))
        + '<b>距離の料金</b>' + pt_q("距離の料金", pt_n("その先 ", "kmごとに"), pt_n("", "円"))
        + '<b>1km未満の距離は</b>' + pt_q("1km未満の距離", pt_sel("p_kmround", "1km未満の距離", ["1kmに切り上げ", "切り捨て", "そのまま（小数で）計算"], ph="選んでください"))
        + '<b>距離で単価が変わるとき</b><textarea data-k="距離で変わる単価" rows="2" maxlength="300" placeholder="例：20kmから先は1kmごとに180円"></textarea>')
    + pt_if("p_kind", ["時間で決まる"],
        '<b>基本料金</b>' + pt_q("時間制の基本料金", pt_n("", "分まで"), pt_n("", "円"))
        + '<b>延長</b>' + pt_q("時間制の延長", pt_n("その先 ", "分ごとに"), pt_n("", "円")))
    + pt_if("p_kind", ["エリア・区間ごとの定額"],
        '<textarea data-k="区間ごとの定額" rows="3" maxlength="400" placeholder="例：広島市内 3,000円、広島空港まで 15,000円"></textarea>'), "", "p_kind"),
  pt_f("お迎え料金（お店からお迎えの場所まで）", pt_leg("p_pick", "お迎え料金"), "", "p_pick"),
  pt_f("回送料金（降りた場所からお店に戻る分）", pt_leg("p_back", "回送料金", ["お迎え料金と同じ"]), "", "p_back"),
  pt_f("夜間・早朝の割増", pt_sel("p_night", "夜間・早朝の割増", ["なし", "率で増える（◯割増など）", "定額を足す"])
    + pt_if("p_night", ["率で増える（◯割増など）"], pt_q("割増の率", pt_n("", "％増し")))
    + pt_if("p_night", ["定額を足す"], pt_q("割増の金額", pt_n("", "円を足す")))
    + pt_if("p_night", ["率で増える（◯割増など）", "定額を足す"],
        '<b>時間帯</b>' + pt_q("割増の時間帯", pt_n("", "時から"), pt_n("", "時まで"))
        + '<b>割増になるのは</b>' + pt_q("割増のかかり方", pt_sel("p_nightby", "割増のかかり方", ["乗っているあいだに少しでも時間帯に入れば", "乗る時刻が時間帯のときだけ"]))
        + '<b>割増をかける料金</b>' + pt_q("割増をかける料金", pt_sel("p_nighton", "割増をかける料金", ["乗車の料金だけ", "お迎え・回送の料金にもかける"]))), "", "p_night"),
  pt_f("待ち時間の料金", pt_sel("p_wait", "待ち時間の料金", ["かからない", "かかる"])
    + pt_if("p_wait", ["かかる"], pt_q("待ち時間の内訳", pt_n("最初の ", "分は無料、", opt=True), pt_n("その先 ", "分ごとに"), pt_n("", "円"))), "", "p_wait"),
  pt_f("高速道路・有料道路の料金", pt_sel("p_toll", "高速道路の料金", ["実費をいただく（乗っている区間だけ）", "実費をいただく（お店に戻る分も）", "料金に含む", "使わない"]), "", "p_toll"),
  pt_f("頭数による料金", pt_sel("p_heads", "頭数による料金", ["頭数で変わらない", "2頭目から足す"])
    + pt_if("p_heads", ["2頭目から足す"], pt_q("2頭目からの料金", pt_n("1頭ごとに ", "円"))), "", "p_heads"),
  pt_f("体重・大きさによる料金", pt_sel("p_kg", "体重による料金", ["体重で変わらない", "重い子は足す"])
    + pt_if("p_kg", ["重い子は足す"], pt_q("体重による料金", pt_n("", "kg以上は"), pt_n("", "円を足す"))), "", "p_kg"),
  pt_f("同乗する人の料金", pt_sel("p_ridefee", "同乗する人の料金", ["人数で変わらない", "人数で足す"])
    + pt_if("p_ridefee", ["人数で足す"], pt_q("同乗する人の追加料金", pt_n("", "人目から1人"), pt_n("", "円"))), "", "p_ridefee"),
  pt_f("当日の依頼", pt_sel("p_sameday", "当日の依頼", ["受けない（前日まで）", "受けない（2日前まで）", "受けない（3日前より前まで）", "空いていれば受ける", "空いていれば受ける（当日の追加料金あり）"])
    + pt_if("p_sameday", ["空いていれば受ける", "空いていれば受ける（当日の追加料金あり）"], pt_q("当日の締め切り", pt_n("お迎えの ", "時間前まで", opt=True)))
    + pt_if("p_sameday", ["空いていれば受ける（当日の追加料金あり）"], pt_q("当日の追加料金", pt_n("", "円"))), "", "p_sameday"),
  pt_f("キャンセル料", pt_sel("p_cxl", "キャンセル料", ["かからない", "前日まで無料、当日はかかる", "前々日から・当日以外もかかる"])
    + pt_if("p_cxl", ["前日まで無料、当日はかかる"], pt_q("当日のキャンセル料", pt_n("運賃の ", "％"))), "", "p_cxl"),
])
# 料金は「料金表のページを見てもらう」を選べば、くわしい質問をとばせる（当サイトがページを読んで入れる）
PT_FARE = "".join([
  pt_f("料金のうかがい方", pt_sel("p_faremode", "料金のうかがい方", ["料金表のページを見てほしい（入力をとばす）", "ここで入力する"])
    + pt_if("p_faremode", ["料金表のページを見てほしい（入力をとばす）"], '<b>料金表のページのURL</b><input type="url" id="p_fareurl" data-k="料金ページ" required placeholder="https://">')
    + pt_if("p_faremode", ["ここで入力する"], '<div class="pt-fare">' + PT_FARE_DETAIL + '</div>'), "", ""),
  pt_f("お支払いのタイミング", pt_sel("p_paytime", "お支払いのタイミング", ["乗る前", "降りるとき", "後日（請求書など）"]), "", "p_paytime"),
])
PT_FARE_MORE = "".join([
  pt_f("往復（病院などで待って帰る）の料金", pt_sel("p_round", "往復の料金", ["行きと帰りの料金に、待ち時間の料金を足す", "行きと帰りを続けた1回の距離で計算", "往復の料金表がある", "決まっていない"]), "", "p_round"),
  pt_f("長い距離", pt_sel("p_long", "長い距離", ["同じ料金表で計算する", "一定の距離を超えると別にお見積もり"])
    + pt_if("p_long", ["一定の距離を超えると別にお見積もり"], pt_q("お見積もりになる距離", pt_n("", "kmを超えると"))), "", "p_long"),
  pt_f("空港など、決まった区間の定額", '<input type="text" id="p_fixed" data-k="決まった区間の定額" maxlength="300" placeholder="例：広島市内→広島空港 15,000円">', "あれば", "p_fixed"),
  pt_f("料金でほかに伝えたいこと", '<textarea id="p_fare" data-k="料金の補足" rows="2" maxlength="500" placeholder="例：往復は1割引き"></textarea>', "あれば", "p_fare"),
])
# 車種（ペットタクシーで多い車。予約のしくみは車種から軽バンかどうかを読む）
PT_CARS = ["スズキ エブリイ", "ダイハツ ハイゼットカーゴ／アトレー", "ホンダ N-VAN", "ホンダ N-BOX", "スズキ スペーシア", "トヨタ ハイエース", "日産 キャラバン", "トヨタ ノア／ヴォクシー", "日産 セレナ",
           "ホンダ ステップワゴン", "トヨタ アルファード／ヴェルファイア", "トヨタ シエンタ", "ホンダ フリード", "三菱 デリカD:5", "トヨタ JPN TAXI", "トヨタ プリウス"]
PT_LARGE = ["1頭まで", "2頭まで", "3頭まで", "4頭以上"]
PT_COND = "".join([
  pt_f("1回に乗せられる頭数", pt_sel("p_maxpets", "乗せられる頭数", ["1頭", "2頭まで", "3頭まで", "4頭以上"]), "", "p_maxpets"),
  pt_f("一緒に乗れる飼い主さん", pt_sel("p_ride", "飼い主さんの同乗", ["同乗できない", "1人まで", "2人まで", "3人まで", "4人以上"]), "", "p_ride"),
  pt_f("大型犬（30kg以上）は何頭まで乗せられるか", pt_sel("p_large", "大型犬（30kg以上）の数", ["乗せられない"] + PT_LARGE), "", "p_large"),
  pt_f("乗せられる体重（いちばん大きい子）", pt_sel("p_maxkg", "乗せられる体重", ["10kgまで", "20kgまで", "30kgまで", "40kgまで", "50kgまで", "50kgを超えても乗せられる"]), "", "p_maxkg"),
  pt_f("ペットだけの送迎（飼い主さんが乗らない）", pt_sel("p_petonly", "ペットだけの送迎", ["できる", "できない"]), "", "p_petonly"),
  pt_f("ケージ・キャリー", pt_sel("p_cage", "ケージ", ["なくても乗せられる", "必要（貸し出しあり）", "必要（貸し出しなし）"])
    + pt_if("p_cage", ["必要（貸し出しあり）"], '<b>貸し出せるいちばん大きいケージ</b>' + pt_sel("p_lend", "貸し出せるケージ", ["小型犬用（10kgまで）", "中型犬用（20kgまで）", "大型犬用（40kgまで）", "もっと大きい子も入る"], req=False)), "", "p_cage"),
  pt_f("ワクチン", pt_sel("p_vac", "ワクチン", ["接種していなくても乗せられる", "接種していれば証明はいらない", "証明が必要（狂犬病の予防注射だけ）", "証明が必要（狂犬病と混合ワクチン）"]), "", "p_vac"),
  pt_f("大きな荷物（スーツケース・大きなケージ・カートなど）", pt_sel("p_lug", "大きな荷物", ["載せられる", "少しなら載せられる", "載せられない"]), "", "p_lug"),
  pt_f("途中で寄る（経由地）", pt_sel("p_via", "途中で寄る", ["できる（料金は距離と待ち時間のとおり）", "できる（1か所ごとに料金を足す）", "できない"])
    + pt_if("p_via", ["できる（1か所ごとに料金を足す）"], pt_q("寄るときの料金", pt_n("1か所ごとに ", "円"))), "", "p_via"),
])
# 介護が必要な子（お客さまのフォームの「どんな手助けが必要ですか？」と同じ言葉。app.js の CARE_OPTS）
PT_CARE = pt_f("介護が必要な子（歩くのがつらい・寝たきりなど）", pt_sel("p_care", "介護が必要な子", ["受けられる", "相談して決める", "受けられない"])
    + pt_if("p_care", ["受けられる", "相談して決める"], '<b>介護が必要な大型犬（30kg以上）を運ぶ</b>' + pt_sel("p_carebig", "介護が必要な大型犬", ["運べる", "相談して決める", "運べない"])), "", "p_care")
PT_QUALS = ["愛玩動物看護師（国家資格）", "獣医師", "ペット介護士・ペットケアの民間資格", "ペットの救急救命の講習を受けた", "動物取扱責任者", "とくになし"]
PT_NEED = [
 ("お申し込みでうかがうこと", ["会社名・屋号、ご担当者のお名前", "お問い合わせを受け取るメールアドレス（窓口がお問い合わせフォームだけの会社さまも、メールで受け取れるアドレスをお知らせください）", "車が出発するお店の場所とお迎えに行ける範囲（km）、行き先までの距離、受けられる曜日・時間、車の台数と種類", "乗せられる動物・頭数・体重、大型犬は何頭まで、ペットだけの送迎、ケージ、ワクチン、大きな荷物、途中で寄れるか", "介護が必要な子を受けられるか、介護が必要な大型犬（30kg以上）を運べるか"]),
 ("料金でうかがうこと", ["料金表のページのURL", "税込か税別か", "基本料金と距離（または時間）の料金、1km未満の数え方", "お迎え料金・回送料金", "夜間・早朝の割増（率か金額、時間帯）", "待ち時間・高速道路・頭数・体重・同乗する人の料金", "キャンセル料、お支払い方法とタイミング"]),
 ("そのほかうかがうこと", ["動物取扱業の登録番号", "お持ちの事業の許可・届出（旅客の許可、貨物軽自動車運送事業の届出など）", "スタッフの資格（愛玩動物看護師など）", "往復・長い距離・空港などの料金", "依頼から出発できるまでの時間"]),
]
pt_merits = "".join(f'<div class="pt-merit">{ic}<h3>{e(t)}</h3><p>{e(d)}</p></div>' for ic, t, d in PT_MERITS)
pt_faq = "".join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in PT_FAQ)
pt_need = "".join(f'<div><h3>{e(h)}</h3><ul>' + "".join(f"<li>{e(x)}</li>" for x in xs) + '</ul></div>' for h, xs in PT_NEED)
pt_ld = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in PT_FAQ]}, ensure_ascii=False) + '</script>'
# 提携の申し込みフォームの動き（手書きのJSは tools/partner_form.js。お店の場所の候補は、トップと同じブラウザ用のキーを使う）
_top_src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
pt_js = (open(os.path.join(ROOT, "tools", "partner_form.js"), encoding="utf-8").read()
         .replace("__GAS__", gas).replace("__PKEY__", re.search(r'var PLACES_KEY = "([^"]*)"', _top_src).group(1))
         .replace("__PREFS__", json.dumps(PREFS47, ensure_ascii=False)).replace("__PREFLL__", re.search(r"var PREF_LL = (\[\[.*?\]\]);", _top_src).group(1)))
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
<li><span class="who s">当サイト</span><h3>会社さまへメールでお届け</h3><p>日時・お迎えの場所・行き先・同乗する人数・荷物・介助の要否・ペットの種類や体重・頭数・ケージの有無・飼い主さんのメモと、料金の目安をお届けします。</p><span class="lock">🔒 この段階では、飼い主さんのお名前と連絡先はお伝えしません</span></li>
<li><span class="who y">会社さま</span><h3>空いていればお返事</h3><p>メールのリンクを開き、確定料金（税込・一般道のとき／高速を使うとき）と、飼い主さんからの連絡を受ける電話番号・メールを入れて送るだけです（登録の連絡先が最初から入っています）。日時は飼い主さんの希望のままで、日付だけのご依頼のときだけ時刻を入れます。受けられないとき・日時が合わないときは、何もしなくて大丈夫です。<a href="#screens">画面の見本を見る</a></p></li>
<li><span class="who c">飼い主さん</span><h3>内容を見て予約を確定</h3><p>飼い主さんが「この内容で予約する」を押した時点で予約が確定します。何社かに問い合わせたときは、くらべて1社を選びます。選ばれなかった会社さまには「締め切り」のお知らせが届きます。</p></li>
<li><span class="who y">会社さま</span><h3>飼い主さんと直接やり取りして送迎</h3><p>確定すると、飼い主さんのお名前と連絡先をメールでお知らせします。そのあとの打ち合わせ・送迎・運賃のお受け取りは、会社さまと飼い主さんで直接お願いします。</p></li>
</ol>
</div></section>

<section class="pt-sec" id="screens"><div class="wrap">
<h2>届くメールとお返事の画面（見本）</h2><p class="sub">実際に会社さまへ届くメールと、お返事の画面です。内容は架空のお問い合わせです。画面の中はスクロールできます。</p>
<div class="pt-shots">
<figure><div class="ph"><img src="/img/partner/mail.webp" width="390" height="1365" loading="lazy" alt="当サイトから届く「空き状況と料金のお問い合わせ」メールの見本。日時・お迎えの場所・行き先・ペット・同乗人数が書かれ、お名前と連絡先は伏せてある"></div><figcaption><b>1. メールが届く</b>日時・場所・ペットの様子が届きます。お名前と連絡先はまだ伏せています。受けられないときは何もしなくて大丈夫です。</figcaption></figure>
<figure><div class="ph"><img src="/img/partner/reply.webp" width="390" height="2007" loading="lazy" alt="メールのリンクから開くお返事の画面の見本。ご依頼の内容は変えられない枠にあり、確定料金と連絡先を入れて「この内容でお返事する」を押す"></div><figcaption><b>2. リンクを開いて数字を入れる</b>ご依頼の内容（日時など）は変えられない枠に出ます。確定料金と連絡先を入れて「この内容でお返事する」を押すだけです。ログインやアプリは要りません。</figcaption></figure>
</div>
</div></section>

<section class="pt-sec" id="fee"><div class="wrap">
<h2>費用とお金の流れ</h2><p class="sub">当サイトが運賃をお預かりすることはありません。お金の流れはいまと同じです。</p>
<div class="pt-money" role="img" aria-label="飼い主さんは運賃を会社さまへ直接支払います。当サイトへの手数料は当面ありません">
<div class="box">飼い主さん<small>当サイトの利用は無料</small></div><div class="arw">運賃を<br>当日直接</div><div class="box">会社さま<small>これまでどおり受け取り</small></div><div class="arw">手数料は<br>当面なし</div><div class="box">当サイト<small>当面は手数料をいただきません</small></div>
</div>
<div class="pt-fee"><table>
<tr><th>登録料・月額料金・掲載料</th><td><b>0円</b></td></tr>
<tr><th>お問い合わせの受け取り・お返事</th><td><b>0円</b>（選ばれなかったときも0円）</td></tr>
<tr><th>予約が確定し、送迎をしたとき</th><td><b>当面0円</b></td></tr>
<tr><th>キャンセルで送迎しなかったとき</th><td><b>0円</b></td></tr>
</table>
<p class="now">当面、手数料はいただきません。将来いただくことにした場合は、率と始める日を30日前までにメールでお知らせし、それより前に確定した予約にさかのぼってご請求することはありません。ご了承いただけないときは、違約金なしで提携をやめられます。くわしくは<a href="/partner/terms/">提携規約</a>の第8条をご覧ください。</p>
</div>
</div></section>

<section class="pt-sec alt"><div class="wrap">
<h2>提携までの4ステップ</h2>
<ol class="pt-steps">
<li><b>このページから申し込む</b><span>下のフォームに、エリア・時間帯・料金などを入れて送ってください（10分ほど。ほとんど選ぶだけです）。</span></li>
<li><b>内容の確認</b><span>当サイトで公式サイトなどを拝見し、数日以内にメールでご連絡します。わからない点はメールでおたずねします。お問い合わせを受け取るメールアドレスには確認のメールをお送りし、届くこと・お返事できることを確かめます。</span></li>
<li><b>提携規約のご確認</b><span>お問い合わせとお返事のしかた、個人情報の扱いなどを定めた<a href="/partner/terms/">提携規約</a>をご確認ください。規約への同意のお手続きは、あらためてメールでご案内します。</span></li>
<li><b>お問い合わせのお届け開始</b><span>候補の一覧で問い合わせできる状態になり、条件に合うお問い合わせがメールで届きはじめます。</span></li>
</ol>
</div></section>

<section class="pt-sec"><div class="wrap">
<h2>お申し込みでうかがうこと</h2>
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
<form id="partnerForm" class="pt-form" novalidate>
  <div aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden"><label>空欄のままにしてください<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
  
  <div class="group-h"><span>1</span>会社とご連絡先</div>
  <div class="f"><label for="p_co">会社名・屋号</label><input type="text" id="p_co" data-k="会社名・屋号" required autocomplete="organization"></div>
  <div class="f"><label for="p_name">ご担当者のお名前</label><input type="text" id="p_name" name="name" required autocomplete="name"></div>
  <div class="f"><label for="p_email">お問い合わせを受け取るメールアドレス<span class="any">飼い主さんからのお問い合わせがここに届きます。窓口がお問い合わせフォームだけの会社さまも、メールで受け取れるアドレスを入れてください</span></label><input type="email" id="p_email" name="email" required autocomplete="email"></div>
  <div class="group-h"><span>2</span>お店とお迎えのエリア</div>
  <div class="f"><label for="p_shop">車が出発するお店・事業所の住所</label>
    <div class="pt-ac"><input type="text" id="p_shop" data-k="車が出発する場所" required autocomplete="street-address" placeholder="例：広島県広島市安芸区矢野西1丁目2-3"><ul id="p_shopList" hidden></ul><span class="ok" id="p_shopOk" hidden></span></div></div>
  {pt_f("お迎えに行ける範囲", pt_sel("p_radius", "お迎えに行ける範囲", ["お店から5kmまで", "10kmまで", "20kmまで", "30kmまで", "50kmまで", "80kmまで", "100kmまで"]), "", "")}
  <div class="f"><span class="lbl">お迎えできる都道府県<span class="any">お店の場所と範囲から自動で選んでいます。ちがうところだけ直してください</span></span>
    <div class="checks seg" id="p_prefs" data-k="都道府県"></div>
    <details class="pt-prefs-more"><summary>ほかの都道府県も選ぶ</summary><div class="checks seg" id="p_prefs2">{''.join(f'<label><input type="checkbox" value="{p}"><span>{p}</span></label>' for p in PREFS47)}</div></details></div>
  {pt_f("行き先までの距離", pt_sel("p_dest", "行き先までの距離", ["お迎えの都道府県の中だけ", "距離に上限がある", "全国どこへでも行ける"])
    + pt_if("p_dest", ["距離に上限がある"], pt_q("行き先までの上限", pt_n("乗っている距離 ", "kmまで"))), "", "")}
  <div class="group-h"><span>3</span>受けられる時間と車</div>
  <div class="f"><span class="lbl">受けられる曜日</span>{pt_chk("p_days", "受けられる曜日", ["月", "火", "水", "木", "金", "土", "日", "祝日"])}</div>
  <div class="f"><span class="lbl">受けられる時間</span>{pt_sel("p_allday", "24時間", ["24時間", "時間を決めている"])}
    <div class="pt-sub" data-if="p_allday" data-v="時間を決めている" hidden><div class="pt-time"><select id="p_from" aria-label="何時から">{''.join(f'<option value="{h}"' + (' selected' if h == 8 else '') + f'>{h}:00</option>' for h in range(0, 24))}</select>から<select id="p_to" aria-label="何時まで">{''.join(f'<option value="{h}"' + (' selected' if h == 20 else '') + f'>{h}:00</option>' for h in range(1, 25))}</select>まで</div></div></div>
  {pt_f("時間外の依頼", pt_sel("p_off", "時間外の依頼", ["受けない", "相談に応じる"]), "", "")}
  {pt_f("車の台数", pt_sel("p_cars", "車の台数", ["1台", "2台", "3台以上"]), "", "")}
  <div class="f"><span class="lbl">車種<span class="any">お使いの車をすべて</span></span>{pt_chk("p_cartype", "車種", PT_CARS)}
    <input type="text" id="p_carother" data-k="車種（そのほか）" maxlength="100" placeholder="ほかの車種（例：マツダ ボンゴ）" aria-label="ほかの車種" style="margin-top:8px"></div>
  <div class="group-h"><span>4</span>乗せられる動物と条件</div>
  <p class="pt-note">乗せられる動物のほかは、わかるところだけで大丈夫です。</p>
  <div class="f"><span class="lbl">乗せられる動物</span>{pt_chk("p_animals", "乗せられる動物", ["犬", "猫", "うさぎ・フェレットなどの小動物", "鳥", "爬虫類・両生類", "魚"])}</div>
  {PT_COND}
  {PT_CARE}
  <div class="group-h"><span>5</span>料金とお支払い</div>
  {PT_FARE}
  <div class="f"><span class="lbl">お支払い方法</span>{pt_chk("p_pays", "お支払い方法", PAYS)}</div>
  <div class="group-h"><span>6</span>そのほか</div>
  <div class="f"><label for="p_url">ホームページ</label><input type="url" id="p_url" data-k="ホームページ" placeholder="https://" required></div>
  {pt_f("依頼を受けてから出発できるまで", pt_sel("p_prep", "出発できるまで", ["30分くらい", "1時間くらい", "2時間くらい", "3時間以上"]), "", "")}
  {PT_FARE_MORE}
  {pt_f("事業の許可・届出", pt_sel("p_lic", "事業の許可・届出", ["緑ナンバー（旅客の許可）", "黒ナンバー（貨物軽自動車の届出）", "両方", "どちらもない"]), "", "")}
  <div class="f"><span class="lbl">スタッフの資格</span>{pt_chk("p_quals", "スタッフの資格", PT_QUALS)}</div>
  <div class="f"><label for="p_reg">動物取扱業の登録番号</label><input type="text" id="p_reg" data-k="動物取扱業の登録番号" maxlength="100" autocomplete="off" placeholder="なければ「なし」" required></div>
  <div class="f"><label for="p_msg">ほかに伝えたいこと<span class="any">あれば</span></label><textarea id="p_msg" data-k="そのほか" rows="3" maxlength="1000"></textarea></div>
  <label class="agree"><input type="checkbox" id="p_agree" required><span><a href="/#privacy">個人情報の取り扱い</a>を確認し、同意します。提携の内容は<a href="/partner/terms/">提携規約</a>をご覧ください（同意のお手続きは、あらためてメールでご案内します）。</span></label>
  <p id="p_err" role="alert" style="display:none;color:#c0392b;font-size:.88rem"></p>
  <button class="btn" type="submit">申し込む{ARROW}</button>
  <p class="form-foot">内容を確認して、数日以内にメールでご連絡します。</p>
</form>
<div id="p_done" style="display:none;text-align:center"><h2 style="font-size:1.2rem">お申し込みを受け付けました</h2><p>内容を確認して、メールでご連絡します。ありがとうございます。</p></div>
</div>
</div></section>
</main>
<script>
{pt_js}
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
            + (f'<div class="emg-score" data-id="{e(x["id"])}"></div>' if x.get("review_query") else '') + taxi_link(x) + '</div>')
def taxi_link(x, label="この病院"):
    # [B] 「この病院までのペットタクシー」：所在地を行き先に入れてフォームへ（2026-11-08。情報ページからタクシーの検索へつなぐ）
    if not x.get("addr"): return ''
    from urllib.parse import quote as _q
    return f'<a class="emg-taxi" href="/?to={_q(x["addr"])}#form">{label}までのペットタクシーの料金をくらべる →</a>'
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
_top = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
_pn = re.search(r"var PREF_NAMES = (\[[^\]]*\]);", _top).group(1)
_pl = re.search(r"var PREF_LL = (\[\[.*?\]\]);", _top).group(1)
EMG_GUESS_JS = """if (!sel.value) (function(){
    var NAMES = """ + _pn + """, LL = """ + _pl + """;
    function at(lat, lng){ var best = -1, bd = Infinity; LL.forEach(function(p, i){ var dy = lat - p[0], dx = (lng - p[1]) * Math.cos((lat + p[0]) * Math.PI / 360), d = dx * dx + dy * dy; if (d < bd) { bd = d; best = i; } }); return best >= 0 && bd < 4 ? NAMES[best] : ""; }
    function use(v, how){
      if (!v || sel.value || ![].some.call(sel.options, function(o){ return o.value === v; })) return;
      sel.value = v; apply(); prefLinks(v);
      var g = document.getElementById("emgGuess"); g.textContent = how + "から、" + v + "を選んでいます。ちがうときは、上で選び直してください。"; g.hidden = false;
    }
    function byNet(){ fetch("https://get.geojs.io/v1/ip/geo.json").then(function(r){ return r.json(); }).then(function(d){ if (d && d.country_code === "JP") use(at(+d.latitude, +d.longitude), "通信の情報（おおよその地域）"); }).catch(function(){}); }
    if (navigator.permissions && navigator.geolocation) navigator.permissions.query({name: "geolocation"}).then(function(st){
      if (st.state !== "granted") return byNet();
      navigator.geolocation.getCurrentPosition(function(p){ use(at(p.coords.latitude, p.coords.longitude), "いまいる場所"); }, byNet, {maximumAge: 600000, timeout: 5000});
    }).catch(byNet); else byNet();
  })();"""
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
      <div class="f emg-pick"><label for="emgPrefAll">都道府県をえらぶ</label><select id="emgPrefAll">{emg_opts}</select><p class="emg-guess" id="emgGuess" hidden></p></div>
      <p class="emg-free">この一覧は無料の情報です。当サイトへのお申し込みやお支払いはありません。料金や受付は、それぞれの会社・病院に直接おたずねください。</p>
      <p class="emg-sum"><a href="/#emergency">現在地から近い病院を、車で行く時間と一緒にさがす</a></p>
      <h2 class="emg-h">夜間・救急の動物病院</h2>
      <p class="emg-sum">夜間の病院が見つからない県には、近くの県の病院を（県名）つきで載せています。</p>
      {emg_prefs_html}
      <h2 class="emg-h">緊急の搬送をしている会社</h2>
      <div id="emgTaxiAll">{''.join(emg_company(t) for t in EMG["taxis"])}</div>
      <p class="emg-none" id="emgTaxiNone" hidden>この都道府県で緊急の搬送をしている会社は、まだ載せていません。</p>
      {emg_tips}
      <p class="emg-note">当サイトとは別の会社・病院です（{e(EMG["checked"])}時点の情報）。受付時間や対応は変わることがあるので、行く前・頼む前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、お問い合わせからお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>急ぎでない移動は、ペットタクシーで</h2><p>通院や退院のお迎えなど、前もって決まっている移動は、ペットタクシーの会社をさがして、空き状況と料金を問い合わせられます。当日の依頼もできます。</p></div>
    <p><a class="btn" href="/#form">空き状況と料金を問い合わせる（無料）</a></p>
    <p><a href="/area/">都道府県からペットタクシーをさがす（全国）</a></p>
  </div>
</section>
</main>
<script>
(function(){{{prefkeep.FN}
  var sel = document.getElementById("emgPrefAll");
  function apply(){{
    var v = sel.value, n = 0;
    document.querySelectorAll(".emg-pref").forEach(function(s){{ s.hidden = !!v && s.dataset.pref !== v; }});
    document.querySelectorAll(".emg-region").forEach(function(h){{ h.hidden = !!v; }});
    document.querySelectorAll("#emgTaxiAll .emg-co").forEach(function(d){{ var ok = !v || d.dataset.prefs.split(" ").indexOf(v) >= 0; d.hidden = !ok; if (ok) n++; }});
    document.getElementById("emgTaxiNone").hidden = n > 0;
  }}
  prefKeep(sel, apply);  // 選んだ都道府県はほかのページでも保つ（tools/prefkeep.py）
  // はじめての人には、いる場所に近い県を最初から選んでおく（位置の利用がすでに許可されていれば端末の位置、なければ通信の情報からの大まかな地域。新しく許可は求めない。覚えはしない）。2026-11-08 飼い主目線のレビュー #7
  {EMG_GUESS_JS}
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
PREF_CITIES = {x[1]: x[3] for x in PREFS}
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
            v = sorted(_r100(_nat_ride(x["fare"], km)) for x in fs)  # お客さまに見せる概算は100円単位（AGENTS.md）
            mid = v[(len(v) - 1) // 2]
            rows += (f'<tr><th>{km}km</th><td>{mid:,}円</td><td>{v[0]:,}〜{v[-1]:,}円</td></tr>' if len(v) >= 3 else
                     f'<tr><th>{km}km</th><td colspan="2">' + "・".join(f"{x:,}円" for x in v) + '</td></tr>')
        head = '<tr><th>乗った距離</th><th>まんなかの会社</th><th>安い会社〜高い会社</th></tr>' if len(fs) >= 3 else '<tr><th>乗った距離</th><th colspan="2">各社の運賃</th></tr>'
        out += (f'<p>そのうち料金表をのせている{len(fs)}社の料金表で、乗った距離の運賃（片道）を計算すると次のとおりです。</p>'
                f'<div class="tbl"><table><thead>{head}</thead><tbody>{rows}</tbody></table></div>'
                '<p class="fare-flag"><b>確定料金ではありません。</b>お迎え料金・待ち時間・夜間や早朝の割増・高速代は入っていません。フォームにお迎えの場所と行き先を入れると、会社ごとにお迎え料金なども入れた目安が出ます。</p>')
    out += pref_company_table(pf, short, cs, PREF_CITIES.get(pf, ()))
    if pf in PREF_AIRPORT:
        out += f'<p>{e(PREF_AIRPORT[pf])}への送迎は、飛行機の預け入れの受付時間に合わせて、お迎えの時刻を決めておくことが大切です。<a href="/guide/airport-moving/">ペットと引っ越し・空港送迎</a>に、航空会社の決まりと準備をまとめています。</p>'
    out += '<p>同乗できる人数、ペットだけの送迎、ワクチン、キャンセル料、夜間の割増は会社ごとに違います。<a href="/guide/choose/">ペットタクシーの選び方（全国の会社のルールをくらべました）</a>もあわせてご覧ください。</p>'
    return out, len(cs)

# [B] SEO 11/10 Nori「大阪名古屋神奈川千葉とかペットの飼い主が多いところもね」：大阪・愛知は /area/ の型だけで地域の中身が薄く、
# 「ペットタクシー 大阪」（月1,300）で出ていなかった。対応エリアに書かれた市の数（公式サイトの文から数える）と、よく行く区間の料金の目安を足す。
# 道のりは地図の車のルートでの目安。料金は全国の会社の料金表から nat_text で計算（概算）。
PREF_LOCAL = {
  "大阪府": dict(
    why="大阪市の中心部は動物病院が多い一方、北摂（豊中・吹田・高槻・茨木）や南の堺・泉州から専門の病院へ通うと、10km以上の移動になることもあります。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。伊丹空港・関西国際空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["大阪市", "堺", "高槻", "茨木", "伊丹", "豊中", "吹田", "東大阪", "枚方"],
    routes=[("大阪駅（梅田）→ 伊丹空港", 16), ("天王寺 → 堺市（堺東）", 10), ("大阪駅（梅田）→ 関西国際空港", 50)],
    faq=[("大阪市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("大阪から関西国際空港まで、ペットタクシーはいくらですか？", "50km")]),
  "愛知県": dict(
    why="名古屋市の中から専門の動物病院へ通うときや、豊田・岡崎・豊橋など名古屋から離れた市からの移動は、20〜40kmになることもあります。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。中部国際空港（セントレア）への送迎や、お引っ越しの移動にも使われます。",
    stems=["名古屋", "豊橋", "豊田", "岡崎"],
    routes=[("名古屋駅 → 県営名古屋空港", 13), ("名古屋駅 → 豊田市", 35), ("名古屋駅 → 中部国際空港", 45)],
    faq=[("名古屋市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("名古屋から中部国際空港まで、ペットタクシーはいくらですか？", "45km")]),
  # [B] SEO 11/11：提携先のある北海道・福岡・広島と、関西の兵庫・京都にも同じ節を足す（Nori「提携が完了してるエリア」「飼い主が多いところ」）
  "北海道": dict(
    why="札幌市の中の通院のほか、江別・北広島・千歳など札幌のまわりの市から市内の専門の病院へ行くと、20km以上の移動になることもあります。冬は雪道で、ペットを連れて歩いたりバスを待ったりするのが大変な日もあります。新千歳空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["札幌", "小樽", "江別", "北広島", "千歳"],
    routes=[("札幌駅 → 江別市", 20), ("札幌駅 → 小樽駅", 40), ("札幌駅 → 新千歳空港", 50)],
    faq=[("札幌市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("札幌から新千歳空港まで、ペットタクシーはいくらですか？", "50km")]),
  "福岡県": dict(
    why="福岡市の中の通院のほか、春日・宗像・古賀など福岡市のまわりや、北九州・久留米から専門の病院へ通うと、長い移動になることもあります。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。福岡空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["福岡市", "北九州", "春日", "久留米", "宗像", "古賀", "福津"],
    routes=[("博多駅 → 福岡空港", 5), ("天神 → 春日市", 10), ("博多駅 → 小倉駅（北九州市）", 70)],
    faq=[("福岡市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("福岡市から北九州市まで、ペットタクシーはいくらですか？", "70km")]),
  "広島県": dict(
    why="広島市の中の通院のほか、呉など広島市から離れた市から専門の病院へ通うと、30km以上の移動になることもあります。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。広島空港への送迎や、県外へのお引っ越しの移動にも使われます。",
    stems=["広島市", "呉"],
    routes=[("広島駅 → 廿日市市", 20), ("広島駅 → 呉駅", 30), ("広島駅 → 広島空港", 50)],
    faq=[("広島市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("広島市から広島空港まで、ペットタクシーはいくらですか？", "50km")]),
  "兵庫県": dict(
    why="神戸市の中の通院のほか、西宮・芦屋・尼崎・宝塚から神戸や大阪の専門の病院へ通うときに使われます。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。神戸空港・伊丹空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["神戸", "芦屋", "伊丹", "西宮", "尼崎", "宝塚", "川西"],
    routes=[("三宮 → 神戸空港", 10), ("三宮 → 西宮市", 20), ("三宮 → 伊丹空港", 30)],
    faq=[("神戸市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("神戸から伊丹空港まで、ペットタクシーはいくらですか？", "30km")]),
  "京都府": dict(
    why="京都市の中の通院のほか、宇治・亀岡など京都市のまわりから専門の病院へ通うときに使われます。電車やバスにはキャリーに入る子しか乗れず、大型犬は乗れません。大阪の病院や伊丹空港への移動、お引っ越しにも使われます。",
    stems=["京都市", "宇治", "亀岡"],
    routes=[("京都駅 → 宇治市", 15), ("京都駅 → 大阪駅（梅田）", 45), ("京都駅 → 伊丹空港", 50)],
    faq=[("京都市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("京都から伊丹空港まで、ペットタクシーはいくらですか？", "50km")]),
  # [B] SEO 11/11 15時：料金表のある会社が多い滋賀・奈良・和歌山と、静岡・宮城にも同じ節を足す
  "滋賀県": dict(
    why="大津・草津・守山など県の南部から、京都や大阪の専門の動物病院へ通うときに使われます。滋賀県にお店のある会社は少なく、京都・大阪・奈良の会社が「近畿一円」として来てくれることが多いので、お迎えの場所をフォームに入れて確かめてください。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。",
    stems=["栗東", "守山", "草津"],
    routes=[("大津駅 → 京都駅", 10), ("草津駅 → 京都駅", 25), ("草津駅 → 大阪駅（梅田）", 65)],
    faq=[("滋賀から京都の動物病院まで、ペットタクシーはいくらですか？", "25km"), ("滋賀から大阪まで、ペットタクシーはいくらですか？", "65km")]),
  "奈良県": dict(
    why="奈良市・生駒・大和郡山の中の通院のほか、大阪の専門の動物病院へ通うときに使われます。奈良市にお店のある会社のほか、大阪の会社が「近畿一円」として来てくれることもあります。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。関西国際空港・伊丹空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["奈良市", "大和郡山", "生駒"],
    routes=[("奈良駅 → 生駒市", 15), ("奈良駅 → 大阪駅（梅田）", 35), ("奈良駅 → 関西国際空港", 75)],
    faq=[("奈良から大阪の動物病院まで、ペットタクシーはいくらですか？", "35km"), ("奈良から関西国際空港まで、ペットタクシーはいくらですか？", "75km")]),
  "和歌山県": dict(
    why="和歌山市の中の通院のほか、大阪の専門の動物病院へ通うときに使われます。和歌山県にお店のある会社は少なく、大阪の会社が「近畿一円」として来てくれることが多いので、お迎えの場所をフォームに入れて確かめてください。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。関西国際空港への送迎にも使われます。",
    stems=[],
    routes=[("和歌山駅 → 岩出市", 15), ("和歌山駅 → 関西国際空港", 40), ("和歌山駅 → 堺市", 60)],
    faq=[("和歌山から関西国際空港まで、ペットタクシーはいくらですか？", "40km"), ("和歌山から大阪の動物病院まで、ペットタクシーはいくらですか？", "60km")]),
  "静岡県": dict(
    why="静岡市や浜松市の中の通院のほか、東西に長い県なので、専門の動物病院まで遠い移動になることもあります。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。富士山静岡空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["静岡市", "浜松", "湖西"],
    routes=[("静岡駅 → 清水駅", 10), ("静岡駅 → 富士山静岡空港", 35), ("静岡駅 → 浜松駅", 75)],
    faq=[("静岡市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("静岡から富士山静岡空港まで、ペットタクシーはいくらですか？", "35km")]),
  "宮城県": dict(
    why="仙台市の中の通院のほか、名取・多賀城・塩竈・富谷など仙台のまわりの市から市内の専門の動物病院へ行くときに使われます。冬は雪や凍った道で、ペットを連れて歩いたりバスを待ったりするのが大変な日もあります。仙台空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["仙台", "名取", "利府", "多賀城", "塩竈", "富谷"],
    routes=[("仙台駅 → 名取市", 12), ("仙台駅 → 塩竈市", 17), ("仙台駅 → 仙台空港", 20)],
    faq=[("仙台市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("仙台から仙台空港まで、ペットタクシーはいくらですか？", "20km")]),
  # [B] SEO 11/11 17時：首都圏・名古屋に近い茨城・群馬・栃木・岐阜・三重にも同じ節を足す（来てくれる会社は県の外のお店が多い）
  "茨城県": dict(
    why="取手・守谷・牛久・つくば・古河など県の南部から、千葉・埼玉・東京の専門の動物病院へ通うときに使われます。茨城県にお店のある会社は少なく、千葉・埼玉の会社が県の南部まで来てくれることが多いので、お迎えの場所をフォームに入れて確かめてください。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。茨城空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["古河", "坂東", "牛久"],
    routes=[("牛久駅 → 柏駅", 25), ("水戸駅 → 茨城空港", 30), ("つくば駅 → 東京駅", 60)],
    faq=[("茨城の南部から千葉の動物病院まで、ペットタクシーはいくらですか？", "25km"), ("つくばから東京まで、ペットタクシーはいくらですか？", "60km")]),
  "群馬県": dict(
    why="前橋・高崎の中の通院のほか、館林など県の東部から埼玉の専門の動物病院へ通うときや、東京へのお引っ越しの移動に使われます。群馬県にお店のある会社は少なく、埼玉の会社が県の東部まで来てくれることがあるので、お迎えの場所をフォームに入れて確かめてください。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。",
    stems=["館林", "邑楽"],
    routes=[("前橋駅 → 高崎駅", 12), ("館林駅 → 春日部駅", 35), ("高崎駅 → 東京駅", 110)],
    faq=[("前橋から高崎の動物病院まで、ペットタクシーはいくらですか？", "12km"), ("群馬から東京まで、ペットタクシーはいくらですか？", "110km")]),
  "栃木県": dict(
    why="宇都宮の中の通院のほか、小山・野木など県の南部から埼玉の専門の動物病院へ通うときや、東京へのお引っ越しの移動に使われます。栃木県にお店のある会社は少なく、埼玉の会社が県の南部まで来てくれることがあるので、お迎えの場所をフォームに入れて確かめてください。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。",
    stems=["小山", "野木"],
    routes=[("宇都宮駅 → 小山駅", 30), ("小山駅 → 春日部駅", 40), ("宇都宮駅 → 東京駅", 110)],
    faq=[("宇都宮から小山まで、ペットタクシーはいくらですか？", "30km"), ("栃木から東京まで、ペットタクシーはいくらですか？", "110km")]),
  "岐阜県": dict(
    why="岐阜市・羽島・海津など県の南部から、名古屋の専門の動物病院へ通うときに使われます。愛知県にお店のある会社が岐阜県まで来てくれることが多いので、お迎えの場所をフォームに入れて確かめてください。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。中部国際空港（セントレア）への送迎や、お引っ越しの移動にも使われます。",
    stems=["海津", "羽島", "岐阜"],
    routes=[("岐阜駅 → 羽島市", 12), ("岐阜駅 → 名古屋駅", 35), ("岐阜駅 → 中部国際空港", 75)],
    faq=[("岐阜から名古屋の動物病院まで、ペットタクシーはいくらですか？", "35km"), ("岐阜から中部国際空港まで、ペットタクシーはいくらですか？", "75km")]),
  "三重県": dict(
    why="桑名・いなべ・四日市など県の北部から、名古屋の専門の動物病院へ通うときに使われます。愛知県にお店のある会社が県の北部まで来てくれることがあるので、お迎えの場所をフォームに入れて確かめてください。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。中部国際空港（セントレア）への送迎や、お引っ越しの移動にも使われます。",
    stems=["桑名", "いなべ", "四日市"],
    routes=[("桑名駅 → 名古屋駅", 25), ("四日市駅 → 名古屋駅", 40), ("四日市駅 → 中部国際空港", 60)],
    faq=[("桑名から名古屋の動物病院まで、ペットタクシーはいくらですか？", "25km"), ("四日市から名古屋まで、ペットタクシーはいくらですか？", "40km")]),
  # [B] SEO 11/11 21時：人の多い新潟・長野・岡山・熊本・沖縄にも同じ節を足す（県の中のお店はまだ見つかっていない）
  "新潟県": dict(
    why="新潟市の中の通院のほか、長岡・新発田など新潟市から離れた市から専門の動物病院へ通うと、30km以上の移動になることもあります。冬は雪道で、ペットを連れて歩いたりバスを待ったりするのが大変な日もあります。新潟空港への送迎や、お引っ越しの移動にも使われます。",
    stems=[],
    routes=[("新潟駅 → 新潟空港", 10), ("新潟駅 → 新発田駅", 28), ("新潟駅 → 長岡駅", 65)],
    faq=[("新潟市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("新潟から長岡まで、ペットタクシーはいくらですか？", "65km")]),
  "長野県": dict(
    why="長野市・松本市の中の通院のほか、山あいの町から専門の動物病院へ通うと、40km以上の移動になることもあります。冬は雪や凍った道で、運転に不安がある日もあります。信州まつもと空港への送迎や、お引っ越しの移動にも使われます。",
    stems=[],
    routes=[("松本駅 → 信州まつもと空港", 10), ("長野駅 → 上田駅", 40), ("長野駅 → 松本駅", 75)],
    faq=[("長野市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("長野から松本まで、ペットタクシーはいくらですか？", "75km")]),
  "岡山県": dict(
    why="岡山市・倉敷市の中の通院のほか、岡山と倉敷のあいだや、県の北の市から専門の動物病院へ通うときに使われます。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。岡山空港への送迎や、お引っ越しの移動にも使われます。",
    stems=[],
    routes=[("岡山駅 → 倉敷駅", 17), ("岡山駅 → 岡山空港", 20), ("岡山駅 → 福山駅（広島県）", 60)],
    faq=[("岡山市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("岡山から倉敷まで、ペットタクシーはいくらですか？", "17km")]),
  "熊本県": dict(
    why="熊本市の中の通院のほか、菊陽・合志・八代など熊本市のまわりから市内の専門の動物病院へ通うときに使われます。電車やバスにはキャリーに入る子しか乗れず、大型犬は乗れません。阿蘇くまもと空港への送迎や、お引っ越しの移動にも使われます。",
    stems=[],
    routes=[("熊本駅 → 菊陽町", 18), ("熊本駅 → 阿蘇くまもと空港", 25), ("熊本駅 → 八代駅", 45)],
    faq=[("熊本市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("熊本から阿蘇くまもと空港まで、ペットタクシーはいくらですか？", "25km")]),
  "沖縄県": dict(
    why="那覇市の中の通院のほか、沖縄市・うるま市や北部の名護から那覇の専門の動物病院へ通うときに使われます。モノレールやバスにはキャリーに入る子しか乗れず、大型犬は乗れません。那覇空港への送迎や、お引っ越しの移動にも使われます。",
    stems=[],
    routes=[("那覇空港 → 那覇市（県庁前）", 5), ("那覇市 → 沖縄市", 25), ("那覇市 → 名護市", 70)],
    faq=[("那覇空港から那覇市内まで、ペットタクシーはいくらですか？", "5km"), ("那覇から名護まで、ペットタクシーはいくらですか？", "70km")]),
  # [B] SEO 11/13：石川・香川・愛媛・長崎・鹿児島（県庁所在地のまわりと空港）
  "石川県": dict(
    why="金沢市の中の通院のほか、白山・野々市・小松など金沢のまわりの市から市内の専門の動物病院へ通うときに使われます。冬は雪の日も多く、ペットを連れて歩いたりバスを待ったりするのが大変な日もあります。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。小松空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["金沢", "白山", "野々市", "小松"],
    routes=[("金沢駅 → 白山市（松任）", 10), ("金沢駅 → 小松空港", 30), ("金沢駅 → 七尾市", 60)],
    faq=[("金沢市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("金沢から小松空港まで、ペットタクシーはいくらですか？", "30km")]),
  "香川県": dict(
    why="高松市の中の通院のほか、丸亀・坂出・観音寺など西の市から高松の専門の動物病院へ通うと、30km以上の移動になることもあります。電車にはキャリーに入る子しか乗れず、大型犬は乗れません。高松空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["高松", "丸亀", "坂出"],
    routes=[("高松駅 → 高松空港", 16), ("高松駅 → 丸亀市", 28), ("高松駅 → 観音寺市", 60)],
    faq=[("高松市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("高松駅から高松空港まで、ペットタクシーはいくらですか？", "16km")]),
  "愛媛県": dict(
    why="松山市の中の通院のほか、今治・新居浜・西条など東予の市から松山の専門の動物病院へ通うと、40km以上の移動になることもあります。電車や路面電車にはキャリーに入る子しか乗れず、大型犬は乗れません。松山空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["松山", "今治", "新居浜"],
    routes=[("松山駅 → 松山空港", 6), ("松山駅 → 今治市", 45), ("松山駅 → 新居浜市", 70)],
    faq=[("松山市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("松山から今治まで、ペットタクシーはいくらですか？", "45km")]),
  "長崎県": dict(
    why="長崎市は坂と階段の多い町で、ペットを抱えて歩くのが大変な場所もあります。長崎市の中の通院のほか、諫早や佐世保から専門の動物病院へ通うときに使われます。電車や路面電車にはキャリーに入る子しか乗れず、大型犬は乗れません。大村湾の上にある長崎空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["長崎市", "佐世保", "諫早", "大村"],
    routes=[("長崎駅 → 諫早市", 25), ("長崎駅 → 長崎空港", 40), ("長崎駅 → 佐世保市", 80)],
    faq=[("長崎市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("長崎市から長崎空港まで、ペットタクシーはいくらですか？", "40km")]),
  "鹿児島県": dict(
    why="鹿児島市の中の通院のほか、霧島・姶良・薩摩川内など鹿児島市のまわりの市から専門の動物病院へ通うと、長い移動になることもあります。夏は暑い日が続き、ペットを連れて歩いたりバスを待ったりするのが大変な日もあります。電車や路面電車にはキャリーに入る子しか乗れず、大型犬は乗れません。鹿児島空港への送迎や、お引っ越しの移動にも使われます。",
    stems=["鹿児島市", "霧島", "姶良", "薩摩川内"],
    routes=[("鹿児島中央駅 → 姶良市", 20), ("鹿児島中央駅 → 鹿児島空港", 35), ("鹿児島中央駅 → 薩摩川内市", 45)],
    faq=[("鹿児島市内の動物病院まで、ペットタクシーはいくらですか？", "5km"), ("鹿児島市から鹿児島空港まで、ペットタクシーはいくらですか？", "35km")]),
}
def _pref_text(key, km):
    fs = [c for c in _NAT if key in c.get("areas", [])]
    if len(fs) < 3: return nat_text(km), "全国"
    v = sorted(_r100(_nat_ride(c["fare"], km)) for c in fs)
    if v[0] == v[-1]: return f"{v[0]:,}円（{len(fs)}社とも同じ）", f"{len(fs)}社"
    return f"{v[(len(v) - 1) // 2]:,}円（{v[0]:,}〜{v[-1]:,}円）", f"{len(fs)}社"
def pref_local(pf, short, key):
    L = PREF_LOCAL.get(pf)
    if not L: return "", []
    n = _ncos(key)
    cs = [(st, _ccos(key, st)) for st in L["stems"]]
    cs = [(st, c) for st, c in cs if c]
    rows = "".join(f"<tr><td>{e(r)}</td><td>{km}km</td><td>{_pref_text(key, km)[0]}</td></tr>" for r, km in L["routes"])
    basis = _pref_text(key, 10)[1]
    basis = f"{pf}に来てくれる会社のうち料金表をのせている{basis}" if basis != "全国" else "全国の会社"
    html = (f'<h2>{e(short)}でペットタクシーを使うとき</h2><p>{e(L["why"])}</p>'
            + (f'<p>{e(pf)}のお迎えに対応している{n}社のうち、公式サイトの対応エリアに市の名前を書いている会社の数は、' + "・".join(f"「{e(st)}」{c}社" for st, c in cs) + "でした。名前を書いていない市にも来てくれることがあるので、お迎えの場所をフォームに入れて確かめてください。</p>" if cs else "")
            + f'<h3>よく行く区間の料金の目安（片道）</h3><table><thead><tr><th>区間</th><th>車の道のりの目安</th><th>料金の目安（まんなか・安い〜高い）</th></tr></thead><tbody>{rows}</tbody></table>'
            + f'<p class="small">{e(basis)}の公式サイトの料金表をもとに計算した乗った距離の運賃の概算で、確定料金ではありません。お迎え料金・夜間の割増は入っていません。当日の道順・渋滞・待ち時間などで変わり、高速道路を使うときはその料金が別にかかります。</p>')
    faq = []
    for q, k in L["faq"]:
        km = int(k[:-2])
        faq.append((q, f"{basis}の料金表で計算すると、{km}kmで片道{_pref_text(key, km)[0]}が目安です（各社の公式サイトの料金表をもとに計算した概算で、確定料金ではありません）。お迎えの料金や夜間の割増は会社ごとに違うので、フォームに場所と日時を入れると、来てもらえる会社ごとの目安が出ます。"))
    return html, faq

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
    _k = pf if pf == "北海道" else pf[:-1]
    # [B] SEO 11/8：愛知 12表示・0クリック。3社以上の県は数・24時間・当日を先に出す（数えた数だけ）。
    _t24, _tsd = _n24(_k), _nsame(_k)
    _tx = "・".join(x for x in [f"24時間受付{_t24}社" if _t24 else "", f"当日も受ける{_tsd}社" if _tsd else ""] if x)
    _ol = OPEN_LOCAL.get(pf)
    # [B] SEO 11/12：題名は多くの人に関係すること（通院・空港までの料金）を出す。夜間は使う人が限られるので題名に出さない（Nori「夜間割とかあんまり響かない」）
    _air = any("空港" in r for r, _ in PREF_LOCAL.get(pf, {}).get("routes", []))
    _use = "通院・空港までの料金の目安" if _air else "通院の料金の目安"
    title = (f"{short}のペットタクシー｜{PAIN_T}。{'・'.join(l for _, l in _ol)}の会社に空き状況と料金を無料で問い合わせ" if _ol else
             f"{short}のペットタクシー｜{PAIN_T}。料金の目安を無料でしらべる") + "｜ペットタクシー予約窓口"
    dcities = []  # 説明文用：その県の中の病院の市（政令市の区はまとめる）
    for h in hs:
        if other_pref(h, pf): continue
        c = re.sub(r"^(.+?市).+区$", r"\1", re.sub(r"（.*?）", "", h["city"]))
        if c not in dcities: dcities.append(c)
    desc = pain_desc(f"{pf}（{'・'.join(cities[:3])}など）")
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
      <p>上のフォームにお迎えの場所と行き先を入れると、来てもらえる会社と料金の目安が出ます。無料で使えて、当日の依頼もできます。会社から空き状況と料金の返事が届いたら、納得してから予約を確定できます。</p>
      <a class="btn center" href="#form">空き状況と料金を問い合わせる（無料）{ARROW}</a>
    </div>'''
    # 県ごとのよくある質問（数は display_companies.json・emergency.json から毎回数える。会社名・病院名は出さない）
    _key = pf if pf == "北海道" else pf[:-1]
    _hin = [h for h in hs if not other_pref(h, pf)]
    local_html, local_faq = pref_local(pf, short, _key)
    local_html += city_links(pf)
    pfaq = list(local_faq)
    if n_cos:
        _ns = _nsame(_key)
        pfaq.append((f"{short}に来てくれるペットタクシーは何社ありますか？",
            f"当サイトで公式サイトを確かめた全国の会社のうち、対応エリアに{pf}を書いている会社は{n_cos}社でした（{FARES_CHECKED}時点）。地名を書いていない場所に来てくれることもあるので、お迎えの場所をフォームに入れて確かめてください。"))
        _bf = big_faq(short, pf, _key)
        if _bf: pfaq.append(_bf)
        pfaq.append((f"{short}で当日でもペットタクシーを頼めますか？",
            (f"{n_cos}社のうち、公式サイトや会社からの返事に当日も受けると書いてある会社は{_ns}社です。お迎えが今日のときは、この中から空いていて間に合う会社だけが候補に出ます。" if _ns else
             f"{n_cos}社の中に、公式サイトや会社からの返事に当日も受けるとはっきり書いてある会社はまだありません。お迎えが今日だと候補が出ないことがあるので、明日以降の日時でさがすのがおすすめです。")
            + "会社にメールで確認してから決まるしくみなので、お迎えの時刻は、いまから3時間以上あとで選んでください。"))
    if _hin:
        pfaq.append((f"{short}で夜間に診てもらえる動物病院はありますか？",
            f"{pf}の夜間・救急の動物病院を{len(_hin)}件載せています（{'・'.join(hcities[:3])}など）。受付時間は病院ごとに違うので、行く前に電話で受け入れてもらえるか確かめてください。"))
    elif hs:
        pfaq.append((f"{short}で夜間に診てもらえる動物病院はありますか？",
            f"{pf}の中で夜間に診てもらえる病院は見つからなかったため、近くの県の夜間・救急の動物病院を{len(hs)}件載せています。行く前に電話で受け入れてもらえるか確かめてください。"))
    pfaq.append((f"{short}でペットの緊急搬送を頼める会社はありますか？",
        (f"{pf}で緊急の搬送をしていると公式サイトに書いている会社を{len(taxis)}社載せています。急ぐときは、まず動物病院に電話して受け入れを確かめてから頼んでください。" if taxis else
         f"{pf}で緊急の搬送をしている会社は、まだ載せていません。急ぐときは、まず動物病院に電話して、受け入れと行き方をご相談ください。")))
    pfaq_html = (f'<h2>{e(short)}のペットタクシー よくある質問</h2><div class="faq-list">' +
        ''.join(f'<details><summary>{e(q)}</summary><div class="a">{e(a_)}</div></details>' for q, a_ in pfaq) + '</div>')
    ld += '\n<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
      {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a_}} for q, a_ in pfaq]}, ensure_ascii=False, indent=1) + '\n</script>'
    checks = ''.join(f'<h3>{e(h)}</h3><p>{e(t)} <a href="/guide/{g}/">{e(GBY[g]["title"])}</a></p>' for h, t, g in PREF_CHECKS)
    area_html = f'''<!-- 地域の説明（gen_areas.py の PREFS） -->
<section id="area-info" style="padding-top:8px">
  <div class="wrap"><article class="art">
    <p class="fare-flag"><b>{e(pf)}からのお迎えも、上のフォームでさがせます。</b>{NOT_YET}会社ごとに対応する地域が違うので、近くに会社が見つからないこともあります。</p>
    <p class="small">ペットタクシー予約窓口　更新 {TODAY.replace("-", ".")}</p>
    <h2>{e(short)}のペットタクシーの料金{"の例" if has_fare else ""}</h2>
    {pref_fare_html(pf)}
    {local_html}
    <p><a href="/guide/what-is-pet-taxi/">ペットタクシーとは？電車・タクシー・マイカーとの違い</a>では、料金のしくみをくわしく説明しています。キャリーに入る小さな子なら、<a href="/guide/taxi-with-pet/">ふつうのタクシーに乗れることもあります</a>。</p>

    {data_html}

    <h2>ペットタクシーを頼む前に確かめること</h2>
    {checks}

    <h2>{e(pf)}の夜間・救急の動物病院と、緊急の搬送</h2>
    <p>一刻を争う症状のときは、まずかかりつけや夜間・救急の動物病院に電話して、受け入れてもらえるか確かめてください。{hosp_lead}</p>
    <p>受付時間つきの一覧は<a href="/hospital/night/#pref={quote(pf)}">{e(pf)}の夜間・救急の動物病院</a>に、家まで来てくれる獣医さんは<a href="/hospital/visit/#pref={quote(pf)}">往診専門の動物病院</a>にまとめています。</p>
    {gen_dogrun.area_snippet(pf, e)}
    {gen_prefpages.area_snippet(pf, e, [gen_prefcats.NIGHT, gen_prefcats.SOUGI, gen_rojin.CAT, gen_trainers.CAT, gen_sitters.CAT, gen_grooming.CAT, gen_hotels.CAT])}
    <div class="emg">
      <h3 class="emg-h">夜間・救急の動物病院</h3>
      {pref_hosp_html(pf)}
      <h3 class="emg-h">緊急の搬送をしている会社</h3>
      {taxi_html}
      <p class="emg-note">当サイトとは別の会社・病院です（{e(EMG["checked"])}時点の情報）。受付時間や対応は変わることがあるので、行く前・頼む前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、お問い合わせからお知らせください。口コミはページ上の「緊急」タブで見られます。</p>
    </div>
    <p><a href="/emergency/">全国の緊急の連絡先の一覧</a>から、現在地から近い病院も探せます。</p>
    {pfaq_html}
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
    if _ol: desc = desc.replace("料金の目安を、お迎えの場所を入れて無料でしらべられます。", "料金の目安がわかり、" + "・".join(n for n, _ in _ol) + "には空き状況と料金を無料で問い合わせできます。")
    lede = open_lead(pf) + f"{pf}（{'・'.join(cities[:4])}など）で、犬や猫の移動の手段を探している方へ。フォームに入力すると、条件に合う事業者と料金の目安が見られます。急ぐときの連絡先は「緊急」タブにまとめています。"
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
# [B] 2026-11-03「中身の薄いページを充実させる」：都道府県ごとの数の表（会社の数・10kmの運賃・夜間の病院・搬送の会社）。うちのデータで数えたもの、社名なし。
def _hub_table():
    trs, found, many = "", 0, 0
    for lab, ps in emg_regions:
        trs += f'<tr><th colspan="5" style="text-align:left">{e(lab)}</th></tr>'
        for p in ps:
            key = p if p == "北海道" else p[:-1]
            cs = [x for x in _DISP if key in x.get("areas", [])]
            fs = sorted(_nat_ride(x["fare"], 10) for x in cs if x.get("fare") and x["fare"].get("kind", "dist") == "dist" and x["fare"].get("base"))
            found += bool(cs); many += len(cs) >= 5
            hs = [h for h in EMG["hospitals"].get(p, []) if not other_pref(h, p)]
            tx = [t for t in EMG["taxis"] if p in t.get("prefs", [])]
            nm = AREA_SHORT.get(p) or next(x[2] for x in PREFS if x[1] == p)
            r1 = lambda y: f"{int(round(y / 100.0)) * 100:,}円"  # お客さまに見せる概算は100円単位
            mid = r1(fs[(len(fs) - 1) // 2]) if len(fs) >= 3 else ("、".join(r1(v) for v in fs) if fs else "—")
            trs += (f'<tr><td><a href="{pref_href(p)}">{e(nm)}</a></td><td>{len(cs) or "—"}</td><td>{mid}</td>'
                    f'<td><a href="/hospital/night/{gen_dogrun.PSLUG[p]}/">{len(hs)}</a></td><td>{len(tx) or "—"}</td></tr>')
    return (f'<div class="sh" style="margin-top:28px"><h2>都道府県ごとの数</h2></div>'
            f'<p>当サイトで公式サイトを確かめた全国{len(_DISP)}社のペットタクシーのうち、お迎えの対応エリアに書いている都道府県を数えると、会社が見つかったのは47都道府県のうち{found}、5社以上あるのは{many}でした。'
            '会社が見つからない県でも、となりの県の会社が来てくれることがあります。10kmの運賃は料金表をのせている会社で計算した片道の金額（100円単位にまるめています）で、3社以上あるときはまんなかの会社の金額です。確定料金ではありません。距離ごとの運賃やお迎え料金・夜間割増の数は<a href="/guide/pet-taxi-fare-survey/">全国のペットタクシー料金しらべ</a>にまとめています。</p>'
            '<div class="tbl"><table><thead><tr><th>都道府県</th><th>ペットタクシー会社</th><th>10kmの運賃</th><th>夜間・救急の病院（県の中）</th><th>緊急の搬送の会社</th></tr></thead>'
            f'<tbody>{trs}</tbody></table></div>'
            f'<p class="fare-flag"><b>確定料金ではありません。</b>{FARES_CHECKED}時点で各社の公式サイトの料金表をもとに計算した概算です。お迎え料金・待ち時間・夜間や早朝の割増・高速代は入っていません。当日の道順・渋滞・待ち時間などで変わります。</p>')
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
  <div class="wrap">{hub_regions}{_hub_table()}</div>
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
REVIEW_ON_CLICK = re.search(r'var REVIEW_ON_CLICK = (true|false);', top_src).group(1) == "true"  # 口コミを押したときだけ取り寄せるか（index.html の値に合わせる）
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
    fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){ fill(panel, j); })
      .catch(function(){ panel.textContent = "口コミを読み込めませんでした。時間をおいてもう一度お試しください。"; });
  }
  // 取り寄せた口コミを枠に入れる（書いた人・元の口コミへのリンク・並び順の説明・出どころは規約で必要）
  function fill(panel, j){
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
  }
  // 押したときだけ取り寄せる形（REVIEW_ON_CLICK）：最初は「口コミを見る」だけを出し、押したら星と本文をまとめて取り寄せる
  function lazy(box){
    var id = box.dataset.id, b = el("button", "partner-review-open", "口コミを見る"), p = el("p", "partner-score"); b.type = "button";
    p.append(b, el("span", "partner-review-src", "Google Maps")); box.replaceChildren(p);
    b.addEventListener("click", function(){
      b.disabled = true; b.textContent = "口コミを読み込んでいます…";
      if (window.gtag) gtag("event", "open_reviews", {});
      var body = new URLSearchParams(); body.set("kind", "reviews"); body.set("partner_id", id);
      fetch(GAS_URL, {method: "POST", body: body}).then(function(r){ return r.json(); }).then(function(j){
        if (j && j.ok && !(j.rating > 0)) throw "none"; // Googleマップに口コミがまだない（上限や不具合とは別）
        if (!j || !j.ok) throw 0;
        memo[id] = {rating: j.rating, count: j.count}; paint(box, memo[id]);
        var panel = box.querySelector(".review-panel"), open = box.querySelector(".partner-review-open");
        fill(panel, j); panel.hidden = false; open.setAttribute("aria-expanded", "true");
      }).catch(function(e){ box.replaceChildren(el("p", "partner-review-src", e === "none" ? "Googleマップの口コミはまだありません" : "口コミを読み込めませんでした。時間をおいてもう一度お試しください")); });
    });
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
  if (%s) { boxes.forEach(lazy); return; } // REVIEW_ON_CLICK（index.html と同じ値）
  if (!("IntersectionObserver" in window)) { boxes.forEach(want); return; }
  // 口コミの欄は空のあいだ見えないので、会社の枠が画面に入ったら取り寄せる（しぼりこみで隠れている会社は取り寄せない）
  var io = new IntersectionObserver(function(es){ es.forEach(function(x){ if (x.isIntersecting && x.target.offsetParent) { io.unobserve(x.target); want(x.target.querySelector(".emg-score")); } }); }, {rootMargin: "200px"});
  boxes.forEach(function(b){ io.observe(b.parentElement); });
})();
""" % (json.dumps(GAS), "true" if REVIEW_ON_CLICK else "false"))

# 条件でさがす動物病院（/hospital/）：お金を取らない情報ページ（tools/gen_hospitals.py）
gen_hospitals.write_all(ROOT, dict(head=head, e=e, SITE=SITE, EMG=EMG, emg_regions=emg_regions, emg_opts=emg_opts, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = gen_hospitals.urls(SITE)
_pp_ctx0 = dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False)))
# ペットの迷子・犬の登録・引取りの窓口（/jichitai/）：お金を取らない情報ページ（tools/gen_jichitai.py）
import gen_jichitai
gen_jichitai.write_all(ROOT, dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, emg_opts=emg_opts, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = hosp_urls + gen_jichitai.urls(SITE)
# 全国のドッグラン（/dogrun/ と /dogrun/<県>/ と記事）：お金を取らない情報ページ（tools/gen_dogrun.py、データ tools/dogrun.json）
gen_dogrun.write_all(ROOT, dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, emg_opts=emg_opts, area_links=area_links, pref_href=pref_href,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = hosp_urls + gen_dogrun.urls(SITE)
# [B] SEO：ドッグランの施設ごとのページ（試しの30施設。tools/gen_dogrun_fac.py、型は docs/facility-page.md）
import gen_dogrun_fac
gen_dogrun_fac.write_all(ROOT, dict(head=head, e=e, SITE=SITE, foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = hosp_urls + gen_dogrun_fac.urls(SITE)
# ペットが亡くなったら（/sougi/）：お金を取らない情報ページ（tools/gen_sougi.py、データ tools/sougi.json）
import gen_sougi
gen_sougi.write_all(ROOT, dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, emg_opts=emg_opts, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = hosp_urls + gen_sougi.urls(SITE)
# [B] SEO：ペット火葬・霊園と夜間・救急の動物病院の都道府県ごとのページ（tools/gen_prefcats.py、検索がとくに多いため）
import gen_prefcats
for _cat in (gen_prefcats.SOUGI, gen_prefcats.NIGHT):
    gen_prefpages.write_all(ROOT, _pp_ctx0, _cat); gen_prefpages.link_national(ROOT, _pp_ctx0, _cat)
    hosp_urls = hosp_urls + gen_prefpages.urls(SITE, _cat)
# [B] SEO：ペット火葬場・霊園の施設ごとのページ（試しの30施設。tools/gen_sougi_fac.py）
import gen_sougi_fac
gen_sougi_fac.write_all(ROOT, _pp_ctx0)
hosp_urls = hosp_urls + gen_sougi_fac.urls(SITE)
# [B] SEO：夜間・救急の動物病院と犬と泊まれる宿の施設ごとのページ（試しの30ずつ。tools/gen_facpages.py）
import gen_facpages
gen_facpages.write_all(ROOT, _pp_ctx0)
hosp_urls = hosp_urls + gen_facpages.urls(SITE)
# 全国の老犬ホーム・老猫ホーム（/rojin-home/）：お金を取らない情報ページ（tools/gen_rojin.py、データ tools/rojin.json）
gen_rojin.write_all(ROOT, dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, emg_opts=emg_opts, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = hosp_urls + gen_rojin.urls(SITE)
_pp_ctx = dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False)))
gen_prefpages.write_all(ROOT, _pp_ctx, gen_rojin.CAT); gen_prefpages.link_national(ROOT, _pp_ctx, gen_rojin.CAT)
hosp_urls = hosp_urls + gen_prefpages.urls(SITE, gen_rojin.CAT)
# 全国のドッグトレーナー・犬のしつけ教室（/dog-trainer/）：お金を取らない情報ページ（tools/gen_trainers.py、データ tools/trainers.json）
gen_trainers.write_all(ROOT, dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, emg_opts=emg_opts, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = hosp_urls + gen_trainers.urls(SITE)
_pp_ctx = dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False)))
gen_prefpages.write_all(ROOT, _pp_ctx, gen_trainers.CAT); gen_prefpages.link_national(ROOT, _pp_ctx, gen_trainers.CAT)
hosp_urls = hosp_urls + gen_prefpages.urls(SITE, gen_trainers.CAT)
# 全国のペットシッター（/pet-sitter/）：お金を取らない情報ページ（tools/gen_sitters.py、データ tools/sitters.json。口コミの星なし）
import gen_sitters
gen_sitters.write_all(ROOT, dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, emg_opts=emg_opts, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = hosp_urls + gen_sitters.urls(SITE)
_pp_ctx = dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False)))
gen_prefpages.write_all(ROOT, _pp_ctx, gen_sitters.CAT); gen_prefpages.link_national(ROOT, _pp_ctx, gen_sitters.CAT)
hosp_urls = hosp_urls + gen_prefpages.urls(SITE, gen_sitters.CAT)
# 全国の出張トリミング・訪問トリミング（/trimming/）：お金を取らない情報ページ（tools/gen_grooming.py、データ tools/grooming.json。条件でしぼりこめる）
import gen_grooming
import gen_prefcats
gen_grooming.write_all(ROOT, dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, emg_opts=emg_opts, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = hosp_urls + gen_grooming.urls(SITE)
_pp_ctx = dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False)))
gen_prefpages.write_all(ROOT, _pp_ctx, gen_grooming.CAT); gen_prefpages.link_national(ROOT, _pp_ctx, gen_grooming.CAT)
hosp_urls = hosp_urls + gen_prefpages.urls(SITE, gen_grooming.CAT)
# [B] 大型犬OK・猫専用のペットホテル（/pet-hotel/、tools/gen_hotels.py、データ tools/hotels.json）
gen_hotels.write_all(ROOT, dict(head=head, e=e, SITE=SITE, emg_regions=emg_regions, emg_opts=emg_opts, area_links=area_links,
  foot_noband=lambda: re.sub(r'<div class="sticky">.*?</div>\n', "", foot("/#form", band=False))))
hosp_urls = hosp_urls + gen_hotels.urls(SITE)
gen_prefpages.write_all(ROOT, _pp_ctx, gen_hotels.CAT); gen_prefpages.link_national(ROOT, _pp_ctx, gen_hotels.CAT)
hosp_urls = hosp_urls + gen_prefpages.urls(SITE, gen_hotels.CAT)

# [B] SEO 11/13：市のページ（CITIES）。トップのフォームをそのまま写し、市の説明をフォームの後ろに入れる
from prefs import FARES_CHECKED as _FC
for c in CITIES:
    url = SITE + c["path"]
    k, pf, city = c["key"], c["pref"], c["city"]
    n = _ncos(k)
    cnt = [(st, _ccos(k, st)) for st in c["stems"]]
    named = sum(x for _, x in cnt)
    rows = "".join(f"<tr><td>{e(r)}</td><td>{km}km</td><td>{_pref_text(k, km)[0]}</td></tr>" for r, km in c["routes"])
    basis = _pref_text(k, 10)[1]
    basis = f"{pf}に来てくれる会社のうち料金表をのせている{basis}" if basis != "全国" else "全国の会社"
    faq = []
    if n:
        faq.append((f"{city}に来てくれるペットタクシーは何社ありますか？",
            f"当サイトで公式サイトを確かめた会社のうち、{pf}のお迎えに対応している会社は{n}社で、そのうち対応エリアに「{c['stems'][0]}」と市の名前を書いている会社は{named}社でした（{_FC}時点）。名前を書いていない会社も来てくれることがあるので、お迎えの場所をフォームに入れて確かめてください。"))
    for r, km in c["routes"][:2]:
        faq.append((f"{r.split('（')[0]}まで、ペットタクシーはいくらですか？",
            f"{basis}の料金表で計算すると、道のり{km}kmで片道{_pref_text(k, km)[0]}が目安です（各社の公式サイトの料金表をもとに計算した概算で、確定料金ではありません）。お迎えの料金や夜間の割増は会社ごとに違い、当日の道順・渋滞・待ち時間などでも変わります。フォームに場所と日時を入れると、来てもらえる会社ごとの目安が出ます。"))
    _bf = big_faq(city, pf, k)
    if _bf: faq.append(_bf)
    title = f"{city}のペットタクシー｜{PAIN_T}。料金の目安を無料でしらべる｜ペットタクシー予約窓口"
    desc = pain_desc(f"{city}（{c['wards']}）")
    ld = [
      {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":c["parent"][1]+"のペットタクシー","item":SITE+c["parent"][0]},
        {"@type":"ListItem","position":3,"name":city+"のペットタクシー","item":url}]},
      {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a_}} for q, a_ in faq]},
    ]
    ld_html = "\n".join('<script type="application/ld+json">\n' + json.dumps(x, ensure_ascii=False, indent=1) + '\n</script>' for x in ld)
    others = [x for x in CITIES if x["pref"] == pf and x is not c]
    area_html = f'''<!-- 市の説明（gen_areas.py の CITIES） -->
<section id="area-info" style="padding-top:8px">
  <div class="wrap"><article class="art">
    <p class="fare-flag"><b>{e(city)}からのお迎えも、上のフォームでさがせます。</b>{NOT_YET}会社ごとに対応する地域が違うので、お迎えの場所を入れて確かめてください。</p>
    <p class="small">ペットタクシー予約窓口　更新 {TODAY.replace("-", ".")}</p>
    <h2>{e(city)}でペットタクシーを使うとき</h2>
    <p>{e(c["why"])}</p>
    {(f'<p>{e(pf)}のお迎えに対応している{n}社のうち、公式サイトの対応エリアに「{e(c["stems"][0])}」と書いている会社は{named}社でした（{_FC}時点）。名前を書いていない市にも来てくれることがあるので、お迎えの場所をフォームに入れて確かめてください。</p>' if n else '')}
    <h3>{e(city)}からよく行く区間の料金の目安（片道）</h3>
    <table><thead><tr><th>区間</th><th>車の道のりの目安</th><th>料金の目安（まんなか・安い〜高い）</th></tr></thead><tbody>{rows}</tbody></table>
    <p class="small">{e(basis)}の公式サイトの料金表をもとに計算した、乗った距離の運賃の概算で、確定料金ではありません。お迎え料金・夜間の割増は入っていません。当日の道順・渋滞・待ち時間などで変わり、高速道路を使うときは高速代が別にかかります。</p>
    <h3>{e(city)}から行く人が多い病院・施設への行き方</h3>
    {guide_cards([g for g in c["guides"] if g in GBY])}
    <h3>{e(city)}のペットタクシー よくある質問</h3>
    <div class="faq-list">{"".join(f'<details><summary>{e(q)}</summary><div class="a">{e(a_)}</div></details>' for q, a_ in faq)}</div>
    <h3>まわりのページ</h3>
    <ul><li><a href="{c["parent"][0]}">{e(c["parent"][1])}のペットタクシー（県全体の料金・会社の数・夜間の動物病院）</a></li>{"".join(f'<li><a href="{x["path"]}">{e(x["city"])}のペットタクシー</a></li>' for x in others)}<li><a href="/hospital/night/#pref={quote(pf)}">{e(pf)}の夜間・救急の動物病院</a></li><li><a href="/guide/large-dog/">{e(GBY["large-dog"]["title"])}</a></li></ul>
  </article></div>
</section>'''
    page = clone_top(title, desc, url, ld_html, f"{city}のペットタクシー", f"{city}の動物病院への通院から、お引っ越し、空港への送迎まで。フォームにお迎えの場所を入れると、来てもらえる会社と料金の目安が出ます。無料で使えて、当日の依頼もできます。", pf, area_html,
                     f'<a href="/">ペットタクシー予約窓口</a> › <a href="{c["parent"][0]}">{e(c["parent"][1])}のペットタクシー</a> › {e(city)}')
    os.makedirs(os.path.join(ROOT, c["path"].strip("/")), exist_ok=True)
    open(os.path.join(ROOT, c["path"].strip("/"), "index.html"), "w", encoding="utf-8").write(page)
# sitemap / robots / 404
urls = [SITE + "/"] + [f'{SITE}/{a["slug"]}/' for a in AREAS] + [hub_url] + [f'{SITE}/guide/{g["slug"]}/' for g in GUIDES] + [emg_url] + hosp_urls + [pref_hub_url] + [f'{SITE}/area/{x[0]}/' for x in PREFS] + [terms_url, contact_url, partner_url, pterms_url]
urls += [SITE + c["path"] for c in CITIES]
# [B] 検索に出さないページ（tools/noindex.json。Nori 2026-11-13「全部やって」）。サイトマップから外し、最後に noindex,follow を入れる。
NOINDEX = json.load(open(os.path.join(ROOT, "tools", "noindex.json"), encoding="utf-8"))["pages"]
def _keep(u): return u[len(SITE):] not in NOINDEX
urls = [u for u in urls if _keep(u)]
guide_modified = {f'{SITE}/guide/{g["slug"]}/': g.get("modified", TODAY) for g in GUIDES}
# [B] sitemap の lastmod は、ページの本文（<main> の中、script を除く）が変わった日にする（2026-11-08 AI検索・検索の集客）。
# 前は記事以外が全部 TODAY（2026-10-30）のままで、検索エンジンやAI検索に「更新されていない」と伝わっていた。
# tools/lastmod.json に URL ごとの本文のハッシュと日付を覚え、本文が変わったときだけ日付を今日（日本時間）にする。
# ヘッダー・フッターなどサイト全体の小さな直しでは日付を動かさない。記事は記事の更新日（dateModified と同じ）を使う。
import hashlib, datetime
_lm_path = os.path.join(ROOT, "tools", "lastmod.json")
_lm = json.load(open(_lm_path, encoding="utf-8")) if os.path.exists(_lm_path) else {}
_today_jst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")
def _body_hash(u):
  f = os.path.join(ROOT, u[len(SITE) + 1:], "index.html")
  if not os.path.exists(f): return None
  t = open(f, encoding="utf-8").read()
  m = re.search(r"<main.*?</main>", t, re.S)
  t = re.sub(r"<script.*?</script>", "", m.group(0) if m else t, flags=re.S)
  return hashlib.sha1(t.encode("utf-8")).hexdigest()[:16]
_lm_new = {}
for u in urls:
  h = _body_hash(u); old_h, old_d = (_lm.get(u) or [None, None])
  _lm_new[u] = [h, old_d if (old_h == h and old_d) else _today_jst]
# 1行に1ページ（ほかのPRとぶつかったら、どちらかを取ってから gen_areas.py を実行し直せばそろう）
open(_lm_path, "w", encoding="utf-8").write("{\n" + ",\n".join(json.dumps(u) + ": " + json.dumps(_lm_new[u]) for u in sorted(_lm_new)) + "\n}\n")
def _lastmod(u):
  return guide_modified.get(u) or _lm_new[u][1]
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  "".join(f'  <url><loc>{u}</loc><lastmod>{_lastmod(u)}</lastmod></url>\n' for u in urls) + '</urlset>\n')
# [B] 分野ごとのサイトマップ（2026-11-09 戦略担当「サイトマップを分野ごとに分けて」）。sitemap.xml（全部）はそのまま残し、
# 同じURLを分野ごとの /sitemaps/<分野>.xml にも入れて、/sitemap_index.xml でまとめる。Search Console でサイトマップごとの
# 登録数が出るので、分野ごとの登録率（品質の関門）を数えられる。分野はURLの最初のフォルダで決める（ペットタクシーの地域・トップ・規約などは taxi）。
SITEMAP_CATS = {"guide": "guide", "sougi": "sougi", "dogrun": "dogrun", "hospital": "hospital", "pet-hotel": "pet-hotel",
                "pet-sitter": "pet-sitter", "dog-trainer": "dog-trainer", "rojin-home": "rojin-home", "trimming": "trimming", "jichitai": "jichitai"}
def _sm_cat(u):
  return SITEMAP_CATS.get(u[len(SITE) + 1:].split("/")[0], "taxi")
_sm_groups = {}
for u in urls: _sm_groups.setdefault(_sm_cat(u), []).append(u)
# 施設ごとのページ（試し）は、分野のサイトマップとは別にも出す（試しの登録率を見るため。docs/facility-page.md）
import gen_sougi_fac, gen_dogrun_fac
_sm_groups["facility-sougi"] = [u for u in gen_sougi_fac.urls(SITE) if _keep(u)]
_sm_groups["facility-dogrun"] = [u for u in gen_dogrun_fac.urls(SITE) if _keep(u)]
os.makedirs(os.path.join(ROOT, "sitemaps"), exist_ok=True)
for _c in os.listdir(os.path.join(ROOT, "sitemaps")):
  if _c.endswith(".xml") and _c[:-4] not in _sm_groups: os.remove(os.path.join(ROOT, "sitemaps", _c))
for _c, _us in _sm_groups.items():
  open(os.path.join(ROOT, "sitemaps", _c + ".xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f'  <url><loc>{u}</loc><lastmod>{_lastmod(u)}</lastmod></url>\n' for u in _us) + '</urlset>\n')
open(os.path.join(ROOT, "sitemap_index.xml"), "w", encoding="utf-8").write(
  '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  "".join(f'  <sitemap><loc>{SITE}/sitemaps/{_c}.xml</loc><lastmod>{max(_lastmod(u) for u in _sm_groups[_c])}</lastmod></sitemap>\n' for _c in sorted(_sm_groups)) + '</sitemapindex>\n')
open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\nDisallow: /tools/\nDisallow: /booking/\nDisallow: /docs/\n\nSitemap: {SITE}/sitemap.xml\nSitemap: {SITE}/sitemap_index.xml\n")
nf = head("ページが見つかりません｜ペットタクシー予約窓口", "お探しのページは見つかりませんでした。", SITE + "/404.html", '<meta name="robots" content="noindex">') + f'''
<main><section class="area-hero"><div class="wrap" style="text-align:center">
<h1>ページが見つかりませんでした</h1><p class="lede">URLが変わったか、削除された可能性があります。</p>
<a class="btn center" href="/">トップページへ{ARROW}</a></div></section>
<section><div class="wrap"><div class="sh"><h2>エリアからさがす</h2></div>{area_links()}</div></section></main>
''' + foot("/#form")
open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(nf)
# [B] 2026-11-04 同じ県のほかのカテゴリへのリンク（tools/crosslink.py）
import crosslink
_xl_prefs = [(a["slug"], {"tokyo": "東京都", "kanagawa": "神奈川県", "saitama": "埼玉県", "chiba": "千葉県"}[a["slug"]]) for a in AREAS] + [(x[0], x[1]) for x in PREFS]
print("crosslink", crosslink.build(ROOT, _xl_prefs), "pages")
# [B] 2026-11-08 情報ページからペットタクシーの料金くらべへの案内（tools/taxi_cta.py、Nori「1と2」）
import taxi_cta
print("taxi_cta", taxi_cta.build(ROOT, _xl_prefs), "pages")
# タクシー以外の分野のページのサイト名は「ペットのくらし窓口」（tools/brand.py、Nori 2026-11-09）
import brand
print("brand", brand.build(ROOT), "pages")
# AIエージェント向けの入口（/webmcp/data.json と /llms.txt。tools/gen_webmcp.py）
import gen_webmcp
gen_webmcp.build(ROOT)
print("ok", len(AREAS), "areas,", len(PREFS), "prefs")
# [B] noindex.json のページに noindex,follow を入れる（ほかの後処理のあと）
for _p in NOINDEX:
  _f = os.path.join(ROOT, _p.strip("/"), "index.html")
  if not os.path.exists(_f): continue
  _t = open(_f, encoding="utf-8").read()
  _t = re.sub(r'<meta name="robots"[^>]*>\s*', "", _t)
  _t = _t.replace("</title>", '</title>\n<meta name="robots" content="noindex,follow">', 1)
  open(_f, "w", encoding="utf-8").write(_t)
print("noindex", len(NOINDEX), "pages")
