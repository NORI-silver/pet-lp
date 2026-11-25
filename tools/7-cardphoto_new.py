# [C] 事業者カードに写真を出す（Nori 2026-11-16「事業者カードへの写真表示 実装指示」）。gen_areas.py の最後（cardskin.py のあと）に動く。
#
# 写真の元は tools/photos.json だけ（使ってよいと確かめた写真。手で写さない：tools/photo_import.py が入れる）。並び順は
#   1. owner   … 事業者が自分で登録した写真（掲載情報のページ・メールで受け取ったもの）
#   2. permit  … 事業者が「サイトの写真を使ってよい」と言ってくれた（tools/photo_permits.json に記録）→ 公式サイトから取ってきた写真
#   3. license … 公式サイトの決まりで転載を許している（CC BY・政府標準利用規約など）。出どころの表示（写真：◯◯）を付ける
# 写真のないカードは、共通の枠（足あとのアイコンだけ。汎用の「イメージ」写真は使わない）を出す（Nori 同日「掲載可能な写真がない場合は共通のプレースホルダー」）。
# 写真は 全体を縮めた webp（1枚 20〜40KB）、loading="lazy"。横にスワイプで切りかえ（CSS だけ、JSなし）。何度動かしても同じ（cp の印）。
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = ("hinan", "tools", "img", "lib", "node_modules", "jichitai", "guide", "terms", "partner", "contact", "go", "sns")
ORDER = {"owner": 0, "permit": 1, "license": 2}
PLACEHOLDER_ON = True  # 写真のないカードに共通の枠を出す（Nori 2026-11-16 の指示4）。やめるときは False

PAW = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64' fill='%23e3cdb9'%3E"
       "%3Cellipse cx='32' cy='42' rx='13' ry='11'/%3E%3Cellipse cx='16' cy='28' rx='5.5' ry='7'/%3E%3Cellipse cx='48' cy='28' rx='5.5' ry='7'/%3E"
       "%3Cellipse cx='25' cy='17' rx='5.5' ry='7.5'/%3E%3Cellipse cx='39' cy='17' rx='5.5' ry='7.5'/%3E%3C/svg%3E")

CSS = ('<style id="cp-css">'
       '.cs-ph{position:relative;background:#f6efe8;overflow:hidden}'
       '.cs-ph0{aspect-ratio:4/3;background:#f8f3ee url("' + PAW + '") center/38px no-repeat}'
       '.cs-ph-s{display:flex;aspect-ratio:4/3;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;-webkit-overflow-scrolling:touch}'
       '.cs-ph-s::-webkit-scrollbar{display:none}'
       '.cs-ph-i{flex:0 0 100%;position:relative;overflow:hidden;scroll-snap-align:start;background:#efe6dc}'
       '.cs-ph-i img{position:relative;display:block;width:100%;height:100%;object-fit:contain}'
       '.cs-ph-i .b{position:absolute;left:-24px;top:-24px;width:calc(100% + 48px);height:calc(100% + 48px);object-fit:cover;filter:blur(22px) saturate(1.15);opacity:.9}'
       '.cs-ph-n{position:absolute;right:8px;top:8px;background:rgba(0,0,0,.55);color:#fff;font-size:11px;font-weight:700;border-radius:999px;padding:1px 8px;pointer-events:none}'
       '.cs-ph .cs-ph-c{display:block;background:#f6efe8;color:#6b5a4c;opacity:1;font-size:11px;font-weight:400;padding:2px 8px;white-space:normal;line-height:1.35}'  # 出どころの文は省かずに出す（許可の条件の表記）
       '.cs-ph .cs-ph-c a{color:#6b5a4c}'
       '.fr-s{align-items:stretch}'
       '.cs:not(.fc)>.cs-ph,.ux-c>.cs-ph{margin:-12px -14px 10px;border-radius:14px 14px 0 0}'
       '.hc>.cs-ph{margin:-14px -14px 10px;border-radius:14px 14px 0 0}'
       '.cs-ph-w{position:relative}'
       '.cs-ph-d{position:absolute;left:50%;bottom:7px;transform:translateX(-50%);display:flex;gap:5px;padding:3px 7px;border-radius:999px;background:rgba(0,0,0,.35);pointer-events:none}'
       '.cs-ph-d i{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.55)}'
       '.cs-ph-d i.on{background:#fff}'
       '.cs-ph-a{position:absolute;top:50%;width:28px;height:28px;margin-top:-14px;padding:0 0 3px;border:0;border-radius:50%;background:rgba(255,255,255,.78);color:#3d2f25;font-size:20px;line-height:28px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.25);cursor:pointer;opacity:.9}'
       '.cs-ph-a.l{left:6px}.cs-ph-a.r{right:6px}'
       '.cs-ph-w.f .cs-ph-a.l,.cs-ph-w.e .cs-ph-a.r{display:none}'
       '</style>')


