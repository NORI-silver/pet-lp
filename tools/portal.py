"""サイト全体を「ペットのくらし窓口」の総合サイトにする（Nori 2026-11-14「今のサイトってそうなってない？なってなければそうして」）。

gen_areas.py の最後（brand.py・gen_webmcp.py のあと）に、公開する全部のページにかける。
- 上の名前（ロゴ）・og:site_name・構造化データのサイト名（Organization・WebSite・パンくずの1つめ）・見えるパンくずの1つめ・下の名前を
  「ペットのくらし窓口」にそろえる。ペットタクシーは、その中のサービス「ペットタクシー予約窓口」として残す
  （タクシーのページのタイトルの「｜ペットタクシー予約窓口」、サービス（Service）の名前、規約は変えない＝検索順位を守る）。
- 上の名前のすぐ下に、全部の分野へ行ける横に流れるメニュー（catbar）を出す。いま見ている分野に印。
- 下（footer）に、全部の分野の一覧を足す。
- トップ（/index.html）だけ、フォームの後ろに「ペットとのくらしの窓口」（全分野の入口）を入れる。トップを写した地域ページからは外す。
何度動かしても同じ結果になる（印のコメントで入れかえる）。"""
import json, os, re

INFO = "ペットのくらし窓口"
TAXI = "ペットタクシー予約窓口"
SKIP_DIRS = {"go", "booking", "sns", "lib", "tests", "docs", "tools", "node_modules", "webmcp", "img", ".git", ".github"}

# (メニューの短い名前, URL, この URL で始まるページで印をつけるか)
CATBAR = [
    ("ペットタクシー", "/#form"),
    ("夜間・救急の病院", "/hospital/night/"),
    ("動物病院", "/hospital/"),
    ("ペットホテル", "/pet-hotel/"),
    ("シッター", "/pet-sitter/"),
    ("トリミング", "/trimming/"),
    ("しつけ", "/dog-trainer/"),
    ("老犬ホーム", "/rojin-home/"),
    ("ドッグラン", "/dogrun/"),
    ("犬と泊まれる宿", "/inu-yado/"),
    ("犬と入れるカフェ", "/inu-cafe/"),
    ("里親・譲渡", "/joto/"),
    ("迷子・登録", "/jichitai/"),
    ("ペットと避難", "/hinan/"),
    ("亡くなったら", "/sougi/"),
    ("ガイド", "/guide/"),
]
TAXI_PREFIX = ("/tokyo/", "/kanagawa/", "/saitama/", "/chiba/", "/area/")


def _active(path):
    """いまのページの分野（catbar の URL）"""
    if path == "/" or path.startswith(TAXI_PREFIX):
        return "/#form"
    if path.startswith("/emergency/"):
        return "/hospital/night/"
    best = ""
    for _, u in CATBAR:
        if u != "/#form" and path.startswith(u) and len(u) > len(best):
            best = u
    return best


def catbar(path):
    act = _active(path)
    a = "".join(f'<a href="{u}"' + (' aria-current="page"' if u == act else "") + f'>{n}</a>' for n, u in CATBAR)
    return f'<!--CATBAR--><nav class="catbar" aria-label="ペットのくらしの分野"><div class="wrap">{a}</div></nav><!--/CATBAR-->'


def _counts(root):
    try:
        d = json.load(open(os.path.join(root, "webmcp", "data.json"), encoding="utf-8"))
        c = {x["id"]: x["count"] for x in d["categories"]}
    except Exception:
        c = {}
    for k, f, key in (("inns", "inns.json", "inns"), ("cafes", "cafes.json", "cafes")):
        try:
            c[k] = len(json.load(open(os.path.join(root, "tools", f), encoding="utf-8"))[key])
        except Exception:
            pass
    return c


