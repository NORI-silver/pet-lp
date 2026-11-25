# [B][A] 施設の一覧のカードを、写真の枠・要点のチップ・「こんな人に」・くわしくは折りたたみの形にそろえ、
# 一覧の上に「うちの子に合うところをさがす」を入れる（Nori 2026-11-15「施設紹介系がただ施設並べてるだけ。見づらい。写真もない」
# 「フィルターももっとあったほうがいい」「自分の犬や猫とかにマッチするものを探したいはず」）。
#
# gen_areas.py の最後（tables.py のあと）に、できあがったページの .emg-item.emg-co を作りかえる後処理。何度動かしても同じ。
# - 生成側（gen_*.py）は今までどおり <div class="emg-item emg-co"><a href=公式><b>名前</b></a><small>ラベル：値</small>…</div> を出すだけでよい。
# - 写真：カードの左上の枠。最初は名前の1文字（その施設だけの印。ほかの写真は借りない）。<div class="emg-score" data-id> がある施設は、
#   枠の「写真」を押すと地図サービスの写真（撮った人の名前と出どころつき）を取り寄せて枠に入れる（reviews.js）。
# - 合う・合わない：データ（公式サイトの情報）から data-fit を作る。書いていないことは「要確認」で、「しない」ではない。
#   生成側で決めたいときは fit_attr(...) の戻り値を div に足す（あればそれを使う）。
# - 文字は消さない・隠さない（くわしくは <details> の中。検索・AIにも読める）。電話番号・順位・点数順はなし。
import os, re, json, html, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))

# 分野ごとの設定。kinds＝「どの子？」に出す動物、size＝大きさ（犬）を聞く、senior／puppy＝シニア・介護／子犬を聞く
CATS = {
    "dog-trainer": dict(key="trainer", noun="しつけ教室", icon="dog", kinds=["dog"], puppy=True, label="ドッグトレーナー・しつけ教室"),
    "pet-sitter": dict(key="sitter", noun="ペットシッター", icon="home", kinds=["dog", "cat", "small", "bird"], label="ペットシッター"),
    "rojin-home": dict(key="rojin", noun="老犬ホーム", icon="home", kinds=["dog", "cat"], size=True, label="老犬ホーム・老猫ホーム"),
    "trimming": dict(key="trimming", noun="トリミング", icon="scissors", kinds=["dog", "cat"], size=True, senior=True, label="出張トリミング・トリミングサロン"),
    "pet-hotel": dict(key="hotel", noun="ペットホテル", icon="bed", kinds=["dog", "cat"], size=True, senior=True, label="ペットホテル"),
    "sougi": dict(key="sougi", noun="ペット火葬・霊園", icon="flower", kinds=[], label="ペット火葬・霊園"),
    "hospital": dict(key="hospital", noun="動物病院", icon="cross", kinds=["dog", "cat", "small", "bird", "exotic"], size=True, label="動物病院"),
    "joto": dict(key="joto", noun="譲渡の窓口", icon="heart", kinds=["dog", "cat"], want=True, label="譲渡の窓口・保護団体"),
}
DIRS = set(CATS)
# 写真をカードが画面に近づいたら自動で取り寄せるか（false＝「写真を見る」を押したときだけ。地図サービスの写真は1枚ごとに利用料がかかる。Nori の決定で切りかえ）
PHOTO_AUTO = False
KIND_LABEL = {"dog": "犬", "cat": "猫", "small": "うさぎ・小動物", "bird": "鳥", "exotic": "爬虫類など"}

# ---- アイコン（線だけのSVG。文字の代わりにしない＝いつも横に文字がある） ----
_P = {
    "pin": '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
    "yen": '<path d="M6 4l6 8 6-8M12 12v8M7.5 13h9M7.5 16.5h9"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "paw": '<circle cx="7" cy="9" r="1.8"/><circle cx="11" cy="6.2" r="1.8"/><circle cx="15.2" cy="7" r="1.8"/><circle cx="18" cy="11" r="1.7"/><path d="M8.5 17c0-2.6 2-4.8 4.3-4.8s4 2 4 4.1c0 1.7-1.3 2.7-2.9 2.7-1.1 0-1.7-.5-2.6-.5s-1.4.6-2.4.6c-1.2 0-.4-.9-.4-2.1z"/>',
    "car": '<path d="M4 15.5l1.6-5a2 2 0 0 1 1.9-1.4h9a2 2 0 0 1 1.9 1.4l1.6 5v3h-16z"/><circle cx="8" cy="15.5" r="1.3"/><circle cx="16" cy="15.5" r="1.3"/>',
    "badge": '<path d="M12 3l2.4 1.8 3-.1.9 2.9 2.4 1.8-.9 2.8.9 2.8-2.4 1.8-.9 2.9-3-.1L12 21l-2.4-1.8-3 .1-.9-2.9-2.4-1.8.9-2.8-.9-2.8 2.4-1.8.9-2.9 3 .1z"/><path d="M9 12l2 2 4-4"/>',
    "list": '<path d="M9 7h11M9 12h11M9 17h11"/><circle cx="5" cy="7" r=".9"/><circle cx="5" cy="12" r=".9"/><circle cx="5" cy="17" r=".9"/>',
    "dog": '<path d="M5 9l1-4 3 2h6l3-2 1 4v4a7 7 0 0 1-14 0z"/><circle cx="9.5" cy="12" r=".8"/><circle cx="14.5" cy="12" r=".8"/><path d="M11 15.5h2"/>',
    "home": '<path d="M4 11l8-6.5 8 6.5M6.5 9.5V19h11V9.5"/><path d="M10 19v-4.5h4V19"/>',
    "scissors": '<circle cx="6.5" cy="7" r="2.5"/><circle cx="6.5" cy="17" r="2.5"/><path d="M8.6 8.4L19 17M8.6 15.6L19 7"/>',
    "bed": '<path d="M3 18V7M3 14h18v4M21 14v-2.5a3 3 0 0 0-3-3h-7v5.5"/><circle cx="7" cy="11" r="1.8"/>',
    "flower": '<circle cx="12" cy="9" r="2"/><path d="M12 7c0-3 3-3 3-.5S12 9 12 9s-3-1.5-3-2.5S12 4 12 7zM12 11v9M12 16c-2-2.5-5-2-5-2s1 3 5 3M12 16c2-2.5 5-2 5-2s-1 3-5 3"/>',
    "cross": '<rect x="4" y="4" width="16" height="16" rx="4"/><path d="M12 8v8M8 12h8"/>',
    "heart": '<path d="M12 19s-7-4.4-7-9.3A3.9 3.9 0 0 1 12 7.6a3.9 3.9 0 0 1 7 2.1C19 14.6 12 19 12 19z"/>',
    "cam": '<path d="M4 8h3l1.5-2h7L17 8h3v11H4z"/><circle cx="12" cy="13" r="3.3"/>',
    "user": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-3.9 3.1-7 7-7s7 3.1 7 7"/>',
    "family": '<circle cx="8" cy="7.5" r="2.6"/><circle cx="16.5" cy="9" r="2.1"/><path d="M3.5 19c0-3 2-5.5 4.5-5.5s4.5 2.5 4.5 5.5M13 19c0-2.4 1.6-4.4 3.5-4.4s3.5 2 3.5 4.4"/>',
    "book": '<path d="M12 6.5C10 5 7 4.5 4 5v13c3-.5 6 0 8 1.5 2-1.5 5-2 8-1.5V5c-3-.5-6 0-8 1.5zM12 6.5v13"/>',
    "repeat": '<path d="M5 11V9a3 3 0 0 1 3-3h10M15 3l3 3-3 3M19 13v2a3 3 0 0 1-3 3H6M9 21l-3-3 3-3"/>',
    "door": '<path d="M6 21V4h10v17M4 21h16"/><circle cx="13" cy="12.5" r=".9"/>',
    "cal": '<rect x="4" y="5.5" width="16" height="14" rx="2"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/>',
    "bag": '<path d="M5 9h14l-1 11H6zM9 9V7a3 3 0 0 1 6 0v2"/>',
    "check": '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 12.3l2.3 2.3 4.7-4.8"/>',
    "map": '<path d="M9 5l-5 2v12l5-2 6 2 5-2V5l-5 2zM9 5v12M15 7v12"/>',
}
def icon(n, cls="fc-i"):
    # 形はページに1回だけ（SPRITE）。カードからは名前で呼ぶ（ページを軽くするため）
    return f'<svg class="{cls}" aria-hidden="true" focusable="false"><use href="#fci-{n}"/></svg>'
