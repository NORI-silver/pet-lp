"""近畿（三重・滋賀・京都・大阪・兵庫・奈良・和歌山）の登録簿から見つけた施設を、各分野のデータに入れる。

元：tools/kinki_add.json（登録簿にある事業者のうち、公式サイトが開けて分野が分かったもの。
facts は公式サイトの文のまま、出どころ src と確認日つき）。
何度動かしても同じ結果（id がすでにあれば足さない。同じ公式サイトがあれば足さない）。
  python3 tools/kinki_add.py
"""
import json, os, re
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = {"hotels": "hotels.json", "trainers": "trainers.json", "sitters": "sitters.json",
         "groomers": "grooming.json", "homes": "rojin.json"}
# 同じホストに複数の店があるチェーン・ホームページの貸し出し先（店ごとのURLでくらべる）
SHARED = {"kowapets.co.jp", "aeonpet.com", "petmaruesu.com", "ahb.jpn.com", "petplus-trimming.com", "canup.dog",
          "aikensalon.com", "eonet.ne.jp", "big-advance.site", "r.goope.jp", "site.everyone-web.com", "my.canva.site"}


def host(u):
    return urlparse(u).netloc.lower().replace("www.", "")


def key(u):
    h = host(u)
    return (h + urlparse(u).path.rstrip("/")) if any(h.endswith(s) for s in SHARED) else h


def removed():
    try:
        d = json.load(open(os.path.join(HERE, "delisted.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    L = d.get("removed", []) if isinstance(d, dict) else d
    return {key(x.get("url", "")) for x in L if isinstance(x, dict) and x.get("url")} | \
           {x.get("id") for x in L if isinstance(x, dict) and x.get("id")}


def main():
    add = json.load(open(os.path.join(HERE, "kinki_add.json"), encoding="utf-8"))
    gone = removed()
    for k, fn in FILES.items():
        path = os.path.join(HERE, fn)
        d = json.load(open(path, encoding="utf-8"))
        L = d[k]
        ids = {r["id"] for r in L}
        keys = {key(r.get("url", "")) for r in L}
        names = {re.sub(r"\s", "", r["name"]) for r in L}
        n = 0
        for x in add.get(k, []):
            if x["id"] in ids and x["id"] not in gone:  # 近畿で入れた行は、新しい読み取りで置きかえる
                i = next(j for j, r in enumerate(L) if r["id"] == x["id"])
                if L[i] != x: L[i] = x; n += 1
                continue
            if x["id"] in ids or x["id"] in gone or key(x["url"]) in keys or key(x["url"]) in gone \
                    or re.sub(r"\s", "", x["name"]) in names:
                continue
            L.append(x); ids.add(x["id"]); keys.add(key(x["url"])); n += 1
        if n:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
        print(fn, "+", n)
    # お店で施術するトリミングサロン（Nori 11/23「載せる」）。grooming.json の groomers に "shop": true で入れる（千葉 #682 と同じ形）。
    # /trimming/ がお店の印を分けて出せるようになってから入れる（gen_grooming.py に _has_shop があるとき）。
    if "_has_shop" in open(os.path.join(HERE, "gen_grooming.py"), encoding="utf-8").read():
        path = os.path.join(HERE, "grooming.json")
        d = json.load(open(path, encoding="utf-8"))
        L = d["groomers"]
        ids = {r["id"] for r in L}
        keys = {key(r.get("url", "")) for r in L}
        names = {re.sub(r"\s", "", r["name"]) for r in L}
        n = 0
        for x in add.get("salons", []):
            if x["id"] in ids and x["id"] not in gone:  # 近畿で入れた行は、新しい読み取りで置きかえる
                i = next(j for j, r in enumerate(L) if r["id"] == x["id"])
                if L[i] != x: L[i] = x; n += 1
                continue
            if x["id"] in ids or x["id"] in gone or key(x["url"]) in keys or key(x["url"]) in gone \
                    or re.sub(r"\s", "", x["name"]) in names:
                continue
            L.append(x); ids.add(x["id"]); keys.add(key(x["url"])); n += 1
        if n:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
        print("grooming.json（サロン）+", n)
    else:
        print("サロン", len(add.get("salons", [])), "件は /trimming/ のお店の印ができてから入れる")


if __name__ == "__main__":
    main()
