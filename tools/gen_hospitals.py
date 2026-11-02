# お金を取らない情報ページ「条件でさがす動物病院」（/hospital/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「病院は？全部マネタイズじゃなくていい。SEO的なコンテンツでもいい」「全国で」「口コミもつけて」。
# 守ること：病院からお金をもらわない。順位や「おすすめ」をつけない。電話番号は載せない。公式サイトで確かめたことだけ書く。
# データ：夜間・救急＝tools/emergency.json（緊急タブと同じ）、往診・猫専門・エキゾチック・大型犬の設備＝tools/hospitals.json。
import json, os

HOSP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospitals.json"), encoding="utf-8"))

# 条件ごとのページ。slug は /hospital/<slug>/
CONDS = [
 dict(slug="night", short="夜間・救急", h1="夜間・救急の動物病院", src="emg",
      title="夜間・救急の動物病院｜全国47都道府県から探せる一覧（受付時間つき）｜ペットタクシー予約窓口",
      desc="夜間や休日に診てもらえる救急の動物病院を、全国47都道府県から探せます。病院の名前・受付時間・どんな病院か・所在地と公式サイトへのリンクをまとめた無料の一覧です。電話番号や受け入れは、行く前に必ず公式サイトでご確認ください。",
      lede="夜中に具合が悪くなったとき、どこに行けばいいのか。各地の夜間・救急の動物病院を、受付時間と一緒にまとめました。行く前に必ず電話で受け入れを確かめてください。",
      tips=[("まず電話を", "夜間の病院は手術中や混み合っていて受け入れられないことがあります。症状・いつからか・種類と体重・年齢を伝え、受け入れてもらえるか確かめてから出かけてください。"),
            ("持っていくもの", "かかりつけの診察券やお薬手帳、飲んでいる薬、吐いたものや便の写真、保険証があれば保険証。"),
            ("移動の手段がないとき", "<a href=\"/emergency/\">緊急の搬送をしている会社</a>に直接ご連絡ください。急ぎでない通院は、<a href=\"/#form\">ペットタクシー</a>を前もって頼めます。")]),
 dict(slug="visit", short="往診", h1="往診専門の動物病院（自宅に来てくれる）", src="visit",
      title="往診専門の動物病院｜自宅に来てくれる獣医さんを全国から探せる一覧（対応エリアつき）｜ペットタクシー予約窓口",
      desc="病院に連れて行くのがむずかしい老犬・大型犬・猫のために、自宅に来て診てくれる往診専門の動物病院を全国から探せます。往診の対応エリア・診てもらえる動物・受付時間と公式サイトへのリンクをまとめた無料の一覧です。",
      lede="寝たきりの子、車や病院が苦手な子、大型犬、多頭飼い。病院に連れて行くのがむずかしいとき、獣医さんに来てもらう選択肢があります。往診を専門にしている病院を、対応エリアと一緒にまとめました。",
      tips=[("往診でできること・できないこと", "診察・注射・点滴・採血・ワクチン・爪切り・看取りの相談などは自宅でできることが多いです。レントゲンや手術、入院が必要なときは病院を紹介されます。"),
            ("料金のしくみ", "多くの病院で「往診料（距離で変わる）＋診察や処置の料金」です。料金はここには書いていません。公式サイトか予約のときに確かめてください。"),
            ("検査や手術で病院へ行くとき", "往診の先生に紹介された病院へ連れて行くときは、<a href=\"/#form\">ペットタクシー</a>で寝たまま移動できます。")]),
 dict(slug="cat", short="猫専門", h1="猫専門の動物病院", src="cat",
      title="猫専門の動物病院｜猫だけを診る病院を全国から探せる一覧（診療時間つき）｜ペットタクシー予約窓口",
      desc="犬のいない待合室で、猫のことをよく知る先生に診てもらいたい。猫だけを診療している猫専門の動物病院を、全国から探せます。所在地・診療時間と公式サイトへのリンクをまとめた無料の一覧です。",
      lede="病院の待合室で犬に会うだけで固まってしまう子、病院が大の苦手な子。猫だけを診る病院なら、待合室も診察室も猫のためにつくられています。公式サイトに「猫専門」と書いている病院だけをまとめました。",
      tips=[("猫専門の病院のよいところ", "待合室に犬がいない、猫の体に合わせた道具や入院室がある、猫の病気（腎臓病・甲状腺・口内炎など）を多く診ている、といった点を各病院の公式サイトが挙げています。"),
            ("連れて行くとき", "キャリーは上が開くタイプだと、診察台に移すときの負担が少なくなります。家のにおいのついたタオルを入れ、キャリーに布をかけて外が見えないようにすると落ち着く子が多いです。"),
            ("移動がむずかしいとき", "キャリーの中で鳴き続ける子、電車が無理な子は、<a href=\"/guide/cat/\">猫の移動のガイド</a>も参考に。<a href=\"/#form\">ペットタクシー</a>なら家の前から病院の前まで移動できます。")]),
 dict(slug="exotic", short="エキゾチックアニマル", h1="エキゾチックアニマルの専門の動物病院（うさぎ・鳥・爬虫類など）", src="exotic",
      title="エキゾチックアニマル専門の動物病院｜うさぎ・鳥・ハムスター・爬虫類を診てくれる病院を全国から探せる一覧｜ペットタクシー予約窓口",
      desc="うさぎ・鳥・ハムスター・フェレット・爬虫類などのエキゾチックアニマルを専門に診ている動物病院を、全国から探せます。診てもらえる動物・所在地・診療時間と公式サイトへのリンクをまとめた無料の一覧です。",
      lede="犬や猫の病院では診てもらえないことがある、うさぎ・鳥・ハムスター・フェレット・爬虫類。公式サイトにエキゾチックアニマルを専門に、あるいは中心に診ていると書いている病院だけをまとめました。診てもらえる動物の種類は病院ごとに違うので、行く前に確かめてください。",
      tips=[("連れて行く前に確かめること", "診てもらえる動物の種類（うさぎだけ、鳥と小動物だけ、など）と、予約が必要かどうか。多くの病院が予約制です。"),
            ("移動のとき", "小さな動物は温度の変化に弱いので、キャリーをタオルで包み、夏は保冷剤、冬はカイロを布ごしに。鳥はかごごと布でおおうと落ち着きます。"),
            ("遠くの病院に行くとき", "専門の病院は数が少なく、遠くまで行くことがあります。電車がむずかしいときは<a href=\"/#form\">ペットタクシー</a>も使えます（乗せられる動物は会社ごとに違います）。")]),
 dict(slug="large", short="大型犬の設備", h1="大型犬の設備がある動物病院（大型犬用の入院室・診察台など）", src="large",
      title="大型犬の設備がある動物病院｜大型犬用の入院室・昇降式の診察台がある病院を全国から探せる一覧｜ペットタクシー予約窓口",
      desc="大型犬・超大型犬のために、大型犬用の入院室・診察室・昇降式や電動の診察台などの設備があると公式サイトに書いている動物病院を、全国から探せます。所在地・診療時間と公式サイトへのリンクをまとめた無料の一覧です。",
      lede="体の大きな子は、診察台に乗せるのも、入院室に入るのも一苦労。公式サイトに大型犬のための設備（大型犬用の入院室・広い診察室・昇降式の診察台など）があると書いている病院だけをまとめました。ほかの病院でも大型犬は診てもらえます。",
      tips=[("行く前に確かめること", "体重と犬種を伝え、入院や手術になったとき対応できるかを確かめておくと安心です。40kgを超える超大型犬は事前の相談を求める病院もあります。"),
            ("持ち上げられないとき", "歩けない大型犬は、大きめのバスタオルや毛布で担架のように2人で運べます。車への乗せおろしがむずかしいときは、<a href=\"/guide/large-dog/\">大型犬の移動のガイド</a>も参考に。"),
            ("通院の移動", "大型犬が乗れる車がないとき、<a href=\"/#form\">ペットタクシー</a>で病院の前まで移動できます（大型犬を乗せられるかは会社ごとに違います）。")]),
]

