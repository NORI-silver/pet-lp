#!/usr/bin/env python3
"""SNS の投稿に合う写真の候補を集める（GitHub Actions の sns-photos で動かす）。

[B] SNS。2026-11-15 Nori「写真か動画は絶対いれて」。サイトの写真の使い回しはしない。
- posts.json の photo_q（英語のことば）で、無料で使える写真をさがす：
  Unsplash（Unsplash ライセンス・有料の Unsplash+ は除く）→ Wikimedia Commons（CC0・パブリックドメインだけ）→ Openverse（CC0・パブリックドメイン）。
- 投稿ごとに候補を6枚まで、長い辺1080pxにして sns/cand/<名前>_<番号>.jpg に置き、出どころを sns/cand/<名前>.json に書く。
- 7投稿ずつ、候補を並べた一覧の画像（sns/cand/sheet<番号>.jpg）を作る。人かAIが見て、合う1枚を sns/img/<名前>.jpg にする。
- 何も投稿しない。

使い方: python3 sns/photos.py [名前 ...]
"""
import io, json, os, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "cand")
API = "https://api.openverse.org/v1/images/"
UA = {"User-Agent": "pet-kurashi-sns/1.0"}


def get(url, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as f:
        return f.read()


def unsplash(q):
    r = json.loads(get("https://unsplash.com/napi/search/photos?" + urllib.parse.urlencode({"query": q, "per_page": 15})))
    out = []
    for x in r.get("results", []):
        if x.get("premium") or x.get("plus") or "plus.unsplash.com" in (x.get("urls", {}).get("raw") or ""):
            continue
        out.append({"source": "unsplash", "license": "Unsplash License", "url": x["urls"]["raw"] + "&w=1080&q=85&fm=jpg",
                    "landing": x.get("links", {}).get("html"), "creator": (x.get("user") or {}).get("name"),
                    "title": x.get("alt_description")})
    return out


def commons(q):
    """Wikimedia Commons。CC0（Q6938433）かパブリックドメイン（P6216=Q19652）と書いてある写真だけ。"""
    out = []
    for flt in ("haswbstatement:P275=Q6938433", "haswbstatement:P6216=Q19652"):
        r = json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 10,
            "gsrsearch": f"{q} filetype:bitmap {flt}", "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1080})))
        for pg in (r.get("query") or {}).get("pages", {}).values():
            ii = (pg.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata") or {}
            out.append({"source": "commons", "license": (meta.get("LicenseShortName") or {}).get("value"),
                        "url": ii.get("thumburl") or ii.get("url"), "landing": ii.get("descriptionurl"),
                        "creator": (meta.get("Artist") or {}).get("value"), "title": pg.get("title")})
    return out


def openverse(q):
    r = json.loads(get(API + "?" + urllib.parse.urlencode({"q": q, "license": "cc0,pdm", "category": "photograph",
                                                            "page_size": 12, "mature": "false"}), timeout=60))
    return [{"source": "openverse", "license": x.get("license"), "url": x.get("url"), "landing": x.get("foreign_landing_url"),
             "creator": x.get("creator"), "title": x.get("title")} for x in r.get("results", [])]


def main():
    os.makedirs(OUT, exist_ok=True)
    posts = json.load(open(os.path.join(HERE, "posts.json"), encoding="utf-8"))["posts"]
    only = set(sys.argv[1:])
    todo = [p for p in posts if p.get("photo_q") and (p["key"].split(":", 1)[1] in only if only else not p.get("photo"))]
    rows = []
    for p in todo:
        name = p["key"].split(":", 1)[1]
        got, info = [], []
        for src in (unsplash, commons, openverse):
            if len(got) >= 6:
                break
            try:
                cands = src(p["photo_q"])
            except Exception as e:  # noqa: BLE001
                print(name, src.__name__, "さがせませんでした", e)
                continue
            for c in cands:
                if len(got) >= 6:
                    break
                try:
                    im = Image.open(io.BytesIO(get(c["url"]))).convert("RGB")
                except Exception:  # noqa: BLE001
                    continue
                if min(im.size) < 600:
                    continue
                im.thumbnail((1080, 1080))
                n = len(got)
                im.save(os.path.join(OUT, f"{name}_{n}.jpg"), quality=86)
                got.append(im)
                info.append({"n": n, **c})
                time.sleep(0.3)
        json.dump(info, open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(name, len(got))
        rows.append((name, got))
        time.sleep(1)
    # 一覧の画像（7投稿ずつ、1行に候補6枚）
    T = 220
    for s in range(0, len(rows), 7):
        part = rows[s:s + 7]
        sheet = Image.new("RGB", (40 + 6 * (T + 6), len(part) * (T + 30)), "white")
        d = ImageDraw.Draw(sheet)
        for i, (name, ims) in enumerate(part):
            y = i * (T + 30)
            d.text((4, y + 4), name, fill="black")
            for j, im in enumerate(ims):
                t = im.copy()
                t.thumbnail((T, T))
                x = 40 + j * (T + 6)
                sheet.paste(t, (x, y + 22))
                d.rectangle([x, y + 22, x + 22, y + 40], fill="black")
                d.text((x + 7, y + 25), str(j), fill="white")
        sheet.save(os.path.join(OUT, f"sheet{s // 7}.jpg"), quality=80)


if __name__ == "__main__":
    main()
