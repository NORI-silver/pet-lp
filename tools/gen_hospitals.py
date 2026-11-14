# お金を取らない情報ページ「条件でさがす動物病院」（/hospital/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「病院は？全部マネタイズじゃなくていい。SEO的なコンテンツでもいい」「全国で」「口コミもつけて」。
# 守ること：病院からお金をもらわない。順位や「おすすめ」をつけない。電話番号は載せない。公式サイトで確かめたことだけ書く。
# データ：夜間・救急＝tools/emergency.json（緊急タブと同じ）、往診・猫専門・エキゾチック・大型犬の設備＝tools/hospitals.json。
import json, os, re
import prefkeep

_EMGJ = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "emergency.json"), encoding="utf-8"))
_NNIGHT = len({h.get("id") or h["name"] for v in _EMGJ["hospitals"].values() for h in v})  # 近くの県にも出る病院は1つに数える
HOSP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospitals.json"), encoding="utf-8"))

# 条件ごとのページ。slug は /hospital/<slug>/
CONDS = [
 dict(slug="night", short="夜間・救急", h1="夜間・救急の動物病院", src="emg",
      # [B] SEO 11/8：表示21・クリックなし（15位）。数と「県を選ぶだけ」を先に出す。
      title=f"夜間・救急の動物病院 全国{_NNIGHT}院｜都道府県を選んで受付時間・所在地を一覧で確認",
      desc=f"夜間・休日に診てもらえる救急の動物病院を、全国47都道府県・{_NNIGHT}院から探せる無料の一覧です。都道府県を選ぶと、受付時間（何時まで受け付けるか）・所在地・どんな病院かと公式サイトへのリンクが出ます。行く前に必ず電話で受け入れを確かめてください。",
      lede="夜中に具合が悪くなったとき、どこに行けばいいのか。各地の夜間・救急の動物病院を、受付時間と一緒にまとめました。行く前に必ず電話で受け入れを確かめてください。",
      tips=[("まず電話を", "夜間の病院は手術中や混み合っていて受け入れられないことがあります。症状・いつからか・種類と体重・年齢を伝え、受け入れてもらえるか確かめてから出かけてください。"),
            ("持っていくもの", "かかりつけの診察券やお薬手帳、飲んでいる薬、吐いたものや便の写真、保険証があれば保険証。"),
            ("移動の手段がないとき", "<a href=\"/emergency/\">緊急の搬送をしている会社</a>に直接ご連絡ください。")]),
 dict(slug="visit", short="往診", h1="往診専門の動物病院（自宅に来てくれる）", src="visit",
      title="往診専門の動物病院｜自宅に来てくれる獣医さんを全国から探せる一覧（対応エリアつき）｜ペットタクシー予約窓口",
      desc="病院に連れて行くのがむずかしい老犬・大型犬・猫のために、自宅に来て診てくれる往診専門の動物病院を全国から探せます。往診の対応エリア・診てもらえる動物・受付時間と公式サイトへのリンクをまとめた無料の一覧です。",
      lede="寝たきりの子、車や病院が苦手な子、大型犬、多頭飼い。病院に連れて行くのがむずかしいとき、獣医さんに来てもらう選択肢があります。往診を専門にしている病院を、対応エリアと一緒にまとめました。",
      tips=[("往診でできること・できないこと", "診察・注射・点滴・採血・ワクチン・爪切り・看取りの相談などは自宅でできることが多いです。レントゲンや手術、入院が必要なときは病院を紹介されます。"),
            ("料金のしくみ", "多くの病院で「往診料（距離で変わる）＋診察や処置の料金」です。料金はここには書いていません。公式サイトか予約のときに確かめてください。"),
            ("検査や手術で病院へ行くとき", "往診の先生に紹介状を書いてもらい、検査や手術のできる病院を前もって予約しておくと安心です。")]),
 dict(slug="cat", short="猫専門", h1="猫専門の動物病院", src="cat",
      title="猫専門の動物病院｜猫だけを診る病院を全国から探せる一覧（診療時間つき）｜ペットタクシー予約窓口",
      desc="犬のいない待合室で、猫のことをよく知る先生に診てもらいたい。猫だけを診療している猫専門の動物病院を、全国から探せます。所在地・診療時間と公式サイトへのリンクをまとめた無料の一覧です。",
      lede="病院の待合室で犬に会うだけで固まってしまう子、病院が大の苦手な子。猫だけを診る病院なら、待合室も診察室も猫のためにつくられています。公式サイトに「猫専門」と書いている病院だけをまとめました。",
      tips=[("猫専門の病院のよいところ", "待合室に犬がいない、猫の体に合わせた道具や入院室がある、猫の病気（腎臓病・甲状腺・口内炎など）を多く診ている、といった点を各病院の公式サイトが挙げています。"),
            ("連れて行くとき", "キャリーは上が開くタイプだと、診察台に移すときの負担が少なくなります。家のにおいのついたタオルを入れ、キャリーに布をかけて外が見えないようにすると落ち着く子が多いです。"),
            ("移動がむずかしいとき", "キャリーの中で鳴き続ける子、電車が無理な子は、<a href=\"/guide/cat/\">猫の移動のガイド</a>も参考にしてください。")]),
 dict(slug="exotic", short="エキゾチックアニマル", h1="エキゾチックアニマルの専門の動物病院（うさぎ・鳥・爬虫類など）", src="exotic",
      title="エキゾチックアニマル専門の動物病院｜うさぎ・鳥・ハムスター・爬虫類を診てくれる病院を全国から探せる一覧｜ペットタクシー予約窓口",
      desc="うさぎ・鳥・ハムスター・フェレット・爬虫類などのエキゾチックアニマルを専門に診ている動物病院を、全国から探せます。診てもらえる動物・所在地・診療時間と公式サイトへのリンクをまとめた無料の一覧です。",
      lede="犬や猫の病院では診てもらえないことがある、うさぎ・鳥・ハムスター・フェレット・爬虫類。公式サイトにエキゾチックアニマルを専門に、あるいは中心に診ていると書いている病院だけをまとめました。診てもらえる動物の種類は病院ごとに違うので、行く前に確かめてください。",
      tips=[("連れて行く前に確かめること", "診てもらえる動物の種類（うさぎだけ、鳥と小動物だけ、など）と、予約が必要かどうか。多くの病院が予約制です。"),
            ("移動のとき", "小さな動物は温度の変化に弱いので、キャリーをタオルで包み、夏は保冷剤、冬はカイロを布ごしに。鳥はかごごと布でおおうと落ち着きます。"),
            ("遠くの病院に行くとき", "専門の病院は数が少なく、遠くまで行くことがあります。電車やバスに乗せられるかは、動物の種類と交通機関の決まりで変わるので、前もって確かめてください。")]),
 dict(slug="large", short="大型犬の設備", h1="大型犬の設備がある動物病院（大型犬用の入院室・診察台など）", src="large",
      title="大型犬の設備がある動物病院｜大型犬用の入院室・昇降式の診察台がある病院を全国から探せる一覧｜ペットタクシー予約窓口",
      desc="大型犬・超大型犬のために、大型犬用の入院室・診察室・昇降式や電動の診察台などの設備があると公式サイトに書いている動物病院を、全国から探せます。所在地・診療時間と公式サイトへのリンクをまとめた無料の一覧です。",
      lede="体の大きな子は、診察台に乗せるのも、入院室に入るのも一苦労。公式サイトに大型犬のための設備（大型犬用の入院室・広い診察室・昇降式の診察台など）があると書いている病院だけをまとめました。ほかの病院でも大型犬は診てもらえます。",
      tips=[("行く前に確かめること", "体重と犬種を伝え、入院や手術になったとき対応できるかを確かめておくと安心です。40kgを超える超大型犬は事前の相談を求める病院もあります。"),
            ("持ち上げられないとき", "歩けない大型犬は、大きめのバスタオルや毛布で担架のように2人で運べます。車への乗せおろしがむずかしいときは、<a href=\"/guide/large-dog/\">大型犬の移動のガイド</a>も参考に。"),
            ("通院の移動", "大型犬は電車やバスに乗れないことが多いので、通院の移動の方法を前もって決めておくと安心です。")]),
]

