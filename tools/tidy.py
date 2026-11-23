# [B] 運営側の集計や読みにくい部品を、全部のページから取る（Nori 2026-11-16「全体的に全然できてない」の見直し一覧）。
# gen_areas.py のいちばん最後（cardskin.py のあと）に動く。何度動かしても同じ結果。
#  1. h1 の上の小さな赤い字の集計（「全国108件（大型犬OK 54件…）・条件でしぼりこめます」など）
#  2. ○だけの「条件をくらべる」の表は「条件の表を開く」にたたむ（縦書きの見出しで読めない。条件はカードの札で分かる）
#  3. 宿の答えの箱（yd-ans）の「当サイトに◯軒を載せています」の行と、ドッグランの数字のタイル（dr-stats）
#  4. ガイドの記事で、読んでいるあいだ画面の下に出つづけるタクシーのボタン（.sticky）
#  5. 「（公式サイトの記載）」の言い回し（nosrc.py が見ない譲渡のページも）
#  6. いったん外した分野（tools/paused.py の宿・カフェ）へのリンク
#  7. 結果の前の「この一覧は無料の情報です…」の断り書き（.emg-free）は、ページの下へ小さく移す（2026-11-16 スマホ点検：さがす人の最初の画面に要らない）
import os, re

SKIP_DIRS = ("tools", "img", "lib", "node_modules")
TALLY = re.compile(r"\d[\d,]*\s*(件|か所|施設|店舗|軒|自治体|都道府県|院|社|団体)|公式サイトの情報をもとに|載せて")


def _end(h, i, tag="div"):
    d = 0
    for m in re.compile(r"<(/?)%s\b[^>]*>" % tag).finditer(h, i):
        d += -1 if m.group(1) else 1
        if d == 0: return m.end()
    return -1


def _cut_blocks(h, start_rx, tag="div"):
    while True:
        m = re.search(start_rx, h)
        if not m: return h
        j = _end(h, m.start(), tag)
        if j < 0: return h
        h = h[:m.start()] + h[j:]


def _fold_cmp(h):
    out, pos = [], 0
    for m in re.finditer(r'<div class="emg-tips"><h4>条件をくらべる</h4>', h):
        j = _end(h, m.start())
        if j < 0: continue
        inner = h[m.end():j - 6]
        inner = re.sub(r'<p class="emg-tips-note">○は公式サイト[^<]*</p>', '<p class="emg-tips-note">○＝書いてある。空欄は「しない」ではなく「分からない」です。</p>', inner)
        out += [h[pos:m.start()], '<details class="cpt" data-cpt><summary>条件の表を開く</summary><div class="cpt-b">', inner, "</div></details>"]
        pos = j
    out.append(h[pos:])
    return "".join(out)


def _yd_ans(h):
    def fix(m):
        b = m.group(0)
        b = re.sub(r"<li>[^<]*(当サイト|載せて)[^<]*</li>", "", b)
        b = re.sub(r"<h2>[^<]*載せて[^<]*</h2>", "<h2>犬と泊まれる宿のポイント</h2>", b)
        return b if "<li>" in b else ""
    return re.sub(r'<div class="yd-ans">.*?</ul></div>', fix, h, flags=re.S)


def _free_down(h):
    ps = re.findall(r'<p class="emg-free">.*?</p>', h, re.S)
    if not ps or "</main>" not in h: return h
    for p in ps: h = h.replace(p, "", 1)
    note = re.sub(r'^<p class="emg-free">', '<p class="emg-free ft" style="font-size:.78rem;color:#5f6368;background:none;padding:0;margin:16px 0">', ps[0])
    i = h.rfind("</main>")
    return h[:i] + f'<div class="wrap">{note}</div>' + h[i:]


def clean(h):
    """本文の中の直し（thin_gate.py も同じものを数える）。"""
    h = re.sub(r"(<h1[^>]*>)<small>([^<]*)</small>", lambda m: m.group(1) if TALLY.search(m.group(2)) else m.group(0), h)
    h = _fold_cmp(h)
    h = _yd_ans(h)
    h = re.sub(r'<ul class="dr-stats">.*?</ul>', "", h, flags=re.S)
    h = _free_down(h)
    for a in ("（公式サイトの記載）", "（公式サイトに記載）", "と公式サイトに書いている", "と公式サイトに書いてある"):
        h = h.replace(a, "")
    return h


def page(h, rel):
    import paused
    h = clean(h)
    h = paused.unlink(h)  # いったん外した分野（宿・カフェ）へのリンクを消す
    top = rel.split("/")[0]
    if "data-cpt" in h and 'id="cpt-css"' not in h:
        import compact
        h = h.replace("</head>", compact.CSS + "</head>", 1)
    if top == "guide":
        h = re.sub(r'<div class="sticky"><a class="btn" href="/#form">[^<]*</a></div>', "", h)
    return h


def build(root):
    n = 0
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root)
        top = rel.split(os.sep)[0]
        if rel == ".": continue  # トップ（index.html は生成の元でもある）は触らない
        if top.startswith(".") or top in SKIP_DIRS: dn[:] = []; continue
        if "index.html" not in fn: continue
        f = os.path.join(dp, "index.html")
        t = open(f, encoding="utf-8").read()
        if 'http-equiv="refresh"' in t: continue
        u = page(t, rel.replace(os.sep, "/"))
        if u != t: open(f, "w", encoding="utf-8").write(u); n += 1
    return n


if __name__ == "__main__":
    import sys
    print("tidy", build(sys.argv[1] if len(sys.argv) > 1 else "."), "pages")
