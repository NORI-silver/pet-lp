# photos.json で ratio が空の写真に、写真ファイルから縦横比を入れる（枠を写真の比率にして余白をなくすため）。
import json, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
p = os.path.join(HERE, "photos.json")
d = json.load(open(p, encoding="utf-8")); n = 0
for it in d["items"]:
    if it.get("ratio") or not it.get("photos"): continue
    rs = []
    for ph in it["photos"]:
        f = os.path.join(ROOT, ph.lstrip("/"))
        if not os.path.exists(f): rs = []; break
        im = Image.open(f); rs.append(round(im.width / im.height, 3))
    if rs: it["ratio"] = rs; n += 1
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ratio filled", n)
