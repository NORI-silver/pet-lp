# [B] 各カテゴリの入口にキービジュアル（Nori 2026-11-16「各カテゴリでキービジュアルいれて」）。
# トップのキービジュアル（角の丸い大きな絵＋白い小さな札）と同じ形を、分野ごとの自前の絵（SVG。写真・汎用の「イメージ」写真は使わない）で
# 各分野の入口のページの上に入れる。高さは控えめにして、さがす欄がスマホの最初の画面に入るようにする。
# h1 の下の長い説明文（スマホで「…」で切れていた）は、絵の上の短い札1行に置きかえる。
# gen_areas.py の最後に動く。何度動かしても同じ結果（data-kv の印で2回目はしない）。新しい分野を作ったら KV に足す。
import os, re

INK, OR, ORD, CREAM, PEACH = "#1c1a18", "#ff6a1a", "#e2560a", "#fff6ef", "#ffd2b3"
DOG, DOG_D, DOG_L, CAT, CAT_L = "#c98a52", "#8e5a2e", "#f1d3b3", "#8c867f", "#d9d3cc"
GREEN, GREEN_D = "#8fcf9f", "#5aa86e"


def dog(x, y, s=1.0, collar=None):
    """すわっている犬（頭の中心が x,y）"""
    c = (f'<path d="M-16 20h32" stroke="{collar}" stroke-width="5" stroke-linecap="round"/>'
         f'<path d="M0 22l-6 9h12z" fill="#ffd34d"/><circle cx="0" cy="29" r="5" fill="#ffd34d"/>') if collar else ""
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<path d="M20 56c16 2 22-14 15-24" stroke="{DOG}" stroke-width="7" fill="none" stroke-linecap="round"/>'
            f'<ellipse cx="0" cy="42" rx="25" ry="28" fill="{DOG}"/><ellipse cx="0" cy="46" rx="13" ry="17" fill="{DOG_L}"/>'
            f'<rect x="-16" y="54" width="11" height="18" rx="5.5" fill="{DOG}"/><rect x="5" y="54" width="11" height="18" rx="5.5" fill="{DOG}"/>'
            f'<circle cx="0" cy="0" r="23" fill="{DOG}"/>'
            f'<path d="M-18-14c-12-5-19 8-15 22 2 10 9 12 13 7z" fill="{DOG_D}"/><path d="M18-14c12-5 19 8 15 22-2 10-9 12-13 7z" fill="{DOG_D}"/>'
            f'<ellipse cx="0" cy="9" rx="12" ry="9" fill="{DOG_L}"/>'
            f'<circle cx="-9" cy="-3" r="3.2" fill="{INK}"/><circle cx="9" cy="-3" r="3.2" fill="{INK}"/>'
            f'<ellipse cx="0" cy="5" rx="4.5" ry="3.2" fill="{INK}"/>'
            f'<path d="M0 9v3m-5 1c3 3 7 3 10 0" stroke="{INK}" stroke-width="1.8" fill="none" stroke-linecap="round"/>{c}</g>')


def cat(x, y, s=1.0):
    """すわっている猫（頭の中心が x,y）"""
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<path d="M16 62c22 4 28-16 16-26" stroke="{CAT}" stroke-width="7" fill="none" stroke-linecap="round"/>'
            f'<path d="M-20 70c-5-30 4-50 20-50s25 20 20 50z" fill="{CAT}"/><ellipse cx="0" cy="48" rx="9" ry="15" fill="{CAT_L}"/>'
            f'<path d="M-17-4l-4-22 17 12zM17-4l4-22-17 12z" fill="{CAT}"/><path d="M-15-8l-2-11 8 6zM15-8l2-11-8 6z" fill="#e8b4ad"/>'
            f'<circle cx="0" cy="4" r="19" fill="{CAT}"/>'
            f'<circle cx="-7" cy="2" r="2.8" fill="{INK}"/><circle cx="7" cy="2" r="2.8" fill="{INK}"/>'
            f'<path d="M-2.5 8l2.5 2.6 2.5-2.6z" fill="#d97b7b"/>'
            f'<path d="M-6 11h-12M-6 13l-11 4M6 11h12M6 13l11 4" stroke="{INK}" stroke-width="1" opacity=".5"/></g>')


