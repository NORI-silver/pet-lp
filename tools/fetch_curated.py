"""手で選んだ写真だけを、決めた URL から取りなおして img/fac/ に置く（候補の自動集めではない）。
使い方: python3 tools/fetch_curated.py tools/curated_trainer_chiba.json
縮め方は tools/photo_harvest.py の候補作りと同じ（長辺900px・webp・切らない）。縦横比が photos.json の ratio とずれたら置かずに失敗にする。"""
import io, json, os, sys, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import photo_harvest as H
from PIL import Image

man = json.load(open(sys.argv[1], encoding="utf-8"))
ratio = {}
for x in json.load(open(os.path.join(os.path.dirname(__file__), "photos.json"), encoding="utf-8"))["items"]:
    for p, r in zip(x.get("photos", []), x.get("ratio", [])): ratio[p.lstrip("/")] = r
ok = bad = 0
for m in man:
    if m.get("manual") and os.path.exists(m["file"]):
        if hashlib.sha256(open(m["file"], "rb").read()).hexdigest() != m["sha256"]: print("FAIL", m["id"], "置いた画像が一覧の sha256 とちがう"); bad += 1
        else: ok += 1
        continue
    try:
        raw, _ = H.get(m["src"], binary=True)
        im = Image.open(io.BytesIO(raw)); im.load(); im = im.convert("RGB")
        s = min(1.0, 900 / max(im.size)); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        r = im.width / im.height
        want = ratio.get(m["file"])
        if want and abs(r - want) > 0.02: raise ValueError(f"縦横比 {r:.3f} が想定 {want} とちがう")
        b = io.BytesIO(); im.save(b, "WEBP", quality=70, method=6)
        os.makedirs(os.path.dirname(m["file"]), exist_ok=True)
        open(m["file"], "wb").write(b.getvalue()); ok += 1
        if hashlib.sha256(b.getvalue()).hexdigest() != m["sha256"]: print("same-image, different bytes:", m["file"])
    except Exception as e:
        bad += 1; print("FAIL", m["id"], m["file"], e)
print(f"ok {ok} / fail {bad}")
sys.exit(1 if bad else 0)
