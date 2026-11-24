"""手で選んだ写真だけを、決めた URL から取りなおして img/fac/ に置く（候補の自動集めではない）。
使い方: python3 tools/fetch_curated.py tools/curated_trainer_chiba.json
縮め方は tools/photo_harvest.py の候補作りと同じ（長辺900px・webp・切らない）。縦横比が photos.json の ratio とずれたら置かずに失敗にする。"""
import io, json, os, sys, hashlib, time
sys.path.insert(0, os.path.dirname(__file__))
import photo_harvest as H
from PIL import Image

man = json.load(open(sys.argv[1], encoding="utf-8"))
ratio = {}
for x in json.load(open(os.path.join(os.path.dirname(__file__), "photos.json"), encoding="utf-8"))["items"]:
    for p, r in zip(x.get("photos", []), x.get("ratio", [])): ratio[p.lstrip("/")] = r
ok = bad = cached = fetched = 0
def cache_ok(m):
    """すでに置いてある画像（前のビルドで取って検査ずみ）が、一覧の sha256 と同じで、開けて、縦横比もずれないときだけ、取りなおさない。"""
    f = m["file"]
    if not os.path.exists(f): return False
    raw = open(f, "rb").read()
    if hashlib.sha256(raw).hexdigest() != m["sha256"]: return False
    try:
        im = Image.open(io.BytesIO(raw)); im.load()
    except Exception: return False
    want = ratio.get(f)
    return not (want and abs(im.width / im.height - want) > 0.02)
for i, m in enumerate(man):
    if i % 200 == 0: print(f"progress {i}/{len(man)} ok={ok} fail={bad} cached={cached} fetched={fetched}", flush=True)
    if not m.get("manual") and cache_ok(m):
        ok += 1; cached += 1; continue
    if m.get("manual") and os.path.exists(m["file"]):
        if hashlib.sha256(open(m["file"], "rb").read()).hexdigest() != m["sha256"]: print("FAIL", m["id"], "置いた画像が一覧の sha256 とちがう"); bad += 1
        else: ok += 1
        continue
    try:
        for n in range(6):  # 一時的な通信の失敗だけ、間をあけて取りなおす（画像の検査はそのまま）
            try: raw, _ = H.get(m["src"], timeout=40, binary=True); break
            except OSError as e:
                if n == 5 or (getattr(e, "code", 0) in (400, 401, 403, 404, 410, 451)): raise  # 取れないと返事された URL は、くりかえさない
                time.sleep(3 * (n + 1))
        im = Image.open(io.BytesIO(raw)); im.load(); im = im.convert("RGB")
        s = min(1.0, 900 / max(im.size)); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        r = im.width / im.height
        want = ratio.get(m["file"])
        if want and abs(r - want) > 0.02: raise ValueError(f"縦横比 {r:.3f} が想定 {want} とちがう")
        b = io.BytesIO(); im.save(b, "WEBP", quality=70, method=6)
        os.makedirs(os.path.dirname(m["file"]), exist_ok=True)
        open(m["file"], "wb").write(b.getvalue()); ok += 1; fetched += 1
        if hashlib.sha256(b.getvalue()).hexdigest() != m["sha256"]: print("same-image, different bytes:", m["file"])
    except Exception as e:
        bad += 1; print("FAIL", m["id"], m["file"], e)
print(f"ok {ok} / fail {bad} (cached {cached} / fetched {fetched})")
sys.exit(1 if bad else 0)
