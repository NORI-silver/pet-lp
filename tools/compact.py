# [B] 画面を何枚も占める並びをコンパクトにする（Nori 2026-11-16「これもうざい、もっとこんぱくとに」「ほかの記事も同様に見直して」）。
# gen_areas.py のいちばん最後（nosrc.py のあと）に動く。中身は消さずに <details> にたたむ（検索・AIは読める）。
#  1. 「都道府県ごとの◯◯」のリンクの箱 → 1行の「都道府県ごとの◯◯（47）」をタップで開く
#  2. 都道府県が15行以上ならぶ表 → 1行の「都道府県ごとの表を開く」
#  3. 行の多いカード型の表（スマホで1行ずつのカードになる表）→ 最初の4行だけ見せて「のこり◯件を見る」
#  4. トップ（とその写しのエリアページ）の「対応エリア」の市区のチップ → 「地域ごとの主な市区を見る」
# /hinan/ は担当のスレッドが直すので除く。何度動かしても同じ結果（data-cpt の印で2回目はしない）。
import os, re

SKIP_DIRS = ("hinan", "tools", "img", "lib", "node_modules")
PREF = re.compile(r"^(北海道|青森|岩手|宮城|秋田|山形|福島|東京|神奈川|埼玉|千葉|茨城|栃木|群馬|新潟|富山|石川|福井|山梨|長野|岐阜|静岡|愛知|三重|滋賀|京都|大阪|兵庫|奈良|和歌山|鳥取|島根|岡山|広島|山口|徳島|香川|愛媛|高知|福岡|佐賀|長崎|熊本|大分|宮崎|鹿児島|沖縄)")
CUT = 4  # カード型の表で最初に見せる行

CSS = ('<style id="cpt-css">details.cpt{margin:10px 0;border:1px solid var(--line,#eadfd5);border-radius:12px;background:#fff}'
       'details.cpt>summary{list-style:none;cursor:pointer;padding:12px 48px 12px 14px;font-weight:700;font-size:.95rem;display:flex;justify-content:space-between;gap:8px;align-items:center}'
       'details.cpt>summary::-webkit-details-marker{display:none}'
       
       'details.cpt>.cpt-b{padding:0 12px 12px}details.cpt>.cpt-b>.emg-tips,details.cpt>.cpt-b>.tbl{margin-top:0}'
       'details.cpt.more{border:0;background:none;margin:4px 0 12px}details.cpt.more>summary{justify-content:center;border:1px solid var(--line,#eadfd5);border-radius:999px;color:#c2410c;font-size:.9rem;padding:9px 14px;background:#fff}'
       'details.cpt.more>summary::after{content:"";}details.cpt.more>.cpt-b{padding:0}'
       '@media(max-width:640px){.area-hero .lede.cpt-l{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}</style>')


def _end(h, i, tag):
    """h[i] から始まる <tag ...> の閉じタグの後ろの位置。"""
    d, j = 0, i
    rx = re.compile(r"<(/?)%s\b[^>]*>" % tag)
    for m in rx.finditer(h, i):
        d += -1 if m.group(1) else 1
        if d == 0: return m.end()
    return -1


def _det(inner, summary, cls="cpt"):
    return f'<details class="{cls}" data-cpt><summary>{summary}</summary><div class="cpt-b">{inner}</div></details>'


