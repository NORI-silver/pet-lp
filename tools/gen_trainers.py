# お金を取らない情報ページ「全国のドッグトレーナー・犬のしつけ教室」（/dog-trainer/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「老犬ホーム、トレーナー、シッター」「今どんどん拡大していってよ」（拡充の2つめ）。
# 守ること：教室からお金をもらわない。順位・おすすめをつけない。料金を書かない。電話番号を載せない。
# 公式サイトで確かめたことだけ書く（提供内容・対応エリア・資格・登録番号・所在地）。協会の会員一覧に載っていること（assoc）は一覧の名前つきで書く。
# データ：tools/trainers.json。口コミの星は動物病院のページと同じしくみ（/reviews.js → booking/Code.gs の EMG_REVIEWS）。
import json, os
import prefkeep
import facility_cards as FC

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trainers.json"), encoding="utf-8"))

SLUG = "dog-trainer"
H1 = "全国のドッグトレーナー・犬のしつけ教室"
TITLE = "全国のドッグトレーナー・犬のしつけ教室｜出張しつけ・犬の幼稚園・預かりトレーニングを都道府県でさがせる一覧｜ペットタクシー予約窓口"
DESC = "吠える・かむ・トイレ・散歩の引っぱりなど、犬のしつけを相談できるドッグトレーナーと犬のしつけ教室を、都道府県ごとにまとめた無料の一覧です。公式サイトで確かめた提供内容（出張しつけ・教室・犬の幼稚園・預かりトレーニング・オンライン）・対応エリア・資格と、口コミの星を載せています。料金や順位は載せていません。"
ASSOC = {"JAPDT": "日本ペットドッグトレーナーズ協会の会員ドッグトレーナー一覧", "JAHA": "日本動物病院協会のしつけ教室・インストラクター一覧"}

BEFORE = [
 ("しつけの形はいろいろ", "トレーナーが自宅に来る「出張しつけ」、飼い主も一緒に通う「教室」、日中あずけて社会化やトレーニングをしてもらう「犬の幼稚園・保育園」、犬だけをあずける「預かりトレーニング」、「オンライン」。飼い主が一緒に学ぶ形を基本にしている教室が多いです。"),
 ("「登録」を受けている事業者か", "犬をあずかったり訓練したりする事業は、動物の愛護及び管理に関する法律の第一種動物取扱業（訓練・保管）の登録が必要です。多くの教室が公式サイトに登録番号を書いています。この一覧では公式サイトに書いてある番号だけを載せました。"),
 ("資格と協会", "ドッグトレーナーに国家資格はなく、CPDT-KA（国際的な認定）、日本動物病院協会（JAHA）の認定家庭犬しつけインストラクター、JKC公認訓練士などの民間の資格や、協会の会員一覧があります。ここには公式サイトか協会の一覧で確かめたものだけを書いています。"),
 ("子犬はいつから", "人やほかの犬、音に慣れやすい社会化期は子犬のうちの短い期間です。ワクチンの接種の状況で参加できる時期が変わるので、教室と動物病院の両方に相談してください。家でできることは記事「子犬のしつけはいつから？」に。"),
 ("問題行動は病気のこともある", "急にトイレを失敗する、触るとかむ、夜に鳴く、といった変化は、痛みや病気、高齢による変化が原因のことがあります。しつけの相談の前に、かかりつけの動物病院で体を診てもらい、強い攻撃性や不安は動物病院の行動診療と合わせて相談してください。"),
 ("最初に確かめること", "どんな方法でしつけるか（ほめて教えるか、体罰や道具を使わないか）、体験や見学ができるか、犬種・年齢・持病で受けられない場合があるか、途中でやめたときの決まり。問題行動（かむ・吠えが強いなど）は、動物病院の行動診療と合わせて相談することもあります。"),
]

