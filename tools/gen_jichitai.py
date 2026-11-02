# お金を取らない情報ページ「ペットの迷子・犬の登録・引取りの窓口」（/jichitai/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「全部マネタイズじゃなくていい。SEO的なコンテンツでもいい」「どんどん進めて」。
# 守ること：公的な情報源だけ（環境省の自治体連絡先一覧と、各自治体の公式ページ）。電話番号は載せない。
# データ：tools/jichitai.json（都道府県47・政令指定都市20・中核市62。担当の分け方は環境省の一覧に合わせた）。
import json, os

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jichitai.json"), encoding="utf-8"))

SLUG = "jichitai"
TITLE = "ペットの迷子・犬の登録・引取りの窓口｜全国の動物愛護センター・保健所の一覧（47都道府県・129自治体）｜ペットタクシー予約窓口"
DESC = "犬や猫が迷子になったとき、保護したとき、犬の登録や狂犬病の予防注射、飼えなくなったときの相談先を、全国47都道府県と政令指定都市・中核市の動物愛護センター・保健所の公式ページでまとめた無料の一覧です。どこに連絡すればいいかもわかります。"

# どこに連絡するか（どれも法律と各自治体の案内に書いてあること）
WHERE = [
 ("迷子の犬・猫をさがしている／迷子を保護した", "下の一覧の<b>動物愛護センター・保健所</b>と、<b>警察</b>（さがしているときは遺失届、保護したときは拾得の届け出）。となりの市や県に移っていることもあるので、近くの窓口にも。"),
 ("犬を飼い始めた（登録）・狂犬病の予防注射", "お住まいの<b>市区町村</b>。登録は一生に1回、予防注射は毎年1回です。"),
 ("引っ越した・犬が亡くなった", "お住まいの<b>市区町村</b>に届け出（引っ越しは新しい住所の市区町村へ）。マイクロチップを入れている子は、その登録の変更も。"),
 ("飼えなくなった・引取りの相談", "下の一覧の<b>動物愛護センター・保健所</b>。まずは相談から。引き取りは有料のことが多く、理由によっては断られることもあります。"),
 ("夜間・休日に具合が悪い", "<a href=\"/hospital/night/\">夜間・救急の動物病院</a>へ。移動の手段がないときは<a href=\"/emergency/\">緊急のときの連絡先</a>も。"),
]

STEPS_LOST = [
 ("すぐに、動物愛護センター・保健所に連絡する", "迷子の届け出をすると、似た子が保護されたときに知らせてもらえることがあります。保護されてから飼い主が見つからないまま決まった日数が過ぎると、新しい飼い主さがしなどに回ることがあるので、早いほど安心です。"),
 ("警察に遺失届を出す", "迷子の犬・猫を保護した人が、警察に届け出ることがあるためです。"),
 ("収容情報のページを毎日見る", "多くの自治体が、保護した犬・猫の写真や場所をページに出しています。下の一覧の「迷子」のリンクから見られます。となりの市や県のページも。"),
 ("近所に知らせる", "写真つきのチラシ、動物病院やペットショップへの掲示のお願い。猫は家のすぐ近くに隠れていることが多いので、夜に名前を呼びながら家のまわりをさがしてみてください。"),
]

STEPS_DOG = [
 ("登録（一生に1回）", "犬を飼い始めたら30日以内に（生後90日以内の子犬は、生後90日を過ぎてから30日以内に）、お住まいの市区町村に登録します。鑑札がもらえます（狂犬病予防法）。"),
 ("狂犬病の予防注射（毎年1回）", "毎年4月1日〜6月30日の間に1回。注射済票がもらえます。市区町村の集合注射のほか、動物病院でも受けられます。"),
 ("鑑札と注射済票は首輪に", "迷子になったとき、鑑札の番号から飼い主がわかります。"),
 ("マイクロチップ", "2022年6月1日から、ペットショップやブリーダーで売られる犬・猫にはマイクロチップの装着と登録が義務になりました。迎えた人は、環境省の「犬と猫のマイクロチップ情報登録」で飼い主の変更登録をします。市区町村によっては、マイクロチップの登録が犬の登録の代わりになります（狂犬病予防法の特例制度）。"),
]

