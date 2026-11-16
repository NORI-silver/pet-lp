"""[B] 2026-11-15 全カテゴリのUI/UX（Nori「ペットのくらし窓口 全カテゴリUI/UX改善依頼」）。共通の部品とルール。
gen_areas.py の最後（faccard・portal のあと）に動く。何度動かしても同じ結果。

- さがす箱（box）：最初に見せる質問は2〜3つ（どこで・どの子・どんな）。ほかは「詳しい条件で絞り込む」の中。動きは /find.js（tools/find.js）。
  条件は公式サイトの情報だけ（施設の data-k）。書いていない施設は「書いていない（分からない）」で、押せば見られる。
- 結果の後ろのペットタクシーの案内は、横長の小さなカード1枚（ボタンは「ペットタクシーを探す」）。関連のリンクは文字のリンク、地域のリンクは折りたたみ。
- ボタンは3つの型：主なボタン（オレンジ・1つの節に1つ）／しぼりこみ（白地に灰色の枠）／関連のリンク（文字のリンク）。
- 先に動物病院・ペットホテル・ドッグランで試し（PILOT）、よければほかのカテゴリへ広げる。
"""
import html as _h, os, re
import prefkeep

PILOT = ["hospital", "pet-hotel", "dogrun"]
# 広げる先（2026-11-15 Nori「いいよ公開して」のあと、のこりのカテゴリへ）
ALL = ["hospital", "pet-hotel", "dogrun", "pet-sitter", "trimming", "dog-trainer", "rojin-home", "sougi", "joto",
       "inu-yado", "pet-yado", "inu-cafe", "jichitai", "hinan", "emergency"]
LIST_CATS = ["pet-sitter", "trimming", "dog-trainer", "rojin-home", "sougi", "joto"]
HERE = os.path.dirname(os.path.abspath(__file__))