_BASE = {"pin", "yen", "clock", "paw", "car", "badge", "list", "dog", "home", "scissors", "bed", "flower", "cross", "heart", "cam"}
def sprite_for(h):
    """ページで使う形だけを入れる（ページを軽くするため）"""
    used = set(re.findall(r'href="#fci-([a-z]+)"', h)) | _BASE  # もとからの形はいつも入れる（あとから足すカードがある）
    return ('<svg width="0" height="0" style="position:absolute" aria-hidden="true">' +
            "".join(f'<symbol id="fci-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in _P.items() if k in used) + '</svg>')
SPRITE = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true">' +
          "".join(f'<symbol id="fci-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in _P.items()) + '</svg>')

# ---- ラベルの分け方 ----
_AREA = re.compile(r"エリア|地域|往診|出張|対応")
_ADDR = re.compile(r"所在地|住所|場所|教室")
_PRICE = re.compile(r"料金|費用|手数料|金額")
_TIME = re.compile(r"時間|受付|営業|定休|休み")
_ANIM = re.compile(r"動物|受け入れ")
_CERT = re.compile(r"資格|登録|認定")
_CAREER = re.compile(r"^トレーナー歴$")  # [B] 11/16 Nori「ドッグトレーナー歴とか」：公式サイトに年数・開業年が書いてある教室だけ
_SVC = re.compile(r"^(提供内容|内容|できること|サービス)$")

# 条件の印（data-flags）を、カードのチップと「こんな人に」の言葉にする（公式サイトの情報から作った印だけ）
FLAG_CHIP = {
    "large": "大型犬OK", "cat_only": "猫専用", "cat": "猫OK", "vet": "病院が併設", "pickup": "送迎あり", "senior": "シニア・介護OK",
    "night_staff": "夜もスタッフ", "camera": "カメラで見守り", "run": "ドッグラン", "private_room": "個室", "car": "トリミングカー", "in_home": "家の中で", "shop": "お店で（サロン）",
}
FOR_TEXT = {
    # 印・タグ → こんな人に（短く。言い切りすぎない）
    "large": "大型犬の子", "cat_only": "犬の声が苦手な猫", "senior": "シニアや持病のある子", "pickup": "送り迎えしてほしい人",
    "vet": "病院が近いと安心な人", "camera": "留守中も様子を見たい人", "private_room": "静かな個室がいい子", "run": "体を動かしたい子",
    "night_staff": "夜も人がいると安心な人", "car": "家の前でトリミングしたい人", "in_home": "家の中でしてほしい人", "shop": "近くのお店に連れていける人",
    "出張・訪問": "家での困りごとを家で見てほしい人", "教室・グループ": "ほかの犬と一緒に練習したい人", "パピー": "子犬を迎えたばかりの人", "問題行動": "吠え・かみ癖に困っている人",
    "幼稚園・保育園": "日中あずけて社会性を育てたい人", "預かり訓練": "まとめて預けて練習したい人", "オンライン": "近くに教室がない人",
    "猫": "猫を家で留守番させたい人", "小動物": "うさぎ・小動物の飼い主", "鳥": "鳥の飼い主", "散歩": "散歩も頼みたい人",
    "個別火葬": "お骨を返してほしい人", "立ち会い": "最後まで見送りたい人", "お迎え・訪問火葬": "家まで来てほしい人", "霊園・納骨": "納骨の場所もさがしている人",
}

# ---- 公式サイトの情報から「合う・合わない」のデータを作る ----
def fit_attr_str(d):
    """data-fit をシングルクォートで書く（値はDOM上まったく同じ。JSONの " を &quot; にしない分だけ小さくなる）。& ' < > は必ずエスケープする。"""
    v = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    v = v.replace("&", "&amp;").replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")
    return " data-fit='" + v + "'"

def fit_attr_values(h):
    """HTMLの中の data-fit の値（ダブル・シングルどちらの書き方でも）を取り出す。"""
    return [html.unescape(a or b) for a, b in re.findall(r'data-fit="([^"]*)"|data-fit=\'([^\']*)\'', h)]

def fit_single_quote(h):
    """ダブルクォートで書かれた data-fit を、同じ値のままシングルクォートの書き方にそろえる（DOM上の値は変わらない。& ' < > はエスケープ）。"""
    def sub(m):
        v = html.unescape(m.group(1))
        v = v.replace("&", "&amp;").replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")
        return " data-fit='" + v + "'"
    return re.sub(r' data-fit="([^"]*)"', sub, h)

def fit_attr(animals=None, only=False, sizes=None, max_kg=None, senior=None, puppy=None, animals_text="", fee=False):
    """生成側からカードに足す属性（' data-fit="…"'）。書いていないことは渡さない（＝要確認）。"""
    d = {}
    if animals: d["a"] = list(dict.fromkeys(animals))
    if animals and only: d["o"] = 1
    if animals_text: d["at"] = animals_text
    if sizes: d["s"] = list(dict.fromkeys(sizes))
    if max_kg: d["kg"] = max_kg
    if senior: d["sen"] = 1
    if puppy: d["pup"] = 1
    if fee: d["fee"] = 1
    if not d: return ""
    return fit_attr_str(d)


def _fee_of(r):
    """料金が数字で分かるか（facts の「料金」に金額がある）。"""
    return any(isinstance(f, dict) and f.get("k") == "料金" and f.get("yen") for f in (r.get("facts") or []))


def _sizes_in(t):
    """公式サイトの文から受けられる大きさを読む（大型犬の受け入れが書いてあるか中心。お断りの文は除く）。"""
    if re.search(r"大型犬[^、。]{0,4}(不可|お断り|NG|対象外)", t): return None
    if re.search(r"大型犬|大型の犬|25kg", t): return ["s", "m", "l"]
    if re.search(r"中型犬(まで|以下|〜|まで可)", t): return ["s", "m"]
    if re.search(r"小型犬(のみ|だけ|専門|限定)", t): return ["s"]
    return None

def _kinds_in(t):
    a = []
    if re.search(r"犬|ドッグ|わんちゃん", t): a.append("dog")
    if re.search(r"猫|キャット", t): a.append("cat")
    if re.search(r"小動物|うさぎ|ウサギ|ハムスター|フェレット|モルモット|チンチラ", t): a.append("small")
    if re.search(r"鳥|インコ|オウム", t): a.append("bird")
    if re.search(r"エキゾ|爬虫|は虫|カメ|トカゲ|ヘビ", t): a.append("exotic")
    return a

def rojin_only(a, t):
    """「要確認」「記載なし」「など」は他の動物を断った印にしない。"""
    return bool(a) and "など" not in t and not re.search(r"要確認|記載なし", t)

def _load(name):
    try: return json.load(open(os.path.join(HERE, name), encoding="utf-8"))
    except Exception: return None

def _fit_table():
    """分野ごとに、名前 → data-fit の文字列。"""
    import facility_cards as FC
    T = {k: {} for k in ("trainer", "sitter", "rojin", "trimming", "hotel", "hospital")}
    tr = _load("trainers.json") or {}
    for t in tr.get("trainers", []):
        tags = FC.trainer_tags(t)
        ttxt = (t.get("services") or "") + " " + " ".join(f.get("v", "") for f in (t.get("facts") or []) if isinstance(f, dict))
        T["trainer"][t["name"]] = fit_attr(["dog"], True, _sizes_in(ttxt), puppy=bool({"パピー", "幼稚園・保育園"} & set(tags)), animals_text="犬", fee=_fee_of(t))
    si = _load("sitters.json") or {}
    for s in si.get("sitters", []):
        ch = si.get("chains", {}).get(s.get("chain"), {})
        txt = (s.get("animals") or "") + (" " + ch.get("note", "") if s.get("chain") != "indie" else "")
        a = _kinds_in(txt)
        only = bool(re.search(r"専門|のみ|専用|だけ", s.get("animals") or ""))
        if s.get("no_new_dog"):
            a = [k for k in _kinds_in(s.get("animals", "")) if k != "dog"]
            only = True
        stxt = txt + " " + " ".join(f.get("v", "") for f in (s.get("facts") or []) if isinstance(f, dict))
        if a: T["sitter"][s["name"]] = fit_attr(a, only, _sizes_in(stxt), animals_text="・".join(KIND_LABEL[k] for k in a), fee=_fee_of(s))
    ro = _load("rojin.json") or {}
    for h in ro.get("homes", []):
        t = h.get("animals", "")
        a = _kinds_in(t)
        if "猫は受けていません" in t: a = [k for k in a if k != "cat"]
        sizes, kg = None, None
        if "小型犬5kg未満" in t: sizes = ["s"]
        elif re.search(r"大型|小型・中型・大型", t): sizes = ["s", "m", "l"]
        m = re.search(r"(\d+)kgまで", t)
        if m: kg = int(m.group(1))
        T["rojin"][h["name"]] = fit_attr(a, rojin_only(a, t), sizes, kg, senior=True, animals_text="・".join(KIND_LABEL[k] for k in a), fee=_fee_of(h))
    gr = _load("grooming.json") or {}
    for g in gr.get("groomers", []):
        a = ["dog"] + (["cat"] if g.get("cat") else [])
        T["trimming"][g["name"]] = fit_attr(a, False, ["s", "m", "l"] if g.get("large") else None, g.get("max_kg"), g.get("senior"), fee=_fee_of(g))
    ho = _load("hotels.json") or {}
    for h in ho.get("hotels", []):
        if h.get("cat_only"): a, only = ["cat"], True
        else: a, only = ["dog"] + (["cat"] if h.get("cat") else []), False
        T["hotel"][h["name"]] = fit_attr(a, only, ["s", "m", "l"] if h.get("large") and not h.get("cat_only") else None, h.get("max_kg"), h.get("senior"),
                                         animals_text="猫だけ" if h.get("cat_only") else "", fee=_fee_of(h))
    hp = _load("hospitals.json") or {}
    for kind in ("visit", "cat", "exotic", "large"):
        for h in hp.get(kind, []):
            t = h.get("animals", "")
            a = _kinds_in(t)
            T["hospital"][h["name"]] = fit_attr(a, bool(a) and not re.search(r"など|ほか|その他|相談", t), ["s", "m", "l"] if kind == "large" else None,
                                                animals_text=t[:40], fee=_fee_of(h))
    return T

# ---- カードを1枚ずつ作りかえる ----
_OPEN = re.compile(r'<div class="emg-item emg-co(?: [^"]*)?"[^>]*>')
_TAGRX = re.compile(r"<(/?)(div|section|details|ul|dl|p|small|a|span)\b[^>]*>", re.I)

def _end(h, i, tag):
    """h[i] から始まる <tag> の対応する閉じタグの後ろの位置。"""
    depth = 0
    for m in re.finditer(rf"<(/?){tag}\b[^>]*>", h[i:], re.I):
        if m.group(0).endswith("/>"): continue
        depth += -1 if m.group(1) else 1
        if depth == 0: return i + m.end()
    return len(h)

def _children(inner):
    """カードの中身を、いちばん外側の要素ごとに分ける。"""
    out, i = [], 0
    while i < len(inner):
        m = re.match(r"\s*<([a-zA-Z0-9]+)\b[^>]*>", inner[i:])
        if not m:
            j = inner.find("<", i + 1)
            j = len(inner) if j < 0 else j
            t = inner[i:j]
            if t.strip(): out.append(("#text", t))
            i = j
            continue
        tag = m.group(1).lower()
        s = i + m.start(0) + (len(m.group(0)) - len(m.group(0).lstrip()))
        e = _end(inner, s, tag) if tag not in ("br", "img", "hr", "input") else s + len(m.group(0).strip())
        out.append((tag, inner[s:e]))
        i = e
    return out

def _txt(x): return html.unescape(re.sub(r"<[^>]+>", "", x)).strip()

def _mono(name):
    n = re.sub(r"^[\s「『（(【\[〈《\"'・]+", "", name)
    ch = n[:1] or "・"
    return ch.upper()

def _hue(name):
    return int(hashlib.md5(name.encode("utf-8")).hexdigest()[:4], 16) % 360

def _split_items(v):
    """「、」「・」などで区切る。かっこの中では区切らない（「ペットホテル（犬・猫）」を1つのまま）。"""
    out, cur, depth = [], "", 0
    for c in v:
        if c in "（(「『【": depth += 1
        elif c in "）)」』】": depth = max(0, depth - 1)
        if depth == 0 and c in "、,，／/・":
            out.append(cur); cur = ""; continue
        cur += c
    out.append(cur)
    return [x.strip() for x in out if x.strip()]

def _short(lab):
    return re.sub(r"[（(].*?[）)]", "", lab).strip() or lab

_PREF_RX = re.compile(r"^(東京都|北海道|(?:京都|大阪)府|[^\s都道府県]{2,3}県)")
DEPTS = [  # 診療科目（ほかの病院さがしのサイトでよく選べるもの）。公式サイトの言い方 → 選ぶ欄の名前
    ("皮膚科", r"皮膚|アレルギー"), ("眼科", r"眼"), ("歯科", r"歯|口腔"), ("耳鼻科", r"耳"), ("整形外科", r"整形|骨|関節"),
    ("腫瘍科", r"腫瘍|がん|癌"), ("循環器科", r"循環|心臓"), ("神経科", r"神経|脳"), ("腎臓・泌尿器", r"泌尿|腎"), ("消化器科", r"消化|内視鏡|胃腸"),
    ("呼吸器科", r"呼吸"), ("内分泌科", r"内分泌|ホルモン|甲状腺|糖尿"), ("行動診療", r"行動"), ("東洋医学", r"鍼|はり|漢方|東洋"),
    ("CT・MRI", r"CT|ＣＴ|MRI|ＭＲＩ"), ("健康診断", r"健康診断|健診|ドック"),
]
def depts_of(v):
    return [n for n, rx in DEPTS if re.search(rx, v)]

_FT_ORDER = ["24時間", "夜も", "日曜も", "駐車場", "カード払い", "来てくれる・送迎", "料金を公開"]

def features(rows, rest, chips):
    """カードに書いてあることから、しぼりこみの印を作る（書いていないカードには付けない＝しぼると外れる）。"""
    f = []
    tm = " ".join(v for l, v, _ in rows if _TIME.search(l) and not re.search(r"休", l)) + " " + rest
    if re.search(r"24時間", tm): f.append("24時間")
    if re.search(r"翌|2[0-3]時|2[0-3]:\d\d|24時間|夜間|深夜", tm): f.append("夜も")
    hol = [v for l, v, _ in rows if re.search(r"休", l)]
    if hol and not any(re.search(r"日曜|日・|日祝|日、|・日|^日|、日|日$|不定", v) for v in hol): f.append("日曜も")
    for l, v, _ in rows:
        if re.search(r"駐車", l) and not re.search(r"なし|ありません|^0|ない", v): f.append("駐車場")
        if re.search(r"支払", l) and re.search(r"カード|クレジット|キャッシュレス", v) and not re.search(r"不可|使えない|できない", v): f.append("カード払い")
        if re.search(r"ほかにしていること|併設", l): f += [x for x in _split_items(v) if 2 <= len(x) <= 8 and not re.search(r"駐車|パーキング|（", x)]
        if _PRICE.search(l): f.append("料金を公開")
    if any(re.search(r"送迎|出張|訪問|お迎え|往診", c) for c in chips): f.append("来てくれる・送迎")
    return [x for x in _FT_ORDER if x in f] + [x for x in dict.fromkeys(f) if x not in _FT_ORDER]

def cred_chips(val):
    """資格・登録の行 → 緑のチェックの札（ショッピング広告の注記のように）。登録番号の項目は「動物取扱業の登録あり」1つにまとめる。"""
    items, reg = [], False
    for x in re.split(r"[、,，]", val):
        x = x.strip()
        if not x: continue
        if re.match(r"(第一種動物取扱業|動物取扱業|登録)", x) or re.search(r"第?[0-9０-９\-－]+号", x):
            reg = True; continue
        items.append(x)
    if reg: items.append("動物取扱業の登録あり")
    out = []
    for x in dict.fromkeys(items):
        note = cred_note(x)
        out.append(f'<span class="crd" tabindex="0" role="button" aria-label="{html.escape(x)}の説明"><span class="cr">{html.escape(x)}</span><span class="crx">{html.escape(note)}</span></span>' if note
                   else f'<span class="cr">{html.escape(x)}</span>')
    return "".join(out)

# 資格の札を押したときの1行の説明（2026-11-16 Nori「どういう基準でえらべばいいかわからん。いろんな資格があるから」）。
# 中身は各団体の公式ページの説明だけ（くわしくは記事 /guide/choose-dog-trainer/ の表。出どころもそこ）。
CRED_NOTES = [
 (r"CPDT|CCPDT", "米国の認定団体 CCPDT の資格。300時間以上の指導経験のうえで試験に合格し、3年ごとに更新します。"),
 (r"JAHA", "日本動物病院協会の認定。養成コースのあと、筆記・面接と、ごほうびで教える実技の試験があります。"),
 (r"JKC.*訓練士|公認訓練士（JKC", "ジャパンケネルクラブの公認資格。自分で訓練した犬を試験に合格させた実績が要り、6つの段階があります。"),
 (r"JKC愛犬飼育管理士", "ジャパンケネルクラブの、犬の飼い方の知識の資格です。"),
 (r"警察犬協会", "日本警察犬協会の公認資格。警察犬の訓練から始まった資格で、等級があります。"),
 (r"愛玩動物看護師", "2022年にできた国家資格。獣医師の指示のもとで動物の看護をする資格で、しつけ専門の資格ではありません。"),
 (r"愛玩動物飼養管理士", "日本愛玩動物協会の資格。ペットの飼い方と法律の知識を学ぶもので、1級と2級があります。"),
 (r"シェパード|JSV", "日本シェパード犬登録協会の訓練士の資格です。"),
 (r"^動物取扱業の登録あり$", "お金をもらって犬の訓練・預かりをするのに法律で必要な、自治体への登録です。"),
]
def cred_note(x):
    for pat, note in CRED_NOTES:
        if re.search(pat, x): return note
    return ""


def _edge_line(ic, lab, val, conf):
    """動物の行は、犬・猫のほかの動物（例外）だけを出す。犬・猫だけなら出さない（だれでも分かることは書かない）。片方だけなら「猫だけ」。"""
    if ic != "paw": return (ic, lab, val)
    ks = _kinds_in(val)
    other = [x for x in _split_items(val) if not re.fullmatch(r"(犬|猫|イヌ|ネコ|ドッグ|キャット|犬猫|わんちゃん|ねこちゃん)(OK|可)?", x)]  # 条件つき（「犬（5kg未満）」など）は残す
    if other:
        # 病院の対象動物の行では、犬猫も明記されている場合に対象外と読ませない。
        prefix = "犬・猫のほか " if conf["key"] == "hospital" and {"犬", "猫"} <= set(_split_items(val)) else ""
        return (ic, lab, prefix + "・".join(other))
    if ks == ["cat"] and "dog" in conf["kinds"]: return (ic, lab, "猫だけ")
    if ks == ["dog"] and "cat" in conf["kinds"] and len(conf["kinds"]) > 1: return (ic, lab, "犬だけ")
    return None

def build_card(card, conf, fit_by_name):
    m = _OPEN.match(card)
    opentag = m.group(0)
    inner = card[m.end():-len("</div>")]
    kids = _children(inner)
    if not kids or kids[0][0] != "a": return card
    head = kids[0][1]
    name = _txt(head)
    loc, rows, chips, more, tail, keep = "", [], [], [], [], []
    svc_items = []
    for tag, x in kids[1:]:
        cls = (re.match(r"<\w+[^>]*\bclass=\"([^\"]*)\"", x) or [None, ""])[1]
        t = _txt(x)
        if tag == "small" and "sg-src" in cls:
            more.append(x); continue
        if tag == "small" and "emg-spec" in cls:
            sm = re.search(r"（([^）]+)）", t)
            if sm and _kinds_in(sm.group(1)) and re.fullmatch(r"[犬猫鳥・、うさぎウサギ小動物フェレットハムスターモルモットエキゾチック爬虫類などほか]+", sm.group(1)):
                rows.append(("診る動物", sm.group(1), x)); continue
            more.append(x)
            if not loc and not rows and not re.search(r"：", t): pass
            continue
        if tag == "small":
            mk = re.match(r"<small[^>]*>\s*<b class=\"sg-k\">(.*?)</b>(.*)</small>$", x, re.S)
            if mk: lab, val = _txt(mk.group(1)), _txt(mk.group(2))
            else:
                p = t.split("：", 1)
                lab, val = (p[0], p[1]) if len(p) == 2 and len(p[0]) <= 14 else ("", t)
            if not lab:
                if not loc and not re.search(r"より$|一覧", val): loc = val
                else: more.append(x)
                continue
            rows.append((lab, val, x))
            continue
        if tag == "div" and "sg-tags" in cls:
            chips += [_txt(s) for s in re.findall(r"<span[^>]*>.*?</span>", x)]; continue
        if tag == "span" and "sg-tag" in cls:
            chips.insert(0, t); continue
        if tag == "div" and "emg-score" in cls:
            tail.append(x); continue
        if tag == "a" and "emg-taxi" in cls:
            tail.append(x); continue
        if conf["key"] == "joto" and tag == "ul" and "jt-c" in cls:
            keep.append(x); continue
        more.append(x)
    # 安心の材料（ペットホテルの動物取扱業の登録・夜のスタッフなど。Nori 2026-11-16「どこが信用できるかわからない」）：緑のチェックの札で、名前のすぐ下に
    trust = [v for l, v, _ in rows if l == "安心の材料"]
    rows = [r for r in rows if r[0] != "安心の材料"]
    # 見せる行：場所 → 料金 → 時間 → 動物 → 資格（4行まで）。のこりは「くわしく」
    pick, used = [], set()
    def take(rx, ic):
        for i, (lab, val, x) in enumerate(rows):
            if i in used or not rx.search(lab): continue
            used.add(i); pick.append((ic, lab, val)); return True
        return False
    if not take(_AREA, "car"): take(_ADDR, "pin")
    take(_PRICE, "yen"); take(_TIME, "clock"); take(_ANIM, "paw")
    if len(pick) < 4: take(_CERT, "badge")
    if conf["key"] == "trainer": take(_CAREER, "clock")
    dp = []
    for i, (lab, val, x) in enumerate(rows):
        if i in used: continue
        if re.search(r"診療科目|専門", lab): dp = depts_of(val)
        if lab == "提供内容": svc_items = [x for x in _split_items(val) if not re.search(r"[。は]", x)]
        more.append(x)
    # チップ：印（data-flags）・タグ（data-tags）・提供内容の短い言葉
    flags = (re.search(r'data-flags="([^"]*)"', opentag) or [None, ""])[1].split()
    tags = [html.unescape(x) for x in (re.search(r'data-tags="([^"]*)"', opentag) or [None, ""])[1].split("|") if x]
    ch = [FLAG_CHIP[f] for f in flags if f in FLAG_CHIP and f != "cat"] + [t for t in tags + chips if not re.fullmatch(r"(犬|猫|犬・猫)(OK|可|も)?", t) and not re.fullmatch(r"p\d+", t)]  # 犬OK・猫OK はだれでも分かるので出さない。p◯◯ は費用の帯のしぼりこみ専用の印（facility_cards.sougi_tags）で、チップには出さない
    ch += [s for s in svc_items if len(s) <= 12]
    if trust:  # 緑のチェックに出したことは札にくり返さない（「夜もスタッフ」など）
        _tl = [x.strip() for x in re.split(r"[、,]", trust[0])]
        ch = [c for c in ch if not any(c in t for t in _tl)]
    ch = list(dict.fromkeys(c for c in dp + ch if c))[:6]
    fors = list(dict.fromkeys(FOR_TEXT[k] for k in flags + tags if k in FOR_TEXT))[:3]
    # 合う・合わない（生成側で入れていればそれを使う）
    fit = "" if "data-fit=" in opentag else fit_by_name.get(name, "")
    if not fit and conf["key"] == "joto":
        a = _kinds_in(loc.split("・", 1)[1] if "・" in loc else "")
        if a: fit = fit_attr(a, "など" not in loc, animals_text="・".join(KIND_LABEL[k] for k in a))
    if not fit and conf["key"] != "joto":  # 診る・受ける動物の行から（書いてある動物だけ。「など」があれば決めつけない）
        for lab, val, _ in rows:
            a = _kinds_in(val) if _ANIM.search(lab) else []
            if a: fit = fit_attr(a, not re.search(r"など|ほか|その他|相談|…", val), animals_text=val[:30]); break
    ot = opentag.replace('class="emg-item emg-co', 'class="emg-item emg-co fc', 1)
    if fit: ot = ot[:-1] + fit + ">"
    hue = _hue(name)
    sid = re.search(r'class="emg-score" data-id="([^"]+)"', inner)
    # 写真の枠は、地図サービスの写真がある施設だけ（押して取り寄せたときに出す）。写真のない施設に代わりの絵は付けない（Nori 2026-11-15「写真ない奴、無理につけないで」）
    ph = f'<div class="fc-ph" data-ph="{html.escape(sid.group(1))}" hidden></div>' if sid and PHOTO_AUTO else ""
    city = loc.split("・", 1)[0] if loc else ""
    rest = loc.split("・", 1)[1] if loc and "・" in loc and conf["key"] != "joto" else ""
    if conf["key"] == "joto": city = loc
    if not city:  # 場所の行がないカードは所在地から市区町村を取る
        for ic, lab, val in pick + [(None, l, v) for l, v, _ in rows]:
            m = re.search(r"(?:都|道|府|県)?([^都道府県\s]{1,8}?(?:市|区|町|村))", val) if lab and _ADDR.search(lab) else None
            if m: city = m.group(1); break
    if city and len(city) <= 14: ot = ot[:-1] + f' data-city="{html.escape(city)}">'
    # しぼりこみの印（カードに書いてあることだけから。書いていないカードは外れる）
    ft = list(dict.fromkeys(features(rows, rest, ch) + [c for c in ch if len(c) <= 10 and "|" not in c and c not in dp]))
    if ft: ot = ot[:-1] + f' data-ft="{html.escape("|".join(ft))}">'
    if dp: ot = ot[:-1] + f' data-dp="{html.escape("|".join(dp))}">'
    # 見出しの「◯◯市の動物病院」は地域の見出しと重なるので出さない（Nori 2026-11-15「柏市の下に柏市の動物病院って全てのカードに入れてるけど不要」）
    body = [f'<div class="fc-name">{head}</div>']
    if fors: body.append(f'<p class="fc-catch">{html.escape("・".join(fors[:2]))}に</p>')
    if trust:
        cr = "".join(f'<span class="cr">{html.escape(x.strip())}</span>' for x in dict.fromkeys(re.split(r"[、,]", trust[0])) if x.strip())
        body.append(f'<p class="fc-line" title="安心の材料">{icon("badge")}<span>{cr}</span></p>')
    lines = []
    if rest: lines.append(("clock", "", rest))
    lines += [(ic, lab, val) for ic, lab, val in pick if ic != "yen"]
    lines = [x for x in (_edge_line(ic, lab, val, conf) for ic, lab, val in lines) if x]
    for ic, lab, val in lines[:3]:
        v = val
        if ic == "badge" and conf["key"] == "trainer":
            cr = cred_chips(val)
            if cr:
                body.append(f'<p class="fc-line" title="{html.escape(_short(lab))}">{icon(ic)}<span>{cr}</span></p>')
                if re.search(r"登録", val): more.append(f'<small>登録番号：{html.escape(val)}</small>')
                continue
        body.append(f'<p class="fc-line" title="{html.escape(_short(lab))}">{icon(ic)}<span>{html.escape(v)}</span></p>')
    for ic, lab, val in pick:
        if ic == "yen": body.append(f'<p class="fc-price" title="{html.escape(_short(lab))}">{icon("yen")}<span>{html.escape(val)}</span></p>')
    more = [f'<small>{html.escape(lab)}：{html.escape(val)}</small>' for ic, lab, val in lines[3:]] + more
    if ch: body.append('<ul class="fc-tags">' + "".join(f"<li>{html.escape(c)}</li>" for c in ch[:4]) + "</ul>")
    body.append('<p class="fc-fit" hidden></p>')
    body += keep
    # 下のボタンの列：写真（押したとき reviews.js が入れる）・口コミ・タクシーの料金・くわしいページ・そのほか（文は短く、アイコンつき）
    acts = []
    for x in tail:
        if 'class="emg-taxi"' in x:
            hm = re.search(r'href="([^"]*)"', x); hf = hm.group(1) if hm else ""
            full = _txt(x).rstrip(" →")
            if hf.startswith("/?") or "#form" in hf:
                acts.append(f'<a class="emg-taxi fc-a fc-a-car" href="{hf}" aria-label="{html.escape(full)}">タクシー料金</a>')
            else:
                acts.append(f'<a class="emg-taxi fc-a fc-a-info" href="{hf}" aria-label="{html.escape(full)}">くわしく</a>')
        else: acts.append(x)
    if more: acts.append('<details class="fc-more"><summary class="fc-a fc-a-more">そのほか</summary><div class="fc-more-b">' + "".join(more) + "</div></details>")
    if acts: body.append('<div class="fc-acts">' + "".join(acts) + "</div>")
    return ot + ph + '<div class="fc-body">' + "".join(body) + "</div></div>"

# ---- 「うちの子に合うところをさがす」 ----
def panel(conf, kinds_used, has_size, has_sen, has_pup, n, fts=(), box=False, dps=()):
    want = conf.get("want")
    title = "迎えたい子でさがす" if want else "うちの子に合うところをさがす"
    # 犬・猫はほとんどの施設が受けるので選ぶ欄に出さない。飼い主さんが気にするのは「例外」に合うか（Nori 2026-11-15「犬猫はだいたいオッケーでしょ」「エッジケースに対応できるかを気にしてる」）
    if want: kinds = [k for k in conf["kinds"] if k in kinds_used] if len(conf["kinds"]) > 1 else []
    else: kinds = [k for k in conf["kinds"] if k in kinds_used and k not in ("dog", "cat")]
    rows = []
    if (want and len(kinds) > 1) or (not want and kinds):
        rows.append(f'<div class="fp-row"><span class="fp-l">{"どの子？" if want else "動物"}</span><div class="fp-btns" data-g="a">' +
                    "".join(f'<button type="button" data-v="{k}" aria-pressed="false">{KIND_LABEL[k]}</button>' for k in kinds) + "</div></div>")
    ex = []
    if has_size and "dog" in conf["kinds"]: ex.append('<button type="button" data-v="big" aria-pressed="false">大型犬</button>')
    if has_sen and conf.get("senior"): ex.append('<button type="button" data-v="sen" aria-pressed="false">シニア・介護</button>')
    if has_pup and conf.get("puppy"): ex.append('<button type="button" data-v="pup" aria-pressed="false">子犬</button>')
    if ex: rows.append('<div class="fp-row"><span class="fp-l">うちの子は</span><div class="fp-btns" data-g="x">' + "".join(ex) + "</div></div>")
    if dps: rows.append('<div class="fp-row"><span class="fp-l">診療科目</span><div class="fp-btns fp-ft" data-g="d">' +
                        "".join(f'<button type="button" data-v="{html.escape(v)}" aria-pressed="false">{html.escape(v)}</button>' for v in dps) + "</div></div>")
    if fts: rows.append('<div class="fp-row"><span class="fp-l">しぼる</span><div class="fp-btns fp-ft" data-g="f">' +
                        "".join(f'<button type="button" data-v="{html.escape(v)}" aria-pressed="false">{html.escape(v)}</button>' for v in fts) + "</div></div>")
    if not rows and not box: return ""
    hide = '<label class="fp-hide"><input type="checkbox"> 合わないところを隠す</label>' if (kinds or ex or dps) else ""
    return (f'<div class="fp" data-fp><p class="fp-t">{icon("paw")}{html.escape(title)}</p>'
            + "".join(rows) + '<p class="fp-now" aria-live="polite"></p>' + hide + '</div>')

CSS = """<style id="fccss">
.emg-item.fc{display:flex;flex-direction:column;background:#fff;border:1px solid var(--line,#ece6e0);border-radius:18px;padding:0;margin:0;box-shadow:0 2px 10px rgba(28,26,24,.07);overflow:hidden;min-width:0}
.fr{margin:4px 0 18px}
.fr-h{font-size:1.05rem!important;font-weight:800;margin:10px 0 8px!important;display:flex;align-items:baseline;gap:8px}
.fr-h small{font-size:.78rem;font-weight:600;color:var(--ink-3,#6b625b)}
.fr-s{display:grid;gap:12px;padding:2px 2px 12px}
.fr-more{margin:4px 0 18px;font-size:14px}.fr-more a{color:#c2410c;font-weight:600}
.fr-s>.emg-item.fc[hidden],.fr-s>.emg-item.fac-off,.emg-item.fc.fc-off{display:none}
.fr:not(:has(.emg-item.fc:not([hidden]):not(.fac-off):not(.fc-hid):not(.fc-off))),.fr-empty{display:none!important}
.fc-ph{position:relative;aspect-ratio:4/3;background:#f4f1ee;overflow:hidden}
.fc-ph[hidden]{display:none}
.fc-phbtn{display:inline-flex;align-items:center;gap:6px;font-size:.8rem;font-weight:700;padding:6px 12px;margin:10px 0 0;border:1.5px solid var(--line,#ece6e0);border-radius:999px;background:#fff;color:var(--ink,#2b2622);cursor:pointer}
.fc-phbtn[disabled]{opacity:.7;cursor:default}
.fc-car{position:absolute;inset:0;display:flex;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none}
.fc-car::-webkit-scrollbar{display:none}
.fc-car figure{flex:0 0 100%;margin:0;position:relative;scroll-snap-align:start}
.fc-car img{width:100%;height:100%;object-fit:cover;display:block}
.fc-car figcaption{position:absolute;left:8px;bottom:8px;max-width:60%;font-size:.68rem;line-height:1.3;color:#fff;background:rgba(0,0,0,.45);border-radius:6px;padding:2px 6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fc-car figcaption a{color:#fff}
.fc-dots{position:absolute;left:0;right:0;bottom:10px;display:flex;justify-content:center;gap:6px;z-index:2;pointer-events:none}
.fc-dots i{width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.55)}.fc-dots i.on{background:#fff}
.fc-src{position:absolute;right:8px;bottom:8px;z-index:2;font-size:.66rem;color:#fff;background:rgba(0,0,0,.45);border-radius:6px;padding:2px 6px}
.fc-body{padding:12px 14px 14px;flex:1;display:flex;flex-direction:column}
.fc-name{margin:0}.fc-name>a{font-size:1.02rem;line-height:1.45;color:var(--ink,#2b2622);text-decoration:none;display:block}.fc-name>a b{font-weight:800}
.fc-catch{display:inline-block;align-self:flex-start;font-size:.76rem;font-weight:700;color:#a8410b;background:#fff1e6;border-radius:999px;padding:2px 9px;margin:6px 0 0!important;line-height:1.5}
.fc-line,.fc-price{display:flex;gap:6px;align-items:flex-start;font-size:.86rem;line-height:1.55;color:var(--ink-2,#5a524b);margin:4px 0 0!important}
.fc-line>span{display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden;min-width:0}
.fc-price{font-weight:800;color:var(--ink,#2b2622);font-size:.92rem}
.fc-i{flex:0 0 auto;width:16px;height:16px;margin-top:2px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;color:var(--o,#e8590c)}
.fc-k{font-size:.72rem;font-weight:700;color:var(--ink-3,#6b625b);background:#f4f1ee;border-radius:6px;padding:1px 6px;margin-right:6px}
.fc-tags{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0!important;margin:8px 0 0!important}
.fc-tags li{font-size:.74rem;line-height:1.3;padding:3px 8px;border-radius:6px;background:#f4f1ee;color:var(--ink-2,#5a524b);margin:0!important}
.fc-fit{display:flex;flex-wrap:wrap;gap:4px;margin:8px 0 0!important}
.fc-fit[hidden]{display:none}
.fc-fb{font-size:.74rem;font-weight:800;line-height:1.3;padding:3px 8px;border-radius:999px}
.fc-fb.ok{background:#e8f5e9;color:#1b5e20}.fc-fb.unk{background:#f4f1ee;color:#5a524b;font-weight:600}.fc-fb.ng{background:#fdecea;color:#a12a1b}
.emg-item.fc.fc-ng{opacity:.62}
.emg-item.fc.fc-hid{display:none}
.fc-acts{display:flex;flex-wrap:wrap;gap:5px;margin:auto 0 0;padding-top:10px}
.fc-a,.fc-acts .partner-review-open,.fc-acts .fc-phbtn,.fc-acts .fac-act a,.fc-acts .fac-act button{display:inline-flex;align-items:center;gap:3px;font-size:.74rem!important;font-weight:700;line-height:1.2;padding:6px 9px!important;margin:0!important;border:1.5px solid var(--line,#ece6e0)!important;border-radius:999px!important;background:#fff!important;color:var(--ink,#2b2622)!important;text-decoration:none!important;cursor:pointer;list-style:none;min-height:32px;box-sizing:border-box;white-space:nowrap}
.fc-a::before,.fc-acts .partner-review-open::before,.fc-acts .fc-phbtn::before{content:"";width:15px;height:15px;flex:0 0 15px;background:center/contain no-repeat}
.fc-acts .fc-phbtn::before{background-image:var(--fc-cam)}.fc-acts .partner-review-open::before{background-image:var(--fc-star)}
.fc-a-more::-webkit-details-marker{display:none}.fc-more>summary{list-style:none}.fc-acts summary::after{display:none!important;content:none!important}
.fc-acts .emg-score,.fc-acts .partner-score{display:contents;margin:0}
.fc-acts .partner-score .stars,.fc-acts .partner-score>b{align-self:center}
.fc-acts .review-panel,.fc-acts .partner-review-src{flex:0 0 100%;font-size:.72rem}
.fc-acts .fac-act{display:contents}
.fc-acts .fac-act a.fac-site{background:var(--o,#e8590c)!important;border-color:var(--o,#e8590c)!important;color:#fff!important}
.fc-more{display:block;flex:0 0 auto;margin:0;background:none!important;box-shadow:none!important;border:0!important;padding:0!important}.fc-more[open]{flex-basis:100%}.fc-more[open]>summary{border-color:var(--o,#e8590c)!important;display:inline-flex}
.fc-more-b{margin-top:6px;font-size:.82rem;line-height:1.6;color:var(--ink-2,#5a524b);background:#faf8f6;border-radius:10px;padding:6px 10px}
.fc-more-b>small,.fc-more-b>p,.fc-more-b>ul,.fc-more-b>dl,.fc-more-b>a{display:block;margin:4px 0!important}
:root{--fc-cam:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23c2410c%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M4%208h3l1.5-2h7L17%208h3v11H4z%22/%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%2213%22%20r%3D%223.3%22/%3E%3C/svg%3E");--fc-star:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23c2410c%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M12%204l2.4%205%205.4.6-4%203.7%201.1%205.3L12%2016l-4.9%202.6%201.1-5.3-4-3.7%205.4-.6z%22/%3E%3C/svg%3E")}
.fc-a-cam::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23c2410c%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M4%208h3l1.5-2h7L17%208h3v11H4z%22/%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%2213%22%20r%3D%223.3%22/%3E%3C/svg%3E")}.fc-a-star::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23c2410c%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M12%204l2.4%205%205.4.6-4%203.7%201.1%205.3L12%2016l-4.9%202.6%201.1-5.3-4-3.7%205.4-.6z%22/%3E%3C/svg%3E")}.fc-a-car::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23c2410c%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M4%2015.5l1.6-5a2%202%200%200%201%201.9-1.4h9a2%202%200%200%201%201.9%201.4l1.6%205v3h-16z%22/%3E%3Ccircle%20cx%3D%228%22%20cy%3D%2215.5%22%20r%3D%221.3%22/%3E%3Ccircle%20cx%3D%2216%22%20cy%3D%2215.5%22%20r%3D%221.3%22/%3E%3C/svg%3E")}.fc-a-info::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23c2410c%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%2212%22%20r%3D%228.5%22/%3E%3Cpath%20d%3D%22M12%2011v5M12%208h.01%22/%3E%3C/svg%3E")}.fc-a-more::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23c2410c%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M12%206v12M6%2012h12%22/%3E%3C/svg%3E")}.fc-a-site::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23c2410c%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M14%205h5v5M19%205l-8%208M17%2014v5H5V7h5%22/%3E%3C/svg%3E")}.fc-a-note::before{background-image:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23c2410c%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M6%204h9l3%203v13H6z%22/%3E%3Cpath%20d%3D%22M9%2011h6M9%2015h6%22/%3E%3C/svg%3E")}
.emg-item.fc .jt-c{margin-top:8px}
.fp{background:#fffaf5;border:2px solid var(--o,#e8590c);border-radius:20px;padding:14px;margin:12px 0 16px}
.fp-t{display:flex;gap:6px;align-items:center;font-weight:800;font-size:1.04rem;margin:0 0 10px!important;color:var(--ink,#2b2622)}
.fp-t .fc-i{width:20px;height:20px;margin:0}
.fp-row{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin:0 0 10px}
.fp-l{font-size:.8rem;font-weight:800;color:var(--ink-3,#6b625b);min-width:5em}
.fp-btns{display:flex;flex-wrap:wrap;gap:6px;flex:1 1 200px}
.fp-ft button,.fp .fac-chips button{font-size:.84rem;padding:6px 12px;min-height:36px;border-radius:999px;border:1.5px solid var(--line,#ece6e0);background:#fff;font-weight:700;color:var(--ink,#2b2622)}
.fp .fac-chips button[aria-pressed=true]{background:var(--o,#e8590c);border-color:var(--o,#e8590c);color:#fff}
.fp .fac-filter{margin:0 0 8px}.fp .fac-chips{margin:4px 0}.fp .fac-count:empty{display:none}
.fp-btns button{font-size:.9rem;font-weight:700;padding:8px 14px;border-radius:999px;border:1.5px solid var(--line,#ece6e0);background:#fff;color:var(--ink,#2b2622);cursor:pointer;min-height:40px}
.fp-btns button[aria-pressed=true]{background:var(--o,#e8590c);border-color:var(--o,#e8590c);color:#fff}
.fp-row select{flex:1 1 220px;min-width:0;font-size:16px;padding:9px 10px;border:1.5px solid var(--line,#ece6e0);border-radius:12px;background:#fff;color:var(--ink,#2b2622)}
.fp-now{font-size:.84rem;margin:2px 0 6px!important;line-height:1.6;color:var(--ink,#2b2622)}
.fp-now:empty{display:none}
.fp-now b{font-weight:800}
.fp-hide{display:flex;gap:6px;align-items:center;font-size:.82rem;color:var(--ink-2,#5a524b)}
.fp-hide input{width:18px;height:18px}
@media (min-width:760px){.fr-s{grid-template-columns:1fr 1fr}}
</style>"""

FIT_JS = '<script src="/fit.js" defer></script>'

_CARD = re.compile(r'<div class="emg-item emg-co fc[^"]*"[^>]*>')

def rows(h):
    """続いて並ぶカードを、横にスワイプして見る列（.fr）にまとめる。6件以上で市区町村が分かれるときは市区町村ごとの列にする
    （Nori 2026-11-15「ヨコにスワイプしたらいろいろ出てくる。各カテゴリ(エリアとか)でわけるみたいなUI」）。何度動かしても同じ。"""
    if 'class="fr-s"' in h: return h
    out, i, run = [], 0, []
    def flush():
        if not run: return
        cards = [c for c, _ in run]
        cities = [cy for _, cy in run]
        groups = []
        uniq = list(dict.fromkeys(c for c in cities if c))
        if len(cards) >= 6 and len(uniq) >= 2 and sum(1 for u in uniq if cities.count(u) >= 2) >= 1:
            other = []
            for u in uniq:
                cs = [c for c, cy in run if cy == u]
                if len(cs) >= 2: groups.append((u, cs))
                else: other += cs
            other += [c for c, cy in run if not cy]
            if other: groups.append(("ほかの地域", other))
        else:
            groups.append(("", cards))
        for lab, cs in groups:
            hd = f'<h3 class="fr-h">{html.escape(lab)}<small>{len(cs)}件</small></h3>' if lab else ""
            out.append(f'<div class="fr">{hd}<div class="fr-s">' + "".join(cs) + "</div></div>")
        run.clear()
    pos = 0
    for m in _CARD.finditer(h):
        if m.start() < pos: continue
        e = _end(h, m.start(), "div")
        gap = h[pos:m.start()]
        if run and gap.strip():
            flush()
        if not run: out.append(gap)
        cy = (re.search(r'data-city="([^"]*)"', m.group(0)) or [None, ""])[1]
        run.append((h[m.start():e], html.unescape(cy)))
        pos = e
    flush()
    out.append(h[pos:])
    return "".join(out)

def _too_big(h):
    """情報ページの重さの上限（tests/info-light.test.cjs の60KB）を超えるなら作りかえない（全部の施設を並べる全国のページ。県のページで見せる）"""
    import gzip
    return len(gzip.compress(h.encode("utf-8"), 9)) > 52 * 1024  # あとで cardskin.py がカードの形をそろえて少し重くなるので、余裕を残す

def _trim(h, keep, retained=()):
    """全国のページで重すぎるとき、都道府県ごとの箱（emg-pref、見出しに県のページへのリンク）に最初の keep 件だけ残し、のこりは県のページへのリンクにする（施設は県のページにすべて載っている。tests/info-light の「上限を超えたら県のページへのリンクに」）"""
    out, i = [], 0
    for sm in re.finditer(r'<section class="emg-pref"[^>]*>', h):
        if sm.start() < i: continue
        se = _end(h, sm.start(), "section")
        sec = h[sm.start():se]
        lk = re.search(r'<h4><a href="([^"]+)">([^<（]+)', sec)
        cards = [m for m in _OPEN.finditer(sec)]
        if not lk or len(cards) <= keep:
            out.append(h[i:se]); i = se; continue
        pinned = {n for n, m in enumerate(cards) if any(
            f'data-fid="{fid}"' in sec[m.start():_end(sec, m.start(), "div")] for fid in retained)}
        normal = (n for n in range(len(cards)) if n not in pinned)
        included = pinned | {next(normal) for _ in range(max(0, keep - len(pinned)))}
        parts, j, cut = [], 0, 0
        for n, m in enumerate(cards):
            if m.start() < j: continue
            e = _end(sec, m.start(), "div")
            if n not in included:
                parts.append(sec[j:m.start()]); j = e; cut += 1
        parts.append(sec[j:])
        sec2 = "".join(parts)
        more = f'<p class="fr-more"><a href="{lk.group(1)}">{html.escape(lk.group(2))}のほかの{cut}件を見る →</a></p>'
        sec2 = sec2[:sec2.rfind("</section>")] + more + "</section>"
        out.append(h[i:sm.start()]); out.append(sec2); i = se
    out.append(h[i:])
    return "".join(out)

def _one(h, conf, fbn):
    """1ページを作りかえる。重すぎれば None"""
    out, i = [], 0
    for m in _OPEN.finditer(h):
        if m.start() < i: continue
        s = m.start(); e = _end(h, s, "div")
        out.append(h[i:s])
        c = h[s:e]
        if " fc" in m.group(0).split('"')[1].split("emg-co", 1)[1] + " ": out.append(c)
        else: out.append(build_card(c, conf, fbn))
        i = e
    out.append(h[i:])
    h2 = "".join(out)
    if "emg-item emg-co fc" not in h2: return h
    h2 = rows(h2)
    if 'id="fccss"' not in h2:
        h2 = h2.replace("</head>", CSS + "\n</head>", 1)
        h2 = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + sprite_for(h2), h2, count=1)
    if "data-fp" not in h2 and "data-hf" not in h2:  # 動物病院は /hosp.js のさがす欄（tools/hosp_find.py）
        fits = [json.loads(x) for x in fit_attr_values(h2)]
        ku = {k for f in fits for k in f.get("a", [])}
        fl = [html.unescape(x).split("|") for x in re.findall(r'data-ft="([^"]*)"', h2)]
        nc = len(re.findall(r'class="emg-item emg-co fc', h2))
        cnt = {}
        for xs in fl:
            for x in xs: cnt[x] = cnt.get(x, 0) + 1
        old_chips = set((re.search(r'data-fac-chips="([^"]*)"', h2) or [None, ""])[1].split("|"))
        fts = [x for x in _FT_ORDER if 0 < cnt.get(x, 0) < nc]
        if "data-fac-chips" in h2: fts = [x for x in fts if x not in ("来てくれる・送迎", "料金を公開")]
        if "data-fac-chips" not in h2:  # 前からの「条件でしぼりこむ」があるページは、そちらと重ねない
            fts += sorted([x for x in cnt if x not in _FT_ORDER and 2 <= cnt[x] < nc], key=lambda x: -cnt[x])
        fts = [x for x in fts if not re.search(r"シニア|介護|猫OK|犬OK|大型犬|猫専用|子犬|パピー", x)]  # 上の「どの子？」「大きさ」と重ねない
        if any("送迎" in x for x in fts if x != "来てくれる・送迎"): fts = [x for x in fts if x != "来てくれる・送迎"]
        fts = fts[:8] if nc >= 4 else []
        dpc = {}
        for xs in re.findall(r'data-dp="([^"]*)"', h2):
            for x in html.unescape(xs).split("|"): dpc[x] = dpc.get(x, 0) + 1
        dps = [n for n, _ in DEPTS if dpc.get(n)]
        fts = [x for x in fts if x not in dps]
        pn = panel(conf, ku, any("s" in f or "kg" in f for f in fits), any(f.get("sen") for f in fits), any(f.get("pup") for f in fits), len(fits), fts, "data-fac-chips" in h2, dps)
        if pn:
            k = h2.find('class="emg-item emg-co fc')
            em = h2.rfind('<div class="emg">', 0, k)
            if em >= 0 and h2.count("</main>", em, k) == 0:  # 一覧の箱のいちばん上（答えの箱・数字のすぐ後ろ）
                pos = em + len('<div class="emg">')
            else:
                # 最初のカードを含む一覧（emg-pref）の前。しぼりこみのチップや都道府県の選択が直前にあれば、その前に置く
                sec = h2.rfind('<section class="emg-pref"', 0, k)
                pos = sec if sec >= 0 else h2.rfind("<div", 0, k)
                for mark in ('<div class="fac-filter"', '<div class="hosp-pref"', '<div class="trim-cond"', '<label for="hospPref"'):
                    q = h2.rfind(mark, 0, pos)
                    if q >= 0 and pos - q < 6000 and h2.count("<section", q, pos) <= 1: pos = min(pos, q)
            h2 = h2[:pos] + pn + h2[pos:]
            if FIT_JS not in h2: h2 = h2.replace("</body>", FIT_JS + "\n</body>", 1)
    # 前からの「条件でしぼりこむ」（facility.js が市区町村の検索とチップを入れる箱）を、さがす欄の中にまとめる
    ff = h2.find('<div class="fac-filter"'); fn = h2.find('<p class="fp-now"')
    if ff >= 0 and fn >= 0 and ff > fn:
        fe = _end(h2, ff, "div"); box = re.sub(r'<p class="emg-tips-note"[^>]*>条件でしぼりこむ[^<]*</p>', "", h2[ff:fe])
        h2 = h2[:ff] + h2[fe:]
        h2 = h2[:fn] + box + h2[fn:]
    h2 = list_first(h2)
    return None if h2 != h and _too_big(h2) else h2

def list_first(h):
    """一覧（さがす欄とカード）を、ポイントの箱・数字・グラフより前に出す（タクシーのページのフォームと同じく、さがすものを先に。
    Nori 2026-11-15「ページの上の方になんかいろいろ結構長く書いてるけど、フォームとかが先に来たほうがいい」）。説明は消さずに一覧の後ろへ。"""
    k = h.find('class="emg-item emg-co fc')
    if k < 0: return h
    em = h.rfind('<div class="emg">', 0, k)
    if em < 0: return h
    sec = h.rfind('<section style="padding-top:8px"', 0, em)
    if sec < 0 or h.count("</section>", sec, em): return h
    w = h.find("<div", sec)
    if w < 0 or w >= em: return h
    wo = h.find(">", w) + 1
    if not h[wo:em].strip(): return h
    if h.count("</div>", wo, em) > h.count("<div", wo, em): return h  # 同じ箱の中にないときは動かさない
    ee = _end(h, em, "div")
    block = h[em:ee]
    # 一覧の上の「無料の情報です」の注意書きは一覧の後ろへ
    notes = re.findall(r'\s*<p class="emg-free">.*?</p>', block[:block.find("<section") if "<section" in block else 0], re.S)
    for n in notes: block = block.replace(n, "", 1)
    if notes: block = block[:-len("</div>")] + "".join(notes) + "</div>"
    return h[:wo] + block + h[wo:em] + h[ee:]

def build(ROOT):
    T = _fit_table()
    n = 0
    for d in sorted(DIRS):
        conf = CATS[d]
        fbn = T.get(conf["key"], {})
        for base, _, files in os.walk(os.path.join(ROOT, d)):
            if "index.html" not in files: continue
            p = os.path.join(base, "index.html")
            h = open(p, encoding="utf-8").read()
            if 'class="emg-item emg-co' not in h: continue
            national = os.path.normpath(base) == os.path.normpath(os.path.join(ROOT, d))
            summary_max = {"dog-trainer": 3, "pet-hotel": 4}.get(d) if national else None
            retained = ("T114",) if national and d == "dog-trainer" else ()
            h2 = None if summary_max else _one(h, conf, fbn)
            # 全部の施設を並べる全国のページが重すぎるときは、県ごとに数件だけ残して県のページへのリンクにする（写真のない古い形のまま残さない）
            for keep in (n for n in (8, 6, 4, 3, 2) if summary_max is None or n <= summary_max):
                if h2 is not None: break
                h2 = _one(_trim(h, keep, retained), conf, fbn)
                if h2 is not None: print(f"faccard: 重いので県ごとに{keep}件まで", os.path.relpath(p, ROOT))
            if h2 is None:
                print("faccard: 重すぎるので作りかえない", os.path.relpath(p, ROOT)); continue
            if h2 != h:
                open(p, "w", encoding="utf-8").write(h2); n += 1
    return n

def quote_all(ROOT):
    """全ページの data-fit の書き方だけをシングルクォートにそろえる（ほかは何も変えない）。"""
    n = 0
    for d in sorted(DIRS):
        for base, _, files in os.walk(os.path.join(ROOT, d)):
            if "index.html" not in files: continue
            p = os.path.join(base, "index.html")
            h = open(p, encoding="utf-8").read()
            h2 = fit_single_quote(h)
            if h2 != h:
                open(p, "w", encoding="utf-8").write(h2); n += 1
    return n

if __name__ == "__main__":
    import sys
    sys.path.insert(0, HERE)
    if "--quote-only" in sys.argv:
        print("faccard quote-only", quote_all(os.path.dirname(HERE)), "pages"); sys.exit(0)
    print("faccard", build(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)), "pages")
