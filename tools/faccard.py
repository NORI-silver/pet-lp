# [B][A] 施設の一覧のカードを、写真の枠・要点のチップ・「こんな人に」・くわしくは折りたたみの形にそろえ、
# 一覧の上に「うちの子に合うところをさがす」を入れる（Nori 2026-11-15「施設紹介系がただ施設並べてるだけ。見づらい。写真もない」
# 「フィルターももっとあったほうがいい」「自分の犬や猫とかにマッチするものを探したいはず」）。
#
# gen_areas.py の最後（tables.py のあと）に、できあがったページの .emg-item.emg-co を作りかえる後処理。何度動かしても同じ。
# - 生成側（gen_*.py）は今までどおり <div class="emg-item emg-co"><a href=公式><b>名前</b></a><small>ラベル：値</small>…</div> を出すだけでよい。
# - 写真：カードの左上の枠。最初は名前の1文字（その施設だけの印。ほかの写真は借りない）。<div class="emg-score" data-id> がある施設は、
#   枠の「写真」を押すと地図サービスの写真（撮った人の名前と出どころつき）を取り寄せて枠に入れる（reviews.js）。
# - 合う・合わない：データ（公式サイトに書いてあること）から data-fit を作る。書いていないことは「要確認」で、「しない」ではない。
#   生成側で決めたいときは fit_attr(...) の戻り値を div に足す（あればそれを使う）。
# - 文字は消さない・隠さない（くわしくは <details> の中。検索・AIにも読める）。電話番号・順位・点数順はなし。
import os, re, json, html, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))

# 分野ごとの設定。kinds＝「どの子？」に出す動物、size＝大きさ（犬）を聞く、senior／puppy＝シニア・介護／子犬を聞く
CATS = {
    "dog-trainer": dict(key="trainer", icon="dog", kinds=["dog"], puppy=True, label="ドッグトレーナー・しつけ教室"),
    "pet-sitter": dict(key="sitter", icon="home", kinds=["dog", "cat", "small", "bird"], label="ペットシッター"),
    "rojin-home": dict(key="rojin", icon="home", kinds=["dog", "cat"], size=True, label="老犬ホーム・老猫ホーム"),
    "trimming": dict(key="trimming", icon="scissors", kinds=["dog", "cat"], size=True, senior=True, label="出張トリミング"),
    "pet-hotel": dict(key="hotel", icon="bed", kinds=["dog", "cat"], size=True, senior=True, label="ペットホテル"),
    "sougi": dict(key="sougi", icon="flower", kinds=[], label="ペット火葬・霊園"),
    "hospital": dict(key="hospital", icon="cross", kinds=["dog", "cat", "small", "bird", "exotic"], size=True, label="動物病院"),
    "joto": dict(key="joto", icon="heart", kinds=["dog", "cat"], want=True, label="譲渡の窓口・保護団体"),
}
DIRS = set(CATS)
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
}
def icon(n, cls="fc-i"):
    # 形はページに1回だけ（SPRITE）。カードからは名前で呼ぶ（ページを軽くするため）
    return f'<svg class="{cls}" aria-hidden="true" focusable="false"><use href="#fci-{n}"/></svg>'