def norm(u):
    u = html.unescape(u or "").split("#")[0]
    u = re.sub(r"[?&]utm_[^&]*", "", u)
    u = re.sub(r"^https?://(www\.)?", "", u).rstrip("/?&")
    return u.lower()


def load():
    p = os.path.join(HERE, "photos.json")
    if not os.path.exists(p): return {}, {}
    items = json.load(open(p, encoding="utf-8")).get("items", [])
    items.sort(key=lambda x: ORDER.get(x.get("by"), 9))
    by_id, by_url = {}, {}
    for x in items:
        if not x.get("photos"): continue
        by_id.setdefault(x["id"], x)
        if x.get("url"): by_url.setdefault(norm(x["url"]), x)
    return by_id, by_url


def strip(x, name, gph="", compact=False):
    """写真の並び（横スワイプ）。x が None なら共通の枠。"""
    g = f' data-gph="{html.escape(gph)}"' if gph else ""
    if not x:
        return f'<div class="cs-ph cs-ph0"{g} aria-hidden="true"></div>' if PLACEHOLDER_ON else ""
    ps = x["photos"][:5]
    alt = html.escape(re.sub(r"<[^>]+>", "", name))
    rs = x.get("ratio") or []
    imgs = "".join(f'<i class="cs-ph-i"><img class="b" src="{html.escape(p)}" alt="" aria-hidden="true" loading="lazy" decoding="async"><img src="{html.escape(p)}" alt="{alt}の写真{i + 1}" loading="lazy" decoding="async"></i>' for i, p in enumerate(ps))
    n = f'<span class="cs-ph-n" aria-hidden="true">📷 {len(ps)}</span>' if len(ps) > 1 else ""
    cr = ""
    if x.get("by") != "owner" and x.get("credit"):  # サイトの決まり（CC BY など）や事業者の許可の条件で出どころの表示が要る
        cr = f'<small class="cs-ph-c">{html.escape(x["credit"])}' + (f'（<a href="{html.escape(x["lic_url"])}" target="_blank" rel="noopener">{html.escape(x.get("license", ""))}</a>）' if x.get("lic_url") else "") + "</small>"
    # 写真の縦横比に枠を合わせる（余白なし・切らない。極端な縦横比だけ 3:5〜3:1 に丸める）。共通CSSは変えず、カードごとの style で上書きする
    # 全国ページ（SEO 検査の上限 60KB gzip）だけ、写真の並びを ga.js が作る（_1 〜 _N の並びの写真に限る。枚数・ドット・矢印・全体表示・出どころの表示は同じ）。県のページは今まで通り全部書く。
    if compact and re.fullmatch(r"[1-5]", str(len(ps))) and all(p == re.sub(r"_1\.webp$", "_%d.webp" % (i + 1), ps[0]) and ps[0].endswith("_1.webp") for i, p in enumerate(ps)):
        return f'<div class="cs-ph"{g} data-p="{html.escape(ps[0][:-6])}{len(ps)}"><div class="cs-ph-s"></div>{cr}</div>'
    return f'<div class="cs-ph"{g}><div class="cs-ph-s">{imgs}</div>{n}{cr}</div>'


_OPEN = re.compile(r'<div class="(emg-item emg-co fc[^"]*\bcs\b[^"]*|emg-item emg-co cs[^"]*|emg-item yd-card[^"]*\bcs\b[^"]*|ux-c dr-card[^"]*)"([^>]*)>')


def _end(h, i):
    d = 0
    for m in re.compile(r"<(/?)div\b[^>]*>").finditer(h, i):
        d += -1 if m.group(1) else 1
        if d == 0: return m.end()
    return -1


_TRANSPORT_PAGES = frozenset(("area", "tokyo", "chiba", "kanagawa", "saitama", "emergency"))


def page(h, by_id, by_url, top="", compact=False):
    if 'id="cp-css"' in h: return h, 0
    out, pos, n = [], 0, 0
    for m in _OPEN.finditer(h):
        if m.start() < pos: continue
        j = _end(h, m.start())
        if j < 0: continue
        blk = h[m.start():j]
        if 'class="cs-ph' in blk: continue
        ids = re.findall(r'data-fid="([^"]+)"|\bid="([^"]+)"', m.group(0)) + re.findall(r'class="emg-score" data-id="([^"]+)"()', blk)
        ids = [a or b for a, b in ids if a or b]
        x = next((by_id[i] for i in ids if i in by_id), None)
        if not x:
            for u in re.findall(r'href="(https?://[^"]+)"', blk):
                if "google.com/maps" in u: continue
                x = by_url.get(norm(u))
                # A taxi can share its website with a hotel or grooming service.
                # Its service-specific photo must not follow that shared URL.
                if x and x.get("cat") in ("taxi", "emergency") and top not in _TRANSPORT_PAGES:
                    x = None
                if x: break
        nm = re.search(r'class="ux-c-n"[^>]*>(.*?)</(?:a|h3)>', blk, re.S)
        gph = next((i for i in re.findall(r'class="emg-score" data-id="([^"]+)"', blk)), "")
        s = strip(x, nm.group(1) if nm else "", gph, compact)
        if not s: continue
        ot = m.group(0)
        out += [h[pos:m.start()], ot, s, blk[len(ot):]]
        pos = j; n += 1
    out.append(h[pos:])
    h2 = front("".join(out))
    if n or "/hosp.js" in h2:
        photo_css = CSS
        h2 = h2.replace("</head>", photo_css + "</head>", 1)
    return h2, n


