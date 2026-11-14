# [B] お金を取らない情報ページ「保護犬・保護猫を迎える（譲渡・里親）」（/joto/ と /joto/<県>/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-14「そうしよう」（保護シェルター・譲渡のページと都道府県ごとのページ）。
# 検索：「犬の里親」月12,100・「保護犬 譲渡会」「保護猫 譲渡会」月6,600・「犬 シェルター」月720・「保護犬 条件」月320（キーワードプランナー 2026-11-14）。
# 読みに来る人が知りたいこと：どこで迎えられるか（県・市の動物愛護センター＝公的なシェルター）、条件（年齢・住まい・家族・講習）、費用、譲渡会。
# 守ること：都道府県・政令市の公式ページで確かめたことだけ（tools/joto.json、項目ごとに公式ページのリンク）。書いていないことは書かない。
# 順位・おすすめなし。電話番号なし。第2弾（2026-11-14）：中核市62を足し、条件が5つ以上ある市は市のページ /joto/<県>/<市>/ を作る（薄いページは作らない）。
# 民間の保護団体は、自治体が公式に出している登録団体の一覧へのリンクで案内する（団体ごとの条件・費用は書かない）。
# ペットタクシーの話は、下の「迎える日の移動」の枠（taxi_cta.py）と記事 /guide/new-family/ へのリンクだけ（AGENTS.md「分野ごとに話を分ける」）。
import json, os, re
import prefkeep

_D = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(_D, "joto.json"), encoding="utf-8"))
SLUG = "joto"
H1 = "保護犬・保護猫を迎える（譲渡・里親）"
NAME = "保護犬・保護猫の譲渡の窓口"
TITLE = "保護犬・保護猫の譲渡（里親）｜全国の動物愛護センターの条件・費用・譲渡会を都道府県でさがす｜ペットタクシー予約窓口"
DESC = ("保護犬・保護猫の里親になりたい人のために、47都道府県・政令指定都市・中核市の動物愛護センター（公的なシェルター）の譲渡の案内を、"
        "公式ページで確かめた条件（年齢・住まい・家族・講習会・トライアル・費用）と一緒にまとめました。譲渡会や県に登録した保護団体の一覧へのリンクも。")

ITEMS = [dict(c, prefs=[c["pref"]]) for c in J["centers"]]

def _kind(c):
    return f'{c["city"]}（{c.get("kind") or "政令指定都市"}）' if c.get("city") else f'{c["pref"]}（都道府県）'

# 市のページ（/joto/<県>/<市>/）。条件が5つ以上書いてある市だけ（薄いページは作らない。Nori 2026-11-14）。
import gen_dogrun
PSLUG = gen_dogrun.PSLUG
_MUNI = {(m["pref"], m["name"]): m["slug"] for m in json.load(open(os.path.join(_D, "municipalities.json"), encoding="utf-8"))}
CITY_MIN = 5
def city_href(c):
    if not c.get("city") or len(c["conds"]) < CITY_MIN: return None
    s = _MUNI.get((c["pref"], c["city"]))
    return f"/{SLUG}/{PSLUG[c['pref']]}/{s}/" if s else None
CITY_ITEMS = [c for c in ITEMS if city_href(c)]

# 条件の見出しごとに、公式ページに書いてあるかどうか（書いてある＝○、書いていない＝空欄。「しない」ではない）
TOPICS = [("年齢", ("歳", "成人")), ("住まい", ("住まい", "住宅", "賃貸", "借家", "集合", "住居", "公営")),
          ("家族の賛成", ("賛成", "同意")), ("講習", ("講習", "教室", "説明を受け")), ("お試し", ("トライアル", "お試し", "体験飼育")),
          ("不妊去勢", ("不妊", "去勢", "繁殖")), ("室内飼い", ("室内", "屋内")), ("費用", ("円", "無料", "無償", "手数料"))]
def topic_mark(c, words):
    hit = [x for x in c["conds"] if any(w in x for w in words)]
    if not hit: return ""
    if any(("ない" in x and ("トライアル" in x)) for x in hit) and words == TOPICS[4][1]: return "なし"
    return "○"