def heart(x, y, s=1.0, c=OR):
    return f'<path transform="translate({x} {y}) scale({s})" d="M0 6c-6-8-18-2-14 7 2 5 14 13 14 13s12-8 14-13c4-9-8-15-14-7z" fill="{c}"/>'


def paw(x, y, s=1.0, c=OR, o=1):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="{c}" opacity="{o}"><ellipse cx="0" cy="6" rx="7" ry="6"/>'
            f'<circle cx="-8" cy="-3" r="3"/><circle cx="-3" cy="-8" r="3"/><circle cx="3" cy="-8" r="3"/><circle cx="8" cy="-3" r="3"/></g>')


def dots(*pts):
    return "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity=".7"/>' for x, y, r in pts)


def ground(cx=270, rx=120, y=168):
    return f'<ellipse cx="{cx}" cy="{y}" rx="{rx}" ry="9" fill="#000" opacity=".06"/>'


def sparkle(x, y, s=1.0, c="#ffb347"):
    return f'<path transform="translate({x} {y}) scale({s})" d="M0-9l2.4 6.6L9 0l-6.6 2.4L0 9l-2.4-6.6L-9 0l6.6-2.4z" fill="{c}"/>'


# ---- 分野ごとの絵（viewBox 0 0 400 180。左下は札が重なるので、主役は右に寄せる）----
def art_taxi():
    return (dots((40, 30, 9), (110, 18, 5), (372, 26, 7)) + ground(250, 140, 166) +
            '<g transform="translate(40 -40) scale(.95)">'
            f'<path d="M70 230v-50c0-12 8-22 20-25l40-10 34-40c6-7 15-11 24-11h96c11 0 20 6 25 15l22 38 24 6c12 3 21 14 21 27v50z" fill="{OR}"/>'
            f'<path d="M178 104c3-4 8-6 13-6h40v52h-79z" fill="{CREAM}"/><path d="M241 98h43c6 0 11 3 14 8l22 44h-79z" fill="{CREAM}"/>'
            f'<rect x="70" y="200" width="290" height="10" fill="{ORD}"/><rect x="320" y="170" width="22" height="12" rx="6" fill="#fff3b0"/>'
            f'<circle cx="132" cy="232" r="30" fill="{INK}"/><circle cx="132" cy="232" r="12" fill="#efe9e3"/>'
            f'<circle cx="300" cy="232" r="30" fill="{INK}"/><circle cx="300" cy="232" r="12" fill="#efe9e3"/>'
            f'<path d="M252 150c0-22 14-36 30-36s30 14 30 36z" fill="{DOG}"/>'
            f'<path d="M258 122c-10-4-16 6-14 20 2 10 8 12 12 8z" fill="{DOG_D}"/><path d="M306 122c10-4 16 6 14 20-2 10-8 12-12 8z" fill="{DOG_D}"/>'
            f'<ellipse cx="282" cy="138" rx="12" ry="9" fill="{DOG_L}"/>'
            f'<circle cx="271" cy="128" r="3.4" fill="{INK}"/><circle cx="293" cy="128" r="3.4" fill="{INK}"/><ellipse cx="282" cy="135" rx="4.5" ry="3.2" fill="{INK}"/>'
            f'<path d="M196 150c0-18 10-30 22-30s22 12 22 30z" fill="{CAT}"/><path d="M200 128l-2-16 12 9zM236 128l2-16-12 9z" fill="{CAT}"/>'
            f'<circle cx="211" cy="134" r="2.8" fill="{INK}"/><circle cx="225" cy="134" r="2.8" fill="{INK}"/></g>'
            + heart(70, 40, 1.1))


def art_hospital():
    return (dots((30, 28, 8), (380, 150, 6)) + ground(280, 125) +
            # 病院の建物
            f'<rect x="150" y="52" width="118" height="114" rx="10" fill="#fff"/><rect x="150" y="52" width="118" height="22" rx="10" fill="{OR}"/>'
            f'<rect x="150" y="64" width="118" height="10" fill="{OR}"/>'
            f'<circle cx="209" cy="44" r="20" fill="#fff" stroke="{OR}" stroke-width="4"/><path d="M209 33v22M198 44h22" stroke="{OR}" stroke-width="7" stroke-linecap="round"/>'
            f'<rect x="164" y="86" width="26" height="22" rx="4" fill="#cfe6f2"/><rect x="228" y="86" width="26" height="22" rx="4" fill="#cfe6f2"/>'
            f'<rect x="192" y="120" width="34" height="46" rx="5" fill="{PEACH}"/><circle cx="219" cy="144" r="2.5" fill="{ORD}"/>'
            # 心電図の線
            f'<path d="M24 58h30l8-16 10 30 8-14h28" stroke="{OR}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity=".55"/>'
            + dog(310, 92, .82) + cat(364, 104, .72))