def _card(e, t):
    extra = ""
    if t.get("spec"): extra += f'<small class="emg-spec">{e(t["spec"])}</small>'
    extra += f'<small>提供内容：{e(t["services"])}</small>'
    if t.get("area"): extra += f'<small>対応エリア：{e(t["area"])}</small>'
    if t.get("cert"): extra += f'<small>資格・登録（公式サイトより）：{e(t["cert"])}</small>'
    if t.get("assoc"):
        extra += '<small>協会の一覧：' + e("・".join(ASSOC.get(a, a) for a in t["assoc"].split("・"))) + '</small>'
    if t.get("addr"): extra += f'<small>所在地：{e(t["addr"])}</small>'
    tags = FC.trainer_tags(t)
    # 通う場所があるとき（教室・幼稚園・預かり）だけ「ここまでのペットタクシー」を出す（出張だけの事業者の所在地は事務所のことがあるため）
    to = ""
    if t.get("addr") and set(tags) & {"教室・グループ", "幼稚園・保育園", "預かり訓練"}:
        pf = t["prefs"][0]
        to = (t["addr"] if t["addr"].startswith(pf) else pf + t["addr"])
    return (f'<div class="emg-item emg-co"{FC.attrs(e, "trainer", t, tags, t["name"], to, "教室")}><a href="{e(t["url"])}" target="_blank" rel="noopener"><b>{e(t["name"])}</b></a>'
            f'<small>{e(t["city"])}</small>{extra}'
            + (f'<div class="emg-score" data-id="{e(t["id"])}"></div>' if t.get("review_query") else "") + "</div>")

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
      ("トレーナーはどう選べばいいですか？", "どんな方法でしつけるか（ほめて教えるか、道具や体罰を使わないか）、資格や協会の一覧、動物取扱業の登録、体験で犬がこわがっていないか、の4つで確かめます。記事「ドッグトレーナーのえらび方」にまとめました。"),
      ("教室や幼稚園への送り迎えが大変なときは？", "送迎をしている教室もあります。車がないときや大型犬のときは、ペットタクシーで家の前から教室の前まで移動できます。"),
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
    <p class="lede">吠える、かむ、トイレがうまくいかない、散歩で引っぱる。子犬のうちに教えたいことも、成犬になってからの困りごとも、相談できる人がいます。ドッグトレーナーと犬のしつけ教室を、公式サイトで確かめた内容だけで都道府県ごとにまとめました。えらぶときに確かめたいことも一緒にどうぞ。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。教室からお金をもらっていません。順番は都道府県ごとで、おすすめ順や点数順ではありません。料金は載せていないので、それぞれの教室に直接おたずねください。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {FC.chips(e, FC.TRAINER_CHIPS)}
      {body}
      <div class="emg-tips"><h4>ドッグトレーナー・しつけ教室をえらぶときに確かめること</h4><dl>{before}</dl>
      <p class="emg-tips-note">ここに書いたのは一般的な目安です。犬の様子にあわせて、教室や動物病院に相談してください。</p></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      {FC.biz(e, "ドッグトレーナー・しつけ教室")}
      <p class="emg-note">当サイトとは別の事業者です（{e(J["checked"])}に公式サイトで確かめた情報。協会の一覧は各協会のサイトで確かめました）。提供内容や対応エリアは変わることがあるので、頼む前に必ずリンク先でご確認ください。口コミの星と本文は地図サービスから取り寄せたもので、当サイトの評価ではありません。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>教室や幼稚園への送り迎えは、ペットタクシーで</h2><p>車がないとき、大型犬のとき、飼い主さまと一緒に家の前から教室の前まで移動できます。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
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
def _faq(pf, rs, n):
    home = sum(_has(t, '出張', '訪問', 'お家', 'ご自宅') for t in rs)
    return [
     (f"{pf}で家に来てくれるドッグトレーナーはいますか？", f"この一覧の{pf}の{n}件のうち、出張しつけ（家に来てくれる形）を公式サイトに書いているのは{home}件です。対応エリアは一覧でご確認ください。"),
     (f"{pf}で子犬のパピークラスはありますか？", "子犬向けのクラスは、一覧の「提供内容」に書いてあります。ワクチンの接種の状況で参加できる時期が変わるので、教室と動物病院の両方にご相談ください。"),
     ("料金はいくらですか？", "この一覧には料金を載せていません。出張しつけは1回ごと、教室はコースごとが多く、出張の交通費が別のこともあります。"),
     ("教室への送り迎えが大変なときは？", "車がないときや大型犬のときは、ペットタクシーで家の前から教室の前まで移動できます。"),
    ]
CAT = dict(slug=SLUG, name="ドッグトレーナー・しつけ教室", unit="件", h1=H1, items=J["trainers"], card=_card, checked=J["checked"], reviews=True,
  title_word="ドッグトレーナー・犬のしつけ教室", title_tail="出張しつけ・教室・幼稚園・預かり",
  desc_tail="出張しつけ・教室・犬の幼稚園・預かりトレーニング・オンラインのどれをしているか、対応エリア・資格と、口コミの星を載せています。料金や順位は載せていません。",
  lede=lambda pf, n: f"吠える、かむ、トイレ、散歩の引っぱり。{pf}で犬のしつけを相談できるドッグトレーナーと教室を{n}件まとめました。家に来てくれる出張しつけ、通う教室、犬の幼稚園など、公式サイトで確かめた提供内容だけを載せています。",
  facts=_facts, faq=_faq, before_title="ドッグトレーナー・しつけ教室をえらぶときに確かめること", before=BEFORE,
  taxi_h="教室や幼稚園への送り迎えは、ペットタクシーで", taxi_p="車がないとき、大型犬のとき、飼い主さまと一緒に家の前から教室の前まで移動できます。",
  links=[("ドッグトレーナーのえらび方", "/guide/choose-dog-trainer/"), ("子犬のしつけはいつから？", "/guide/puppy-class/"), ("問題行動の相談先", "/guide/dog-behavior-help/"), ("全国のドッグラン", "/dogrun/")])

CAT["table"] = [("出張", lambda t: "○" if _has(t, "出張", "訪問", "お家", "ご自宅") else ""), ("教室", lambda t: "○" if _has(t, "教室", "グループ", "クラス") else ""), ("幼稚園", lambda t: "○" if _has(t, "幼稚園", "保育園") else ""), ("預かり", lambda t: "○" if _has(t, "預かり") else ""), ("オンライン", lambda t: "○" if _has(t, "オンライン") else ""), ("市区町村", lambda t: t.get("city", ""))]
CAT["fac_chips"] = lambda e, pf: FC.chips(e, FC.TRAINER_CHIPS, pf)
CAT["fac_biz"] = lambda e: FC.biz(e, "ドッグトレーナー・しつけ教室")