# トップの「ペットとのくらしの窓口」（グループ, [(名前, URL, 説明, 件数のキー)]）
HUB = [
    ("具合が悪いとき・病院", [
        ("夜間・救急の動物病院", "/hospital/night/", "夜や休日に診てもらえる病院を都道府県で", "night_vet"),
        ("条件でさがす動物病院", "/hospital/", "往診・猫の専門・エキゾチック・大型犬の設備", None),
        ("緊急のときの連絡先", "/emergency/", "夜間の病院と、緊急の搬送をしている会社", None),
    ]),
    ("出かける・移動する", [
        ("ペットタクシー", "/#form", "料金の目安をくらべて、空き状況と料金を無料で問い合わせ", None),
        ("ドッグラン", "/dogrun/", "公園・お店・高速道路のSA・PA", "dog_run"),
        ("犬と泊まれる宿", "/inu-yado/", "犬の大きさ・頭数・料金を確かめた宿", "inns"),
        ("猫・うさぎ・小鳥と泊まれる宿", "/pet-yado/", "犬以外のペットOKと公式サイトにある宿", None),
        ("犬と入れるカフェ・ランチ", "/inu-cafe/", "店内OK・テラス・大型犬の条件", "cafes"),
    ]),
    ("預ける・お世話をたのむ", [
        ("ペットホテル", "/pet-hotel/", "大型犬OK・猫専用のホテル", "pet_hotel"),
        ("ペットシッター", "/pet-sitter/", "留守のあいだ家に来てお世話・散歩", "pet_sitter"),
        ("出張トリミング", "/trimming/", "トリミングカー・家に来てくれるお店", "mobile_grooming"),
        ("ドッグトレーナー・しつけ教室", "/dog-trainer/", "出張しつけ・犬の幼稚園", "dog_trainer"),
        ("老犬ホーム・老猫ホーム", "/rojin-home/", "見学・受け入れる動物・登録番号つき", "senior_dog_home"),
    ]),
    ("迎える・くらしの手続き", [
        ("保護犬・保護猫を迎える", "/joto/", "都道府県・政令市・中核市の譲渡の条件と譲渡会", "adoption_center"),
        ("迷子・犬の登録・引取り", "/jichitai/", "動物愛護センター・保健所の窓口", "city_animal_office"),
        ("ペットと避難", "/hinan/", "避難所で受け入れる動物・大きさ・ケージの決まり", None),
    ]),
    ("お別れのとき", [
        ("ペットが亡くなったら", "/sougi/", "まずすること・火葬の種類と料金・自治体の受付", "pet_funeral"),
    ]),
]


def hub_html(root):
    c = _counts(root)
    out = []
    for g, items in HUB:
        lis = []
        for n, u, d, k in items:
            cnt = f'<em>{c[k]:,}件</em>' if k and c.get(k) else ""
            lis.append(f'<li><a href="{u}" data-hub="{u}"><b>{n}</b>{cnt}<span>{d}</span></a></li>')
        out.append(f'<div class="hub-g"><h3>{g}</h3><ul>{"".join(lis)}</ul></div>')
    return ('<!--KURASHI--><section class="kurashi" id="kurashi" aria-labelledby="kurashiTitle"><div class="wrap">'
            '<div class="sh"><span class="eyebrow">PET LIFE</span><h2 id="kurashiTitle">ペットとのくらしの窓口</h2>'
            '<p>ペットタクシーのほかにも、動物病院・預け先・お出かけ先・自治体の窓口まで、全国の情報を都道府県でさがせます。'
            'どれも公式サイトで確かめたことだけを載せていて、順位はつけていません。</p></div>'
            f'<div class="hub">{"".join(out)}</div>'
            '<p class="hub-more"><a href="/guide/">ペットのくらしと移動のガイド（記事の一覧）→</a></p>'
            '</div></section><!--/KURASHI-->')


FOOT = ('<!--FOOTCATS--><nav class="foot-cats" aria-label="ペットのくらし窓口のすべての分野">'
        + "".join(f'<a href="{u}">{n}</a>' for g, items in HUB for n, u, d, k in items)
        + '<a href="/guide/">ガイド</a></nav><!--/FOOTCATS-->')

_LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
_LD_NAME = re.compile(r'("@type":\s*"(?:Organization|WebSite|ListItem)"[^{}]*?"name":\s*)"' + TAXI + '"')
_LD_ALT = re.compile(r'("@id":\s*"https://pet\.shiokonbu\.com/#website",\s*"name":\s*"' + INFO + r'",\s*"alternateName":\s*)\[[^\]]*\]')
_ORG = re.compile(r'("@type":\s*"Organization",\s*"@id":\s*"https://pet\.shiokonbu\.com/#org",\s*"name":\s*"' + INFO + r'",)(?!\s*"alternateName")')


def _ld(m):
    t = _LD_NAME.sub(lambda x: x.group(1) + '"' + INFO + '"', m.group(2))
    t = _LD_ALT.sub(lambda x: x.group(1) + '["' + TAXI + '","ペットタクシーの予約窓口","pet.shiokonbu.com"]', t)
    t = _ORG.sub(lambda x: x.group(1) + '"alternateName":"' + TAXI + '",', t)
    return m.group(1) + t + m.group(3)