def _text(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def pref_boxes(h):
    out, pos = [], 0
    for m in re.finditer(r'<div class="emg-tips"[^>]*><h4>(都道府県ごとの[^<]{1,40})</h4>', h):
        if m.start() < pos: continue
        j = _end(h, m.start(), "div")
        if j < 0: continue
        blk = h[m.start():j]
        n = len(re.findall(r"<a [^>]*>[^<]{2,8}?(?:都|道|府|県)", blk))
        if n < 10 or "data-cpt" in blk: continue
        out.append(h[pos:m.start()]); out.append(_det(blk.replace(f"<h4>{m.group(1)}</h4>", "", 1), f"{m.group(1)}（{n}）")); pos = j
    out.append(h[pos:])
    return "".join(out)


def _rows(tbody):
    return re.findall(r"<tr\b.*?</tr>", tbody, re.S)


def tables(h):
    out, pos = [], 0
    for m in re.finditer(r"<table\b", h):
        if m.start() < pos: continue
        j = _end(h, m.start(), "table")
        if j < 0: continue
        t = h[m.start():j]
        if "<table" in t[6:]: continue  # 入れ子は見ない
        tb = re.search(r"<tbody>(.*)</tbody>", t, re.S)
        if not tb: continue
        rows = _rows(tb.group(1))
        data = [r for r in rows if "colspan" not in r]
        firsts = [_text((re.search(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", r, re.S) or [None, ""])[1]) for r in data]
        npref = sum(1 for f in firsts if PREF.match(f) and len(f) <= 8)
        # 表の箱（<div class="tbl">）ごと包む
        s, e = m.start(), j
        pre = h[max(0, s - 40):s]
        mm = re.search(r'<div class="tbl[^"]*">\s*$', pre)
        if mm and h[e:e + 12].lstrip().startswith("</div>"):
            s = s - (len(pre) - mm.start()); e = h.index("</div>", e) + 6
        blk = h[s:e]
        if "data-cpt" in h[max(0, s - 60):s]: continue
        if npref >= 15:
            hd = re.findall(r"<h[2-4][^>]*>(.*?)</h[2-4]>", h[max(0, s - 3000):s], re.S)
            cap = _text(hd[-1]) if hd else ""
            label = "都道府県ごとの表を開く" if not cap or len(cap) > 30 else f"{cap}（表を開く）"
            out.append(h[pos:s]); out.append(_det(blk, f"{label}・{npref}都道府県")); pos = e
        elif re.search(r'class="[^"]*\bt2s\b', t) and len(data) > CUT + 2 and not any("colspan" in r for r in rows):
            head = t[:tb.start(1)]; tail = t[tb.end(1):]
            first = head + "".join(rows[:CUT]) + tail
            rest = head + "".join(rows[CUT:]) + tail
            wrap_s, wrap_e = (blk[:blk.index("<table")], blk[blk.rindex("</table>") + 8:])
            out.append(h[pos:s]); out.append(wrap_s + first + wrap_e + _det(wrap_s + rest + wrap_e, f"のこり{len(rows) - CUT}件を見る", "cpt more")); pos = e
    out.append(h[pos:])
    return "".join(out)


def area_grid(h):
    i = h.find('<div class="area-grid">')
    if i < 0 or "data-cpt" in h[i - 80:i]: return h
    j = _end(h, i, "div")
    if j < 0: return h
    return h[:i] + _det(h[i:j], "地域ごとの主な市区を見る") + h[j:]


def page(h):
    m = re.search(r"<main\b.*?</main>", h, re.S)
    if not m: return h
    b = m.group(0)
    b2 = area_grid(tables(pref_boxes(b)))
    if not re.search(r'id="form"', b):  # 情報ページの長い前置きはスマホで3行まで（文は残す）
        b2 = re.sub(r'<p class="lede">([^<]{90,}?)</p>', r'<p class="lede cpt-l">\1</p>', b2, count=1)
    if b2 == b: return h
    h = h[:m.start()] + b2 + h[m.end():]
    if 'id="cpt-css"' not in h: h = h.replace("</head>", CSS + "</head>", 1)
    return h


def build(root):
    n = 0
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root)
        top = rel.split(os.sep)[0]
        if rel != "." and (top.startswith(".") or top in SKIP_DIRS): dn[:] = []; continue
        if "index.html" not in fn: continue
        f = os.path.join(dp, "index.html")
        t = open(f, encoding="utf-8").read()
        if 'http-equiv="refresh"' in t: continue
        u = page(t)
        if u != t: open(f, "w", encoding="utf-8").write(u); n += 1
    return n