CSS = """<style id="uicss">
[data-ffi][hidden],[data-ffg][hidden]{display:none!important}
.ux-img{position:relative;aspect-ratio:3/2;overflow:hidden;background:#f4f1ee}
.ux-img img{display:block;width:100%;height:100%;object-fit:cover}
.ux-img::after{content:"イメージ";position:absolute;right:6px;bottom:6px;font-size:.66rem;line-height:1;padding:3px 6px;border-radius:6px;background:rgba(0,0,0,.45);color:#fff}
.ux-c>.ux-img,.yd-card>.ux-img{margin:-12px -14px 10px;border-radius:13px 13px 0 0;aspect-ratio:2/1}
#ffRes{scroll-margin-top:110px;height:0;margin:0}
[data-ffg]{margin:0;padding:0!important}[data-ffg]>h2{margin-top:18px!important}
body.ux .emg{border:0;padding:0;background:none;box-shadow:none;border-radius:0}
.ux-find{background:#fff;border:1px solid #efe0d3;border-radius:18px;padding:14px 14px 10px;box-shadow:0 2px 12px rgba(0,0,0,.05);margin:4px 0 14px}
.ux-r{padding:8px 0 6px;border-top:1px solid #f5ebe2}.ux-r:first-child{border-top:0;padding-top:0}
.ux-l{display:block;font-size:.8rem;font-weight:700;color:#7a6a5e;margin:0 0 6px}
.ux-w{display:flex;flex-wrap:wrap;gap:6px}
.ux-w select{flex:1 1 100%;min-width:0;font-size:.95rem;padding:10px;border-radius:10px;border:1px solid #d9c9bb;background:#fff;color:#2b2622}
.ux-w input{flex:1 1 100%;min-width:0;font-size:.95rem;padding:10px;border-radius:10px;border:1px solid #d9c9bb}
.ux-w button{border:1px solid #e3d3c6;background:#fff;border-radius:999px;padding:8px 13px;font-size:.88rem;line-height:1.2;color:#3c2f26;cursor:pointer}
.ux-need{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.ux-need button{border:1px solid #e3d3c6;background:#fff;border-radius:12px;padding:12px 8px;font-size:.93rem;font-weight:700;color:#3c2f26;cursor:pointer}
.ux-find button[aria-pressed=true]{background:#e8590c;border-color:#e8590c;color:#fff;font-weight:700}
.ux-find button[hidden]{display:none}
.ux-det{border-top:1px solid #f5ebe2;padding-top:6px;margin-top:2px}
.ux-det summary{cursor:pointer;font-weight:700;font-size:.88rem;color:#a8410a;padding:6px 0;list-style:none;background:none!important;box-shadow:none!important;border:0!important}
.ux-det summary::-webkit-details-marker{display:none}.ux-det summary::after{display:none!important;content:none!important}
.ux-det summary::before{content:"＋ "}.ux-det[open] summary::before{content:"－ "}
.ux-det summary span{margin-left:6px;font-size:.78rem;color:#fff;background:#e8590c;border-radius:999px;padding:1px 7px}.ux-det summary span:empty{display:none}
.ux-det .ux-l{margin-top:8px}
.ux-go{display:block;width:100%;margin:10px 0 4px;border:0;border-radius:999px;background:#2b2622;color:#fff;font-weight:800;font-size:1rem;padding:13px;cursor:pointer}
.ux-foot{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;padding-top:8px;border-top:1px solid #f5ebe2}
.ux-sum{flex:1;margin:0;font-weight:800;font-size:1rem;color:#2b2622}.ux-sum small{display:block;font-weight:400;color:#7a6a5e;font-size:.78rem}
.ux-clear{white-space:nowrap;border:0;background:none;color:#7a6a5e;text-decoration:underline;font-size:.82rem;cursor:pointer}
.ux-alt{display:flex;flex-wrap:wrap;gap:6px}.ux-alt:not(:empty){margin-top:8px}
.ux-alt-b{border:1px solid #e3d3c6;background:#fff;border-radius:999px;padding:7px 11px;font-size:.84rem;color:#3c2f26;cursor:pointer}
.ux-none{flex-basis:100%;margin:0;background:#fff8f2;border-radius:12px;padding:10px 12px;font-size:.88rem}
.ux-unk{opacity:.85}.ux-unk-n{margin:4px 0 0;font-size:.76rem;color:#7a6a5e}
.ux-list{display:grid;gap:10px;margin:8px 0 14px}
.ux-c{background:#fff;border:1px solid #efe0d3;border-radius:14px;padding:12px 14px;margin:0;scroll-margin-top:110px}
.ux-c-n{display:block;font-weight:800;font-size:1.02rem;color:#2b2622;text-decoration:none;line-height:1.35;margin:0}
a.ux-c-n{text-decoration:underline;text-decoration-color:#e3d3c6;text-underline-offset:3px}
.ux-c .ux-c-m{margin:2px 0 6px;font-size:.8rem;color:#7a6a5e}
.ux-c .dr-tags{margin:0 0 6px}
.ux-c .ux-c-l{margin:3px 0 0;font-size:.85rem;color:#4a3f37;display:flex;gap:6px;line-height:1.45}.ux-c-l i{font-style:normal;flex:0 0 1.2em;text-align:center}
.ux-c-a{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.ux-c-a .ux-btn{justify-content:center;padding:10px 6px;font-size:.88rem}
.ux-btn.l{background:#fff;color:#2b2622!important;border:1px solid #d9c9bb}
.ux-c-s{margin:8px 0 0;font-size:.82rem;text-align:center}.ux-c-s a{color:#a8410a}
.ux-c-d{margin-top:8px;border-top:1px solid #f5ebe2;padding-top:4px}
.ux-c-d summary{padding-left:0!important;border-radius:0!important;cursor:pointer;font-size:.85rem;font-weight:700;color:#a8410a;padding:6px 0;list-style:none;background:none!important;border:0!important;box-shadow:none!important}
.ux-c-d summary::-webkit-details-marker{display:none}.ux-c-d summary::after{display:none!important;content:none!important}
.ux-c-d summary::before{content:"＋ "}.ux-c-d[open] summary::before{content:"－ "}
.ux-c-d dl{margin:4px 0;font-size:.84rem}.ux-c-d dt{font-weight:700;margin-top:6px}.ux-c-d dd{margin:0}
.ux-g-p{font-size:.85rem;color:#6b5f56;margin:0 0 4px}
.ux-tx{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #efe0d3;border-radius:16px;padding:12px 14px;margin:8px 0 4px}
.ux-tx-i{flex:0 0 40px;height:40px;border-radius:12px;background:#fff1e6;color:#e8590c;display:flex;align-items:center;justify-content:center}
.ux-tx-i svg{width:24px;height:24px}
.ux-tx-b{flex:1;min-width:0}.ux-tx-b h2{font-size:.98rem;margin:0;line-height:1.35}.ux-tx-b p{margin:2px 0 0;font-size:.8rem;color:#6b5f56;line-height:1.45}
.ux-tx-a{flex:0 0 auto;border-radius:999px;background:#e8590c;color:#fff!important;font-weight:800;font-size:.85rem;padding:9px 12px;text-decoration:none;white-space:nowrap}
.ux-tx-n{display:block;font-size:.72rem;color:#8a7d73;margin:0 0 14px}
@media (max-width:420px){.ux-tx{flex-wrap:wrap}.ux-tx-a{flex:1 1 100%;text-align:center}}
.ux-nav{margin:14px 0}h2.ux-nav-h{font-size:.92rem!important;border:0!important;padding:0!important;margin:0 0 4px!important}h2.ux-nav-h::before,h2.ux-nav-h::after{display:none!important}
body.ux .fc-acts{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px}body.ux .fc-acts .fac-act{display:contents}
body.ux .fc-acts a.fac-site{display:inline-flex;align-items:center;border-radius:10px;background:#2b2622!important;color:#fff!important;font-weight:700;font-size:.82rem;padding:8px 12px;text-decoration:none;border:0}
body.ux .fc-acts .fc-a,body.ux .fc-acts .partner-review-open{background:none!important;border:0!important;box-shadow:none!important;padding:4px 0!important;border-radius:0!important;font-size:.82rem;color:#a8410a!important;text-decoration:underline;text-underline-offset:2px}
body.ux .fc-more[open]{flex-basis:100%}.ux-nav-h{font-size:.85rem;font-weight:700;color:#7a6a5e;margin:0 0 4px}
body.ux ul.other{display:block;columns:2 13em;column-gap:18px;margin:4px 0 12px;padding:0;list-style:none}
body.ux ul.other li{display:block;break-inside:avoid;margin:0;padding:5px 0;border-bottom:1px solid #f3ece6}
body.ux ul.other a,body.ux ul.other li>span{display:inline;background:none!important;border:0!important;box-shadow:none!important;padding:0!important;border-radius:0!important;font-size:.88rem;font-weight:400;color:#a8410a;text-decoration:underline;text-underline-offset:2px;white-space:normal}
.ux-areas{margin:6px 0 14px;border:1px solid #efe0d3;border-radius:12px;padding:0 12px}
.ux-areas>summary{cursor:pointer;font-weight:700;font-size:.9rem;padding:11px 0;list-style:none;background:none!important;box-shadow:none!important;border:0!important}
.ux-areas>summary::-webkit-details-marker{display:none}.ux-areas>summary::after{display:none!important;content:none!important}
.ux-areas>summary::before{content:"＋ ";color:#e8590c}.ux-areas[open]>summary::before{content:"－ "}
.ux-btn{display:inline-flex;align-items:center;gap:4px;border-radius:10px;background:#2b2622;color:#fff!important;font-weight:700;font-size:.82rem;padding:7px 12px;text-decoration:none}
@media (min-width:760px){.ux-list{grid-template-columns:1fr 1fr}.ux-need{grid-template-columns:repeat(4,1fr)}.ux-w select{flex:0 0 14em}.ux-w input{flex:1 1 auto}}
</style>"""

