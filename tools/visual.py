# [B] 2026-11-14 Nori「文字ばかりで読むのに疲れます。Visualで伝えられるように工夫してください(SEOやAIOには配慮して)」
# 図で読む部品。画像は使わず、HTMLとCSSだけで作る（文字はそのまま残るので、検索やAIにも読める）。
#  - 自動：記事の中身を書きかえずに見た目を変える
#      ・「先に答え」「まとめ」で始まる最初の節 → 答えの箱（.answer）
#      ・「□ 」で始まる箇条書き → チェックリスト（.check）
#      ・「見出し：説明」の箇条書き → カード（.kv、見出しを太字に）
#      ・番号つきの箇条書き（ol） → 手順の図（.steps）
#      ・金額の列だけの表 → 表の中に横棒（数字は表のまま。棒は飾りで aria-hidden）
#      ・本文の金額・割合・倍 → 太字の色つき（.n）
#  - 書き足す：("stats", [(大きい数字, 説明), ...])・("bars", {...})・("vs", {...})・("flow", [...])
# 守ること：文字を隠さない・画像にしない・JSを使わない・順位や「おすすめ」を作らない（数字は記事の中のものだけ）。
import re

def e(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# 本文の数字を目立たせる（円・%・倍だけ。ほかの数字はそのまま）
_NUM = re.compile(r"(?<![0-9.,])((?:約)?\d[\d,]*(?:\.\d+)?(?:万|千)?(?:円)?(?:〜\d[\d,]*(?:\.\d+)?(?:万|千)?)?(?:円|%|％|倍))")
def rich(s):
    return _NUM.sub(lambda m: f'<b class="n">{m.group(1)}</b>', e(s))

_KV = re.compile(r"^([^：。「」]{2,30})：(.+)$", re.S)

def _li(x):
    m = _KV.match(x)
    return f'<li><b class="k">{e(m.group(1))}</b>{rich(m.group(2))}</li>' if m else f"<li>{rich(x)}</li>"

_CHECK_H = re.compile(r"用意|準備|持ち物|持っていく|確かめ|確認|チェック|伝え|気をつけ|注意")

def _ul(items, ordered=False, heading=""):
    tag = "ol" if ordered else "ul"
    if not ordered and items and (all(x.startswith("□") for x in items) or (_CHECK_H.search(heading) and len(items) >= 2)):
        return '<ul class="check">' + "".join(_li(x.lstrip('□').strip()) for x in items) + "</ul>"
    kv = [_KV.match(x) for x in items]
    if ordered:
        li = "".join((f'<li><b class="k">{e(m.group(1))}</b>{rich(m.group(2))}</li>' if m else f"<li>{rich(x)}</li>") for x, m in zip(items, kv))
        return f'<ol class="steps">{li}</ol>'
    if len(items) >= 2 and sum(bool(m) for m in kv) * 2 >= len(items):
        li = "".join((f'<li><b class="k">{e(m.group(1))}</b>{rich(m.group(2))}</li>' if m else f"<li>{rich(x)}</li>") for x, m in zip(items, kv))
        return f'<ul class="kv">{li}</ul>'
    return f"<{tag}>" + "".join(f"<li>{rich(x)}</li>" for x in items) + f"</{tag}>"

# 表の中の金額（「3,000円」「600円〜6,400円」「0〜2,500円」）
_YEN = re.compile(r"^([\d,]+)円?(?:〜([\d,]+))?円$")
def _yen(c):
    m = _YEN.match(str(c).strip())
    if not m: return None
    a = int(m.group(1).replace(",", ""))
    b = int(m.group(2).replace(",", "")) if m.group(2) else None
    return (a, b)

def _table(v):
    h, *rows = v
    ncol = len(h)
    bar_cols = set()
    for j in range(1, ncol):
        vals = [_yen(r[j]) for r in rows if j < len(r) and str(r[j]).strip()]
        if len(rows) >= 2 and vals and all(vals) and len(vals) == len(rows):
            bar_cols.add(j)
    top = max([max(x for x in _yen(r[j]) if x is not None) for r in rows for j in bar_cols] or [0])
    def cell(r, j, x):
        if j == 0: return f"<th>{e(x)}</th>"
        if j in bar_cols and top > 0:
            a, b = _yen(x)
            if b is None:
                bar = f'<i class="tb" style="width:{max(a / top * 100, 1.5):.1f}%" aria-hidden="true"></i>'
            else:
                bar = f'<i class="tb rg" style="margin-left:{a / top * 100:.1f}%;width:{max((b - a) / top * 100, 1.5):.1f}%" aria-hidden="true"></i>'
            return f'<td class="y">{e(x)}{bar}</td>'
        return f"<td>{e(x)}</td>"
    # 文の多い表（4列以上）は、スマホでは1行ずつのカードにする（表のまま。見出しは data-l で各欄に出す）
    cells = [str(x) for r in rows for j, x in enumerate(r) if j and j not in bar_cols]
    stack = ncol >= 4 and cells and sum(len(x) for x in cells) / len(cells) > 14 and all(str(x).strip() for x in h[1:])
    if stack:
        def cell(r, j, x, _c=cell):
            c = _c(r, j, x)
            return c if j == 0 else c.replace("<td", f'<td data-l="{e(h[j])}"', 1)
    cls = ' class="has-bars"' if bar_cols else ""
    if stack: cls = cls[:-1] + ' stack"' if cls else ' class="stack"'
    return (f'<div class="tbl"><table{cls}><thead><tr>' + "".join(f"<th>{e(x)}</th>" for x in h) + "</tr></thead><tbody>" +
            "".join("<tr>" + "".join(cell(r, j, x) for j, x in enumerate(r)) + "</tr>" for r in rows) + "</tbody></table></div>")

def stats(items):
    """大きい数字のタイル。items = [(数字, 説明), ...]"""
    return '<ul class="vstats">' + "".join(f'<li><b>{e(n)}</b><span>{e(t)}</span></li>' for n, t in items) + "</ul>"

def bars(d):
    """横棒グラフ。d = {"title":見出し, "rows":[(ラベル, 値, 表示する文字), ...], "note":注, "hi":強調する行の番号の集合}
    値は数字（棒の長さだけに使う）。表示する文字は省略すると「値,円」。"""
    rows = d["rows"]
    top = d.get("max") or max(r[1] for r in rows) or 1  # max を渡すと「◯社のうち」の割合で棒の長さを決める
    hi = set(d.get("hi", ()))
    li = "".join(
        f'<li{" class=hi" if i in hi else ""}><span class="l">{e(r[0])}</span><span class="t"><i style="width:{max(r[1] / top * 100, 1.5):.1f}%"></i></span><b>{e(r[2] if len(r) > 2 else f"{r[1]:,}円")}</b></li>'
        for i, r in enumerate(rows))
    note = f'<p class="note">{e(d["note"])}</p>' if d.get("note") else ""
    return f'<figure class="bars"><figcaption>{e(d["title"])}</figcaption><ol>{li}</ol>{note}</figure>'

def vs(d):
    """2つをならべてくらべる。d = {"a":(見出し, [項目]), "b":(見出し, [項目])}"""
    def col(cls, t, items):
        return f'<div class="{cls}"><b class="vh">{e(t)}</b><ul>' + "".join(f"<li>{rich(x)}</li>" for x in items) + "</ul></div>"
    return '<div class="vs">' + col("va", *d["a"]) + col("vb", *d["b"]) + "</div>"

def flow(items):
    """短い流れ（→でつなぐ）。items = [(見出し, ひとこと), ...]"""
    return '<ol class="flow">' + "".join(f'<li><b>{e(t)}</b>{("<span>" + e(s) + "</span>") if s else ""}</li>' for t, s in items) + "</ol>"

def block(b, arrow="", heading=""):
    """記事の1かたまりをHTMLにする（gen_areas.py の block から呼ぶ）"""
    if isinstance(b, str): return f"<p>{rich(b)}</p>"
    k, v = b
    if k == "ul": return _ul(v, heading=heading)
    if k == "ol": return _ul(v, ordered=True)
    if k == "links": return '<ul class="links">' + "".join(f'<li><a href="{e(u)}">{e(n)}</a></li>' for n, u in v) + "</ul>"
    if k == "tip": return f'<p class="tip">{rich(v)}</p>'
    if k == "cta": return f'<a class="btn" href="/#form">{e(v)}{arrow}</a>'
    if k == "table": return _table(v)
    if k == "stats": return stats(v)
    if k == "bars": return bars(v)
    if k == "vs": return vs(v)
    if k == "flow": return flow(v)
    if k == "html": return v  # 生成側で作ったHTML（エスケープ済みのものだけ）
    raise ValueError(k)

def many(g):
    """目次と節の番号を出す長い記事か（節が5つ以上で、本文が3,000字以上）"""
    n = sum(len(b if isinstance(b, str) else str(b[1])) for _, bs in g["sections"] for b in bs)
    return len(g["sections"]) >= 5 and n >= 3000

def is_answer(h):
    return h.startswith(("先に答え", "結論", "まとめ：", "要点"))

# 白いアイコン（チェック）
_CHECK = "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fff' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12.5l4.5 4.5L19 7.5'/%3E%3C/svg%3E\")"

CSS = """
/* 図で読む部品（tools/visual.py、2026-11-14） */
.art b.n,.prose b.n{color:var(--o-d);font-weight:800}
.art ul.kv{list-style:none;padding:0;display:grid;gap:10px}
.art ul.kv li{background:#fff;border:1.5px solid var(--line);border-radius:16px;padding:12px 14px;margin:0;line-height:1.75}
.art ul.kv li b.k{display:block;color:var(--ink);font-size:1rem;line-height:1.5;margin-bottom:3px;padding-left:12px;border-left:4px solid var(--o)}
.art ul.check{list-style:none;padding:0}
.art ul.check li{position:relative;background:#fff;border:1.5px solid var(--line);border-radius:16px;padding:12px 14px 12px 46px;margin:0 0 8px;line-height:1.75}
.art ul.check li::before{content:"";position:absolute;left:14px;top:15px;width:22px;height:22px;border-radius:7px;background:var(--o) CHECK center/15px no-repeat}
.art ol.steps{list-style:none;padding:0;counter-reset:st;margin:4px 0 18px}
.art ol.steps>li{counter-increment:st;position:relative;padding:3px 0 18px 48px;margin:0;line-height:1.75}
.art ol.steps>li::before{content:counter(st);position:absolute;left:0;top:0;width:34px;height:34px;border-radius:50%;background:var(--o);color:#fff;font-weight:800;font-size:.95rem;display:flex;align-items:center;justify-content:center}
.art ol.steps>li::after{content:"";position:absolute;left:16px;top:38px;bottom:4px;width:2px;background:#ffd9c2}
.art ol.steps>li:last-child::after{display:none}
.art ol.steps b.k,.art ul.check b.k{display:block;color:var(--ink);font-size:1rem;line-height:1.5;margin-bottom:2px}
.art ul:not([class]) li::marker{color:var(--o)}
.art .answer{background:#fff;border:2.5px solid var(--o);border-radius:22px;padding:4px 18px 4px;margin:28px 0 8px;box-shadow:0 6px 18px rgba(255,106,26,.08)}
.art .answer>h2{border-left:0;padding-left:0;margin:16px 0 10px;font-size:1.2rem}
.art .answer>h2::before{content:"この記事の答え";display:block;width:max-content;font-size:.72rem;letter-spacing:.08em;background:var(--o);color:#fff;border-radius:999px;padding:2px 10px;margin-bottom:8px}
.art .answer ul:not([class]){list-style:none;padding:0}
.art .answer ul:not([class]) li{position:relative;padding:10px 0 10px 32px;border-top:1px dashed var(--line);margin:0}
.art .answer ul:not([class]) li:first-child{border-top:0}
.art .answer ul:not([class]) li::before{content:"";position:absolute;left:0;top:13px;width:20px;height:20px;border-radius:50%;background:var(--o) CHECK center/13px no-repeat}
.art.num{counter-reset:h2}
.art.num>h2:not(.nonum),.art.num>.answer>h2{counter-increment:h2}
.art.num>h2:not(.nonum)::before{content:counter(h2);display:inline-flex;align-items:center;justify-content:center;width:1.7em;height:1.7em;border-radius:9px;background:var(--o-l);color:var(--o-d);font-size:.8em;margin-right:8px;vertical-align:.1em}
.art.num>h2:not(.nonum){border-left:0;padding-left:0}
.art nav.art-toc ol{counter-reset:none;margin:6px 0 0;padding-left:1.5em}
.art nav.art-toc li{margin:4px 0;font-weight:600}
.art nav.art-toc a{color:var(--ink);text-decoration:none;border-bottom:1px dashed var(--o)}
.art td.y{text-align:right;white-space:nowrap}
.art table.stack td.y{white-space:normal}
.art .tb{display:block;height:7px;border-radius:4px;background:var(--o);margin-top:5px;opacity:.85}
.art .tb.rg{background:#ffb37f}
.art td:last-child .tb{background:var(--o-d)}
.art td:last-child .tb.rg{background:#f08c4a}
@media (max-width:599px){
.art table.stack{background:transparent;font-size:.9rem}
.art table.stack thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.art table.stack tr{display:block;background:#fff;border:1.5px solid var(--line);border-radius:16px;margin:0 0 10px;overflow:hidden}
.art table.stack tbody th{display:block;border:0;background:var(--o-l);color:var(--o-d);text-align:left;padding:10px 14px;font-size:.98rem}
.art table.stack td{display:block;border:0;border-top:1px dashed var(--line);text-align:left;padding:8px 14px;background:transparent;font-weight:400}
.art table.stack td:last-child{background:transparent;font-weight:700}
.art table.stack td::before{content:attr(data-l);display:block;font-size:.72rem;font-weight:800;color:var(--ink-3);margin-bottom:1px}
}
.vstats{list-style:none;padding:0;margin:6px 0 20px;display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.vstats li{background:var(--o-l);border-radius:18px;padding:14px 14px 12px;margin:0;display:flex;flex-direction:column;gap:4px}
.vstats b{font-size:1.2rem;line-height:1.25;color:var(--o-d);font-weight:800;letter-spacing:-.01em}
.vstats span{font-size:.82rem;line-height:1.55;color:var(--ink-2)}
@media (min-width:600px){.vstats{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}.vstats b{font-size:1.55rem}}
.bars{margin:6px 0 22px;background:#fff;border:1.5px solid var(--line);border-radius:20px;padding:16px 16px 10px}
.bars figcaption{font-weight:800;color:var(--ink);font-size:.98rem;margin-bottom:10px}
.bars ol{list-style:none;padding:0;margin:0}
.bars li{display:grid;grid-template-columns:1fr auto;gap:2px 10px;align-items:center;margin:0 0 8px}
.bars .l{grid-column:1/-1;font-size:.84rem;color:var(--ink-2);line-height:1.45}
.bars .t{height:14px;background:#f7f4f1;border-radius:7px;overflow:hidden}
.bars .t i{display:block;height:100%;background:#ffb37f;border-radius:7px}
.bars li.hi .t i{background:var(--o)}
.bars li b{font-size:.92rem;color:var(--ink);white-space:nowrap}
.bars li.hi b{color:var(--o-d)}
.bars .note{font-size:.76rem;color:var(--ink-3);margin:4px 0 4px;line-height:1.6}
.vs{display:grid;gap:10px;margin:6px 0 20px}
.vs>div{border-radius:18px;padding:14px 16px 6px;background:#fff;border:2px solid var(--o)}
.vs>div.vb{border-color:var(--line);background:#fbfaf8}
.vs b.vh{display:block;font-size:1rem;margin-bottom:6px;color:var(--o-d)}
.vs .vb b.vh{color:var(--ink-2)}
.vs ul{padding-left:1.2em;margin:0 0 8px}
@media (min-width:600px){.vs{grid-template-columns:1fr 1fr}}
.flow{list-style:none;padding:0;margin:6px 0 20px;display:grid;gap:22px}
.flow li{position:relative;background:#fff;border:1.5px solid var(--line);border-radius:16px;padding:10px 14px;margin:0;text-align:center}
.flow li b{display:block;color:var(--o-d);font-size:.98rem}
.flow li span{display:block;font-size:.82rem;color:var(--ink-2);line-height:1.55}
.flow li:not(:last-child)::after{content:"";position:absolute;left:50%;bottom:-17px;margin-left:-7px;border:7px solid transparent;border-top:9px solid var(--o)}
@media (min-width:700px){.flow{grid-auto-flow:column;grid-auto-columns:1fr;gap:20px}.flow li:not(:last-child)::after{left:auto;right:-17px;top:50%;bottom:auto;margin:-7px 0 0;border:7px solid transparent;border-left:9px solid var(--o)}}
""".replace("CHECK", _CHECK)
