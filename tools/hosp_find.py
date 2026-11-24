"""動物病院を「自分の条件で」さがす欄（/hospital/ と、その下の条件・県・市区町村のページで共通）。

Nori 2026-11-15「このページひどすぎ」「自分の条件で探せるようにして」「自分にあった病院を見つけたいんじゃないの？」
「この見せ方なら犬猫が対象じゃないように見える」「このフィルター、ほとんどフィルターできなくない？もっとあるでしょ」

- 全部の病院（夜間・救急／往診／猫専門／エキゾチック／大型犬の設備／獣医師会の一覧のふつうの病院）を県ごとの JSON
  （/hospital/data/<県>.json）にまとめ、/hosp.js が選んだ条件に合う病院をその場でカードに並べる。
- 選ぶ欄は1つの箱。場所（県→市区町村）・うちの子（犬・猫も含めて）・いつ・病院の種類・診療科目・設備とサービスを、
  すべて同じ形のボタンで選ぶ。ボタンは、その県のデータで1院以上に当てはまるものだけ出す。
- 書いてあることだけで判定する。書いていない病院は外さず「書いていないので要確認」として後ろに並べる。
  犬・猫は書いていなくても診る（「猫だけ」「犬だけ」とはっきり書く病院だけ外す）。
- 電話番号・順位・おすすめは出さない。並び順は合う順→市区町村の順。
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

# うちの子（犬・猫も出す。犬・猫はほぼ全院なので、例外の動物を追加の選択肢として並べる）
ANIMALS = [("dog", "犬"), ("cat", "猫"), ("rabbit", "うさぎ"), ("hamster", "ハムスター・モルモット"), ("ferret", "フェレット"),
           ("bird", "鳥"), ("reptile", "爬虫類"), ("fish", "魚")]
_AN_RX = {"rabbit": r"うさぎ|ウサギ|兎", "hamster": r"ハムスター|モルモット|チンチラ|デグー|ラット|マウス|リス",
          "ferret": r"フェレット", "bird": r"鳥|インコ|オウム|文鳥|トリ", "reptile": r"爬虫|は虫|カメ|亀|トカゲ|ヘビ|蛇|リクガメ",
          "fish": r"魚"}
# いつ（open＝いま受付中。曜日で変わらない受付時間 t と休診の文から hosp_find.js がその場で判定する）
WHEN = [("open", "いま受付中"), ("night", "夜間・救急"), ("h24", "24時間"), ("late", "19時以降も"), ("early", "朝9時前から"),
        ("sat", "土曜も"), ("sun", "日曜も"), ("hol", "祝日も"), ("nohol", "年中無休"), ("nolunch", "昼休みなし")]
# 病院の種類・こんなとき
KIND = [("visit", "家に来てくれる（往診）"), ("catspec", "猫専門"), ("exospec", "うさぎ・鳥などの専門"),
        ("large", "大型犬の設備"), ("catroom", "猫用の待合室"), ("noresv", "予約なしでも"), ("resv", "予約できる")]
# 設備・サービス
SVC = [("park", "駐車場"), ("card", "カード払い"), ("ins", "ペット保険が使える"), ("hotel", "ペットホテル"), ("trim", "トリミング"),
       ("school", "しつけ教室・パピークラス"), ("ct", "CT・MRI")]
# 症状・お悩みから探す（飼い主さんの言葉 → 診療科目。科目は公式サイトの文から depts_of が決めたものだけを見る）
SYMPTOMS = [("吐く・下痢", ["消化器科"]), ("皮膚のかゆみ", ["皮膚科"]), ("咳", ["呼吸器科", "循環器科"]),
            ("歩き方がおかしい", ["整形外科", "神経科"]), ("目・耳の異常", ["眼科", "耳鼻科"])]
LABEL = dict(ANIMALS + WHEN + KIND + SVC)
LABEL.update({"y:" + n: n for n, _ in SYMPTOMS})


def _t(*xs):
    return " ".join(str(x) for x in xs if x)


def _facts(h, *keys):
    return " ".join(f["v"] for f in h.get("facts", []) if any(k in f["k"] for k in keys))


def _times(s):
    """「9:00〜12:00」「8時30分〜13時」などから (始め, 終わり) の分を取り出す。"""
    out = []
    for m in re.finditer(r"(\d{1,2})(?::(\d{2})|時(\d{1,2})?分?)?\s*[〜~～\-－]\s*(?:翌)?(\d{1,2})(?::(\d{2})|時(\d{1,2})?分?)?", s):
        a = int(m.group(1)) * 60 + int(m.group(2) or m.group(3) or 0)
        b = int(m.group(4)) * 60 + int(m.group(5) or m.group(6) or 0)
        if "翌" in m.group(0) or b < a: b += 24 * 60
        if 0 <= a <= 24 * 60: out.append((a, b))
    return out


def _tels():
    """夜間・救急の病院の電話番号（night_hospital_facts.json の tel・tel_src。公式サイトにある番号だけ）。"""
    import json as _j
    try: its = _j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "night_hospital_facts.json"), encoding="utf-8"))["items"]
    except Exception: return {}
    return {x["id"]: x for x in its if x.get("tel") and x.get("tel_src") and not x.get("closed")}
_TEL = _tels()

def record(h, pref, tags, depts_of):
    """1院を検索用の短い形にする。y＝書いてある（合う）、n＝はっきり合わない。どちらにもない項目は「書いていない」。"""
    y, n = set(tags), set()
    hours = _t(h.get("hours"), _facts(h, "診療時間", "受付時間", "夜間・時間外"))
    closed = h.get("closed") if isinstance(h.get("closed"), str) else ""
    closed = _t(closed, _facts(h, "休診日"))
    animals = h.get("animals") or _facts(h, "対象の動物", "診る動物")
    spec = _t(h.get("spec"))
    svc = _t(h.get("services"), _facts(h, "設備", "駐車場", "猫にやさしい工夫", "大型犬のための設備"))
    pay = _t(h.get("pay"), _facts(h, "支払い方法"))
    resv = _t(_facts(h, "予約のしかた"), hours)
    every = _t(hours, closed, animals, spec, svc, pay)
    # 動物：犬・猫は「だけ」とはっきり書く病院だけ外す
    a_txt = re.sub(r"[（(][^）)]*対象外[^）)]*[）)]|魚類・昆虫は対象外|[^。、・]*は(診療し|診)ない[^。、]*", "", animals)
    only_cat = "cat" in tags and "catspec" in y or re.search(r"猫(のみ|だけ|専門)", spec + animals)
    only_dog = re.search(r"犬(のみ|だけ)", animals) and not re.search(r"猫", re.sub(r"犬(のみ|だけ)", "", animals))
    if only_cat: n.add("dog"); y.add("cat")
    elif only_dog: n.add("cat"); y.add("dog")
    else: y.update(("dog", "cat"))
    for k, rx in _AN_RX.items():
        if re.search(rx, a_txt): y.add(k)
    if re.search(r"小動物|小型哺乳|エキゾチック", a_txt + spec): y.update(("rabbit", "hamster", "ferret"))
    if re.search(r"エキゾチック", a_txt + spec): y.update(("bird", "reptile"))
    if animals and not re.search(r"など|ほか|その他|相談|エキゾ|小動物", animals):
        for k in ("rabbit", "hamster", "ferret", "bird", "reptile", "fish"):
            if k not in y: n.add(k)
    if only_cat:
        for k in ("rabbit", "hamster", "ferret", "bird", "reptile", "fish"): n.add(k) if k not in y else None
    if re.search(r"魚類[^。]*対象外|魚[^。]*診ない", animals): n.add("fish")
    # いつ
    ts = _times(hours)
    if re.search(r"24時間", hours + spec): y.update(("h24", "late", "early"))
    if ts:
        if max(b for a, b in ts) > 19 * 60: y.add("late")
        else: n.add("late") if "night" not in y and "h24" not in y else None
        if min(a for a, b in ts) < 9 * 60: y.add("early")
        elif "h24" not in y: n.add("early")
        if len(ts) == 1 and ts[0][1] - ts[0][0] >= 7 * 60 and not re.search(r"・\d|、\d", hours.split("（")[0]): y.add("nolunch")
        elif len(ts) >= 2 and "h24" not in y: n.add("nolunch")
    if "night" in y: y.add("late")
    if re.search(r"年中無休|休診日なし|休みなし|無休", every): y.update(("nohol", "sat", "sun", "hol"))
    if closed or re.search(r"休", hours):
        cl = closed + " " + " ".join(re.findall(r"[（(]([^）)]*休[^）)]*)[）)]", hours))
        if re.search(r"日曜(?!と祝日の午後|・祝日の午後|の午後)|日・|・日(?!本)|日祝|^日$|、日", cl) and not re.search(r"日曜[^、・]*午後", cl): n.add("sun")
        elif closed: y.add("sun")
        if re.search(r"土曜(?!午後|の午後)|土・|・土", cl): n.add("sat")
        elif closed: y.add("sat")
        if re.search(r"祝", cl) and not re.search(r"祝日の午後|祝の午後|祝日午後", cl): n.add("hol")
        elif closed: y.add("hol")
        if closed: n.add("nohol") if "nohol" not in y else None
    # 種類
    if re.search(r"猫専用の待合|猫専用待合|猫だけの待合|猫用の待合|待合室を分け|犬と猫の待合室", svc): y.add("catroom")
    if "catspec" in y: y.add("catroom")
    if re.search(r"予約制|完全予約", resv): n.add("noresv"); y.add("resv")
    if re.search(r"予約なし|予約不要|予約の必要はありません|順番", resv): y.add("noresv")
    if re.search(r"予約(?!制)|ネット予約|WEB予約|Web予約|電話予約", resv): y.add("resv")
    # 設備・サービス
    if re.search(r"駐車場(\d+台|あり)|駐車場がある|提携(の)?(コイン)?(駐車場|パーキング)|専用駐車", svc + every): y.add("park")
    if re.search(r"駐車場なし|駐車場はありません", svc + every): n.add("park"); y.discard("park")
    # カード可否は文ごとに見る（支払いの文に「保険の窓口精算はできない」など別項目の否定が混ざると誤判定するため。2026-11-24）
    for s in re.split(r"。", pay):
        if re.search(r"カード|クレジット|キャッシュレス|電子マネー|QR", s):
            (n if re.search(r"不可|使えない|できない|ご利用いただけません", s) else y).add("card")
    # ペット保険：支払いの文と「動物保険」の項目だけを見る。窓口精算・保険会社名（アニコム等）も根拠にする。
    # 「窓口精算はできない／なし」など、はっきり使えないと書いてある病院は付けない（保険証の持参だけでは付けない）
    inst = _t(pay, _facts(h, "動物保険"))
    if re.search(r"ペット保険|動物保険|窓口精算|窓口で精算|窓口払い|アニコム|アイペット", inst) and not re.search(
            r"窓口精算は(なし|できません|できない|使えない|不可)|窓口精算でき(ません|ない)|精算は(できません|できない|なし|なく)|精算でき(ません|ない)|ペット保険は(使えない|使えません|不可|対象外)|保険は使え(ない|ません)|対応していません", inst): y.add("ins")
    if re.search(r"ペットホテル|ホテル|預かり", h.get("services", "") + svc): y.add("hotel")
    if re.search(r"トリミング", h.get("services", "") + svc): y.add("trim")
    if re.search(r"しつけ|パピークラス|パピー教室", h.get("services", "") + svc): y.add("school")
    dps = depts_of(_t(" ".join(h.get("depts") or []), spec, svc))
    if re.search(r"CT|MRI", every + " ".join(h.get("depts") or [])): y.add("ct")
    r = {"n": h["name"], "c": h.get("city", ""), "u": h.get("url", "")}
    import cardphoto  # 使ってよいと確かめた写真（tools/photos.json）があれば、カードの上に出す（Nori 2026-11-16）
    _ph = cardphoto.hosp_photo(h)
    if _ph: r["ph"] = _ph
    if h.get("addr"): r["ad"] = h["addr"]
    hv = h.get("hours") or _facts(h, "診療時間", "受付時間")
    if hv: r["h"] = hv
    # いま受付時間か（曜日で変わる書き方の病院は出さない）
    if ts and not re.search(r"[月火水木金土日祝]|平日|曜", hours.split("（")[0]) and not re.search(r"曜|平日|土|日祝", hv or ""):
        r["t"] = [[a, b] for a, b in ts]
    elif "h24" in y and re.search(r"^24時間", hv or ""): r["t"] = [[0, 1440]]
    if closed.strip(): r["x"] = closed.strip()
    if animals: r["a"] = "・".join(dict.fromkeys(x for x in re.split(r"[・、,\s]+", animals) if x))
    if h.get("area"): r["ar"] = h["area"]
    st = _facts(h, "最寄り駅", "アクセス", "行き方")
    if st: r["st"] = st[:120]
    if dps: r["d"] = dps
    r["y"] = sorted(y); r["no"] = sorted(n - y)
    if h.get("review_query") and h.get("id"): r["rv"] = h["id"]
    # 電話番号は、公式サイトか獣医師会の一覧にある番号だけ（tel_src つき）。Nori 2026-11-15 判断のカード「出す」
    tl = h if h.get("tel") else _TEL.get(h.get("id"), {})
    if tl.get("tel") and tl.get("tel_src"): r["tel"] = re.sub(r"[^0-9\-]", "", tl["tel"])
    if re.search(r"（[^）]+[都道府県]）$", r["c"]): r["far"] = 1
    return r


def build(ROOT, ctx, CONDS, rows_of, hhref_of, vet_by_pref, vet_page_of, pslug, depts_of):
    """県ごとの JSON を書き、県ごとに使えるボタン（1院以上に当てはまるもの）を返す。"""
    TAG = {"night": "night", "visit": "visit", "cat": "catspec", "exotic": "exospec", "large": "large"}
    per = {}
    for c in CONDS:
        for pf, hs in rows_of(c).items():
            for h in hs:
                key = (pf, h["name"])
                cur = per.setdefault(pf, {}).get(key[1])
                if cur is None:
                    per[pf][key[1]] = {"h": dict(h), "tags": {TAG[c["slug"]]}}
                else:
                    cur["tags"].add(TAG[c["slug"]])
                    for k, v in h.items():
                        if k not in cur["h"] or not cur["h"][k]: cur["h"][k] = v
                        elif k == "facts": cur["h"]["facts"] = cur["h"]["facts"] + [f for f in v if f not in cur["h"]["facts"]]
    for pf, cs in vet_by_pref().items():
        for v in cs:
            cur = per.setdefault(pf, {}).get(v["name"])
            if cur is None: per[pf][v["name"]] = {"h": dict(v), "tags": set()}
            else:
                for k, x in v.items():
                    if k not in cur["h"] or not cur["h"][k]: cur["h"][k] = x
    out_dir = os.path.join(ROOT, "hospital", "data")
    os.makedirs(out_dir, exist_ok=True)
    avail, counts = {}, {}
    for pf, m in per.items():
        recs = []
        for name, x in m.items():
            r = record(x["h"], pf, x["tags"], depts_of)
            pg = hhref_of(x["h"]) or vet_page_of(pf, x["h"])
            home = x["h"].get("pref") or (x["h"].get("prefs") or [pf])[0]
            if "visit" in x["tags"] and home != pf: r["c"] = ""; r["vz"] = 1  # ほかの県のお店から、この県へも来てくれる往診
            if pg: r["pg"] = pg
            recs.append(r)
        recs.sort(key=lambda r: (r.get("far", 0), r.get("vz", 0), r["c"], r["n"]))
        with open(os.path.join(out_dir, pslug[pf] + ".json"), "w", encoding="utf-8") as f:
            json.dump(recs, f, ensure_ascii=False, separators=(",", ":"))
        ys = {}
        for r in recs:
            for k in r["y"] + (["d:" + d for d in r.get("d", [])]): ys[k] = ys.get(k, 0) + 1
        avail[pf] = ys
        counts[pf] = sum(1 for r in recs if not r.get("far"))
    return avail, counts


CSS = """<style id="hfcss">
@media(max-width:640px){.area-hero{padding-bottom:14px!important}.area-hero .lede{font-size:.9rem!important;line-height:1.65!important;margin-bottom:0!important}}
.hf{background:#fff;border:1px solid #efe0d3;border-radius:18px;padding:14px 14px 10px;box-shadow:0 2px 12px rgba(0,0,0,.05);margin:4px 0 14px}
.hf-r{padding:7px 0 6px;border-top:1px solid #f5ebe2}
.hf-r:first-child{border-top:0;padding-top:0}
.hf-l{display:block;font-size:.76rem;font-weight:700;color:#7a6a5e;margin:0 0 5px}
.hf-c{display:flex;flex-wrap:nowrap;gap:6px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;margin:0 -14px;padding:0 14px 2px}
.hf-c::-webkit-scrollbar{display:none}
.hf-c button{flex:0 0 auto;white-space:nowrap}
.hf-p{flex-wrap:wrap;overflow:visible}
.hf-c select{flex:1 1 9em;min-width:0;font-size:.95rem;padding:9px 10px;border-radius:10px;border:1px solid #d9c9bb;background:#fff;color:#2b2622}
.hf-c button{border:1px solid #e3d3c6;background:#fff;border-radius:999px;padding:7px 11px;font-size:.86rem;line-height:1.2;color:#3c2f26;cursor:pointer}
.hf-c button[aria-pressed=true]{background:#e8590c;border-color:#e8590c;color:#fff;font-weight:700}
.hf-c button.hf-x{display:none}.hf-c.open button.hf-x{display:inline-block}.hf-c.open .hf-mo{display:none}
.hf-w{flex-wrap:wrap;overflow:visible;margin:0;padding:0}
.hf-need{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.hf-need button{border:1px solid #e3d3c6;background:#fff;border-radius:12px;padding:12px 8px;font-size:.95rem;font-weight:700;color:#3c2f26;cursor:pointer}
.hf-need button[aria-pressed=true]{background:#e8590c;border-color:#e8590c;color:#fff}
.hf-go{display:block;width:100%;margin:10px 0 2px;border:0;border-radius:999px;background:#2b2622;color:#fff;font-weight:800;font-size:1rem;padding:13px;cursor:pointer}
.hc-a2{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.hc-a2 a{display:flex;align-items:center;justify-content:center;gap:6px;border-radius:12px;padding:11px 6px;font-weight:800;font-size:.92rem;text-decoration:none;background:#2b2622;color:#fff}
.hc-a2 a.l{background:#fff;color:#2b2622;border:1px solid #d9c9bb}
.hc-sub{display:block;text-align:center;margin-top:8px;font-size:.84rem;color:#6b5f56}
.hf-c button.hf-mo{border-style:dashed;color:#7a6a5e}
.hf-foot{display:flex;justify-content:space-between;align-items:center;gap:8px;padding-top:8px;border-top:1px solid #f5ebe2}
.hf-sum{flex:1;margin:0;font-weight:800;font-size:1rem;color:#2b2622}.hf-sum small{font-weight:400;color:#7a6a5e;font-size:.78rem;display:block}
.hf-clear{white-space:nowrap;border:0;background:none;color:#7a6a5e;text-decoration:underline;font-size:.82rem;cursor:pointer}
.hf-list{display:grid;gap:10px}
.hf-h{margin:14px 0 2px;font-size:.88rem;color:#7a6a5e;font-weight:700}
.hc{background:#fff;border:1px solid #efe0d3;border-radius:14px;padding:12px 14px;overflow:hidden}
.hc>.ux-img{position:relative;margin:-12px -14px 10px;aspect-ratio:2/1;overflow:hidden;background:#f4f1ee}.hc>.ux-img img{display:block;width:100%;height:100%;object-fit:cover}.hc>.ux-img span{position:absolute;right:6px;bottom:6px;font-size:.66rem;line-height:1;padding:3px 6px;border-radius:6px;background:rgba(0,0,0,.45);color:#fff}
.hc-n{display:block;font-weight:800;font-size:1.02rem;color:#2b2622;text-decoration:none;line-height:1.35}
.hc-b{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0 4px}
.hc-b span{font-size:.74rem;padding:2px 8px;border-radius:999px;background:#fff1e6;color:#a8410a;font-weight:700}
.hc-b span.u{background:#f2efec;color:#6b5f56;font-weight:400}
.hc-l{margin:3px 0 0;font-size:.85rem;color:#4a3f37;display:flex;gap:6px;line-height:1.45}
.hc-l i{font-style:normal;flex:0 0 1.2em;text-align:center}
.hc-a{display:flex;flex-wrap:wrap;justify-content:center;gap:2px 16px;margin-top:8px}
.hc-a a,.hc-a .partner-review-open{font-size:.82rem;font-weight:700;padding:4px 0;border:0;background:none;color:#a8410a;text-decoration:none}
.hc-a a.o{background:#e8590c;border-color:#e8590c;color:#fff;font-weight:700}
.hc-a .emg-score{display:contents}.hc-a .partner-score{margin:0}
.hc .review-panel{flex-basis:100%}
.hf-more{display:block;margin:12px auto 0;border:1px solid #e3d3c6;background:#fff;border-radius:999px;padding:9px 18px;font-size:.9rem;cursor:pointer}
.hf-none{background:#fff8f2;border-radius:12px;padding:12px;font-size:.9rem}
.hf-on .hf-static{display:none}
.hf-p .pp-root{flex:1 1 100%;min-width:0}.hf-p input{flex:1 1 100%;min-width:0;font-size:.95rem;padding:9px 10px;border-radius:10px;border:1px solid #d9c9bb}
.hf-det{border-top:1px solid #f5ebe2;padding-top:6px;margin-top:2px}
.hf-det summary{cursor:pointer;font-weight:700;font-size:.88rem;color:#a8410a;padding:6px 0;list-style:none}
.hf-det summary::-webkit-details-marker{display:none}
.hf-det summary::after{display:none!important;content:none!important}
.hf-det summary{background:none!important;box-shadow:none!important;border:0!important}
.hf-det summary::before{content:"＋ "}.hf-det[open] summary::before{content:"－ "}
.hf-det summary span{margin-left:6px;font-size:.78rem;color:#fff;background:#e8590c;border-radius:999px;padding:1px 7px}
.hf-det summary span:empty{display:none}
.hf-alt{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.hf-alt button,.hf-alt a{border:1px solid #e3d3c6;background:#fff;border-radius:999px;padding:7px 11px;font-size:.85rem;color:#3c2f26;text-decoration:none;cursor:pointer}
.pk{display:grid;gap:8px;margin:4px 0 6px}
.pk-h{margin:0 0 2px;font-size:.9rem;font-weight:700;color:#2b2622}
.pk-g{background:#fff;border:1px solid #efe0d3;border-radius:12px;padding:0 12px}
.pk-g summary{cursor:pointer;list-style:none;font-weight:700;font-size:.92rem;color:#2b2622;padding:11px 34px 11px 0;position:relative;display:block}
.pk-g summary::-webkit-details-marker{display:none}

.pk-b{display:flex;flex-wrap:wrap;gap:6px;padding:0 0 12px}
.pk-b button{border:1px solid #e3d3c6;background:#fff;border-radius:999px;padding:7px 11px;font-size:.88rem;color:#3c2f26;cursor:pointer;line-height:1.2}
.pk-b button small{margin-left:4px;font-size:.76rem;color:#6b5f56}
@media (min-width:760px){.hf-list{grid-template-columns:1fr 1fr}.hf-p select{flex:0 0 14em}.hf-p input{flex:1 1 auto}.hf-need{grid-template-columns:repeat(3,1fr)}.hf-c{flex-wrap:wrap;overflow:visible;margin:0;padding:0}}
</style>"""


def _btns(g, items, more_after=None, extra=False):
    x = ' class="hf-x"' if extra else ""
    return "".join(f'<button type="button" data-g="{g}" data-v="{k}" aria-pressed="false"{x}>{lab}</button>' for k, lab in items)


NEED = [("", "指定なし"), ("night", "夜間・救急"), ("sunhol", "日曜・祝日"), ("h24", "24時間"), ("visit", "往診"), ("spec", "専門診療")]


def html(e, emg_opts, depts, preset="", pref="", city="", night_href="/hospital/night/"):
    """さがす欄の箱。最初に見えるのは 地域・動物・診療ニーズ の3つだけ。ほかは「詳しい条件」の中。
    preset＝最初から選んでおく条件（例 night）、pref・city＝最初に選んでおく場所。"""
    d_items = [("d:" + n, n) for n in depts]
    need = "".join(f'<button type="button" data-need="{k}" aria-pressed="{"true" if (k == preset or (not k and not preset)) else "false"}">{lab}</button>' for k, lab in NEED)
    return (CSS + f'<div class="hf" id="hf" data-hf data-preset="{e(preset)}" data-pref="{e(pref)}" data-city="{e(city)}">'
            # 上の赤い「いま具合が悪いとき」の箱は出さない（Nori 2026-11-16「いらんって言ったよね」。夜間・救急は「どんな病院」のボタンで選ぶ）
            f'<div class="hf-r"><span class="hf-l">どこで探しますか？</span><div class="hf-c hf-p"><select id="hospPref" aria-label="都道府県" hidden>{emg_opts}</select>'
            # 1つの入力で、都道府県（いくつでも）・市区町村・駅の候補を出す（/place.js。Nori 2026-11-16「県とか複数選択」「市町村とかサジェスト」）
            '<div id="hfPlace" class="pp-root"></div></div></div>'
            f'<div class="hf-r"><span class="hf-l">どの動物ですか？</span><div class="hf-c hf-w">{_btns("a", ANIMALS[:3] + [ANIMALS[5]], None)}<button type="button" class="hf-mo">その他</button>{_btns("a", ANIMALS[3:5] + ANIMALS[6:], None, True)}</div></div>'
            f'<div class="hf-r"><span class="hf-l">どんな病院をお探しですか？</span><div class="hf-need">{need}</div></div>'
            '<details class="hf-det" id="hfDet"><summary>詳しい条件で絞り込む<span id="hfDetN"></span></summary>'
            f'<div class="hf-r"><span class="hf-l">症状・お悩みから探す</span><div class="hf-c">{_btns("y", [("y:" + n, n) for n, _ in SYMPTOMS])}</div></div>'
            f'<div class="hf-r"><span class="hf-l">診療科目</span><div class="hf-c">{_btns("d", d_items)}</div></div>'
            f'<div class="hf-r"><span class="hf-l">病院の種類</span><div class="hf-c">{_btns("k", KIND)}</div></div>'
            f'<div class="hf-r"><span class="hf-l">診療の日・時間</span><div class="hf-c">{_btns("w", WHEN)}</div></div>'
            f'<div class="hf-r"><span class="hf-l">設備・サービス</span><div class="hf-c">{_btns("s", SVC)}</div></div>'
            '</details>'
            '<button type="button" class="hf-go" id="hfGo">この条件で病院を探す</button>'
            f'<div class="hf-foot"><p class="hf-sum" id="hfSum" aria-live="polite">都道府県を選ぶと、合う病院が下に並びます</p><button type="button" class="hf-clear" id="hfClear">条件をクリア</button></div>'
            f'</div><div class="hf-list" id="hfList"></div>')


def near_prefs():
    """都道府県ごとに、県庁所在地が近い県を3つ（結果が少ないときに近くの県の病院も出すため）。"""
    import prefkeep, math
    names = json.loads(prefkeep._PN); ll = json.loads(prefkeep._PL)
    out = {}
    for i, n in enumerate(names):
        d = sorted(((ll[i][0] - p[0]) ** 2 + ((ll[i][1] - p[1]) * math.cos(math.radians(ll[i][0]))) ** 2, names[j]) for j, p in enumerate(ll) if j != i)
        out[n] = [x[1] for x in d[:3]]
    return out


def _pics(ROOT):
    """カードのイメージ写真（uikit.stock と同じ img/stock/<分野>/ の webp）。分野ごとのファイル名の一覧。"""
    import uikit
    out = {}
    for k in ("hospital", "hospital-night"):
        if not uikit.STOCK_ON: out[k] = []; continue
        d = os.path.join(ROOT, "img", "stock", k)
        out[k] = sorted(f for f in os.listdir(d) if f.endswith(".webp")) if os.path.isdir(d) else []
    return out

# 都道府県を地方ごとに（さがす前の「県を選ぶ」ボタンの並び。2026-11-16 一覧が空に見えた見直し）
REGIONS = [("北海道・東北", ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"]),
           ("関東", ["茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県"]),
           ("中部", ["新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県"]),
           ("近畿", ["三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"]),
           ("中国・四国", ["鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県"]),
           ("九州・沖縄", ["福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"])]


def write_js(ROOT, avail, pslug, counts=None):
    import prefkeep
    body = open(os.path.join(HERE, "hosp_find.js"), encoding="utf-8").read()
    body = (body.replace("__SLUG__", json.dumps(pslug, ensure_ascii=False))
                .replace("__LABEL__", json.dumps(LABEL, ensure_ascii=False))
                .replace("__SYM__", json.dumps({"y:" + n: ds for n, ds in SYMPTOMS}, ensure_ascii=False))
                .replace("__NEAR__", json.dumps(near_prefs(), ensure_ascii=False, separators=(",", ":")))
                .replace("__PICS__", json.dumps(_pics(ROOT), separators=(",", ":")))
                .replace("__REG__", json.dumps([[g, [[pf, (counts or {}).get(pf, 0)] for pf in ps if (counts or {}).get(pf)]] for g, ps in REGIONS], ensure_ascii=False, separators=(",", ":"))))
    # 行だけのコメントと行頭の空白を落として軽くする（/hosp.js は 24KB まで）
    body = "\n".join(l.strip() for l in body.split("\n") if l.strip() and not l.strip().startswith("//"))
    js = "// 生成ファイル（tools/hosp_find.py）。手で直さない\n(function(){" + prefkeep.FN + prefkeep.GUESS + body + "\n})();\n"
    open(os.path.join(ROOT, "hosp.js"), "w", encoding="utf-8").write(js)
    return len(js.encode())