def _card(e, d, sub=""):
    links = "".join(f'<small>迷子・保護：<a href="{e(l["u"])}" target="_blank" rel="noopener">{e(l["t"])}</a></small>' for l in d["links"])
    return (f'<div class="emg-item emg-co"><a href="{e(d["url"])}" target="_blank" rel="noopener"><b>{e(d["name"])}</b></a>'
            f'<small>{e(sub)}</small>{links}</div>')

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
            note = ("" if not cs else
                    f'<p class="emg-sum">{e("・".join(c["city"] for c in cs))}にお住まいの方は、市の窓口です。それ以外の市町村は{e(pf)}の窓口です。</p>')
            inner = _card(e, P[pf], f"{pf}の窓口") + "".join(_card(e, c, f'{c["city"]}（{c["kind"]}）の窓口') for c in cs)
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{note}{inner}</section>\n'
    where = "".join(f"<dt>{e(t)}</dt><dd>{d}</dd>" for t, d in WHERE)
    lost = "".join(f"<li><b>{e(t)}</b><br>{e(d)}</li>" for t, d in STEPS_LOST)
    dog = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in STEPS_DOG)
    faq = [
      ("迷子の犬・猫は、どこに連絡すればいいですか？", "住んでいる都道府県の動物愛護センター・保健所（政令指定都市・中核市なら市の窓口）と、警察です。このページの一覧から、各自治体の迷子の情報のページに行けます。"),
      ("犬の登録や狂犬病の予防注射は、どこでしますか？", "お住まいの市区町村です。登録は一生に1回、予防注射は毎年4月1日〜6月30日の間に1回です。"),
      ("猫にも登録はありますか？", "猫には犬のような登録の決まりはありません。ただ、ペットショップなどから迎えた猫はマイクロチップが入っていることがあり、飼い主の変更登録が必要です。"),
    ]
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
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
    <p class="lede">「うちの子がいなくなった」「迷子の犬を保護した」「犬の登録はどこで？」。ペットのことで自治体に相談したいとき、どこに連絡すればいいかと、全国の動物愛護センター・保健所の公式ページをまとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips" style="margin-top:0"><h4>どこに連絡すればいい？</h4><dl>{where}</dl></div>
      <p class="emg-free">都道府県・政令指定都市・中核市が、それぞれ動物愛護の窓口（動物愛護センター・保健所）を持っています。政令指定都市・中核市にお住まいの方は市の窓口、それ以外の市町村の方は都道府県の窓口です。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>迷子になったら、すぐにすること</h4><ol>{lost}</ol></div>
      <div class="emg-tips"><h4>犬を飼い始めたら（登録・予防注射・マイクロチップ）</h4><dl>{dog}</dl>
      <p class="emg-tips-note">手続きの細かいところ（手数料・必要なもの・集合注射の日程）は市区町村ごとに違います。お住まいの市区町村のページでご確認ください。</p></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">どの自治体がどの地域を受け持つかは、環境省の<a href="{e(J["source"])}" target="_blank" rel="noopener">地方自治体連絡先一覧</a>に合わせています。リンク先は各自治体の公式ページです（{e(J["checked"])}に確認）。ページの場所や受付の方法は変わることがあるので、つながらないときは自治体のサイトの中でさがしてください。掲載の内容の誤りは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>保護された子のお迎えや、通院の移動に</h2><p>動物愛護センターや動物病院への移動は、ペットタクシーを予約できます。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    <ul class="other"><li><a href="/hospital/">条件でさがす動物病院</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li><li><a href="/guide/hospital/">動物病院への通院の送迎ガイド</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
<script>
(function(){{
  var sel = document.getElementById("hospPref");
  function apply(){{
    var v = sel.value;
    document.querySelectorAll(".emg-pref").forEach(function(s){{ s.hidden = !!v && s.dataset.pref !== v; }});
    document.querySelectorAll(".emg-region").forEach(function(h){{ h.hidden = !!v; }});
  }}
  sel.addEventListener("change", apply);
  var m = location.hash.match(/^#pref=(.+)$/);
  if (m) {{ try {{ sel.value = decodeURIComponent(m[1]); apply(); }} catch (x) {{}} }}
}})();
</script>
""" + ctx["foot_noband"]()

def urls(SITE):
    return [f"{SITE}/{SLUG}/"]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))