def card(e, c):
    conds = "".join(f"<li>{e(x)}</li>" for x in c["conds"])
    links = "".join(f'<li><a href="{e(l["u"])}" target="_blank" rel="noopener">{e(l["t"])} ↗</a></li>' for l in c.get("links", []))
    return (f'<div class="emg-item emg-co jt-card"><a href="{e(c["url"])}" target="_blank" rel="noopener"><b>{e(c["name"])}</b></a>'
            f'<small>{e(_kind(c))}・{e(c["animals"])}</small>'
            f'<p class="jt-h">公式ページに書いてあること</p><ul class="jt-c">{conds}</ul>'
            + (f'<p class="jt-h">あわせて見る（公式ページ）</p><ul class="jt-l">{links}</ul>' if links else "")
            + (f'<p class="jt-more"><a href="{city_href(c)}">{e(c["city"])}で迎えるときの条件をくわしく見る →</a></p>' if city_href(c) and not c.get("_nolink") else "")
            + f'<small class="sg-src">{e(J["checked"])}に公式ページで確認</small></div>')

CSS = """<style>
.jt-card .jt-h{font-size:.76rem;font-weight:700;color:var(--ink-2);margin:10px 0 2px}
.jt-card ul{margin:0;padding-left:1.2em;font-size:.86rem;line-height:1.7}
.jt-card ul.jt-l{font-size:.84rem}
.emg-item small.sg-src{color:var(--ink-3);font-size:.72rem;margin-top:6px}
.jt-card .jt-more{margin:8px 0 0;font-size:.86rem;font-weight:700}
.jt-chk{display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:6px;margin:8px 0 4px!important;padding:0!important;list-style:none}
.jt-chk li{border-radius:10px;padding:7px 10px;font-size:.84rem;background:#f1f3f4;color:#5f6368}
.jt-chk li.on{background:#e6f4ea;color:#1e4620;font-weight:700}
.jt-chk li.on::before{content:"✓ ";color:#188038}
.jt-flow{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 4px;padding:0;list-style:none;counter-reset:jt}
.jt-flow li{flex:1 1 140px;background:var(--cream);border-radius:10px;padding:8px 10px;font-size:.84rem;counter-increment:jt}
.jt-flow li b{display:block;font-size:.88rem}
.jt-flow li b::before{content:counter(jt) ". "}
</style>"""

FLOW = [("さがす", "県や市の動物愛護センター、譲渡会、保護団体のページで、迎えたい子をさがす"),
        ("講習・申し込み", "多くの県で、飼い方の講習（動画のところも）と申込書・誓約書が先"),
        ("面会・審査", "家族構成・住まい・留守の時間などを聞かれる。家庭訪問のところも"),
        ("お試し・お迎え", "トライアル（多くは2週間）のあと正式に譲渡。手数料がかかる県も"),
        ("迎えたあと", "不妊去勢・マイクロチップ・犬の登録、決まった時期の近況報告")]

def flow_html(e):
    return '<ol class="jt-flow">' + "".join(f"<li><b>{e(t)}</b>{e(s)}</li>" for t, s in FLOW) + "</ol>"

