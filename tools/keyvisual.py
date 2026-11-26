# [B] 各カテゴリの入口にキービジュアル（Nori 2026-11-16「各カテゴリでキービジュアルいれて」「キービジュアルはイラストじゃないほうがいい」）。
# トップのキービジュアルと同じ角の丸い大きな写真を、分野ごとに別の写真で各分野の入口のページの上に入れる。
# Nori 2026-11-16「キービジュアルももっとかんがえろ」：その時の気持ちを写真の色と構図で（TONE）、日本の家・街・犬種に見える写真、
# 写真の上に「ここで何が解決するか」を言い切る1行（2行に分けるところは <br> で決め、1文字だけ次の行に落ちないようにする）、緊急は写真より速さで高さを抑える（4:1）。
# Nori 2026-11-16「即刻変えて。しこたま考えろ」：分野ごとに「誰が・どんな気持ちで・何をさがしに来たか」から写真を選び直した（柴犬ばかりにしない・猫も出す・人の手でやさしさを見せる・亡くなった子に見える写真は使わない）。
# 写真は img/kv/<分野>.jpg・.webp（1000×500、軽くしてある）。入手元とライセンスは tools/keyvisual_photos.json（どの写真も1か所だけで使う）。
# 特定の施設に見えない、その分野の雰囲気を伝える写真だけ（施設のカードの写真とは別。カードには「イメージ」写真を出さない）。
# 高さは控えめにして、さがす欄がスマホの最初の画面に入るようにする。h1 の下の長い説明文は、写真の上の1行に置きかえる。
# gen_areas.py の最後に動く。何度動かしても同じ結果（data-kv の印で2回目はしない）。新しい分野を作ったら KV と写真を足す。
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = json.load(open(os.path.join(HERE, "keyvisual_photos.json"), encoding="utf-8"))["photos"]

# パス → (見出しの1行＝ここで何が解決するか, 気持ちの色, 文字の位置, 高さの比)
# 気持ちの色：calm＝悲しみに静かに寄り添う／warm＝安心して任せる・迎える／bright＝前向き・元気／care＝落ち着いて急ぐ（病院・避難）／urgent＝夜間・救急（写真より速さ、高さを抑える）
KV = {
    "area": ("車がなくても大丈夫。<br>迎えに来てくれる会社をさがす", "warm", "bottom", "2/1"),
    "hospital": ("うちの子を診てくれる、<br>近くの動物病院をさがす", "care", "bottom", "5/2"),
    "emergency": ("夜間・休日に診てくれる病院", "urgent", "bottom", "4/1"),
    "sougi": ("ありがとうを伝える<br>お別れの場所を、近くで", "calm", "bottom", "2/1"),
    "rojin-home": ("年をとったこの子を、<br>やさしく見てくれる場所", "warm", "bottom", "2/1"),
    "dog-trainer": ("吠える・かむ・引っぱる。<br>プロと一緒に直していく", "bright", "bottom", "2/1"),
    "pet-sitter": ("留守のあいだも、<br>いつもの家で過ごせるように", "warm", "bottom", "2/1"),
    "trimming": ("近くのサロンも、<br>家まで来てくれるトリマーさんも", "bright", "bottom", "2/1"),
    "pet-hotel": ("旅行や入院のあいだも、<br>安心して預けられる場所", "warm", "bottom", "2/1"),
    "hinan": ("災害のとき、<br>この子と一緒に避難するために", "care", "bottom", "2/1"),
    "jichitai": ("迷子・犬の登録・飼えなくなった。<br>困りごとから次にやることへ", "care", "top", "2/1"),
    "joto": ("保護された犬や猫を、<br>新しい家族に迎える", "warm", "bottom", "2/1"),
    "dogrun": ("近くで、思いきり<br>走れるドッグランをさがす", "bright", "bottom", "2/1"),
    "guide": ("通院・引っ越し・帰省。<br>ペットとの移動のコツ", "bright", "bottom", "2/1"),
}
TONE = {  # 文字の下に敷く色と、写真の色あい
    "calm": ("62,52,72", "saturate(.8) brightness(1.03)"),
    "warm": ("92,52,20", "sepia(.08) saturate(1.05)"),
    "bright": ("24,22,20", "none"),
    "care": ("16,42,72", "none"),
    "urgent": ("140,22,22", "saturate(.9)"),
}

