# [B] 分野ごとのキービジュアル（Nori 2026-11-16「各カテゴリでキービジュアルいれて」）。
# 写真は使い回さない・汎用のイメージ写真は使わない決まりなので、分野ごとに別の絵（インラインSVG、文字なし・JSなし・軽い）を描く。
# gen_areas.py の最後（portal.py のあと）に、分野の入口・県・市区町村のページの見出しの上へ入れる。記事・施設1件のページには入れない。
# 新しい分野を作ったら SCENES に足す。何度動かしても同じ結果（data-kv の印）。
import os, re

INK = "#3b2a20"

def dog(x, y, s=1.0, fur="#e9a86b", ear="#b8703a", flip=False):
    t = f'translate({x} {y}) scale({-s if flip else s} {s})'
    return (f'<g transform="{t}">'
            f'<ellipse cx="0" cy="34" rx="26" ry="18" fill="{fur}"/>'  # 体
            f'<rect x="10" y="30" width="9" height="22" rx="4.5" fill="{fur}"/><rect x="-18" y="32" width="9" height="20" rx="4.5" fill="{fur}"/>'
            f'<path d="M-24 30q-14-10-8-24" stroke="{fur}" stroke-width="7" fill="none" stroke-linecap="round"/>'  # しっぽ
            f'<circle cx="8" cy="4" r="20" fill="{fur}"/>'  # 顔
            f'<ellipse cx="-9" cy="2" rx="7" ry="13" fill="{ear}" transform="rotate(18 -9 2)"/><ellipse cx="25" cy="2" rx="7" ry="13" fill="{ear}" transform="rotate(-18 25 2)"/>'
            f'<ellipse cx="8" cy="13" rx="11" ry="8" fill="#fff4e8"/>'
            f'<circle cx="1" cy="2" r="2.6" fill="{INK}"/><circle cx="15" cy="2" r="2.6" fill="{INK}"/>'
            f'<ellipse cx="8" cy="10" rx="3.6" ry="2.6" fill="{INK}"/><path d="M5 15q3 3 6 0" stroke="{INK}" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
            f'<path d="M2 20l3 9h6l3-9z" fill="#ef6b4a" opacity=".0"/></g>')

def cat(x, y, s=1.0, fur="#9aa3ad", flip=False):
    t = f'translate({x} {y}) scale({-s if flip else s} {s})'
    return (f'<g transform="{t}">'
            f'<path d="M18 40q20 4 16-18" stroke="{fur}" stroke-width="6" fill="none" stroke-linecap="round"/>'
            f'<ellipse cx="0" cy="34" rx="18" ry="17" fill="{fur}"/>'
            f'<path d="M-17-2l3-20 12 12zM17-2l-3-20-12 12z" fill="{fur}"/>'
            f'<circle cx="0" cy="4" r="17" fill="{fur}"/>'
            f'<path d="M-13-6l2-11 7 7zM13-6l-2-11-7 7z" fill="#f2b8b0"/>'
            f'<ellipse cx="-6" cy="3" rx="2.4" ry="3.2" fill="{INK}"/><ellipse cx="6" cy="3" rx="2.4" ry="3.2" fill="{INK}"/>'
            f'<path d="M-2 9h4l-2 2.4z" fill="#e58a8a"/>'
            f'<path d="M-4 13q4 3 8 0M-9 10l-11-2M-9 12l-11 2M9 10l11-2M9 12l11 2" stroke="{INK}" stroke-width="1.2" fill="none" stroke-linecap="round"/></g>')

def paws(pts, c="#fff", o=".55"):
    out = ""
    for x, y, r in pts:
        out += (f'<g fill="{c}" opacity="{o}" transform="translate({x} {y}) rotate({r})"><ellipse cx="0" cy="3" rx="5" ry="4.2"/>'
                '<circle cx="-5" cy="-3.5" r="2"/><circle cx="-1.7" cy="-6" r="2"/><circle cx="1.7" cy="-6" r="2"/><circle cx="5" cy="-3.5" r="2"/></g>')
    return out

def heart(x, y, s=1, c="#ef6b6b"):
    return f'<path transform="translate({x} {y}) scale({s})" d="M0 6C-9-1-7-9 0-5c7-4 9 4 0 11z" fill="{c}"/>'