BEFORE = [
 ("住んでいる県・市の窓口へ", "多くの自治体は、原則として住んでいる都道府県・市の人に譲渡します（神奈川県は東京都・山梨県・静岡県も、奈良県・高知県・広島県・静岡県は県外も可など、広げているところもあります）。政令指定都市に住んでいる人は、市のセンターが窓口です。"),
 ("年齢と「代わりに飼う人」", "60歳・65歳などを目安に、それより上の人や一人暮らしの人には、飼えなくなったときに代わりに飼う人（後見人・サポートする人）を決めるよう求める県が多くあります。高齢の人向けに、10歳以上の子をすすめる神奈川県のような例もあります。"),
 ("住まいと家族", "ペットを飼える住まいであること（賃貸は契約書や規約の写し）と、同居の家族全員の賛成は、ほとんどの自治体の条件です。先住の犬猫の頭数や、不妊去勢をしているかを聞かれることもあります。"),
 ("講習会とお試し", "譲渡の前に、飼い方の講習会（オンラインの動画のところもあります）を受けるのがふつうです。2週間ほどのトライアルがある自治体と、トライアルをしない自治体があります。"),
 ("費用", "無料のところと、手数料がかかるところがあります（このページで確かめた例：青森県3,000円、福島県4,000円、岐阜県7,900円、愛知県9,000円、長野県の犬13,000円・猫12,000円。不妊去勢やワクチン、マイクロチップを済ませている分がふくまれることが多いです）。迎えたあとの食事・医療・犬の登録の費用は飼い主の負担です。"),
 ("保護団体（ボランティア）から迎えるとき", "県や市に登録した団体の一覧を出している自治体があります（このページの「あわせて見る」）。団体ごとに条件と譲渡費用が違うので、公式サイトで確かめ、分からないことは迎える前にたずねてください。"),
]

def faq(n_pref, n_city, n_core=0):
    return [
     ("保護犬・保護猫はどこで迎えられますか？", f"都道府県・政令指定都市・中核市の動物愛護センターや保健所（公的なシェルター）と、民間の保護団体・ボランティアの譲渡会や施設です。このページでは{n_pref}都道府県・{n_city}の政令指定都市・{n_core}の中核市の公式の譲渡の案内をまとめています。"),
     ("譲渡会はどこでさがせますか？", "県や市のセンターの公式ページの「譲渡会」「お知らせ」に出ます。センターが開くもののほか、県に登録した保護団体の譲渡会を案内している自治体もあります。開く日や予約のしかたは毎回変わるので、公式ページで確かめてください。"),
     ("一人暮らしや高齢でも里親になれますか？", "自治体によって違います。一人暮らしや60〜66歳以上の人は、代わりに飼う人（後見人）を決めれば申し込める自治体が多く、一人暮らしを原則受けない県（兵庫県・茨城県など）もあります。このページの各県の条件をご覧ください。"),
     ("譲渡の費用はいくらですか？", "無料の自治体（広島県・愛媛県など）と、手数料がかかる自治体（例：青森県3,000円、福島県4,000円、岐阜県7,900円、愛知県9,000円、長野県の犬13,000円・猫12,000円）があります。民間の保護団体は、医療費などの実費を譲渡費用として求めることが多く、金額は団体ごとに違います。"),
     ("トライアル（お試し）はありますか？", "あるところとないところがあります。このページで確かめた例では、茨城県・千葉県・大阪府・熊本県・札幌市（先住動物がいるときだけ）などが2週間ほどのトライアルを書いていて、神奈川県や和歌山県は「していない」と書いています。"),
     ("「シェルター」とは何ですか？", "保護した犬や猫を、新しい飼い主が見つかるまで世話する施設のことです。日本では、県や市の動物愛護センター（公的なシェルター）と、民間の保護団体が運営する施設があります。"),
     ("迎える日はどうやって連れて帰ればいいですか？", "キャリーや首輪・リードを持っていくよう案内している自治体が多いです。車がないときや大きな犬のときは、ペットタクシーで家まで一緒に帰る方法もあります（記事「新しい家族を迎えに行くとき」）。"),
    ]

