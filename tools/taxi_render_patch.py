# ペットタクシー候補カードの写真を、枠の黒い/灰色の余白なしで全体表示にする。
# 1) CO_PH（会社ID→写真）を photos.json から作りなおす（gen_areas.py と同じ作り）
# 2) 写真の枠を固定の3:2にしていたCSSをやめ、写真そのものの縦横比で出す
import json, os, re, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import cardphoto
from display_companies import PUBLIC_PAUSES
hidden = set(PUBLIC_PAUSES) | set(PUBLIC_PAUSES.values())
m = {k: v for k, v in cardphoto.taxi_map().items() if k not in hidden}
ADD = {"Dcfbfbf2", "De3f35f2", "E05"}  # この枠で新しく写真を足す会社（既存の項目は触らない）
def new_map_for(old_json):
    d = json.loads(old_json)
    for k in ADD:
        if k in m: d[k] = m[k]
    return "/*CO_PH*/var CO_PH = " + json.dumps(d, ensure_ascii=False) + ";/*/CO_PH*/"
OLD = "partner-photos img{flex:0 0 100%;width:100%;aspect-ratio:3/2;object-fit:contain;scroll-snap-align:start;border-radius:12px;background:#f3eee8}"
NEW = "partner-photos{align-items:flex-start;overflow-y:hidden}.partner-photos img{flex:0 0 100%;width:100%;height:auto;object-fit:contain;scroll-snap-align:start;border-radius:12px}"
JS_OLD = 'ph.appendChild(im); });'
JS_NEW = ('ph.appendChild(im); });'
          ' (function(){ var fit = function(){ var ims = ph.querySelectorAll("img"), k = Math.round(ph.scrollLeft / (ph.clientWidth || 1)), m = ims[k]; if (m && m.clientHeight) ph.style.height = m.clientHeight + "px"; };'
          ' ph.addEventListener("scroll", fit, {passive: true}); ph.querySelectorAll("img").forEach(function(m){ m.addEventListener("load", fit); }); window.addEventListener("resize", fit); })();')
pat = re.compile(r"/\*CO_PH\*/var CO_PH = (.*?);/\*/CO_PH\*/", re.S)
nh = nc = 0
files = [os.path.join(r, f) for r, _, fs in os.walk(ROOT) if '/.git' not in r and '/node_modules' not in r for f in fs if f.endswith((".html", ".css"))]
for f in files:
    t = open(f, encoding="utf-8").read(); u = t
    if "CO_PH*/" in u: u = pat.sub(lambda mo: new_map_for(mo.group(1)), u, count=1)
    u = u.replace(OLD, NEW)
    if JS_OLD in u and "var fit = function" not in u: u = u.replace(JS_OLD, JS_NEW, 1)
    if u != t:
        open(f, "w", encoding="utf-8").write(u); nh += 1
print("patched files", nh, "co_ph entries", len(m))