def house(x, y, w=70, h=50, wall="#fff", roof="#e8590c", door="#c98b5a"):
    return (f'<g transform="translate({x} {y})"><rect x="0" y="{h*0.35}" width="{w}" height="{h*0.65}" rx="4" fill="{wall}"/>'
            f'<path d="M-8 {h*0.4}L{w/2} 0L{w+8} {h*0.4}z" fill="{roof}"/>'
            f'<rect x="{w*0.4}" y="{h*0.62}" width="{w*0.2}" height="{h*0.38}" rx="2" fill="{door}"/>'
            f'<rect x="{w*0.1}" y="{h*0.55}" width="{w*0.18}" height="{h*0.16}" rx="2" fill="#bfe3f2"/><rect x="{w*0.72}" y="{h*0.55}" width="{w*0.18}" height="{h*0.16}" rx="2" fill="#bfe3f2"/></g>')

def tree(x, y, s=1):
    return (f'<g transform="translate({x} {y}) scale({s})"><rect x="-3" y="10" width="6" height="22" fill="#a26a3f"/>'
            '<circle cx="0" cy="4" r="16" fill="#6fbf73"/><circle cx="-10" cy="12" r="10" fill="#5cae62"/><circle cx="10" cy="12" r="10" fill="#5cae62"/></g>')

def sun(x, y, r=14, c="#ffd36b"):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'

def cloud(x, y, s=1, c="#fff"):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="{c}" opacity=".9"><ellipse cx="0" cy="0" rx="16" ry="9"/>'
            '<ellipse cx="12" cy="-5" rx="11" ry="9"/><ellipse cx="-12" cy="-2" rx="9" ry="7"/></g>')

def ground(c):
    return f'<path d="M0 118Q90 104 180 112T360 108V140H0z" fill="{c}"/>'