SPRITE = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true">' +
          "".join(f'<symbol id="fci-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in _P.items()) + '</svg>')

# ---- ラベルの分け方 ----
_AREA = re.compile(r"エリア|地域|往診|出張|対応")
_ADDR = re.compile(r"所在地|住所|場所|教室")
_PRICE = re.compile(r"料金|費用|手数料|金額")
_TIME = re.compile(r"時間|受付|営業|定休|休み")
_ANIM = re.compile(r"動物|受け入れ")
_CERT = re.compile(r"資格|登録|認定")
_SVC = re.compile(r"^(提供内容|内容|できること|サービス)$")

# 条件の印（data-flags）を、カードのチップと「こんな人に」の言葉にする（公式サイトに書いてあることから作った印だけ）
FLAG_CHIP = {
    "large": "大型犬OK", "cat_only": "猫専用", "cat": "猫OK", "vet": "病院が併設", "pickup": "送迎あり", "senior": "シニア・介護OK",
    "night_staff": "夜もスタッフ", "camera": "カメラで見守り", "run": "ドッグラン", "private_room": "個室", "car": "トリミングカー", "in_home": "家の中で",
}
FOR_TEXT = {
    # 印・タグ → こんな人に（短く。言い切りすぎない）
    "large": "大型犬の子", "cat_only": "犬の声が苦手な猫", "senior": "シニアや持病のある子", "pickup": "送り迎えしてほしい人",
    "vet": "病院が近いと安心な人", "camera": "留守中も様子を見たい人", "private_room": "静かな個室がいい子", "run": "体を動かしたい子",
    "night_staff": "夜も人がいると安心な人", "car": "家の前でトリミングしたい人", "in_home": "家の中でしてほしい人",
    "出張・訪問": "家での困りごとを家で見てほしい人", "教室・グループ": "ほかの犬と一緒に練習したい人", "パピー": "子犬を迎えたばかりの人",
    "幼稚園・保育園": "日中あずけて社会性を育てたい人", "預かり訓練": "まとめて預けて練習したい人", "オンライン": "近くに教室がない人",
    "猫": "猫を家で留守番させたい人", "小動物": "うさぎ・小動物の飼い主", "鳥": "鳥の飼い主", "散歩": "散歩も頼みたい人",
    "個別火葬": "お骨を返してほしい人", "立ち会い": "最後まで見送りたい人", "お迎え・訪問火葬": "家まで来てほしい人", "霊園・納骨": "納骨の場所もさがしている人",
}

# ---- 公式サイトに書いてあることから「合う・合わない」のデータを作る ----
def fit_attr(animals=None, only=False, sizes=None, max_kg=None, senior=None, puppy=None, animals_text=""):
    """生成側からカードに足す属性（' data-fit="…"'）。書いていないことは渡さない（＝要確認）。"""
    d = {}
    if animals: d["a"] = list(dict.fromkeys(animals))
    if animals and only: d["o"] = 1
    if animals_text: d["at"] = animals_text
    if sizes: d["s"] = list(dict.fromkeys(sizes))
    if max_kg: d["kg"] = max_kg
    if senior: d["sen"] = 1
    if puppy: d["pup"] = 1
    if not d: return ""
    return ' data-fit="' + html.escape(json.dumps(d, ensure_ascii=False, separators=(",", ":"))) + '"'

def _kinds_in(t):
    a = []
    if re.search(r"犬|ドッグ|わんちゃん", t): a.append("dog")
    if re.search(r"猫|キャット", t): a.append("cat")
    if re.search(r"小動物|うさぎ|ウサギ|ハムスター|フェレット|モルモット|チンチラ", t): a.append("small")
    if re.search(r"鳥|インコ|オウム", t): a.append("bird")
    if re.search(r"エキゾ|爬虫|は虫|カメ|トカゲ|ヘビ", t): a.append("exotic")
    return a

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
        T["trainer"][t["name"]] = fit_attr(["dog"], True, puppy=bool({"パピー", "幼稚園・保育園"} & set(tags)), animals_text="犬")
    si = _load("sitters.json") or {}
    for s in si.get("sitters", []):
        ch = si.get("chains", {}).get(s.get("chain"), {})
        txt = (s.get("animals") or "") + (" " + ch.get("note", "") if s.get("chain") != "indie" else "")
        a = _kinds_in(txt)
        only = bool(re.search(r"専門|のみ|専用|だけ", s.get("animals") or ""))
        if a: T["sitter"][s["name"]] = fit_attr(a, only, animals_text="・".join(KIND_LABEL[k] for k in a))
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
        T["rojin"][h["name"]] = fit_attr(a, bool(a) and "など" not in t, sizes, kg, senior=True, animals_text="・".join(KIND_LABEL[k] for k in a))
    gr = _load("grooming.json") or {}
    for g in gr.get("groomers", []):
        a = ["dog"] + (["cat"] if g.get("cat") else [])
        T["trimming"][g["name"]] = fit_attr(a, False, ["s", "m", "l"] if g.get("large") else None, g.get("max_kg"), g.get("senior"))
    ho = _load("hotels.json") or {}
    for h in ho.get("hotels", []):
        if h.get("cat_only"): a, only = ["cat"], True
        else: a, only = ["dog"] + (["cat"] if h.get("cat") else []), False
        T["hotel"][h["name"]] = fit_attr(a, only, ["s", "m", "l"] if h.get("large") and not h.get("cat_only") else None, h.get("max_kg"), h.get("senior"),
                                         animals_text="猫だけ" if h.get("cat_only") else "")
    hp = _load("hospitals.json") or {}
    for kind in ("visit", "cat", "exotic", "large"):
        for h in hp.get(kind, []):
            t = h.get("animals", "")
            a = _kinds_in(t)
            T["hospital"][h["name"]] = fit_attr(a, bool(a) and not re.search(r"など|ほか|その他|相談", t), ["s", "m", "l"] if kind == "large" else None,
                                                animals_text=t[:40])
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
        if conf["key"] == "joto" and ((tag == "p" and "jt-h" in cls and "公式ページに書いてあること" in t) or (tag == "ul" and "jt-c" in cls)):
            keep.append(x); continue
        more.append(x)
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
    for i, (lab, val, x) in enumerate(rows):
        if i in used: continue
        if lab == "提供内容": svc_items = [x for x in _split_items(val) if not re.search(r"[。は]", x)]
        more.append(x)
    # チップ：印（data-flags）・タグ（data-tags）・提供内容の短い言葉
    flags = (re.search(r'data-flags="([^"]*)"', opentag) or [None, ""])[1].split()
    tags = [html.unescape(x) for x in (re.search(r'data-tags="([^"]*)"', opentag) or [None, ""])[1].split("|") if x]
    ch = [FLAG_CHIP[f] for f in flags if f in FLAG_CHIP and not (f == "cat" and "cat_only" in flags)] + tags + chips
    ch += [s for s in svc_items if len(s) <= 12]
    ch = list(dict.fromkeys(c for c in ch if c))[:6]
    fors = list(dict.fromkeys(FOR_TEXT[k] for k in flags + tags if k in FOR_TEXT))[:3]
    # 合う・合わない（生成側で入れていればそれを使う）
    fit = "" if "data-fit=" in opentag else fit_by_name.get(name, "")
    if not fit and conf["key"] == "joto":
        a = _kinds_in(loc.split("・", 1)[1] if "・" in loc else "")
        if a: fit = fit_attr(a, "など" not in loc, animals_text="・".join(KIND_LABEL[k] for k in a))
    ot = opentag.replace('class="emg-item emg-co', 'class="emg-item emg-co fc', 1)
    if fit: ot = ot[:-1] + fit + ">"
    hue = _hue(name)
    sid = re.search(r'class="emg-score" data-id="([^"]+)"', inner)
    ph = (f'<div class="fc-ph" style="--fh:{hue}"' + (f' data-ph="{html.escape(sid.group(1))}"' if sid else "") +
          f'><span class="fc-mono" aria-hidden="true">{html.escape(_mono(name))}</span>{icon(conf["icon"], "fc-ci")}</div>')
    hd = (f'<div class="fc-hd">{head}' + (f'<p class="fc-loc">{icon("pin")}{html.escape(loc)}</p>' if loc else "") + '</div>')
    out = [ot, f'<div class="fc-top">{ph}{hd}</div>', '<p class="fc-fit" hidden></p>']
    if ch: out.append('<ul class="fc-chips">' + "".join(f"<li>{html.escape(c)}</li>" for c in ch) + "</ul>")
    if pick:
        out.append('<ul class="fc-rows">' + "".join(f'<li>{icon(ic)}<span class="fc-k">{html.escape(_short(lab))}</span><span class="fc-v">{html.escape(val)}</span></li>' for ic, lab, val in pick) + "</ul>")
    out += keep
    if fors: out.append(f'<p class="fc-for"><b>こんな人に</b>{html.escape("・".join(fors))}</p>')
    if more:
        out.append('<details class="fc-more"><summary>くわしく見る</summary>' + "".join(more) + "</details>")
    out += tail
    out.append("</div>")
    return "".join(out)

# ---- 「うちの子に合うところをさがす」 ----
def panel(conf, kinds_used, has_size, has_sen, has_pup, n):
    import breeds as B
    want = conf.get("want")
    title = "迎えたい子で窓口をさがす" if want else f"うちの子に合う{conf['label']}をさがす"
    lead = ("迎えたい動物を選ぶと、その動物の譲渡をしていると公式ページに書いてある窓口が上に来ます。" if want else
            "選ぶと、合うところから順に並び、カードに「この子OK」「要確認」「合わないかも」と理由が出ます（公式サイトに書いていないことは「要確認」）。")
    kinds = [k for k in conf["kinds"] if k in kinds_used] if len(conf["kinds"]) > 1 else []
    rows = []
    if len(kinds) > 1:
        rows.append('<div class="fp-row"><span class="fp-l">どの子？</span><div class="fp-btns" data-g="a">' +
                    "".join(f'<button type="button" data-v="{k}" aria-pressed="false">{KIND_LABEL[k]}</button>' for k in kinds) + "</div></div>")
    if has_size and "dog" in (kinds or conf["kinds"]):
        opts = ['<option value="">えらばない</option><optgroup label="体重で選ぶ（ミックスの子も）">']
        opts += [f'<option value="{k}" data-lo="{lo}" data-hi="{hi}">{html.escape(lab)}</option>' for k, lab, lo, hi in B.SIZES]
        opts.append('</optgroup><optgroup label="犬種で選ぶ（体重の目安で判定）">')
        opts += [f'<option value="{b["id"]}" data-lo="{b["kg"][0]}" data-hi="{b["kg"][1]}">{html.escape(b["name"])}</option>' for b in sorted(B.BREEDS, key=lambda b: (not b.get("rank"), b["name"]))]
        opts.append("</optgroup>")
        rows.append(f'<div class="fp-row fp-dog"><label class="fp-l" for="fp-size">犬の大きさ</label><select id="fp-size">{"".join(opts)}</select></div>')
    ex = []
    if has_sen and conf.get("senior"): ex.append('<button type="button" data-v="sen" aria-pressed="false">シニア・介護が必要</button>')
    if has_pup and conf.get("puppy"): ex.append('<button type="button" data-v="pup" aria-pressed="false">子犬（1歳まで）</button>')
    if ex: rows.append('<div class="fp-row"><span class="fp-l">ほかに</span><div class="fp-btns" data-g="x">' + "".join(ex) + "</div></div>")
    if not rows: return ""
    return (f'<div class="fp" data-fp><p class="fp-t">{icon("paw")}{html.escape(title)}</p><p class="fp-lead">{html.escape(lead)}</p>'
            + "".join(rows) +
            '<p class="fp-now" aria-live="polite"></p><label class="fp-hide"><input type="checkbox"> 合わないかもしれないところを隠す</label></div>')

CSS = """<style id="fccss">
.emg-item.fc{display:block;background:#fff;border:1.5px solid var(--line,#ece6e0);border-radius:18px;padding:14px;margin:0 0 12px;box-shadow:0 2px 8px rgba(28,26,24,.04)}
.fc-top{display:flex;gap:12px;align-items:flex-start}
.fc-ph{position:relative;flex:0 0 76px;width:76px;height:76px;border-radius:16px;overflow:hidden;background:hsl(var(--fh) 60% 93%);color:hsl(var(--fh) 45% 32%);display:flex;align-items:center;justify-content:center}
.fc-mono{font-size:1.9rem;font-weight:800;line-height:1}
.fc-ci{position:absolute;right:5px;bottom:5px;width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;opacity:.7}
.fc-ph img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.fc-phbtn{position:absolute;left:4px;right:4px;bottom:4px;font-size:.7rem;font-weight:700;padding:3px 0;border:0;border-radius:999px;background:rgba(255,255,255,.92);color:var(--ink,#2b2622);display:flex;align-items:center;justify-content:center;gap:3px;cursor:pointer}
.fc-phbtn .fc-i{width:13px;height:13px}
.fc-hd{min-width:0;flex:1}
.fc-hd>a{font-size:1.04rem;line-height:1.45;text-decoration:none;color:var(--ink,#2b2622)}
.fc-hd>a b{font-weight:800}
.fc-loc{display:flex;gap:4px;align-items:flex-start;font-size:.84rem;color:var(--ink-2,#5a524b);margin:4px 0 0!important;line-height:1.5}
.fc-i{flex:0 0 auto;width:16px;height:16px;margin-top:2px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;color:var(--o,#e8590c)}
.fc-chips{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0!important;margin:10px 0 0!important}
.fc-chips li{font-size:.78rem;font-weight:700;line-height:1.3;padding:4px 10px;border-radius:999px;background:#fff3ea;color:#a8410b;margin:0!important}
.fc-rows{list-style:none;padding:0!important;margin:10px 0 0!important;display:grid;gap:6px}
.fc-rows li{display:flex;gap:6px;align-items:flex-start;font-size:.86rem;line-height:1.55;margin:0!important}
.fc-k{flex:0 0 auto;max-width:6.5em;font-size:.72rem;font-weight:700;color:var(--ink-3,#6b625b);background:#f4f1ee;border-radius:6px;padding:1px 6px;margin-top:1px;line-height:1.5}
.fc-v{min-width:0;overflow-wrap:anywhere}
.fc-for{font-size:.84rem;line-height:1.6;margin:10px 0 0!important;padding:8px 10px;background:#f6faf6;border-radius:10px;color:#2f5130}
.fc-for b{display:inline-block;font-size:.72rem;background:#2f7d32;color:#fff;border-radius:6px;padding:0 6px;margin-right:6px}
.fc-fit{font-size:.84rem;font-weight:700;line-height:1.5;margin:10px 0 0!important;padding:7px 10px;border-radius:10px}
.fc-fit small{display:block;font-weight:400;font-size:.78rem;margin-top:1px}
.fc-fit.ok{background:#e8f5e9;color:#1b5e20}.fc-fit.unk{background:#f4f1ee;color:#5a524b}.fc-fit.ng{background:#fdecea;color:#a12a1b}
.emg-item.fc.fc-ng{opacity:.62}
.emg-item.fc.fc-hid{display:none}
.fc-more{margin:10px 0 0;font-size:.84rem}
.fc-more summary{cursor:pointer;color:var(--ink-2,#5a524b);font-weight:700;font-size:.82rem;padding:2px 0}
.fc-more>small,.fc-more>p,.fc-more>ul,.fc-more>dl{display:block;margin:6px 0 0!important}
.emg-item.fc .fac-photos{margin-top:10px}
.emg-item.fc .jt-c{margin-top:8px}
.fp{background:#fffaf5;border:2px solid var(--o,#e8590c);border-radius:20px;padding:14px;margin:12px 0 16px}
.fp-t{display:flex;gap:6px;align-items:center;font-weight:800;font-size:1.04rem;margin:0 0 4px!important;color:var(--ink,#2b2622)}
.fp-t .fc-i{width:20px;height:20px;margin:0}
.fp-lead{font-size:.84rem;line-height:1.7;margin:0 0 10px!important;color:var(--ink-2,#5a524b)}
.fp-row{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin:0 0 10px}
.fp-l{font-size:.8rem;font-weight:800;color:var(--ink-3,#6b625b);min-width:5em}
.fp-btns{display:flex;flex-wrap:wrap;gap:6px}
.fp-btns button{font-size:.9rem;font-weight:700;padding:8px 14px;border-radius:999px;border:1.5px solid var(--line,#ece6e0);background:#fff;color:var(--ink,#2b2622);cursor:pointer;min-height:40px}
.fp-btns button[aria-pressed=true]{background:var(--o,#e8590c);border-color:var(--o,#e8590c);color:#fff}
.fp-row select{flex:1 1 220px;min-width:0;font-size:16px;padding:9px 10px;border:1.5px solid var(--line,#ece6e0);border-radius:12px;background:#fff;color:var(--ink,#2b2622)}
.fp-now{font-size:.84rem;margin:2px 0 6px!important;line-height:1.6;color:var(--ink,#2b2622)}
.fp-now:empty{display:none}
.fp-now b{font-weight:800}
.fp-hide{display:flex;gap:6px;align-items:center;font-size:.82rem;color:var(--ink-2,#5a524b)}
.fp-hide input{width:18px;height:18px}
@media (min-width:760px){.emg-pref:has(>.emg-item.fc){display:grid;grid-template-columns:1fr 1fr;gap:0 12px;align-items:start}.emg-pref:has(>.emg-item.fc)>:not(.emg-item){grid-column:1/-1}}
</style>"""

FIT_JS = '<script src="/fit.js" defer></script>'

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
            out, i, changed = [], 0, False
            for m in _OPEN.finditer(h):
                if m.start() < i: continue
                s = m.start(); e = _end(h, s, "div")
                out.append(h[i:s])
                c = h[s:e]
                if " fc" in m.group(0).split('"')[1].split("emg-co", 1)[1] + " ": out.append(c)
                else:
                    nc = build_card(c, conf, fbn); out.append(nc); changed |= nc != c
                i = e
            out.append(h[i:])
            h2 = "".join(out)
            if "emg-item emg-co fc" not in h2: continue
            if 'id="fccss"' not in h2:
                h2 = h2.replace("</head>", CSS + "\n</head>", 1)
                h2 = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + SPRITE, h2, count=1)
            if "data-fp" not in h2:
                fits = [json.loads(html.unescape(x)) for x in re.findall(r'data-fit="([^"]+)"', h2)]
                ku = {k for f in fits for k in f.get("a", [])}
                pn = panel(conf, ku, any("s" in f or "kg" in f for f in fits), any(f.get("sen") for f in fits), any(f.get("pup") for f in fits), len(fits))
                if pn and fits:
                    k = h2.find('class="emg-item emg-co fc')
                    # 最初のカードを含む一覧（emg-pref）の前。しぼりこみのチップや都道府県の選択が直前にあれば、その前に置く
                    em = h2.rfind('<div class="emg">', 0, k)
                    if em >= 0 and h2.count("</main>", em, k) == 0:  # 一覧の箱のいちばん上（答えの箱・数字のすぐ後ろ）
                        pos = em + len('<div class="emg">')
                        h2 = h2[:pos] + pn + h2[pos:]
                        if FIT_JS not in h2: h2 = h2.replace("</body>", FIT_JS + "\n</body>", 1)
                        open(p, "w", encoding="utf-8").write(h2); n += 1
                        continue
                    sec = h2.rfind('<section class="emg-pref"', 0, k)
                    pos = sec if sec >= 0 else h2.rfind("<div", 0, k)
                    for mark in ('<div class="fac-filter"', '<div class="hosp-pref"', '<div class="trim-cond"', '<label for="hospPref"'):
                        q = h2.rfind(mark, 0, pos)
                        if q >= 0 and pos - q < 6000 and h2.count("<section", q, pos) <= 1: pos = min(pos, q)
                    h2 = h2[:pos] + pn + h2[pos:]
                    if FIT_JS not in h2: h2 = h2.replace("</body>", FIT_JS + "\n</body>", 1)
            if h2 != h:
                open(p, "w", encoding="utf-8").write(h2); n += 1
    return n

if __name__ == "__main__":
    import sys
    sys.path.insert(0, HERE)
    print("faccard", build(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)), "pages")
