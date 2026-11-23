"""[B] 2026-11-08 情報ページ（病院・ドッグラン・自治体の窓口・火葬・ホテルなど）から、ペットタクシーの料金くらべ・問い合わせへ進む案内を強める。
Nori 2026-11-08「1と2」。gen_areas.py の最後（crosslink のあと）に動く。何度動かしても同じ結果（<!--TAXICTA--> の中を入れ替える）。
- 下の「…ペットタクシーで」の節に、オレンジのボタン（その県のエリアページのフォームへ。県を選んだ状態で開く）を足す。
- ドッグラン・ホテル・老犬ホーム・しつけ教室・病院（夜間以外）は、一覧の上にも短い案内を出す。夜間・救急、火葬・霊園、迷子の窓口は、急ぎや気持ちを考えて上には出さない。
- 押した回数は ga.js が taxi_cta（cta＝カテゴリ-top／bottom）で数える。
料金は概算で、確定料金ではないことを必ず添える。電話番号は出さない。"""
import os, re

DIRS = ["hospital", "dogrun", "jichitai", "sougi", "pet-hotel", "pet-sitter", "trimming", "dog-trainer", "rojin-home", "inu-yado", "inu-cafe", "hinan", "joto"]
TOP4 = {"tokyo", "kanagawa", "saitama", "chiba"}
# 一覧の上に出す短い案内（見出し, 説明）。ないカテゴリは上に出さない
# 2026-11-14 Nori「一番最初にタクシーの動線があるけど、不適切な気がする、ユーザーのインテントと違うよね？」：
# 一覧を見に来た人の最初に見るものは一覧そのもの。上の案内はやめ、各カードの「ここまでのペットタクシーの料金をくらべる」と下の節だけにする。
TOP_OFF = True
TOP = {
    "dogrun": ("ドッグランまで、車がないときは", "大型犬や何頭もいっしょでも、ペットタクシーで行けます。"),
    "pet-hotel": ("ホテルへの送り迎えに", "家の前からホテルの前まで、ペットタクシーで移動できます。"),
    "rojin-home": ("見学・入所・面会の日の移動に", "家の前から施設の前まで、ペットタクシーで移動できます。"),
    "dog-trainer": ("教室や幼稚園への送り迎えに", "家の前から教室の前まで、ペットタクシーで移動できます。"),
    "inu-cafe": ("お店までの移動に", "大きな犬や何頭もいっしょでも、家の前からお店の前までペットタクシーで移動できます。"),
    "inu-yado": ("宿までの移動に", "大きな犬や何頭もいっしょでも、家の前から宿の前までペットタクシーで移動できます。"),
    "hospital": ("通院や退院のお迎えに", "前もって決まっている通院は、ペットタクシーを予約できます。"),
}
MARK = re.compile(r"<!--TAXICTA-->.*?<!--/TAXICTA-->\n?", re.S)
# 下の「…ペットタクシーで」の節（見出しか説明にペットタクシーとある、最初の節）
BOTTOM = re.compile(r'(<section style="padding-top:0">\s*<div class="wrap">\s*<div class="sh"><h2>[^<]*ペットタクシー[^<]*</h2><p>[^<]*</p></div>|<section style="padding-top:0">\s*<div class="wrap">\s*<div class="sh"><h2>[^<]*</h2><p>[^<]*ペットタクシー[^<]*</p></div>)')
HERO_END = re.compile(r'(<section class="area-hero">.*?</section>\n?)', re.S)
NOTE = "公式サイトの料金表から計算した概算です。確定料金ではありません。"
ARROW = '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 10h12M11 5l5 5-5 5"/></svg>'


def build(root, prefs):
    """prefs: [(slug, 都道府県名)]。書きかえたページの数を返す。"""
    names = dict(prefs)
    n = 0
    for d in DIRS:
        for r, _, fs in os.walk(os.path.join(root, d)):
            if "index.html" not in fs: continue
            p = os.path.join(r, "index.html")
            parts = os.path.relpath(r, root).split(os.sep)
            slug = next((x for x in parts[1:] if x in names), None)
            cat = "hospital-night" if parts[:2] == ["hospital", "night"] else d
            href = (f"/{slug}/#form" if slug in TOP4 else f"/area/{slug}/#form") if slug else "/#form"
            where = names[slug] if slug else ""
            label = f"{where}のペットタクシーの料金をくらべる（無料）" if where else "ペットタクシーの料金をくらべる（無料）"
            html = MARK.sub("", open(p, encoding="utf-8").read())
            old = html
            btn = (f'<!--TAXICTA--><div class="taxi-cta"><a class="btn" href="{href}" data-taxi-cta="{cat}-bottom">{label}{ARROW}</a>'
                   f'<small>お迎えの場所と行き先を入れると、来てもらえる会社と料金の目安が並びます。{NOTE}</small></div><!--/TAXICTA-->')
            html = BOTTOM.sub(lambda m: m.group(1) + "\n    " + btn, html, count=1)
            top = None if TOP_OFF else TOP.get(cat)
            if top and "<!--TAXICTA-->" in html:
                card = (f'<!--TAXICTA--><section class="taxi-top-sec"><div class="wrap"><div class="taxi-top"><p><b>{top[0]}</b>{top[1]}</p>'
                        f'<a class="btn" href="{href}" data-taxi-cta="{cat}-top">{label}{ARROW}</a><small>{NOTE}</small></div></div></section><!--/TAXICTA-->\n')
                html = HERO_END.sub(lambda m: m.group(1) + card, html, count=1)
            if html != old:
                open(p, "w", encoding="utf-8").write(html); n += 1
    return n
