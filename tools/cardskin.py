# [B] 施設のカードの形を全部の分野でそろえる（Nori 2026-11-16「カードもばらばら。統一してー」）。
# gen_areas.py のいちばん最後（compact.py のあと）に動く。
# 見本は動物病院（hosp.js の .hc）とドッグラン（uikit の .ux-c）のカード：
#   白い箱・名前（太字・黒）・小さな場所の行・札・アイコン＋値の行・大きいボタン2つ（公式／経路）・小さな文字のリンク
# 作りかえるもの：
#  1. 犬・ペットと泊まれる宿の .yd-card（オレンジの名前・表の行・文字のリンクだけ だったもの）
#  2. 緊急・エリアページの夜間病院と搬送の会社の .emg-item.emg-co（ピンクの箱・文字のリンク だったもの）
#  3. 横に流れる施設カード .fc は形はそのまま、枠・角・影だけそろえる（CSS）
# 中身は消さない（表の4行目からは「くわしく」にたたむ）。何度動かしても同じ（cs の印で2回目はしない）。
import os, re
from urllib.parse import unquote


def quote(x):
    # 日本語はそのまま（ページを軽くする。ブラウザが送るときに直す）
    return re.sub(r'[%&#"<>?+\s]', lambda m: '%%%02X' % ord(m.group()), x)

SKIP_DIRS = ("hinan", "tools", "img", "lib", "node_modules")

CSS = ('<style id="cs-css">'
       '.cs.cs{background:#fff;border:1px solid #efe0d3;border-radius:14px;padding:12px 14px;margin:0 0 10px;box-shadow:none;display:block}'
       '.cs .ux-c-n{display:block;font-weight:800;font-size:1.02rem;color:#2b2622;text-decoration:none;line-height:1.35;margin:0}'
       '.cs .ux-c-n b{font-weight:800}'
       '.cs .ux-c-m{margin:2px 0 6px;font-size:.8rem;color:#7a6a5e}'
       '.cs .dr-tags{display:flex;flex-wrap:wrap;gap:5px;list-style:none;padding:0!important;margin:0 0 6px!important}'
       '.cs .dr-tags li{font-size:.74rem;font-weight:700;border-radius:999px;padding:2px 10px;background:#f7f4f1;color:#5b4f47;margin:0}'
       '.cs .dr-tags li.ok{background:#fff1e6;color:#a8410a}.cs .dr-tags li.an{background:#fff4e0;color:#8a5300}'
       '.cs .ux-c-l{margin:3px 0 0;font-size:.85rem;color:#4a3f37;display:flex;gap:6px;line-height:1.5}'
       '.cs .ux-c-l i{font-style:normal;flex:0 0 1.2em;text-align:center}'
       '.cs .ux-c-l small{display:inline;color:#7a6a5e;font-size:.76rem;margin-right:4px}'
       '.cs .ux-c-a{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}'
       '.cs .ux-c-a a{display:flex;align-items:center;justify-content:center;gap:4px;border-radius:12px;padding:10px 6px;font-weight:800;font-size:.88rem;text-decoration:none;background:#2b2622;color:#fff!important;border:1px solid #2b2622;min-width:0}'
       '.cs .ux-c-a a.emg-tel{white-space:nowrap;font-size:.84rem}.cs .ux-c-a a.l{background:#fff;color:#2b2622!important;border-color:#d9c9bb}'
       '.cs .ux-c-a a:only-child{grid-column:1/-1}'
       '.cs .ux-c-s{margin:8px 0 0;font-size:.82rem;text-align:center}'
       '.cs .ux-c-s a{color:#a8410a;font-weight:700;text-decoration:none}'
       '.cs .ux-c-d{margin-top:8px;border-top:1px solid #f5ebe2;padding-top:2px}'
       '.cs .ux-c-d summary{list-style:none;cursor:pointer;font-size:.85rem;font-weight:700;color:#a8410a;padding:6px 0;background:none!important;border:0!important}'
       '.cs .ux-c-d summary::-webkit-details-marker{display:none}.cs .ux-c-d summary::after{content:none!important;display:none!important}'
       '.cs .ux-c-d summary::before{content:"＋ "}.cs .ux-c-d[open] summary::before{content:"－ "}'
       '.cs .ux-c-d .ux-c-l{margin-top:4px}'
       '.cs .emg-score{margin-top:6px}'
       '.cs .cr{display:inline-flex;align-items:center;gap:4px;font-size:.8rem;color:#3c4043;margin:1px 10px 1px 0;white-space:nowrap}'
       '.cs .cr::before{content:"✓";display:inline-grid;place-items:center;width:15px;height:15px;border-radius:50%;background:#1e8e3e;color:#fff;font-size:10px;font-weight:900;flex:0 0 15px}'
       '.fc.cs .ux-c-l>span:has(.cr){display:flex;flex-wrap:wrap;-webkit-line-clamp:unset;overflow:visible}'
    '.cs .crd{display:inline-block;max-width:100%}.cs .crd:focus,.cs .crd:focus-within{flex-basis:100%}.cs .crd>.cr{cursor:pointer;text-decoration:underline dotted #9aa0a6;text-underline-offset:3px}.cs .crd>.crx{display:none}'
    '.cs .crd:focus>.crx,.cs .crd:focus-within>.crx{display:block;font-size:.8rem;line-height:1.6;color:#3c4043;background:#f1f3f4;border-radius:8px;padding:6px 9px;margin:3px 0 6px;white-space:normal}.cs .crd:focus{outline:none}.cs .crd>.cr{margin-right:10px}'
       '.cs-list{display:grid;gap:10px;margin:8px 0}.cs-list>.cs{margin:0}'
       '.fc.cs{padding:0;margin:0;display:flex;border-radius:14px;box-shadow:none;overflow:hidden}'
       '.fc.cs .fc-body{padding:12px 14px 12px}'
       '.cs .fc-catch{margin:4px 0 2px!important}'
       '.cs .cs-l.cs-p{font-weight:800;color:#2b2622}'
       '.cs .cs-l>span{min-width:0}'
       '.fc.cs .ux-c-l>span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}'
       '.fc.cs .dr-tags{margin:8px 0 0!important}'
       '.fc.cs .ux-c-a{margin-top:auto;padding-top:10px}'
       '.fc.cs .fc-acts{display:flex;flex-wrap:wrap;justify-content:center;gap:2px 14px;margin:8px 0 0;padding:0}'
       '.cs .fc-acts .fc-a,.cs .fc-acts .partner-review-open,.cs .fc-acts .fac-act a,.cs .fc-acts .fac-act button{border:0!important;background:none!important;padding:4px 0!important;min-height:0;font-size:.8rem!important;color:#a8410a!important;border-radius:0!important}'
       '.cs .fc-acts .fc-a::before,.cs .fc-acts .partner-review-open::before{display:none}'
       '.cs .fc-acts .fac-act a.fac-site{display:none!important}'
       '.cs .fc-more[open]>summary{border:0!important}'
       '.cs .fc-more-b{text-align:left}'
       '</style>')