CAR = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
       '<path d="M5 16V11l2-5h10l2 5v5"/><path d="M3 16h18v3H3z"/><circle cx="7.5" cy="19" r="1.5"/><circle cx="16.5" cy="19" r="1.5"/><path d="M5 11h14"/></svg>')

def e(x): return _h.escape(str(x), quote=True)

def _b(items, cls=""):
    return "".join(f'<button type="button" data-k="{e(k)}" data-l="{e(l)}" aria-pressed="false">{e(l)}</button>' for k, l in items)

def box(cat, *, q_ph, opts=None, who=None, need=None, more=(), unit="件", noun="ところ", go="この条件でさがす", guess=False, needpref=False):
    """さがす箱。opts＝都道府県の <option>（全国のページだけ）、who＝(質問, [(key, 名前)])、need＝(質問, [(key, 名前)])、more＝[(小見出し, [(key, 名前)])]。"""
    rows = []
    place = (f'<select id="ffPref" aria-label="都道府県">{opts}</select>' if opts else "") + f'<input id="ffQ" type="search" placeholder="{e(q_ph)}" aria-label="{e(q_ph)}" autocomplete="off">'
    rows.append(f'<div class="ux-r"><span class="ux-l">どこで探しますか？</span><div class="ux-w">{place}</div></div>')
    if who and who[1]: rows.append(f'<div class="ux-r"><span class="ux-l">{e(who[0])}</span><div class="ux-w">{_b(who[1])}</div></div>')
    if need and need[1]: rows.append(f'<div class="ux-r"><span class="ux-l">{e(need[0])}</span><div class="ux-need">{_b(need[1])}</div></div>')
    if more:
        inner = "".join(f'<span class="ux-l">{e(t)}</span><div class="ux-w">{_b(it)}</div>' for t, it in more if it)
        rows.append(f'<details class="ux-det"><summary>詳しい条件で絞り込む<span></span></summary>{inner}</details>')
    attrs = f' data-ff="{e(cat)}" data-unit="{e(unit)}" data-noun="{e(noun)}"' + (" data-guess" if guess else "") + (" data-needpref" if needpref else "")
    return (f'<div class="ux-find"{attrs}>' + "".join(rows) + f'<button type="button" class="ux-go" id="ffGo">{e(go)}</button>'
            '<div class="ux-foot"><p class="ux-sum" id="ffSum" aria-live="polite"></p><button type="button" class="ux-clear" id="ffClear" hidden>条件をクリア</button></div>'
            '<div class="ux-alt" id="ffAlt"></div></div><div id="ffRes"></div>')