def art_sougi():
    arcs = "".join(f'<path d="M{200 - r} 176a{r} {r} 0 0 1 {2 * r} 0" stroke="{c}" stroke-width="13" fill="none"/>'
                   for r, c in ((150, "#ffd2b3"), (137, "#ffe8a3"), (124, "#cfe8d6"), (111, "#d6e4f5")))
    flowers = "".join(f'<path d="M{x} 176v-{h}" stroke="{GREEN_D}" stroke-width="3"/>'
                      f'<g transform="translate({x} {176 - h})">' + "".join(
                          f'<circle cx="{dx}" cy="{dy}" r="6" fill="{c}"/>' for dx, dy in ((0, -6), (6, 0), (0, 6), (-6, 0))) +
                      f'<circle r="4" fill="#ffd34d"/></g>'
                      for x, h, c in ((268, 46, "#fff"), (288, 60, "#ffc2cf"), (308, 44, "#fff"), (326, 56, "#ffe0b3"), (344, 40, "#ffc2cf")))
    return (dots((36, 30, 6), (380, 30, 8)) + arcs +
            f'<path d="M262 176l12-18h64l12 18z" fill="{OR}" opacity=".9"/>' + flowers +
            paw(150, 54, .9, "#fff", .9) + paw(186, 40, .8, "#fff", .8) + paw(222, 34, .7, "#fff", .7) +
            sparkle(120, 30, .9, "#fff") + sparkle(372, 76, .8, "#ffb347"))


def art_trainer():
    hanamaru = (f'<g transform="translate(232 70)" fill="none" stroke="{OR}" stroke-width="4" stroke-linecap="round">'
                f'<circle r="20"/><path d="M-12-6c6-14 26-8 22 6-3 10-18 12-20 2-2-9 10-12 14-6"/></g>')
    bone = (f'<g transform="translate(160 54) rotate(-18)" fill="#fff"><rect x="-20" y="-6" width="40" height="12" rx="6"/>'
            f'<circle cx="-20" cy="-6" r="7"/><circle cx="-20" cy="6" r="7"/><circle cx="20" cy="-6" r="7"/><circle cx="20" cy="6" r="7"/></g>')
    ball = f'<circle cx="372" cy="148" r="14" fill="{OR}"/><path d="M360 142c8 4 16 4 24 0" stroke="#fff" stroke-width="3" fill="none"/>'
    return (dots((34, 26, 8), (390, 30, 6)) + ground(305, 95) + hanamaru + bone + ball +
            sparkle(196, 34, 1) + sparkle(128, 88, .7) + dog(306, 86, .95, collar=OR))


def art_rojin():
    house = (f'<path d="M172 166V92l94-58 94 58v74z" fill="#fff"/><path d="M160 98l106-66 106 66" stroke="{OR}" stroke-width="11" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
             f'<rect x="326" y="40" width="16" height="30" rx="3" fill="{ORD}"/>')
    sleep = (f'<g transform="translate(310 146)"><ellipse cx="0" cy="10" rx="70" ry="13" fill="{PEACH}"/>'
             f'<ellipse cx="14" cy="-4" rx="42" ry="18" fill="{DOG}"/>'
             f'<path d="M-10-14h56a12 12 0 0 1 0 24h-56z" fill="{OR}"/><path d="M4-14v24M20-14v24M36-14v24" stroke="#fff" stroke-width="3" opacity=".6"/>'
             f'<circle cx="-34" cy="-8" r="18" fill="{DOG}"/><path d="M-46-16c-10 0-12 14-6 20 4 4 9 2 9-2z" fill="{DOG_D}"/>'
             f'<ellipse cx="-44" cy="0" rx="10" ry="7" fill="{DOG_L}"/><ellipse cx="-51" cy="-2" rx="3.5" ry="2.6" fill="{INK}"/>'
             f'<path d="M-36-12c3 3 7 3 9 0" stroke="{INK}" stroke-width="2" fill="none" stroke-linecap="round"/>'
             f'<path d="M-38-18l8-2" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/></g>')
    zz = f'<text x="300" y="86" font-size="18" font-weight="700" fill="{ORD}" opacity=".6" font-family="sans-serif">z z</text>'
    return dots((36, 26, 8), (130, 20, 5)) + house + sleep + zz + heart(118, 62, 1.1, "#ff9a5c")


