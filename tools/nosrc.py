# [B] 「公式ページに書いてあること」のような言い回しを出さない・事実の表をアイコンつきの一覧にする
# （Nori 2026-11-16「公式ページにかいてあることは削除してっていったよね」「文字ばかりで辛いからアイコンなどVisualでわかりやすくして」）。
# gen_areas.py のいちばん最後に動き、全部のページ（/joto/ は担当のスレッドが直すので除く）の文から
# 「公式サイトに書いてある」「公式ページによると」などを取り、施設ページの「項目・内容（・出どころ）」の表を
# アイコン＋見出し＋中身の一覧（.fx）に作りかえる。出どころは一覧の下に1行だけ（リンクと「◯年◯月◯日時点」）。
# 中身の文は消さない（検索・AIが読める）。thin_gate.py もこの clean() を通した文で数える。何度動かしても同じ結果。
# 新しく文を書くときも「公式サイトに書いてある」は書かない（tools/seo_check.py の SRC_PHRASE で止める）。
import os, re

SKIP_DIRS = ("joto",)

_D = r"(\d{4}年\d{1,2}月\d{1,2}日(?:〜\d{1,2}月\d{1,2}日)?|\d{4}-\d{2}-\d{2})"
_S = r"公式(?:サイト|ページ|の(?:サイト|ページ))"
RULES = [
    (rf"{_S}に書いてある、そのほかのこと", "そのほかの情報"),
    (rf"(<h[23][^>]*>){_S}に書いてあること(</h[23]>)", r"\1基本情報\2"),
    (rf"{_D}時点の、{_S}に書いてある情報", r"\1時点の情報"),
    (rf"（{_D}時点の{_S}の情報）", r"（\1時点）"),
    (rf"{_S}に書いてある条件：", ""),
    (rf"書いていない項目は、{_S}に見つからなかったものです", "書いていない項目は、分からないものです"),
    (rf"{_S}に書いてあることだけで作った表です。", ""),
    (rf"、?{_S}に書いてあることだけで", ""),
    (rf"(\S{{1,40}}?)について「([^」]+)」と書いてあります", r"\1は「\2」です"),
    (rf"の{_S}には、", "の"),
    (rf"」と{_S}に書いてあります", "」です"),
    (rf"、?{_S}に([^。、「」<>]{{1,60}}?)を書いています", r"、\1をしています"),
    (rf"([^。、「」<>]{{1,60}}?)を{_S}に書いています", r"\1をしています"),
    (rf"、?{_S}によると、?", ""),
    (rf"{_S}の料金の例で", "料金の例で"),
    (rf"料金は{_S}に書いてある(店|施設|会社|宿|病院)だけ", r"料金は公開している\1だけ"),
    (rf"料金は{_S}に書いてある(?:もの|例)だけ", "料金は公開されているものだけ"),
    (rf"(各(?:病院|宿|店|社|施設|市|県)の){_S}に書いてある", r"\1"),
    (rf"各(?:病院|宿|店|社|施設)の{_S}に書いてあることです。?", ""),
    (rf"、?{_S}に書いてある(内容|情報)で", ""),
    (rf"{_S}に書いてある(内容|情報)", r"\1"),
    (rf"{_S}に書いてあること", "わかっていること"),
    (rf"{_S}に書いてある", ""),
    (rf"{_S}に書かれている", ""),
    (rf"{_S}の情報をもとに", ""),
    (rf"（{_S}に料金の記載なし）", ""),
    (r"（\s*）", ""),
    (r"、、", "、"),
    (r"を、で", "を"),
]
RULES = [(re.compile(a), b) for a, b in RULES]


def clean(t):
    for a, b in RULES:
        t = a.sub(b, t)
    return t


