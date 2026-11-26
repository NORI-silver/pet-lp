"""[E] 生成元がもう作らない昔のページ（no_page の県、なくなった市のページ）に残っている、さがす欄の見出しだけをそろえる。
URL・リンク・robots・ほかの中身には触らない。何度かけても同じ結果（べき等）。gen_areas.py の最後に呼ぶ。
2026-11-26 Nori「うちの子にあてはまるもの」→「よく使用される項目」。"""
import os

# （ページ, ）生成元が作らない古いページ。ここに足すのは「生成元がなくて、公開のままのページ」だけ。
ORPHANS = ["pet-hotel/aomori", "pet-hotel/yamagata", "trimming/chiba/matsudo-shi"]
SWAPS = [('class="ux-l">うちの子にあてはまるもの</span>', 'class="ux-l">よく使用される項目</span>'),
         ('class="fp-l">うちの子は</span>', 'class="fp-l">よく使用される項目</span>')]


def normalize(root):
    n = 0
    for d in ORPHANS:
        p = os.path.join(root, d, "index.html")
        if not os.path.exists(p): continue
        h = open(p, encoding="utf-8").read()
        g = h
        for a, b in SWAPS: g = g.replace(a, b)
        if g != h:
            open(p, "w", encoding="utf-8").write(g); n += 1
    return n
