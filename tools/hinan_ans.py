# [A][B] ペットと避難：飼い主の「うちの子はどうなる？」に、えらんだ子ごとに答える（Nori 2026-11-17
# 「飼い主は自分の子はどうなるんだろうを心配してる。それに回答が得られるようにしないと意味ない」
# 「自治体の情報を転記するだけとかやめて」「各かてごりで民間のプレイヤーもいるよね？」）。
# 1つの箱に：連れて行ける？ → どこで過ごす？ → 今日やる準備 → 避難所に入れないとき（民間の預け先）。
# 自治体の文は根拠として下にたたむ（gen_hinan.render_city）。子をえらぶのはラジオボタンとCSSだけ（JSなし。えらんだ子だけ端末に覚える）。
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PETS = [  # (id, ラベル, アイコン, 旗のキー)
    ("s", "小型犬", "🐕", "dog"),
    ("l", "中・大型犬", "🦮", "large"),
    ("c", "猫", "🐈", "cat"),
    ("r", "うさぎ・小動物", "🐇", "small"),
    ("b", "鳥", "🐦", "bird"),
    ("t", "爬虫類", "🦎", "reptile"),
]

# 今日やる準備（環境省「人とペットの災害対策ガイドライン」の持ち出し品・日ごろの備えから、子ごとに大事なものを先に）
COMMON = ["5日分以上のフード・水と、ふだんの薬", "うちの子の写真（スマホに）と、迷子札・マイクロチップの登録の確認"]
PREP = {
    "s": ["キャリーかクレートに入って静かに過ごせるように慣らす", "リード2本・首輪（迷子札つき）", "狂犬病とワクチンの接種の記録", "トイレシーツ・ふんの袋"],
    "l": ["じょうぶなリードと、つなぐ用の長いリード", "敷くマット・雨や暑さ寒さの対策（屋外につなぐことが多い）", "狂犬病とワクチンの接種の記録", "避難所に入れないときの行き先（車・親戚や知人の家・預け先）を決めておく"],
    "c": ["キャリー（洗濯ネットに入れてから入れると逃げにくい）", "猫砂と小さなトイレ", "キャリーをふだんから部屋に置いて慣らす", "ワクチンの接種の記録"],
    "r": ["持ち運べるケージ（外が見えないよう布をかける）", "冬はカイロ・夏は保冷剤（温度に弱い）", "ふだんの牧草・ペレット", "避難所に入れないときの預け先を決めておく"],
    "b": ["持ち運べる小さなケージと、かける布", "保温のカイロ（寒さに弱い）", "ふだんのエサ・水入れ", "鳴き声が気になるときの預け先を決めておく"],
    "t": ["フタのしっかりしまる容器", "保温のカイロ・断熱の袋", "ふだんのエサ", "避難所に入れないときの預け先を決めておく"],
}

def _verdict(nm, pid, f, large):
    """(色, 一言, 説明)。書いていないときも「分からない」とは言わず、国の手引きにそって、どう動けばいいかを言う"""
    if pid == "l":
        k, txt = large
        head = {"ok": ("yes", "連れて行けます（つないで過ごす）"), "cage": ("hard", "ケージに入る大きさまで"),
                "no": ("no", "避難所に入れないことがあります"), "nobig": ("hard", "入れないこともあります"),
                "hard": ("hard", "むずかしいことがあります"), "small": ("hard", "むずかしいことがあります"),
                "none": ("yes", "大きさで分けていません")}[k]
        if k == "none":
            txt = f"{nm}の決まりに、犬の大きさによる区別はありません。国の手引きでも、同行避難は大きさにかかわらず「犬や猫など」が対象です。ケージに入らない子は、人と別の場所にリードでつなぐ形がほとんどです。"
        return head[0], head[1], txt
    v = f.get({"s": "dog", "c": "cat", "r": "small", "b": "bird", "t": "reptile"}[pid])
    lab = {"s": "犬", "c": "猫", "r": "うさぎ・小動物", "b": "鳥", "t": "爬虫類"}[pid]
    if v == "yes": return "yes", "連れて行けます", f"{nm}は、{lab}を避難所で受け入れるとしています。"
    if v == "cond": return "hard", "条件つきで連れて行けます", f"{nm}は、{lab}を条件つきで受け入れるとしています（条件は下の「{nm}の決まり」に）。"
    if v == "hard": return "hard", "むずかしいことがあります", f"{nm}は、{lab}は避難所での受け入れがむずかしいことがあるとしています。"
    if v == "no": return "no", "避難所には入れません", f"{nm}は、{lab}を避難所で受け入れないとしています。前もって預け先を決めておきましょう。"
    if pid in ("s", "c"):
        return "yes", "同行避難の対象です", f"国の手引きでは、{lab}は同行避難の対象です。{nm}でも、連れて行く前提で準備しましょう。"
    return "hard", "ケージに入れて相談", f"{nm}は{lab}について決まりを出していません。ケージに入れて連れて行き、受付で飼う場所を相談します。入れないときの預け先も決めておくと安心です。"

