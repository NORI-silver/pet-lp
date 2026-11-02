# お金を取らない情報ページ「ペットが亡くなったら（火葬・葬儀・霊園）」（/sougi/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「葬儀・霊園のページを作る」。
# 守ること：民間の葬儀社・霊園の名前は載せない（順位・おすすめなし）。自治体の公式ページだけにリンク。電話番号なし。
# 言い方はやさしく（「死体」などのことばは自分の文では使わない。ペットは家族）。データ：tools/sougi.json（県庁所在地、東京都は新宿区）。
import json, os
import prefkeep

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sougi.json"), encoding="utf-8"))

SLUG = "sougi"
TITLE = "ペットが亡くなったら｜火葬・葬儀・霊園の選び方と自治体の受付（全国の県庁所在地）｜ペットタクシー予約窓口"
DESC = "大切なペットが亡くなったときに、まずすること、自治体に頼む・民間のペット葬儀や霊園に頼む・自宅に埋めるの違い、犬の死亡届とマイクロチップの手続き、全国の県庁所在地の受付ページをまとめた無料の案内です。"

FIRST = [
 ("体をととのえる", "まぶたや口をそっと閉じ、手足をやさしく曲げて、眠っているような姿にしてあげます。体をふいて、毛をととのえます。"),
 ("涼しい場所に寝かせる", "箱やかごにタオルを敷いて寝かせ、保冷剤やドライアイスをタオルでくるんで、おなかや首のまわりを冷やします。夏は特に早めに。"),
 ("見送りの方法を決める", "自治体に頼む、民間のペット葬儀・霊園に頼む、自宅の庭に埋める、のどれにするかを家族で話し合います（下の表）。急がなくて大丈夫です。"),
 ("手続きをする", "犬は30日以内に市区町村へ死亡届。マイクロチップが入っている子は、その登録の死亡の届け出も。"),
]

WAYS = [
 ("自治体に頼む", "市区町村が引き取る、または火葬場・清掃工場へ持ち込む方法です。費用は無料〜数千円のところが多く、ほかの子と一緒に火葬（合同火葬）して、お骨は返ってこないのがふつうです。市によっては、斎場に動物用の火葬炉があり、お骨を返してもらえるところもあります。下の一覧で、お住まいの地域の案内をご確認ください。"),
 ("民間のペット葬儀・霊園に頼む", "ひとりだけで火葬する（個別火葬）、家族が立ち会ってお骨を拾う、霊園や納骨堂に納める、などを選べます。家まで火葬の車が来るところもあります。料金や内容は会社ごとに大きく違います。"),
 ("自宅の庭に埋める", "自分の土地であれば埋めることができます。深めに掘り、においや動物に掘り返されないようにします。公園・河川敷・山など、自分の土地ではない場所に埋めてはいけません。"),
]

CHECK = [
 "料金に何が含まれるか（火葬・お骨つぼ・お迎え・休日や夜の料金など）。あとから足される料金がないか",
 "火葬の方法（合同／個別／立ち会い）と、お骨が返ってくるか",
 "霊園・納骨堂に納めるときの年間の管理料と、やめるときの扱い",
 "家まで来る火葬の車のときは、どこで火葬するか（近所への配慮）",
 "ペット霊園の設置に市の許可がいる地域もあります（京都市・新潟市・秋田市などに条例があります）",
]

def _card(e, c):
    return (f'<div class="emg-item emg-co"><a href="{e(c["u"])}" target="_blank" rel="noopener"><b>{e(c["city"])}：{e(c["t"])}</b></a>'
            f'<small>{e(c["city"])}の公式ページ</small></div>')

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    rows = {c["pref"]: c for c in J["cities"]}
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            c = rows.get(pf)
            inner = _card(e, c) if c else f'<p class="emg-none">{e(pf)}の案内は、まだ載せていません。お住まいの市町村のサイトで「ペット 亡くなった」と検索すると見つかることがあります。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    first = "".join(f"<li><b>{e(t)}</b><br>{e(d)}</li>" for t, d in FIRST)
    ways = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in WAYS)
    check = "".join(f"<li>{e(t)}</li>" for t in CHECK)
    faq = [
      ("ペットが亡くなったら、どこに連絡すればいいですか？", "自治体に頼むときは、お住まいの市区町村（清掃の担当や斎場）です。民間のペット葬儀・霊園に頼むときは、その会社です。犬は30日以内に市区町村へ死亡届を出します。"),
      ("自治体に頼むと、お骨は返ってきますか？", "ほかの子と一緒に火葬するため、返ってこないのがふつうです。斎場の動物用の火葬炉で、お骨を返してもらえる市もあります。お住まいの市区町村の案内でご確認ください。"),
      ("犬の死亡届は必要ですか？", "はい。狂犬病予防法で、犬が亡くなったら30日以内に市区町村へ届け出ることになっています。鑑札と注射済票を返すように言われることがあります。マイクロチップが入っている子は、その登録の死亡の届け出もします。"),
      ("猫や小さな動物も、自治体で受け付けてもらえますか？", "多くの市区町村で、犬・猫のほか、うさぎや小鳥などの小さな動物も受け付けています。受け付ける動物の大きさや種類は自治体ごとに違います。"),
    ]
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "ペットが亡くなったら", "item": url}]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, indent=1) + "\n</script>"
    return ctx["head"](TITLE, DESC, url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › ペットが亡くなったら</nav>
    <h1><small>火葬・葬儀・霊園と、自治体の受付（全国）</small>ペットが亡くなったら</h1>
    <p class="lede">長い時間を一緒に過ごした家族とのお別れは、とてもつらいものです。あわてなくて大丈夫です。まずすること、見送りの方法のちがい、手続き、全国の自治体の案内をまとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips" style="margin-top:0"><h4>まずすること</h4><ol>{first}</ol></div>
      <div class="emg-tips"><h4>見送りの方法</h4><dl>{ways}</dl></div>
      <div class="emg-tips"><h4>民間のペット葬儀・霊園に頼むときに確かめること</h4><ul>{check}</ul>
      <p class="emg-tips-note">このページでは、民間の葬儀社や霊園の名前は載せていません（おすすめや順位もつけていません）。</p></div>
      <p class="emg-free">自治体の受け付け方（引き取り・持ち込み・斎場での火葬・費用）は、市区町村ごとに違います。下の一覧は各都道府県の県庁所在地（東京都は新宿区。23区は区ごと）の公式ページです。ほかの市町村にお住まいの方は、お住まいの市町村のサイトでご確認ください。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">{e(J["checked"])}に各自治体の公式ページで確かめた情報です。受け付けの方法や費用は変わることがあるので、必ずリンク先でご確認ください。掲載の内容の誤りは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>ほかの窓口の案内</h2><p>ペットのことで自治体に相談したいときの窓口や、動物病院の一覧もまとめています。</p></div>
    <ul class="other"><li><a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="/hospital/">条件でさがす動物病院</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li></ul>
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