FIND_JS = '<script src="/find.js" defer></script>'

def write_js(ROOT):
    js = open(os.path.join(HERE, "find.js"), encoding="utf-8").read()
    out = "// 生成：tools/uikit.py（元は tools/find.js と tools/prefkeep.py）\n" + prefkeep.FN + prefkeep.GUESS + "\n" + js
    open(os.path.join(ROOT, "find.js"), "w", encoding="utf-8").write(out)
    return len(out.encode())

def head(h):
    h = re.sub(r'<style id="uicss">.*?</style>\n?', "", h, flags=re.S)
    h = h.replace("</head>", CSS + "\n</head>", 1)
    if not re.search(r'<body[^>]*class="[^"]*\bux\b', h):
        h = re.sub(r"<body(?![^>]*class=)", '<body class="ux"', h, count=1)
        h = re.sub(r'<body([^>]*)class="(?![^"]*\bux\b)', r'<body\1class="ux ', h, count=1)
    return h

# ── 結果の後ろのペットタクシーの案内 ──
TX = {
    "hospital": "通院や退院のお迎えに。家の前から病院の前まで、飼い主さんも一緒に乗れます。",
    "hospital-night": "前もって決まっている通院や退院のお迎えに。急ぎの搬送は緊急の連絡先へ。",
    "pet-hotel": "家の前からホテルの前まで。大きな子やキャリーの猫も、飼い主さんと一緒に。",
    "dogrun": "車がないとき、大きな子や何頭もいっしょのときに。",
    "trimming": "サロンへの送り迎えに。家の前からお店の前まで、飼い主さんも一緒に。",
    "dog-trainer": "教室や幼稚園への送り迎えに。家の前から教室の前まで。",
    "rojin-home": "見学・入所・面会の日に。大きな子や介護中の子の移動に。",
    "inu-yado": "旅先や空港への移動に。大きな子や何頭もいっしょでも。",
    "pet-yado": "旅先や空港への移動に。キャリーの子も飼い主さんと一緒に。",
    "inu-cafe": "お店までの移動に。大きな子や何頭もいっしょでも。",
    "joto": "迎える日の移動に。家の前から譲渡の場所まで。",
}
# 大きなカードを出さず、関連のリンクの中に文字のリンク1行だけ（亡くなったとき・家に来てもらうシッター・迷子・避難）
TX_LINK = {"sougi": "火葬場や霊園への移動に、ペットタクシーを探す", "pet-sitter": "ホテルや病院への移動に、ペットタクシーを探す",
           "jichitai": "保護された子のお迎えの移動に、ペットタクシーを探す", "hinan": "預け先への移動に、ペットタクシーを探す",
           "emergency": "急ぎでない通院に、ペットタクシーを探す"}
NOTE = "料金の目安は各社の公式サイトの料金表から計算した概算で、確定料金ではありません。"
_SEC = re.compile(r'<section style="padding-top:0">\s*<div class="wrap">\s*<div class="sh"><h2>([^<]*)</h2><p>[^<]*</p></div>\s*'
                  r'<!--TAXICTA--><div class="taxi-cta"><a class="btn" href="([^"]*)" data-taxi-cta="([^"]*)">.*?<!--/TAXICTA-->\s*((?:<ul class="other">.*?</ul>\s*)*)', re.S)
_TAXI_LINK = re.compile(r'^/(tokyo|kanagawa|chiba|saitama|area)/|#form$')

def _split_links(uls):
    guide, area = [], []
    for li in re.findall(r"<li>.*?</li>", uls, re.S):
        m = re.search(r'href="([^"]*)"', li)
        hf = m.group(1) if m else ""
        if _TAXI_LINK.search(hf):
            if hf != "/#form": area.append(li)
        else: guide.append(li)
    return guide, area

def taxi(h, cat):
    def rep(m):
        title, href, cta, uls = m.group(1), m.group(2), m.group(3), m.group(4)
        guide, area = _split_links(uls)
        key = cat.replace("-bottom", "")
        if key in TX_LINK:
            out = ('<section style="padding-top:0" class="ux-tx-sec">\n  <div class="wrap">\n'
                   f'    <nav class="ux-nav" aria-label="関連のページ"><h2 class="ux-nav-h">{title}</h2><ul class="other">'
                   f'<li><!--TAXICTA--><a href="{href}" data-taxi-cta="{cta}">{e(TX_LINK[key])}</a><!--/TAXICTA--></li>{"".join(guide)}</ul></nav>\n')
            if area: out += f'    <details class="ux-areas"><summary>地域のペットタクシー</summary><ul class="other">{"".join(area)}</ul></details>\n'
            return out
        out = ('<section style="padding-top:0" class="ux-tx-sec">\n  <div class="wrap">\n'
               f'    <!--TAXICTA--><div class="ux-tx"><span class="ux-tx-i">{CAR}</span><div class="ux-tx-b"><h2>{title}</h2><p>{e(TX.get(cat.replace("-bottom", ""), TX.get(cat.split("-")[0], "")))}</p></div>'
               f'<a class="ux-tx-a" href="{href}" data-taxi-cta="{cta}">ペットタクシーを探す</a></div><small class="ux-tx-n">{NOTE}</small><!--/TAXICTA-->\n')
        if guide: out += f'    <nav class="ux-nav" aria-label="関連ガイド"><p class="ux-nav-h">関連ガイド</p><ul class="other">{"".join(guide)}</ul></nav>\n'
        if area: out += f'    <details class="ux-areas"><summary>地域のペットタクシー</summary><ul class="other">{"".join(area)}</ul></details>\n'
        return out
    return _SEC.sub(rep, h, count=1)