YD_IC = {"犬の大きさ": "🐕", "頭数": "🐾", "犬の料金": "¥", "料金": "¥", "一緒にいられる": "🏠",
         "犬以外": "🐈", "条件": "📋", "大きさ": "🐕"}


def _attrs(tag):
    return dict(re.findall(r'([a-z-]+)="([^"]*)"', tag))


def _route(name, addr):
    return ('<a class="l" href="https://www.google.com/maps/dir/?api=1&amp;destination='
            + quote(f"{name} {addr}".strip()) + '" target="_blank" rel="noopener" data-route>経路を見る</a>')


def _line(ic, body, label=""):
    lb = f"<small>{label}</small>" if label else ""
    return f'<p class="ux-c-l cs-l"><i aria-hidden="true">{ic}</i><span>{lb}{body}</span></p>'


def _end(h, i):
    d = 0
    for m in re.compile(r"<(/?)div\b[^>]*>").finditer(h, i):
        d += -1 if m.group(1) else 1
        if d == 0: return m.end()
    return -1


def _add_cls(open_tag):
    return re.sub(r'class="([^"]*)"', lambda m: f'class="{m.group(1)} cs"', open_tag, count=1)


def yd(blk):
    """.yd-card → 見本の形。"""
    ot = re.match(r"<div[^>]*>", blk).group(0)
    inner = blk[len(ot):-6]
    m = re.search(r'<h3><a ([^>]*)>(.*?)</a></h3>', inner, re.S)
    if not m: return None
    a = _attrs(m.group(1)); name = re.sub(r"\s*↗\s*$", "", re.sub(r"<[^>]+>", "", m.group(2))).strip()
    href = a.get("href", "")
    off = f' data-official="{a["data-official"]}"' if "data-official" in a else ""
    out = [f'<a class="ux-c-n" href="{href}" target="_blank" rel="noopener"{off}><b>{name}</b></a>']
    at = re.search(r'<p class="yd-at">(.*?)</p>', inner, re.S)
    if at: out.append(f'<p class="ux-c-m">{at.group(1)}</p>')
    ch = re.search(r'<ul class="yd-chips">(.*?)</ul>', inner, re.S)
    if ch: out.append(f'<ul class="dr-tags">{ch.group(1)}</ul>')
    dl = re.search(r"<dl>(.*?)</dl>", inner, re.S)
    rows = re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", dl.group(1), re.S) if dl else []
    lines = [_line(YD_IC.get(k.strip(), "・"), v, k) for k, v in rows]
    out += lines[:3]
    if len(lines) > 3:
        out.append('<details class="ux-c-d"><summary>くわしく</summary>' + "".join(lines[3:]) + "</details>")
    go = re.search(r'<p class="yd-go">(.*?)</p>', inner, re.S)
    taxi, addr = "", ""
    if go:
        links = re.findall(r"<a [^>]*>.*?</a>", go.group(1), re.S)
        for l in links:
            if "data-taxi-cta" in l or "?to=" in l:
                taxi = l
                t = re.search(r"\?to=([^#&\"]+)", l)
                if t: addr = unquote(t.group(1))
    btn = [f'<a href="{href}" target="_blank" rel="noopener"{off}>公式サイト ↗</a>']
    if addr: btn.append(_route(name, addr))
    out.append('<div class="ux-c-a">' + "".join(btn) + "</div>")
    # 表・ボタン以外の部品（口コミの枠など）は残す
    rest = inner
    for pat in (r'<h3><a [^>]*>.*?</a></h3>', r'<p class="yd-at">.*?</p>', r'<ul class="yd-chips">.*?</ul>', r"<dl>.*?</dl>", r'<p class="yd-go">.*?</p>'):
        rest = re.sub(pat, "", rest, count=1, flags=re.S)
    if rest.strip(): out.append(rest)
    if taxi: out.append(f'<p class="ux-c-s">{taxi}</p>')
    return _add_cls(ot) + "".join(out) + "</div>"


