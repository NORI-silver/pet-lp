# [B] 事業者カードの共通の形（Nori 2026-11-27 00:05「タクシー以外のカード」の決まり）。cardskin.py・cardphoto.py のあと（gen_areas.py の最後）に動く。
# 決まり：
#   1. 共通の骨組み（名前・場所・写真・判断に効く項目3〜5・ボタン）に、分野ごとの項目をのせる
#   2. 「詳しく見る」はたたんでおく：料金の内訳・別料金・条件・資格・出典と確認日
#   3. 写真の上の強みは1〜2個。公式サイトの該当する項目に書いてあることだけ。書いていないことは「不可」にしない（未確認）
#   4. 口コミはサイトの中だけ（外部へ飛ばさない）。公式サイトのボタンと、ペットタクシーの料金のリンク（行き先が公開されているときだけ）
# 元データは tools/<分野>.json の facts（項目・値・出典・確認日）。何度動かしても同じ（pc の印で2回目はしない）。
import gzip, hashlib, html, json, os, re

LIMIT = 60800  # tests/info-light.test.cjs の上限（61440）に余裕を残す

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape

ICONS = {  # 画面の絵はインラインSVG（文字の絵文字は使わない）
    "yen": '<path d="M5 3l7 9 7-9M12 12v9M7 13h10M7 17h10"/>',
    "paw": '<circle cx="6" cy="10" r="2"/><circle cx="10" cy="6" r="2"/><circle cx="14" cy="6" r="2"/><circle cx="18" cy="10" r="2"/><path d="M12 12c-3 0-5 3-5 5 0 2 2 2 5 1 3 1 5 1 5-1 0-2-2-5-5-5z"/>',
    "eye": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "med": '<path d="M12 5v14M5 12h14"/><rect x="3" y="3" width="18" height="18" rx="4"/>',
    "care": '<path d="M12 21s-8-5-8-11a4.5 4.5 0 0 1 8-2.5A4.5 4.5 0 0 1 20 10c0 6-8 11-8 11z"/>',
    "pin": '<path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
}


def ic(n):
    return f'<svg class="pc-i"><use href="#pci-{n}"/></svg>'