# ── ペットホテル（faccard のカードの一覧）の上を、さがす箱1つにまとめる ──
HOTEL = dict(
    cat="pet-hotel", unit="件", noun="ホテル", q_ph="市区町村（例：世田谷区、札幌市）",
    who=("どの子を預けますか？", [("large", "大型犬"), ("cat", "猫"), ("senior", "シニア・介護")]),
    need=("どんなホテルをお探しですか？", [("cat_only", "猫専用"), ("vet", "病院が併設"), ("pickup", "送迎あり"), ("night_staff", "夜もスタッフ")]),
    more=[("設備", [("private_room", "個室"), ("camera", "カメラで見守り"), ("run", "ドッグラン")])],
    go="この条件でホテルを探す")

def _end(h, i, tag="div"):
    import faccard
    return faccard._end(h, i, tag)

def _cut(h, start_pat):
    i = h.find(start_pat)
    if i < 0: return h, ""
    j = _end(h, i, "div")
    return h[:i] + h[j:], h[i:j]

def _list_end(h, em):
    """一覧（最後の emg-pref の節）の終わりの位置。"""
    i = h.rfind('<section class="emg-pref"')
    if i < em: return -1
    return _end(h, i, "section")

def _move_below(h):
    """一覧の上にある「無料の情報です」の注意書きと「都道府県ごとの◯◯」のリンクを、一覧の後ろへ（リンクは折りたたみ）。"""
    em = h.find('<div class="emg">')
    first = h.find('<section class="emg-pref"', em)
    if em < 0 or first < 0: return h
    top = h[em:first]
    chunks = re.findall(r'\s*<p class="emg-free">.*?</p>', top, re.S)
    navs = []
    for m in re.finditer(r'<div class="emg-tips"[^>]*><h4>([^<]*)</h4>', top):
        a = em + m.start(); b = _end(h, a, "div")
        navs.append((h[a:b], m.group(1)))
    for c in chunks: h = h[:em] + h[em:].replace(c, "", 1)
    for blk, _ in navs: h = h.replace(blk, "", 1)
    if not (chunks or navs): return h
    pos = _list_end(h, em)
    if pos < 0: return h
    add = "".join((f'<details class="ux-areas"><summary>{t}</summary>{blk}</details>' if t.startswith("都道府県ごとの") else blk) for blk, t in navs) + "".join(c.strip() for c in chunks)
    return h[:pos] + "\n      " + add + h[pos:]

def facility_list(h, conf, hub):
    if 'id="ffRes"' in h: return h
    em = h.find('<div class="emg">')
    if em < 0: return h
    h, _ = _cut(h, '<div class="fp" data-fp>')
    h, pf = _cut(h, '<div class="f"><label for="hospPref">')
    h, _ = _cut(h, '<div class="f"><span>条件でしぼりこむ')
    opts = ""
    m = re.search(r"<select[^>]*>(.*)</select>", pf, re.S)
    if m: opts = m.group(1)
    h = _move_below(h)
    bx = box(conf["cat"], q_ph=conf["q_ph"], opts=opts if hub else None, who=conf["who"], need=conf["need"], more=conf["more"],
             unit=conf["unit"], noun=conf["noun"], go=conf["go"], guess=hub)
    em = h.find('<div class="emg">')
    h = h[:em + len('<div class="emg">')] + bx + h[em + len('<div class="emg">'):]
    # 施設に印（data-flags をそのまま条件に）と「公式サイト」のボタン
    def card(m):
        t = m.group(0)
        fl = re.search(r'data-flags="([^"]*)"', t)
        return t[:-1] + f' data-ffi data-k="{fl.group(1) if fl else ""}">'
    h = re.sub(r'<div class="emg-item emg-co fc[^"]*"[^>]*>', card, h)
    h = re.sub(r'(<div class="fc-name"><a href="([^"]*)"[^>]*>.*?</div>)((?:(?!class="fc-name").)*?)<div class="fc-acts">',
               lambda m: m.group(1) + m.group(3) + f'<div class="fc-acts"><a class="ux-btn" href="{m.group(2)}" target="_blank" rel="noopener">公式サイトを見る ↗</a>', h, flags=re.S)
    # 前の動き（fit.js・条件のチェック）を外して /find.js に
    h = h.replace('<script src="/fit.js" defer></script>\n', "").replace('<script src="/fit.js" defer></script>', "")
    h = re.sub(r"<script>\n\(function\(\)\{(?:(?!</script>).)*?\.trim-cond input(?:(?!</script>).)*?</script>\n?", "", h, flags=re.S)
    if FIND_JS not in h: h = h.replace("</body>", FIND_JS + "\n</body>", 1)
    return h


