# [C] 2026-11-14 Nori「そもそも薄い記事作らないで」：病院1院のページ（/hospital/night/<県>/<id>/）のうち、
# そのページだけの字数（本文を文に分け、サイトの3ページ以上に出る文を除いた字数。薄いページの測り方と同じ）が900字に満たないものを
# tools/hosp_fold.json に書く。gen_facpages.py はそこに載った病院のページを作らず、県のページへ移す。
# 使い方：python3 tools/gen_areas.py . → python3 tools/thin_hosp.py . → もう一度 gen_areas.py（病院の facts を足したら毎回）。
import glob, json, os, re, sys, collections
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
MIN = 900
def sents(p):
    h = open(p, encoding="utf-8").read()
    if 'http-equiv="refresh"' in h: return None
    m = re.search(r"<main.*?</main>", h, re.S); h = m.group(0) if m else h
    h = re.sub(r"<(script|style|nav|footer|form)[^>]*>.*?</\1>", "", h, flags=re.S)
    return [s.strip() for s in re.split(r"[。\n]", re.sub(r"<[^>]+>", "\n", h)) if len(s.strip()) > 3]
S = {}
for f in glob.glob(os.path.join(ROOT, "**/index.html"), recursive=True):
    v = sents(f)
    if v is not None: S[f] = v
c = collections.Counter(s for v in S.values() for s in set(v))
fp = os.path.join(ROOT, "tools", "hosp_fold.json")
fold = set(json.load(open(fp))["ids"]) if os.path.exists(fp) else set()
for f, v in S.items():
    m = re.search(r"hospital/night/[^/]+/(h\d+)/index\.html$", f)
    if m and sum(len(s) for s in set(v) if c[s] < 3) < MIN: fold.add(m.group(1).upper())
json.dump({"_説明": "そのページだけの字数が900字に満たず、1院のページを作らない夜間の病院（tools/thin_hosp.py が書く）。facts を足して濃くなったら、ここから消して gen_areas.py を実行し直す。", "ids": sorted(fold)},
          open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("fold", len(fold))
