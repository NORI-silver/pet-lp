# [B] SEO・AIO：独自データ記事「全国のペットタクシー料金しらべ」（2026-11-09、戦略担当の打ち手4「引用される土台」・Nori「倍のスピードで」）。
# 数字はすべて tools/display_companies.json（各社の公式サイトの料金表を当サイトが読み取ったもの）から、生成のたびに数える。手で数字を書かない。
# 会社名は出さない（提携していない会社のため）。同じチェーンのお店は1社ずつ数える。お客さまに見せる金額は100円単位（AGENTS.md「料金は目安」）。
import json, os, re, collections
from prefs import PREFS

_D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "display_companies.json"), encoding="utf-8"))["companies"]
_F = [c for c in _D if c.get("fare") and c["fare"].get("kind", "dist") == "dist" and c["fare"].get("base")]

def _ride(F, km):
    a, bk = F["base"]
    for t in F["tiers"]:
        lo = max(t[0], bk + 1); hi = min(km, t[1] if t[1] is not None else 10**9)
        if hi >= lo: a += -(-(hi - lo + 1) // (t[3] if len(t) > 3 else 1)) * t[2]
    if re.search("税抜|税別", F.get("tax") or "") and "税込" not in (F.get("tax") or ""): a = -(-a * 11 // 10)
    return a
def _r(n): return int((n + 50) // 100 * 100)
def _y(n): return f"{_r(n):,}円"
def _mid(v): v = sorted(v); return v[(len(v) - 1) // 2]
def _span(v): v = sorted(v); return f"{_y(_mid(v))}（{_y(v[0])}〜{_y(v[-1])}）"

N_ALL, N_F = len(_D), len(_F)
_KEYS = sorted({a for c in _D for a in c.get("areas", [])})
_FULL = {}
for _s, _n, *_ in PREFS: _FULL[_n if _n == "北海道" else _n[:-1]] = (_n, f"/area/{_s}/")
_FULL.update({"東京": ("東京都", "/tokyo/"), "神奈川": ("神奈川県", "/kanagawa/"), "埼玉": ("埼玉県", "/saitama/"), "千葉": ("千葉県", "/chiba/")})
N_PREF = len([k for k in _KEYS if k in _FULL])

KMS = [3, 5, 10, 20, 30, 50]
_dist_rows = [[f"{km}km", _y(_mid([_ride(c["fare"], km) for c in _F])), f"{_y(min(_ride(c['fare'], km) for c in _F))}〜{_y(max(_ride(c['fare'], km) for c in _F))}"] for km in KMS]
M10 = _y(_mid([_ride(c["fare"], 10) for c in _F]))
M5 = _y(_mid([_ride(c["fare"], 5) for c in _F]))

# 基本料金（初乗り）と、そのあとの1kmあたり
_base_yen = [c["fare"]["base"][0] for c in _F]
_base_km = [c["fare"]["base"][1] for c in _F]
_per1 = [c["fare"]["tiers"][0][2] / (c["fare"]["tiers"][0][3] if len(c["fare"]["tiers"][0]) > 3 else 1) for c in _F if c["fare"]["tiers"]]
# お迎え料金
_pk = [c["fare"].get("pick") or {} for c in _F]
N_PICK_KM = sum(1 for p in _pk if p.get("per") and not p.get("yen"))
N_PICK_FLAT = sum(1 for p in _pk if p.get("yen") and not p.get("per"))
N_PICK_MIX = sum(1 for p in _pk if p.get("yen") and p.get("per"))
N_PICK_NONE = sum(1 for p in _pk if not p or (p.get("yen") == 0 and not p.get("per")))
# 夜間・早朝
_nt = [c["fare"].get("night") for c in _F]
N_NIGHT = sum(1 for n in _nt if n and not n.get("unknown"))
N_NIGHT_FLAT = sum(1 for n in _nt if n and n.get("flat"))
N_NIGHT_RATE = sum(1 for n in _nt if n and n.get("rate"))
_flat_c = collections.Counter(n["flat"] for n in _nt if n and n.get("flat"))
FLAT_MODE, FLAT_MODE_N = _flat_c.most_common(1)[0]
_rates = sorted({int(round(n["rate"] * 100)) for n in _nt if n and n.get("rate")})
_from_c = collections.Counter(n["from"] for n in _nt if n and n.get("from") is not None)
FROM_MODE = _from_c.most_common(1)[0][0]
# 待ち時間
_wt = [c["fare"].get("wait") for c in _F if c["fare"].get("wait")]
N_WAIT = len(_wt)
_w10 = [w["yen"] * 10 / w["unit"] for w in _wt if w.get("unit")]
_wfree = [w.get("free", 0) for w in _wt]
# 税
_tax = collections.Counter("税込" if (c["fare"].get("tax") or "") == "税込" else "税抜・税別" if re.search("税抜|税別", c["fare"].get("tax") or "") else "書いていない" for c in _F)
# 受付
# 同じ料金表のお店が多いチェーン（同じ料金表をいちばん多くの会社が使っている数）
_same = collections.Counter(json.dumps({k: v for k, v in c["fare"].items() if k != "src"}, sort_keys=True) for c in _F)
N_SAME_TABLE = _same.most_common(1)[0][1]
_UNIQ = list({json.dumps({k: v for k, v in c["fare"].items() if k != "src"}, sort_keys=True): c for c in _F}.values())
N_UNIQ = len(_UNIQ)
U10 = _y(_mid([_ride(c["fare"], 10) for c in _UNIQ]))
U5 = _y(_mid([_ride(c["fare"], 5) for c in _UNIQ]))
def _yen(n): return f"{int(n):,}円"  # 料金表に書いてある単価（概算ではないので、まるめない）
N24 = sum(1 for c in _D if c.get("hours") == "0-24")
NSAME = sum(1 for c in _D if c.get("lead_days") == 0)

# 都道府県ごと（お迎えに来てくれる会社が2社以上の県）
_pref_rows = []
for k in sorted(_KEYS, key=lambda k: (-sum(1 for c in _D if k in c.get("areas", [])), _FULL.get(k, ("", "~"))[1])):
    if k not in _FULL: continue
    cs = [c for c in _D if k in c.get("areas", [])]
    fs = [c for c in _F if k in c.get("areas", [])]
    if len(cs) < 2: continue
    _pref_rows.append([_FULL[k][0], f"{len(cs)}社", f"{len(fs)}社",
                       _y(_mid([_ride(c["fare"], 5) for c in fs])) if len(fs) >= 2 else "—",
                       _y(_mid([_ride(c["fare"], 10) for c in fs])) if len(fs) >= 2 else "—",
                       f"{sum(1 for c in cs if c.get('hours') == '0-24')}社", f"{sum(1 for c in cs if c.get('lead_days') == 0)}社"])
_pref_links = [(f"{r[0]}のペットタクシー", _FULL[r[0] if r[0] == "北海道" else r[0][:-1]][1]) for r in _pref_rows[:12]]

NOTE = ("金額は、各社の公式サイトの料金表を同じ式で計算した概算で、100円単位にまるめています。確定料金ではありません。"
        "当日の道順・渋滞・待ち時間などで変わります。お迎え料金・夜間の割増・待ち時間・高速代は、表に書いたもののほかは入っていません。")
CITE = "ペットタクシー予約窓口「全国のペットタクシー料金しらべ（2026年11月）」https://pet.shiokonbu.com/guide/pet-taxi-fare-survey/"

FARE_SURVEY = dict(slug="pet-taxi-fare-survey",
 title="全国のペットタクシー料金しらべ（2026年11月）",
 seo_title=f"ペットタクシーの料金相場は？全国{N_ALL}社しらべ｜10kmで{M10}・都道府県別の運賃と夜間割増",
 desc=(f"全国{N_ALL}社のペットタクシーの公式サイトの料金表を当サイトで読み取り、同じ式で計算しました。"
       f"乗った距離の運賃はまんなかの会社で5kmが{M5}、10kmが{M10}。都道府県別の料金、お迎え料金・夜間割増・待ち時間のつけ方の違いを数字でまとめています。確定料金ではありません。"),
 lede=f"「ペットタクシーっていくらかかるの？」に、全国{N_ALL}社の公式サイトの料金表を同じ式で計算して答えます。数字は当サイトのデータから自動で数えていて、データが変わるとこのページも変わります。",
 img="fare.jpg", img_alt="リビングのテーブルで財布と硬貨を前にメモを書く飼い主と、奥のキャリーから見つめる柴犬", img_caption="写真はイメージです。",
 published="2026-11-09", modified="2026-11-09", checked="2026年11月（各社の公式サイト）",
 sections=[
  ("まとめ", [
   ("tip", f"まとめ：乗った距離の運賃（片道・昼間）は、まんなかの会社で5kmが{M5}、10kmが{M10}。いちばん差がつくのはお迎え料金（営業所から家までの距離でかかる会社が{N_PICK_KM + N_PICK_MIX}社。定額との組み合わせを含む）。夜間・早朝の割増は{N_NIGHT}社が書いていて、定額{FLAT_MODE:,}円がいちばん多い（{FLAT_MODE_N}社）。"),
   ("ul", [f"しらべた会社：全国{N_ALL}社（お迎えに来てくれる都道府県は{N_PREF}）。距離で計算できる料金表がある会社は{N_F}社",
           f"24時間受付と公式サイトに書いている会社：{N24}社。当日も受けるとはっきり書いている会社：{NSAME}社",
           f"料金表の税の書き方：税込{_tax['税込']}社・税抜や税別{_tax['税抜・税別']}社・書いていない{_tax['書いていない']}社（税抜の会社は税込に直して計算）",
           f"同じチェーンのお店は1社ずつ数えています。いちばん多い料金表は{N_SAME_TABLE}社が同じものを使っているため、まんなかの金額はその料金にそろいやすくなっています。会社名は出していません"]),
  ]),
  ("距離ごとの運賃（全国）", [
   f"距離で計算できる料金表がある{N_F}社で、乗った距離の運賃（片道・昼間）を計算しました。まんなかの会社の金額と、安い会社〜高い会社の幅です。",
   ("table", [["乗る距離", "まんなかの会社", "安い会社〜高い会社"]] + _dist_rows),
   f"同じ料金表を使っているお店を1つにまとめて数えると（{N_UNIQ}種類の料金表）、まんなかは5kmが{U5}、10kmが{U10}でした。",
   NOTE,
  ]),
  ("都道府県ごとの料金と会社の数", [
   "お迎えに来てくれる会社が2社以上ある都道府県です。「料金表あり」は、距離で計算できる料金表を公式サイトに出している会社の数で、運賃はその会社たちのまんなかの金額です。",
   ("table", [["お迎えの都道府県", "来てくれる会社", "料金表あり", "5km", "10km", "24時間受付", "当日も受ける"]] + _pref_rows),
   NOTE,
   ("links", _pref_links),
  ]),
  ("基本料金（初乗り）と1kmごとの料金", [
   f"基本料金はまんなかの会社で{_yen(_mid(_base_yen))}、その中に入っている距離は{_mid(_base_km)}kmでした（安い会社{_yen(min(_base_yen))}〜高い会社{_yen(max(_base_yen))}。初乗りの距離は会社で違います）。そのあとの1kmごとの料金は、まんなかの会社で{_yen(_mid(_per1))}です（料金表に書いてある金額）。",
   "初乗りが安くても1kmごとの料金が高い会社は、長い距離になると逆に高くなります。行き先までの距離で合計をくらべるのが確かです。",
  ]),
  ("お迎え料金のつけ方", [
   ("table", [["つけ方", "社数"],
              ["営業所から家までの距離でかかる", f"{N_PICK_KM}社"],
              ["1回いくらの定額", f"{N_PICK_FLAT}社"],
              ["定額＋一定の距離をこえた分", f"{N_PICK_MIX}社"],
              ["料金表に書いていない・かからない", f"{N_PICK_NONE}社"]]),
   "お迎え料金は、乗る距離の運賃と同じくらいかかることがあります。家の近くに営業所がある会社ほど安くなりやすいので、同じ行き先でも会社によって合計が大きく変わります。",
  ]),
  ("夜間・早朝の割増", [
   ("table", [["割増のつけ方", "社数"],
              [f"1回いくらの定額（{FLAT_MODE:,}円が{FLAT_MODE_N}社）", f"{N_NIGHT_FLAT}社"],
              ["運賃の◯割増し（" + "・".join(f"{x}%" for x in _rates) + "）", f"{N_NIGHT_RATE}社"],
              ["時間帯ごとに料金が変わる", f"{N_NIGHT - N_NIGHT_FLAT - N_NIGHT_RATE}社"],
              ["料金表に書いていない", f"{N_F - N_NIGHT}社"]]),
   f"割増がはじまる時刻は{FROM_MODE}時がいちばん多くありました。乗っているあいだに割増の時間に入るとかかる会社と、乗る時刻だけで決める会社があります。",
  ]),
  ("待ち時間の料金", [
   f"病院で待っていてもらうときの料金を書いている会社は{N_WAIT}社。まんなかの会社で、はじめの{_mid(_wfree)}分は無料、そのあと10分ごとに{_yen(_mid(_w10))}でした。診察が長くなりそうなときは、いったん帰ってもらって迎えに来てもらうほうが安いこともあります。",
  ]),
  ("しらべ方と、このデータの引用", [
   f"各社の公式サイトの料金表（基本料金・距離ごとの料金・お迎え料金・待ち時間・夜間の割増・税）を当サイトが読み取り、全部の会社を同じ式で計算しました。AIに金額を計算させてはいません。公式サイトは定期的に照合し、料金が変わったらデータを直します。",
   "距離だけで決まらない料金（時間制・地域ごとの定額など）の会社は、距離ごとの表からは外しています。料金表を公開していない会社は「お見積もり」なので入っていません。",
   f"このページの数字は、出どころを書いていただければ引用していただいてかまいません。例：{CITE}",
   ("cta", "あなたのルートで各社の料金をくらべる（無料）"),
  ]),
 ],
 faq=[(f"ペットタクシーの料金の相場はいくらですか？", f"全国{N_F}社の料金表で計算すると、乗った距離の運賃（片道・昼間）は、まんなかの会社で5kmが{M5}、10kmが{M10}でした。これにお迎え料金や待ち時間、夜間の割増が加わることがあります。確定料金ではありません。"),
      ("お迎え料金はかかりますか？", f"多くの会社でかかります。営業所から家までの距離でかかる会社が{N_PICK_KM + N_PICK_MIX}社（定額との組み合わせの{N_PICK_MIX}社を含む）、1回いくらの定額だけの会社が{N_PICK_FLAT}社でした。家の近くに営業所がある会社ほど安くなりやすいです。"),
      ("夜はいくら高くなりますか？", f"夜間・早朝の割増を書いている会社は{N_NIGHT}社で、定額の会社が{N_NIGHT_FLAT}社（{FLAT_MODE:,}円が多い）、運賃の◯割増しの会社が{N_NIGHT_RATE}社でした。はじまる時刻は{FROM_MODE}時が多くありました。"),
      ("このデータを記事やSNSで使ってもいいですか？", f"出どころ（{CITE}）を書いていただければかまいません。数字は当サイトのデータから自動で数えていて、更新日の時点のものです。")],
 sources=[],
 related=["fare", "choose", "same-day"])