# ── 施設のカードの一覧（シッター・トリミング・しつけ・老犬ホーム・火葬・譲渡）。条件はカードに書いてあることだけから作る ──
WHO_L = {"a:dog": "犬", "a:cat": "猫", "a:small": "うさぎ・小動物", "a:bird": "鳥", "a:exotic": "爬虫類など", "big": "大型犬", "sen": "シニア・介護", "pup": "子犬"}
LCONF = {
    "pet-sitter": ("シッター", "どの子のお世話ですか？", "どんなシッターをお探しですか？", "この条件でシッターを探す"),
    "trimming": ("ところ", "どの子ですか？", "どんなトリミングをお探しですか？", "この条件で探す"),
    "dog-trainer": ("ところ", "どの子ですか？", "どんな教室・トレーナーをお探しですか？", "この条件で探す"),
    "rojin-home": ("ホーム", "どの子ですか？", "どんなホームをお探しですか？", "この条件でホームを探す"),
    "sougi": ("ところ", "どの子ですか？", "どんな見送り方をお考えですか？", "この条件で探す"),
    "joto": ("窓口", "迎えたい子は？", "知りたいことは？", "この条件で窓口を探す"),
}
_ATTR = lambda t, a: html_unescape((re.search(r'\b%s="([^"]*)"' % a, t) or [None, ""])[1])
def html_unescape(x): return _h.unescape(x)

def _keys(t, cat):
    import json as _j
    k, no = [], []
    # 印は、公式サイトの文から選んだ data-tags があればそれだけ（似た言葉が並ばないように）。なければ data-ft
    src = _ATTR(t, "data-tags") or _ATTR(t, "data-ft")
    k += [x.strip().replace(" ", "_") for x in src.split("|") if x.strip()]
    try: f = _j.loads(_ATTR(t, "data-fit") or "{}")
    except Exception: f = {}
    kinds = ("dog", "cat", "small", "bird", "exotic") if cat == "joto" else ("small", "bird", "exotic")
    a = f.get("a") or []
    for x in kinds:
        if x in a: k.append("a:" + x)
        elif a and f.get("o"): no.append("a:" + x)
    if cat != "joto" and "cat" in _ATTR(t, "data-flags").split(): k.append("a:cat")  # トリミングの「猫に対応」
    if cat != "joto":
        if f.get("kg"): (k if f["kg"] >= 25 else no).append("big")
        elif f.get("s"): (k if "l" in f["s"] else no).append("big")
        if f.get("sen"): k.append("sen")
        if f.get("pup"): k.append("pup")
    return list(dict.fromkeys(k)), list(dict.fromkeys(no))

