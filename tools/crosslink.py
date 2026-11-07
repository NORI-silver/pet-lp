"""[B] 2026-11-04：都道府県ごとの情報ページを、同じ県のほかのカテゴリへつなぐ。
例：/dogrun/osaka/ から /sougi/osaka/・/hospital/night/osaka/・/area/osaka/ など。
gen_areas.py の最後に動く（ページを作り直したあとに、</main> の前へ「◯◯のほかの情報」を入れる）。
その県にページがあるカテゴリだけをつなぐ。何度動かしても同じ結果になる（<!--XLINK--> の中を入れ替える）。"""
import os, re

CATS = [  # (フォルダ, ボタンの文字)
    ("hospital/night", "夜間・救急の動物病院"),
    ("dogrun", "ドッグラン"),
    ("sougi", "ペット火葬・霊園"),
    ("pet-hotel", "ペットホテル"),
    ("pet-sitter", "ペットシッター"),
    ("trimming", "出張トリミング"),
    ("dog-trainer", "ドッグトレーナー・しつけ教室"),
    ("rojin-home", "老犬ホーム・老猫ホーム"),
]
# その県の病院・施設への移動ガイド（tools/facility_guides.py）。夜間病院の県ページにだけ足す
GUIDE_LINKS = {"osaka": [("/guide/osaka-yakan-taxi/", "大阪どうぶつ夜間急病センターへの行き方"), ("/guide/hokusetsu-yakan-taxi/", "北摂夜間救急動物病院への行き方")],
               "tokyo": [("/guide/jarmec-tokyo-taxi/", "日本動物高度医療センター東京病院へのタクシー通院"), ("/guide/trva-yakan-taxi/", "TRVA動物医療センター（世田谷）夜間救急への行き方")],
               "kanagawa": [("/guide/jarmec-kawasaki-taxi/", "日本動物高度医療センター川崎本院へのタクシー通院"), ("/guide/dvms-yokohama-taxi/", "DVMsどうぶつ医療センター横浜（夜間救急）への行き方")]}
TOP4 = {"tokyo", "kanagawa", "saitama", "chiba"}
MARK = re.compile(r"<!--XLINK-->.*?<!--/XLINK-->\n?", re.S)

def build(root, prefs):
    """prefs: [(slug, 都道府県名)]。書きかえたページの数を返す。"""
    n = 0
    for slug, name in prefs:
        have = [(d, label) for d, label in CATS if os.path.exists(os.path.join(root, d, slug, "index.html"))]
        taxi = f"/{slug}/" if slug in TOP4 else f"/area/{slug}/"
        for d, _ in have:
            p = os.path.join(root, d, slug, "index.html")
            html = MARK.sub("", open(p, encoding="utf-8").read())
            links = "".join(f'<li><a href="/{d2}/{slug}/">{name}の{label}</a></li>' for d2, label in have if d2 != d)
            links += f'<li><a href="{taxi}">{name}のペットタクシー</a></li>'
            if d == "hospital/night":
                links += "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in GUIDE_LINKS.get(slug, []))
            block = (f'<!--XLINK--><section style="padding-top:0"><div class="wrap"><div class="sh"><h2>{name}のほかの情報</h2></div>'
                     f'<ul class="other">{links}</ul></div></section><!--/XLINK-->\n')
            if "</main>" not in html: continue
            html = html.replace("</main>", block + "</main>", 1)
            open(p, "w", encoding="utf-8").write(html); n += 1
    return n
