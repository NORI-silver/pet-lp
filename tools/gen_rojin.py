# お金を取らない情報ページ「全国の老犬ホーム・老猫ホーム」（/rojin-home/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「老犬ホーム、トレーナー、シッター」「今どんどん拡大していってよ」（拡充の1つめ）。
# 守ること：施設からお金をもらわない。順位・おすすめをつけない。電話番号を載せない。料金は県のページで、公式サイトに書いてある金額だけ（2026-11-14、出どころと確認日つき）。
# 公式サイトの情報だけ書く（受け入れる動物・見学・登録番号・所在地）。データ：tools/rojin.json。
# 口コミの星は動物病院のページと同じしくみ（/reviews.js → booking/Code.gs の EMG_REVIEWS）。
import json, os, re
import prefkeep
import facility_review_links as RL

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rojin.json"), encoding="utf-8"))

SLUG = "rojin-home"
H1 = "全国の老犬ホーム・老猫ホーム"
TITLE = "老犬ホーム・老猫ホームを探す｜老犬介護・短期・長期預かりと費用｜ペットのくらし窓口"
DESC = "老犬ホームは、シニア犬を預かり、食事や排せつの介助、見守りなどを行う施設です。短期・長期・生涯預かりの違いや費用、受け入れ条件を地域別に比較できます。老猫ホームも探せます。犬の介護施設や猫の介護先を探す方にも。"
CHIBA_DESC = "千葉県でシニア犬や猫を預けられる老犬ホーム・老猫ホームを比較。短期・長期・生涯預かり、大型犬や寝たきりの子の受け入れ、入所金・月額、見学の条件を確認できます。料金は公開されている施設のみ掲載しています。"

BEFORE = [
 ("「登録」を受けた施設か", "老犬ホームは、動物の愛護及び管理に関する法律の第一種動物取扱業（保管・譲受飼養）の登録を受けて営む施設です。登録番号は施設に掲げられ、多くの施設が公式サイトにも書いています。この一覧では公式サイトに書いてある番号だけを載せました。"),
 ("見学で見ること", "日中と夜のスタッフの人数、1人が何頭を見ているか、寝たきりの子の体位変換や床ずれの手当て、散歩や日なたぼっこ、かかりつけの動物病院との連携、面会の方法（来訪・写真・動画・カメラ）。"),
 ("契約の前に聞くこと", "終生の預かりか期限つきか、飼い主が先に亡くなったときの扱い、病気や入院のときの費用の決め方、連絡の頻度、途中で引き取れるか、亡くなったときの見送りの方法。"),
 ("受け入れの条件", "犬だけ・猫だけ、体重や犬種、年齢、ワクチン接種、持病のある子を受けるかは施設ごとに違います。ここには公式サイトに書いてある範囲だけを載せています。"),
 ("「預かり」と「譲り受け」", "飼い主が所有者のまま世話を頼む「保管」と、施設が有償で譲り受けて飼う「譲受飼養」の2つの形があります。終生のお預かりは譲り受けの形になることがあり、その場合は医療の判断やマイクロチップの登録の所有者も施設に移ります。どちらの形かを契約書で確かめてください。"),
 ("費用の見方", "料金の例は、公式サイトに掲載している施設だけ載せています。入所のときの費用、月ごとの費用、医療費・消耗品、終生の一括払いの組み合わせで決まり、犬の大きさや介護の度合いで変わります。見積もりで何を確かめるかは、記事「老犬ホームの費用のしくみ」にまとめました。"),
]

# 一覧に載せる条件（Nori 2026-11-10「それの条件とかもサイトに書いといてね」）。全国のページと県のページの両方に出す。
CRITERIA = [
 "シニアの犬・猫を長期または終生で預かること、寝たきり・看取りまでの介護つきのお預かり、または月ごとの老犬ホームのお預かりをしていることを、施設の公式サイトに今も書いていること。",
 "県の中に施設が少ない県では、近くの県の施設も同じ欄に出しています（所在地の県はカードに書いています）。",
 "施設の公式サイトがあること。情報サイト・まとめサイト・SNSだけの施設は載せていません。",
 "ペットホテルやデイケア（日帰りのお預かり）だけの施設、受け入れをやめた・休んでいる施設は載せません。",
 "書くのは、公式サイトに書いてある所在地・受け入れる動物・料金・時間・見学や面会のきまり・動物取扱業の登録番号などだけです。電話番号・順位は書きません。",
 "施設からお金はもらっていません。載っていない施設もあるので、見つけしだい足します。",
]
def criteria_html(e, pf=None):
    # 運営側の決まりは読む人の役に立たないので、小さく折りたたむ（AGENTS.md「品質の決まり」A2、Nori 2026-11-16）
    return ('<details class="emg-tips pp-fold"><summary>この一覧について</summary><ul>'
            + "".join(f"<li>{e(t)}</li>" for t in CRITERIA) + "</ul></details>")