def emg(blk):
    """緊急の病院・搬送の会社の .emg-item.emg-co → 見本の形。"""
    ot = re.match(r"<div[^>]*>", blk).group(0)
    inner = blk[len(ot):-6]
    m = re.match(r'\s*<a ([^>]*)><b>(.*?)</b></a>', inner, re.S)
    if not m: return None
    a = _attrs(m.group(1)); href = a.get("href", ""); name = m.group(2)
    pos = m.end()
    smalls = re.findall(r'<small( class="[^"]*")?>(.*?)</small>', inner, re.S)
    tel = re.search(r'<a class="emg-tel"[^>]*>.*?</a>', inner, re.S)
    score = re.search(r'<div class="emg-score"[^>]*></div>', inner)
    taxi = re.search(r'<a class="emg-taxi"[^>]*>.*?</a>', inner, re.S)
    review = re.search(r'<a class="emg-review-link"[^>]*>.*?</a>', inner, re.S)
    left = inner[pos:]
    for x in [r'<small( class="[^"]*")?>.*?</small>', r'<a class="emg-tel"[^>]*>.*?</a>', r'<div class="emg-score"[^>]*></div>', r'<a class="emg-taxi"[^>]*>.*?</a>']:
        left = re.sub(x, "", left, flags=re.S)
    if review: left = left.replace(review.group(0), "", 1)
    if left.strip(): return None  # 知らない部品があれば作りかえない
    out = [f'<a class="ux-c-n" href="{href}" target="_blank" rel="noopener"><b>{name}</b></a>']
    addr = ""
    for k, (cls, s) in enumerate(smalls):
        if cls and "emg-spec" in cls:
            out.append(_line("🩺", s)); continue
        if s.startswith("所在地："):
            addr = s[4:]; out.append(_line("📍", s)); continue  # 「所在地：」は残す（ほかのページと同じ文にならないように）
        if s.startswith("対応エリア："):
            out.append(_line("🗺", s[6:])); continue
        if k == 0 and "・" in s:
            p, t = s.split("・", 1)
            out.append(f'<p class="ux-c-m">{p}</p>'); out.append(_line("🕒", t)); continue
        out.append(_line("・", s))
    if score: out.append(score.group(0))
    btn = [f'<a href="{href}" target="_blank" rel="noopener">公式サイト ↗</a>']
    if tel:  # 搬送は電話が先。受付時間などの（…）はボタンの外の行へ
        tm = re.match(r'(<a [^>]*>)(.*?)</a>', tel.group(0), re.S)
        num, note = tm.group(2), ""
        k = num.find("（")
        if k > 0: num, note = num[:k].strip(), (num[k + 1:-1] if num.endswith("）") else num[k + 1:]).strip()
        if note: out.append(_line("📞", note))
        btn = [tm.group(1) + num + "</a>", f'<a class="l" href="{href}" target="_blank" rel="noopener">公式サイト ↗</a>']
    elif addr: btn.append(_route(re.sub(r"<[^>]+>", "", name), addr))
    if review: btn.append(review.group(0).replace('class="emg-review-link"', 'class="emg-review-link l"', 1))
    out.append('<div class="ux-c-a">' + "".join(btn) + "</div>")
    if taxi: out.append(f'<p class="ux-c-s">{taxi.group(0)}</p>')
    return _add_cls(ot) + "".join(out) + "</div>"


