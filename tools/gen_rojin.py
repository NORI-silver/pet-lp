# お金を取らない情報ページ「全国の老犬ホーム・老猫ホーム」（/rojin-home/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「老犬ホーム、トレーナー、シッター」「今どんどん拡大していってよ」（拡充の1つめ）。
# 守ること：施設からお金をもらわない。順位・おすすめをつけない。料金を書かない。電話番号を載せない。
# 公式サイトで確かめたことだけ書く（受け入れる動物・見学・登録番号・所在地）。データ：tools/rojin.json。
# 口コミの星は動物病院のページと同じしくみ（/reviews.js → booking/Code.gs の EMG_REVIEWS）。
import json, os
import prefkeep

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rojin.json"), encoding="utf-8"))

SLUG = "rojin-home"
H1 = "全国の老犬ホーム・老猫ホーム"
TITLE = "全国の老犬ホーム・老猫ホーム｜都道府県でさがせる一覧（受け入れる動物・見学・登録番号つき）｜ペットタクシー予約窓口"
DESC = "シニアの犬や猫を長期・終生で預かってくれる老犬ホーム・老猫ホームを、都道府県ごとにまとめた無料の一覧です。公式サイトで確かめた所在地・受け入れる動物・見学のきまり・動物取扱業の登録番号と、口コミの星を載せています。料金や順位は載せていません。"

BEFORE = [
 ("「登録」を受けた施設か", "老犬ホームは、動物の愛護及び管理に関する法律の第一種動物取扱業（保管・譲受飼養）の登録を受けて営む施設です。登録番号は施設に掲げられ、多くの施設が公式サイトにも書いています。この一覧では公式サイトに書いてある番号だけを載せました。"),
 ("見学で見ること", "日中と夜のスタッフの人数、1人が何頭を見ているか、寝たきりの子の体位変換や床ずれの手当て、散歩や日なたぼっこ、かかりつけの動物病院との連携、面会の方法（来訪・写真・動画・カメラ）。"),
 ("契約の前に聞くこと", "終生の預かりか期限つきか、飼い主が先に亡くなったときの扱い、病気や入院のときの費用の決め方、連絡の頻度、途中で引き取れるか、亡くなったときの見送りの方法。"),
 ("受け入れの条件", "犬だけ・猫だけ、体重や犬種、年齢、ワクチン接種、持病のある子を受けるかは施設ごとに違います。ここには公式サイトに書いてある範囲だけを載せています。"),
]

def _card(e, h):
    extra = ""
    if h.get("spec"): extra += f'<small class="emg-spec">{e(h["spec"])}</small>'
    extra += f'<small>受け入れる動物：{e(h["animals"])}</small>'
    if h.get("visit"): extra += f'<small>見学・面会：{e(h["visit"])}</small>'
    if h.get("reg"): extra += f'<small>動物取扱業の登録（公式サイトより）：{e(h["reg"])}</small>'
    extra += f'<small>所在地：{e(h["addr"])}</small>'
    return (f'<div class="emg-item emg-co"><a href="{e(h["url"])}" target="_blank" rel="noopener"><b>{e(h["name"])}</b></a>'
            f'<small>{e(h["city"])}</small>{extra}'
            + (f'<div class="emg-score" data-id="{e(h["id"])}"></div>' if h.get("review_query") else "") + "</div>")

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    rows = {}
    for h in J["homes"]:
        for pf in h["prefs"]:
            rows.setdefault(pf, []).append(h)
    total = len(J["homes"])
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            hs = rows.get(pf, [])
            inner = "".join(_card(e, h) for h in hs) or f'<p class="emg-none">{e(pf)}の老犬ホーム・老猫ホームは、まだ載せていません。見つけしだい足します。近くの県の施設も、送迎や面会の方法とあわせてご検討ください。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    faq = [
      ("老犬ホームの料金はいくらですか？", "この一覧には料金を載せていません。入居のときの費用と月ごとの費用のほかに、医療費や消耗品を別に払う施設が多く、犬の大きさや介護の度合いでも変わります。それぞれの公式サイトか見学のときにご確認ください。"),
      ("老犬ホームと老猫ホームの違いは？", "多くの施設は犬だけを受けています。猫だけ、または犬と猫の両方を受ける施設は、一覧の「受け入れる動物」に書いています。"),
      ("入所の日や面会の日の移動はどうすれば？", "寝たきりの子や大型犬は、ペットタクシーで家の前から施設の前まで移動できます。施設によっては送迎をしているところもあるので、まず施設にたずねてみてください。"),
    ]
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": H1, "item": url}]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, indent=1) + "\n</script>"
    return ctx["head"](TITLE, DESC, url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › {e(H1)}</nav>
    <h1><small>全国{total}施設・都道府県でしぼりこめます</small>{e(H1)}</h1>
    <p class="lede">自分で世話ができなくなったとき、介護が夜も続くとき、最後まで安心して暮らせる場所をさがしている方へ。シニアの犬や猫を長期・終生で預かる老犬ホーム・老猫ホームを、公式サイトで確かめた内容だけで都道府県ごとにまとめました。見学で確かめたいことも一緒にどうぞ。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。施設からお金をもらっていません。順番は都道府県ごとで、おすすめ順や点数順ではありません。料金は載せていないので、それぞれの施設に直接おたずねください。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>老犬ホームをえらぶときに確かめること</h4><dl>{before}</dl>
      <p class="emg-tips-note">くわしくは<a href="/guide/rojin-home/">老犬ホーム・老猫ホームを見学するときに確かめること</a>にまとめています。</p></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">当サイトとは別の施設です（{e(J["checked"])}に公式サイトで確かめた情報）。受け入れや見学の方法は変わることがあるので、頼む前に必ずリンク先でご確認ください。口コミの星と本文は地図サービスから取り寄せたもので、当サイトの評価ではありません。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>入所や面会の日の移動は、ペットタクシーで</h2><p>寝たきりの子や大型犬も、家の前から施設の前まで飼い主さまと一緒に移動できます。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    <ul class="other"><li><a href="/guide/rojin-home/">老犬ホームを見学するときに確かめること</a></li><li><a href="/guide/senior/">シニア犬・シニア猫、介護中の子の移動</a></li><li><a href="/hospital/visit/">往診専門の動物病院</a></li><li><a href="/sougi/">ペットが亡くなったら</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{prefkeep.LIST_JS}
<script src="/reviews.js" defer></script>
""" + ctx["foot_noband"]()

def review_rows():
    """口コミの場所を探すことば（booking/Code.gs の EMG_REVIEWS に足す）。"""
    return [h for h in J["homes"] if h.get("review_query")]

def urls(SITE):
    return [f"{SITE}/{SLUG}/"]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))