CSS = ('<style id="kv-css2">'
       '.area-hero.kvh{padding:12px 0 8px;min-height:0}'
       '.kvh .wrap{display:flex;flex-direction:column}'
       '.kvh .kv{order:-1;position:relative;margin:0 0 10px;border-radius:22px;overflow:hidden;aspect-ratio:var(--ar,2/1);background:#e9e2da;'
       'box-shadow:0 12px 30px rgba(28,26,24,.12)}'
       '.kvh .kv img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;filter:var(--flt,none)}'
       '.kvh .kv::after{content:"";position:absolute;inset:0;background:linear-gradient(to top,rgba(var(--tc),.78) 0%,rgba(var(--tc),.35) 38%,rgba(var(--tc),0) 62%)}'
       '.kvh .kv.kv-top::after{background:linear-gradient(to bottom,rgba(var(--tc),.78) 0%,rgba(var(--tc),.35) 38%,rgba(var(--tc),0) 62%)}'
       '.kvh .kv-t{position:absolute;left:16px;right:16px;bottom:12px;z-index:1;margin:0;color:#fff;font-family:var(--round);font-weight:800;'
       'font-size:1.12rem;line-height:1.38;letter-spacing:.02em;text-shadow:0 1px 8px rgba(0,0,0,.35)}'
       '.kvh .kv-top .kv-t{bottom:auto;top:12px}'
       '.kvh .kv-urgent{border-radius:16px}.kvh .kv-urgent .kv-t{font-size:1rem;bottom:9px}'
       '.kvh .crumb{margin:0}'
       '.kvh h1{margin:6px 0 2px;font-size:1.45rem}'
       '.kvh h1 small{font-size:.8rem;margin-bottom:2px}'
       '@media(min-width:760px){.area-hero.kvh{padding:24px 0 16px}.kvh .kv{max-width:760px;aspect-ratio:var(--ard,20/7)}'
       '.kvh .kv-t{font-size:1.6rem;left:24px;bottom:20px}.kvh .kv-top .kv-t{top:20px}.kvh h1{font-size:2.1rem}}'
       '</style>')


ACTION_FIRST = {"jichitai"}
ALT_FIX = {"jichitai": "窓口で、職員が犬を連れた飼い主に笑顔で説明している"}
HUB_CSS = '<style>.kvh .kv-hub{display:none}@media(min-width:760px){.kvh .kv-hub{display:block}}</style>'


def visual(key):
    p = PHOTOS[key]
    line, tone, pos, ar = KV[key]
    tc, flt = TONE[tone]
    w, h = (int(x) for x in ar.split("/"))
    ard = "6/1" if tone == "urgent" else "20/7"
    cls = "kv" + (" kv-top" if pos == "top" else "") + (" kv-urgent" if tone == "urgent" else "") + (" kv-hub" if key in ACTION_FIRST else "")
    # 入口（/jichitai/）はスマホで写真を出さず、選ぶカードを最初の画面に出す。写真の上の文字は h1 と同じ意味なので入れない。
    # 写真は画面が広いときだけ出す（スマホでは読みこまない）。Nori 2026-11-26「迷子登録のページもなおってない」（スクショは /jichitai/）
    fp = 'loading="lazy"' if key in ACTION_FIRST else 'fetchpriority="high"'
    alt = ALT_FIX.get(key, p["alt"])
    img = (f'<picture><source srcset="/img/kv/{key}.webp" type="image/webp">'
           f'<img src="/img/kv/{key}.jpg" alt="{alt}" width="1000" height="{1000 * h // w}" {fp} decoding="async"></picture>')
    tt = "" if key in ACTION_FIRST else f'<p class="kv-t">{line}</p>'
    st = HUB_CSS if key in ACTION_FIRST else ""
    return (f'<figure class="{cls}" data-kv="{key}" style="--ar:{ar};--ard:{ard};--tc:{tc};--flt:{flt}">{img}'
            f'{tt}</figure>{st}')


def apply(h, key):
    if 'data-kv="' in h:  # 前の版が残っていれば今の形に置きかえる
        h = re.sub(r'<figure class="kv[^"]*" data-kv="[^"]*"[^>]*>.*?</figure>(?:<style>\.kvh \.kv-hub\{[^<]*</style>)?', lambda m: visual(key), h, count=1, flags=re.S)
        h = re.sub(r'<style id="kv-css">.*?</style>', "", h, flags=re.S)
        return h if 'id="kv-css2"' in h else h.replace("</head>", CSS + "</head>", 1)
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
    if 'id="kv-css2"' not in h:
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