def art_sitter():
    house = (f'<rect x="150" y="76" width="112" height="90" rx="8" fill="#fff"/><path d="M140 82l66-46 66 46" stroke="{OR}" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
             f'<rect x="166" y="94" width="34" height="30" rx="5" fill="#cfe6f2"/><rect x="214" y="110" width="32" height="56" rx="5" fill="{PEACH}"/>'
             f'<circle cx="239" cy="140" r="2.5" fill="{ORD}"/>'
             # 窓から見ている猫
             f'<path d="M172 124c0-12 5-18 11-18s11 6 11 18z" fill="{CAT}"/><path d="M174 112l-1-9 7 5zM192 112l1-9-7 5z" fill="{CAT}"/>'
             f'<circle cx="179" cy="115" r="1.8" fill="{INK}"/><circle cx="187" cy="115" r="1.8" fill="{INK}"/>')
    key = (f'<g transform="translate(110 56) rotate(-30)"><circle r="12" fill="none" stroke="#ffb347" stroke-width="6"/>'
           f'<path d="M12 0h30M34 0v9M42 0v7" stroke="#ffb347" stroke-width="6" stroke-linecap="round"/></g>')
    bowl = f'<path d="M290 158h44l-5 10h-34z" fill="{OR}"/><ellipse cx="312" cy="158" rx="22" ry="5" fill="{ORD}"/><circle cx="304" cy="154" r="3" fill="{DOG_D}"/><circle cx="314" cy="153" r="3" fill="{DOG_D}"/><circle cx="322" cy="155" r="3" fill="{DOG_D}"/>'
    return dots((30, 24, 7), (382, 22, 8)) + ground(280, 120) + house + key + bowl + dog(352, 96, .78) + heart(300, 60, .9)


def art_trimming():
    fluffy = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#f6e3cf"/>' for x, y, r in
                     ((280, 70, 22), (262, 58, 15), (298, 58, 15), (280, 46, 15), (246, 80, 14), (314, 80, 14),
                      (280, 128, 32), (256, 120, 18), (304, 120, 18), (262, 158, 12), (298, 158, 12)))
    face = (f'<ellipse cx="280" cy="84" rx="13" ry="10" fill="#fdf2e6"/><circle cx="271" cy="72" r="3.2" fill="{INK}"/><circle cx="289" cy="72" r="3.2" fill="{INK}"/>'
            f'<ellipse cx="280" cy="81" rx="4.5" ry="3.2" fill="{INK}"/><path d="M262 40l6-8 6 8z" fill="{OR}"/><circle cx="268" cy="40" r="4" fill="{OR}"/>')
    sc = (f'<g transform="translate(178 74) rotate(-35)" stroke="{INK}" stroke-width="3" fill="none"><circle cx="-10" cy="22" r="8"/><circle cx="10" cy="22" r="8"/>'
          f'<path d="M-5 15L6-24M5 15L-6-24" stroke-width="4" stroke-linecap="round"/></g>')
    comb = (f'<g transform="translate(352 66) rotate(20)"><rect x="-22" y="-6" width="44" height="10" rx="4" fill="{OR}"/>'
            + "".join(f'<rect x="{-20 + i * 6}" y="3" width="3" height="11" rx="1.5" fill="{OR}"/>' for i in range(7)) + '</g>')
    bub = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="#cfe6f2" stroke-width="2" opacity=".9"/>'
                  for x, y, r in ((340, 132, 9), (364, 114, 6), (220, 140, 7), (130, 40, 6)))
    return dots((34, 26, 7)) + ground(280, 70) + fluffy + face + sc + comb + bub + sparkle(372, 160, .8)