def _rows(cond, emg):
    """都道府県 → その県の病院の一覧。"""
    out = {}
    if cond["src"] == "emg":
        for pf, lst in emg["hospitals"].items():
            out[pf] = list(lst)
    else:
        for h in HOSP[cond["src"]]:
            for pf in h["prefs"]:
                out.setdefault(pf, []).append(h)
    return out

def item_html(e, cond, h):
    """1病院のカード。名前は公式サイトへのリンク。口コミの星は緊急タブと同じしくみ（/reviews.js）。"""
    spec = f'<small class="emg-spec">{e(h["spec"])}</small>' if h.get("spec") else ''
    extra = ''
    if cond["src"] == "visit":
        extra += f'<small>往診エリア：{e(h["area"])}</small><small>診てもらえる動物：{e(h["animals"])}</small>'
    elif h.get("animals"):
        extra += f'<small>診てもらえる動物：{e(h["animals"])}</small>'
    if h.get("addr"):
        extra += f'<small>所在地：{e(h["addr"])}</small>'
    # [C] 2026-11-14 公式サイトで確かめた項目（facts）をカードに。出どころと確認日つき
    fs = [f for f in h.get("facts", []) if f["k"] not in ("往診の地域", "対象の動物")]
    if fs:
        ck = max(f["checked"] for f in fs)
        extra += ('<dl class="hosp-facts">' + "".join(f'<dt>{e(f["k"])}</dt><dd>{e(f["v"])}</dd>' for f in fs)
                  + f'</dl><small class="hosp-src">公式サイトより（{int(ck[5:7])}月{int(ck[8:10])}日に確認）</small>')
    return (f'<div class="emg-item emg-co"><a href="{e(h["url"])}" target="_blank" rel="noopener"><b>{e(h["name"])}</b></a>'
            f'<small>{e(h["city"])}・{e(h["hours"])}</small>{spec}{extra}'
            + (f'<div class="emg-score" data-id="{e(h["id"])}"></div>' if h.get("review_query") else '')
            + (_taxi(h) if cond["src"] != "visit" else '') + _fac(e, cond, h) + '</div>')

