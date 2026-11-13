# [B] SEO：料金しらべのデータから作る記事2本（2026-11-13、Nori「全部やって」の3「検索されているのにページがない言葉で記事を作る」）。
# 「ペットタクシー 夜間 料金」「ペットタクシー 待ち時間」などの言葉に、全国の料金表を数えた数字で答える。
# 数字はすべて tools/display_companies.json から生成のたびに数える（tools/guides_fare_survey.py と同じ計算）。会社名は出さない。
import collections
import guides_fare_survey as S

_y, _yen, _mid, _ride = S._y, S._yen, S._mid, S._ride
NOTE = S.NOTE

# ---- 夜間・早朝 ----
_NF = [c for c in S._F if (c["fare"].get("night") or {}) and not c["fare"]["night"].get("unknown")]
def _night_total(c, km):
    n, a = c["fare"]["night"], _ride(c["fare"], km)
    if n.get("flat"): return a + n["flat"]
    if n.get("rate"): return int(a * (1 + n["rate"]))
    return None
def _row(km):
    day = [_ride(c["fare"], km) for c in _NF]
    nt = [x for x in (_night_total(c, km) for c in _NF) if x is not None]
    return [f"{km}km", _y(_mid(day)), _y(_mid(nt)), _y(_mid(nt) - _mid(day))]
_night_rows = [_row(km) for km in (5, 10, 20)]
_from = collections.Counter(c["fare"]["night"].get("from") for c in _NF if c["fare"]["night"].get("from") is not None)
_to = collections.Counter(c["fare"]["night"].get("to") for c in _NF if c["fare"]["night"].get("to") is not None)
N_BY_START = sum(1 for c in _NF if c["fare"]["night"].get("by") == "start")
N_NIGHT = len(_NF)
FROM_MODE, FROM_N = _from.most_common(1)[0]
TO_MODE, TO_N = _to.most_common(1)[0]
N10_DAY, N10_NIGHT = _night_rows[1][1], _night_rows[1][2]