def _rows(cond, emg):
    """都道府県 → その県の病院の一覧。"""
    out = {}
    if cond["src"] == "emg":
        for pf, lst in emg["hospitals"].items():
            out[pf] = list(lst)
    else:
        for h in HOSP[cond["src"]]:
            for pf in h["prefs"]:
                out.setdefault(pf, []).append(h)
    return out

def item_html(e, cond, h):
    """1病院のカード。名前は公式サイトへのリンク。口コミの星は緊急タブと同じしくみ（/reviews.js）。"""
    spec = f'<small class="emg-spec">{e(h["spec"])}</small>' if h.get("spec") else ''
    extra = ''
    if cond["src"] == "visit":
        extra += f'<small>往診エリア：{e(h["area"])}</small><small>診てもらえる動物：{e(h["animals"])}</small>'
    elif h.get("animals"):
        extra += f'<small>診てもらえる動物：{e(h["animals"])}</small>'
    if h.get("addr"):
        extra += f'<small>所在地：{e(h["addr"])}</small>'
    return (f'<div class="emg-item emg-co"><a href="{e(h["url"])}" target="_blank" rel="noopener"><b>{e(h["name"])}</b></a>'
            f'<small>{e(h["city"])}・{e(h["hours"])}</small>{spec}{extra}'
            + (f'<div class="emg-score" data-id="{e(h["id"])}"></div>' if h.get("review_query") else '') + '</div>')