def _text_only(html, fn):
    # 動きのプログラム（script。構造化データ ld+json は除く）と、個人情報の外部送信の表の中は変えない
    out, pos = [], 0
    for m in re.finditer(r'<script(?![^>]*ld\+json)[^>]*>.*?</script>|<dl data-sendlist.*?</dl>', html, re.S):
        out.append(fn(html[pos:m.start()])); out.append(m.group(0)); pos = m.end()
    out.append(fn(html[pos:]))
    return "".join(out)


# ---- 事実の表 → アイコンつきの一覧 ----
def _svg(p):
    return ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
            "stroke='%23c2410c' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E" + p + "%3C/svg%3E\")")
ICONS = {
    "pin": "%3Cpath d='M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z'/%3E%3Ccircle cx='12' cy='10' r='2.3'/%3E",
    "clock": "%3Ccircle cx='12' cy='12' r='8.5'/%3E%3Cpath d='M12 7.5V12l3 2'/%3E",
    "cal": "%3Crect x='4' y='5.5' width='16' height='14' rx='2'/%3E%3Cpath d='M4 10h16M8.5 3.5v4M15.5 3.5v4'/%3E",
    "yen": "%3Cpath d='M7 4l5 7 5-7M12 11v9M8 13h8M8 16.5h8'/%3E",
    "dog": "%3Cpath d='M6 8l-2-3v6c0 3 2 5 4 5h1v4h6v-4h1c2 0 4-2 4-5V5l-2 3c-1-1-3-2-6-2S7 7 6 8z'/%3E%3Cpath d='M10 12h.01M14 12h.01'/%3E",
    "doc": "%3Cpath d='M6 3.5h8l4 4v13H6z'/%3E%3Cpath d='M9 12h6M9 16h6'/%3E",
    "ng": "%3Ccircle cx='12' cy='12' r='8.5'/%3E%3Cpath d='M6 6l12 12'/%3E",
    "rule": "%3Cpath d='M9 11l2 2 4-4'/%3E%3Cpath d='M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6z'/%3E",
    "car": "%3Cpath d='M4 15.5l1.6-5a2 2 0 0 1 1.9-1.4h9a2 2 0 0 1 1.9 1.4l1.6 5v3h-16z'/%3E%3Ccircle cx='8' cy='15.5' r='1.3'/%3E%3Ccircle cx='16' cy='15.5' r='1.3'/%3E",
    "cup": "%3Cpath d='M5 9h11v5a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5z'/%3E%3Cpath d='M16 10h1.5a2.5 2.5 0 0 1 0 5H16M9 3.5v2.5M12 3.5v2.5'/%3E",
    "heart": "%3Cpath d='M12 20s-7-4.3-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.7-7 10-7 10z'/%3E",
    "pay": "%3Crect x='3.5' y='6' width='17' height='12' rx='2'/%3E%3Cpath d='M3.5 10h17M7 14.5h4'/%3E",
    "info": "%3Ccircle cx='12' cy='12' r='8.5'/%3E%3Cpath d='M12 11v5M12 8h.01'/%3E",
}
PICK = [  # 見出しの言葉 → アイコン（上から順に当てる）
    ("pay", r"支払"), ("yen", r"料金|費用|円|会費|キャンセル"), ("ng", r"入れない|受けない|できない|注意"),
    ("pin", r"所在地|場所|住所|アクセス|行き方|エリア(?!.*犬)|地域"), ("clock", r"時間|受付|営業|診療"),
    ("cal", r"休み|定休|休館|休診|季節|期間|開いて"), ("car", r"駐車|お迎え|送迎|交通"),
    ("dog", r"犬|猫|動物|大きさ|頭数|体重|エリア|ゾーン|うさぎ|大型"), ("doc", r"登録|必要|持ち物|申し込み|予約|書類|条件"),
    ("rule", r"きまり|ルール|決まり|マナー"), ("cup", r"メニュー|席|カフェ|食"),
    ("heart", r"火葬|納骨|供養|法要|お骨|立ち会い|霊園|セレモニー|流れ"), ("info", r""),
]
PICK = [(k, re.compile(v)) for k, v in PICK]


def _icon(label):
    for k, rx in PICK:
        if rx.search(label): return k
    return "info"


