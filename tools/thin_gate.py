# [B] 薄いページを検索に出さない（Nori 2026-11-14「じゃあそうしてよ」＝中身が足りるまで検索に出さない）。
# ページの本文（<main> の中。script・style・nav・footer・form・目次を除く）を、文と箇条書き・表の欄ごとに分け、
# サイトの5ページ以上に出てくるひな形の文を除いた「そのページだけの字数」を数える。MIN_CHARS に足りないページは
# サイトマップから外して noindex,follow にする。足りるようになれば、次の gen_areas.py で自動で外れる（手で戻す必要なし）。
# タクシーのページ（トップ・エリア・市・規約・提携）は対象外。検索の多いページで答えがはっきりしているものだけ
# tools/thin_keep.json に理由つきで入れて残す。どの分野の新しいページも、gen_areas.py を通ればこの決まりに従う。
import os, re, json
from collections import Counter

MIN_CHARS = 900
TEMPLATE_DF = 5  # 5ページ以上に出る文はひな形とみなす（施設の名前は県・施設・全国のページに出るので3では厳しすぎる）
SKIP_TAGS = ("script", "style", "nav", "footer", "form", "noscript", "template")


def _segments(html):
    m = re.search(r"<main[^>]*>(.*)</main>", html, re.S)
    t = m.group(1) if m else ""
    for tag in SKIP_TAGS:
        t = re.sub(r"<%s\b.*?</%s>" % (tag, tag), " ", t, flags=re.S)
    t = re.sub(r'<details class="toc2".*?</details>', " ", t, flags=re.S)
    t = re.sub(r"&[a-z#0-9]+;", " ", t)
    out = []
    for part in re.split(r"<[^>]+>", t):
        for s in re.split(r"(?<=[。！？])", part):
            s = re.sub(r"\s+", "", s)
            if len(s) >= 2: out.append(s)
    return out


def measure(root, paths):
    segs = {}
    for p in paths:
        f = os.path.join(root, p.strip("/"), "index.html")
        if os.path.exists(f): segs[p] = set(_segments(open(f, encoding="utf-8").read()))
    df = Counter(s for v in segs.values() for s in v)
    return {p: sum(len(s) for s in v if df[s] < TEMPLATE_DF) for p, v in segs.items()}


# 数える分野（URLの最初のフォルダ）。ここにない分野（ペットタクシーのトップ・エリア・市・規約・提携）は対象外。
# 新しい情報の分野を作ったらここに足す。分野の入口のページ（/dogrun/ など1段目）は一覧の入口なので数えない。
CATS = ("guide", "dogrun", "sougi", "hospital", "jichitai", "hinan", "joto", "pet-sitter", "trimming", "dog-trainer",
        "rojin-home", "pet-hotel", "inu-yado", "pet-yado", "inu-cafe", "emergency")


def target(p):
    parts = [x for x in p.split("/") if x]
    return len(parts) >= 2 and parts[0] in CATS


def keep_list(root):
    return json.load(open(os.path.join(root, "tools", "thin_keep.json"), encoding="utf-8"))["pages"]


def thin(root, paths):
    keep = keep_list(root)
    n = measure(root, paths)  # ひな形の文はサイト全体で数えるので、対象外のページも数えに入れる
    return {p: c for p, c in n.items() if c < MIN_CHARS and target(p) and p not in keep}, n


def all_pages(root):
    """リポジトリにある全部のページ（noindex のページも）。"""
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith(".") and d not in ("tools", "node_modules", "tests", "img", "lib", "docs", "sns", "booking")]
        if "index.html" in fn:
            # 県のページへ移した案内だけのページ（tools/thin_hosp.py。noindex・サイトマップなし）は本文がないので数えない
            if 'http-equiv="refresh"' in open(os.path.join(dp, "index.html"), encoding="utf-8").read(2000): continue
            rel = os.path.relpath(dp, root).replace(os.sep, "/")
            out.append("/" if rel == "." else "/" + rel + "/")
    return out


def baseline(root):
    f = os.path.join(root, "tools", "thin_baseline.json")
    return json.load(open(f, encoding="utf-8"))["pages"] if os.path.exists(f) else []


def new_thin(root):
    """薄いページを新しく作っていないか（Nori 2026-11-14「そもそも薄い記事作らないで」）。
    2026-11-14 にあった薄いページ（thin_baseline.json）だけは、中身を足すまで noindex で残す。それ以外の薄いページは作らない＝CI で止める。"""
    n = measure(root, all_pages(root))
    keep, base = keep_list(root), set(baseline(root))
    return {p: c for p, c in n.items() if target(p) and c < MIN_CHARS * 0.9 and p not in keep and p not in base}
