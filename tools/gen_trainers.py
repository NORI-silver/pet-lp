# お金を取らない情報ページ「全国のドッグトレーナー・犬のしつけ教室」（/dog-trainer/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「老犬ホーム、トレーナー、シッター」「今どんどん拡大していってよ」（拡充の2つめ）。
# 守ること：教室からお金をもらわない。順位・おすすめをつけない。料金を書かない。電話番号を載せない。
# 公式サイトの情報だけ書く（提供内容・対応エリア・資格・登録番号・所在地）。協会の会員一覧に載っていること（assoc）は一覧の名前つきで書く。
# データ：tools/trainers.json。口コミの星は動物病院のページと同じしくみ（/reviews.js → booking/Code.gs の EMG_REVIEWS）。
from facility_review_links import link as review_link
import json, os
import prefkeep
import facility_cards as FC

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trainers.json"), encoding="utf-8"))

SLUG = "dog-trainer"
H1 = "全国のドッグトレーナー・犬のしつけ教室"
TITLE = "全国のドッグトレーナー・犬のしつけ教室｜出張しつけ・パピークラス・犬の幼稚園・預かりトレーニングを都道府県でさがせる一覧｜ペットタクシー予約窓口"
DESC = "吠える・かむ・トイレ・散歩の困りごとから、全国のドッグトレーナーやしつけ教室を探せます。子犬のパピークラス、出張・幼稚園・預かり・オンラインなどの提供内容、対応地域、資格、口コミを掲載。料金や順位は載せていません。"
ASSOC = {"JAPDT": "日本ペットドッグトレーナーズ協会の会員ドッグトレーナー一覧", "JAHA": "日本動物病院協会のしつけ教室・インストラクター一覧"}

BEFORE = [
 ("しつけの形はいろいろ", "トレーナーが自宅に来る「出張しつけ」、飼い主も一緒に通う「教室」、日中あずけて社会化やトレーニングをしてもらう「犬の幼稚園・保育園」、犬だけをあずける「預かりトレーニング」、「オンライン」。飼い主が一緒に学ぶ形を基本にしている教室が多いです。"),
 ("「登録」を受けている事業者か", "犬をあずかったり訓練したりする事業は、動物の愛護及び管理に関する法律の第一種動物取扱業（訓練・保管）の登録が必要です。多くの教室が公式サイトに登録番号を書いています。この一覧では公式サイトに書いてある番号だけを載せました。"),
 ("資格と協会", "ドッグトレーナーに国家資格はなく、CPDT-KA（国際的な認定）、日本動物病院協会（JAHA）の認定家庭犬しつけインストラクター、JKC公認訓練士などの民間の資格や、協会の会員一覧があります。ここには公式サイトか協会の一覧に載っているものだけを書いています。"),
 ("子犬はいつから", "人やほかの犬、音に慣れやすい社会化期は子犬のうちの短い期間です。ワクチンの接種の状況で参加できる時期が変わるので、教室と動物病院の両方に相談してください。家でできることは記事「子犬のしつけはいつから？」に。"),
 ("問題行動は病気のこともある", "急にトイレを失敗する、触るとかむ、夜に鳴く、といった変化は、痛みや病気、高齢による変化が原因のことがあります。しつけの相談の前に、かかりつけの動物病院で体を診てもらい、強い攻撃性や不安は動物病院の行動診療と合わせて相談してください。"),
 ("最初に確かめること", "どんな方法でしつけるか（ほめて教えるか、体罰や道具を使わないか）、体験や見学ができるか、犬種・年齢・持病で受けられない場合があるか、途中でやめたときの決まり。問題行動（かむ・吠えが強いなど）は、動物病院の行動診療と合わせて相談することもあります。"),
]

# 選ぶときに見る5つ（2026-11-16 Nori「どういう基準でえらべばいいかわからん。いろんな資格があるから」）。
# 一覧と県のページには短くこれだけ。資格のちがい・しつけの考え方のちがいは記事 /guide/choose-dog-trainer/ に。
POINTS = [
 ("doc", "動物取扱業（訓練）の登録", "お金をもらって犬の訓練をするには、出張だけでも登録が要ります。公式サイトか標識に番号があるか。"),
 ("heart", "ほめて教えるか", "ごほうびで教えるのが今の主流です。たたく・首を強く引く・「リーダーになる」を前に出すところは避けます。"),
 ("eye", "体験・カウンセリングがあるか", "犬がこわがっていないか、家での様子を聞いてくれるかを、頼む前に見られます。"),
 ("yen", "料金と回数が書いてあるか", "1回の料金、コースの回数、出張の交通費、やめるときの決まりが分かるか。"),
 ("star", "得意なことが合うか", "子犬・吠え・かみ癖・大型犬など。資格は「何を学んだか」の目安なので、得意なことと合わせて見ます。"),
]
POINTS_MORE = ("資格のちがい（JKC・CPDT-KA・JAHA など）としつけの考え方をくわしく", "/guide/choose-dog-trainer/")
def points_html():
    import visual as _V
    return _V.checks("ドッグトレーナーを選ぶときに見る5つ", POINTS, POINTS_MORE)