SPRITE = '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">' + "".join(f'<symbol id="pci-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items()) + '</svg>'

CSS = ('/* 事業者カードの共通の形（tools/cardpolicy.py が /pc.css に書く）*/'
       '.pc .fc-body{padding:12px 14px}'
       '.pc .pc-top{margin:0 0 6px}.pc .pc-n{display:block;font-weight:800;font-size:1.02rem;color:#2b2622;text-decoration:none;line-height:1.35}'
       '.pc .pc-loc{display:flex;gap:5px;align-items:center;margin:3px 0 0;font-size:.8rem;color:#7a6a5e}.pc .pc-loc::before{content:"";flex:0 0 18px;width:18px;height:18px;background:#5b4a3d;-webkit-mask:var(--i) center/contain no-repeat;mask:var(--i) center/contain no-repeat}'
       '.pc .pc-i{flex:0 0 18px;width:18px;height:18px;fill:none;stroke:#5b4a3d;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}'
       '.pc .pc-f li::before{content:"";width:18px;height:18px;background:#5b4a3d;-webkit-mask:var(--i) center/contain no-repeat;mask:var(--i) center/contain no-repeat}'
       + "".join('.pc .pc-f li.%s::before,.pc .pc-loc.%s::before{--i:url("data:image/svg+xml,%%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%%23000\' stroke-width=\'1.9\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%%3E%s%%3C/svg%%3E")}' % (k, k, v.replace('"', "'").replace('<', '%3C').replace('>', '%3E')) for k, v in ICONS.items()) +
       '.pc .pc-f{display:grid;gap:6px;margin:10px 0 0;padding:0;list-style:none}'
       '.pc .pc-f li{display:grid;grid-template-columns:18px 6.2em 1fr;gap:6px;align-items:start;font-size:.85rem;line-height:1.5;color:#4a3f37;margin:0}'
       '.pc .pc-f b{font-weight:700;color:#7a6a5e;font-size:.78rem;line-height:1.7}'
       '.pc .pc-f i{font-style:normal;color:#8f8378}'
       '.pc .pc-m{margin:10px 0 0;font-size:.85rem}.pc .pc-m a{color:#a8410a;font-weight:700;text-decoration:none}'
       '.pc .pc-d{margin:10px 0 0;border-top:1px solid #f5ebe2;padding-top:2px}'
       '.pc .pc-d summary{list-style:none;cursor:pointer;font-size:.85rem;font-weight:700;color:#a8410a;padding:7px 0}'
       '.pc .pc-d summary::-webkit-details-marker{display:none}.pc .pc-d summary::before{content:"＋ "}.pc .pc-d[open] summary::before{content:"－ "}'
       '.pc .pc-dl{display:grid;gap:7px;font-size:.82rem;color:#4a3f37;line-height:1.55}.pc .pc-dl p{margin:0}.pc .pc-dl b{display:block;font-weight:700;color:#7a6a5e;font-size:.76rem}'
       '.pc .pc-d small a{color:#a8410a}.pc .pc-d small{display:block;color:#8f8378;font-size:.72rem;margin-top:6px}'
       '.pc .pc-a{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}'
       '.pc .pc-a a{display:flex;align-items:center;justify-content:center;text-align:center;border-radius:12px;padding:10px 6px;font-weight:800;font-size:.86rem;text-decoration:none;background:#2b2622;color:#fff!important;border:1px solid #2b2622;min-width:0}'
       '.pc .pc-a .pc-ask{grid-column:1/-1;background:#fff;color:#7a5a3a;border:1px dashed #d9c9bb;border-radius:12px;padding:8px;font-weight:700;font-size:.82rem;cursor:pointer}'
       '.pc .pc-a a.l{background:#fff;color:#2b2622!important;border-color:#d9c9bb}.pc .pc-a a:only-child{grid-column:1/-1}'
       '.pc .cs-ph{position:relative}.pc .pc-ov{position:absolute;left:8px;bottom:26px;display:flex;flex-wrap:wrap;gap:5px;max-width:calc(100% - 16px);pointer-events:none}'
       '.pc .pc-ov span{background:rgba(43,38,34,.82);color:#fff;font-size:.74rem;font-weight:800;border-radius:999px;padding:3px 10px;line-height:1.3}'
       )
CSS_LINK = '<link rel="stylesheet" href="/pc.css?v=%s" id="pc-css">' % hashlib.md5(CSS.encode("utf-8")).hexdigest()[:8]

# ---- 分野ごとの決まり（項目の名前・元の項目・見つからないとき） ----
def _fact(h, *keys):
    for k in keys:
        for f in h.get("facts", []):
            if f.get("k") == k or (k.endswith("*") and f.get("k", "").startswith(k[:-1])):
                return f
    return None


def _txt(f):
    return (f or {}).get("v", "")


def _price_note(v):
    # 公式の文のまま出す。入所金と月額を分けて書いていない文は、分けて読めると思わせない
    return ""


def _vet_resident(h):
    # この施設（老犬ホーム）自身の公式の項目・ページに「獣医師が常駐/常勤」と書いてあるときだけ（隣の動物病院や回診は含めない）
    t = h.get("web", {}).get("text", "")
    return bool(re.search(r"獣医師[^。]{0,8}(常駐|常勤)", h.get("spec", "")) and re.search(r"獣医師(が)?(常駐|常勤)", t))


def rojin_fields(h):
    """老犬ホームの判断に効く5つ。値は公式サイトの項目から。なければ「未確認」。
    大型犬の条件・予約の条件・見守りカメラは、判断が変わる条件なので、書いてあるものはたたまずに該当の項目に「項目名：」つきで出す。"""
    price = _fact(h, "料金", "料金*")
    cond = _fact(h, "受け入れ条件", "受け入れ（公式サイトの文）", "受け入れ")
    big = _fact(h, "大型犬の条件")
    visit = h.get("visit") or _txt(_fact(h, "見学・面会", "見学", "面会"))
    resv = _fact(h, "予約の条件")
    med = _fact(h, "病院", "体制")
    cam = _fact(h, "見守りカメラ")
    care = _fact(h, "ふくまれるお世話", "お世話", "介護", "食事")
    spec = h.get("spec", "")
    medv = " ".join(x for x in (_txt(med), "獣医師が常駐" if _vet_resident(h) and not med else "", ("見守りカメラ：" + _txt(cam)) if cam else "") if x)
    acc = " ".join(x for x in (h.get("animals", ""), _txt(cond), ("大型犬の条件：" + _txt(big)) if big else "") if x)
    vis = " ".join(x for x in (visit, ("予約の条件：" + _txt(resv)) if resv else "") if x)
    return [
        ("yen", "費用例（内訳未確認）" if re.search(r"入所金・月額", _txt(price)) else "料金", _guard(_txt(price)), price),
        ("paw", "受け入れ", acc, cond),
        ("eye", "見学・面会", vis, None),
        ("med", "医療・見守り", medv, med),
        ("care", "お世話", _txt(care), care),
    ]


def rojin_overlay(h):
    """写真に重ねる強み（公式サイトの項目に書いてあるものだけ・最大2つ）。"""
    out = []
    if _vet_resident(h): out.append("獣医師が常駐")
    cam = _fact(h, "見守りカメラ")
    if cam: out.append("見守りカメラ")
    tx = _fact(h, "送迎")
    if tx and re.search(r"無料", _txt(tx)): out.append("送迎無料")
    return out[:2]


def rojin_detail(h):
    """たたむ中身：のこりの項目すべて（出典と確認日つき）と登録番号。"""
    used = {"料金", "受け入れ条件", "受け入れ（公式サイトの文）", "受け入れ", "大型犬の条件", "病院", "体制", "見守りカメラ", "ふくまれるお世話", "お世話", "介護", "食事", "見学・面会", "見学", "面会"}
    rows = []
    for f in h.get("facts", []):
        rows.append((f["k"], f["v"], f.get("src"), f.get("checked")))
    if any(re.search(r"入所金・月額", f.get("v", "")) for f in h.get("facts", [])):
        rows.insert(0, ("費用の内訳について", "公式サイトに「入所金・月額は各」とだけ書かれており、入所金と月額が別々の金額か同じ金額かは確認できていません。月額の目安として読まず、公式サイトをご覧ください。", None, None))
    if h.get("reg"): rows.append(("動物取扱業の登録番号", h["reg"], h.get("url"), None))
    return rows


def _pickup_free(h):
    tx = _txt(_fact(h, "送迎"))
    if not tx or re.search(r"行っておりません|行っていません|ありません|不可|できません|なし", tx): return ""
    m = re.search(r"([^。、「」（）()\s]{2,10}(?:市内|区内|町内|圏内|エリア内|周辺|以内))[^。]{0,14}無料", tx)
    return (m.group(1) + "は送迎無料") if m else ""


_ADD = re.compile(r"延長|追加|時間外|割増|オプション|別途|超過|加算|深夜|早朝|繁忙|連休|年末年始")


def _addon_only(v):
    """お金の出てくる文（／。で区切った1つずつ）が、すべて延長・追加・時間外などの上乗せの文か。そうなら、基本料金は書かれていない。
    かっこの中は数えない。上乗せの言葉より前に金額がある文、上乗せの言葉のない金額つきの文があれば、基本料金ありとして、そのまま出す。"""
    v = re.sub(r"[(（【][^)）】]*[)）】]", "", v)
    if re.search(r"基本料金[^、。]{0,6}\d", v): return False
    add = 0
    for s in re.split(r"[／/。\n]", v):
        if not re.search(r"[円¥￥]", s): continue
        k = _ADD.search(s)
        if not k and not add: return False  # 最初にお金が出てくる文が上乗せの文でないなら、基本の料金とみなす
        if k:
            if re.search(r"[\d,，]+\s*円|[¥￥]\s*\d", s[:k.start()]): return False
            add += 1
        elif len(re.sub(r"[\d,，.~〜～+＋\s円¥￥頭匹税込別0-9]", "", s)) > 2: return False
    return add > 0


def _guard(v):
    return ("基本料金：未確認（延長・追加などの料金の記載のみ。内容は「詳しく見る」）" if v and _addon_only(v) else v)


def _base_price(t):
    """1泊（1日）の基本料金の文か。時間外・延長・追加の料金だけの文は基本料金にしない。"""
    return bool(re.search(r"(1|１|一)泊|宿泊|お泊|1日|１日|24時間|泊まり|/泊", t)) and not re.match(r"\s*(時間外|延長|追加|オプション)", t)


def hotel_fields(h):
    """ペットホテルの判断に効く5つ。値は公式サイトの項目から。なければ「未確認」。
    料金は1泊の基本料金と追加料金（時間外・延長など）を分ける。設備・体制は、公式に書いてある項目ごとに名前をつけて出す（まとめて「安心」とは言わない）。"""
    price = _fact(h, "料金")
    cond = _fact(h, "受け入れ条件", "受け入れの注意")
    animal = _fact(h, "対象の動物")
    hours = _fact(h, "営業・受付時間")
    stay = _fact(h, "預かり期間")
    pick = _fact(h, "送迎")
    resv = _fact(h, "予約のしかた", "予約")
    pv = _txt(price)
    if not pv: pr = ""
    elif _base_price(pv): pr = pv
    else: pr = "1泊の基本料金：未確認／追加料金（公式の記載）：" + pv
    tv = (h.get("trust") or {}).get("vet", {}) if isinstance(h.get("trust"), dict) else {}
    eq = []
    # 絞り込みの印（data-flags）は「その言葉が書いてある」だけで、可否の根拠にならない（「送迎なし」「大型犬不可」でも付く）。事実として出さない。もとのカードの施設ごとの文は「詳しく見る」に残す
    if h.get("private_room"): eq.append("個室：あり")
    if h.get("camera"): eq.append("見守りカメラ：あり")
    if h.get("night_staff"): eq.append("夜間のスタッフ：あり")
    if h.get("run"): eq.append("ドッグラン：あり")
    if tv.get("v"): eq.append("獣医・病院：" + tv["v"])
    acc = " ".join(x for x in (_txt(animal), _txt(cond), ("大型犬 " + str(h["max_kg"]) + "kgまで") if h.get("large") and h.get("max_kg") else "", "") if x)
    off = _fact(h, "定休日")
    hr = " ".join(x for x in (_txt(hours), ("定休日：" + _txt(off)) if off and "定休日" not in _txt(off) else _txt(off), _txt(stay), ("予約：" + _txt(resv)) if resv else "") if x)
    return [
        ("yen", "料金", pr, price),
        ("paw", "受け入れ", acc, cond or animal),
        ("eye", "受付・預かり", hr, hours),
        ("pin", "送迎", _txt(pick), pick),
        ("med", "設備・体制", "／".join(eq), None),
    ]


def hotel_overlay(h):
    out = []
    if h.get("large") and h.get("max_kg"): out.append(f"大型犬可（{h['max_kg']}kgまで）")
    pf = _pickup_free(h)
    if pf: out.append(pf)
    return out[:2]


def hotel_detail(h):
    rows = [(f["k"], f["v"], f.get("src"), f.get("checked")) for f in h.get("facts", [])]
    t = h.get("trust", {})
    if isinstance(t, dict) and t.get("reg"):
        r = t["reg"]; ka = "・".join(x for x in (r.get("kind"), r.get("auth")) if x)
        v = r.get("no", "") + (f"（{ka}）" if ka else "")
        if r.get("until"): v += "／有効期限：" + r["until"]
        if isinstance(r.get("registry"), dict) and r["registry"].get("asof"): v += f"／{r['registry'].get('name','')}の登録簿：{r['registry']['asof']}時点"
        rows.append(("動物取扱業の登録番号", v, r.get("src"), r.get("checked")))
    return rows


def sitter_fields(h):
    """ペットシッター（家に来てくれる）の判断に効く5つ。事業者の公式の項目だけ。お客さんの家が分かる書き方はしない。"""
    price = _fact(h, "料金")
    trip = _fact(h, "交通費・出張費", "出張費")
    area = _fact(h, "対応エリア")
    animal = _fact(h, "対応する動物")
    ins = _fact(h, "保険")
    reg = _fact(h, "動物取扱業")
    first = _fact(h, "初回・契約")
    canc = _fact(h, "キャンセル料")
    key = _fact(h, "鍵")
    hrs = _fact(h, "営業・受付時間")
    pay = _fact(h, "お支払い")
    pv = " ".join(x for x in (_guard(_txt(price)), ("出張費：" + _txt(trip)) if trip else "") if x)
    av = h.get("area") or _txt(area)
    an = _txt(animal) or h.get("animals", "")
    sv = " ".join(x for x in (("保険：" + _txt(ins)) if ins else "", ("動物取扱業：" + _txt(reg)) if reg else "") if x)
    rv = " ".join(x for x in (("初回・契約：" + _txt(first)) if first else "", ("キャンセル料：" + _txt(canc)) if canc else "", ("鍵：" + _txt(key)) if key else "") if x)
    return [
        ("yen", "料金", pv, price),
        ("pin", "対応エリア", av, area),
        ("paw", "対応する動物", an, animal),
        ("med", "保険・登録", sv, ins or reg),
        ("eye", "契約・キャンセル", rv, first or canc) if (rv or not (hrs or pay)) else ("eye", "お支払い" if (pay and not hrs) else ("受付時間" if (hrs and not pay) else "受付・お支払い"), " ".join(x for x in (_txt(hrs), ("お支払い：" + _txt(pay)) if pay else "") if x), hrs or pay),
    ]


def sitter_overlay(h):
    out = []
    if _fact(h, "動物取扱業"): out.append("動物取扱業の登録あり")
    if _fact(h, "保険"): out.append("シッター保険の記載あり")
    return out[:2]


def sitter_detail(h):
    return [(f["k"], f["v"], f.get("src"), f.get("checked")) for f in h.get("facts", [])]


SPEC = {"rojin": (rojin_fields, rojin_overlay, rojin_detail), "hotel": (hotel_fields, hotel_overlay, hotel_detail), "sitter": (sitter_fields, sitter_overlay, sitter_detail)}
DATA = {"rojin": ("rojin.json", "homes"), "hotel": ("hotels.json", "hotels"), "sitter": ("sitters.json", "sitters")}


def _load(cat):
    fn, key = DATA[cat]
    j = json.load(open(os.path.join(HERE, fn), encoding="utf-8"))
    D = {}
    for x in j[key]:
        if cat == "hotel":
            D.setdefault(x["url"], []).append(x)
        else: D[x["id"]] = x
    return D


def _norm(t):
    import unicodedata
    return re.sub(r"[\s　・\-－()（）【】「」『』/／]|店$|本店|支店", "", unicodedata.normalize("NFKC", t)).lower()


def _end(h, i):
    d = 0
    for m in re.compile(r"<(/?)div\b[^>]*>").finditer(h, i):
        d += -1 if m.group(1) else 1
        if d == 0: return m.end()
    return -1


def _taxi_ok(h):
    # 行き先が公開されているときだけ。「所在地は見学の方に個別に案内」のところは出さない（行き先が分からない）
    return bool(h.get("addr")) and not re.search(r"個別|非公開|お問い合わせ", h.get("visit", ""))


_FLAG_SENT = ("大型犬を泊められる", "猫専用のホテル", "猫も泊められる", "動物病院が併設・運営", "送迎がある", "シニア・介護・投薬の子を受ける", "夜もスタッフがいる", "カメラで様子を見られる", "ドッグランがある")


def card(blk, h, cat, more=None, compact=False):
    fields, overlay, detail = SPEC[cat]
    if cat == "sitter" and not h.get("animals"):  # 対応する動物：項目がなければ、一覧の絞り込みに使っている「対応する動物」（data-fit の at）を使う
        at = re.search(r'data-fit=\'\{[^\']*"at":"([^"]+)"', blk[:2500])
        if at: h = dict(h, animals=html.unescape(at.group(1)))
    ot = re.match(r"<div[^>]*>", blk).group(0)
    ot = re.sub(r'class="([^"]*)"', lambda m: f'class="{m.group(1)} pc"', ot, count=1)
    _fid = re.search(r' data-fid="([^"]+)"', ot)
    if _fid and not re.search(r" id=\"", ot): ot = ot[:-1] + f' id="c-{_fid.group(1)}">'  # 県・市のページへのリンクが、カードの位置まで開くための目印
    ph = re.search(r'<div class="cs-ph.*?(?=<div class="fc-body">)', blk, re.S)
    ph = ph.group(0) if ph else ""
    ov = overlay(h)
    if ov and ph:
        ph = re.sub(r"(<small class=\"cs-ph-c\")", '<div class="pc-ov">' + "".join(f"<span>{E(x)}</span>" for x in ov) + r"</div>\1", ph, count=1)
    name, url = h["name"], h["url"]
    locv = h.get("addr") or h.get("area") or "".join(h.get("prefs", [])) + h.get("city", "")
    fl = fields(h)
    loc = "" if any(v == locv for _, _, v, _ in fl) else f'<p class="pc-loc pin"><span>{E(locv)}</span></p>'  # 同じ文を2回出さない
    top = f'<div class="pc-top"><a class="pc-n" href="{E(url)}" target="_blank" rel="noopener"><b>{E(name)}</b></a>{loc}</div>'
    li = []
    for icn, lab, val, f in fl:
        v = E(val) if val else '<i>未確認</i>'
        li.append(f'<li class="{icn}"><b>{lab}</b><span>{v}</span></li>')  # 項目の絵はCSS（::before）。1枚ずつSVGを置かない（重いページの容量のため。ラベルの文字が意味を持つ）
    shown = " ".join(v for _, _, v, _ in fl)
    rows = [r for r in detail(h) if r[1] not in shown]  # カードの項目にそのまま出した文は、くり返さない
    # もとのカードに書いてあった施設ごとの記載（「そのほか」の中・条件の1行・一覧の行）のうち、新しい項目にも出ていないものは消さずに「詳しく見る」に残す
    _n = lambda x: re.sub(r"[、。，,．・：:／/（）()\s]", "", x)
    have = _n(shown + " " + " ".join(r[1] for r in rows) + " " + locv + " " + " ".join(ov))
    old_txt = []
    for rx_ in (r'<div class="fc-more-b">(.*?)</div></details>', ):
        for m_ in re.finditer(rx_, blk, re.S): old_txt += re.findall(r"<small[^>]*>(.*?)</small>", m_.group(1), re.S)
    old_txt += re.findall(r'<p class="fc-line"[^>]*><span[^>]*>(.*?)</span></p>', blk, re.S)
    old_txt += re.findall(r'<p class="ux-c-l[^"]*"><i[^>]*>[^<]*</i><span>(.*?)</span></p>', blk, re.S)
    kept = []
    for x in old_txt:
        x = html.unescape(re.sub(r"<[^>]+>", "", x)).strip()
        if len(x) < 6 or re.match(r"(出典|確認日)", x) or re.search(r"(公式サイト|店舗一覧|サイト)より$", x): continue
        _r = x
        for lab_ in _FLAG_SENT: _r = _r.replace(lab_, "")
        if not _r.replace("・", "").strip(): continue  # 「その言葉が書いてある」だけで作った旧チップの文（gen_hotels.CONDS の言葉だけをつないだ1行）は、事実として残さない。本物の文の中の言葉は消さない
        if len(x) < 6: continue
        body = x.split("：", 1)[1] if "：" in x[:12] else x
        if "：" not in x[:12]:  # 項目名のない一文：すでに出ている文と半分以上が同じなら、くり返さない
            from difflib import SequenceMatcher
            nb_ = _n(x)
            mm_ = SequenceMatcher(None, have, nb_, autojunk=False).find_longest_match(0, len(have), 0, len(nb_)) if nb_ and have else None
            if mm_ and mm_.size >= 5:
                rest_ = re.sub(r"お世話する|お世話|いたします|できます|します|です|ます|する|こと", "", nb_[:mm_.b] + nb_[mm_.b + mm_.size:])
                if len(rest_) == 0:  # すでに出ている文の言い回し違いだけ。条件・金額・日付などの固有の語が残るときは落とさない
                    if os.environ.get("CP_LOG"): open(os.environ["CP_LOG"], "a", encoding="utf-8").write(f"{h.get('id','')}\t{x}\t{[r[1] for r in fl if r[2]]}\n")
                    continue  # 「項目名：中身」の形は、中身がすでに出ていれば、くり返さない
        nb, nx = _n(body), _n(x)
        if nx in have or nb in have or nx in _n(" ".join(kept)): continue
        if any(len(_n(r[1])) >= 6 and _n(r[1]) in nx for r in rows): continue  # すでに出ている項目の値をふくむ文
        if any(len(_n(v_)) >= 6 and nb in _n(v_) for _, _, v_, _ in fl): continue  # カードの項目の文の一部
        kept.append(x)
    def _lab(x):
        m_ = re.match(r"([^：]{2,10})：(.+)", x, re.S)
        return (m_.group(1), m_.group(2)) if m_ else ("ほかの記載", x)
    rows = rows + [(*_lab(x), None, None) for x in kept]
    # 「項目名：中身」を1つの文として出す（元のカードの書き方と同じ）。項目名を別のタグに分けると、検索に出すかどうかの字数（thin_gate）が、同じ事実でも減る
    dl = "".join((f"<p>{E(k)}：{E(v)}</p>" if k != "ほかの記載" else f"<p>{E(v)}</p>") for k, v, s, c in rows)
    srcs = list(dict.fromkeys([(f_.get("src"), f_.get("checked")) for _, _, _, f_ in fl if isinstance(f_, dict) and f_.get("src")] + [(s, c) for k, v, s, c in rows if s]))  # 出典と確認日は同じものを1回だけ
    if srcs:
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        def one(i, s, c):
            same = compact and urlparse(s).netloc == host  # 重いページだけ：公式サイトと同じサイトの出典は、リンクを重ねず「公式サイト」と確認日だけ（カードの公式サイトのボタンと同じ）
            lab = f'<a href="{E(s)}" target="_blank" rel="noopener">公式サイト{"" if i == 0 else i + 1}</a>' if not same else f'公式サイト{"" if i == 0 else i + 1}'
            return lab + (f"（確認日 {E(c)}）" if c else "")
        dl += "<small>出典：" + "／".join(one(i, s_, c) for i, (s_, c) in enumerate(srcs[:3])) + "</small>"
    if more:  # 全国のページが重いときは、くわしい中身を県のページのカードに置き、ここからリンクする（カードは減らさない）
        det = f'<p class="pc-m"><a href="{E(more)}">県のページで詳しく見る（料金・条件の全文と出典）→</a></p>'
    else:
        det = f'<details class="pc-d"><summary>詳しく見る</summary><div class="pc-dl">{dl}</div></details>' if dl else ""  # 追加の項目がなくても、出典と確認日（元のデータにあるものだけ）は必ず見られるようにする
    btn = [f'<a href="{E(url)}" target="_blank" rel="noopener">公式サイト ↗</a>']
    from urllib.parse import quote
    # ペットタクシーの料金：行き先が公開されているときは行き先を入れて開く。公開されていない（個別案内など）ときは、行き先なしの通常の料金ページ
    to = f"/?to={quote(h['addr'][:80], safe='')}#form" if cat != "sitter" and _taxi_ok(h) else "/#form"  # 出張型のシッターは行き先を入れない（お客様の自宅を特定しない）
    btn.append(f'<a class="l" href="{to}"' + ("" if compact else f' aria-label="{E(name)}までのペットタクシー料金"') + '>タクシー料金</a>')  # 大きいページ（compact）では、ボタンの文字だけにして容量を節約
    score = re.search(r'<div class="emg-score" data-id="[^"]*"></div>', blk)  # サイトの中の口コミ（外へ飛ばさない）
    body = top + f'<ul class="pc-f">{"".join(li)}</ul>' + "" + det + f'<div class="pc-a">{"".join(btn)}</div>'
    return ot + ph + '<div class="fc-body">' + body + "</div></div>"


def _convert(h, cat, D, lite, compact=False):
    out, pos, n = [], 0, 0
    if cat == "hotel":
        rx = re.compile(r'<div class="emg-item emg-co fc cs"[^>]*>(?=.*?class="ux-c-n" href="([^"]+)")', re.S)
    else:
        rx = re.compile(r'<div class="emg-item emg-co fc cs"[^>]*? data-cat="%s" data-fid="([^"]+)"[^>]*>' % cat)
    for m in rx.finditer(h):
        key = html.unescape(m.group(1))
        if m.start() < pos or key not in D: continue
        hit = D[key]
        if cat == "hotel":
            # 同じ公式URLを使う別の店・別の支店の事実を借りない：市区町村がカードと同じ1件に決まるときだけ
            cy = re.search(r' data-city="([^"]*)"', m.group(0))
            cy = html.unescape(cy.group(1)) if cy else ""
            c2 = [x for x in hit if x.get("city") == cy] if cy else (hit if len(hit) == 1 else [])
            nm0 = re.search(r'class="ux-c-n"[^>]*><b>(.*?)</b>', h[m.start():m.start() + 6000], re.S)
            cname = _norm(html.unescape(re.sub(r"<[^>]+>", "", nm0.group(1)))) if nm0 else ""
            # 市区町村が同じ1件でも、カードの名前と記録の名前が合わないときは（同じ公式URLの別の支店など）事実を借りない
            if len(c2) == 1 and cname and not (_norm(c2[0]["name"]) in cname or cname in _norm(c2[0]["name"])): c2 = []
            if len(c2) != 1:
                nm = re.search(r'class="ux-c-n"[^>]*><b>(.*?)</b>', h[m.start():m.start() + 6000], re.S)
                c2 = [{"name": html.unescape(re.sub(r"<[^>]+>", "", nm.group(1))) if nm else hit[0]["name"], "url": hit[0]["url"], "prefs": [], "city": cy, "facts": []}]
            hit = dict(c2[0])
            fgm = re.search(r' data-flags="([^"]*)"', m.group(0))
            hit["_flags"] = fgm.group(1).split() if fgm else []
        j = _end(h, m.start())
        if j < 0: continue
        if cat == "hotel" and not re.match(r'.*?class="ux-c-n" href="%s"' % re.escape(m.group(1)), h[m.start():j], re.S): continue
        more = None
        if lite:  # この箱（県）の見出しのリンク
            sec = h.rfind('<section class="emg-pref"', 0, m.start())  # 同じ県の箱の見出しにリンクがあるときだけ（ほかの県のリンクは使わない）
            lk = re.match(r'<section class="emg-pref"[^>]*><h4><a href="([^"]+)"', h[sec:sec + 400]) if sec >= 0 else None
            more = lk.group(1) if lk else None
        out.append(h[pos:m.start()]); out.append(card(h[m.start():j], hit if cat == "hotel" else D[key], cat, more, compact)); pos = j; n += 1
    out.append(h[pos:])
    return "".join(out), n


def _gz(x):
    # tests/info-light.test.cjs は node の zlib（レベル9）で数える。python の gzip とは数百バイトずれるので、同じ node で数える
    import subprocess
    r = subprocess.run(["node", "-e", "const z=require('zlib');let b=[];process.stdin.on('data',d=>b.push(d)).on('end',()=>console.log(z.gzipSync(Buffer.concat(b),{level:9}).length))"], input=x.encode("utf-8"), capture_output=True, check=True)
    return int(r.stdout)


def _fin(h2):
    return h2.replace("</head>", CSS_LINK + "</head>", 1)  # 見た目は /pc.css（ページごとに重ねない。build が書く）


def page(h, cat, D):
    if 'id="pc-css"' in h or "/pc.css" in h: return h
    h2, n = _convert(h, cat, D, False)
    if not n: return h
    if len(h2) > 150000 and _gz(_fin(h2)) > LIMIT:
        # 全国のページが重すぎるとき：カードは1枚も減らさず、まず出典のリンクを軽くし、次に「詳しく見る」の中身を県のページのカードに置く。それでも重ければ faccard.py と同じ県ごとの件数の絞り込み
        h2, n = _convert(h, cat, D, False, True)
        if _gz(_fin(h2)) > LIMIT: h2, n = _convert(h, cat, D, True, True)
        if _gz(_fin(h2)) > LIMIT:
            import faccard
            for keep in (8, 6, 4, 3, 2):
                h3 = faccard._trim(h2, keep)
                if _gz(_fin(h3)) <= LIMIT: h2 = h3; break
            else: h2 = faccard._trim(h2, 2)
    return _fin(h2)


def build(root, cats=("rojin", "hotel", "sitter")):
    n = 0
    open(os.path.join(root, "pc.css"), "w", encoding="utf-8").write(CSS + "\n")
    top = {"rojin": "rojin-home", "hotel": "pet-hotel", "sitter": "pet-sitter"}
    for cat in cats:
        D = _load(cat)
        for dp, dn, fn in os.walk(os.path.join(root, top[cat])):
            if "index.html" not in fn: continue
            f = os.path.join(dp, "index.html")
            t = open(f, encoding="utf-8").read()
            u = page(t, cat, D)
            if u != t: open(f, "w", encoding="utf-8").write(u); n += 1
    for cat in cats: _relink(root, top[cat])
    return n


def _relink(root, top):
    """全国のページの簡易カード（県のページで詳しく見る）のリンクを、カードが実際にある宛先に直す。県のページにカードがなければ（市のページだけにある）、その市のページ。見つからないときはリンクを出さず、中身をカードに戻すのではなく、このカードだけ宛先なし（呼び出し側が検出できるよう例外にする）"""
    where = {}
    pages = {}
    for dp, dn, fn in os.walk(os.path.join(root, top)):
        if "index.html" not in fn: continue
        rel = "/" + os.path.relpath(dp, root).replace(os.sep, "/") + "/"
        if rel == "/" + top + "/": continue
        t = open(os.path.join(dp, "index.html"), encoding="utf-8").read()
        pages[rel] = t
        for m in re.finditer(r'<div class="emg-item[^>]*? data-fid="([^"]+)"', t):
            where.setdefault(m.group(1), []).append(rel)
    f = os.path.join(root, top, "index.html")
    t = open(f, encoding="utf-8").read()
    if 'class="pc-m"' not in t: return
    parts = re.split(r'(?=<div class="emg-item[^>]*? data-fid=")', t)
    for k, blk in enumerate(parts):
        if 'class="pc-m"' not in blk: continue
        fid = re.match(r'<div class="emg-item[^>]*? data-fid="([^"]+)"', blk).group(1)
        c = sorted(set(where.get(fid, [])), key=lambda r: (r.count("/"), r))
        if not c: raise SystemExit(f"relink: {top} {fid} 宛先のページがない")
        parts[k] = re.sub(r'(<p class="pc-m"><a href=")[^"]*"', lambda q: q.group(1) + c[0] + "#c-" + fid + '"', blk, count=1)
    t2 = "".join(parts)
    if t2 != t: open(f, "w", encoding="utf-8").write(t2)


if __name__ == "__main__":
    import sys
    print("cardpolicy", build(sys.argv[1] if len(sys.argv) > 1 else "."), "pages")
