# [A] 運営者と掲載の基準（/about/）。Nori 2026-11-16「信頼されるサイトにする」：
# 運営者が誰か・何を載せるか（出どころ）・並び順の決め方（お金で変わらない）・情報の時点・誤りの報告を1ページに。
# どのページの下からも portal.py の短い表示（TRUST）でここへ来られる。誇張しない：いましていることだけを書く。
# 運営者の表記は AGENTS.md のとおり「ペットのくらし窓口（ペットタクシーのサービス名は「ペットタクシー予約窓口」）」だけ。
import json

SLUG = "about"
TITLE = "運営者と掲載の基準｜ペットのくらし窓口"
DESC = "ペットのくらし窓口の運営者、載せている情報の出どころ、並び順の決め方（お金で順位は変わりません）、情報の時点、誤りのお知らせ先をまとめています。"

ROWS = [
    ("👤", "運営者", "ペットのくらし窓口（ペットタクシーのサービス名は「ペットタクシー予約窓口」）。ご連絡は<a href=\"/contact/\">お問い合わせフォーム</a>からどうぞ。"),
    ("🧭", "このサイトでできること", "動物病院・預け先・しつけ・老犬ホーム・葬儀・自治体の窓口・避難など、ペットとのくらしの情報を都道府県や市区町村でさがせます。ペットタクシーは、条件に合う会社をさがして空き状況と料金を問い合わせられます。どれも無料です。"),
    ("💴", "お金と順位", "掲載料はいただいていません。順位を売ることもしません。お金で並び順が変わることはありません。サイトに広告は載せていません。"),
]

BASIS = [
    ("📄", "出どころ", "施設・会社の公式サイト、自治体の公式ページ、獣医師会などが公開している一覧に書いてあることをもとに載せています。各ページに出どころへのリンクと「◯年◯月◯日時点」を書いています。"),
    ("🚫", "書いていないことは載せない", "公式サイトなどに書いていない項目は、推測で埋めずに載せません。「受け入れない」と書いていないことを「できない」とはしません。"),
    ("⭐", "口コミ", "口コミの星と本文は、地図サービスから見るたびに取り寄せて、そのまま表示しています。点数を書き写したり、書き換えたりはしていません。"),
    ("☎️", "電話番号", "原則として載せていません。動物病院の「電話する」と緊急の搬送の会社だけは、公式サイトなどに書いてある番号を載せています。"),
    ("💡", "料金", "公式サイトの料金表をもとにした目安です。確定の料金は、それぞれの会社・施設にご確認ください。"),
]

ORDER = [
    ("📍", "施設の一覧", "地域（都道府県・市区町村）ごとに並べ、その中では施設の写真があるもの・公式サイトの情報が多いものを先に出します。条件を選ぶと、合うものを先に出します。さがす欄では、写真がある順・名前順にも並べかえられます。おすすめ順や口コミの点数順ではありません。"),
    ("🚕", "ペットタクシーの候補", "はじめはお店がお迎えの場所に近い順です。料金の安い順・口コミの順にも並べかえられます。問い合わせを送れる会社には社名の横に印が付きます。"),
]

CHECK = [
    ("🔁", "見直し", "ペットタクシー会社は、載せている料金や条件がいまも公式サイトに書いてあるかを毎週照合しています。ほかの施設は、気づいたところから順に見直しています。"),
    ("✉️", "誤りのお知らせ", "内容のまちがい・古い情報・リンク切れは<a href=\"/contact/\">お問い合わせ</a>からお知らせください。施設・会社の方からの訂正や掲載をやめるご依頼も受け付けています。確かめたうえで直します。"),
]

CSS = """<style>
.ab-rows{list-style:none;padding:0;margin:8px 0 18px;border-top:1px solid var(--line,#eadfd5)}
.ab-rows li{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid var(--line,#eadfd5);line-height:1.7;font-size:.95rem}
.ab-rows .i{flex:0 0 1.8em;font-size:1.35rem;line-height:1.3;text-align:center}
.ab-rows b{display:block;font-size:.98rem;margin-bottom:2px}
.ab h2{font-size:1.15rem;margin:22px 0 4px}
</style>"""


def _rows(e, rows):
    return '<ul class="ab-rows">' + "".join(f'<li><span class="i" aria-hidden="true">{i}</span><span><b>{e(t)}</b>{d}</span></li>' for i, t, d in rows) + "</ul>"


def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    ld = '<script type="application/ld+json">\n' + json.dumps([
        {"@context": "https://schema.org", "@type": "AboutPage", "name": "運営者と掲載の基準", "url": url,
         "publisher": {"@type": "Organization", "@id": "https://pet.shiokonbu.com/#org", "name": "ペットのくらし窓口"}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ペットのくらし窓口", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "運営者と掲載の基準", "item": url}]}],
        ensure_ascii=False, indent=1) + "\n</script>"
    return ctx["head"](TITLE, DESC, url, ld).replace("</head>", CSS + "</head>", 1) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットのくらし窓口</a> › 運営者と掲載の基準</nav>
    <h1>運営者と掲載の基準</h1>
    <p class="lede">だれが運営し、どんな基準で載せているかをまとめています。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap ab">
    {_rows(e, ROWS)}
    <h2>載せている情報</h2>
    {_rows(e, BASIS)}
    <h2>並び順の決め方</h2>
    {_rows(e, ORDER)}
    <h2>見直しと、誤りのお知らせ</h2>
    {_rows(e, CHECK)}
    <p style="font-size:.85rem;color:#5f6368">サービスの決まりは<a href="/terms/">利用規約</a>、個人情報の扱いは<a href="/#privacy">個人情報の取り扱い</a>にあります。</p>
  </div>
</section>
</main>
""" + ctx["foot_noband"]()


def urls(SITE):
    return [f"{SITE}/{SLUG}/"]


def write_all(ROOT, ctx):
    import os
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))