def _where(nm, place):
    """自治体の文を写さず、飼い主に分かる言葉で「どこで過ごすか」を言う"""
    t = place or ""
    same = [x for x in t.split("。") if re.search(r"同室|同じ部屋|同じ空間|同じスペース|居室で一緒", x)]
    if same and any(not re.search(r"(?:同室|部屋|空間|スペース|一緒)[^。]*(?:ない|ません|限らない|不可|ではなく|できず|むずかし|難し)", x) and "ほかのペットと" not in x for x in same):
        return f"{nm}では、ペットと同じ部屋で過ごせる避難所もあります。ほかの避難所では、人とは別の場所で過ごします。"
    neg = r"[^。]{0,10}(?:入れない|入れません|不可|禁止|持ち込めない|持ち込み禁止)"
    ind = bool(re.search(r"屋内|室内|空き教室|倉庫|廊下", t)) and not re.search(r"(?:屋内|室内|建物内|居住スペース)" + neg, t)
    out = bool(re.search(r"(?:建物内|屋内|室内|居住スペース)" + neg, t)) or bool(re.search(r"屋外|軒下|テント|ピロティ|駐輪場|駐車場|校庭|グラウンド", t))
    if ind and out:
        return f"{nm}では、ペットは人とは別の場所で過ごします。屋内（空き教室・倉庫など）のことも、屋外（軒下・テントなど）のこともあり、場所は避難所ごとに決まります。"
    if ind:
        return f"{nm}では、ペットは人とは別の、屋内の場所（空き教室・倉庫・廊下など）で過ごします。場所は避難所ごとに決まります。"
    if out:
        return f"{nm}では、ペットは人とは別の、屋外の場所（軒下・駐輪場・テントなど）で過ごします。雨や暑さ寒さの対策を持って行きましょう。"
    return f"{nm}でも、ペットは人とは別の場所で、ケージに入れるかリードでつないで過ごすのがふつうです。場所は避難所に着いてから、運営の係が決めます。"

def _slug(pf, pref_pages):
    p = pref_pages.get(pf) or ""
    return p.strip("/").split("/")[-1] if p else ""

_D = None
def _data():
    global _D
    if _D is None:
        try: _D = json.load(open(os.path.join(ROOT, "webmcp", "data.json"), encoding="utf-8"))
        except Exception: _D = {"pref_pages": {}, "items": {}}
    return _D

def private_links(pf, pid):
    """避難所に入れないとき・長引くときの民間の預け先（宿・カフェは止めているので出さない）"""
    d = _data(); sl = _slug(pf, d.get("pref_pages", {}))
    def page(folder):
        return f"/{folder}/{sl}/" if sl and os.path.isdir(os.path.join(ROOT, folder, sl)) else f"/{folder}/"
    def has(cat):
        return any(x.get("pref") == pf for x in d.get("items", {}).get(cat, []))
    out = [("🏨", "ペットホテル" + ("（大型犬OK）" if pid == "l" else "（猫専用も）" if pid == "c" else ""), page("pet-hotel"),
            "家がこわれた・避難が長引くときに、しばらく預ける")]
    out.append(("🏠", "ペットシッター", page("pet-sitter"), "在宅避難や車中避難のあいだ、家で世話をしてもらう"))
    if pid in ("r", "b", "t"):
        out.append(("🩺", "エキゾチックアニマルを診る病院", "/hospital/exotic/", "温度や体調がくずれたとき・預かりの相談"))
    elif pid == "l" and has("large_facility_vet"):
        out.append(("🩺", "大型犬の設備がある動物病院", "/hospital/large/", "けが・体調がくずれたとき"))
    else:
        out.append(("🩺", "夜間・救急の動物病院", "/emergency/", "けが・体調がくずれたとき"))
    return out