FC_IC = {"pin": "📍", "clock": "🕒", "car": "🚗", "yen": "¥", "paw": "🐾", "badge": "🏅"}


def fc(blk):
    """横に流れる施設カード .fc → 共通の形（写真の枠・地域の横スワイプはそのまま）。"""
    ot = re.match(r"<div[^>]*>", blk).group(0)
    a0 = _attrs(ot)
    # 名前
    def _name(m):
        a = _attrs(m.group(1))
        off = f' data-official="{a["data-official"]}"' if "data-official" in a else ""
        return f'<a class="ux-c-n" href="{a.get("href", "")}" target="_blank" rel="noopener"{off}>{m.group(2)}</a>'
    b = re.sub(r'<div class="fc-name"><a ([^>]*)>(.*?)</a></div>', _name, blk, count=1, flags=re.S)
    nm = re.search(r'<a class="ux-c-n" href="([^"]*)"[^>]*>(.*?)</a>', b, re.S)
    if not nm: return None
    href, name = nm.group(1), re.sub(r"<[^>]+>", "", nm.group(2)).strip()
    # アイコンの行
    def _ln(m):
        ic = FC_IC.get(m.group(2), "・")
        cls = " cs-p" if m.group(1) == "price" else ""
        sty = ' style="display:block;overflow:visible"' if 'title="ご利用の前に"' in m.group(0)[:80] else ""  # 来館先の注記は途中で切らずに全部見せる
        return f'<p class="ux-c-l cs-l{cls}"><i aria-hidden="true">{ic}</i><span{sty}>{m.group(3)}</span></p>'
    b = re.sub(r'<p class="fc-(line|price)"[^>]*><svg[^>]*><use href="#fci-([a-z]+)"/></svg><span>(.*?)</span></p>', _ln, b, flags=re.S)
    b = b.replace('<ul class="fc-tags">', '<ul class="dr-tags">')
    # 大きいボタン2つ：公式サイト・経路（行き先が分かるときだけ）
    acts = re.search(r'<div class="fc-acts">', b)
    if not acts: return None
    off_btn = re.search(r'<a class="ux-btn" href="([^"]*)"[^>]*>[^<]*</a>', b)
    if off_btn:
        href = off_btn.group(1); b = b.replace(off_btn.group(0), "", 1)
    lab = "公式ページ ↗" if re.search(r"\.(lg\.jp|go\.jp)|/city\.|\.pref\.", href) else "公式サイト ↗"
    btn = [f'<a href="{href}" target="_blank" rel="noopener">{lab}</a>']
    to = a0.get("data-to", "")
    if to and re.search(r"[都道府県市区町村郡]", to):
        # 廣瀬さん指定の京都の事業所。店名で検索すると別の教室が選ばれる場合がある。
        office_pin = a0.get("data-cat") == "trainer" and a0.get("data-fid") == "T114"
        dest = to if office_pin or name in to else f"{name} {to}"
        route_label = "事業所への経路" if office_pin else "経路を見る"
        btn.append('<a class="l" href="https://www.google.com/maps/dir/?api=1&amp;destination=' + quote(dest) + f'" target="_blank" rel="noopener" data-route>{route_label}</a>')
    grid = '<div class="ux-c-a">' + "".join(btn) + "</div>"
    b = b[:acts.start()] + grid + b[acts.start():]
    return _add_cls(b[:len(ot)]) + b[len(ot):]


