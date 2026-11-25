"""[E] 県を選んだら、その県の施設を全部その場に出すためのデータ（Nori 2026-11-24「すでに東京を選んでるんだから全部出して」）。

全国のページ（ハブ）は重くならないよう県ごとに数件だけ載せ、のこりは県のページへのリンクにしている。
そこで、生成済みの県ページ・市区町村ページから さがす箱のカード（[data-ffi]）を抜き出し、
/find-data/<分野>/<県のスラッグ>.json に市区町村ごとのまとまりで書く。/find.js が県の選択時に読み、
その県のまとまりを全部のカードに置きかえる（県のページへ逃がさない）。
呼び出しは gen_areas.py の最後（uikit.build のあと。カードに data-ffi・data-k が付いたあと）。
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
CATS = ["pet-hotel", "pet-sitter", "trimming", "dog-trainer", "rojin-home", "sougi", "joto"]

_OPEN = re.compile(r'<div[^>]*\bdata-ffi\b[^>]*>')
_DIV = re.compile(r'<div\b|</div>')
_FRH = re.compile(r'<h3 class="fr-h">([^<]+)')
_ATTR = lambda t, a: (re.search(r'\b%s="([^"]*)"' % a, t) or [None, ""])[1]


def _pref_slugs():
    from prefs import PREFS
    s = {x[0] for x in PREFS}
    s |= {"tokyo", "kanagawa", "saitama", "chiba"}
    return s


def _cards(h):
    """ページの中の [data-ffi] カードを (HTML, 市区町村) で返す。市区町村は data-city、なければ直前の .fr-h の見出し。"""
    out = []
    heads = [(m.start(), re.sub(r"\s+", "", m.group(1))) for m in _FRH.finditer(h)]
    for m in _OPEN.finditer(h):
        depth, i = 0, m.start()
        for d in _DIV.finditer(h, m.start()):
            depth += 1 if d.group(0) == "<div" else -1
            if depth == 0:
                i = d.end()
                break
        tag = m.group(0)
        if "data-near" in tag:
            continue
        city = _ATTR(tag, "data-city")
        if not city:
            prev = [t for p, t in heads if p < m.start()]
            city = prev[-1] if prev else ""
        out.append((h[m.start():i], city))
    return out


def build(ROOT):
    slugs = _pref_slugs()
    n_files = n_cards = 0
    for cat in CATS:
        base = os.path.join(ROOT, cat)
        if not os.path.isdir(base):
            continue
        for slug in sorted(os.listdir(base)):
            pdir = os.path.join(base, slug)
            if slug not in slugs or not os.path.isdir(pdir):
                continue
            pages = [os.path.join(pdir, "index.html")]
            for sub in sorted(os.listdir(pdir)):
                p2 = os.path.join(pdir, sub, "index.html")
                if os.path.isfile(p2):
                    pages.append(p2)
            groups, seen = {}, set()
            for p in pages:
                if not os.path.isfile(p):
                    continue
                h = open(p, encoding="utf-8").read()
                for html, city in _cards(h):
                    key = _ATTR(html[:html.find(">") + 1], "data-fid") or (_ATTR(html[:html.find(">") + 1], "data-name") + "|" + city)
                    if key in seen:
                        continue
                    seen.add(key)
                    groups.setdefault(city, []).append(html)
            if not groups:
                continue
            rows = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            out = {"groups": [[c, hs] for c, hs in rows]}
            d = os.path.join(ROOT, "find-data", cat)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, slug + ".json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
            n_files += 1
            n_cards += sum(len(v) for v in groups.values())
    return n_files, n_cards
