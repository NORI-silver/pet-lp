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
}
SHORT = {"big": "大型犬", "sen": "シニア・介護", "pup": "子犬・子猫", "med": "薬・持病", "multi": "2頭以上", "shy": "かむ・ほえる子", "bed": "寝たきり", "night": "夜鳴き・認知症"}
# 分野ごとに聞くこと（順番もこのまま）。件数が少ない・ほぼ全部に当てはまるものは uikit が出さない
CAT_WHO = {
    "pet-hotel": ["big", "sen", "pup", "med", "multi", "shy"],
    "pet-sitter": ["big", "sen", "med", "multi"],
    "trimming": ["big", "sen", "pup", "shy", "med"],
    "dog-trainer": ["shy", "pup", "big", "multi"],
    "rojin-home": ["big", "bed", "night", "med"],
    "sougi": ["big"],
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
        for r in json.load(open(os.path.join(HERE, f), encoding="utf-8"))[k]:
            u = r.get("url") or r.get("u")
            if u: m.setdefault(_norm(u), r)
    _MAP[cat] = m
    return m

def keys(cat, url):
    """カードの公式サイトのURLから、(合うkey, 合わないkey) を返す。データにない施設は ([], [])。"""
    r = _load(cat).get(_norm(url))
    if not r: return [], []
    t = _text(r)
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
    if cat in ("sougi", "pet-sitter"):
        for k in ("a:small", "a:bird", "a:exotic"): put(k, _find(t, k))
    if cat == "sougi":
        for k in WHEN: put(k, _find(t, k))
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

def joto_keys(url):
    if not _JOTO:
        for c in json.load(open(os.path.join(HERE, "joto.json"), encoding="utf-8"))["centers"]:
            _JOTO.setdefault(_norm(c.get("url")), c)
    c = _JOTO.get(_norm(url))
    if not c: return [], []
    cs = [x for x in c.get("conds", []) if re.search(r"[5-7]\d歳|高齢|ひとり暮らし|一人暮らし|単身|独居", x)]
    if any(_BACKUP.search(x) for x in cs): return ["older"], []
    if any(_STOP.search(x) and re.search(r"[5-7]\d歳|ひとり暮らし|一人暮らし|高齢", x) for x in cs): return [], ["older"]
    return [], []