def _ld(SITE, url, name, faq_list, crumbs):
    return '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq_list]}],
      ensure_ascii=False, indent=1) + "\n</script>"

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    rows = {}
    for c in ITEMS:
        rows.setdefault(c["pref"], []).append(c)
    n_pref = len({c["pref"] for c in ITEMS if not c.get("city")})
    n_city = sum(1 for c in ITEMS if c.get("kind") == "政令指定都市")
    n_core = sum(1 for c in ITEMS if c.get("kind") == "中核市")
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            cs = rows.get(pf, [])
            inner = "".join(card(e, c) for c in cs) or f'<p class="emg-none">{e(pf)}の譲渡の案内は、まだ載せていません。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    fq = faq(n_pref, n_city, n_core)
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in fq)
    ld = _ld(SITE, url, H1, fq, [("ペットタクシー予約窓口", SITE + "/"), (H1, url)])
    return ctx["head"](TITLE, DESC, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › {e(H1)}</nav>
    <h1><small>{n_pref}都道府県・{n_city}政令市・{n_core}中核市の公式の案内</small>{e(H1)}</h1>
    <p class="lede">保護犬・保護猫の里親になるには、まず住んでいる県や市の動物愛護センター（公的なシェルター）の案内を見るのが近道です。申し込める人の条件・講習会・トライアル・費用は自治体ごとに違うので、公式ページに書いてあることを都道府県ごとにまとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips jt-ans" style="margin-top:0"><h4>先に答え：迎えるまでの流れ</h4>{flow_html(e)}
      <p class="emg-tips-note">くわしい条件・費用・保護団体のえらび方は、記事「<a href="/guide/adopt-pet/">保護犬・保護猫を迎えるには</a>」に。</p></div>
      <p class="emg-free">この一覧は無料の情報です。自治体や団体からお金をもらっていません。条件は{e(J["checked"])}に各自治体の公式ページで確かめた内容を短くまとめたもので、変わることがあります。申し込む前に、必ずリンク先の公式ページでご確認ください。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>申し込む前に確かめること</h4><dl>{before}</dl></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">市に住んでいる人は、まず市の窓口の案内をご覧ください（大阪府の高槻市・豊中市・八尾市・寝屋川市などは大阪府が譲渡します）。民間の保護団体は、県や市が公式に出している登録団体の一覧（各窓口の「あわせて見る」）からさがせます。掲載の内容の誤りは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>迎える日の移動は、ペットタクシーでも</h2><p>車がないとき、大きな犬のとき、家族と一緒に新しい子を家まで連れて帰れます。</p></div>
    <ul class="other"><li><a href="/guide/adopt-pet/">保護犬・保護猫を迎えるには（条件・費用・流れ）</a></li><li><a href="/guide/new-family/">新しい家族を迎えに行くとき</a></li><li><a href="/jichitai/">全国の動物愛護センター・保健所（迷子・登録）</a></li><li><a href="/dog-trainer/">ドッグトレーナー・しつけ教室</a></li><li><a href="/hospital/">条件でさがす動物病院</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{prefkeep.LIST_JS}
""" + ctx["foot_noband"]()

def urls(SITE):
    return [f"{SITE}/{SLUG}/"]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))

# ── 都道府県ごとのページ（tools/gen_prefpages.py。「保護犬 譲渡会 ◯◯」「◯◯県 動物愛護センター 譲渡」） ──
def _has(rs, *ws): return sum(any(w in x for x in c["conds"] for w in ws) for c in rs)
def _facts(rs):
    return [f"載せている窓口：{len(rs)}（" + "・".join(c["city"] or c["pref"] for c in rs) + "）",
            f"講習会（動画をふくむ）を案内に書いている窓口：{_has(rs, '講習', '教室', '動画')}／{len(rs)}",
            f"トライアル（お試し）を書いている窓口：{sum(any(('トライアル' in x or 'お試し' in x) and 'ない' not in x for x in c['conds']) for c in rs)}／{len(rs)}"]

def _faq(pf, rs, n):
    names = "、".join(c["name"] for c in rs)
    return [
     (f"{pf}で保護犬・保護猫を迎えるにはどこに申し込みますか？", f"{pf}では{names}が譲渡の窓口です（政令指定都市・中核市に住んでいる人は、まず市の窓口。市ごとの条件はそれぞれの欄で）。条件と流れはこのページの各窓口の欄と、リンク先の公式ページでご確認ください。"),
     (f"{pf}の譲渡会はどこでわかりますか？", "県や市の窓口の公式ページの「譲渡会」「お知らせ」に出ます。このページの「あわせて見る」に、確かめた譲渡会や登録団体のページを載せています。"),
     ("譲渡の費用はかかりますか？", "自治体ごとに違います。手数料が書いてある窓口は、このページの条件の欄にその金額を載せています。迎えたあとの食事・医療・犬の登録の費用は飼い主の負担です。"),
     ("迎える日はどうやって連れて帰りますか？", "キャリーや首輪・リードを持って迎えに行きます。車がないときや大きな犬のときは、ペットタクシーで家まで一緒に帰る方法もあります。"),
    ]

def _title(pf, rs, n):
    return f"{pf}の保護犬・保護猫の譲渡（里親）｜動物愛護センターの条件・講習会・譲渡会｜ペットタクシー予約窓口"

def _desc(pf, rs, n):
    return (f"{pf}で保護犬・保護猫の里親になりたい人へ。" + "・".join(c["name"] for c in rs)
            + "の譲渡の案内を、公式ページで確かめた条件（年齢・住まい・家族・講習会・トライアル・費用）と、譲渡会・登録団体のリンクと一緒にまとめました。")[:160]

CAT = dict(slug=SLUG, name="保護犬・保護猫の譲渡", unit="か所", h1=H1, items=ITEMS, card=card, checked=J["checked"], min=1, css=CSS,
  free="この一覧は無料の情報です。自治体や団体からお金をもらっていません。条件は公式ページに書いてあることを短くまとめたもので、変わることがあります。申し込む前に必ずリンク先でご確認ください。",
  list_h="譲渡の窓口（県・市の動物愛護センター）",
  lede=lambda pf, n: f"{pf}で保護犬・保護猫を迎えたいときの窓口と、申し込める人の条件・講習会・トライアル・費用を、公式ページに書いてあることだけでまとめました。譲渡会や県に登録した保護団体のページへのリンクも一緒にどうぞ。",
  facts=_facts, faq=_faq, title_fn=_title, desc_fn=_desc,
  before_title="申し込む前に確かめること", before=BEFORE,
  taxi_h="迎える日の移動は、ペットタクシーでも", taxi_p="車がないとき、大きな犬のとき、家族と一緒に新しい子を家まで連れて帰れます。",
  links=[("保護犬・保護猫を迎えるには（条件・費用・流れ）", "/guide/adopt-pet/"), ("新しい家族を迎えに行くとき", "/guide/new-family/"), ("全国の動物愛護センター・保健所", "/jichitai/")])

# 県のページの「条件をくらべる」表（gen_prefpages.table_html。○＝公式ページの条件に書いてある、空欄＝書いていない）
CAT["table"] = [(h, (lambda w: (lambda c: topic_mark(c, w)))(w)) for h, w in TOPICS]

# ── 自治体に登録された民間の保護団体（tools/joto_groups.json。団体の公式サイトに書いてある条件・費用だけ） ──
G = json.load(open(os.path.join(os.path.dirname(__file__), "joto_groups.json"), encoding="utf-8"))

def groups_html(e, pf):
    gs = [g for g in G["groups"] if g["pref"] == pf]
    if not gs: return ""
    reg = G["registries"].get(pf)
    cards = "".join(
        f'<div class="emg-item emg-co jt-card"><a href="{e(g["url"])}" target="_blank" rel="noopener"><b>{e(g["name"])}</b></a>'
        f'<small>民間の保護団体・{e(g["animals"])}{("・" + e(g["area"])) if g["area"] else ""}</small>'
        '<p class="jt-h">おもな条件（団体の公式サイトより）</p><ul class="jt-c">' + "".join(f"<li>{e(x)}</li>" for x in g["conds"]) + "</ul>"
        '<p class="jt-h">費用</p><ul class="jt-c">' + "".join(f"<li>{e(x)}</li>" for x in g["fees"]) + "</ul>"
        f'<p class="jt-more"><a href="{e(g["cond_url"])}" target="_blank" rel="noopener">条件・費用のページ（団体の公式サイト） ↗</a></p>'
        f'<small class="sg-src">{e(G["checked"])}に公式サイトで確認</small></div>'
        for g in gs)
    src = f'<a href="{e(reg["u"])}" target="_blank" rel="noopener">{e(reg["t"])} ↗</a>' if reg else "自治体の登録団体の一覧"
    return (f'<section class="emg-pref"><h2 style="font-size:1.15em">{e(pf)}に登録された保護団体（{len(gs)}団体）</h2>'
            f'<p class="emg-note">{src}に載っている団体のうち、公式サイトに譲渡の条件と費用が書いてある団体です。条件と費用は団体ごとにちがい、自治体の窓口より細かいことが多いので、くらべてから申し込んでください（{e(G["checked"])}に確かめた内容。おすすめ順ではありません）。</p>'
            + cards + '</section>')

CAT["extra_after"] = groups_html

# ── 市のページ（/joto/<県>/<市>/。「◯◯市 保護犬 譲渡」「◯◯市 里親 猫」） ──
def chk_html(e, c):
    return '<ul class="jt-chk">' + "".join(
        f'<li class="{"on" if topic_mark(c, w) else ""}">{e(h)}{"" if topic_mark(c, w) else "：書いていない"}</li>' for h, w in TOPICS) + "</ul>"

def _fee(c):
    xs = [x for x in c["conds"] if any(w in x for w in ("円", "無料", "無償"))]
    return "・".join(xs)

def city_faq(c, pref_c):
    city, name = c["city"], c["name"]
    fee = _fee(c)
    tri = [x for x in c["conds"] if any(w in x for w in ("トライアル", "お試し", "体験飼育"))]
    q = [(f"{city}で保護犬・保護猫を迎えるにはどこに申し込みますか？",
          f"{city}の譲渡の窓口は{name}です。申し込める人の条件と流れは公式ページで確かめてください（このページは{J['checked']}に確かめた内容です）。"
          + (f"市の外に住んでいる人や、県のセンターの子を迎えたいときは{pref_c['name']}の案内もご覧ください。" if pref_c else "")),
         (f"{city}の譲渡の条件は？", "公式ページに書いてある主な条件は、" + "、".join(c["conds"][:4]) + "などです。"),
         (f"{city}の譲渡の費用はかかりますか？", (f"公式ページには「{fee}」と書いてあります。" if fee else "公式ページには譲渡の費用は書いてありません。申し込むときにたずねてください。") + "迎えたあとの食事・医療・犬の登録の費用は飼い主の負担です。"),
         (f"{city}の譲渡にトライアル（お試し）はありますか？", ("公式ページには「" + "・".join(tri) + "」と書いてあります。") if tri else "公式ページにはトライアルのことは書いてありません。気になるときは申し込むときにたずねてください。"),
         ("迎える日はどうやって連れて帰りますか？", "キャリーや首輪・リードを持って迎えに行きます。車がないときや大きな犬のときは、ペットタクシーで家まで一緒に帰る方法もあります。")]
    return q

def render_city(ctx, c):
    e, SITE = ctx["e"], ctx["SITE"]
    pf, city = c["pref"], c["city"]
    url = SITE + city_href(c)
    pref_c = next((x for x in ITEMS if x["pref"] == pf and not x.get("city")), None)
    others = [x for x in CITY_ITEMS if x["pref"] == pf and x is not c]
    fq = city_faq(c, pref_c)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in fq)
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    ppage = f"/{SLUG}/{PSLUG[pf]}/"
    title = f"{city}の保護犬・保護猫の譲渡（里親）｜{c['name']}の条件・講習・譲渡会｜ペットのくらし窓口"
    desc = (f"{city}で保護犬・保護猫の里親になりたい人へ。{c['name']}の譲渡の条件（" + "、".join(c["conds"][:2]) + "など）と流れ・譲渡会のリンクを、公式ページで確かめた内容だけでまとめました。")[:150]
    ld = _ld(SITE, url, f"{city}の保護犬・保護猫の譲渡", fq,
             [("ペットタクシー予約窓口", SITE + "/"), (H1, f"{SITE}/{SLUG}/"), (f"{pf}の保護犬・保護猫の譲渡", SITE + ppage), (city, url)])
    lead3 = "".join(f"<li>{e(x)}</li>" for x in c["conds"][:3])
    pref_html = ""
    if pref_c:
        pref_html = (f'<div class="emg-tips"><h4>{e(pf)}の窓口（県のセンター）</h4><p>市の外に住んでいる人や、県のセンターにいる子を迎えたいときは、'
                     f'<a href="{e(pref_c["url"])}" target="_blank" rel="noopener">{e(pref_c["name"])} ↗</a>の案内を見ます。県の条件は、'
                     + "、".join(e(x) for x in pref_c["conds"][:3]) + f'などです（<a href="{ppage}">{e(pf)}の譲渡の窓口をまとめて見る</a>）。</p></div>')
    oth = ("" if not others else '<p class="emg-note">' + e(pf) + "のほかの市："
           + "、".join(f'<a href="{city_href(x)}">{e(x["city"])}</a>' for x in others) + "</p>")
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{SLUG}/">{e(H1)}</a> › <a href="{ppage}">{e(pf)}</a> › {e(city)}</nav>
    <h1><small>{e(c.get('kind') or '')}・公式ページで確かめた条件</small>{e(city)}で保護犬・保護猫を迎える（譲渡・里親）</h1>
    <p class="lede">{e(city)}で保護犬・保護猫の里親になりたいときの窓口は、{e(c['name'])}です。申し込める人の条件・講習・お試し・費用を、公式ページに書いてあることだけで短くまとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips jt-ans" style="margin-top:0"><h4>先に答え：{e(city)}の窓口と主な条件</h4>
      <p><a href="{e(c['url'])}" target="_blank" rel="noopener"><b>{e(c['name'])}</b> ↗</a></p><ul>{lead3}</ul>
      <p class="emg-tips-note">公式ページに書いてあるかどうか（✓＝書いてある。「書いていない」は「ない」ではなく、ページに書いていないという意味）</p>{chk_html(e, c)}</div>
      <p class="emg-free">この案内は無料の情報です。自治体からお金をもらっていません。{e(J['checked'])}に公式ページで確かめた内容を短くまとめたもので、変わることがあります。申し込む前に、必ずリンク先でご確認ください。</p>
      <section class="emg-pref" data-pref="{e(pf)}"><h2 style="font-size:1.15em">{e(city)}の譲渡の窓口</h2>{card(e, dict(c, _nolink=True))}</section>
      <div class="emg-tips"><h4>迎えるまでのふつうの流れ</h4>{flow_html(e)}<p class="emg-tips-note">順番や中身は自治体ごとに少しずつ違います。{e(city)}の流れは上の公式ページで確かめてください。</p></div>
      {pref_html}
      <div class="emg-tips"><h4>申し込む前に確かめること</h4><dl>{before}</dl></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      {oth}
      <p class="emg-note">くわしい条件・費用・保護団体のえらび方は、記事「<a href="/guide/adopt-pet/">保護犬・保護猫を迎えるには</a>」に。掲載の内容の誤りは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>迎える日の移動は、ペットタクシーでも</h2><p>車がないとき、大きな犬のとき、家族と一緒に新しい子を家まで連れて帰れます。</p></div>
    <ul class="other"><li><a href="{ppage}">{e(pf)}の保護犬・保護猫の譲渡</a></li><li><a href="/guide/adopt-pet/">保護犬・保護猫を迎えるには（条件・費用・流れ）</a></li><li><a href="/guide/new-family/">新しい家族を迎えに行くとき</a></li><li><a href="/jichitai/">全国の動物愛護センター・保健所（迷子・登録）</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
""" + ctx["foot_noband"]()

def city_urls(SITE):
    return [SITE + city_href(c) for c in CITY_ITEMS]

def write_cities(ROOT, ctx):
    for c in CITY_ITEMS:
        d = os.path.join(ROOT, city_href(c).strip("/"))
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render_city(ctx, c))
