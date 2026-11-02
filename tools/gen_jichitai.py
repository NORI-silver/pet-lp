# お金を取らない情報ページ「ペットの迷子・犬の登録・引取りの窓口」（/jichitai/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「全部マネタイズじゃなくていい。SEO的なコンテンツでもいい」「どんどん進めて」。
# 守ること：公的な情報源だけ（環境省の自治体連絡先一覧と、各自治体の公式ページ）。電話番号は載せない。
# データ：tools/jichitai.json（都道府県47・政令指定都市20・中核市62。担当の分け方は環境省の一覧に合わせた）。
import json, os
import prefkeep

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jichitai.json"), encoding="utf-8"))

SLUG = "jichitai"
TITLE = "ペットの迷子・犬の登録・引取りの窓口｜全国の動物愛護センター・保健所の一覧（47都道府県・129自治体）｜ペットタクシー予約窓口"
DESC = "犬や猫が迷子になったとき、保護したとき、犬の登録や狂犬病の予防注射、引っ越し、飼えなくなったときの相談先を、全国47都道府県と政令指定都市・中核市の動物愛護センター・保健所、都道府県警察の公式ページでまとめた無料の一覧です。窓口ごとに受け付けていることと、迷子のときにすることもわかります。"

# どこに連絡するか（どれも法律と各自治体の案内に書いてあること）
WHERE = [
 ("迷子の犬・猫をさがしている", "下の一覧の<b>動物愛護センター・保健所</b>（住んでいる所と、いなくなった所の両方）と、<b>警察</b>（遺失届）。市区町村の清掃の担当や近くの動物病院にも。くわしくは<a href=\"/guide/lost-pet/\">ペットが迷子になったら</a>（<a href=\"/guide/lost-cat/\">猫のさがし方</a>・<a href=\"/guide/lost-dog/\">犬のさがし方</a>・<a href=\"/guide/lost-flyer/\">チラシの作り方</a>）。"),
 ("迷子の犬・猫を見つけた・保護した", "首輪や鑑札がある子は<b>警察</b>へ。飼い主の分からない子は<b>動物愛護センター・保健所</b>に引き取りを求めることもできます。くわしくは<a href=\"/guide/found-pet/\">迷子の犬・猫を保護したら</a>。"),
 ("犬を飼い始めた（登録）・狂犬病の予防注射", "お住まいの<b>市区町村</b>。登録は一生に1回、予防注射は毎年1回です。くわしくは<a href=\"/guide/dog-registration/\">犬の登録と狂犬病の予防注射</a>。"),
 ("引っ越した・犬が亡くなった", "お住まいの<b>市区町村</b>に30日以内に届け出（引っ越しは新しい住所の市区町村へ）。マイクロチップを入れている子は、その登録の変更も。くわしくは<a href=\"/guide/moving-with-pet/\">ペットと引っ越すときの手続き</a>、<a href=\"/sougi/\">ペットが亡くなったら</a>。"),
 ("飼えなくなった・引取りの相談", "下の一覧の<b>動物愛護センター・保健所</b>。いきなり連れていくのではなく、まずは相談から。引き取りは有料のことが多く、理由によっては断られることもあります。くわしくは<a href=\"/guide/cant-keep-pet/\">ペットを飼えなくなったときの相談先</a>。"),
 ("夜間・休日に具合が悪い", "<a href=\"/hospital/night/\">夜間・救急の動物病院</a>へ。移動の手段がないときは<a href=\"/emergency/\">緊急のときの連絡先</a>も。"),
]

# 窓口ごとに受け付けていること（環境省・警察庁・厚生労働省・自治体の案内から）
ROLES = [
 ("動物愛護センター・保健所（都道府県・政令指定都市・中核市）",
  "迷子の届け出と、保護された犬・猫の情報（収容情報のページ）／保護された子の返還／飼い主の分からない犬・猫の引き取り／飼えなくなったときの相談と引き取り／新しい飼い主への譲渡（譲渡会）／けがをした犬・猫の収容／ペットショップなど動物取扱業の登録"),
 ("市区町村（区役所・市役所・町村役場）",
  "犬の登録と鑑札／狂犬病の予防注射の済票と集合注射／引っ越し・飼い主の変更・亡くなったときの届け出（30日以内）／道路で亡くなった犬・猫の引き取り（清掃事務所・環境事業センターなど）"),
 ("警察（警察署・交番）",
  "迷子の犬・猫の遺失届（多くの道府県はオンラインでも）／首輪や鑑札のある犬・猫を拾ったときの届け出／明らかに捨てられている動物の通報"),
 ("環境省のマイクロチップのデータベース",
  "マイクロチップの登録、飼い主の変更（オンライン400円など）、住所・連絡先の変更と亡くなったときの届け出（無料）"),
]

# 都道府県警察の落とし物の届け出・検索（警察庁「落とし物の届出・検索」のページにあるリンク。2026年11月2日に確認）
NPA_URL = "https://www.npa.go.jp/bureau/soumu/ishitsubutsu/ishitsu-todokedekensaku.html"
POLICE = {
 "東京都": ("警視庁「落とし物・忘れ物」", "https://www.keishicho.metro.tokyo.lg.jp/sodan/otoshimono/index.html"),
 "大阪府": ("大阪府警察の落とし物の公表（遺失届は警察署・交番の窓口で）", "http://www.otoshimono.police.pref.osaka.jp/"),
}

