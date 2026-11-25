"""[E] うちの子に合うかで しぼる（Nori 2026-11-17「各カテゴリの絞り込みフィルターはもっと飼い主の気持ちになって考えて。自分の子にあてはまるものを探してるんだよ」）。

飼い主さんが自分の子について知っていること（どの動物・大きさ・シニアや介護・子犬子猫・薬や持病・2頭以上・かむ／ほえる／こわがり、
葬儀なら「夜中でも連絡できるか」「今日・明日に見送れるか」）を、施設の公式サイトに書いてある文（各データの文と、グループの公式サイトの文）から決める。
- 書いてあれば「合う」（key）、「お断り・不可・受けない」と同じ文にあれば「合わない」（no）。書いていなければ どちらにもしない（find.js が「公式サイトに書いていない」として後ろに回す）。
- 「相談」と書いてあるものは、受ける形があるので「合う」に入れる（ただし大きさの上限の「◯kgをこえると相談」は数字で決める）。
- 新しい言葉を作らない・盛らない。数字はデータの文の中の数字だけ。
uikit.py がカードの公式サイトのURLからデータをさがして、カードの data-k／data-no に足す。
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

# うちの子にあてはまるもの（飼い主さんの言い方で）
WHO = {
    "big": "大型犬（25kg以上）",
    "sen": "シニア・介護が必要",
    "pup": "子犬・子猫",
    "med": "薬・持病がある",
    "multi": "2頭以上いる",
    "shy": "かむ・ほえる・こわがり",
    "bed": "寝たきり",
    "night": "夜鳴き・認知症",
    "care": "介護が必要",
}
SHORT = {"big": "大型犬", "sen": "シニア・介護", "pup": "子犬・子猫", "med": "薬・持病", "multi": "2頭以上", "shy": "かむ・ほえる子", "bed": "寝たきり", "night": "夜鳴き・認知症", "care": "介護"}
# 分野ごとに聞くこと（順番もこのまま）。件数が少ない・ほぼ全部に当てはまるものは uikit が出さない
CAT_WHO = {
    "pet-hotel": ["big", "sen", "pup", "med", "multi", "shy"],
    "pet-sitter": ["big", "sen", "med", "multi"],
    "trimming": ["big", "sen", "pup", "shy", "med"],
    "dog-trainer": ["shy", "pup", "big", "multi"],
    "rojin-home": ["big", "bed", "night", "med", "care"],
    "sougi": ["big"],
}
# 施設の内容のキー（うちの子の条件ではなく、施設がしていること。uikit の SVC の「サービスの内容」に出す）。
# 判定は CAT_WHO と同じ _find（公式サイトの文・同じ文に「不可・お断り」があれば合わない）。
FAC = {
    "rojin-home": ["mitori", "long", "menkai", "pickup", "staff24", "medical"],
    "pet-hotel": ["cagefree", "walk", "longstay", "staff24", "smallonly"],
    "pet-sitter": ["cert", "stay", "sameday", "regular"],
    "trimming": ["bubun", "pickup", "nail", "ear"],
    "dog-trainer": ["private", "agility", "dance", "nosework", "disc", "competition", "seminar"],
}

# しつけ：困りごとから探す（施設の公式サイトの文に、その困りごとへの対応が明記してあるときだけ。Nori 2026-11-23 第2弾）
# 2026-11-24 全面改修で Space の採用条件（困りごとの細分化・猫の困りごと）まで広げた。判定は今までどおり公式サイトの文だけ。
# データ（trainers.json）に残っている文は「サービス・料金の要約」が中心で、困りごとの対応を書いた文はほぼ未収集。
# そのため大半のキーはまだ0件で、ボタンは件数の決まり（uikit の use）で出ない。文が集まれば自動で出る。
CONCERNS = {
    "bark": "無駄吠え", "bite": "噛みつき・噛み癖", "toilet": "トイレの失敗", "pull": "散歩の引っ張り",
    "basic": "基本の号令（お座り・待て）", "social": "社会化", "jump": "飛びつき", "leave": "分離不安・留守番ができない",
    "dogfear": "他の犬が苦手", "call": "呼び戻しができない", "care": "お手入れを嫌がる",
    "visitor": "来客・インターホンへの吠え", "ama": "甘噛み", "hiroi": "拾い食い",
    "hitogirai": "人が苦手・人見知り", "kowagari": "怖がり", "koufun": "興奮しやすい・落ち着きがない",
    "tossin": "リード中に他の犬へ吠える・突進する", "oikake": "追いかけ（自転車・人・猫）",
    "house": "ハウス・クレートに入れない", "kuruma": "車酔い・お出かけが苦手",
    "shokufun": "食糞", "marking": "マーキング", "itazura": "いたずら・物を壊す",
    "yonaki": "夜泣き（子犬）", "yoru": "老犬の夜鳴き・徘徊", "kodomo": "子どもとの接し方",
    "sosou": "粗相（トイレの失敗）", "tsumetogi": "爪とぎ", "spray": "スプレー（マーキング）",
    "nekonight": "夜鳴き・夜の運動会", "hikkaki": "噛む・引っかく",
}

NEG = r"(不可|お断り|断り|受けて(い)?ません|受けない|預から(ない|ず)|預かり(でき|出来)ません|対象外|ご遠慮|お受けできません|受け付けて(い)?ません|入所(でき|出来)(ない|ません)|NG)"
PAT = {
    "sen": r"シニア|老犬|老猫|高齢|介護",
    "pup": r"子犬|子猫|パピー|仔犬|仔猫",
    "med": r"投薬|服薬|お薬|飲み薬|薬を|持病|療養|てんかん|糖尿|腎臓|闘病|病気|治療中",
    "multi": r"多頭|複数頭|2頭以上|２頭以上|頭目|何頭でも|頭数",
    "shy": r"噛む|噛み|咬|攻撃性|吠え|臆病|怖がり|こわがり|神経質|問題行動|しつけ相談",
    "bed": r"寝たきり|全介助|歩行困難|立ち上がり困難|自力で(歩|立)|歩けな|歩行(でき|出来)な|起き上が(れな|ることができな)|立てな",
    "night": r"夜鳴き|夜泣き|認知症|徘徊",
    "care": r"介護",
    # 施設の内容（FAC）
    "mitori": r"看取り|看取",
    "long": r"終身|生涯|終生|長期",
    "menkai": r"面会",
    "cagefree": r"ケージフリー|ケージレス",
    "walk": r"散歩",
    # 施設の内容（FAC の続き）
    "pickup": r"送迎",
    "staff24": r"24時間(スタッフ|常駐|体制|在住|見守り|介護|お世話|対応)",
    "cert": r"資格保有|資格を保有|資格取得者|有資格|認定ペットシッター|ペットシッターの資格|資格を持",
    "bubun": r"部分(ケア|カット|コース|メニュー|のみ)|単品(メニュー|料金|OK|可)|爪切り(のみ|だけ|単品)",
    # しつけの困りごと（CONCERNS）
    "bark": r"無駄吠え|吠え癖|吠えすぎ|よく吠える",
    "bite": r"本気噛み|噛みつき|咬みつき|噛み癖|かみ癖",
    "toilet": r"トイレ",
    "pull": r"引っ張り|引っぱり",
    "basic": r"お座り|待て|伏せ|服従|基本(の)?(しつけ|トレーニング|訓練|コマンド)",
    "social": r"社会化|社会性",
    "jump": r"飛びつき|飛び付き|飛びつく",
    "leave": r"分離不安|留守番",
    "dogfear": r"他の犬|ほかの犬|犬同士|犬見知り|犬が苦手",
    "call": r"呼び戻し",
    "care": r"爪切り|歯磨き|ブラッシング|お手入れ|グルーミング",
    # 2026-11-24 追加の困りごと（Space の採用条件）。言葉は公式サイトで対応を書くときの言い方に寄せ、広すぎる言葉は入れない
    "visitor": r"来客|インターホン|チャイム|ピンポン|宅配",
    "ama": r"甘噛み|甘咬み|あま噛み|甘がみ",
    "hiroi": r"拾い食い",
    "hitogirai": r"人見知り|人が苦手|知らない人|対人",
    "kowagari": r"怖がり|こわがり|臆病|ビビり|音に敏感|雷を怖|花火を怖|雷が苦手|花火が苦手",
    "koufun": r"興奮しやすい|落ち着きがない|落ち着かせる|興奮",
    "tossin": r"突進|すれ違い|リードリアクティブ|他の犬に吠|ほかの犬に吠",
    "oikake": r"追いかけ|追い回",
    "house": r"ハウス|クレート",
    "kuruma": r"車酔い|乗り物酔い|車に弱い",
    "shokufun": r"食糞",
    "marking": r"マーキング",
    "itazura": r"いたずら|イタズラ|物を壊|家具をかじ|家具を噛",
    "yonaki": r"夜泣き",
    "yoru": r"夜鳴き|徘徊|認知症",
    "kodomo": r"子ども|子供|赤ちゃん|お子さま|お子様",
    "sosou": r"粗相",
    "tsumetogi": r"爪とぎ|爪研ぎ",
    "spray": r"スプレー|尿スプレー|尿マーキング",
    "nekonight": r"夜の運動会",
    "hikkaki": r"引っか|ひっか",
    # しつけの形（個別）。サービスの内容の軸に出す（uikit）
    "private": r"個別レッスン|個別対応|個別指導|個別トレーニング|マンツーマン|プライベートレッスン",
    # しつけ：種目・レッスンの種類（2026-11-25 追加。Nori「アジリティとかの要件もある」）
    "agility": r"アジリティ",
    "dance": r"ドッグダンス",
    "nosework": r"ノーズワーク",
    "disc": r"ディスクドッグ|フリスビー|ディスク競技",
    "competition": r"競技会|オビディエンス|服従訓練|大会出場",
    "seminar": r"セミナー|講座|勉強会",
    # ホテル：小型犬のみ（2026-11-25 追加。公式サイトの収集文から）
    "smallonly": r"小型犬(のみ|だけ|専用|限定)",
    # ホテル：長期・24時間（staff24 は下の既存パターンを共用）
    "longstay": r"長期",
    # シッター：泊まり・当日・定期
    "stay": r"お泊まり|泊まりの留守番|泊まり対応|宿泊対応",
    "sameday": r"当日(の|も)?(ご)?(予約|受付|対応|依頼|相談|申込)|当日予約|即日",
    "regular": r"定期(利用|契約|コース|のお世話|訪問|的)",
    # トリミング：部分ケアを分ける
    "nail": r"爪切り",
    "ear": r"耳掃除|耳そうじ",
    # 老犬ホーム：医療・投薬への対応（うちの子の「薬・持病がある」とは別。施設ができること）
    "medical": r"投薬|点滴|医療ケア|獣医師|訪問診療|服薬のお手伝い",
    "big": r"大型犬|超大型|ラブラドール|ゴールデン|大型",
    "a:small": r"うさぎ|ウサギ|小動物|ハムスター|フェレット|モルモット",
    "a:bird": r"小鳥|鳥類|インコ|文鳥|オウム|鳥さん|鳥など|鳥・",
    "a:exotic": r"爬虫類|カメ|トカゲ|ヘビ",
    "a:cat": r"猫|ねこ|ネコ",
    # 葬儀：いつ
    "call24": r"24時間",
    "today": r"亡くなった当日|当日(の|も)?(火葬|予約|受付|対応|お迎え|できる)|当日予約|最短即日|即日対応",
}
WHEN = {"call24": "夜中・早朝でも連絡できる（24時間受付）", "today": "今日・明日に見送りたい（当日も相談できる）"}

def _segs(t):
    return [s for s in re.split(r"[。\n／]|、(?=[^、]{0,4}(?:は|も))", t) if s.strip()]

def _find(t, key):
    """0＝書いていない、1＝合う、2＝合わない（同じ文に お断り・不可 など）。"""
    p = PAT[key]; hit = 0
    for s in _segs(t):
        m = re.search(p, s)
        if not m: continue
        if re.search(NEG, s[m.start():]) and not re.search(r"相談", s[m.start():]):
            return 2
        hit = 1
    return hit

def _maxkg(t):
    kg = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?:kg|ｋｇ|キロ)", t)]
    return max(kg) if kg else 0

def _text(rec, skip=("url", "u", "id", "review_query", "review_name", "src", "photo_ok", "trust")):
    out = []
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in skip: continue
                walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
        elif isinstance(x, str): out.append(x)
    walk(rec)
    t = "。".join(out)
    if isinstance(rec.get("trust"), dict):
        t += "。" + "。".join(v.get("quote", "") + v.get("v", "") for v in rec["trust"].values() if isinstance(v, dict))
    return t

def _norm(u):
    u = (u or "").strip().split("#")[0].split("?")[0]
    return re.sub(r"^https?://(www\.)?", "", u).rstrip("/").lower()

# グループの公式サイトに書いてあること（店ごとのページに書いていなくても、グループ全体の決まり）。2026-11-17 公式サイトの情報をもとに
CHAIN = {
    "SOS": {"keys": ["big", "multi", "a:small", "a:bird"],
            "src": "https://www.petsitter.co.jp/service/ ・ https://www.petsitter.co.jp/faq/",
            "quote": "犬（小型・中型・大型）や猫／多頭飼いで1時間ではお世話が終わらない場合は時間延長で対応／うさぎやハムスター、小鳥などの小動物のお世話も承っております"},
    "intopet": {"keys": ["sen", "a:small", "a:bird", "a:exotic"],
                "src": "https://intopet.jp/service/ ・ https://intopet.jp/faq/",
                "quote": "介護が必要なペットのサポートも行っていて／犬、猫、小動物、鳥、その他ペットのお世話にお伺いします"},
    "nihon": {"keys": ["sen", "a:small", "a:bird"],
              "src": "https://www.pet-ss.com/ ・ https://www.pet-ss.com/contents/category/faq/",
              "quote": "ペットの訪問介護／小動物、鳥類（インコ・小鳥）のお世話"},
}

FILES = {"pet-hotel": ("hotels.json", "hotels"), "pet-sitter": ("sitters.json", "sitters"), "trimming": ("grooming.json", "groomers"),
         "dog-trainer": ("trainers.json", "trainers"), "rojin-home": ("rojin.json", "homes"), "sougi": ("sougi_facilities.json", "facilities")}
_MAP = {}

def _load(cat):
    if cat in _MAP: return _MAP[cat]
    m = {}
    if cat in FILES:
        f, k = FILES[cat]
        recs = json.load(open(os.path.join(HERE, f), encoding="utf-8"))[k]
        if cat == "pet-hotel":
            # 公式サイトの収集文は別ファイル（hotels.json 本体が送信サイズの上限を超えるため。2026-11-26）
            wp = os.path.join(HERE, "hotels_web.json")
            if os.path.exists(wp):
                web = json.load(open(wp, encoding="utf-8"))
                for r in recs:
                    if r.get("id") in web: r["web"] = web[r["id"]]
        for r in recs:
            u = r.get("url") or r.get("u")
            if u: m.setdefault(_norm(u), r)
    _MAP[cat] = m
    return m

_CHAINS = {}
def _chain_note(cat, r):
    """グループ（チェーン）の公式サイトの説明文。店ごとの文にない、グループ全体の決まりを見るため。"""
    if cat != "pet-sitter": return ""
    if "sitters" not in _CHAINS:
        d = json.load(open(os.path.join(HERE, "sitters.json"), encoding="utf-8"))
        _CHAINS["sitters"] = d.get("chains", {})
    ch = _CHAINS["sitters"].get(r.get("chain"), {})
    return ch.get("note", "") if r.get("chain") != "indie" else ""

def keys(cat, url):
    """カードの公式サイトのURLから、(合うkey, 合わないkey) を返す。データにない施設は ([], [])。"""
    r = _load(cat).get(_norm(url))
    if not r: return [], []
    t = _text(r)
    note = _chain_note(cat, r)
    if note: t += "。" + note
    yes, no = [], []
    def put(k, v):
        if v == 1 and k not in yes: yes.append(k)
        elif v == 2 and k not in no: no.append(k)
    for k in CAT_WHO.get(cat, []):
        if k == "big":
            kg = r.get("max_kg") or 0
            if r.get("large"): put("big", 1)
            elif kg: put("big", 1 if kg >= 25 else 2)
            else:
                v = _find(t, "big")
                mk = _maxkg(t)
                if v == 0 and mk >= 30: v = 1
                put("big", v)
        else:
            put(k, _find(t, k))
    for k in FAC.get(cat, []):
        put(k, _find(t, k))
    if cat == "rojin-home":
        # 映像のライブ視聴は飼い主向けであることを、出典付きの専用項目で確認する。
        # 防犯カメラ、施設側の見守り、写真・動画の報告からは推定しない。
        live = r.get("care_evidence", {}).get("owner_live_camera", {})
        if live.get("src") and live.get("checked") and "dog" in live.get("animals", []):
            put("owner_live_dog", 1)
    if cat == "pet-hotel":
        # 体重帯（データに体重の上限 max_kg が書いてあるホテルだけ。上限が帯の上まであれば合う、上限が帯の下より小さければ合わない）
        kg = r.get("max_kg") or 0
        if kg:
            for k, lo_, hi in (("wb5", 0, 5), ("wb10", 5, 10), ("wb25", 10, 25)):
                if kg >= hi: put(k, 1)
                elif kg < lo_: put(k, 2)
    if cat == "dog-trainer":
        for k in CONCERNS: put(k, _find(t, k))
        if r.get("cert"): put("cert", 1)  # 公式サイトに資格・認定が書いてある（データの cert）
    if cat in ("sougi", "pet-sitter"):
        for k in ("a:small", "a:bird", "a:exotic"): put(k, _find(t, k))
    if cat == "sougi":
        for k in WHEN: put(k, _find(t, k))
        # 合同・返骨の組み合わせに限って非対応。個別火葬の返骨可否には影響させない。
        if r.get("group_returns_ashes") is False: put("合同火葬+お骨を返してもらえる", 2)
    if cat == "pet-sitter" and r.get("chain") in CHAIN:
        for k in CHAIN[r["chain"]]["keys"]:
            if k not in no: put(k, 1)
    return yes, [k for k in no if k not in yes]

# ── 譲渡：迎える人の心配（「60歳をこえていても、ひとり暮らしでも迎えられる？」）。公式ページの条件の文から ──
JOTO_WHO = {"older": "60歳以上・ひとり暮らし（支える人がいれば）"}
_OLD = re.compile(r"\d+歳以上|高齢|ひとり暮らし|一人暮らし|単身|独居|\d+歳(未満|以下|まで)")
_BACKUP = re.compile(r"誓約|同意書|保証人|引受|引き受け|後見|後継|承諾|了承|協力|支える|代わりに|準譲受人|身元|申立書|補助者|相談|飼える人|第2飼養|世話を頼める|サポート|にも譲渡|例外")
_STOP = re.compile(r"受けられない|できない|でない|不可|申し込めない|\d+歳(未満|以下|まで)")
_JOTO = {}

_JOTO_NEG = re.compile(r"(制度|仕組み|トライアル|お試し|譲渡会).{0,8}(ない|なし|できません|行って(い)?ません|実施して(い)?ません|やって(い)?ません)")

def _joto_flag(conds, rx):
    """1＝ある（条件の文に明記）、2＝ない（はっきり書いてある）、0＝書いていない。"""
    hit = 0
    for x in conds:
        for s in _segs(x):
            if not re.search(rx, s): continue
            if _JOTO_NEG.search(s): return 2
            hit = 1
    return hit

def joto_keys(url):
    if not _JOTO:
        for c in json.load(open(os.path.join(HERE, "joto.json"), encoding="utf-8"))["centers"]:
            _JOTO.setdefault(_norm(c.get("url")), c)
    c = _JOTO.get(_norm(url))
    if not c: return [], []
    yes, no = [], []
    conds = c.get("conds", [])
    for k, rx in (("event", r"譲渡会"), ("trial", r"トライアル|お試し(期間|飼育|預かり)")):
        v = _joto_flag(conds, rx)
        if v == 1: yes.append(k)
        elif v == 2: no.append(k)
    cs = [x for x in conds if re.search(r"[5-7]\d歳|高齢|ひとり暮らし|一人暮らし|単身|独居", x)]
    if any(_BACKUP.search(x) for x in cs): yes.append("older")
    elif any(_STOP.search(x) and re.search(r"[5-7]\d歳|ひとり暮らし|一人暮らし|高齢", x) for x in cs): no.append("older")
    return yes, [k for k in no if k not in yes]