import decisionfit

def _card(e, h):
    extra = ""
    if h.get("intro"): extra += f'<small class="emg-intro">{e(h["intro"])}</small>'
    if h.get("spec"): extra += f'<small class="emg-spec">{e(h["spec"])}</small>'
    extra += f'<small>受け入れる動物：{e(h["animals"])}</small>'
    # うちの子に合うか（公式サイトの文から。Nori 2026-11-17「自分の子にあてはまるものを探してる」）
    import ownerfit
    ok = [ownerfit.SHORT[k] for k in ("bed", "night", "med", "big") if k in ownerfit.keys("rojin-home", h["url"])[0]]
    if ok: extra += f'<small>こんな子も相談できる：{e("・".join(ok))}</small>'
    if h.get("visit"): extra += f'<small>見学・面会：{e(h["visit"])}</small>'
    if h.get("reg"): extra += f'<small>動物取扱業の登録（公式サイトより）：{e(h["reg"])}</small>'
    if h.get("addr"):
        extra += f'<small>所在地：{e(h["addr"])}</small>'
    # [B] 2026-11-22 Nori「他のサイトにいって追加で調べることがないように」：公式サイトに書いてある料金・条件・時間などもカードに
    for f in h.get("facts", []):
        if (f["k"] in ("料金", "ふくまれるお世話", "別料金", "受け入れ条件", "見学・面会", "病院", "用意するもの", "営業・受付時間", "お支払い", "部屋", "お世話", "1泊・日帰り", "定休日", "駐車場") and not (f["k"] == "見学・面会" and h.get("visit"))) or (f.get("show") and not (f["k"] in ("見学", "面会") and h.get("visit"))):
            extra += f'<small>{e(f["k"])}：{e(f["v"])}</small>'
    for label, value in decisionfit.rows("rojin-home", h):
        extra += f'<small>{e(label)}：{e(value)}</small>'
    fa = f' data-cat="rojin" data-fid="{e(h["id"])}" data-name="{e(h["name"])}"' + (' data-partner="1"' if h.get("partner") else '')  # facility.js（問い合わせ文・提携先へは当サイトから送る）
    review = RL.link("rojin", h, scope="facility")
    if not review and h.get("review_query"):
        review = f'<div class="emg-score" data-id="{e(h["id"])}"></div>'
    return (f'<div class="emg-item emg-co"{decisionfit.attrs("rojin-home", h)}{fa}><a href="{e(h["url"])}" target="_blank" rel="noopener"><b>{e(h["name"])}</b></a>'
            f'<small>{e(h["city"])}</small>{extra}'
            + review + "</div>")

