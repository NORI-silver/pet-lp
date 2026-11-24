"""写真のカードの部品（tools/cardphoto.py）を作りなおす。cp-css を持つページだけ、今の photos.json で入れなおす。"""
import glob, re, sys
sys.path.insert(0, "tools")
import cardphoto as C
by_id, by_url = C.load()

def strip(h):
    h = re.sub(r'<style id="cp-css">.*?</style>', "", h, flags=re.S)
    while True:
        m = re.search(r'<div class="cs-ph[ "]', h)
        if not m: break
        h = h[:m.start()] + h[C._end(h, m.start()):]
    return h

n = 0
for f in glob.glob("**/index.html", recursive=True):
    if "/" not in f or f.split("/")[0] in C.SKIP_DIRS: continue
    t = open(f, encoding="utf-8").read()
    if "cp-css" not in t: continue
    h, _ = C.page(strip(t), by_id, by_url, f.split("/")[0])
    if h != t: open(f, "w", encoding="utf-8").write(h); n += 1
print("pages rewritten:", n)