NIGHT = dict(slug="night-fare",
 title="ペットタクシーの夜間・早朝の料金（全国の料金表しらべ）",
 seo_title=f"ペットタクシーの夜間料金はいくら？割増は{FROM_MODE}時から・定額{S.FLAT_MODE:,}円が多い（全国{N_NIGHT}社しらべ）",
 desc=(f"夜間・早朝の割増を料金表に書いているペットタクシー{N_NIGHT}社を数えました。割増がはじまるのは{FROM_MODE}時が{FROM_N}社でいちばん多く、"
       f"1回いくらの定額は{S.FLAT_MODE:,}円が{S.FLAT_MODE_N}社。10kmの運賃は昼間{N10_DAY}、夜間{N10_NIGHT}（まんなかの会社の概算）。確定料金ではありません。"),
 lede="夜中に具合が悪くなった、早朝の手術に連れていきたい。そんなときに気になる夜間・早朝のペットタクシーの料金を、全国の会社の公式サイトの料金表で数えました。",
 img="same-day.jpg", img_alt="夜明け前の住宅街で、キャリーに入ったトイ・プードルを抱えてワゴン車に向かう飼い主", img_caption="写真はイメージです。",
 published="2026-11-13", modified="2026-11-13", checked="2026年11月（各社の公式サイト）",
 sections=[
  ("まとめ", [
   ("tip", f"まとめ：夜間・早朝の割増を書いている会社は{N_NIGHT}社。はじまるのは{FROM_MODE}時（{FROM_N}社）、終わるのは{TO_MODE}時（{TO_N}社）がいちばん多く、"
           f"割増は1回いくらの定額（{S.FLAT_MODE:,}円が{S.FLAT_MODE_N}社）が多い。10kmなら、まんなかの会社で昼間{N10_DAY}、夜間{N10_NIGHT}です（概算）。"),
  ]),
  ("昼間と夜間の運賃のちがい", [
   f"割増を書いている{N_NIGHT}社で、乗った距離の運賃（片道）を昼間と夜間で計算しました。どちらも、まんなかの会社の金額です。",
   ("table", [["乗る距離", "昼間", "夜間・早朝", "ちがい"]] + _night_rows),
   NOTE,
  ]),
  ("割増のつけ方", [
   ("table", [["割増のつけ方", "社数"],
              [f"1回いくらの定額（{S.FLAT_MODE:,}円が{S.FLAT_MODE_N}社）", f"{S.N_NIGHT_FLAT}社"],
              ["運賃の◯割増し（" + "・".join(f"{x}%" for x in S._rates) + "）", f"{S.N_NIGHT_RATE}社"],
              ["時間帯ごとに料金が変わる", f"{S.N_NIGHT - S.N_NIGHT_FLAT - S.N_NIGHT_RATE}社"]]),
   "定額の会社は、距離が短いほど割増の重みが大きくなります。近くの夜間の病院へ行くときは、運賃の◯割増しの会社のほうが安くなることもあります。",
  ]),
  ("割増の時間帯", [
   ("table", [["はじまる時刻", "社数"]] + [[f"{h}時", f"{n}社"] for h, n in sorted(_from.items())]),
   ("table", [["終わる時刻", "社数"]] + [[f"{h}時", f"{n}社"] for h, n in sorted(_to.items())]),
   f"乗っているあいだに少しでも割増の時間に入ると、その乗車の全部にかける会社が多く、乗る時刻だけで決める会社は{N_BY_START}社でした。"
   f"{FROM_MODE}時の少し前に乗っても、着くのが{FROM_MODE}時をすぎると割増になることがあります。",
  ]),
  ("夜に頼むときに確かめること", [
   ("ul", ["受け付けている時間（夜は受けていない会社もあります）",
           "割増がかかる時間帯と、乗っているあいだに時間帯が変わったときの計算",
           "病院で待ってもらう料金と、帰りも頼めるか",
           "夜間・救急の動物病院が受け入れてくれるか（先に病院へ電話）"]),
   ("links", [("夜間・救急の動物病院（都道府県ごと）", "/hospital/night/"),
              ("ペットタクシーは当日でも頼める？", "/guide/same-day/"),
              ("全国のペットタクシー料金しらべ", "/guide/pet-taxi-fare-survey/")]),
   ("cta", "夜間の料金も入れて各社をくらべる（無料）"),
  ]),
 ],
 faq=[("ペットタクシーは夜は高くなりますか？", f"夜間・早朝の割増を料金表に書いている会社は{N_NIGHT}社でした。10kmなら、まんなかの会社で昼間{N10_DAY}、夜間{N10_NIGHT}です（概算・確定料金ではありません）。"),
      ("何時から夜間料金になりますか？", f"はじまる時刻は{FROM_MODE}時がいちばん多く（{FROM_N}社）、終わるのは{TO_MODE}時が多くありました。会社によって違うので、頼むときに確かめてください。"),
      ("夜間の割増はいくらですか？", f"1回いくらの定額の会社が{S.N_NIGHT_FLAT}社で、{S.FLAT_MODE:,}円がいちばん多くありました。運賃の◯割増しの会社は{S.N_NIGHT_RATE}社です。")],
 sources=[],
 dataset=["昼間と夜間の運賃", "夜間・早朝の割増のつけ方", "割増の時間帯"],
 related=["same-day", "pet-taxi-fare-survey", "hospital"])

