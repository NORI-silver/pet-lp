"""サイト全体の表を読みやすくする（Nori 2026-11-14「表にまとめてるものが見にくい。字が多くて、改行とかも、位置とかも含めて」）。
gen_areas.py の最後に、できあがったページの <table> を1つずつ整える（表は表のまま。文字は消さない・隠さない）。
- 文字は左、数字・金額は右、○は真ん中。太字にしない。最後の列のオレンジの背景もやめる。
- 名前の後ろの「（栃木県）」などは小さい字で次の行に。
- 金額がいくつも並ぶ欄（「3.5寸（猫など）4,000円、4寸…5,000円」）は、1つずつの行にして、金額を右にそろえる。
- 文の多い表は、スマホでは1行ずつのカード（上に名前、下に「見出し：中身」）にする（class="t2s"）。
何度動かしても同じになる（class="t2" の表はとばす）。トップ（index.html）は元のファイルなので触らない。"""
import os, re, html

CSS = """<style id="t2css">
table.t2.t2.t2.t2{border-collapse:collapse;width:100%;font-size:.9rem;line-height:1.6;background:#fff;color:var(--ink,#2b2622)}
table.t2.t2.t2.t2 th,table.t2.t2.t2.t2 td{border:0;border-bottom:1px solid var(--line,#ece6e0);padding:10px 8px;text-align:left;vertical-align:top;font-weight:400;background:transparent;white-space:normal;font-size:inherit}
table.t2.t2.t2.t2 thead th{background:#f7f4f1;color:var(--ink-3,#6b625b);font-size:.78rem;font-weight:600;white-space:nowrap;border-bottom:1.5px solid var(--line,#ece6e0)}
table.t2.t2.t2.t2 tbody tr>:first-child{color:var(--ink,#2b2622);font-weight:600;min-width:7.5em}
table.t2.t2.t2.t2 .n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
table.t2.t2.t2.t2 .c{text-align:center}
table.t2.t2.t2.t2 .s{white-space:nowrap}
table.t2.t2.t2.t2 small.sub{display:block;font-size:.76rem;font-weight:400;color:var(--ink-3,#6b625b);line-height:1.4;margin-top:1px}
table.t2.t2.t2.t2 small.nt{font-size:.86em;color:var(--ink-3,#6b625b)}
table.t2.t2.t2.t2 .ln{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:2px 0}
table.t2.t2.t2.t2 .ln+.ln{border-top:1px dotted var(--line,#ece6e0)}
table.t2.t2.t2.t2 .ln .p{white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums;font-weight:600;color:var(--ink,#2b2622)}
table.t2.t2.t2.t2 .tx{display:block;padding:2px 0}
table.t2.t2.t2.t2 .tx+.ln,table.t2.t2.t2.t2 .ln+.tx,table.t2.t2.t2.t2 .tx+.tx{border-top:1px dotted var(--line,#ece6e0)}
@media (max-width:599px){
table.t2.t2.t2.t2 th,table.t2.t2.t2.t2 td{padding:9px 6px}
table.t2.t2.t2.t2 .n{white-space:normal;word-break:keep-all}
table.t2.t2.t2.t2 thead th{white-space:normal}
table.t2s.t2s.t2s.t2s{background:transparent}
table.t2s.t2s.t2s.t2s thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
table.t2s.t2s.t2s.t2s,table.t2s.t2s.t2s.t2s tbody{display:block}
table.t2s.t2s.t2s.t2s tr{display:block;background:#fff;border:1.5px solid var(--line,#ece6e0);border-radius:14px;margin:0 0 10px;overflow:hidden}
table.t2s.t2s.t2s.t2s tbody tr>:first-child{display:block;background:#f7f4f1;border:0;padding:10px 14px;font-size:.98rem;min-width:0}
table.t2s.t2s.t2s.t2s td:not(:first-child){display:grid;grid-template-columns:5.6em 1fr;gap:8px;border:0;border-top:1px solid var(--line,#ece6e0);padding:9px 14px;text-align:left;white-space:normal}
table.t2s.t2s.t2s.t2s td:not(:first-child)::before{content:attr(data-l);font-size:.74rem;color:var(--ink-3,#6b625b);line-height:1.5;padding-top:2px}
table.t2s.t2s.t2s.t2s.one td:not(:first-child){display:block}
table.t2s.t2s.t2s.t2s.one td:not(:first-child)::before{display:none}
table.t2s.t2s.t2s.t2s td.n{text-align:left}
table.t2s.t2s.t2s.t2s td:empty,table.t2s.t2s.t2s.t2s td:has(>div:empty){display:none}
}
</style>"""