def rich(blk):
    """カードの情報の多さ（公式サイトの情報からできた行・札・資格・ひとことの数）。"""
    return (blk.count('class="ux-c-l') + min(blk.count("<li>"), 6) + blk.count('class="crd"')
            + 2 * ('class="fc-catch"' in blk) + min(blk.count("<small>"), 6))


def front(h):
    h = _front(h, _OPEN, lambda t: (-('class="cs-ph"' in t), -rich(t)))
    # 写真のあるカードがある地域の列も、そのページの先頭のほうへ（地域の中の順は上で決まる）
    return _front(h, re.compile(r'<div class="fr">'), lambda t: -('class="cs-ph"' in t))


def _front(h, pat, key):
    """写真のあるカード・情報の多いカードを、同じ並び（横スワイプの列・一覧）の先頭へ。
    Nori 2026-11-22「写真付きとかの事業者は一番前に動かしてね」。同じなら元の順（安定な並べかえ）。"""
    blks = []
    for m in pat.finditer(h):
        if blks and m.start() < blks[-1][1]: continue
        j = _end(h, m.start())
        if j > 0: blks.append((m.start(), j))
    runs, cur = [], []
    for b in blks:
        if cur and h[cur[-1][1]:b[0]].strip() == "": cur.append(b)
        else:
            if len(cur) > 1: runs.append(cur)
            cur = [b]
    if len(cur) > 1: runs.append(cur)
    out, pos = [], 0
    for run in runs:
        parts = [h[a:b] for a, b in run]
        gaps = [h[run[k][1]:run[k + 1][0]] for k in range(len(run) - 1)]
        srt = sorted(parts, key=key)
        if srt == parts: continue
        out += [h[pos:run[0][0]], srt[0]] + [g + t for g, t in zip(gaps, srt[1:])]
        pos = run[-1][1]
    out.append(h[pos:])
    return "".join(out)


def build(root):
    by_id, by_url = load()
    pages = cards = 0
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root)
        top = rel.split(os.sep)[0]
        if rel != "." and (top.startswith(".") or top in SKIP_DIRS): dn[:] = []; continue
        if rel == "." or "index.html" not in fn: continue  # トップ（タクシーの候補カード）は index.html の buildCard が出す
        f = os.path.join(dp, "index.html")
        t = open(f, encoding="utf-8").read()
        if 'http-equiv="refresh"' in t: continue
        u, k = page(t, by_id, by_url, top, rel == "dog-trainer")
        if u != t: open(f, "w", encoding="utf-8").write(u); pages += 1; cards += k
    return pages, cards, sum(1 for _ in by_id)


def taxi_map():
    """タクシーの候補カード用（index.html の CO_PH）。会社ID → [写真のURL…, 出どころの表示]。"""
    by_id, _ = load()
    out = {}
    for i, x in by_id.items():
        if x.get("cat") in ("taxi", "emergency"):
            out[i] = [x["photos"][:5], x.get("credit", "") if x.get("by") != "owner" else ""]
    return out


def hosp_photo(h):
    """病院のさがす欄（hosp.js）用。その病院の写真の一覧と出どころの表示（なければ None）。"""
    global _H
    try: _H
    except NameError: _H = load()
    by_id, by_url = _H
    x = by_id.get(h.get("id", "")) or by_url.get(norm(h.get("url", "")))
    if not x: return None
    r0 = (x.get("ratio") or [0])[0] or 0  # photos.json に入れた縦横比を先に使う（Pillow が無い環境でも同じ結果になる）
    if not r0:
      try:
        from PIL import Image
        im = Image.open(os.path.join(os.path.dirname(HERE), x["photos"][0].lstrip("/")))
        r0 = round(im.width / im.height, 3)
      except Exception: pass
    out = [x["photos"][:5], x.get("credit", "") if x.get("by") != "owner" else "", r0]
    rs = (x.get("ratio") or [])[:5]
    if r0 and len(rs) == len(out[0]) and any(abs(r - r0) > 0.02 * r0 for r in rs): out.append(rs)  # 縦横比がちがう写真が混じる病院だけ、1枚ずつの比を渡す（hosp.js が data-r に入れ、cp-js が枠を合わせる）
    return out


if __name__ == "__main__":
    import sys
    print("cardphoto", build(sys.argv[1] if len(sys.argv) > 1 else "."))