def art_hinan():
    umb = (f'<path d="M150 70a92 50 0 0 1 184 0z" fill="{OR}"/><path d="M150 70c15-10 31-10 46 0 15-10 31-10 46 0 15-10 31-10 46 0 15-10 31-10 46 0" fill="{ORD}"/>'
           f'<path d="M242 20v-6M242 70v24" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')
    rain = "".join(f'<path d="M{x} {y}l-4 10" stroke="#9fc5e8" stroke-width="3" stroke-linecap="round"/>'
                   for x, y in ((120, 30), (136, 60), (104, 74), (360, 40), (378, 70), (356, 96), (140, 100)))
    carrier = (f'<rect x="186" y="104" width="78" height="62" rx="12" fill="{PEACH}"/><path d="M206 104v-10a19 19 0 0 1 38 0v10" stroke="{ORD}" stroke-width="5" fill="none"/>'
               f'<rect x="196" y="116" width="40" height="40" rx="6" fill="#fff"/>'
               f'<path d="M204 152c0-14 5-20 12-20s12 6 12 20z" fill="{CAT}"/><path d="M206 138l-1-10 8 6zM226 138l1-10-8 6z" fill="{CAT}"/>'
               f'<circle cx="212" cy="142" r="1.8" fill="{INK}"/><circle cx="220" cy="142" r="1.8" fill="{INK}"/>'
               + "".join(f'<path d="M{x} 116v40" stroke="{ORD}" stroke-width="2.4"/>' for x in (204, 212, 220, 228)))
    bag = (f'<rect x="326" y="118" width="40" height="48" rx="9" fill="#e85d5d"/><rect x="334" y="110" width="24" height="12" rx="5" fill="none" stroke="#c94747" stroke-width="4"/>'
           f'<path d="M346 132v18M337 141h18" stroke="#fff" stroke-width="5" stroke-linecap="round"/>')
    return ground(270, 110) + rain + umb + carrier + dog(296, 110, .7) + bag


def art_jichitai():
    mapbg = (f'<path d="M150 46l50-14 50 14 50-14v120l-50 14-50-14-50 14z" fill="#fff"/><path d="M200 32v120M250 46v120" stroke="#efe0d3" stroke-width="2"/>'
             f'<path d="M166 130c20-10 30-40 60-36s36 30 60 12" stroke="{OR}" stroke-width="3" stroke-dasharray="2 7" stroke-linecap="round" fill="none" opacity=".8"/>')
    pin = (f'<path d="M286 104c-17-20-26-34-26-46a26 26 0 0 1 52 0c0 12-9 26-26 46z" fill="{OR}"/><circle cx="286" cy="58" r="14" fill="#fff"/>'
           + paw(286, 58, .9, OR))
    mag = (f'<circle cx="124" cy="70" r="20" fill="#eaf4fb" stroke="{INK}" stroke-width="5"/><path d="M110 86l-16 16" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
    return dots((36, 24, 7), (384, 24, 6)) + ground(300, 100) + mapbg + pin + mag + dog(350, 96, .78, collar="#e85d5d")


def art_joto():
    roof = f'<path d="M200 76l100-56 100 56" stroke="{OR}" stroke-width="11" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    return (dots((36, 26, 8), (130, 18, 5)) + ground(300, 100) + heart(300, 50, 3.0, "#ffd2b3") + roof +
            dog(268, 92, .82) + cat(334, 104, .72) + heart(146, 64, 1.1) + heart(176, 40, .7, "#ff9a5c") + sparkle(124, 100, .8))