def apply(s, path, hub=None):
    # 上の名前（ロゴ）
    s = re.sub(r'(<a class="logo" href="[^"]*"><i>.*?</i>)' + TAXI + '</a>', r'\1' + INFO + '</a>', s, count=1, flags=re.S)
    s = s.replace(f'<meta property="og:site_name" content="{TAXI}">', f'<meta property="og:site_name" content="{INFO}">')
    s = _LD.sub(_ld, s)
    # 見えるパンくずの1つめ
    s = re.sub(r'(<nav class="crumb"[^>]*><a href="/">)' + TAXI + '</a>', r'\1' + INFO + '</a>', s)
    # 下の名前
    s = s.replace(f'<p>{TAXI}</p>\n    <p>&copy; 2026 {TAXI}</p>',
                  f'<p>{INFO}（ペットタクシーは「{TAXI}」）</p>\n    <p>&copy; 2026 {INFO}</p>')
    s = s.replace(f'<p>{INFO}</p>\n    <p>&copy; 2026 {INFO}</p>',
                  f'<p>{INFO}（ペットタクシーは「{TAXI}」）</p>\n    <p>&copy; 2026 {INFO}</p>')
    # 分野のメニュー（上）
    s = re.sub(r'<!--CATBAR-->.*?<!--/CATBAR-->\n?', '', s, flags=re.S)
    if '<header class="top">' in s:
        s = re.sub(r'(<header class="top">.*?</header>\n?)', lambda m: m.group(1) + catbar(path) + "\n", s, count=1, flags=re.S)
    # 分野の一覧（下）
    s = re.sub(r'[ \t]*<!--FOOTCATS-->.*?<!--/FOOTCATS-->\n?', '', s, flags=re.S)
    s = re.sub(r'(<footer>\s*<div class="wrap">\n?)', lambda m: m.group(1) + "    " + FOOT + "\n", s, count=1)
    # 前からある下のメニューから、上の一覧と同じ分野のリンクを外す（同じリンクが2回並ばないように）
    hubs = {u for g, items in HUB for n, u, d, k in items} | {"/guide/"}
    s = re.sub(r'(<!--/FOOTCATS-->\s*<nav>)(.*?)(</nav>)',
               lambda m: m.group(1) + re.sub(r'<a href="([^"]+)">[^<]*</a>', lambda a: "" if a.group(1) in hubs else a.group(0), m.group(2)) + m.group(3),
               s, count=1, flags=re.S)
    # 前からある下のメニューのタクシーの項目は、どのサービスの話か分かる名前に
    for a, b in (("使い方", "ペットタクシーの使い方"), ("料金の目安", "ペットタクシーの料金の目安"), ("よくある質問", "ペットタクシーのよくある質問"),
                 ("キャンセルについて", "ペットタクシーのキャンセル")):
        s = re.sub(r'(<!--/FOOTCATS-->\s*<nav>.*?<a href="/?#[a-z]+">)' + a + '(</a>)', lambda m: m.group(1) + b + m.group(2), s, count=1, flags=re.S)
    s = re.sub(r'(<!--/FOOTCATS-->\s*<nav><a href="/">)トップ(</a>)', r'\1ホーム\2', s, count=1)
    # トップの全分野の入口（トップだけ）
    s = re.sub(r'<!--KURASHI-->.*?<!--/KURASHI-->\n*', '', s, flags=re.S)
    if hub:
        s = s.replace('<section id="how">', hub + "\n\n" + '<section id="how">', 1)
    return s


def build(root):
    hub = hub_html(root)
    n = 0
    for dp, dns, fs in os.walk(root):
        rel = os.path.relpath(dp, root)
        if rel != "." and rel.split(os.sep)[0] in SKIP_DIRS:
            dns[:] = []
            continue
        for f in fs:
            if not f.endswith(".html"):
                continue
            p = os.path.join(dp, f)
            path = "/" + ("" if rel == "." else rel.replace(os.sep, "/") + "/")
            if f != "index.html":
                path += f
            s = open(p, encoding="utf-8").read()
            if "<html" not in s:
                continue
            t = apply(s, path, hub if path == "/" else None)
            if t != s:
                open(p, "w", encoding="utf-8").write(t)
                n += 1
    return n


if __name__ == "__main__":
    import sys
    print(build(sys.argv[1] if len(sys.argv) > 1 else "."))
