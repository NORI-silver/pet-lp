"""[E] 施設の並び順：情報が多い施設を先に出す（Nori 2026-11-25「内容、情報が多いものは上位に表示」）。

生成（gen_areas.py）が各分野の生成器を読み込む前に、施設データの配列を「情報の多さ」で並び替える。
点数は、その施設について公式サイトなどから集めた情報だけから作る：
  写真の枚数（最大3枚まで）／ facts の数（最大10件まで）／ 料金が数字で分かる ／ 公式サイトの有無 ／
  説明文の量 ／ 病院・ドッグランなどで埋まっている項目の数。
お金・提携の有無は使わない（/about/ の「お金で並び順は変わりません」のまま）。
並び替えは安定ソートで、同点なら今の順番を保つ。順番が変わるファイルだけ書き戻す。
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

FILES = [
    ("trainers.json", ["trainers"]),
    ("sitters.json", ["sitters"]),
    ("grooming.json", ["groomers"]),
    ("hotels.json", ["hotels"]),
    ("rojin.json", ["homes"]),
    ("hospitals.json", ["visit", "cat", "exotic", "large"]),
    ("vet_clinics.json", ["clinics"]),
    ("joto.json", ["centers"]),
    ("dogrun.json", ["dogruns"]),
    ("sougi_facilities.json", None),  # 中身のリストは _lists() が探す
]

_PRESENCE = ("hours", "pay", "addr", "fee", "parking", "access", "reg", "limit")


def _photos():
    try:
        items = json.load(open(os.path.join(HERE, "photos.json"), encoding="utf-8"))["items"]
    except Exception:
        return {}
    out = {}
    for it in items:
        n = len(it.get("photos") or [])
        for k in (it.get("id"), it.get("name")):
            if k:
                out[k] = max(out.get(k, 0), n)
    return out


def _txt(v):
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "".join(_txt(x) for x in v)
    if isinstance(v, dict):
        return "".join(_txt(x) for x in v.values())
    return ""


def _score(r, ph):
    s = 0
    s += min(ph.get(r.get("id"), 0) or ph.get(r.get("name"), 0), 3) * 3
    facts = [f for f in (r.get("facts") or []) if isinstance(f, dict)]
    s += min(len(facts), 10)
    if any(f.get("k") == "料金" and f.get("yen") for f in facts):
        s += 2
    if r.get("url"):
        s += 2
    txt = _txt(r.get("services")) + _txt(r.get("animals")) + _txt(r.get("area"))
    s += min(len(txt) // 60, 3)
    s += sum(1 for k in _PRESENCE if r.get(k))
    if r.get("links"):
        s += min(len(r["links"]), 3)
    if r.get("conds"):
        s += min(len(r["conds"]), 3)
    return s


def _sorted(rows, ph):
    return [r for _, r in sorted(enumerate(rows), key=lambda x: (-_score(x[1], ph), x[0]))]


def _lists(d):
    if isinstance(d, list):
        return [None]
    return [k for k, v in d.items() if isinstance(v, list) and v and isinstance(v[0], dict)]


def sort_all():
    ph = _photos()
    changed = []
    for fn, keys in FILES:
        p = os.path.join(HERE, fn)
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        dirty = False
        for k in (keys if keys is not None else _lists(d)):
            rows = d if k is None else d.get(k)
            if not rows:
                continue
            new = _sorted(rows, ph)
            if new != rows:
                if k is None:
                    d = new
                else:
                    d[k] = new
                dirty = True
        if dirty:
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            changed.append(fn)
    return changed


if __name__ == "__main__":
    print(sort_all())