_TAG = re.compile(r"<[^>]+>")
_NUM = re.compile(r"^[約\s]*[\d,.]+(?:円|社|km|件|院|か所|分|時間|%|寸|kg|頭|人|回|日|歳)?(?:\s*[〜~～\-–]\s*[\d,.]*(?:円|社|km|件|分|%|kg)?)?(?:ほど|から)?$")
_YEN = re.compile(r"[\d,]+円")
_ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S)
_CELL = re.compile(r"<(th|td)\b([^>]*)>(.*?)</\1>", re.S)

def _plain(x):
    return html.unescape(_TAG.sub("", x)).strip()

def _kind(t):
    if t in ("○", "◯", "×", "△", "—", "-", "–", "なし", "あり"): return "c"
    if _NUM.match(t): return "n"
    return ""

def _addcls(attrs, c):
    m = re.search(r'class="([^"]*)"', attrs)
    if m: return attrs.replace(m.group(0), f'class="{m.group(1)} {c}"', 1)
    return attrs + f' class="{c}"'

# 「名前（栃木県）」→ 名前 と 小さい字の（栃木県）
_TAIL = re.compile(r"^(.{2,}?)(（[^（）]{1,30}）)$")
def _name(inner):
    if "<" in inner: return inner
    m = _TAIL.match(inner.strip())
    if not m: return inner
    return f'{m.group(1)}<small class="sub">{m.group(2)}</small>'

# 金額がいくつも並ぶ欄を「名前……金額」の行にする
_SEG_PRICE = re.compile(r"^(.*?)\s*((?:[\d,.]+寸)?[\d,]+円(?:\s*[〜~]\s*(?:[\d,.]+寸)?(?:[\d,]+円)?)?)$")
def _paren_small(t):
    return re.sub(r"（([^（）]{1,40})）", lambda m: f'<small class="nt">（{m.group(1)}）</small>', t)

def _lines(inner):
    if "<" in inner: return inner
    t = html.unescape(inner).strip()
    if len(_YEN.findall(t)) < 2 or len(t) < 22: return inner
    # 「、」「。」で区切る（かっこの中の「、」では切らない）
    segs, depth, buf = [], 0, ""
    for ch in t:
        if ch == "（": depth += 1
        if ch == "）": depth = max(0, depth - 1)
        if ch in "、。" and depth == 0:
            if buf.strip(): segs.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip(): segs.append(buf.strip())
    if len(segs) < 2: return inner
    out = []
    for s in segs:
        m = _SEG_PRICE.match(s)
        if m and m.group(1).strip():
            out.append(f'<span class="ln"><span>{_paren_small(html.escape(m.group(1).strip()))}</span><span class="p">{html.escape(m.group(2))}</span></span>')
        else:
            out.append(f'<span class="tx">{_paren_small(html.escape(s))}</span>')
    return "".join(out)

