#!/usr/bin/env python3
"""公開の直前に、トップページ（index.html）の大きなプログラムを /app.js の読み込みに置きかえる（2026-11-13 Nori「全部やって」の4「トップページを軽くする」）。

リポジトリの index.html は gen_areas.py の元なので、プログラムを中に書いたまま残す。公開する写し（pages.yml のチェックアウト）だけを書きかえる。
地域ページと同じ /app.js?v=<ハッシュ> を使うので、トップを見たあとに地域ページを開いても、その逆でも、ブラウザに残った写しが使われる。
app.js の中身がトップのプログラムと違うとき（gen_areas.py を実行し忘れたなど）は、何もしない（そのまま出す）。
"""
import hashlib, os, re, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
p = os.path.join(ROOT, "index.html")
h = open(p, encoding="utf-8").read()
m = max(re.finditer(r"<script>(.*?)</script>", h, re.S), key=lambda m: len(m.group(1)))
app = open(os.path.join(ROOT, "app.js"), encoding="utf-8").read()
if m.group(1) != app:
    print("app.js とトップのプログラムが違うので、置きかえません")
    sys.exit(0)
tag = '<script src="/app.js?v=' + hashlib.sha1(app.encode("utf-8")).hexdigest()[:10] + '"></script>'
h = h[:m.start()] + tag + h[m.end():]
open(p, "w", encoding="utf-8").write(h)
print("トップのプログラムを", tag, "に置きかえました", len(h.encode("utf-8")), "バイト")