def render_cond(cond, ctx):
    """条件ページ1枚のHTML。ctx は gen_areas.py の関数と値（head, foot, e, area_links, SITE, EMG, emg_regions, emg_opts）。"""
    e, SITE = ctx["e"], ctx["SITE"]
    url = f'{SITE}/hospital/{cond["slug"]}/'
    rows = _rows(cond, ctx["EMG"])
    total = len({h["id"] for v in rows.values() for h in v})
    body = ''
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            hs = rows.get(pf, [])
            inner = ''.join(item_html(e, cond, h) for h in hs) or f'<p class="emg-none">{e(pf)}の{e(cond["short"])}の動物病院は、まだ載せていません。見つけしだい足します。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    tips = ''.join(f'<dt>{e(t)}</dt><dd>{d}</dd>' for t, d in cond["tips"])
    others = ''.join(f'<li><a href="/hospital/{c["slug"]}/">{e(c["short"])}の動物病院</a></li>' for c in CONDS if c["slug"] != cond["slug"])
    checked = ctx["EMG"]["checked"] if cond["src"] == "emg" else HOSP["checked"]
    ld = '<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
      {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
      {"@type":"ListItem","position":2,"name":"条件でさがす動物病院","item":SITE+"/hospital/"},
      {"@type":"ListItem","position":3,"name":cond["h1"],"item":url}]}, ensure_ascii=False, indent=1) + '\n</script>'
    return ctx["head"](cond["title"], cond["desc"], url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/hospital/">条件でさがす動物病院</a> › {e(cond["short"])}</nav>
    <h1><small>全国{total}件・都道府県でしぼりこめます</small>{e(cond["h1"])}</h1>
    <p class="lede">{e(cond["lede"])}</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。病院からお金をもらっていません。順番は都道府県ごとで、おすすめ順や点数順ではありません。料金や受け入れは、それぞれの病院に直接おたずねください。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      <p class="emg-sum">ほかの条件：</p><ul class="other" style="justify-content:flex-start">{others}</ul>
      {body}
      <div class="emg-tips"><h4>{e(cond["short"])}の病院にかかるときに</h4><dl>{tips}</dl>
      <p class="emg-tips-note">ここに書いたのは一般的な心がけです。ペットの様子にあわせて、病院の指示にしたがってください。</p></div>
      <p class="emg-note">当サイトとは別の病院です（{e(checked)}に公式サイトで確かめた情報）。診療時間や対応は変わることがあるので、行く前・頼む前に必ずリンク先でご確認ください。口コミの星と本文は地図サービスから取り寄せたもので、当サイトの評価ではありません。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>病院への移動は、ペットタクシーで</h2><p>通院や退院のお迎えなど、前もって決まっている移動は、ペットタクシーを予約できます。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    <ul class="other"><li><a href="/guide/hospital/">動物病院への通院の送迎ガイド</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li></ul>
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
<script src="/reviews.js" defer></script>
""" + ctx["foot_noband"]()

def render_hub(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = SITE + "/hospital/"
    counts = {c["slug"]: len({h["id"] for v in _rows(c, ctx["EMG"]).values() for h in v}) for c in CONDS}
    cards = ''.join(f'<li><a href="/hospital/{c["slug"]}/"><b>{e(c["h1"])}</b><span>全国{counts[c["slug"]]}件。{e(c["lede"].split("。")[0])}。</span></a></li>' for c in CONDS)
    ld = '<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
      {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
      {"@type":"ListItem","position":2,"name":"条件でさがす動物病院","item":url}]}, ensure_ascii=False, indent=1) + '\n</script>'
    return ctx["head"]("条件でさがす動物病院（夜間・救急／往診／猫専門）｜全国47都道府県｜ペットタクシー予約窓口",
      "夜間・救急、自宅に来てくれる往診専門、猫だけを診る猫専門。条件に合う動物病院を全国47都道府県から探せる無料の一覧です。公式サイトで確かめた受付時間・所在地と、口コミの星をまとめています。", url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › 条件でさがす動物病院</nav>
    <h1><small>全国47都道府県・無料</small>条件でさがす動物病院</h1>
    <p class="lede">「夜中に診てくれる病院は？」「寝たきりだから家に来てほしい」「猫だけの病院がいい」。そんなときに、公式サイトで確かめた病院の一覧を条件ごとにまとめました。病院からお金はもらわず、順位もつけていません。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <ul class="gcards">{cards}</ul>
    <p class="emg-note" style="margin-top:18px">それぞれのページで都道府県をしぼりこめます。まだ載っていない県や病院は、見つけしだい足していきます。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>病院への移動は、ペットタクシーで</h2><p>家の前から病院の前まで、飼い主さまと一緒に。お迎えの場所と行き先を入れると、条件に合う会社と料金の目安が出ます。</p></div>
    <ul class="other"><li><a href="/guide/hospital/">動物病院への通院の送迎ガイド</a></li><li><a href="/guide/senior/">シニア犬・シニア猫、介護中の子の移動</a></li><li><a href="/guide/cat/">猫の移動のガイド</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
""" + ctx["foot_noband"]()

def review_rows():
    """口コミの場所を探すことば（booking/Code.gs の EMG_REVIEWS に足す）。"""
    return [h for k in ("visit", "cat", "exotic", "large") for h in HOSP[k] if h.get("review_query")]

def urls(SITE):
    return [SITE + "/hospital/"] + [f'{SITE}/hospital/{c["slug"]}/' for c in CONDS]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, "hospital"), exist_ok=True)
    open(os.path.join(ROOT, "hospital", "index.html"), "w", encoding="utf-8").write(render_hub(ctx))
    for c in CONDS:
        d = os.path.join(ROOT, "hospital", c["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render_cond(c, ctx))