def generic_list(h, cat, hub):
    if 'id="ffRes"' in h or '<div class="fp" data-fp>' not in h: return h
    noun, qwho, qneed, go = LCONF[cat]
    h, _ = _cut(h, '<div class="fp" data-fp>')
    h, pf = _cut(h, '<div class="f"><label for="hospPref">')
    h, _ = _cut(h, '<div class="f"><span>条件でしぼりこむ')
    opts = (re.search(r"<select[^>]*>(.*)</select>", pf, re.S) or [None, ""])[1] if pf else ""
    if h.find('<div class="emg">') < 0: return h
    h = _move_below(h)
    cnt = {}
    def card(m):
        t = m.group(0)
        ks, no = _keys(t, cat)
        for x in ks: cnt[x] = cnt.get(x, 0) + 1
        own = [x for x in ks if x in WHO_L]  # data-ft・data-tags にある条件は find.js がそこから読む（ページを軽く）
        return t[:-1] + " data-ffi" + (f' data-k="{e(" ".join(own))}"' if own else "") + (f' data-no="{e(" ".join(no))}"' if no else "") + ">"
    h = re.sub(r'<div class="emg-item emg-co fc[^"]*"[^>]*>', card, h)
    who = [(x, WHO_L[x]) for x in WHO_L if cnt.get(x)]
    dup = {"a:small": {"小動物", "うさぎ・小動物", "うさぎ"}, "a:bird": {"鳥", "小鳥"}, "a:exotic": {"爬虫類", "爬虫類など"}, "big": {"大型犬", "大型犬OK"}, "sen": {"シニア", "シニア・介護OK", "シニア・介護"}, "pup": {"パピー", "子犬"}, "a:cat": {"猫"}}
    drop = set().union(*[v for k, v in dup.items() if cnt.get(k)]) if cnt else set()
    rest = sorted((x for x in cnt if x not in WHO_L and x not in drop), key=lambda x: (-cnt[x], x))
    rest = [x for x in rest if cnt[x] >= (2 if hub else 1)]
    need = [(x, x.replace("_", " ")) for x in rest[:4]]
    more = [(x, x.replace("_", " ")) for x in rest[4:14]]
    n_items = h.count(" data-ffi ")
    bx = box(cat, q_ph="市区町村・名前（例：世田谷区）", opts=opts if (hub and opts) else None, who=(qwho, who), need=(qneed, need),
             more=[("そのほかの条件", more)] if more else (), unit="件", noun=noun, go=go, guess=bool(hub and opts))
    em = h.find('<div class="emg">')
    h = h[:em + len('<div class="emg">')] + bx + h[em + len('<div class="emg">'):]
    if "/facility.js" not in h:
        h = re.sub(r'(<div class="fc-name"><a href="([^"]*)"[^>]*>.*?</div>)((?:(?!class="fc-name").)*?)<div class="fc-acts">',
                   lambda m: m.group(1) + m.group(3) + f'<div class="fc-acts"><a class="ux-btn" href="{m.group(2)}" target="_blank" rel="noopener">公式サイトを見る ↗</a>', h, flags=re.S)
    h = h.replace('<script src="/fit.js" defer></script>\n', "").replace('<script src="/fit.js" defer></script>', "")
    if opts:
        h = re.sub(r"<script>\n\(function\(\)\{(?:(?!</script>).)*?getElementById\(\"hospPref\"\)(?:(?!</script>).)*?</script>\n?", "", h, flags=re.S)
    if FIND_JS not in h: h = h.replace("</body>", FIND_JS + "\n</body>", 1)
    return h

PREF47 = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"]

def cafe_hub(h):
    """カフェの一覧（地方ごとの表）：上に「どこで」のさがす箱、表の行が結果。「数えて分かったこと」は一覧の後ろへ。"""
    if 'id="ffRes"' in h: return h
    em = h.find('<div class="emg">')
    if em < 0: return h
    m = re.search(r'\s*<div class="emg-tips" style="margin-top:0"><h2[^>]*>数えて分かったこと</h2>', h[em:])
    facts = ""
    if m:
        a = em + m.start(); b = _end(h, a + len(m.group(0)) - len(m.group(0).lstrip()), "div")
        facts = h[a:b].strip(); h = h[:a] + h[b:]
    seen = []
    def row(m):
        t = m.group(0)
        pm = re.search(r'data-l="場所"><div>(' + "|".join(PREF47) + ')', t)
        if not pm: return t
        if pm.group(1) not in seen: seen.append(pm.group(1))
        return '<tr data-ffi data-pref="' + pm.group(1) + '">' + t[4:]
    h = re.sub(r'<tr><td><a href="/inu-cafe/.*?</tr>', row, h, flags=re.S)
    h = re.sub(r'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">([^<（]*)（(\d+店)）</h2><div class="tbl"><table class="pp-tbl cmp',
               lambda m: f'<div class="emg-tips" data-ffg><h2 style="font-size:1.05em;margin:0 0 6px">{m.group(1)}（<span data-ffn>{m.group(2)}</span>）</h2><div class="tbl"><table class="pp-tbl cmp', h)
    opts = '<option value="">すべての都道府県</option>' + "".join(f"<option>{p}</option>" for p in PREF47 if p in seen)
    bx = box("inu-cafe", q_ph="市区町村・お店の名前（例：札幌市）", opts=opts, unit="店", noun="お店", go="この条件でお店を探す")
    em = h.find('<div class="emg">') + len('<div class="emg">')
    h = h[:em] + bx + h[em:]
    if facts:
        last = h.rfind("<div class=\"emg-tips\" data-ffg>")
        if last > 0:
            j = _end(h, last, "div"); h = h[:j] + facts + h[j:]
    if FIND_JS not in h: h = h.replace("</body>", FIND_JS + "\n</body>", 1)
    return h

