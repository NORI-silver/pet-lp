# [B] SEO：検索の多い「ペット火葬 ◯◯県」（全国 月40,500・霊園12,100）と「夜間 動物病院 ◯◯県」（全国 月22,200）の都道府県ごとのページ。
# キーワードプランナー 2026-11-02（docs/seo-agents.md）で、情報ページのカテゴリの中で検索がとくに多かったため。
# 生成は tools/gen_prefpages.py（/sougi/<県>/、/hospital/night/<県>/）。データは全国のページと同じ（sougi.json・sougi_facilities.json・emergency.json）。
# 守ること：順位・おすすめなし。電話番号なし。病院の料金なし。火葬の料金は公式サイトに書いてある例だけ（全国のページと同じ）。
import json, os
import gen_sougi, gen_hospitals

_D = os.path.dirname(os.path.abspath(__file__))
EMG = json.load(open(os.path.join(_D, "emergency.json"), encoding="utf-8"))

# ── ペットが亡くなったら（火葬・霊園）──
_FAC = [dict(f, prefs=[f["pref"]], url=f["u"]) for f in gen_sougi.F["facilities"]]
_CITIES = {}
for c in gen_sougi.J["cities"]:
    _CITIES.setdefault(c["pref"], []).append(c)

def _has(f, w): return w in f.get("kinds", []) or w in f.get("services", [])

# [B] 2026-11-03：県ごとの料金の幅（公式サイトに書いてある、いちばん小さい区分の料金）と全国の真ん中。数え方は guides_sougi と同じ。
import guides_sougi as _gs
_TYPES = [("kobetsu", "個別火葬（おまかせ）", _gs.SK), ("tachiai", "立ち会い火葬", _gs.ST), ("goudou", "合同火葬", _gs.SG)]
def _price_lines(rs):
    out = []
    for k, lab, nat in _TYPES:
        v = sorted(g[k] for g in (_gs._prices(f.get("price")) for f in rs) if k in g)
        if len(v) >= 2:
            out.append((lab, len(v), f"{v[0]:,}円〜{v[-1]:,}円", nat["med"]))
    return out

def _sougi_facts(rs):
    n = len(rs)
    pl = [f"{lab}の料金の例（{k}か所・猫や小型犬など小さい区分）：{rng}（全国{nat_n}か所の真ん中は{med}）"
          for lab, k, rng, med in _price_lines(rs) for nat_n in [{"個別火葬（おまかせ）": _gs.SK, "立ち会い火葬": _gs.ST, "合同火葬": _gs.SG}[lab]["n"]]]
    return pl + [f"個別火葬：{sum(_has(f, '個別火葬') for f in rs)}／{n}", f"立ち会い火葬：{sum(_has(f, '立ち会い火葬') for f in rs)}／{n}",
            f"お迎え（家まで来てくれる）：{sum(_has(f, 'お迎え') for f in rs)}／{n}", f"霊園：{sum(_has(f, '霊園') for f in rs)}／{n}",
            f"納骨堂：{sum(_has(f, '納骨堂') for f in rs)}／{n}", f"公式サイトに料金の例があるところ：{sum(bool(f.get('price')) for f in rs)}／{n}"]

def _sougi_extra(e, pf):
    cs = _CITIES.get(pf, [])
    if not cs: return ""
    return (f'<section class="emg-pref" data-pref="{e(pf)}"><h2 style="font-size:1.15em">{e(pf)}の自治体の受け付け（{len(cs)}市区）</h2>'
            '<p class="emg-free" style="margin-top:0">市や区でも、ペットの火葬や引き取りを受け付けていることがあります。料金が安いかわりに、ほかの動物と一緒に火葬してお骨が返らないことが多いので、お骨の扱いを確かめてください。</p>'
            + "".join(gen_sougi._card(e, c) for c in cs) + "</section>")

