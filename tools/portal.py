"""サイト全体を「ペットのくらし窓口」の総合サイトにする（Nori 2026-11-14「今のサイトってそうなってない？なってなければそうして」）。

gen_areas.py の最後（brand.py・gen_webmcp.py のあと）に、公開する全部のページにかける。
- 上の名前（ロゴ）・og:site_name・構造化データのサイト名（Organization・WebSite・パンくずの1つめ）・見えるパンくずの1つめ・下の名前を
  「ペットのくらし窓口」にそろえる。検索向けのタイトルは、内容やサービス名を変えず、末尾の旧サイト名だけ置きかえる。
  ペットタクシーは、その中のサービス「ペットタクシー予約窓口」として残す（Service の名前、規約は変えない）。
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
    ("動物病院・夜間救急", "/hospital/"),  # 夜間・救急は病院のさがす欄の「夜間・救急」と上の赤いボタンから（Nori 2026-11-15「タブわけたほうがいいのか？」→ひとつに）
    ("ペットホテル", "/pet-hotel/"),
    ("シッター", "/pet-sitter/"),
    ("トリミング", "/trimming/"),
    ("しつけ", "/dog-trainer/"),
    ("老犬ホーム", "/rojin-home/"),
    ("ドッグラン", "/dogrun/"),
    ("犬と泊まれる宿", "/inu-yado/"),
    ("犬と入れるカフェ", "/inu-cafe/"),
    ("里親・譲渡", "/joto/"),
    ("迷子", "/jichitai/maigo/"),
    ("犬の登録", "/jichitai/touroku/"),
    ("ペットと避難", "/hinan/"),
    ("亡くなったら", "/sougi/"),
    ("ガイド", "/guide/"),
]
import paused
CATBAR = [c for c in CATBAR if not paused.is_paused(c[1])]  # いったん外した分野（tools/paused.py）
TAXI_PREFIX = ("/tokyo/", "/kanagawa/", "/saitama/", "/chiba/", "/area/")


def _active(path):
    """いまのページの分野（catbar の URL）"""
    if path == "/" or path.startswith(TAXI_PREFIX):
        return "/#form"
    if path.startswith("/emergency/"):
        return "/hospital/"
    best = ""
    for _, u in CATBAR:
        if u != "/#form" and path.startswith(u) and len(u) > len(best):
            best = u
    return best


# Top-level discovery surfaces distinguish the paid comparison from the urgent guide.
_DETECTIVE_NAV = {"/", "/guide/", "/jichitai/maigo/", "/pet-detective/"}

def catbar(path):
    act = _active(path)
    items = CATBAR
    if path in _DETECTIVE_NAV:
        items = [(n,u) if u!="/jichitai/maigo/" else ("ペット探偵","/pet-detective/") for n,u in items]
        if path=="/":
            act = None  # トップは総合の入口。分野のどれもハイライトしない
            # 並びは下の「分野からえらぶ」と同じ（病院、移動、預ける、迷子、手続き、お別れ）。タクシーだけ前に出さない
            _o = ["/hospital/", "/#form", "/dogrun/", "/pet-hotel/", "/pet-sitter/", "/trimming/", "/dog-trainer/", "/rojin-home/", "/jichitai/maigo/", "/pet-detective/", "/hinan/", "/sougi/", "/guide/"]
            items = [("迷子ガイド","/jichitai/maigo/")] + items
            items = sorted(items, key=lambda c: _o.index(c[1]) if c[1] in _o else 99)
        if path=="/pet-detective/": act=path
        if path=="/jichitai/maigo/": act="/guide/"
    a = "".join(f'<a href="{u}"' + (' aria-current="page"' if u == act else "") + f'>{n}</a>' for n, u in items)
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
        ("犬と泊まれる宿", "/inu-yado/", "犬の大きさ・頭数・料金でくらべる宿", "inns"),
        ("猫・うさぎ・小鳥と泊まれる宿", "/pet-yado/", "犬以外のペットOKと公式サイトにある宿", None),
        ("犬と入れるカフェ・ランチ", "/inu-cafe/", "店内OK・テラス・大型犬の条件", "cafes"),
    ]),
    ("預ける・お世話をたのむ", [
        ("ペットホテル", "/pet-hotel/", "全国のホテル・大型犬OK・猫専用", "pet_hotel"),
        ("ペットシッター", "/pet-sitter/", "留守のあいだ家に来てお世話・散歩", "pet_sitter"),
        ("トリミング", "/trimming/", "サロン・トリミングカー・家に来てくれるお店", "mobile_grooming"),
        ("ドッグトレーナー・しつけ教室", "/dog-trainer/", "出張しつけ・犬の幼稚園", "dog_trainer"),
        ("老犬ホーム・老猫ホーム", "/rojin-home/", "見学・受け入れる動物・登録番号つき", "senior_dog_home"),
    ]),
    ("迎える・くらしの手続き", [
        ("保護犬・保護猫を迎える", "/joto/", "自治体や保健所ごとの譲渡の条件と譲渡会", "adoption_center"),
        ("迷子・引取り", "/jichitai/", "動物愛護センター・保健所の窓口", "city_animal_office"),
        ("ペットと避難", "/hinan/", "避難所で受け入れる動物・大きさ・ケージの決まり", None),
    ]),
    ("お別れのとき", [
        ("ペットが亡くなったら", "/sougi/", "まずすること・火葬の種類と料金・自治体の受付", "pet_funeral"),
    ]),
]
HUB = [(g, [it for it in items if not paused.is_paused(it[1])]) for g, items in HUB]  # いったん外した分野（tools/paused.py）


def hub_html(root):
    c = _counts(root)
    out = []
    groups = [(g,items) for g,items in HUB]
    groups.insert(3, ("ペットが迷子になったら", [
        ("迷子の初動ガイド", "/jichitai/maigo/", "今日やること・地域の届け先・チラシ作り", None),
        ("ペット探偵", "/pet-detective/", "対応地域・料金・現地入りの目安で比較", None),
    ]))
    for g, items in groups:
        lis = []
        for n, u, d, k in items:
            cnt = f'<em>{c[k]:,}件</em>' if k and c.get(k) else ""
            lis.append(f'<li><a href="{u}" data-hub="{u}"><b>{n}</b>{cnt}<span>{d}</span></a></li>')
        out.append(f'<div class="hub-g"><h3>{g}</h3><ul>{"".join(lis)}</ul></div>')
    return ('<!--KURASHI--><section class="kurashi" id="kurashi" aria-labelledby="kurashiTitle"><div class="wrap">'
            '<div class="sh"><span class="eyebrow">PET LIFE</span><h2 id="kurashiTitle">ペットとのくらしの窓口</h2>'
            '<p>ペットタクシーのほかにも、動物病院・預け先・お出かけ先・自治体の窓口まで、全国の情報を都道府県でさがせます。'
            '公式サイトの情報をもとに載せていて、順位はつけていません。</p></div>'
            f'<div class="hub">{"".join(out)}</div>'
            '<p class="hub-more"><a href="/guide/">ペットのくらしと移動のガイド（記事の一覧）→</a></p>'
            '</div></section><!--/KURASHI-->')


FOOT = ('<!--FOOTCATS--><nav class="foot-cats" aria-label="ペットのくらし窓口のすべての分野">'
        + "".join(f'<a href="{u}">{n}</a>' for g, items in HUB for n, u, d, k in items)
        + '<a href="/guide/">ガイド</a></nav><!--/FOOTCATS-->')

# どのページの下にも出す短い表示（運営・出どころ・並び順・誤りの報告。2026-11-16「信頼されるサイトにする」）。くわしくは /about/
TRUST = ('<!--TRUST--><p class="foot-trust" style="font-size:.78rem;line-height:1.7;color:#5f6368;margin:10px 0">'
         '公式サイトや自治体などの公開情報をもとに、各ページに時点を書いて載せています。掲載は無料で、お金で並び順は変わりません。'
         '<a href="/about/">運営者と掲載の基準</a>・<a href="/contact/">まちがいを知らせる</a></p><!--/TRUST-->')

_LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
_LD_NAME = re.compile(r'("@type":\s*"(?:Organization|WebSite|ListItem)"[^{}]*?"name":\s*)"' + TAXI + '"')
# サブドメイン全体の名前と、タクシーサービスの名称を混ぜない。
_LD_ALT = re.compile(r'("@id"\s*:\s*"https://pet\.shiokonbu\.com/#(?:website|org)"\s*,\s*"name"\s*:\s*"' + INFO + r'")\s*,\s*"alternateName"\s*:\s*(?:\[[^\]]*\]|"[^"]*")')
_OLD_TITLE_SUFFIX = re.compile(r'(?:\s*[｜|–—-]\s*(?:ペットタクシー(?:の?予約窓口)?|SHIOKONBU)\s*)+$', re.I)
_HEAD_TITLES = re.compile(r'(<title>)([^<]*)(</title>)|(<meta (?:name|property)="(?:og:title|twitter:title)" content=")([^"]*)(")', re.I)


def _ld(m):
    t = _LD_NAME.sub(lambda x: x.group(1) + '"' + INFO + '"', m.group(2))
    return m.group(1) + _LD_ALT.sub(r'\1', t) + m.group(3)


def _title(m):
    begin, value, end = m.groups()[:3] if m.group(1) else m.groups()[3:]
    return begin + _OLD_TITLE_SUFFIX.sub("｜" + INFO, value) + end


def apply(s, path, hub=None):
    # 上の名前（ロゴ）
    s = re.sub(r'(<a class="logo" href="[^"]*"><i>.*?</i>)' + TAXI + '</a>', r'\1' + INFO + '</a>', s, count=1, flags=re.S)
    s = s.replace(f'<meta property="og:site_name" content="{TAXI}">', f'<meta property="og:site_name" content="{INFO}">')
    s = _HEAD_TITLES.sub(_title, s)
    s = _LD.sub(_ld, s)
    # 見えるパンくずの1つめ
    s = re.sub(r'(<nav class="crumb"[^>]*><a href="/">)' + TAXI + '</a>', r'\1' + INFO + '</a>', s)
    # 下の名前
    s = s.replace(f'<p>{TAXI}</p>\n    <p>&copy; 2026 {TAXI}</p>',
                  f'<p>{INFO}（ペットタクシーは「{TAXI}」）</p>\n    <p>&copy; 2026 {INFO}</p>')
    if path != "/":  # トップは総合の入口：名前はそのまま（タクシーだけ別名を添えない）
        s = s.replace(f'<p>{INFO}</p>\n    <p>&copy; 2026 {INFO}</p>',
                      f'<p>{INFO}（ペットタクシーは「{TAXI}」）</p>\n    <p>&copy; 2026 {INFO}</p>')
    # 分野のメニュー（上）
    s = re.sub(r'<!--CATBAR-->.*?<!--/CATBAR-->\n?', '', s, flags=re.S)
    if '<header class="top">' in s:
        s = re.sub(r'(<header class="top">.*?</header>\n?)', lambda m: m.group(1) + catbar(path) + "\n", s, count=1, flags=re.S)
    if path in _DETECTIVE_NAV:
        def clean_header(m):
            return re.sub(r'<a href="([^"]+)">[^<]*</a>', lambda a: "" if paused.is_paused(a[1]) else (
                '<a href="/jichitai/maigo/">迷子ガイド</a>' if a[1]=="/jichitai/maigo/" else a[0]), m[1])
        s = re.sub(r'(<header class="top">.*?</header>)', clean_header, s, count=1, flags=re.S)
    # 分野の一覧（下）
    s = re.sub(r'[ \t]*<!--FOOTCATS-->.*?<!--/FOOTCATS-->\n?', '', s, flags=re.S)
    s = re.sub(r'(<footer>\s*<div class="wrap">\n?)', lambda m: m.group(1) + "    " + FOOT + "\n", s, count=1)
    s = re.sub(r'[ \t]*<!--TRUST-->.*?<!--/TRUST-->\n?', '', s, flags=re.S)
    s = re.sub(r'(<p>&copy; 2026 )', lambda m: TRUST + "\n    " + m.group(1), s, count=1)
    s = s.replace('<a href="/#operator">運営者情報</a>', '<a href="/about/">運営者と掲載の基準</a>')
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
        if path == "/" and "<!--/PHERO-->" in s:
            # トップは総合の入口：検索の下にそのまま全分野（下に同じ一覧をもう一度出さない）
            hub_home = hub.replace('<span class="eyebrow">PET LIFE</span><h2 id="kurashiTitle">ペットとのくらしの窓口</h2>', '<h2 id="kurashiTitle">分野からえらぶ</h2>')
            hub_home = re.sub(r'<em>[^<]*件</em>', '', hub_home)  # 件数は出さない（サイト内の集計で、検索の結果とずれうる）
            hub_home = re.sub(r'<p>ペットタクシーのほかにも.*?</p></div>', '</div>', hub_home, count=1, flags=re.S)
            s = s.replace("<!--/PHERO-->", "<!--/PHERO-->\n" + hub_home, 1)
        else:
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