def jichitai_hub(h):
    """迷子・登録の窓口：「いますぐ知りたいこと」（場面ごとの答え）と都道府県の選択を先に、窓口の受け持ちの表は一覧の後ろへ。"""
    if "data-uxmoved" in h: return h
    em = h.find('<div class="emg">')
    i = h.find('<div class="emg-tips"><h4>窓口ごとに受け付けていること</h4>', em)
    if em < 0 or i < 0: return h
    j = _end(h, i, "div"); blk = h[i:j]; h = h[:i] + h[j:]
    m = re.search(r'\s*<p class="emg-free">.*?</p>', h[em:], re.S)
    free = ""
    if m and em + m.start() < h.find('<section class="emg-pref"', em):
        free = m.group(0).strip(); h = h[:em + m.start()] + h[em + m.end():]
    pos = _list_end(h, em)
    if pos < 0: return h
    return h[:pos] + "\n      " + blk.replace("<div class=\"emg-tips\">", '<div class="emg-tips" data-uxmoved>', 1) + free + h[pos:]

# ── カードのイメージ写真（Nori 2026-11-16「無料の写真を使って。その都度読み込むのじゃなくて、アップロードして」）──
# 無料の写真素材（Unsplash の無料の写真。tools/stock.json に写真ID・撮った人・ページを控える）を、縮めて img/stock/<分野>/<番号>.webp に置く。
# 本物の施設の写真ではないので、写真の右下に小さく「イメージ」と書き、alt は空（その施設の写真だと読ませない）。
# 同じページの中で、となりのカードが同じ写真にならないよう、カードの順番で回す。写真のファイルがない分野には何も足さない。
STOCK_KEY = {"hospital": "hospital", "hospital-night": "hospital-night", "pet-hotel": "pet-hotel", "trimming": "trimming", "dog-trainer": "dog-trainer",
             "pet-sitter": "pet-sitter", "rojin-home": "rojin-home", "sougi": "sougi", "joto": "joto", "dogrun": "dogrun",
             "inu-yado": "inu-yado", "pet-yado": "pet-yado", "inu-cafe": "inu-cafe"}
# Nori 2026-11-16「写真はイメージじゃなくて、その施設のやつ使ってっていったよね」：汎用の写真はやめた。カードには何も足さない
# （前に入れた写真と data-pics は消す）。その施設の写真は、使ってよいものだけ写真のスレッドが入れる。rules_check の [stock] で止める。
STOCK_ON = False
_STOCK = {}
def _stock_files(ROOT, key):
    if key not in _STOCK:
        d = os.path.join(ROOT, "img", "stock", key)
        _STOCK[key] = sorted(f for f in os.listdir(d) if f.endswith(".webp")) if os.path.isdir(d) else []
    return _STOCK[key]

_CARD_OPEN = re.compile(r'<div class="(?:emg-item emg-co fc[^"]*|ux-c dr-card[^"]*|emg-item yd-card[^"]*)"[^>]*>')
def stock(h, ROOT, cat):
    h = re.sub(r'<div class="ux-img">.*?</div>', "", h, flags=re.S)
    if not STOCK_ON: return re.sub(r' data-pics="[^"]*"', "", h)
    fs = _stock_files(ROOT, STOCK_KEY.get(cat, ""))
    if not fs: return h
    # さがす箱（/find.js）のあるページは、写真の一覧を箱に書いておき、find.js がカードに入れる（カードの数が多いページでも軽く）
    if 'data-ff="' in h:
        h = re.sub(r'(<div class="ux-find" data-ff="[^"]*")(?: data-pics="[^"]*")?', lambda m: m.group(1) + f' data-pics="/img/stock/{STOCK_KEY[cat]}/|{",".join(fs)}"', h, count=1)
        return h
    i = [0]
    def put(m):
        f = fs[i[0] % len(fs)]; i[0] += 1
        return m.group(0) + f'<div class="ux-img"><img src="/img/stock/{STOCK_KEY[cat]}/{f}" alt="" loading="lazy"></div>'  # 「イメージ」の字は CSS で（ページを軽く）
    return _CARD_OPEN.sub(put, h)

def build(ROOT):
    n = 0
    sz = write_js(ROOT)
    for d in ALL:
        for r, _, fs in os.walk(os.path.join(ROOT, d)):
            if "index.html" not in fs: continue
            p = os.path.join(r, "index.html")
            parts = os.path.relpath(r, ROOT).split(os.sep)
            h = open(p, encoding="utf-8").read()
            old = h
            cat = "hospital-night" if parts[:2] == ["hospital", "night"] else d
            h = taxi(h, cat)
            if d == "pet-hotel" and len(parts) <= 2: h = facility_list(h, HOTEL, hub=len(parts) == 1)
            if d in LIST_CATS: h = generic_list(h, d, hub=len(parts) == 1)
            if d == "inu-cafe" and len(parts) == 1: h = cafe_hub(h)
            if d == "jichitai" and len(parts) == 1: h = jichitai_hub(h)
            if 'data-ff="' in h and FIND_JS not in h: h = h.replace("</body>", FIND_JS + "\n</body>", 1)
            h = stock(h, ROOT, cat)
            h = head(h)
            if h != old:
                open(p, "w", encoding="utf-8").write(h); n += 1
    return n, sz