def art_dogrun():
    fence = "".join(f'<rect x="{x}" y="104" width="9" height="56" rx="3" fill="#fff"/>' for x in range(150, 400, 30)) + \
        '<rect x="140" y="116" width="270" height="7" rx="3" fill="#fff"/><rect x="140" y="140" width="270" height="7" rx="3" fill="#fff"/>'
    grass = f'<path d="M0 160h400v20H0z" fill="{GREEN}"/><path d="M0 160c40-8 80-8 120 0s80 8 120 0 80-8 160 0" fill="{GREEN}"/>'
    tree = f'<rect x="352" y="60" width="10" height="60" rx="4" fill="{DOG_D}"/><circle cx="357" cy="54" r="26" fill="{GREEN_D}"/><circle cx="340" cy="66" r="16" fill="{GREEN}"/>'
    run = (f'<g transform="translate(262 120)">'
           f'<path d="M34-14c12-10 18-22 12-30" stroke="{DOG}" stroke-width="7" fill="none" stroke-linecap="round"/>'
           f'<path d="M-24 6l-16 18M-14 8l-6 22M18 8l12 20M26 4l20 12" stroke="{DOG}" stroke-width="9" stroke-linecap="round"/>'
           f'<ellipse cx="2" cy="-4" rx="38" ry="18" fill="{DOG}"/><ellipse cx="-6" cy="4" rx="20" ry="9" fill="{DOG_L}"/>'
           f'<circle cx="-36" cy="-22" r="18" fill="{DOG}"/><path d="M-30-38c10-6 18 4 12 16-4 6-8 4-9 0z" fill="{DOG_D}"/>'
           f'<ellipse cx="-50" cy="-16" rx="10" ry="7" fill="{DOG_L}"/><ellipse cx="-58" cy="-18" rx="3.6" ry="2.8" fill="{INK}"/>'
           f'<circle cx="-40" cy="-26" r="2.8" fill="{INK}"/><path d="M-54-10c2 3 6 4 9 2" stroke="{INK}" stroke-width="1.8" fill="none" stroke-linecap="round"/></g>')
    ball = f'<circle cx="168" cy="72" r="12" fill="{OR}"/><path d="M158 67c6 4 14 4 20 0" stroke="#fff" stroke-width="3" fill="none"/>'
    motion = f'<path d="M318 96h26M324 108h20" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".8"/>'
    return dots((40, 26, 8), (110, 16, 5)) + fence + grass + tree + ball + motion + run


def art_emergency():
    van = (f'<g transform="translate(120 34)">'
           f'<path d="M20 116V64c0-10 8-18 18-18h86l40 30c8 6 12 14 12 22v18z" fill="#fff"/>'
           f'<path d="M130 52l30 26h-30z" fill="#cfe6f2"/><rect x="20" y="100" width="156" height="8" fill="{OR}"/>'
           f'<rect x="56" y="32" width="26" height="14" rx="5" fill="#e85d5d"/><path d="M50 26l-6-6M88 26l6-6M69 22v-8" stroke="#e85d5d" stroke-width="3" stroke-linecap="round"/>'
           f'<circle cx="80" cy="76" r="17" fill="#e85d5d"/><path d="M80 66v20M70 76h20" stroke="#fff" stroke-width="6" stroke-linecap="round"/>'
           f'<circle cx="56" cy="118" r="16" fill="{INK}"/><circle cx="56" cy="118" r="6" fill="#efe9e3"/>'
           f'<circle cx="148" cy="118" r="16" fill="{INK}"/><circle cx="148" cy="118" r="6" fill="#efe9e3"/></g>')
    pulse = f'<path d="M300 52h20l8-16 10 30 8-14h30" stroke="#e85d5d" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    moon = f'<path d="M64 22a18 18 0 1 0 18 26 14 14 0 1 1-18-26z" fill="#ffe8a3"/>'
    return moon + dots((130, 20, 4), (380, 120, 6)) + ground(220, 100) + van + pulse + heart(352, 92, .9, "#ff9a5c")


def art_guide():
    book = (f'<path d="M158 58c30-10 56-10 80 4v104c-24-14-50-14-80-4z" fill="#fff"/><path d="M318 58c-30-10-56-10-80 4v104c24-14 50-14 80-4z" fill="#fff"/>'
            f'<path d="M238 62v104" stroke="#efe0d3" stroke-width="3"/>'
            + "".join(f'<path d="M{a} {y}h{w}" stroke="#efe0d3" stroke-width="4" stroke-linecap="round"/>' for a, y, w in
                      ((172, 82, 50), (172, 98, 44), (172, 114, 50), (252, 82, 50), (252, 98, 40))))
    route = (f'<path d="M260 130c10-14 30-8 40-22" stroke="{OR}" stroke-width="3" stroke-dasharray="2 6" stroke-linecap="round" fill="none"/>'
             f'<path d="M300 98v-24" stroke="{INK}" stroke-width="3"/><path d="M300 74h18l-5 6 5 6h-18z" fill="{OR}"/>')
    car = (f'<g transform="translate(330 128)"><path d="M0 22v-10c0-4 3-7 7-8l8-2 7-8c1-1 3-2 5-2h18c2 0 4 1 5 3l4 7 5 1c3 1 4 3 4 6v13z" fill="{OR}"/>'
           f'<circle cx="12" cy="24" r="6" fill="{INK}"/><circle cx="46" cy="24" r="6" fill="{INK}"/></g>')
    return dots((36, 26, 8), (390, 30, 5)) + ground(260, 110) + book + route + car + paw(130, 60, 1, "#fff", .9) + sparkle(150, 30, .8)