CSS = """<style>
.hk{background:#fff;border:2px solid var(--accent,#e8590c);border-radius:18px;padding:14px 14px 10px;margin:4px 0 18px}
.hk h2{font-size:1.12rem;margin:0 0 10px;line-height:1.5}
.hk>input{position:absolute;opacity:0;pointer-events:none}
.hk-t{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:0 0 10px}
.hk-t label{display:flex;flex-direction:column;align-items:center;gap:1px;border:1.5px solid var(--line);border-radius:12px;padding:6px 2px;font-size:.8rem;font-weight:700;cursor:pointer;background:#fff;line-height:1.3;text-align:center}
.hk-t label span{font-size:1.5rem;line-height:1.2}
.hk-p{display:none}
.hk-v{display:flex;gap:10px;align-items:flex-start;border-radius:14px;padding:10px 12px;margin:0 0 8px;line-height:1.6}
.hk-v b{display:block;font-size:1.05rem}
.hk-v p{margin:2px 0 0;font-size:.88rem}
.hk-v .i{font-size:1.6rem;line-height:1.2}
.hk-v.yes{background:#e6f4ea;color:#14532d}.hk-v.hard{background:#fff4e0;color:#6b4100}.hk-v.no{background:#fde8e6;color:#8c1d18}
.hk h3{font-size:.95rem;margin:12px 0 4px}
.hk p.hk-x{font-size:.88rem;line-height:1.7;margin:0;color:#3c4043}
.hk ul.hk-c{list-style:none;padding:0!important;margin:4px 0 0!important}
.hk ul.hk-c li{position:relative;padding:4px 0 4px 1.7em;font-size:.88rem;line-height:1.6;border-top:1px dashed var(--line);margin:0}
.hk ul.hk-c li:first-child{border-top:0}
.hk ul.hk-c li::before{content:"☐";position:absolute;left:.2em;top:3px;font-size:1rem;color:var(--accent,#e8590c)}
.hk ul.hk-a{list-style:none;padding:0!important;margin:4px 0 0!important;display:grid;gap:6px}
.hk ul.hk-a li{margin:0}
.hk ul.hk-a a{display:flex;gap:10px;align-items:center;border:1px solid var(--line);border-radius:12px;padding:8px 10px;text-decoration:none;color:inherit;line-height:1.45}
.hk ul.hk-a a .i{font-size:1.4rem}
.hk ul.hk-a a b{display:block;font-size:.9rem;color:var(--accent-ink,#b3420a)}
.hk ul.hk-a a small{font-size:.78rem;color:#5f6368}
@media(min-width:720px){.hk-t{grid-template-columns:repeat(6,minmax(0,1fr))}}
"""

def block(e, it, pf, large, shelter_note=False, title=None):
    nm = it["name"]; f = it.get("flags") or {}
    css = CSS + "".join(f"#hk-{p}:checked~.hk-ps .hk-p-{p}{{display:block}}#hk-{p}:checked~.hk-t label[for=hk-{p}]{{border-color:var(--accent,#e8590c);background:#fff4ec}}" for p, *_ in PETS) + "</style>"
    radios = "".join(f'<input type="radio" name="hkpet" id="hk-{p}" value="{p}"{" checked" if i == 0 else ""}>' for i, (p, *_) in enumerate(PETS))
    labels = '<div class="hk-t" role="radiogroup" aria-label="うちの子をえらぶ">' + "".join(
        f'<label for="hk-{p}"><span aria-hidden="true">{ic}</span>{e(lab)}</label>' for p, lab, ic, _ in PETS) + "</div>"
    where = (it.get("decision_place") or _where(nm, it.get("place"))) + ("避難所ごとのペットの場所は、下の避難所の一覧の🐾に書いています。" if shelter_note else "")
    panels = []
    for p, lab, ic, _ in PETS:
        cls, head, why = _verdict(nm, p, f, large)
        if p != "l" and it.get("decision_species"):
            cls, head, why = it["decision_species"]
        elif p == "l" and it.get("decision_large_head"):
            head = it["decision_large_head"]
        ic2 = {"yes": "✅", "hard": "⚠️", "no": "⛔"}[cls]
        alts = "".join(f'<li><a href="{e(u)}"><span class="i" aria-hidden="true">{i}</span><span><b>{e(t)}</b><small>{e(s)}</small></span></a></li>'
                       for i, t, u, s in private_links(pf, p))
        car = "車の中で過ごすときは、エコノミークラス症候群と暑さに気をつけ、ペットは車内に置きっぱなしにしない。" if p in ("s", "l") else ""
        panels.append(
            f'<div class="hk-p hk-p-{p}"><div class="hk-v {cls}"><span class="i" aria-hidden="true">{ic2}</span><div><b>{e(lab)}：{e(head)}</b><p>{e(why)}</p></div></div>'
            f'<h3>🏠 どこで過ごす？</h3><p class="hk-x">{e(where)}</p>'
            f'<h3>☑️ 今日やっておく準備</h3><ul class="hk-c">' + "".join(f"<li>{e(x)}</li>" for x in PREP[p] + COMMON) + "</ul>"
            f'<h3>🚗 避難所に入れないとき・長引くとき</h3><p class="hk-x">在宅避難（家が安全なら）・車の中・親戚や知人の家のほか、民間の預け先もあります。{e(car)}</p>'
            f'<ul class="hk-a">{alts}</ul></div>')
    remember = ("<script>(function(){try{var v=localStorage.getItem('hnPet'),r=v&&document.getElementById('hk-'+v);if(r)r.checked=true;"
                "document.querySelectorAll('input[name=hkpet]').forEach(function(x){x.addEventListener('change',function(){try{localStorage.setItem('hnPet',x.value)}catch(e){}})})}catch(e){}})();</script>")
    h = title or f"うちの子は、{nm}の避難所でどうなる？"
    return "<!--thin0-->" + css + f'<div class="hk" id="uchinoko"><h2>{e(h)}</h2>{radios}{labels}<div class="hk-ps">{"".join(panels)}</div></div>' + remember + "<!--/thin0-->"