CAFE_IC = {"犬と入れる席": "🪑", "犬の大きさ": "🐕", "営業時間": "🕒", "定休日": "📅"}


def _cafes():
    import json
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cafes.json")
    return {c["id"]: c for c in json.load(open(p, encoding="utf-8"))["cafes"]}


def cafe_card(tr, C):
    m = re.search(r'<a href="(/inu-cafe/[^/]+/([^/]+)/)">(.*?)</a>', tr)
    if not m or m.group(2) not in C: return None
    c, page, name = C[m.group(2)], m.group(1), m.group(3)
    attrs = re.match(r"<tr([^>]*)>", tr).group(1)
    f = {x["k"]: x["v"] for x in c.get("facts", [])}
    out = [f'<a class="ux-c-n" href="{page}">{name}</a>', f'<p class="ux-c-m">{c.get("pref", "")}{c.get("city", "")}・{c.get("kind", "カフェ")}</p>']
    tags = []
    if f.get("犬用メニュー"): tags.append('<li class="ok">犬用メニュー</li>')
    if f.get("ドッグラン") or "ドッグラン" in c.get("note", ""): tags.append("<li>ドッグラン</li>")
    if tags: out.append('<ul class="dr-tags">' + "".join(tags) + "</ul>")
    for k in ("犬と入れる席", "犬の大きさ", "営業時間", "定休日"):
        if f.get(k): out.append(_line(CAFE_IC[k], f[k], k))
    url = c["url"] + ("&" if "?" in c["url"] else "?") + "utm_source=pet.shiokonbu.com&amp;utm_medium=referral&amp;utm_campaign=cafe_cards"
    btn = [f'<a href="{url}" target="_blank" rel="noopener">公式サイト ↗</a>']
    if f.get("所在地"): btn.append(_route(re.sub(r"<[^>]+>", "", name), f["所在地"]))
    out.append('<div class="ux-c-a">' + "".join(btn) + "</div>")
    out.append(f'<p class="ux-c-s"><a href="{page}">くわしく見る</a></p>')
    return f'<div class="ux-c cs"{attrs}>' + "".join(out) + "</div>"


def cafe_hub(h):
    if "<tr data-ffi" not in h: return h, 0
    C = _cafes(); n = [0]
    def tbl(m):
        rows = re.findall(r"<tr data-ffi.*?</tr>", m.group(0), re.S)
        cards = [cafe_card(r, C) for r in rows]
        if not rows or any(x is None for x in cards): return m.group(0)
        n[0] += len(cards)
        return '<div class="cs-list">' + "".join(cards) + "</div>"
    h = re.sub(r'<div class="tbl"><table class="pp-tbl cmp[^"]*">.*?</table></div>', tbl, h, flags=re.S)
    return h, n[0]


def page(h):
    if 'id="cs-css"' in h: return h
    out, pos, n = [], 0, 0
    for m in re.finditer(r'<div class="(emg-item yd-card|emg-item emg-co|emg-item emg-co fc[^"]*)"( [^>]*)?>', h):
        if m.start() < pos: continue
        isfc = " fc" in m.group(1)
        if not isfc and m.group(1) == "emg-item emg-co" and "data-cat=" in (m.group(2) or ""): continue  # 施設1つのページの入口の枠
        j = _end(h, m.start())
        if j < 0: continue
        blk = h[m.start():j]
        new = (fc if isfc else yd if "yd-card" in m.group(1) else emg)(blk)
        if not new: continue
        out.append(h[pos:m.start()]); out.append(new); pos = j; n += 1
    out.append(h[pos:])
    h2 = "".join(out)
    if 'data-cat="cafe"' in h2 or "/inu-cafe/" in h2[:3000] or 'href="/inu-cafe/' in h2:
        h2, k = cafe_hub(h2); n += k
    if n or 'class="jc-card cs' in h2:  # 迷子・登録の窓口のカードは生成側（gen_jichitai.py）が共通の形で出す
        h2 = h2.replace("</head>", CSS + "</head>", 1)
    return h2


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


if __name__ == "__main__":
    import sys
    print("cardskin", build(sys.argv[1] if len(sys.argv) > 1 else "."), "pages")