CSS = ("<style id=\"fx-css\">.fx.fx{list-style:none;margin:6px 0 0;padding:0!important;display:grid;gap:2px}"
       ".fx>li{display:grid;grid-template-columns:34px 1fr;gap:10px;align-items:start;padding:10px 2px;border-bottom:1px solid var(--line,#eee)}"
       ".fx>li:last-child{border-bottom:0}"
       ".fx-i{width:34px;height:34px;border-radius:50%;background:#fff1e6 center/20px 20px no-repeat;display:block}"
       ".fx-k{display:block;font-size:.82rem;color:#6b5a4e;font-weight:700;margin-bottom:2px}"
       ".fx-v{display:block;font-size:.95rem;line-height:1.65;color:var(--ink,#2b211b)}"
       ".fx-v .ln{display:flex;justify-content:space-between;gap:10px;border-bottom:1px dotted #e5d5c8;padding:2px 0}"
       ".fx-v .ln .p{font-weight:700;white-space:nowrap}.fx-v .tx{display:block}"
       ".fx-src{font-size:.8rem;color:#777;margin:8px 0 0}"
       + "".join(f".fx-i.i-{k}{{background-image:{_svg(v)}}}" for k, v in ICONS.items()) + "</style>")

_TBL = re.compile(r'<div class="tbl"><table class="pp-tbl t2 t2s(?: one)?"><thead><tr><th>項目</th><th>内容</th>(<th>出どころ</th>)?</tr></thead><tbody>(.*?)</tbody></table></div>', re.S)
_ROW = re.compile(r'<tr><th scope="row">(.*?)</th><td data-l="内容"><div>(.*?)</div></td>(?:<td data-l="出どころ"><div>(.*?)</div></td>)?</tr>', re.S)


def _fx(m):
    rows, srcs = [], []
    for k, v, s in _ROW.findall(m.group(2)):
        lab = re.sub(r"<[^>]+>", "", k)
        rows.append(f'<li><span class="fx-i i-{_icon(lab)}" aria-hidden="true"></span><div><b class="fx-k">{k}</b><span class="fx-v">{v}</span></div></li>')
        if s:
            a = re.search(r'<a href="([^"]+)"', s); d = re.search(_D, s)
            if a: srcs.append((a.group(1), d.group(1) if d else ""))
    if not rows: return m.group(0)
    note = ""
    if srcs:
        urls = list(dict.fromkeys(u for u, _ in srcs)); days = sorted({d for _, d in srcs if d})
        when = f"（{days[-1]}時点）" if days else ""
        note = ('<p class="fx-src">出どころ：' + "・".join(f'<a href="{u}" target="_blank" rel="noopener">公式サイト{"" if len(urls) == 1 else i + 1}</a>' for i, u in enumerate(urls)) + when + "</p>")
    return f'<ul class="fx">{"".join(rows)}</ul>{note}'


def page(html):
    html = _TBL.sub(_fx, html)
    html = _text_only(html, clean)
    html = re.sub(r"（((?:\d{4}年)?\d{1,2}(?:〜\d{1,2})?月(?:\d{1,2}日)?(?:〜(?:\d{1,2}月)?\d{1,2}日)?|\d{4}-\d{2}-\d{2})(?:まで)?に確認）", r"（\1時点）", html)
    if 'class="fx"' in html and 'id="fx-css"' not in html:
        html = html.replace("</head>", CSS + "</head>", 1)
    return html


def build(root):
    n = 0
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root)
        top = rel.split(os.sep)[0]
        if rel != "." and (top.startswith(".") or top in SKIP_DIRS or top in ("tools", "node_modules", "lib", "img")): dn[:] = []; continue
        if "index.html" not in fn: continue
        f = os.path.join(dp, "index.html")
        t = open(f, encoding="utf-8").read()
        u = page(t)
        if u != t:
            open(f, "w", encoding="utf-8").write(u); n += 1
    return n