def _sougi_faq(pf, rs, n):
    cs = _CITIES.get(pf, [])
    back = sum(c.get("k") == "back" for c in cs)
    return [
     (f"{pf}でペットの火葬ができるところは？", f"この一覧では、{pf}の民間のペット火葬場・霊園・納骨堂を{n}か所と、{len(cs)}の市区の受け付けを、公式サイトで確かめた内容で載せています。"),
     (f"{pf}で家まで来てくれるペット火葬はありますか？", f"公式サイトに「お迎え」や訪問の火葬を書いているところは、この一覧の{pf}では{sum(_has(f, 'お迎え') for f in rs)}か所です。"),
     ("市や区に頼むと、お骨は返ってきますか？", (f"{pf}で載せている{len(cs)}の市区のうち、お骨を返してもらえると案内しているのは{back}か所です。" if cs else "") + "多くの市区では、ほかの動物と一緒に火葬するためお骨は返りません。お骨を手元に残したいときは、民間の個別火葬をえらびます。"),
     *([(f"{pf}のペット火葬の料金は？", "公式サイトに書いてある、猫や小型犬など小さい区分の料金の例では、" + "、".join(f"{lab}が{rng}（{k}か所）" for lab, k, rng, med in _price_lines(rs)) + f"でした。全国の施設で数えた真ん中は、個別火葬（おまかせ）が{_gs.SK['med']}（{_gs.SK['n']}か所）、立ち会い火葬が{_gs.ST['med']}（{_gs.ST['n']}か所）です。体重やお迎えの有無で変わるので、見積もりで確かめてください。")] if _price_lines(rs) else []),
     ("亡くなってから火葬までに、まずすることは？", "体をきれいにして、保冷剤などで体を冷やし、涼しい部屋で安置します。くわしくは全国のページ「ペットが亡くなったら」にまとめました。"),
    ]

SOUGI = dict(slug="sougi", name="ペット火葬・霊園", unit="か所", h1="ペットが亡くなったら", items=_FAC, card=gen_sougi._fcard,
  checked=gen_sougi.F.get("checked", gen_sougi.J["checked"]), reviews=False, min=1, css=gen_sougi.CSS,
  free="この一覧は無料の情報です。火葬場・霊園や自治体からお金をもらっていません。おすすめ順や点数順ではありません。料金は公式サイトに書いてある例だけで、体重や内容で変わります。", list_h="民間のペット火葬場・霊園・納骨堂",
  title_word="ペット火葬・ペット霊園", title_tail="個別火葬・立ち会い・お迎え・自治体の受け付け",
  desc_tail="個別火葬・立ち会い火葬・お迎え・霊園・納骨堂のどれをしているか、公式サイトに書いてある料金の例、市区の受け付け（料金・お骨が返るか）を載せています。順位やおすすめはつけていません。",
  lede=lambda pf, n: f"大切な家族が亡くなったとき、{pf}でどこに頼めばいいか。民間のペット火葬場・霊園・納骨堂{n}か所と、市や区の受け付けを、公式サイトで確かめた内容だけでまとめました。お骨を返してもらえるか、家まで来てくれるかも書いています。",
  facts=_sougi_facts, faq=_sougi_faq, extra=_sougi_extra, before_title="火葬の種類と、えらぶときに確かめること",
  before=[("合同火葬", "ほかの子と一緒に火葬します。費用はおさえられますが、お骨は返らないことが多いです。"),
          ("個別火葬", "1頭ずつ火葬します。お骨を返してもらえます。スタッフにまかせる形と、家族が立ち会ってお骨を拾う「立ち会い火葬」があります。"),
          ("訪問火葬・お迎え", "火葬炉のある車で家の近くまで来る形や、家まで迎えに来て火葬場へ運ぶ形があります。近所への配慮や駐車の場所を確かめてください。"),
          ("料金の見方", "体重や大きさで料金が変わります。骨つぼ・お迎え・夜間の追加の費用が別になることもあるので、見積もりでたずねてください。"),
          ("市や区に頼むとき", "安い料金で受け付けている市区もありますが、お骨が返らない・立ち会えないことが多いです。受け付けの日時と持ちこみ方を、市区のページで確かめてください。")],
  taxi_h="火葬場や霊園への移動は、ペットタクシーで", taxi_p="車がないとき、家族と一緒に、家の前から火葬場や霊園の前まで移動できます。",
  links=[("ペットが亡くなったら（全国）", "/sougi/"), ("お別れの日の移動", "/guide/farewell/")])