def _fac(e, cond, h):
    # 施設ページ（試しの30院、tools/gen_facpages.py）がある病院は、カードからつなぐ
    if cond["src"] != "emg": return ''
    import gen_facpages
    x = next((y for y in gen_facpages.HOSPS if y["id"] == h.get("id")), None)
    return f'<a class="emg-taxi" href="{gen_facpages.hhref(x)}">{e(h["name"])}のくわしい情報（受付時間・料金・行き方）→</a>' if x else ''

def _taxi(h):
    # [B] 「この病院までのペットタクシー」：所在地を行き先に入れてフォームへ（2026-11-08）。往診は家に来るので付けない
    if not h.get("addr"): return ''
    from urllib.parse import quote
    return f'<a class="emg-taxi" href="/?to={quote(h["addr"])}#form">この病院までのペットタクシーの料金をくらべる →</a>'

def _night_answer(e, rows):
    """[C] 2026-11-14 Nori「動物病院の内容うすすぎ」：夜間の一覧のいちばん上に答えの箱（数は公式サイトで確かめた事実から数える）。"""
    import visual as _V, guides_hospital as _G
    hs = {h["id"]: h for v in rows.values() for h in v}
    hf = {x["id"]: x for x in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "night_hospital_facts.json"), encoding="utf-8"))["items"]
          if x.get("ok", True) and not x.get("closed") and x["id"] in hs}
    def has(x, k, pat): return any(f["k"] == k and re.search(pat, f["v"]) for f in x["facts"])
    n24 = sum(1 for h in hs.values() if "24時間" in h.get("hours", ""))
    eq = sum(1 for x in hf.values() if has(x, "設備", "CT|MRI"))
    card_only = sum(1 for x in hf.values() if has(x, "支払い方法", "原則クレジット|現金は使えない|現金のお取り扱いはしておりません|現金.*不可"))
    call = sum(1 for x in hf.values() if has(x, "来院前の連絡", "電話"))
    far = sum(1 for pf, v in rows.items() if v and all(re.search(r"（[^）]+[都道府県]）$", h.get("city") or "") for h in v))
    kv = [("夜間に診てもらえる動物病院は？", f"全国{len(hs)}院を都道府県ごとに載せています。下の都道府県をえらぶと、受付時間・所在地・公式サイトが出ます。県の中に見つからない{far}県は、近くの県の病院を載せています。"),
          ("夜間の診察料はいくら？", f"公式サイトに金額のある{_G.N_FEE}院では、基本の診察料のまん中が{_G.MED:,}円（税込にそろえて{_G.LO:,}〜{_G.HI:,}円）。検査や処置を合わせると2万〜5万円ほどが多いです。"),
          ("行く前にすることは？", f"必ず電話です。公式サイトを確かめた{len(hf)}院のうち{call}院が、来院前の電話を求めています。症状・いつから・種類・体重を伝えてください。")]
    tiles = [(f"{len(hs)}院", "公式サイトで確かめた夜間・救急の動物病院"), (f"{n24}院", "受付時間に「24時間」と書いている病院"),
             (f"{_G.MED:,}円", "夜間の基本の診察料のまん中（税込にそろえて）"), (f"{eq}院", "CT・MRIがあると書いている病院")]
    li = "".join(f'<li><b class="k">{e(q)}</b>{e(a)}</li>' for q, a in kv)
    return (f'<div class="art pp-ans"><div class="answer"><h2 id="answer">夜間・救急の動物病院のポイント</h2><ul class="kv">{li}</ul></div>{_V.stats(tiles)}'
            f'<p>クレジットカードだけで現金が使えないと書いている病院が{card_only}院あります。料金と、夜に受診したほうがいい症状は'
            f'<a href="/guide/night-vet-fee/">夜間の動物病院の料金の相場と、夜に受診したほうがいい症状</a>にまとめました。都道府県のページには、病院ごとの料金・対象の動物・設備・お支払い・駐車場をくらべる表があります。</p></div>')