def art_hotel():
    moon = f'<path d="M120 22a20 20 0 1 0 20 28 15 15 0 1 1-20-28z" fill="#ffe8a3"/>'
    bed = (f'<rect x="196" y="70" width="14" height="96" rx="5" fill="{DOG_D}"/><rect x="370" y="110" width="12" height="56" rx="5" fill="{DOG_D}"/>'
           f'<rect x="200" y="118" width="178" height="30" rx="8" fill="#fff"/>'
           f'<ellipse cx="236" cy="112" rx="24" ry="12" fill="#cfe6f2"/>')
    head = (f'<g transform="translate(244 98)"><circle r="20" fill="{DOG}"/><path d="M-16-12c-10-4-16 8-12 20 2 8 8 9 11 5z" fill="{DOG_D}"/>'
            f'<path d="M16-12c10-4 16 8 12 20-2 8-8 9-11 5z" fill="{DOG_D}"/><ellipse cx="0" cy="8" rx="10" ry="8" fill="{DOG_L}"/>'
            f'<path d="M-11-2c3 3 6 3 8 0M3-2c3 3 6 3 8 0" stroke="{INK}" stroke-width="2" fill="none" stroke-linecap="round"/>'
            f'<ellipse cx="0" cy="5" rx="4" ry="3" fill="{INK}"/></g>')
    blanket = (f'<path d="M232 112h136a10 10 0 0 1 10 10v20h-146z" fill="{OR}"/>'
               + "".join(f'<path d="M{x} 112v30" stroke="#fff" stroke-width="3" opacity=".5"/>' for x in (268, 300, 332)))
    bell = (f'<g transform="translate(340 56)"><path d="M-16 12a16 16 0 0 1 32 0z" fill="#ffb347"/><rect x="-20" y="12" width="40" height="5" rx="2" fill="{ORD}"/>'
            f'<circle cy="-6" r="3" fill="{ORD}"/></g>')
    return moon + dots((60, 30, 5), (170, 24, 4), (390, 26, 6)) + ground(290, 100) + bed + head + blanket + bell + \
        sparkle(160, 60, .8, "#fff") + sparkle(300, 36, .7, "#ffe8a3")


# パス → (絵, 背景の色2つ, 札の文。h1 の下の長い説明文のかわりの1行)
KV = {
    "area": (art_taxi, ("#ffe6d3", "#fff6ee"), "都道府県ごとの料金の目安と、迎えに来てくれる会社"),
    "hospital": (art_hospital, ("#e3f1f7", "#fff6ee"), "夜間・往診・うさぎや鳥も条件でさがせる病院"),
    "sougi": (art_sougi, ("#f3e9f7", "#fff6ee"), "近くのペット火葬場・霊園と、市区の受け付け"),
    "pet-hotel": (art_hotel, ("#e9e6f7", "#fff6ee"), "大型犬・猫専用・病院が併設のホテルも"),
    "dog-trainer": (art_trainer, ("#fff1cf", "#fff6ee"), "吠える・かむ・トイレ。困りごとを相談できる先生"),
    "rojin-home": (art_rojin, ("#ffe9dc", "#fff6ee"), "シニアの犬・猫を長期や終生で預けられるホーム"),
    "pet-sitter": (art_sitter, ("#e6f3e8", "#fff6ee"), "いつもの家で、ごはんと散歩をお願いできます"),
    "trimming": (art_trimming, ("#e4f0fb", "#fff6ee"), "トリマーさんが家まで来てくれる出張トリミング"),
    "hinan": (art_hinan, ("#e3eef8", "#fff6ee"), "避難所に連れて行ける動物と、ケージの決まり"),
    "jichitai": (art_jichitai, ("#e9f3e4", "#fff6ee"), "迷子・犬の登録・引っ越しのときの連絡先"),
    "joto": (art_joto, ("#ffe6e6", "#fff6ee"), "動物愛護センターの譲渡の条件と、申し込みの流れ"),
    "dogrun": (art_dogrun, ("#dff1fb", "#f2fbef"), "公園・お店・高速道路のSA・PAのドッグラン"),
    "emergency": (art_emergency, ("#ece8f6", "#fff6ee"), "夜間・救急の動物病院と、緊急の搬送の会社"),
    "guide": (art_guide, ("#fff0d9", "#fff6ee"), "通院・引っ越し・帰省・お別れのときのヒント"),
}