# 県の中に施設が0〜1か所の県は、近くの県の施設も同じ欄に出す（rojin.json の near。「0件」「まだ載せていません」の箱は出さない。2026-11-17）
_BYID = {h["id"]: h for h in J["homes"]}
def _near_html(e, pf):
    ids = J.get("near", {}).get(pf) or []
    hs = [_BYID[i] for i in ids if i in _BYID]
    if not hs: return ""
    others = "・".join(dict.fromkeys(p for h in hs for p in h["prefs"]))
    cards = "".join(_card(e, h).replace('<div class="emg-item emg-co"', '<div class="emg-item emg-co" data-near="1"', 1) for h in hs)
    return f'<p class="emg-near-h" data-near-h style="font-size:.9rem;font-weight:700;color:#3c4043;margin:14px 0 6px">📍 {e(pf)}から近い{e(others)}の施設</p>{cards}'

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    rows = {}
    for h in J["homes"]:
        for pf in h["prefs"]:
            rows.setdefault(pf, []).append(h)
    shown = [h for _lab, _prefs in ctx["emg_regions"] for _pf in _prefs for h in rows.get(_pf, [])]
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            hs = rows.get(pf, [])
            inner = "".join(_card(e, h) for h in hs) + _near_html(e, pf)
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    faq = [
      ("老犬ホームの料金はいくらですか？", "この一覧では、公式サイトで公開されている施設のみ料金の例を載せています。入居のときの費用と月ごとの費用のほかに、医療費や消耗品が別になることがあり、犬の大きさや介護の度合いでも変わります。それぞれの公式サイトか見学のときにご確認ください。"),
      ("老犬ホームと老猫ホームの違いは？", "多くの施設は犬だけを受けています。猫だけ、または犬と猫の両方を受ける施設は、一覧の「受け入れる動物」に書いています。"),
      ("見学の予約から入所の日まで、何を準備すればいいですか？", "見学の予約、かかりつけの先生への相談、ワクチンや薬の書類、いつものフードと寝具、契約書で確かめる項目を、記事「老犬ホームに預ける前の準備」に順番にまとめました。"),
      ("飼い主が先に亡くなったら、どうなりますか？", "終生のお預かりの契約では、飼い主が亡くなったあとも施設が世話を続ける形が多いですが、費用の払い方や連絡先をだれにするかは契約で決めます。自治体の案内でも、だれが世話を引き継ぐかを先に決めておくことがすすめられています。"),
      ("入所の日や面会の日の移動はどうすれば？", "施設によっては送迎をしているところもあるので、まず施設にたずねてみてください。寝たきりの子は、体を支えられるクッションやバスタオルを用意すると安心です。"),
    ]
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    def _rcnt(*ws):
        return sum(1 for h in J["homes"] if any(w in json.dumps(h, ensure_ascii=False) for w in ws))
    n_cat = sum(1 for h in J["homes"] if _cat_ok(h))
    stats_html = ('<div class="emg-tips"><h4>全国の老犬ホーム・老猫ホームのデータ（公式サイトの記載から集計）</h4><dl>'
      f'<dt>掲載数</dt><dd>全国{len(J["homes"])}施設。猫を受け入れる老猫ホームは{n_cat}施設です。</dd>'
      f'<dt>介護の体制</dt><dd>看護師がいると書いている施設は{_rcnt("看護師")}施設、夜間の見守りにふれている施設は{_rcnt("夜間")}施設です。</dd>'
      f'<dt>預かり方</dt><dd>一時預かり・短期に対応する施設は{_rcnt("一時預かり", "短期")}施設、終生預かりは{_rcnt("終生", "生涯")}施設です。</dd>'
      f'<dt>部屋と設備</dt><dd>個室がある施設は{_rcnt("個室")}施設、ドッグランがある施設は{_rcnt("ドッグラン")}施設です。</dd>'
      '</dl><p class="emg-tips-note">件数は公式サイトの記載をもとに数えた目安です。受け入れの実際は施設にご確認ください。</p></div>')
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットのくらし窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": H1, "item": url}]},
      {"@context": "https://schema.org", "@type": "ItemList", "name": H1, "numberOfItems": len(shown),
       "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": h["name"], "url": h["url"]} for i, h in enumerate(shown[:100])]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, separators=(",", ":")) + "\n</script>"
    return ctx["head"](TITLE, DESC, url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットのくらし窓口</a> › {e(H1)}</nav>
    <h1>{e(H1)}</h1>
    <p class="lede">自分で世話ができなくなったとき、介護が夜も続くとき、最後まで安心して暮らせる場所をさがしている方へ。シニアの犬や猫を預かったり介護したりする老犬ホーム・老猫ホームを、公式サイトの情報をもとに都道府県ごとにまとめました。長期・終生か月ごとのお預かりかは施設ごとに違います。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。施設からお金をもらっていません。順番は都道府県ごとで、おすすめ順や点数順ではありません。料金を公開している施設は、料金の例を載せています。実際の費用は施設に直接おたずねください。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      <details class="emg-tips" id="fit-senior-care">
        <summary>うちの子に合う預け先の選び方</summary>
        <dl>
          <dt>家で暮らし続けたい、数時間だけ介護を頼みたい</dt><dd>訪問介護や日帰りのデイケアが候補です。通う負担と、家でしてほしいお世話を分けて考えます。日帰りがあるか、送迎が使えるかは施設に確認します。</dd>
          <dt>飼い主の入院などで、数日〜数週間だけ預けたい</dt><dd>期間を伝え、短期でも普段どおりの介護を頼める施設を探します。薬の回数、夜の見守り、いつもの食事を渡せるかを確認し、可能なら先に日帰りや短い宿泊を試します。</dd>
          <dt>寝たきり・夜鳴きがある、薬が欠かせない</dt><dd>「介護対応」だけで決めず、うちの子に必要な体位交換、排せつの介助、夜の見守り、投薬を一つずつ伝えます。大型犬は体重と立てるかどうかも伝え、夜間のスタッフと急変時の連絡・受診先を確認します。カメラは施設内の見守り用か、家族も映像を見られるかで分けて確認しましょう。<a href="/guide/rojin-home/">見学時に確かめること</a></dd>
          <dt>長期・終生で預けたい</dt><dd>日常の介護に加え、面会の頻度、医療の判断をする人、看取り、契約を途中で終える場合の扱いを確認します。入所金・月額・医療費を分けて比べます。猫は犬の施設と兼用か、猫だけで落ち着ける場所があるかも見学で確認します。<a href="/guide/rojin-home-cost/">費用の内訳</a>・<a href="/guide/roneko-home/">老猫ホームの選び方</a></dd>
        </dl>
        <p class="emg-tips-note">一覧で見つからない条件は、受け入れ不可とは限りません。絞り込みの結果は候補として、空きと実際のお世話の内容を施設に確認してください。</p>
      </details>
      {body}
      <div class="emg-tips" id="rojin-overview"><h2>老犬ホームとは</h2><p>{e(DESC)}</p></div>
      {stats_html}
      {criteria_html(e)}
      <div class="emg-tips"><h4>老犬ホームをえらぶときに確かめること</h4><dl>{before}</dl>
      <p class="emg-tips-note">くわしくは<a href="/guide/rojin-home/">老犬ホーム・老猫ホームを見学するときに確かめること</a>にまとめています。</p></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">当サイトとは別の施設です（{e(J["checked"])}時点の情報）。受け入れや見学の方法は変わることがあるので、頼む前に必ずリンク先でご確認ください。口コミの星と本文は地図サービスから取り寄せたもので、当サイトの評価ではありません。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>入所や面会の日の移動は、ペットタクシーで</h2><p>寝たきりの子や大型犬も、家の前から施設の前まで飼い主さまと一緒に移動できます。当日の依頼もできます。</p></div>
    <ul class="other"><li><a href="/guide/rojin-home/">老犬ホームを見学するときに確かめること</a></li><li><a href="/guide/rojin-home-cost/">老犬ホームの費用のしくみ</a></li><li><a href="/guide/rojin-home-prepare/">預ける前の準備・持ち物・契約</a></li><li><a href="/guide/roneko-home/">老猫ホームのえらび方</a></li><li><a href="/guide/senior/">シニア犬・シニア猫、介護中の子の移動</a></li><li><a href="/hospital/visit/">往診専門の動物病院</a></li><li><a href="/sougi/">ペットが亡くなったら</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{prefkeep.LIST_JS}
<script src="/reviews.js" defer></script>
<script src="/facility.js" defer></script>
""" + ctx["foot_noband"]()

def apply_public_snippets(root):
    # Keep exact list markup intact until the card and finder builders finish.
    # Google can still discover the prefecture links; only nationwide snippet text is restricted.
    p = os.path.join(root, SLUG, "index.html")
    with open(p, encoding="utf-8") as f:
        source = f.read()
    result = re.sub(r'(<section class="emg-pref"[^>]*?)(?<!data-nosnippet)>', r'\1 data-nosnippet>', source)
    result = re.sub(r'(<h3 class="emg-region"[^>]*>)([^<]+)(</h3>)', r'\1<span data-nosnippet>\2</span>\3', result)
    if result != source:
        with open(p, "w", encoding="utf-8") as f:
            f.write(result)

def review_rows():
    """口コミの場所を探すことば（booking/Code.gs の EMG_REVIEWS に足す）。"""
    return [h for h in J["homes"] if h.get("review_query")]

def urls(SITE):
    return [f"{SITE}/{SLUG}/"]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))

# ── 都道府県ごとのページ（tools/gen_prefpages.py。[B] SEO「老犬ホーム ◯◯県」） ──
def _cat_ok(h): return "猫" in h["animals"] and "猫は受けていません" not in h["animals"] and "ペットホテルは猫も" not in h["animals"]  # ペットホテルだけ猫を受ける施設は老猫ホームに数えない（11/9）
def _facts(rs):
    n = len(rs)
    return [f"猫も受けると公式サイトに書いてある施設：{sum(_cat_ok(h) for h in rs)}／{n}",
            f"大型犬について公式サイトに書いてある施設：{sum('大型' in h['animals'] for h in rs)}／{n}",
            f"見学・面会のきまりが公式サイトに書いてある施設：{sum(bool(h.get('visit')) for h in rs)}／{n}",
            f"動物取扱業の登録番号を公式サイトに書いている施設：{sum(bool(h.get('reg')) for h in rs)}／{n}"]
def _fee(pf, rs):
    fs = [(h["name"], f["v"]) for h in rs for f in h.get("facts", []) if f["k"] == "料金"]
    base = "入所の費用・月ごとの費用・医療費の組み合わせで決まり、犬の大きさや介護の度合いでも変わります。見積もりで確かめることは記事「老犬ホームの費用のしくみ」にまとめました。"
    if not fs: return base
    return "公式サイトに書いてある料金は、" + "。".join(f"{n}：{v}" for n, v in fs[:3]) + "。" + base
def _faq(pf, rs, n):
    cities = "、".join(dict.fromkeys(h["city"] for h in rs))
    return [
     (f"{pf}に老犬ホームは何か所ありますか？", f"この一覧では、公式サイトに書いてある{pf}の老犬ホーム・老猫ホームを{n}か所載せています（{cities}）。ここにない施設もあるので、見つけしだい足します。"),
     (f"{pf}で猫を預けられる老猫ホームはありますか？", f"{pf}で猫も受けると公式サイトに書いてある施設は{sum(_cat_ok(h) for h in rs)}か所です。一覧の「受け入れる動物」でご確認ください。"),
     ("料金はいくらですか？", _fee(pf, rs)),
     ("見学や入所の日の移動はどうすれば？", "施設が送迎をしていることもあるので、まず施設にたずねてみてください。"),
    ]
_TITLE_TEST_PREFS = {"静岡県", "埼玉県", "福岡県"}
def _has_fee_examples(rs):
    return any(f.get("k") == "料金" and f.get("v") for h in rs for f in h.get("facts", []))

def _pref_title(pf, rs, n):
    if pf == "千葉県": return "千葉県の老犬ホーム・老猫ホーム｜費用・介護・見学｜ペットのくらし窓口"
    tail = "費用の例・介護・見学" if pf in _TITLE_TEST_PREFS and _has_fee_examples(rs) else "受け入れる動物・見学・登録番号つき"
    return f"{pf}の老犬ホーム・老猫ホーム｜{n}施設の一覧（{tail}）｜ペットのくらし窓口"

def _pref_desc(pf, rs, n):
    if pf == "千葉県":
        return CHIBA_DESC
    return f"{pf}でシニア犬や猫を預けられる老犬ホーム・老猫ホームを探せます。短期・長期預かり、介護や大型犬の受け入れ、見学の条件を比較できます。費用は公開されている施設のみ掲載しています。"

CAT = dict(slug=SLUG, name="老犬ホーム・老猫ホーム", unit="施設", h1=H1, items=J["homes"], card=_card, checked=J["checked"], reviews=True,
  title_word="老犬ホーム・老猫ホーム", title_tail="受け入れる動物・見学・登録番号つき", title_fn=_pref_title, desc_fn=_pref_desc,
  desc_tail="所在地・受け入れる動物（犬・猫・大型犬）・見学のきまり・動物取扱業の登録番号と、口コミの星を載せています。料金は公式サイトに書いてある施設だけ載せています。順位はつけていません。",
  lede=lambda pf, n: f"{pf}で、シニアの犬や猫を預かったり介護したりしてくれる老犬ホーム・老猫ホームを{n}施設まとめました。長期・終生か月ごとのお預かりかは施設ごとに違います。",
  fact_cols=[("料金", ("料金", "料金詳細")), ("別料金", ("別料金",)), ("ふくまれるお世話", ("ふくまれるお世話",)), ("受け入れ条件", ("受け入れ条件",)), ("見学・面会", ("見学・面会",)), ("病院", ("病院",))],
  price_title="月ごとの料金（いちばん小さい区分・公式サイトの表示どおり）",
  facts=_facts, faq=_faq, extra_after=criteria_html, before_title="老犬ホームをえらぶときに確かめること", before=BEFORE,
  taxi_h="見学・入所・面会の移動は、ペットタクシーで", taxi_p="寝たきりの子や大型犬も、飼い主さまと一緒に家の前から施設の前まで移動できます。",
  links=[("老犬ホームの費用のしくみ", "/guide/rojin-home-cost/"), ("老犬ホームに預ける前の準備", "/guide/rojin-home-prepare/"), ("老猫ホームのえらび方", "/guide/roneko-home/"), ("シニア犬・シニア猫、介護中の子の移動", "/guide/senior/"), ("往診専門の動物病院", "/hospital/visit/")])

# 2026-11-22：件数は足りても中身が薄い県（新しい薄いページは作らない。全国のページには載る）。中身を足したら外す
CAT["no_page"] = ('岡山県', '青森県', '山梨県', '愛媛県', '長野県')
CAT["fact_cols"] = [("料金", ("料金", "料金詳細")), ("別料金", ("別料金",)), ("受け入れ条件", ("受け入れ条件",)), ("見学・面会", ("見学・面会",)), ("営業・受付時間", ("営業・受付時間",))]
CAT["table"] = [("猫", lambda h: "○" if _cat_ok(h) else ""), ("大型犬の記載", lambda h: "○" if "大型" in h["animals"] else ""), ("見学・面会の記載", lambda h: "○" if h.get("visit") else ""), ("登録番号", lambda h: "○" if h.get("reg") else ""), ("市区町村", lambda h: h["city"])]

# [B] 2026-11-14「うちの子で見る」：公式サイトに書いてある受け入れる動物で分ける（犬だけ・猫だけ・小型犬だけ）
def _bf_keys(h):
    a = h["animals"]
    k = ["cat"] if _cat_ok(h) else []
    if not a.startswith("猫"):
        k += ["s"] if "小型犬5kg未満" in a else ["s", "m", "l"]
    return k
CAT["bf_keys"] = _bf_keys
CAT["bf_lead"] = "公式サイトに書いてある「受け入れる動物」で分けています（犬だけ・猫だけ・小型犬だけの施設など）。大きさの決まりを書いていない施設は、犬ならどの大きさでも表示します。"

# 千葉の施設の公式案内を同じ選び方で比較。受け入れの可否・夜間の処置・空きは保証しない。
def _chiba_care_examples(e):
    return (
        '<section class="emg-tips" id="chiba-large-dog-care" aria-labelledby="chiba-care-title">'
        '<h2 id="chiba-care-title">千葉で大型犬・超大型犬を預ける：夜間介護と初月費用</h2>'
        '<p>夜に自力で水を飲めないなら、スタッフがいるかだけでなく、夜間にどんな介助をしてもらえるかを確認します。'
        '1か月以上なら、月額に入所金と別料金を足し、初月に支払う額で比べます。</p>'
        '<dl>'
        '<dt>夜の給水や食事の介助を頼みたい：わんにゃんハウス・オレンジ（千葉市中央区）</dt>'
        '<dd>超大型犬も対象。スタッフは夜間も施設にいて、見回りのほか、カルテを確認して自力で食事や水分補給ができない子を介助します。'
        '必要な回数と頻度、体重の上限、介助を含む料金は事前に確認してください。'
        '<a href="https://wannyanhouse-orange.com/faq.html">夜間の介助の出典</a>・'
        '<a href="https://wannyanhouse-orange.com/receive.html">受け入れ・事前相談の案内</a></dd>'
        '<dt>長期で初月費用を知りたい：老犬ホーム ルル（長柄町）</dt>'
        '<dd>25kgの料金区分は入所金22万円と月額22万円で、初月は合計44万円（税込）。'
        '35kgの料金区分は入所金33万円と月額33万円で、初月は合計66万円（税込）。'
        '介護は月額に含まれますが、検査・治療・特別食などは別料金。30kg以上という料金区分は、どの体重でも受け入れられるという意味ではありません。'
        '<a href="https://lulurh.com/menu">入所金・月額の出典</a></dd>'
        '<dt>家族が不在の間だけ預けたい：Dog care house ふみちゃん家（野田市）</dt>'
        '<dd>老犬ホームは原則10歳以上で、3時間から24時間のコースがあります。大型犬の老犬介護は個別相談。'
        'ペットホテルの超大型犬料金を老犬介護の見積もりには使えません。専任の夜勤スタッフの追加が必要な場合は事前相談と別料金です。'
        '<a href="https://dog-fumichanti.com/menu/">受け入れ・別料金の出典</a></dd>'
        '</dl>'
        '<p class="emg-tips-note">2026年11月27日に施設の公式案内を確認。'
        '見学時には、体重・自力で立てるか・夜に必要な介助と回数を伝え、急変時の受診先と見積もりに含む内容を確認してください。'
        '<a href="/guide/rojin-home-prepare/">預ける前の準備</a></p></section>'
    )

CAT["pref_overrides"] = {
    "千葉県": {
        "section": '<p class="emg-tips-note"><a href="#chiba-large-dog-care">大型犬・超大型犬の夜間介護・初月費用を比較する</a></p>',
        "extra_after": _chiba_care_examples,
    },
}