def _visit_answer(e, rows):
    """[C] 2026-11-14 往診の一覧のいちばん上に答えの箱と、公式サイトで確かめた往診料・できること・できないことをくらべる表。"""
    import visual as _V
    hs = list({h["id"]: h for v in rows.values() for h in v}.values())
    fx = [h for h in hs if h.get("facts")]
    def fv(h, k): return next((f["v"] for f in h.get("facts", []) if f["k"] == k), "")
    ys = sorted(int(m.replace(",", "")) for h in fx for m in re.findall(r"([\d,]{4,})円", fv(h, "往診料"))[:1])
    mitori = sum(1 for h in fx if re.search("看取り|ターミナル|終末期|最期", fv(h, "家でできること")))
    exo = sum(1 for h in hs if re.search("うさぎ|ウサギ|鳥|ハムスター|フェレット|爬虫", (h.get("animals", "") + fv(h, "対象の動物"))))
    ng = sum(1 for h in fx if re.search("手術|レントゲン|入院", fv(h, "家でできないこと")))
    prefs = len([p for p, v in rows.items() if v])
    kv = [("往診の動物病院は？", f"全国{len(hs)}院を、{prefs}都道府県に分けて載せています。往診の地域は病院ごとに決まっているので、カードの「往診エリア」で家が入るかを確かめてください。"),
          ("往診料はいくら？", (f"公式サイトに金額のある病院では、往診料は{ys[0]:,}〜{ys[-1]:,}円ほど（無料の病院もあります）。距離で上がる病院が多く、ほかに診察料・検査・お薬の料金がかかります。" if len(ys) >= 2 else "病院ごとに違います。距離で上がる病院が多いです。")),
          ("家で何ができる？", f"診察・血液や尿の検査・注射・点滴・ワクチンなどは家でできる病院が多いです。手術・レントゲン・入院は家ではできないと書いている病院が{ng}院あり、そのときは設備のある病院を紹介してくれます。")]
    tiles = [(f"{len(hs)}院", "公式サイトで確かめた往診の動物病院"), (f"{len(fx)}院", "往診料・できることなどを公式サイトで確かめた病院"),
             (f"{mitori}院", "家での看取り・終末期のケアを書いている病院（確かめた病院のうち）"), (f"{exo}院", "犬・猫のほかの動物も診ると書いている病院")]
    li = "".join(f'<li><b class="k">{e(q)}</b>{e(a)}</li>' for q, a in kv)
    def cell(h, k): return e(fv(h, k)) or "—"
    tx = [h for h in fx if sum(1 for k in ("往診料", "受付時間", "家でできること", "家でできないこと", "支払い方法") if fv(h, k)) >= 3]
    rows_h = "".join(f'<tr><th scope="row">{e(h["name"])}<small>（{e(h["prefs"][0])}）</small></th><td>{cell(h, "往診料")}</td><td>{cell(h, "受付時間")}</td><td>{cell(h, "家でできること")}</td><td>{cell(h, "家でできないこと")}</td><td>{cell(h, "支払い方法")}</td></tr>' for h in tx)
    return (f'<div class="art pp-ans"><div class="answer"><h2 id="answer">往診の動物病院のポイント</h2><ul class="kv">{li}</ul></div>{_V.stats(tiles)}</div>'
            f'<div class="emg-tips" style="margin-top:0"><h4>往診料・家でできること・できないことをくらべる（{len(tx)}院）</h4>'
            '<p>公式サイトに書いてあることを写しました。金額は税込・税抜が病院ごとに違うので、そのままです。「—」は公式サイトに書いていない・見つからなかった項目です（「しない」という意味ではありません）。</p>'
            f'<table><thead><tr><th>病院</th><th>往診料</th><th>受付時間</th><th>家でできること</th><th>家でできないこと</th><th>お支払い</th></tr></thead><tbody>{rows_h}</tbody></table></div>')