CHECK = ('<i aria-hidden="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" '
         'stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></i>')

CSS = ('<style id="kv-css">'
       '.area-hero.kvh{padding:12px 0 8px;min-height:0}'
       '.kvh .wrap{display:flex;flex-direction:column}'
       '.kvh .kv{order:-1;position:relative;margin:0 0 10px;border-radius:24px;overflow:hidden;aspect-ratio:20/9;'
       'box-shadow:0 14px 34px rgba(226,86,10,.12)}'
       '.kvh .kv>svg{position:absolute;inset:0;width:100%;height:100%;display:block}'
       '.kvh .kv-chip{position:absolute;left:10px;bottom:10px;max-width:58%;display:flex;gap:8px;align-items:center;margin:0;'
       'background:#fff;border-radius:14px;padding:7px 11px 7px 8px;font-size:.78rem;font-weight:700;color:#2b2622;line-height:1.4;'
       'box-shadow:0 6px 18px rgba(28,26,24,.10)}'
       '.kvh .kv-chip i{flex:none;width:24px;height:24px;border-radius:50%;background:#e8f7ee;color:#1f9d55;display:grid;place-items:center}'
       '.kvh .crumb{margin:0}'
       '.kvh h1{margin:6px 0 2px;font-size:1.45rem}'
       '.kvh h1 small{font-size:.8rem;margin-bottom:2px}'
       '@media(min-width:760px){.area-hero.kvh{padding:24px 0 16px}.kvh .kv{max-width:760px;aspect-ratio:20/7}'
       '.kvh .kv-chip{font-size:.92rem;left:16px;bottom:16px;padding:10px 16px 10px 10px}.kvh h1{font-size:2.1rem}}'
       '</style>')


SHIFT = {"hinan": 34, "sitter": 0, "pet-sitter": 16}  # 札に主役が隠れないよう右へ


def visual(key):
    art, (a, b), chip = KV[key]
    dx = SHIFT.get(key, 0)
    g = f"kvg-{key}"
    svg = (f'<svg viewBox="0 0 400 180" preserveAspectRatio="xMaxYMid slice" aria-hidden="true" focusable="false">'
           f'<defs><linearGradient id="{g}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs>'
           f'<rect width="400" height="180" fill="url(#{g})"/><g transform="translate({dx} 0)">{art()}</g></svg>')
    return f'<figure class="kv" data-kv="{key}">{svg}<p class="kv-chip">{CHECK}{chip}</p></figure>'


def apply(h, key):
    if 'data-kv="' in h:
        return h
    m = re.search(r'<section class="area-hero"([^>]*)>\s*<div class="wrap">', h)
    if not m:
        return h
    end = h.find("</section>", m.end())
    inner = h[m.end():end]
    # h1 の下の長い説明文は札の1行に置きかえる（スマホで「…」で切れていた）
    inner = re.sub(r'\s*<p class="lede[^"]*">.*?</p>', "", inner, count=1, flags=re.S)
    attrs = re.sub(r'\s*style="[^"]*"', "", m.group(1))
    new = f'<section class="area-hero kvh"{attrs}>\n  <div class="wrap">\n    {visual(key)}' + inner
    h = h[:m.start()] + new + h[end:]
    if 'id="kv-css"' not in h:
        h = h.replace("</head>", CSS + "</head>", 1)
    return h


def build(root):
    n = 0
    for key in KV:
        f = os.path.join(root, key, "index.html")
        if not os.path.exists(f):
            continue
        h = open(f, encoding="utf-8").read()
        h2 = apply(h, key)
        if h2 != h:
            open(f, "w", encoding="utf-8").write(h2)
            n += 1
    return n


if __name__ == "__main__":
    import sys
    print(build(sys.argv[1] if len(sys.argv) > 1 else "."))