import decisionfit

def _card(e, t):
    extra = ""
    if t.get("spec"): extra += f'<small class="emg-spec">{e(t["spec"])}</small>'
    extra += f'<small>提供内容：{e(t["services"])}</small>'
    if t.get("area"): extra += f'<small>対応エリア：{e(t["area"])}</small>'
    if t.get("cert"): extra += f'<small>資格・登録（公式サイトより）：{e(t["cert"])}</small>'
    if t.get("assoc"):
        extra += '<small>協会の一覧：' + e("・".join(ASSOC.get(a, a) for a in t["assoc"].split("・"))) + '</small>'
    if t.get("addr"): extra += f'<small>所在地：{e(t["addr"])}</small>'
    # [B] 2026-11-22 Nori「他のサイトにいって追加で調べることがないように」：公式サイトに書いてある料金・時間・休み・対象・出張費・お支払いもカードに
    fx = {}
    for f in t.get("facts", []):
        if f["k"] in ("料金", "営業・受付時間", "定休日", "対象の犬", "しつけの方法", "出張費", "お支払い", "初回・体験", "駐車場", "用意するもの") and f["k"] not in fx: fx[f["k"]] = f["v"]
    for k in ("料金", "初回・体験", "営業・受付時間", "定休日", "対象の犬", "しつけの方法", "出張費", "お支払い", "駐車場", "用意するもの"):
        if fx.get(k): extra += f'<small>{e(k)}：{e(fx[k])}</small>'
    # [B] 11/16 Nori「ドッグトレーナー歴とか」：公式サイトに書いてある教室だけ
    if t.get("career"): extra += f'<small>トレーナー歴：{e(t["career"])}</small>'
    # 教室の会場が所在地と別のとき（事業者本人のお申し出。エコル 2026-11-09）。タクシーの行き先も会場にする
    if t.get("venue"): extra += f'<small>教室の会場：{e(t["venue"])}</small>'
    tags = FC.trainer_tags(t)
    # 通う場所があるとき（教室・幼稚園・預かり）だけ「ここまでのペットタクシー」を出す（出張だけの事業者の所在地は事務所のことがあるため）
    to = ""
    if t.get("addr") and set(tags) & {"教室・グループ", "幼稚園・保育園", "預かり訓練"}:
        pf = t["prefs"][0]
        to = t.get("venue_addr") or (t["addr"] if t["addr"].startswith(pf) else pf + t["addr"])
    for label, value in decisionfit.rows("dog-trainer", t):
        extra += f'<small>{e(label)}：{e(value)}</small>'
    rv = review_link("trainer", t)
    return (f'<div class="emg-item emg-co"{decisionfit.attrs("dog-trainer", t)}{FC.attrs(e, "trainer", t, tags, t["name"], to, "教室")}><a href="{e(t["url"])}" target="_blank" rel="noopener"><b>{e(t["name"])}</b></a>'
            f'<small>{e(t["city"])}</small>{extra}'
            + (rv or (f'<div class="emg-score" data-id="{e(t["id"])}"></div>' if t.get("review_query") else "")) + "</div>")

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    rows = {}
    for t in J["trainers"]:
        for pf in t["prefs"]:
            rows.setdefault(pf, []).append(t)
    total = len(J["trainers"])
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            ts = rows.get(pf, [])
            inner = "".join(_card(e, t) for t in ts) or f'<p class="emg-none">{e(pf)}のドッグトレーナー・しつけ教室は、まだ載せていません。見つけしだい足します。近くの県の出張しつけやオンラインに対応している教室もご覧ください。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    faq = [
      ("犬のしつけ教室の料金はいくらですか？", "この一覧には料金を載せていません。出張しつけは1回ごと、教室はコースごと、幼稚園は月ごとの料金が多く、出張の交通費が別のこともあります。それぞれの公式サイトか最初の相談のときにご確認ください。"),
      ("子犬は何か月からしつけ教室に行けますか？", "多くの教室が生後2〜6か月ごろのパピークラスを設けています。ワクチンの接種の状況で参加できる時期が変わるので、教室と動物病院にご相談ください。"),
      ("成犬や保護犬でも相談できますか？", "成犬向けのクラスや問題行動の相談を受けている教室が多くあります。一覧の「提供内容」に書いてあるので、そこから確かめてください。"),
      ("トレーナーはどう選べばいいですか？", "動物取扱業（訓練）の登録があるか、ほめて教えるか、体験やカウンセリングがあるか、料金と回数が書いてあるか、得意なことが合うかの5つで見ます。資格は「何を学んだか」の目安で、JKC・CPDT-KA・JAHA などで中身がちがいます。記事「ドッグトレーナーのえらび方」で、資格としつけの考え方のちがいを表にしています。"),
      ("教室や幼稚園への送り迎えが大変なときは？", "送迎をしている教室もあります。家に来てくれる出張トレーニングを選ぶ方法もあります。"),
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
    <h1><small>全国{total}件・都道府県でしぼりこめます</small>{e(H1)}</h1>
    <p class="lede">吠える、かむ、トイレがうまくいかない、散歩で引っぱる。子犬のうちに教えたいことも、成犬になってからの困りごとも、相談できる人がいます。ドッグトレーナーと犬のしつけ教室を、公式サイトの情報をもとに都道府県ごとにまとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">掲載料はいただいていません。都道府県別の一覧で、順位はつけていません。料金は教室にご確認ください。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {FC.chips(e, FC.TRAINER_CHIPS)}
      {body}
      {points_html()}
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      {FC.biz(e, "ドッグトレーナー・しつけ教室")}
      <p class="emg-note">当サイトとは別の事業者です。提供内容や対応地域は依頼前にご確認ください。口コミは地図サービスの情報で、当サイトの評価ではありません。掲載の訂正・取り下げは<a href="/contact/">お問い合わせ</a>へ。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>教室や幼稚園への送り迎えは、ペットタクシーで</h2><p>車がないとき、大型犬のとき、飼い主さまと一緒に家の前から教室の前まで移動できます。当日の依頼もできます。</p></div>
    <ul class="other"><li><a href="/guide/choose-dog-trainer/">ドッグトレーナーのえらび方</a></li><li><a href="/guide/puppy-class/">子犬のしつけはいつから？社会化期とパピークラス</a></li><li><a href="/guide/dog-behavior-help/">かむ・吠える・トイレの失敗：問題行動の相談先</a></li><li><a href="/dogrun/">全国のドッグラン</a></li><li><a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="/hospital/">条件でさがす動物病院</a></li><li><a href="/guide/large-dog/">大型犬の移動のガイド</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{prefkeep.LIST_JS}
