#!/usr/bin/env python3
"""Xの投稿を、サイトの施設データ（県ごとの事実）から作って sns/posts.json に足す。

[B] SNS。2026-11-09 Nori「遅い。倍のスピードで進めて」→ 戦略担当「Xを毎日に。ネタはサイトの施設データから。リンクは貼らない」。
- 元データ：tools/dogrun.json（ドッグラン）・tools/emergency.json の hospitals（夜間・救急の動物病院）。
  公式サイトで確かめて載せている事実だけを、短く書き写す（数字を作らない・順位をつけない・電話番号なし）。
- すでに posts.json にある投稿（同じ key）は作り直さない。番号は続きから。
- 文の決まり（schedule_x.py の BAN と長さ280）に合わないものは、項目を減らすか、作らない。

使い方: python3 sns/gen_facts.py [--dry]
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from schedule_x import BAN  # noqa: E402

# 人の多い県から順に（だいたいの順。県ごとに交互に出す）
ORDER = ["東京都", "神奈川県", "大阪府", "愛知県", "埼玉県", "千葉県", "兵庫県", "北海道", "福岡県", "静岡県",
         "茨城県", "広島県", "京都府", "宮城県", "新潟県", "長野県", "岐阜県", "栃木県", "群馬県", "岡山県",
         "三重県", "熊本県", "鹿児島県", "沖縄県", "滋賀県", "山口県", "愛媛県", "奈良県", "長崎県", "青森県",
         "岩手県", "石川県", "大分県", "宮崎県", "山形県", "富山県", "秋田県", "香川県", "和歌山県", "山梨県",
         "佐賀県", "福井県", "徳島県", "高知県", "島根県", "鳥取県", "福島県"]
DOG_PHOTOS = ["img/dog.jpg", "img/guide/large-dog.jpg", "img/guide/new-family.jpg", "img/guide/multi-pet.jpg"]
NIGHT_PHOTOS = ["img/guide/hospital.jpg", "img/senior.jpg"]


def width(s):
    return sum(1 if ord(c) < 0x1100 else 2 for c in s)


def first(s, n=40):
    """最初の文だけ。長ければ読点で切る。"""
    s = (s or "").split("。")[0].strip()
    return s if len(s) <= n else ""  # 途中で切ると意味が変わるので、長いものは出さない


def ok(s):
    return not any(w in s for w in BAN)


def tagname(pref):
    return pref if pref == "北海道" else pref[:-1]


def fit(head, lines, foot):
    """280に収まるまで、うしろの行から減らす。"""
    lines = [l for l in lines if l and ok(l)]
    while lines:
        t = "\n".join([head, *lines, foot])
        if width(t) <= 280:
            return t
        lines = lines[:-1]
    return None


def dog_post(r):
    kind = r.get("kind") or "公営"
    head = f"【{r['pref']}のドッグラン】\n{r['name']}（{r['city']}）"
    lines = []
    if kind == "高速道路":
        lines.append(f"・{first(r.get('place'), 34)}")
    if r.get("fee"):
        lines.append(f"・料金：{first(r['fee'], 24)}")
    if r.get("hours"):
        lines.append(f"・時間：{first(r['hours'], 26)}")
    if r.get("size"):
        lines.append(f"・エリア：{first(r['size'], 34)}")
    if r.get("limit"):
        lines.append(f"・頭数：{first(r['limit'], 20)}")
    if "登録" in (r.get("reg") or "")[:12]:
        lines.append(f"・登録：{first(r['reg'], 30)}")
    lines = [l for l in lines if not l.endswith("：") and l != "・"]
    foot = f"決まりは変わることがあるので、行く前に公式ページで確かめてください。\n#ドッグラン #{tagname(r['pref'])}"
    return fit(head, lines, foot)


def hours_text(h):
    return (h or "").replace("24時間", "終日")


def night_post(pref, hs):
    # 所在地に（◯◯県）と付いているのは、近くの県の病院
    own = [h for h in hs if not re.search(r"（[^（）]{2,3}[都道府県]）$", h.get("city", ""))]
    if own:
        head = f"【{pref}の夜間・救急の動物病院】"
        lines = [f"・{h['name']}／{h['city']}／{first(hours_text(h.get('hours')), 24)}" for h in own[:3]]
    else:
        head = (f"【{pref}の夜間・救急の動物病院】\n{pref}の中では、確かめられた夜間の病院がまだありません。近くでは：")
        lines = [f"・{h['name']}／{h['city']}／{first(hours_text(h.get('hours')), 24)}" for h in sorted(hs, key=lambda h: len(h['name']))[:2]]
    foot = "行く前に、病院へ電話して受診できるか確かめてください。\n#動物病院 #夜間救急"
    return fit(head, lines, foot)


def main():
    dry = "--dry" in sys.argv
    pj = os.path.join(HERE, "posts.json")
    data = json.load(open(pj, encoding="utf-8"))
    posts = data["posts"]
    have = {p.get("key") for p in posts}
    no = max(p["no"] for p in posts)

    dogs = json.load(open(os.path.join(ROOT, "tools/dogrun.json"), encoding="utf-8"))["dogruns"]
    night = json.load(open(os.path.join(ROOT, "tools/emergency.json"), encoding="utf-8"))["hospitals"]

    # 県ごとのドッグランの列（公営→高速道路→民間の順）
    rank = {"公営": 0, None: 0, "高速道路": 1, "民間": 2}
    bypref = {}
    for r in sorted(dogs, key=lambda r: rank.get(r.get("kind"), 3)):
        bypref.setdefault(r["pref"], []).append(r)

    new, skipped = [], []
    dog_round = 0
    prefs_night = [p for p in ORDER if p in night]
    ni = 0
    # 夜間の病院1本 → ドッグラン2本 の順で、人の多い県から回す
    while ni < len(prefs_night) or any(bypref.values()):
        if ni < len(prefs_night):
            p = prefs_night[ni]; ni += 1
            key = f"night:{p}"
            if key not in have:
                t = night_post(p, night[p])
                (new if t else skipped).append({"key": key, "x": t, "tag": f"夜間の病院・{p}", "photo": NIGHT_PHOTOS[ni % 2]} if t else key)
        for _ in range(2):
            p = next((q for q in ORDER[dog_round:] + ORDER[:dog_round] if bypref.get(q)), None)
            if not p:
                break
            dog_round = (ORDER.index(p) + 1) % len(ORDER)
            r = bypref[p].pop(0)
            key = f"dogrun:{r['id']}"
            if key in have:
                continue
            t = dog_post(r)
            if t:
                new.append({"key": key, "x": t, "tag": f"ドッグラン・{p}", "photo": DOG_PHOTOS[len(new) % len(DOG_PHOTOS)]})
            else:
                skipped.append(key)

    for p in new:
        no += 1
        p["no"] = no
        p["alt"] = "犬の写真" if p["key"].startswith("dogrun") else "動物病院のイメージ写真"
        p["head"] = p["tag"]
    print(f"足す投稿 {len(new)}・作れなかった {len(skipped)}: {skipped[:10]}")
    if dry:
        for p in new[:6]:
            print("----", p["no"], width(p["x"]), "\n" + p["x"])
        return 0
    posts.extend(new)
    json.dump(data, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(pj, "a", encoding="utf-8").write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