def _card(e, d, sub=""):
    links = "".join(f'<small>迷子・保護：<a href="{e(l["u"])}" target="_blank" rel="noopener">{e(l["t"])}</a></small>' for l in d["links"])
    return (f'<div class="emg-item emg-co"><a href="{e(d["url"])}" target="_blank" rel="noopener"><b>{e(d["name"])}</b></a>'
            f'<small>{e(sub)}</small>{links}</div>')

def _police(e, pf):
    t, u = POLICE.get(pf, (f"{pf}警察の遺失届・落とし物の検索（警察庁のページから{pf}を選ぶ）", NPA_URL))
    return f'<p class="emg-sum">警察：<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></p>'

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    P = {p["pref"]: p for p in J["prefs"]}
    C = {}
    for c in J["cities"]:
        C.setdefault(c["pref"], []).append(c)
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            cs = C.get(pf, [])
            if cs:
                names = "・".join(c["city"] for c in cs)
                note = (f'<p class="emg-sum">{e(pf)}では、{e(names)}にお住まいの方は市の窓口、それ以外の市町村にお住まいの方は{e(pf)}の窓口です'
                        f'（{len(cs) + 1}つの窓口）。犬の登録・予防注射・引っ越しの届け出は、どこにお住まいでも市区町村です。</p>')
            else:
                note = f'<p class="emg-sum">{e(pf)}では、迷子・保護・引き取りの相談はどの市町村も{e(pf)}の窓口です。犬の登録・予防注射・引っ越しの届け出は市町村です。</p>'
            inner = _card(e, P[pf], f"{pf}の窓口") + "".join(_card(e, c, f'{c["city"]}（{c["kind"]}）の窓口') for c in cs)
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{note}{inner}{_police(e, pf)}</section>\n'
    where = "".join(f"<dt>{e(t)}</dt><dd>{d}</dd>" for t, d in WHERE)
    roles = "".join(f"<tr><th>{e(t)}</th><td>{e(d)}</td></tr>" for t, d in ROLES)
    faq = [
      ("迷子の犬・猫は、どこに連絡すればいいですか？", "住んでいる所と、いなくなった所の動物愛護センター・保健所（政令指定都市・中核市なら市の窓口）と、警察（遺失届）です。あわせて、市区町村の清掃の担当と近くの動物病院にも連絡しておくと安心です。このページの一覧から、各自治体の迷子の情報のページに行けます。"),
      ("保健所と動物愛護センターは、どちらに連絡すればいいですか？", "自治体によって、動物愛護センターが受け持つ地域と、保健所が受け持つ地域があります。このページの一覧は、住んでいる都道府県・市の窓口の公式ページにつながっているので、そこで受け持ちを確かめてください。"),
      ("保護された子は、いつまで待っていてもらえますか？", "保護してから飼い主をさがす期間は自治体ごとに決まっていて、すぎると新しい飼い主さがしなどに回ることがあります。日数は自治体ごとに違うので、いなくなったらできるだけ早く届け出てください。"),
      ("保護された子を迎えに行くときは、何がいりますか？", "飼い主と分かるもの（写真、鑑札やマイクロチップの番号）と本人確認の書類です。返還には手数料がかかることが多く、金額や必要なものは自治体ごとに違うので、行く前に窓口で確かめてください。"),
      ("迷子の犬を保護しました。警察と保健所のどちらに届けますか？", "首輪や鑑札がある、飼われていたと思われる犬は、警察に届けます。飼い主の分からない犬・猫は、動物愛護センター・保健所に引き取りを求めることもできます。"),
      ("犬の登録や狂犬病の予防注射は、どこでしますか？", "お住まいの市区町村です。登録は飼い始めてから30日以内に一生に1回、予防注射は毎年4月1日〜6月30日の間に1回です。"),
      ("猫にも登録はありますか？", "猫には犬のような登録の決まりはありません。ただ、ペットショップなどから迎えた猫はマイクロチップが入っていることがあり、飼い主の変更登録が必要です。"),
      ("飼えなくなったら、保健所は必ず引き取ってくれますか？", "必ずではありません。年をとった・病気になったという理由や、新しい飼い主をさがす取り組みを先にしていないときなどは、断ることができると法律で決められています。まずは窓口に相談してください。"),
    ]
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    guides = [("ペットが迷子になったら：すぐにすること・届け出先・さがし方", "/guide/lost-pet/"),
              ("迷子の猫のさがし方", "/guide/lost-cat/"),
              ("迷子の犬のさがし方", "/guide/lost-dog/"),
              ("迷子のチラシの作り方", "/guide/lost-flyer/"),
              ("迷子の犬・猫を見つけた・保護したら", "/guide/found-pet/"),
              ("マイクロチップの登録を確かめる・変更する", "/guide/microchip/"),
              ("犬の登録と狂犬病の予防注射（いつ・どこで・いくら）", "/guide/dog-registration/"),
              ("ペットと引っ越すときの手続き", "/guide/moving-with-pet/"),
              ("ペットを飼えなくなったときの相談先", "/guide/cant-keep-pet/"),
              ("ペットが亡くなったら（火葬・葬儀と自治体の受付）", "/sougi/")]
    guides_html = "".join(f'<li><a href="{u}">{e(t)}</a></li>' for t, u in guides)
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "ペットの迷子・犬の登録・引取りの窓口", "item": url}]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, indent=1) + "\n</script>"
    return ctx["head"](TITLE, DESC, url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › ペットの迷子・犬の登録・引取りの窓口</nav>
    <h1><small>全国47都道府県・政令指定都市・中核市（129自治体）</small>ペットの迷子・犬の登録・引取りの窓口</h1>
    <p class="lede">「うちの子がいなくなった」「迷子の犬を保護した」「犬の登録はどこで？」「引っ越したら何を届ける？」。ペットのことで役所に相談したいとき、どこに連絡すればいいかと、全国の動物愛護センター・保健所の公式ページ、都道府県警察の落とし物の窓口をまとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips" style="margin-top:0"><h4>いますぐ知りたいこと</h4><dl>{where}</dl></div>
      <div class="emg-tips"><h4>窓口ごとに受け付けていること</h4>
      <div class="tbl"><table><thead><tr><th>窓口</th><th>おもに受け付けていること</th></tr></thead><tbody>{roles}</tbody></table></div>
      <p class="emg-tips-note">迷子・保護・引き取りは都道府県（政令指定都市・中核市は市）、犬の登録と予防注射は市区町村、と受け持ちが分かれています。迷子のときは、動物愛護センター・保健所と警察の両方に届け出てください。見つけた人がどちらに届けるか分からないからです。</p></div>
      <p class="emg-free">都道府県・政令指定都市・中核市が、それぞれ動物愛護の窓口（動物愛護センター・保健所）を持っています。政令指定都市・中核市にお住まいの方は市の窓口、それ以外の市町村の方は都道府県の窓口です。都道府県をえらぶと、その県の窓口と警察の落とし物の窓口が出ます。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>迷子になったら、まずすること</h4><ol>
        <li><b>すぐにさがし始める</b><br>猫は家の中と、家のまわりの狭くて暗い場所（物置、室外機の下、植え込み、縁の下）。犬はいなくなった場所を中心に円をえがくように広げます。</li>
        <li><b>その日のうちに届け出る</b><br>動物愛護センター・保健所（住んでいる所と、いなくなった所）、警察（遺失届）、市区町村の清掃の担当、近くの動物病院。マイクロチップの登録の連絡先がいまのものかも確かめます。</li>
        <li><b>収容情報のページを毎日見る</b><br>東京都は収容期限を7日間としているので、問い合わせの間をあけすぎないように。上の一覧の「迷子・保護」のリンクや、<a href="https://www.env.go.jp/nature/dobutsu/aigo/shuyo/link.html" target="_blank" rel="noopener">環境省の自治体リンク一覧</a>から。となりの市や県も。</li>
        <li><b>チラシ・掲示板・SNSで知らせる</b><br>写真、いなくなった日時と場所、特徴、連絡先（自宅の住所は書かない）。</li>
      </ol><p class="emg-tips-note">さがし方・チラシの書き方・犬と猫のちがい・見つかったあとの手続きは<a href="/guide/lost-pet/">ペットが迷子になったら</a>にまとめています。</p></div>
      <div class="emg-tips"><h4>保護された子を迎えに行くとき</h4><dl>
        <dt>持っていくもの</dt><dd>飼い主と分かるもの（写真、鑑札やマイクロチップの番号）と、本人確認の書類。リードやキャリーも。</dd>
        <dt>手数料</dt><dd>返還には手数料がかかることが多く、金額は自治体ごとに違います。行く前に窓口に確かめてください。</dd>
        <dt>迎えに行ったあと</dt><dd>警察やほかの窓口に出した届け出を取り下げ、動物病院で一度みてもらうと安心です。動物愛護センターは駅から遠いこともあるので、移動はケージごと乗れる車が便利です。</dd>
      </dl></div>
      <div class="emg-tips"><h4>手続きと相談のガイド</h4><ul class="other">{guides_html}</ul></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">どの自治体がどの地域を受け持つかは、環境省の<a href="{e(J["source"])}" target="_blank" rel="noopener">地方自治体連絡先一覧</a>に合わせています。リンク先は各自治体と警察の公式ページです（{e(J["checked"])}に確認）。ページの場所や受付の方法は変わることがあるので、つながらないときは自治体のサイトの中でさがしてください。電話番号は各自治体のページでご確認ください。掲載の内容の誤りは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>保護された子のお迎えや、通院の移動に</h2><p>動物愛護センターや動物病院への移動は、ペットタクシーを予約できます。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    <ul class="other"><li><a href="/hospital/">条件でさがす動物病院</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li><li><a href="/guide/hospital/">動物病院への通院の送迎ガイド</a></li><li><a href="/dogrun/">全国の公営ドッグラン</a></li></ul>
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