def fix_table(tb):
    """<table …>…</table> を1つ受け取って、整えたものを返す"""
    if re.match(r'<table[^>]*class="[^"]*\bt2\b', tb) or 'class="us"' in tb: return tb
    head = re.search(r"<thead>(.*?)</thead>", tb, re.S)
    hcells = [_plain(c[2]) for c in _CELL.findall(head.group(1))] if head else []
    body = re.search(r"<tbody>(.*?)</tbody>", tb, re.S)
    rows = [_CELL.findall(r) for r in _ROW.findall(body.group(1) if body else tb)]
    rows = [r for r in rows if r]
    if not rows: return tb
    ncol = max(len(r) for r in rows)
    # 列ごとに：数字だけの列か、文の多い列か
    kinds, lens = {}, {}
    for j in range(ncol):
        vals = [_plain(r[j][2]) for r in rows if j < len(r) and _plain(r[j][2])]
        ks = {_kind(v) for v in vals}
        short = bool(vals) and max(len(v) for v in vals) <= 8
        kinds[j] = ks.pop() if len(ks) == 1 and ks != {""} else ("n" if ks <= {"n", "c"} and vals else "")
        if short and not kinds[j]: kinds[j] = "s"
        lens[j] = (sum(len(v) for v in vals) / len(vals), max(len(v) for v in vals)) if vals else (0, 0)
    texty = any(j and kinds[j] in ("", "s") and (lens[j][0] > 12 or lens[j][1] > 26) for j in range(ncol))
    stack = texty and len(hcells) == ncol and ncol >= 2 and all(hcells[1:])
    def cell(j, tag, attrs, inner):
        attrs = re.sub(r'\s*style="[^"]*"', "", attrs) if tag == "td" else attrs
        k = kinds.get(j, "")
        if k and j: attrs = _addcls(attrs, k)
        if k == "n": inner = re.sub(r"^([^<]*)", lambda m: m.group(1).replace("〜", "〜<wbr>"), inner, count=1)
        if j == 0: inner = _name(inner)
        elif not k: inner = _lines(inner)
        if stack and j:
            attrs += f' data-l="{html.escape(hcells[j])}"'
            inner = f"<div>{inner}</div>"
        return f"<{tag}{attrs}>{inner}</{tag}>"
    def fix_row(m):
        cs = _CELL.findall(m.group(1))
        return m.group(0).replace(m.group(1), "".join(cell(j, *c) for j, c in enumerate(cs)), 1)
    out = tb
    if body:
        nb = _ROW.sub(fix_row, body.group(1))
        out = out.replace(body.group(1), nb, 1)
    if head:
        nh = head.group(1)
        hs = _CELL.findall(nh)
        nh2 = "".join(f'<{t}{_addcls(a, kinds[j]) if j and kinds.get(j) == "n" else a}>{i}</{t}>' for j, (t, a, i) in enumerate(hs))
        nh = re.sub(r"(<tr\b[^>]*>).*?(</tr>)", lambda m: m.group(1) + nh2 + m.group(2), nh, count=1, flags=re.S)
        out = out.replace(head.group(1), nh, 1)
    cls = "t2" + (" t2s" if stack else "") + (" one" if stack and ncol == 2 else "")
    out = re.sub(r'<table([^>]*)>', lambda m: "<table" + _addcls(re.sub(r'\bstack\b', "", m.group(1)), cls) + ">", out, count=1)
    return out

def fix_page(s):
    t = re.sub(r"<table\b.*?</table>", lambda m: fix_table(m.group(0)), s, flags=re.S)
    if t != s and 'id="t2css"' not in t:
        t = t.replace("</head>", CSS + "\n</head>", 1)
    return t

def build(root):
    n = 0
    for dp, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if not d.startswith(".") and d not in ("tools", "node_modules", "booking", "tests", "sns", "docs", "lib", "img")]
        for f in fs:
            if not f.endswith(".html"): continue
            p = os.path.join(dp, f)
            if os.path.abspath(p) == os.path.abspath(os.path.join(root, "index.html")): continue
            s = open(p, encoding="utf-8").read()
            if "<table" not in s: continue
            t = fix_page(s)
            if t != s:
                open(p, "w", encoding="utf-8").write(t); n += 1
    return n
