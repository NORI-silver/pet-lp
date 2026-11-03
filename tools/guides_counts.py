# [B] 2026-11-03「中身の薄いページを充実させる」：本文の短かったガイドに、うちのデータを数えた節を足す。
# 数えるもの：候補カードと同じ全国の会社のデータ（display_companies.json の animals・fare.wait）と、病院・老犬ホームの一覧（hospitals.json・rojin.json）。
# 生成のたびに数え直すので、データが変わると本文の数字もそろう。会社名は出さない。金額は概算で、100円単位にまるめる。
import json, os, re

_D = os.path.dirname(os.path.abspath(__file__))
_C = json.load(open(os.path.join(_D, "display_companies.json"), encoding="utf-8"))["companies"]
_H = json.load(open(os.path.join(_D, "hospitals.json"), encoding="utf-8"))
_R = json.load(open(os.path.join(_D, "rojin.json"), encoding="utf-8"))
_ROJIN = _R if isinstance(_R, list) else next(v for v in _R.values() if isinstance(v, list))

def _r100(y): return f"{int(round(y / 100.0)) * 100:,}円"
def _mid(v): v = sorted(v); return v[(len(v) - 1) // 2]

def _ride(F, km):  # gen_areas._nat_ride と同じ決まり（Code.gs の displayPrice_ の乗車料金）
    a, bk = F["base"]
    for t in F["tiers"]:
        lo = max(t[0], bk + 1); hi = min(km, t[1] if t[1] is not None else 10**9)
        if hi >= lo: a += -(-(hi - lo + 1) // (t[3] if len(t) > 3 else 1)) * t[2]
    if re.search("税抜|税別", F.get("tax") or "") and "税込" not in (F.get("tax") or ""): a = -(-a * 11 // 10)
    return a
_DIST = [c["fare"] for c in _C if c.get("fare") and c["fare"].get("kind", "dist") == "dist" and c["fare"].get("base")]

def _wait(W, m):  # booking/Code.gs の waitFee と同じ決まり
    if m <= W.get("free", 0): y = 0
    elif W.get("after"):
        b0 = W["first"][1] if W.get("first") else 0; s0 = W["first"][0] if W.get("first") else W.get("free", 0)
        y = b0 + -(-max(0, min(m, W["after"][0]) - s0) // W["unit"]) * W["yen"] + -(-max(0, m - W["after"][0]) // W["unit"]) * W["after"][1]
    elif W.get("first"): y = W["first"][1] + max(0, -(-(m - W["first"][0]) // W["unit"])) * W["yen"]
    else: y = -(-(m - W.get("free", 0)) // W["unit"]) * W["yen"]
    return min(y, W["cap"]) if W.get("cap") is not None else y

# ── 乗せられる動物 ──
_A = [c.get("animals") or {} for c in _C]
N_ALL = len(_C)
N_KNOWN = sum(1 for x in _A if x.get("all") or x.get("only") or x.get("ok") or x.get("no"))
N_ANY = sum(1 for x in _A if x.get("all"))
N_ONLY = sum(1 for x in _A if x.get("only"))
def _ok(k): return sum(1 for x in _A if k in (x.get("ok") or []) and not x.get("all"))
def _okall(k): return sum(1 for x in _A if x.get("all") or k in (x.get("ok") or []))
def _no(k): return sum(1 for x in _A if k in (x.get("no") or []))
def _prefs(k):
    ps = set()
    for c in _C:
        x = c.get("animals") or {}
        if x.get("all") or k in (x.get("ok") or []): ps.update(c.get("areas", []))
    return len(ps)

def _exotic():
    hs = _H.get("exotic", [])
    return len(hs), len({p for h in hs for p in h["prefs"]})

def _animal_section(k, lab):
    ne, npf = _exotic()
    far = [f"{km}kmなら{_r100(_mid([_ride(F, km) for F in _DIST]))}" for km in (20, 50)]
    return (f"全国{N_ALL}社のデータで数えると", [
        f"候補に出している全国{N_ALL}社のペットタクシーのうち、乗せられる動物を公式サイトに書いているのは{N_KNOWN}社でした。そのうち「種類を問わない」「法律で禁止されていないペットなら」のように広く書いている会社が{N_ANY}社、{lab}を名前を出して書いている会社が{_ok(k)}社（「種類を問わない」とは別に数えています）、「犬・猫のみ」と書いている会社が{N_ONLY}社" + (f"、{lab}は断ると書いている会社が{_no(k)}社" if _no(k) else "") + "でした。",
        f"「種類を問わない」会社と合わせると、{lab}を乗せられると読める会社は{_okall(k)}社で、お迎えの対応エリアに書かれている都道府県は{_prefs(k)}になります。残りの{N_ALL - N_KNOWN}社は、公式サイトに乗せられる動物を書いていません。書いていない会社が断るとは限らないので、フォームで種類を選んで問い合わせると、会社が確かめて返事をします。",
        ("table", [["公式サイトの書き方", "社数"],
                   ["種類を問わない（広く受ける）", f"{N_ANY}社"],
                   [f"{lab}を名前を出して書いている", f"{_ok(k)}社"],
                   ["犬・猫のみ", f"{N_ONLY}社"]] + ([[f"{lab}は断る", f"{_no(k)}社"]] if _no(k) else []) + [
                   ["乗せられる動物を書いていない", f"{N_ALL - N_KNOWN}社"]]),
        f"うさぎ・鳥・爬虫類などを専門に診る動物病院は数が少なく、当サイトの一覧では{ne}院・{npf}都道府県です。遠くの病院へ通うことが多くなるので、乗る距離の運賃（片道）を全国{len(_DIST)}社の料金表で計算すると、まんなかの会社で" + "、".join(far) + "でした（確定料金ではありません。各社の公式サイトの料金表をもとに計算した概算で、お迎え料金・待ち時間・当日の道順や渋滞などで変わります）。",
        ("links", [("エキゾチックアニマルの専門の動物病院（全国）", "/hospital/exotic/"), ("ペットタクシーの長距離移動｜50km・100kmの料金の目安", "/guide/long-distance/")]),
    ])

# ── 待ち時間（退院・通院） ──
_W = [c["fare"]["wait"] for c in _C if c.get("fare") and c["fare"].get("wait") and c["fare"]["wait"].get("unit")]
def _wait_section():
    frees = [W.get("free", 0) for W in _W]
    f0 = sum(1 for x in frees if x == 0); f10 = sum(1 for x in frees if 0 < x < 30); f30 = sum(1 for x in frees if x >= 30)
    rows = [["待ってもらう時間", "まんなかの会社", "安い会社〜高い会社"]]
    for m in (30, 60, 120):
        v = sorted(_wait(W, m) for W in _W)
        rows.append([f"{m}分", _r100(_mid(v)), f"{_r100(v[0])}〜{_r100(v[-1])}"])
    return ("退院の手続きを待ってもらうと、いくら？", [
        f"退院の日は、会計や説明で病院の中で待つ時間が長くなりがちです。全国{N_ALL}社のうち、待ち時間の料金を公式サイトの料金表に書いている{len(_W)}社で数えると、無料で待ってもらえる時間は「なし」が{f0}社、「10〜20分くらい」が{f10}社、「30分以上」が{f30}社でした。",
        f"その料金表で、待ってもらったときの料金を計算すると次のとおりです（乗る料金・お迎え料金とは別にかかります）。",
        ("table", rows),
        ("tip", "確定料金ではありません。各社の公式サイトの料金表をもとに計算した概算で、当日の道順・渋滞・待ち時間などで変わります。待ち時間が長くなりそうなときは、いったん帰ってもらって、帰りの便を別に頼むほうが安いこともあります。"),
        "フォームでは、往復にして「病院で待つ時間」を選ぶと、会社ごとの待ち時間の料金を入れた目安が出ます。退院の時刻がはっきりしないときは、問い合わせのメモ欄に「会計のあと連絡します」と書いておくと、会社が受けられるかを返事してくれます。",
    ])

# ── シニア（家から出るのがむずかしいとき） ──
def _senior_section():
    v = _H.get("visit", []); vp = len({p for h in v for p in h["prefs"]})
    rp = len({p for r in _ROJIN for p in (r.get("prefs") or [r.get("pref")]) if p})
    cs = [c for c in _C if "介助のサポートあり" in c.get("points", [])]
    return ("通院がむずかしくなってきたら", [
        f"候補に出している全国{N_ALL}社のうち、公式サイトの文から「介助のサポートあり」と読める会社は{len(cs)}社でした。数は多くないので、歩けない子の移動は、問い合わせのメモ欄に体重と体の様子を書いて、乗せられるかを会社に確かめてもらうのが確実です。",
        f"移動そのものが負担になってきたら、獣医さんに家に来てもらう方法もあります。往診を専門にしている動物病院は、当サイトの一覧で{len(v)}院・{vp}都道府県です。家での介護がむずかしくなったときの老犬ホーム・老猫ホームは{len(_ROJIN)}施設・{rp}都道府県を載せています。",
        ("links", [("往診専門の動物病院（自宅に来てくれる）", "/hospital/visit/"), ("老犬ホーム・老猫ホーム（全国）", "/rojin-home/"), ("老犬ホームの費用と、えらび方", "/guide/rojin-home-cost/")]),
    ])

EXTRA = {
    "small-animals": [_animal_section("small", "小動物（うさぎ・ハムスター・フェレットなど）")],
    "birds-reptiles": [_animal_section("bird", "鳥"), ("爬虫類・魚は、さらに少ない", [
        f"爬虫類（カメ・トカゲ・ヘビなど）を名前を出して書いている会社は{_ok('reptile')}社、魚は{_ok('fish')}社でした（「種類を問わない」{N_ANY}社とは別に数えています）。爬虫類を断ると書いている会社は{_no('reptile')}社です。",
        "ヘビなどは、電車でも持ちこめないことがあります。どんな動物か（種類・大きさ・入れ物）を問い合わせのメモ欄にくわしく書くと、会社が乗せられるかを判断しやすくなります。",
    ])],
    "discharge-transfer": [_wait_section()],
    "senior": [_senior_section()],
}