<script src="/reviews.js" defer></script>
{FC.SCRIPT}
""" + ctx["foot_noband"]()

def review_rows():
    """口コミの場所を探すことば（booking/Code.gs の EMG_REVIEWS に足す）。"""
    return [t for t in J["trainers"] if t.get("review_query")]

def urls(SITE):
    return [f"{SITE}/{SLUG}/"]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))

# ── 都道府県ごとのページ（tools/gen_prefpages.py。[B] SEO「ドッグトレーナー ◯◯県」「犬 しつけ教室 ◯◯」） ──
def _has(t, *ws): return any(w in t.get("services", "") for w in ws)
def _facts(rs):
    n = len(rs)
    return [f"出張しつけ（家に来てくれる）を公式サイトに書いている：{sum(_has(t, '出張', '訪問', 'お家', 'ご自宅') for t in rs)}／{n}",
            f"教室・グループレッスン：{sum(_has(t, '教室', 'グループ', 'クラス') for t in rs)}／{n}",
            f"犬の幼稚園・保育園：{sum(_has(t, '幼稚園', '保育園') for t in rs)}／{n}",
            f"預かりトレーニング：{sum(_has(t, '預かり') for t in rs)}／{n}",
            f"オンライン：{sum(_has(t, 'オンライン') for t in rs)}／{n}"]
# 無料のしつけ方教室（[B] 2026-11-09。「犬のしつけ教室 無料 福岡」「…無料 岡山」の検索に答える）。
# 都道府県・市の動物愛護センター・保健所が開くことがある、とだけ書き、窓口の公式ページ（tools/jichitai.json）へつなぐ。
# 開く日や回数は年ごとに変わるので、日付や「毎月」などは書かない。
_JI = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jichitai.json"), encoding="utf-8"))
def _public(pf):
    return [x for x in _JI["prefs"] if x["pref"] == pf] + [x for x in _JI["cities"] if x["pref"] == pf]
# 愛知は実際の自治体教室の参加条件と、預かり訓練の料金単位を比較する。
_AICHI_CLASS_CHOICES = (
    '<div class="emg-tips">'
    '<h3>愛知で犬のしつけを学ぶ：自治体の無料教室と有料の預かり訓練</h3>'
    '<p>飼い主が教え方を学びたいなら自治体の教室、愛犬を預けて個別に練習してもらいたいなら日中預かりや合宿型の訓練が候補です。無料相談は無料レッスンとは異なります。</p>'
    '<dl>'
    '<dt>吠え・引っ張りの対処を学ぶ：名古屋市の無料教室</dt>'
    '<dd>名古屋市動物愛護センターの講座では、トレーナーによる実演が見られます。事前申込制で、犬を同伴できる組数は限られます。<a href="https://www.city.nagoya.jp/kurashi/pet/1015473/1015495/1035065/1017801.html">名古屋市の開催・申込案内</a></dd>'
    '<dt>愛犬と実技を練習する：豊田市の無料教室</dt>'
    '<dd>初日は飼い主だけの講義、2日目は愛犬と実技。両日参加と、豊田市での犬の登録・予防接種などが条件です。<a href="https://www.city.toyota.aichi.jp/sumaikankyo/pet/pet/1073805/1078837/1075881.html">豊田市の参加条件・日程</a></dd>'
    '<dt>預けて練習する：日中の定期コースと1か月の訓練の料金例</dt>'
    '<dd><a href="https://kitanagoya-ds.com/">きたなごやドッグスクール</a>の日中預かりは週1回（月4回）25,000円。<a href="https://www.inunogakuen.com/">愛知県の犬のしつけ学園</a>の預かり訓練は1か月69,500円（税込）で、相談・カウンセリングは無料です。料金例は2026年11月25日時点。</dd>'
    '</dl>'
    '<p>預かりを選ぶ前に、日帰りか宿泊か、家に帰ってから飼い主が練習を続ける方法も教えてもらえるかを確認しておくと比べやすくなります。</p></div>'
)

def _free_class(e, pf):
    ws = _public(pf)
    if not ws: return ""
    li = "".join(f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener">{e(x["name"])} ↗</a>' + (f'（{e(x["city"])}）' if x.get("city") else "") + "</li>" for x in ws)
    local = _AICHI_CLASS_CHOICES if pf == "愛知県" else ""
    return local + (f'<div class="emg-tips"><h4>{e(pf)}の無料の「犬のしつけ方教室」は、県や市の窓口へ</h4>'
            f'<p>県や市の動物愛護センター・保健所が、無料の「犬のしつけ方教室」や吠え・かみつきの相談を開いていることがあります。'
            f'日程や参加の条件（狂犬病の予防注射・混合ワクチンなど）は年ごとに変わるので、下の公式ページでたしかめてください。</p><ul>{li}</ul></div>')
def _fee(pf, rs):
    pr = sorted([(t["name"], f) for t in rs for f in t.get("facts", []) if f["k"] == "料金" and f.get("yen")], key=lambda x: x[1]["yen"])
    if len(pr) < 2:
        return "出張しつけは1回ごと、教室はコースごとが多く、出張の交通費が別のこともあります。それぞれの公式サイトでご確認ください。"
    return (f"{pf}で公式サイトに料金を書いている{len(pr)}件では、1回のレッスン（多くは1時間）が{pr[0][1]['yen']:,}円〜{pr[-1][1]['yen']:,}円です。"
            "初回のカウンセリング料や出張の交通費が別になる教室と、初回にふくむ教室があります。くわしくはこのページの「料金・条件をくらべる」の表をご覧ください。")
def _faq(pf, rs, n):
    home = sum(_has(t, '出張', '訪問', 'お家', 'ご自宅') for t in rs)
    return [
     (f"{pf}で家に来てくれるドッグトレーナーはいますか？", f"この一覧の{pf}の{n}件のうち、出張しつけ（家に来てくれる形）を公式サイトに書いているのは{home}件です。対応エリアは一覧でご確認ください。"),
     (f"{pf}で子犬のパピークラスはありますか？", "子犬向けのクラスは、一覧の「提供内容」に書いてあります。ワクチンの接種の状況で参加できる時期が変わるので、教室と動物病院の両方にご相談ください。"),
     (f"{pf}で無料の犬のしつけ教室はありますか？", f"{pf}や市の動物愛護センター・保健所が、無料の「犬のしつけ方教室」を開いていることがあります。開く日や申し込み方法は年ごとに変わるので、このページの一覧の下にある、県や市の窓口の公式ページでたしかめてください。"),
     ("料金はいくらですか？", _fee(pf, rs)),
     ("教室への送り迎えが大変なときは？", "送迎をしている教室もあります。家に来てくれる出張トレーニングを選ぶ方法もあります。"),
    ]
CAT = dict(slug=SLUG, name="ドッグトレーナー・しつけ教室", unit="件", h1=H1, items=J["trainers"], card=_card, checked=J["checked"], reviews=True,
  title_word="ドッグトレーナー・犬のしつけ教室", title_tail="出張しつけ・教室・幼稚園・預かり",
  desc_tail="出張しつけ・教室・犬の幼稚園・預かりトレーニング・オンラインのどれをしているか、対応エリア・資格と、口コミの星と、無料のしつけ方教室を開くことがある県や市の窓口を載せています。料金は公式サイトにある教室だけ。順位なし。",
  lede=lambda pf, n: f"吠える、かむ、トイレ、散歩の引っぱり。{pf}で犬のしつけを相談できるドッグトレーナーと教室を{n}件まとめました。家に来てくれる出張しつけ、通う教室、犬の幼稚園など、公式サイトに書いてある提供内容だけを載せています。",
  facts=_facts, faq=_faq, before_title="ドッグトレーナー・しつけ教室をえらぶときに確かめること", before=BEFORE,
  taxi_h="教室や幼稚園への送り迎えは、ペットタクシーで", taxi_p="車がないとき、大型犬のとき、飼い主さまと一緒に家の前から教室の前まで移動できます。",
  links=[("ドッグトレーナーのえらび方", "/guide/choose-dog-trainer/"), ("子犬のしつけはいつから？", "/guide/puppy-class/"), ("問題行動の相談先", "/guide/dog-behavior-help/"), ("全国のドッグラン", "/dogrun/")])

# 2026-11-22：件数は足りても中身が薄い県（新しい薄いページは作らない。全国のページと近くの県には載る）。中身を足したら外す
CAT["no_page"] = ("秋田県", "福井県", "高知県", "熊本県", "佐賀県", "山形県", "山梨県", "富山県")
CAT["table"] = [("出張", lambda t: "○" if _has(t, "出張", "訪問", "お家", "ご自宅") else ""), ("教室", lambda t: "○" if _has(t, "教室", "グループ", "クラス") else ""), ("幼稚園", lambda t: "○" if _has(t, "幼稚園", "保育園") else ""), ("預かり", lambda t: "○" if _has(t, "預かり") else ""), ("オンライン", lambda t: "○" if _has(t, "オンライン") else ""), ("市区町村", lambda t: t.get("city", ""))]
CAT["fac_chips"] = lambda e, pf: FC.chips(e, FC.TRAINER_CHIPS, pf)
CAT["extra_after"] = _free_class
# [B] 11/15 GSC「犬しつけ教室 預かり」（愛知・福岡）：預かりの料金と出張の地域も表に出す
CAT["fact_cols"] = [("料金", ("料金",)), ("預かり", ("預かり",)), ("初回・体験", ("初回・体験",)), ("出張費・地域", ("出張費", "対応エリア")), ("対象の犬", ("対象の犬",)), ("しつけの方法", ("しつけの方法",))]
CAT["price_title"] = "1回のレッスンの料金（公式サイトの表示どおり）"
# [B] 11/10：「埼玉 犬のようちえん」「出張 ドッグトレーナー 福岡」などで表示されるので、題名に出張・幼稚園・預かりの件数（公式サイトに書いてある数）を出す
def _title(pf, rs, n):
    home = sum(_has(t, '出張', '訪問', 'お家', 'ご自宅') for t in rs)
    kg = sum(_has(t, '幼稚園', '保育園') for t in rs)
    az = sum(_has(t, '預かり') for t in rs)
    parts = [f"出張しつけ{home}件" if home else "", f"犬の幼稚園{kg}件" if kg else "", f"預かり{az}件" if az else ""]
    # [B] 11/13：題名は多くの飼い主さんの悩みと「あきらめずに済むこと」を先に（Nori 11/12「ペインポイントとなんの断念を解決するものなのか」）
    return f"{pf}のドッグトレーナー・犬のしつけ教室{n}件｜吠え・かみ癖・トイレの悩みに。" + (f"家に来てくれる出張しつけ{home}件" if home else "教室・犬の幼稚園の一覧") + "｜ペットタクシー予約窓口"
CAT["title_fn"] = _title
CAT["before_html"] = lambda e, pf: points_html()
CAT["fac_biz"] = lambda e: FC.biz(e, "ドッグトレーナー・しつけ教室")
