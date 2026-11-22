"""公式サイトに書いてある くわしい項目（more）を施設に足す。
使い方：python3 tools/sougi_enrich.py <enrich-*.json ...>
ファイルの形：[{"id": "S…", "more": [{"k": "体重ごとの料金（税込）", "v": "…"}], "services_add": [...], "checked": "2026-11-22"}]
同じキーがあれば置きかえ、ないキーは足す。電話番号・番地に見える値は止める。"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "sougi_facilities.json")
BAN = re.compile(r"0\d{1,4}-\d{1,4}-\d{3,4}|0120|手配|取り次|代理|公式サイトで確か|くらい|約\d")
SV = {"合同火葬", "個別火葬", "立ち会い火葬", "お迎え", "訪問火葬", "納骨"}
D = json.load(open(P, encoding="utf-8"))
ix = {f["id"]: f for f in D["facilities"]}
n = 0
for fn in sys.argv[1:]:
    for r in json.load(open(fn, encoding="utf-8")):
        f = ix.get(r["id"])
        if not f: print("no id", r["id"]); continue
        bad = [x for x in r.get("more", []) + [{"k": "price", "v": r.get("price") or ""}] if BAN.search(x["v"]) or BAN.search(x["k"])]
        if bad: print("NG", r["id"], bad); continue
        cur = {x["k"]: i for i, x in enumerate(f.setdefault("more", []))}
        for x in r.get("more", []):
            if x["k"] in cur: f["more"][cur[x["k"]]] = x
            else: f["more"].append(x)
        for s in r.get("services_add", []):
            if s in SV and s not in f["services"]: f["services"].append(s)
        if r.get("price") and not f.get("price"): f["price"] = r["price"]  # カードの料金の行（小型犬・猫の例）
        if r.get("checked"): f["checked"] = r["checked"]
        n += 1
open(P, "w", encoding="utf-8").write(json.dumps(D, ensure_ascii=False, indent=1) + "\n")
print("enriched", n)