def _cat_answer(e, rows):
    """[C] 2026-11-14 猫専門の一覧の上に答えの箱と、公式サイトで確かめた予約・猫にやさしい工夫・設備をくらべる表。"""
    import visual as _V
    hs = list({h["id"]: h for v in rows.values() for h in v}.values())
    fx = [h for h in hs if h.get("facts")]
    def fv(h, k): return next((f["v"] for f in h.get("facts", []) if f["k"] == k), "")
    gold = sum(1 for h in hs if re.search("ゴールド|GOLD|Gold", fv(h, "猫にやさしい工夫") + h.get("spec", "")))
    rsv = sum(1 for h in fx if re.search("予約制|予約優先", fv(h, "予約のしかた")))
    free = sum(1 for h in fx if re.search("予約なしで来院|予約なしでよい", fv(h, "予約のしかた")))
    park = sum(1 for h in fx if fv(h, "駐車場"))
    prefs = len([p for p, v in rows.items() if v])
    kv = [("猫専門の動物病院は？", f"全国{len(hs)}院を{prefs}都道府県に分けて載せています。猫だけを診る病院なので、待合室で犬に会うことがありません。"),
          ("予約はいる？", f"公式サイトを確かめた{len(fx)}院のうち{rsv}院が予約制か予約優先です。予約なしで行ける病院は{free}院。行く前に公式サイトか電話で確かめてください。"),
          ("猫にやさしい病院の目じるしは？", f"国際ねこ医学会（ISFM）の「キャット・フレンドリー・クリニック」の認定があります。最高位のゴールドと書いている病院は{gold}院です。")]
    tiles = [(f"{len(hs)}院", "公式サイトで確かめた猫専門の動物病院"), (f"{gold}院", "キャット・フレンドリー・クリニックのゴールド"),
             (f"{rsv}院", "予約制・予約優先と書いている病院"), (f"{park}院", "駐車場か駐車料金の負担を書いている病院")]
    li = "".join(f'<li><b class="k">{e(q)}</b>{e(a)}</li>' for q, a in kv)
    def cell(h, k): return e(fv(h, k)) or "—"
    tx = [h for h in fx if sum(1 for k in ("診療時間", "予約のしかた", "猫にやさしい工夫", "設備", "駐車場") if fv(h, k)) >= 3]
    rows_h = "".join(f'<tr><th scope="row">{e(h["name"])}<small>（{e(h["prefs"][0])}）</small></th><td>{cell(h, "休診日")}</td><td>{cell(h, "予約のしかた")}</td><td>{cell(h, "猫にやさしい工夫")}</td><td>{cell(h, "設備")}</td><td>{cell(h, "駐車場")}</td></tr>' for h in tx)
    return (f'<div class="art pp-ans"><div class="answer"><h2 id="answer">猫専門の動物病院のポイント</h2><ul class="kv">{li}</ul></div>{_V.stats(tiles)}</div>'
            f'<div class="emg-tips" style="margin-top:0"><h4>予約・猫にやさしい工夫・設備をくらべる（{len(tx)}院）</h4>'
            '<p>公式サイトに書いてあることを短くしました。「—」は公式サイトに書いていない・見つからなかった項目です（「ない」という意味ではありません）。</p>'
            f'<table><thead><tr><th>病院</th><th>休診日</th><th>予約</th><th>猫にやさしい工夫</th><th>設備</th><th>駐車場</th></tr></thead><tbody>{rows_h}</tbody></table></div>')