# ---- 待ち時間 ----
_WF = [c for c in S._F if c["fare"].get("wait") and c["fare"]["wait"].get("unit")]
def _wcost(w, m):
    over = max(0, m - w.get("free", 0))
    return -(-over // w["unit"]) * w["yen"]
_wait_rows = [[f"{m}分", _y(_mid([_wcost(c["fare"]["wait"], m) for c in _WF])),
               f"{_y(min(_wcost(c['fare']['wait'], m) for c in _WF))}〜{_y(max(_wcost(c['fare']['wait'], m) for c in _WF))}"] for m in (30, 60, 90, 120)]
_free = collections.Counter(c["fare"]["wait"].get("free", 0) for c in _WF)
N_WAIT = len(_WF)
W60 = _wait_rows[1][1]
_W10 = _yen(_mid([c["fare"]["wait"]["yen"] * 10 / c["fare"]["wait"]["unit"] for c in _WF]))
_FREE_MID = _mid([c["fare"]["wait"].get("free", 0) for c in _WF])

WAIT = dict(slug="wait-fare",
 title="ペットタクシーの待ち時間の料金（全国の料金表しらべ）",
 seo_title=f"ペットタクシーの待ち時間はいくら？病院で60分待つと{W60}（全国{N_WAIT}社しらべ）",
 desc=(f"病院で待っていてもらうときの料金を書いているペットタクシー{N_WAIT}社を数えました。まんなかの会社で、はじめの{_FREE_MID}分は無料、そのあと10分ごとに{_W10}。"
       f"60分待つと{W60}です（概算）。待ってもらうか、いったん帰ってもらうかの考え方もまとめました。"),
 lede="診察や検査、トリミングのあいだ、ペットタクシーに待っていてもらうといくらかかるのか。全国の会社の公式サイトの料金表で数えました。",
 img="hospital.jpg", img_alt="動物病院の前でペットタクシーから降りる、キャリーに入った猫と飼い主", img_caption="写真はイメージです。",
 published="2026-11-13", modified="2026-11-13", checked="2026年11月（各社の公式サイト）",
 sections=[
  ("まとめ", [
   ("tip", f"まとめ：待ち時間の料金を書いている会社は{N_WAIT}社。まんなかの会社で、はじめの{_FREE_MID}分は無料、そのあと10分ごとに{_W10}。60分待ってもらうと{W60}です（概算）。"),
  ]),
  ("待つ時間ごとの料金", [
   f"待ち時間の料金を書いている{N_WAIT}社で、待ってもらう時間ごとの料金を計算しました。往復の運賃とは別にかかります。",
   ("table", [["待つ時間", "まんなかの会社", "安い会社〜高い会社"]] + _wait_rows),
   "待ち時間の料金は、当日の実際の待ち時間で変わります。診察が長びくと、そのぶん料金も上がります。",
   NOTE,
  ]),
  ("はじめの何分が無料か", [
   ("table", [["無料の時間", "社数"]] + [[("なし" if f == 0 else "ずっと無料（待ち時間の料金なし）" if f >= 600 else f"{f}分"), f"{n}社"] for f, n in sorted(_free.items())]),
  ]),
  ("待ってもらうか、いったん帰ってもらうか", [
   "待ち時間が短い（30分ほどまで）なら、待ってもらうほうが手間も料金も少ないことが多いです。",
   "検査や処置で何時間もかかりそうなときは、いったん帰ってもらい、終わったころにもう一度来てもらうほうが安いことがあります。そのときは、帰りのお迎え料金がもう一度かかるかを、頼むときに確かめてください。",
   ("ul", ["待ってもらうとき：待ち時間の料金と、はじめの無料の時間",
           "帰ってもらうとき：帰りのお迎え料金と、帰りの時刻が決まっていなくても来てもらえるか",
           "どちらも：病院の駐車場に車を止められるか"]),
   ("links", [("ペットタクシーの料金のしくみ", "/guide/fare/"),
              ("動物病院への通院にペットタクシーを使う", "/guide/hospital/"),
              ("全国のペットタクシー料金しらべ", "/guide/pet-taxi-fare-survey/")]),
   ("cta", "待ち時間も入れて各社をくらべる（無料）"),
  ]),
 ],
 faq=[("ペットタクシーの待ち時間は有料ですか？", f"待ち時間の料金を書いている会社は{N_WAIT}社で、まんなかの会社ははじめの{_FREE_MID}分が無料、そのあと10分ごとに{_W10}でした。"),
      ("病院で1時間待ってもらうといくらですか？", f"まんなかの会社で{W60}です（概算・確定料金ではありません）。往復の運賃とは別にかかり、当日の実際の待ち時間で変わります。"),
      ("待ってもらうのと帰ってもらうのはどちらが安いですか？", "短い待ち時間なら待ってもらうほうが安いことが多く、何時間もかかるときは、いったん帰ってもらうほうが安いことがあります。帰りのお迎え料金がかかるかを確かめてください。")],
 sources=[],
 dataset=["待つ時間ごとの料金", "はじめの無料の時間"],
 related=["fare", "hospital", "pet-taxi-fare-survey"])

MORE_GUIDES = [NIGHT, WAIT]
