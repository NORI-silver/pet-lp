#!/usr/bin/env python3
"""SNS の投稿に合う写真の候補を集める（GitHub Actions の sns-photos で動かす）。

[B] SNS。2026-11-15 Nori「写真か動画は絶対いれて」。サイトの写真の使い回しはしない。
- posts.json の photo_q（英語のことば）で、無料で使える写真（CC0・パブリックドメイン）を Openverse の公開APIからさがす。
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


def main():
    os.makedirs(OUT, exist_ok=True)
    posts = json.load(open(os.path.join(HERE, "posts.json"), encoding="utf-8"))["posts"]
    only = set(sys.argv[1:])
    todo = [p for p in posts if p.get("photo_q") and (p["key"].split(":", 1)[1] in only if only else not p.get("photo"))]
    rows = []
    for p in todo:
        name = p["key"].split(":", 1)[1]
        q = urllib.parse.urlencode({"q": p["photo_q"], "license": "cc0,pdm", "category": "photograph",
                                    "size": "large", "page_size": 12, "mature": "false"})
        try:
            res = json.loads(get(f"{API}?{q}"))["results"]
        except Exception as e:  # noqa: BLE001
            print(name, "さがせませんでした", e)
            res = []
        got, info = [], []
        for r in res:
            if len(got) >= 6:
                break
            try:
                im = Image.open(io.BytesIO(get(r["url"]))).convert("RGB")
            except Exception:  # noqa: BLE001
                continue
            if min(im.size) < 600:
                continue
            im.thumbnail((1080, 1080))
            n = len(got)
            im.save(os.path.join(OUT, f"{name}_{n}.jpg"), quality=86)
            got.append(im)
            info.append({"n": n, "title": r.get("title"), "creator": r.get("creator"), "license": r.get("license"),
                         "landing": r.get("foreign_landing_url"), "url": r.get("url"), "source": r.get("source")})
            time.sleep(0.5)
        json.dump(info, open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(name, len(got))
        rows.append((name, got))
        time.sleep(2)
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