def bg(c1, c2):
    return (f'<defs><linearGradient id="kvg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            '<rect width="360" height="140" fill="url(#kvg)"/>')

def scene_hospital():
    return (bg("#e3f2fb", "#d4ecf7") + cloud(300, 26) + cloud(60, 22, .8) + ground("#c5e3f1")
            + '<g transform="translate(170 26)"><rect width="110" height="88" rx="6" fill="#fff"/><rect x="40" y="58" width="30" height="30" rx="3" fill="#8cc7e3"/>'
            '<rect x="12" y="20" width="22" height="16" rx="2" fill="#bfe3f2"/><rect x="76" y="20" width="22" height="16" rx="2" fill="#bfe3f2"/>'
            '<rect x="45" y="8" width="20" height="40" rx="3" fill="#3aa0d0"/><rect x="35" y="18" width="40" height="20" rx="3" fill="#3aa0d0"/>'
            '<rect x="49" y="12" width="12" height="32" rx="2" fill="#fff"/><rect x="39" y="22" width="32" height="12" rx="2" fill="#fff"/></g>'
            + dog(90, 72, .95) + cat(140, 80, .8) + heart(300, 70, 1.4, "#f58f8f"))

def scene_sitter():
    return (bg("#fff3e2", "#ffe6c7") + sun(320, 26) + ground("#f6d7ad") + house(196, 52, 96, 66, roof="#f08a4b")
            + dog(98, 72, .95) + cat(150, 80, .8, fur="#e7b77a")
            + '<g transform="translate(300 84)"><circle r="9" fill="none" stroke="#c98b2a" stroke-width="4"/><rect x="7" y="-2.5" width="24" height="5" rx="2" fill="#c98b2a"/><rect x="24" y="2" width="4" height="7" fill="#c98b2a"/></g>'
            + paws([(40, 110, -20), (24, 92, -10)], "#e8a35c", ".5"))

def scene_trimming():
    return (bg("#fde8ef", "#fbd9e6") + ground("#f6c7d9") + paws([(330, 30, 15), (300, 50, 20)], "#fff", ".7")
            + dog(150, 70, 1.05, fur="#f3dcc4", ear="#dcb48f")
            + '<g transform="translate(240 50) rotate(-25)"><circle cx="-8" cy="22" r="7" fill="none" stroke="#e05a8a" stroke-width="4"/><circle cx="8" cy="22" r="7" fill="none" stroke="#e05a8a" stroke-width="4"/>'
            '<path d="M-5 16L6 -22M5 16L-6 -22" stroke="#9aa3ad" stroke-width="4" stroke-linecap="round"/></g>'
            + '<g transform="translate(60 52)"><rect width="36" height="12" rx="3" fill="#f39bbd"/>' + "".join(f'<rect x="{3+i*5}" y="12" width="2.4" height="14" rx="1" fill="#f39bbd"/>' for i in range(7)) + '</g>'
            + '<g fill="#bfe3f2"><circle cx="210" cy="96" r="5"/><circle cx="222" cy="88" r="3.5"/><circle cx="96" cy="100" r="4"/></g>')

def scene_trainer():
    return (bg("#e8f6e9", "#d6efd8") + sun(40, 28, 13) + cloud(300, 24, .9) + ground("#bfe2c2") + tree(318, 70, 1.1)
            + dog(150, 70, 1.0) + '<circle cx="232" cy="106" r="11" fill="#ff7a59"/><path d="M222 102q10 6 20 0" stroke="#fff" stroke-width="2" fill="none"/>'
            + '<g transform="translate(70 60)"><rect x="-2" y="0" width="4" height="54" fill="#8a6a50"/><rect x="-14" y="54" width="28" height="4" rx="2" fill="#8a6a50"/>'
            '<path d="M2 2h30l-6 8 6 8H2z" fill="#f4b400"/></g>'
            + '<path d="M196 54l6-10M206 58l10-6M190 50l-2-12" stroke="#f4b400" stroke-width="3" stroke-linecap="round"/>')

def scene_rojin():
    return (bg("#fff7e8", "#fbeacc") + sun(320, 28, 15, "#ffc76b") + ground("#f2dbb0") + house(40, 54, 90, 64, roof="#c98b5a")
            + dog(200, 76, .95, fur="#d9c3a5", ear="#a88b67") + cat(262, 84, .78, fur="#c7c1b8")
            + '<g transform="translate(150 92)"><rect x="-16" y="0" width="34" height="22" rx="8" fill="#f3a46b"/><rect x="-18" y="16" width="38" height="8" rx="4" fill="#e08a4f"/></g>'
            + heart(232, 40, 1.3, "#f58f8f") + heart(254, 30, .9, "#f8b1b1"))

def scene_dogrun():
    return (bg("#e2f4fb", "#d9f0e0") + sun(330, 24, 13) + cloud(80, 26) + ground("#a9dca9")
            + "".join(f'<rect x="{10+i*30}" y="86" width="5" height="30" rx="2" fill="#c9a27a"/>' for i in range(12))
            + '<rect x="0" y="92" width="360" height="4" fill="#c9a27a"/><rect x="0" y="104" width="360" height="4" fill="#c9a27a"/>'
            + tree(36, 64, .9) + dog(170, 66, 1.0) + dog(250, 74, .8, fur="#3b3b3b", ear="#222", flip=True)
            + '<circle cx="306" cy="108" r="8" fill="#ff7a59"/>' + '<path d="M120 60q10-14 20 0" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round"/>')

def scene_joto():
    return (bg("#fff0ea", "#ffe0d3") + ground("#f9cdb9") + house(222, 48, 92, 70, roof="#ef6b4a")
            + heart(268, 28, 2.4, "#ef6b4a") + dog(100, 72, .95) + cat(160, 80, .82, fur="#e7b77a")
            + '<g transform="translate(40 96)"><rect width="34" height="22" rx="4" fill="#c98b5a"/><path d="M0 6h34" stroke="#a26a3f" stroke-width="2"/></g>'
            + heart(60, 50, .9, "#f8b1b1") + heart(190, 36, 1, "#f8b1b1"))

def scene_jichitai():
    return (bg("#eef3ff", "#dfe8fb") + cloud(300, 22) + ground("#c9d6f2")
            + '<g transform="translate(250 30)"><rect x="-3" y="10" width="6" height="80" fill="#8a6a50"/>'
            '<path d="M-40 14h66l10 9-10 9h-66z" fill="#4c7ad9"/><path d="M40 42h-66l-10 9 10 9h66z" fill="#f08a4b"/></g>'
            + '<g transform="translate(70 40)"><path d="M0 50s-22-20-22-36a22 22 0 0 1 44 0C22 30 0 50 0 50z" fill="#ef6b4a"/><circle cy="14" r="8" fill="#fff"/></g>'
            + dog(150, 72, .95) + '<rect x="146" y="92" width="14" height="10" rx="2" fill="#f4b400"/>')

def scene_hinan():
    return (bg("#e9f1f7", "#d7e6f1") + ground("#c3d8e6")
            + "".join(f'<path d="M{x} {y}l-4 10" stroke="#8fb3d1" stroke-width="2" stroke-linecap="round"/>' for x, y in [(30, 20), (60, 40), (100, 16), (300, 30), (330, 52), (260, 14)])
            + '<g transform="translate(200 36)"><rect x="0" y="22" width="110" height="60" rx="5" fill="#fff"/><path d="M-10 26L55 0l65 26z" fill="#3a8f6f"/>'
            '<rect x="44" y="50" width="22" height="32" rx="2" fill="#7cc3a5"/><circle cx="55" cy="38" r="7" fill="#3a8f6f"/><path d="M51 38h8M55 34v8" stroke="#fff" stroke-width="2"/></g>'
            + '<g transform="translate(110 30)"><path d="M-40 26a40 26 0 0 1 80 0z" fill="#f08a4b"/><rect x="-1.5" y="26" width="3" height="40" fill="#8a6a50"/></g>'
            + dog(96, 76, .8) + cat(140, 84, .7))

def scene_sougi():
    arcs = "".join(f'<path d="M60 128a120 100 0 0 1 240 0" stroke="{c}" stroke-width="7" fill="none" transform="translate({0} {i*8}) scale(1)" opacity=".75"/>'
                   for i, c in enumerate(["#f4a3a3", "#f7c98b", "#f3e39b", "#a8dba8", "#a3c9f0", "#c3b0e8"]))
    return (bg("#f7f3fb", "#ece6f6") + arcs + cloud(56, 112, 1.2) + cloud(304, 112, 1.2)
            + '<g transform="translate(180 92)">' + "".join(f'<circle cx="{dx}" cy="{dy}" r="7" fill="{c}"/>' for dx, dy, c in [(-14, -6, "#f4a3a3"), (0, -12, "#fff"), (14, -6, "#f7c98b"), (-6, 4, "#c3b0e8"), (8, 4, "#f4a3a3")])
            + '<path d="M0 8v26M0 20l-8-6M0 24l8-6" stroke="#6fbf73" stroke-width="3" stroke-linecap="round"/></g>'
            + paws([(120, 50, -10), (240, 50, 10)], "#c3b0e8", ".7"))

def scene_hotel():
    return (bg("#eceaf8", "#dcd8f3") + '<circle cx="312" cy="30" r="14" fill="#ffe08a"/><circle cx="318" cy="25" r="12" fill="#dcd8f3"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="1.8" fill="#fff"/>' for x, y in [(40, 20), (90, 34), (150, 16), (220, 28), (270, 50)])
            + '<path d="M0 118H360V140H0z" fill="#c9c3ea"/>'
            + '<g transform="translate(120 74)"><rect x="0" y="16" width="130" height="26" rx="10" fill="#8f86d9"/><rect x="6" y="8" width="118" height="18" rx="9" fill="#fff"/>'
            '<rect x="0" y="0" width="12" height="44" rx="5" fill="#6f65c9"/><rect x="118" y="10" width="12" height="34" rx="5" fill="#6f65c9"/></g>'
            + cat(160, 62, .72, fur="#e7b77a") + dog(214, 56, .78, fur="#f3dcc4", ear="#dcb48f", flip=True)
            + '<text x="250" y="52" font-size="14" fill="#8f86d9" font-family="sans-serif" font-weight="700">z z</text>')

