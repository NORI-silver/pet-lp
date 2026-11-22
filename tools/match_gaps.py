"""[E] マッチングの穴の表（Nori 2026-11-22「エッジケースも含めて、全部の分野でマッチングの精度を上げたい」）。

施設の分野ごとに、飼い主さんが選ぶ「うちの子のこと」（ownerfit.CAT_WHO など）が、
データ（公式サイトの文）から 合う／合わない／分からない の何件に決まるかを数え、分からない割合の大きい順に出す。
分からない割合が大きい項目から、公式サイトを読み直す → だめなら事業者に聞く（pet-db docs/provider-questions.md の形）。
使い方：python3 tools/match_gaps.py   （何も送らない・何も書きかえない）
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ownerfit as o

NAME = {"pet-hotel": "ペットホテル", "pet-sitter": "シッター", "trimming": "トリミング", "dog-trainer": "しつけ",
        "rojin-home": "老犬ホーム", "sougi": "葬儀・火葬"}
LABEL = dict(o.WHO, **o.WHEN, **{"a:small": "うさぎ・小動物", "a:bird": "鳥", "a:exotic": "爬虫類"})

def rows():
    out = []
    for cat, (f, k) in o.FILES.items():
        data = json.load(open(os.path.join(o.HERE, f), encoding="utf-8"))[k]
        ks = list(o.CAT_WHO[cat]) + (["a:small", "a:bird", "a:exotic"] if cat in ("sougi", "pet-sitter") else []) \
             + (list(o.WHEN) if cat == "sougi" else [])
        c = {x: [0, 0] for x in ks}; n = 0
        for r in data:
            u = r.get("url") or r.get("u")
            if not u: continue
            n += 1
            y, no = o.keys(cat, u)
            for x in ks:
                if x in y: c[x][0] += 1
                elif x in no: c[x][1] += 1
        for x, (a, b) in c.items():
            out.append((cat, x, n, a, b, n - a - b))
    return out

if __name__ == "__main__":
    rs = sorted(rows(), key=lambda r: -r[5] / max(r[2], 1))
    print("| 分野 | うちの子のこと | 件数 | 合う | 合わない | 分からない |")
    print("|---|---|---:|---:|---:|---:|")
    for cat, x, n, a, b, u in rs:
        print(f"| {NAME[cat]} | {LABEL.get(x, x)} | {n} | {a} | {b} | {u}（{round(100*u/max(n,1))}%） |")
