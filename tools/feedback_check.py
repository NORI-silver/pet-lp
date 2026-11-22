#!/usr/bin/env python3
"""[G] Nori さんの指摘の台帳（docs/ai/feedback.json）の点検（Nori 2026-11-22「同じような指摘を今後なくしたい」）。

使い方:
  python3 tools/feedback_check.py .          → 止めるしくみ（check）のない指摘・存在しないしくみの名前があれば終了コード1（PRごと）
  python3 tools/feedback_check.py . --report → 2回目の指摘の数と、批判役の確認項目の一覧（月曜の見回り用）
指摘を受けたら、ページを直すだけでなく台帳に1行足し、止めるしくみ（rules_check などの記号か、批判役の目線）を必ず書く。
"""
import json, os, re, sys, collections

LENSES = {"persona", "business", "seo", "partner"}

def codes(root):
    rc = open(os.path.join(root, "tools/rules_check.py"), encoding="utf-8").read()
    pc = open(os.path.join(root, "tools/phone_check.cjs"), encoding="utf-8").read()
    sc = open(os.path.join(root, "tools/seo_check.py"), encoding="utf-8").read()
    return {
        "rules": set(re.findall(r'found\.append\(\("(\w+)"', rc)),
        "phone": set(re.findall(r"['\"](\w+)['\"]", pc)),
        "seo": set(re.findall(r"\b([A-Za-z_]\w*)\b", sc)),
    }

def problems(root, items):
    c = codes(root); out = []; ids = {i.get("id") for i in items}
    for i in items:
        ch = (i.get("check") or "").strip(); iid = i.get("id", "?")
        for k in ("id", "date", "quote", "pattern"):
            if not i.get(k): out.append(f"{iid}: {k} がない")
        if not ch: out.append(f"{iid}: 止めるしくみ（check）がない「{i.get('pattern','')}」"); continue
        kind, _, name = ch.partition(":")
        if kind in ("draft", "consistency") and not name:
            if not os.path.exists(os.path.join(root, f"tools/{kind}_check.py")): out.append(f"{iid}: tools/{kind}_check.py がない")
        elif kind == "critic":
            if name not in LENSES: out.append(f"{iid}: 批判役の目線は {sorted(LENSES)} のどれか（{ch}）")
        elif kind in c:
            if name not in c[kind]: out.append(f"{iid}: {kind} に「{name}」というしくみがない")
        else: out.append(f"{iid}: check の形がちがう（{ch}）")
        if i.get("repeat_of") and i["repeat_of"] not in ids: out.append(f"{iid}: repeat_of の {i['repeat_of']} がない")
    dup = [k for k, n in collections.Counter(i.get("id") for i in items).items() if n > 1]
    if dup: out.append(f"同じ id がある：{dup}")
    return out

def main():
    root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
    items = json.load(open(os.path.join(root, "docs/ai/feedback.json"), encoding="utf-8"))["items"]
    if "--report" in sys.argv:
        rep = [i for i in items if i.get("repeat_of")]
        print(f"指摘 {len(items)}件・2回目の指摘 {len(rep)}件")
        for i in rep: print(f"  2回目: {i['date']} {i['pattern']}（前は {i['repeat_of']}）")
        print("批判役の確認項目:")
        for lens in sorted(LENSES):
            for i in items:
                if i.get("check") == f"critic:{lens}": print(f"  [{lens}] {i['pattern']}")
        return 0
    bad = problems(root, items)
    for b in bad: print("NG:", b)
    print(f"指摘 {len(items)}件を確認。NG {len(bad)}件")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