def scene_emergency():
    return (bg("#fdecec", "#fbdcdc") + ground("#f6c3c3")
            + '<g transform="translate(180 30)"><rect width="120" height="70" rx="12" fill="#fff"/><rect y="40" width="120" height="8" fill="#ef4f4f"/>'
            '<rect x="12" y="12" width="30" height="22" rx="3" fill="#bfe3f2"/><path d="M78 12h10v8h8v10h-8v8H78v-8h-8V20h8z" fill="#ef4f4f"/>'
            '<circle cx="28" cy="74" r="11" fill="#3b3b3b"/><circle cx="94" cy="74" r="11" fill="#3b3b3b"/><circle cx="28" cy="74" r="4" fill="#ccc"/><circle cx="94" cy="74" r="4" fill="#ccc"/>'
            '<rect x="48" y="-8" width="20" height="10" rx="3" fill="#ef4f4f"/></g>'
            + dog(90, 72, .95) + '<path d="M240 14l-6-8M250 12v-10M260 14l6-8" stroke="#ef4f4f" stroke-width="3" stroke-linecap="round"/>')

def scene_guide():
    return (bg("#fff4e6", "#ffe8cc") + ground("#f7d6a8")
            + '<g transform="translate(176 46)"><path d="M0 8q30-10 60 0v62q-30-10-60 0z" fill="#fff"/><path d="M60 8q30-10 60 0v62q-30-10-60 0z" fill="#fff6ea"/>'
            '<path d="M60 8v62" stroke="#e8a35c" stroke-width="2"/>' + "".join(f'<path d="M10 {22+i*10}h40M70 {22+i*10}h40" stroke="#f0c896" stroke-width="3" stroke-linecap="round"/>' for i in range(4)) + '</g>'
            + dog(96, 72, .95) + cat(146, 80, .78) + paws([(318, 30, 20), (336, 54, 25)], "#e8a35c", ".5"))