def render_cond(cond, ctx):
    """条件ページ1枚のHTML。ctx は gen_areas.py の関数と値（head, foot, e, area_links, SITE, EMG, emg_regions, emg_opts）。"""
    e, SITE = ctx["e"], ctx["SITE"]
    url = f'{SITE}/hospital/{cond["slug"]}/'
    rows = _rows(cond, ctx["EMG"])
    total = len({h["id"] for v in rows.values() for h in v})
    body = ''
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            hs = rows.get(pf, [])
            inner = ''.join(item_html(e, cond, h) for h in hs) or f'<p class="emg-none">{e(pf)}の{e(cond["short"])}の動物病院は、まだ載せていません。見つけしだい足します。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    tips = ''.join(f'<dt>{e(t)}</dt><dd>{d}</dd>' for t, d in cond["tips"])
    others = ''.join(f'<li><a href="/hospital/{c["slug"]}/">{e(c["short"])}の動物病院</a></li>' for c in CONDS if c["slug"] != cond["slug"])
    checked = ctx["EMG"]["checked"] if cond["src"] == "emg" else HOSP["checked"]
    ld = '<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
      {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
      {"@type":"ListItem","position":2,"name":"条件でさがす動物病院","item":SITE+"/hospital/"},
      {"@type":"ListItem","position":3,"name":cond["h1"],"item":url}]}, ensure_ascii=False, indent=1) + '\n</script>'
    return ctx["head"](cond["title"], cond["desc"], url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/hospital/">条件でさがす動物病院</a> › {e(cond["short"])}</nav>
    <h1><small>全国{total}件・都道府県でしぼりこめます</small>{e(cond["h1"])}</h1>
    <p class="lede">{e(cond["lede"])}</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    {_night_answer(e, rows) if cond["slug"] == "night" else _visit_answer(e, rows) if cond["slug"] == "visit" else _cat_answer(e, rows) if cond["slug"] == "cat" else ""}
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。病院からお金をもらっていません。順番は都道府県ごとで、おすすめ順や点数順ではありません。料金や受け入れは、それぞれの病院に直接おたずねください。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      <p class="emg-sum">ほかの条件：</p><ul class="other" style="justify-content:flex-start">{others}</ul>
      {body}
      <div class="emg-tips"><h4>{e(cond["short"])}の病院にかかるときに</h4><dl>{tips}</dl>
      <p class="emg-tips-note">ここに書いたのは一般的な心がけです。ペットの様子にあわせて、病院の指示にしたがってください。</p></div>
      <p class="emg-note">当サイトとは別の病院です（{e(checked)}に公式サイトで確かめた情報）。診療時間や対応は変わることがあるので、行く前・頼む前に必ずリンク先でご確認ください。口コミの星と本文は地図サービスから取り寄せたもので、当サイトの評価ではありません。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>病院への移動は、ペットタクシーで</h2><p>通院や退院のお迎えなど、前もって決まっている移動は、ペットタクシーを予約できます。当日の依頼もできます。</p></div>
    <ul class="other"><li><a href="/guide/hospital/">動物病院への通院の送迎ガイド</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{prefkeep.LIST_JS}
<script src="/reviews.js" defer></script>
""" + ctx["foot_noband"]()

def render_hub(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = SITE + "/hospital/"
    counts = {c["slug"]: len({h["id"] for v in _rows(c, ctx["EMG"]).values() for h in v}) for c in CONDS}
    # [B] 2026-11-03：都道府県ごとの病院の数の表（うちの一覧で数えたもの）。夜間は県のページへ、ほかは全国のページの県の絞り込みへ。
    from urllib.parse import quote
    import gen_dogrun
    per = {c["slug"]: _rows(c, ctx["EMG"]) for c in CONDS}
    trs = ''
    for lab, prefs in ctx["emg_regions"]:
        trs += f'<tr><th colspan="{len(CONDS) + 1}" style="text-align:left">{e(lab)}</th></tr>'
        for pf in prefs:
            tds = ''
            for c in CONDS:
                n = len(per[c["slug"]].get(pf, []))
                href = f'/hospital/night/{gen_dogrun.PSLUG[pf]}/' if c["slug"] == "night" else f'/hospital/{c["slug"]}/#pref={quote(pf)}'
                tds += f'<td><a href="{href}">{n}</a></td>' if n else '<td>—</td>'
            trs += f'<tr><td>{e(pf)}</td>{tds}</tr>'
    zero_night = [pf for _, prefs in ctx["emg_regions"] for pf in prefs if not any(not re.search(r"（[^）]+[都道府県]）$", h.get("city", "")) for h in per["night"].get(pf, []))]
    nh = [h for v in per["night"].values() for h in v]
    h24 = len({h["id"] for h in nh if "24時間" in h.get("hours", "")})
    summary = (f'<p>載せている夜間・救急の病院{counts["night"]}院のうち、受付時間に「24時間」と書いているのは{h24}院です。'
               + (f'県の中に夜間・救急の病院が見つからず、近くの県の病院を載せているのは{len(zero_night)}県（' + "・".join(zero_night) + '）です。' if zero_night else '')
               + "見つかった都道府県の数は、" + "、".join(f'{c["short"]}が{sum(1 for _, ps in ctx["emg_regions"] for pf in ps if per[c["slug"]].get(pf))}' for c in CONDS[1:]) + 'です。</p>')
    matrix = (f'<div class="sh" style="margin-top:28px"><h2>都道府県ごとの病院の数</h2></div>{summary}'
              '<div class="tbl"><table><thead><tr><th>都道府県</th>' + ''.join(f'<th>{e(c["short"])}</th>' for c in CONDS) + f'</tr></thead><tbody>{trs}</tbody></table></div>'
              '<p class="emg-note">数字は、この一覧に載せている病院の数です（公式サイトで確かめられた病院だけ）。0（—）でも、その県に病院がないとは限りません。夜間・救急の数には、県の中に見つからないときに載せている近くの県の病院をふくみます。</p>')
    cards = ''.join(f'<li><a href="/hospital/{c["slug"]}/"><b>{e(c["h1"])}</b><span>全国{counts[c["slug"]]}件。{e(c["lede"].split("。")[0])}。</span></a></li>' for c in CONDS)
    ld = '<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
      {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
      {"@type":"ListItem","position":2,"name":"条件でさがす動物病院","item":url}]}, ensure_ascii=False, indent=1) + '\n</script>'
    return ctx["head"]("条件でさがす動物病院（夜間・救急／往診／猫専門）｜全国47都道府県｜ペットタクシー予約窓口",
      "夜間・救急、自宅に来てくれる往診専門、猫だけを診る猫専門。条件に合う動物病院を全国47都道府県から探せる無料の一覧です。公式サイトで確かめた受付時間・所在地と、口コミの星をまとめています。", url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › 条件でさがす動物病院</nav>
    <h1><small>全国47都道府県・無料</small>条件でさがす動物病院</h1>
    <p class="lede">「夜中に診てくれる病院は？」「寝たきりだから家に来てほしい」「猫だけの病院がいい」。そんなときに、公式サイトで確かめた病院の一覧を条件ごとにまとめました。病院からお金はもらわず、順位もつけていません。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <ul class="gcards">{cards}</ul>
    {matrix}
    <p class="emg-note" style="margin-top:18px">それぞれのページで都道府県をしぼりこめます。まだ載っていない県や病院は、見つけしだい足していきます。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>病院への移動は、ペットタクシーで</h2><p>家の前から病院の前まで、飼い主さまと一緒に。お迎えの場所と行き先を入れると、条件に合う会社と料金の目安が出ます。</p></div>
    <ul class="other"><li><a href="/guide/hospital/">動物病院への通院の送迎ガイド</a></li><li><a href="/guide/senior/">シニア犬・シニア猫、介護中の子の移動</a></li><li><a href="/guide/cat/">猫の移動のガイド</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{prefkeep.LINKS_JS}
""" + ctx["foot_noband"]()

def review_rows():
    """口コミの場所を探すことば（booking/Code.gs の EMG_REVIEWS に足す）。"""
    return [h for k in ("visit", "cat", "exotic", "large") for h in HOSP[k] if h.get("review_query")]

def urls(SITE):
    return [SITE + "/hospital/"] + [f'{SITE}/hospital/{c["slug"]}/' for c in CONDS]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, "hospital"), exist_ok=True)
    open(os.path.join(ROOT, "hospital", "index.html"), "w", encoding="utf-8").write(render_hub(ctx))
    for c in CONDS:
        d = os.path.join(ROOT, "hospital", c["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render_cond(c, ctx))
