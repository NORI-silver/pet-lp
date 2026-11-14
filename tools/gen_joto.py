# [B] お金を取らない情報ページ「保護犬・保護猫を迎える（譲渡・里親）」（/joto/ と /joto/<県>/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-14「そうしよう」（保護シェルター・譲渡のページと都道府県ごとのページ）。
# 検索：「犬の里親」月12,100・「保護犬 譲渡会」「保護猫 譲渡会」月6,600・「犬 シェルター」月720・「保護犬 条件」月320（キーワードプランナー 2026-11-14）。
# 読みに来る人が知りたいこと：どこで迎えられるか（県・市の動物愛護センター＝公的なシェルター）、条件（年齢・住まい・家族・講習）、費用、譲渡会。
# 守ること：都道府県・政令市の公式ページで確かめたことだけ（tools/joto.json、項目ごとに公式ページのリンク）。書いていないことは書かない。
# 順位・おすすめなし。電話番号なし。民間の保護団体は第2弾（公式サイトで確かめられた団体だけ）。
# ペットタクシーの話は、下の「迎える日の移動」の枠（taxi_cta.py）と記事 /guide/new-family/ へのリンクだけ（AGENTS.md「分野ごとに話を分ける」）。
import json, os, re
import prefkeep

_D = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(_D, "joto.json"), encoding="utf-8"))
SLUG = "joto"
H1 = "保護犬・保護猫を迎える（譲渡・里親）"
NAME = "保護犬・保護猫の譲渡の窓口"
TITLE = "保護犬・保護猫の譲渡（里親）｜全国の動物愛護センターの条件・費用・譲渡会を都道府県でさがす｜ペットタクシー予約窓口"
DESC = ("保護犬・保護猫の里親になりたい人のために、47都道府県と政令指定都市の動物愛護センター（公的なシェルター）の譲渡の案内を、"
        "公式ページで確かめた条件（年齢・住まい・家族・講習会・トライアル・費用）と一緒にまとめました。譲渡会や県に登録した保護団体の一覧へのリンクも。")

ITEMS = [dict(c, prefs=[c["pref"]]) for c in J["centers"]]

def _kind(c):
    return f'{c["city"]}（政令指定都市）' if c.get("city") else f'{c["pref"]}（都道府県）'

def card(e, c):
    conds = "".join(f"<li>{e(x)}</li>" for x in c["conds"])
    links = "".join(f'<li><a href="{e(l["u"])}" target="_blank" rel="noopener">{e(l["t"])} ↗</a></li>' for l in c.get("links", []))
    return (f'<div class="emg-item emg-co jt-card"><a href="{e(c["url"])}" target="_blank" rel="noopener"><b>{e(c["name"])}</b></a>'
            f'<small>{e(_kind(c))}・{e(c["animals"])}</small>'
            f'<p class="jt-h">公式ページに書いてあること</p><ul class="jt-c">{conds}</ul>'
            + (f'<p class="jt-h">あわせて見る（公式ページ）</p><ul class="jt-l">{links}</ul>' if links else "")
            + f'<small class="sg-src">{e(J["checked"])}に公式ページで確認</small></div>')

CSS = """<style>
.jt-card .jt-h{font-size:.76rem;font-weight:700;color:var(--ink-2);margin:10px 0 2px}
.jt-card ul{margin:0;padding-left:1.2em;font-size:.86rem;line-height:1.7}
.jt-card ul.jt-l{font-size:.84rem}
.emg-item small.sg-src{color:var(--ink-3);font-size:.72rem;margin-top:6px}
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

def faq(n_pref, n_city):
    return [
     ("保護犬・保護猫はどこで迎えられますか？", f"都道府県・政令指定都市・中核市の動物愛護センターや保健所（公的なシェルター）と、民間の保護団体・ボランティアの譲渡会や施設です。このページでは{n_pref}都道府県と{n_city}の政令指定都市の公式の譲渡の案内をまとめています。"),
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
    n_city = sum(1 for c in ITEMS if c.get("city"))
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            cs = rows.get(pf, [])
            inner = "".join(card(e, c) for c in cs) or f'<p class="emg-none">{e(pf)}の譲渡の案内は、まだ載せていません。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    fq = faq(n_pref, n_city)
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in fq)
    ld = _ld(SITE, url, H1, fq, [("ペットタクシー予約窓口", SITE + "/"), (H1, url)])
    return ctx["head"](TITLE, DESC, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › {e(H1)}</nav>
    <h1><small>{n_pref}都道府県・{n_city}政令市の公式の案内</small>{e(H1)}</h1>
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
      <p class="emg-note">中核市（宇都宮市・船橋市・八王子市など）の窓口は、<a href="/jichitai/">全国の動物愛護センター・保健所の一覧</a>にあります。民間の保護団体は、公式サイトで確かめられたところから順に足します。掲載の内容の誤りは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
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
     (f"{pf}で保護犬・保護猫を迎えるにはどこに申し込みますか？", f"{pf}では{names}が譲渡の窓口です（政令指定都市に住んでいる人は市の窓口）。条件と流れはこのページの各窓口の欄と、リンク先の公式ページでご確認ください。"),
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