SCENES = {
    "hospital": scene_hospital, "emergency": scene_emergency, "pet-sitter": scene_sitter, "trimming": scene_trimming,
    "dog-trainer": scene_trainer, "rojin-home": scene_rojin, "dogrun": scene_dogrun, "joto": scene_joto,
    "jichitai": scene_jichitai, "hinan": scene_hinan, "sougi": scene_sougi, "pet-hotel": scene_hotel, "guide": scene_guide,
}

CSS = ('<style id="kv-css">.kv{display:block;width:100%;height:auto;max-height:150px;border-radius:16px;margin:0 0 12px;aspect-ratio:360/140}'
       '@media(min-width:760px){.kv{max-height:none;max-width:720px}}</style>')

def svg(cat):
    k = "kv" + re.sub(r"[^a-z]", "", cat)
    return (f'<svg class="kv" data-kv viewBox="0 0 360 140" role="img" aria-hidden="true" focusable="false" preserveAspectRatio="xMidYMid slice">'
            + SCENES[cat]().replace('id="kvg"', f'id="{k}"').replace("url(#kvg)", f"url(#{k})") + '</svg>')

def want(rel, h):
    """分野の入口・県・市区町村のページだけ（記事・施設1件のページ・移す案内は入れない）"""
    parts = rel.split("/")
    if parts[0] not in SCENES or "data-kv" in h or 'http-equiv="refresh"' in h: return False
    if parts[0] == "guide": return len(parts) == 1  # ガイドは一覧だけ（記事にはその記事の写真がある）
    if parts[0] == "hospital" and len(parts) >= 3 and parts[1] == "night": return False  # 夜間の病院1院のページ
    if len(parts) >= 3 and re.match(r"^(d\d|s[0-9a-f]|[a-z]?\d)", parts[-1] or ""): return False  # 施設1件のページ（id）
    return '<section class="area-hero"' in h

def page(h, cat):
    m = re.search(r'(<section class="area-hero"[^>]*>\s*<div class="wrap">)', h)
    if not m: return h
    h = h[:m.end()] + svg(cat) + h[m.end():]
    if 'id="kv-css"' not in h: h = h.replace("</head>", CSS + "</head>", 1)
    return h

def build(root):
    n = 0
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root).replace(os.sep, "/")
        if rel == "." or rel.split("/")[0].startswith(".") or rel.split("/")[0] in ("tools", "img", "lib", "node_modules"): continue
        if "index.html" not in fn: continue
        f = os.path.join(dp, "index.html"); t = open(f, encoding="utf-8").read()
        if not want(rel, t): continue
        open(f, "w", encoding="utf-8").write(page(t, rel.split("/")[0])); n += 1
    return n

if __name__ == "__main__":
    import sys
    print("keyvisual", build(sys.argv[1] if len(sys.argv) > 1 else "."), "pages")
