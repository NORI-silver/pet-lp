# [B] 各カテゴリの入口にキービジュアル（Nori 2026-11-16「各カテゴリでキービジュアルいれて」「キービジュアルはイラストじゃないほうがいい」）。
# トップのキービジュアル（角の丸い大きな写真＋白い小さな札）と同じ形を、分野ごとに別の写真で各分野の入口のページの上に入れる。
# 写真は img/kv/<分野>.jpg・.webp（1000×500、軽くしてある）。入手元とライセンスは tools/keyvisual_photos.json（どの写真も1か所だけで使う）。
# 特定の施設に見えない、その分野の雰囲気を伝える写真だけ（施設のカードの写真とは別。カードには「イメージ」写真を出さない）。
# 高さは控えめにして、さがす欄がスマホの最初の画面に入るようにする。h1 の下の長い説明文は、写真の上の短い札1行に置きかえる。
# gen_areas.py の最後に動く。何度動かしても同じ結果（data-kv の印で2回目はしない）。新しい分野を作ったら KV と写真を足す。
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = json.load(open(os.path.join(HERE, "keyvisual_photos.json"), encoding="utf-8"))["photos"]

# パス → 札の文（h1 の下の長い説明文のかわりの1行）
KV = {
    "area": "都道府県ごとの料金の目安と、迎えに来る会社",
    "hospital": "夜間・往診・うさぎや鳥も条件でさがせる病院",
    "sougi": "近くのペット火葬場・霊園と、市区の受け付け",
    "pet-hotel": "大型犬・猫専用・病院が併設のホテルも",
    "dog-trainer": "吠える・かむ・トイレの困りごとの相談先",
    "rojin-home": "シニアの犬・猫を長期や終生で預けられるホーム",
    "pet-sitter": "いつもの家で、ごはんと散歩をお願いできます",
    "trimming": "トリマーさんが家まで来てくれる出張トリミング",
    "hinan": "避難所に連れて行ける動物と、ケージの決まり",
    "jichitai": "迷子・犬の登録・引っ越しのときの連絡先",
    "joto": "愛護センターの譲渡の条件と申し込みの流れ",
    "dogrun": "公園・お店・高速道路のSA・PAのドッグラン",
    "emergency": "夜間・救急の動物病院と、緊急の搬送の会社",
    "guide": "通院・引っ越し・帰省・お別れのときのヒント",
}

CHECK = ('<i aria-hidden="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" '
         'stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></i>')

CSS = ('<style id="kv-css">'
       '.area-hero.kvh{padding:12px 0 8px;min-height:0}'
       '.kvh .wrap{display:flex;flex-direction:column}'
       '.kvh .kv{order:-1;position:relative;margin:0 0 10px;border-radius:24px;overflow:hidden;aspect-ratio:2/1;'
       'box-shadow:0 14px 34px rgba(226,86,10,.12)}'
       '.kvh .kv img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}.kvh .kv{background:#f3e7dc}'
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


def visual(key):
    p = PHOTOS[key]
    img = (f'<picture><source srcset="/img/kv/{key}.webp" type="image/webp">'
           f'<img src="/img/kv/{key}.jpg" alt="{p["alt"]}" width="1000" height="500" fetchpriority="high" decoding="async"></picture>')
    return f'<figure class="kv" data-kv="{key}">{img}<p class="kv-chip">{CHECK}{KV[key]}</p></figure>'


def apply(h, key):
    if 'data-kv="' in h:  # 前の版（絵）が残っていれば写真に置きかえる
        return re.sub(r'<figure class="kv" data-kv="[^"]*">.*?</figure>', lambda m: visual(key), h, count=1, flags=re.S)
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