# ── 夜間・救急の動物病院 ──
_NIGHT = gen_hospitals.CONDS[0]
_HOS = [dict(h, prefs=[pf]) for pf, lst in EMG["hospitals"].items() for h in lst]

import re
def _far(h): return bool(re.search(r"（[^）]+[都道府県]）$", h.get("city", "")))
def _night_facts(rs):
    far = sum(_far(h) for h in rs)
    out = [f"県の中にある夜間・救急の病院：{len(rs) - far}院"]
    if far: out.append(f"県の中に見つからないため、近くの県の病院も載せています：{far}院（所在地の県をカードに書いています）")
    return out

def _night_faq(pf, rs, n):
    names = "、".join(h["name"] for h in rs[:3])
    return [
     (f"{pf}で夜間に診てもらえる動物病院は？", f"この一覧では、{pf}で夜間・救急に診てもらえる動物病院を{n}院載せています（{names}{'など' if n > 3 else ''}）。受付時間は病院ごとに違うので、各カードでご確認ください。"),
     ("夜間の病院に行く前にすることは？", "まず電話で、症状・いつからか・動物の種類と体重を伝えて、受け入れてもらえるかを確かめてください。手術中や混雑で受けられないことがあります。"),
     ("夜間の診察の料金は？", "この一覧には料金を載せていません。夜間は時間外の料金が加わることが多いので、電話のときにたずねてください。"),
     ("夜中に病院まで行く車がないときは？", "緊急の搬送をしている会社に直接連絡できます。くわしくは「緊急のときの連絡先」のページをご覧ください。"),
    ]

NIGHT = dict(slug="hospital/night", name="夜間・救急の動物病院", unit="院", h1=_NIGHT["h1"], items=_HOS,
  card=lambda e, h: gen_hospitals.item_html(e, _NIGHT, h), checked=EMG["checked"], reviews=True, min=1,
  free="この一覧は無料の情報です。病院からお金をもらっていません。おすすめ順や点数順ではありません。料金や受け入れは、それぞれの病院に直接おたずねください。",
  title_word="夜間・救急の動物病院", title_tail="受付時間・所在地つき",
  desc_tail="病院の名前・受付時間・どんな病院か・所在地と公式サイトへのリンク、口コミの星を載せています。順位はつけていません。行く前に必ず電話で受け入れを確かめてください。",
  lede=lambda pf, n: f"夜中に具合が悪くなったとき、{pf}ではどこに行けばいいのか。夜間・救急に診てもらえる動物病院を{n}院、受付時間と一緒にまとめました。行く前に必ず電話で受け入れを確かめてください。",
  facts=_night_facts, faq=_night_faq, before_title="夜間の病院にかかるときに",
  before=[(t, d.replace('<a href="/emergency/">', "").replace('<a href="/#form">', "").replace('</a>', "")) for t, d in _NIGHT["tips"]],
  taxi_h="前もって決まっている通院は、ペットタクシーで", taxi_p="再診や退院のお迎えなど、前もって決まっている移動はペットタクシーを予約できます。",
  links=[("緊急のときの連絡先", "/emergency/"), ("条件でさがす動物病院", "/hospital/"), ("動物病院への通院の送迎ガイド", "/guide/hospital/")])

SOUGI["table"] = [("個別火葬", lambda f: "○" if _has(f, "個別火葬") else ""), ("立ち会い", lambda f: "○" if _has(f, "立ち会い火葬") else ""), ("お迎え", lambda f: "○" if _has(f, "お迎え") or _has(f, "訪問火葬") else ""), ("霊園", lambda f: "○" if _has(f, "霊園") else ""), ("納骨堂", lambda f: "○" if _has(f, "納骨堂") else ""), ("料金の例", lambda f: "○" if f.get("price") else "")]
NIGHT["table"] = [("受付時間", lambda h: h.get("hours", "")), ("所在地", lambda h: h.get("city", ""))]
