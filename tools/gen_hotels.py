# [B] SEO：お金を取らない情報ページ「ペットホテル」（全部のペットホテルを載せる。Nori 2026-11-22「全部のペットホテルを載せる」。大型犬OK・猫専用は しぼりこみと印で見せる）（/pet-hotel/、県ごとの /pet-hotel/<県>/）。gen_areas.py が読み込んで使う。
# 「ペットホテル」は全国 月110,000回（キーワードプランナー 2026-11-02）。前は大型犬OK・猫専用だけにしぼっていたが、2026-11-22 から全部を載せる。
# 「大型犬 ペットホテル」「猫 ペットホテル」で来る人のために、タイトル・説明・しぼりこみ・FAQに大型犬OK・猫専用の言葉は残す。
# [C] 条件（large・cat_only・cat・vet・pickup・senior・night_staff・camera・run・max_kg）は公式サイトにはっきり書いてあるときだけ持つ（ない＝不明）。
# 守ること：ホテルからお金をもらわない。順位・おすすめなし。料金は公式サイトに書いてある分だけ。電話番号なし。公式サイトの情報。データ：tools/hotels.json。
from facility_review_links import link as review_link
import visual as _V  # 「見ておく◯つ」は共通の部品（トレーナーと同じ見た目）
import json, os
import gen_grooming

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotels.json"), encoding="utf-8"))

SLUG = "pet-hotel"
H1 = "全国のペットホテル"
TITLE = "ペットホテルを都道府県でさがす｜大型犬OK・猫専用（キャットホテル）・送迎・動物病院併設でしぼれる一覧｜ペットタクシー予約窓口"
DESC = "全国のペットホテルを都道府県ごとにまとめた無料の一覧です。大型犬を泊められるホテル・猫専用のホテル（キャットホテル）・動物病院の併設・送迎・シニアの子・夜のスタッフでしぼりこめます。ペットホテルの料金は公開しているホテルだけ載せ、順位は付けていません。"

CONDS = [("large", "大型犬を泊められる"), ("cat_only", "猫専用のホテル"), ("cat", "猫も泊められる"), ("vet", "動物病院が併設・運営"),
         ("pickup", "送迎がある"), ("senior", "シニア・介護・投薬の子を受ける"), ("night_staff", "夜もスタッフがいる")]
EXTRA = [("camera", "カメラで様子を見られる"), ("run", "ドッグランがある"), ("private_room", "個室")]

BEFORE = [
 ("「登録」を受けたホテルか", "ペットを預かる事業は、動物の愛護及び管理に関する法律の第一種動物取扱業（保管）の登録が必要です。登録番号は店に掲げられ、公式サイトに書いているホテルも多いです。"),
 ("大型犬のとき", "部屋やケージの大きさ、体重の上限、散歩の回数と時間、ほかの犬と一緒に遊ばせるかを確かめてください。はじめての子は短い日数で試してみると安心です。"),
 ("猫のとき", "犬の声やにおいが届かないか、上下に動ける部屋か、トイレと食事の場所が離れているか。猫は環境が変わると食べなくなることがあるので、いつものフードとにおいのついたものを持っていきます。"),
 ("夜とシニアの子", "夜にスタッフがいるか、投薬や持病の子を受けるか、具合が悪くなったときにどの動物病院に連れていくかを、預ける前に決めておきます。"),
 ("持っていくもの・必要な書類", "多くのホテルで、1年以内の混合ワクチンの接種証明と、犬は狂犬病予防注射の証明が必要です。ノミ・ダニの予防を求めるホテルもあります。"),
]

# 「預ける前に見る6つ」（結果のすぐ後ろ。アイコンのカード）。カードの緑のチェックと同じ順・同じ言葉にする
CHECK = [
 ("badge", "動物取扱業（保管）の登録", "登録番号と有効期限が店とサイトに出ているか。「登録一覧にも掲載」は、自治体の公開の一覧でも名前と番号が合ったホテルです。"),
 ("moon", "夜はだれがいるか", "夜もスタッフが泊まりこむのか、夜はカメラで見るだけなのか。"),
 ("cross", "具合が悪くなったとき", "併設・提携の動物病院はあるか。連れていく病院と費用の決め方。"),
 ("eye", "見学とお試し", "部屋・におい・音を見られるか。はじめての子は1泊のお試しで。"),
 ("camera", "預かり中の様子", "写真やメッセージで様子を送ってくれるか、カメラで見られるか。"),
 ("shield", "ワクチンの決まり", "証明を求めるホテルは、ほかの子から病気がうつる心配が少なくなります。"),
]

def checklist(e):
    return _V.checks("安心して預けるために、見ておく6つ", CHECK, more=("登録の確かめ方と、見学で見ること・預ける前の準備", "/guide/choose-pet-hotel/"), tag="h3")

def _flags(h):
    return [k for k, _ in CONDS + EXTRA if h.get(k)]

# ── 安心の材料（Nori 2026-11-16「預けようと思ったが、どこが信用できるかわからない」） ──
# hotels.json の trust：公式サイト（src・quote・checked）に書いてあることだけ。書いていない項目は出さない（「不明」も出さない）。
#   reg      動物取扱業（保管）の登録。no＝登録番号、auth＝登録した自治体、until＝有効期限。
#            registry＝自治体が公開している登録の一覧でも、名前・番号が合った（name・asof・page）。
#   night・vet・report・visit・trial・vaccine：v＝カードに出す短い言葉
TRUST = [("reg", None), ("night", "夜もスタッフがいる"), ("vet", "提携の動物病院あり"), ("report", "預かり中の様子を報告"), ("camera", "カメラで様子を見られる"),
         ("visit", "見学できる"), ("trial", "お試しの預かり"), ("vaccine", "ワクチンの証明が必要")]

def _jd(d):
    y, m, dd = (d or "--").split("-")[:3] if d and d.count("-") == 2 else ("", "", "")
    return f"{int(y)}年{int(m)}月{int(dd)}日" if y else ""

def _reg(h):
    r = (h.get("trust") or {}).get("reg")
    return r if r and r.get("no") and (not r.get("until") or r["until"] >= TODAY) else None

def trust_labels(h):
    t = h.get("trust") or {}
    out = []
    r = _reg(h)
    if r:
        out.append(f'動物取扱業（{r["kind"]}）の登録あり' if r.get("kind") else "動物取扱業の登録あり")
        if r.get("registry"): out.append(f'{r["registry"]["name"]}の登録一覧に掲載')
    for k, lab in TRUST[1:]:
        x = t.get(k)
        if x: out.append(x.get("v") or lab)
    if h.get("camera") and not t.get("camera"): out.append("カメラで様子を見られる")
    if h.get("night_staff") and not t.get("night"): out.append("夜もスタッフがいる")
    return list(dict.fromkeys(out))

def trust_detail(h):
    """「そのほか」に入れる、何をもとにしたか（登録番号・一覧の時点・公式サイトの文）。"""
    t = h.get("trust") or {}
    out = []
    r = _reg(h)
    if r:
        head = "・".join(x for x in (r.get("auth"), r.get("kind")) if x)
        s = f'動物取扱業の登録：{head + " " if head else ""}{r["no"]}'
        if r.get("until"): s += f'（有効期限 {_jd(r["until"])}）'
        g = r.get("registry")
        if r.get("by") == "registry":
            s += f'。{g["name"]}が公開している第一種動物取扱業者の一覧（{_jd(g["asof"])}時点）に載っている番号です'
        else:
            s += "。ホテルが出している番号です"
            if g: s += f'。{g["name"]}が公開している第一種動物取扱業者の一覧（{_jd(g["asof"])}時点）にも載っています'
        out.append(s)
    for k, lab in TRUST[1:]:
        x = t.get(k)
        if x and x.get("quote"): out.append(f'{x.get("v") or lab}：「{x["quote"]}」')
    return out

TODAY = __import__("datetime").date.today().isoformat()

FACT_KEYS = ("料金", "営業・受付時間", "定休日", "駐車場", "送迎", "予約のしかた", "お支払い", "対象の動物", "用意するもの", "受け入れの注意", "預かり期間")

import decisionfit

def _card(e, h):
    flags = " ".join(_flags(h))
    tags = [lab for k, lab in CONDS + EXTRA if h.get(k)]
    tl = trust_labels(h)
    if tl: tags = [x for x in tags if x not in ("夜もスタッフがいる", "カメラで様子を見られる")]
    if h.get("max_kg"): tags.append(f'{h["max_kg"]}kgまで')
    if h.get("separate"): tags.append(h["separate"])
    extra = ""
    if h.get("services"): extra += f'<small>内容：{e(h["services"])}</small>'
    if tags: extra += '<small class="emg-spec">公式サイトに書いてある条件：' + e("・".join(tags)) + '</small>'
    if tl: extra = f'<small>安心の材料：{e("、".join(tl[:5]))}</small>' + extra
    for d in trust_detail(h): extra += f'<small class="emg-spec">{e(d)}</small>'
    for f in h.get("facts", []):
        if f["k"] in FACT_KEYS:
            extra += f'<small>{e(f["k"])}：{e(f["v"])}</small>'
            if f["k"] in ("料金", "受け入れの注意") and h.get("fit_status") and f.get("src"):
                extra += f'<a class="fc-source" href="{e(f["src"])}" target="_blank" rel="noopener">{e(f["k"])}の案内</a>'
    for label, value in decisionfit.rows("pet-hotel", h):
        extra += f'<small>{e(label)}：{e(value)}</small>'
    city = f'<small>{e(h["city"])}</small>' if h.get("city") else ""
    # 条件が限定される送迎情報は、全国ページで県を切り替えても同じカードに残す。
    scope_id = f' data-fid="{e(h["id"])}"' if h.get("pickup_comparison") else ""
    return (f'<div class="emg-item emg-co" data-flags="{e(flags)}"{scope_id}{decisionfit.attrs("pet-hotel", h)}><a href="{e(h["url"])}" target="_blank" rel="noopener"><b>{e(h["name"])}</b></a>{city}{extra}{review_link("hotel", h, scope="facility")}</div>')

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    rows = {}
    for h in J["hotels"]:
        for pf in h["prefs"]:
            rows.setdefault(pf, []).append(h)
    total = len(J["hotels"])
    nl = sum(bool(h.get("large")) for h in J["hotels"]); nc = sum(bool(h.get("cat_only") or h.get("separate")) for h in J["hotels"])
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            hs = rows.get(pf, [])
            if hs:
                inner = "".join(_card(e, h) for h in hs) + '<p class="emg-none trim-none" hidden>えらんだ条件をすべて公式サイトに書いているホテルは、この県ではまだ載せていません。条件を減らすか、ホテルに直接おたずねください。</p>'
            else:
                inner = f'<p class="emg-none">{e(pf)}のペットホテルは、まだ載せていません。見つけしだい足します。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    conds = "".join(f'<label><input type="checkbox" value="{k}"> {e(lab)}</label>' for k, lab in CONDS)
    faq = [
      ("大型犬を泊められるペットホテルはどうさがせばいいですか？", f"この一覧では、大型犬を受けると公式サイトにはっきり書いているホテルを{nl}件載せています。「条件でしぼりこむ」で「大型犬を泊められる」をえらび、都道府県でしぼってください。体重の上限が書いてあるホテルは、カードに「◯kgまで」と出ます。"),
      ("猫専用のペットホテル（キャットホテル）はありますか？", f"猫だけを預かるホテルと、犬とは別のフロア・部屋で猫を預かるホテルを、あわせて{nc}件載せています。「猫専用のホテル」でしぼりこめます。"),
      ("ペットホテルが登録を受けているかは、どう確かめられますか？", "ペットを預かる仕事には動物取扱業（保管）の登録が要り、登録番号と有効期限を店の標識とホームページなどの広告に出すことになっています。東京都・大阪府・埼玉県・千葉市・札幌市・北九州市などは、登録している業者の一覧を公開しています。このページのカードの「登録一覧に掲載」は、その一覧でも名前と番号が合ったホテルです。"),
      ("ペットホテルの料金はいくらですか？", "公式サイトに料金が書いてあるホテルは、カードに料金の目安を出しています。体の大きさ・日数・季節（連休や年末年始）で変わり、散歩やおやつ、送迎が別料金のこともあります。"),
      ("ペットホテルとペットシッター、どちらがいいですか？", "家から出ると落ち着かない子や猫はシッター、人やほかの動物に慣れている子や長い日数はホテル、などが目安です。記事「ペットシッターとペットホテル、どちらがいい？」にまとめました。"),
      ("ホテルまでの送り迎えはどうすれば？", "送迎をしているホテルもあります（「送迎がある」でしぼりこめます）。送迎の範囲や料金はホテルごとに違うので、公式サイトで確かめてください。"),
    ]
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    def _hcnt(*ws):
        return sum(1 for h in J["hotels"] if any(w in json.dumps(h, ensure_ascii=False) for w in ws))
    n_fee = sum(1 for h in J["hotels"] if any("料金" in (f.get("k") or "") for f in h.get("facts", [])))
    stats_html = ('<div class="emg-tips"><h4>全国のペットホテルのデータ（公式サイトの記載から集計）</h4><dl>'
      f'<dt>掲載数</dt><dd>全国{total}件。大型犬を泊められるホテルは{nl}件、猫専用・猫を別に預かるホテルは{nc}件です。</dd>'
      f'<dt>夜のお世話</dt><dd>夜間のスタッフや24時間の見守りにふれているホテルは{_hcnt("夜間", "24時間")}件です。</dd>'
      f'<dt>部屋と送迎</dt><dd>個室があるホテルは{_hcnt("個室")}件、送迎に対応するホテルは{_hcnt("送迎")}件、動物病院に併設のホテルは{_hcnt("動物病院")}件です。</dd>'
      f'<dt>料金</dt><dd>料金を公式サイトで公開しているホテルは{n_fee}件です。ペットホテルの料金は大きさ・泊数・お世話の内容で変わるので、預ける前に総額をご確認ください。</dd>'
      '</dl></div>')
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": H1, "item": url}]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, indent=1) + "\n</script>"
    return ctx["head"](TITLE, DESC, url, ld) + f"""
<style>.trim-cond{{display:flex;flex-wrap:wrap;gap:6px 14px;margin:6px 0 12px}}.trim-cond label{{font-size:14px;display:flex;align-items:center;gap:4px}}#trimCount{{font-size:13px;color:#666}}</style>
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › {e(H1)}</nav>
    <h1><small>全国{total}件（大型犬OK {nl}件・猫専用 {nc}件）・条件でしぼりこめます</small>{e(H1)}</h1>
    <p class="lede">全国のペットホテルを、公式サイトの情報をもとに都道府県ごとにまとめました。大型犬OK・猫専用・送迎・動物病院の併設でしぼりこめます。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。ホテルからお金をもらっていません。順番は都道府県ごとで、おすすめ順や点数順ではありません。料金は公式サイトに書いてある分だけ載せています。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      <div class="f"><span>条件でしぼりこむ（公式サイトに書いてある条件だけで判定しています）</span><div class="trim-cond">{conds}</div><span id="trimCount" aria-live="polite"></span></div>
      {stats_html}
      {body}
      {checklist(e)}
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">当サイトとは別の事業者です（{e(J["checked"])}時点の情報）。受け入れの条件は変わることがあるので、預ける前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>ホテルへの送り迎えは、ペットタクシーで</h2><p>大型犬やキャリーの猫も、飼い主さまと一緒に家の前からホテルの前まで移動できます。当日の依頼もできます。</p></div>
    <ul class="other"><li><a href="/guide/large-dog-hotel/">大型犬を預けられるペットホテルの探し方</a></li><li><a href="/guide/cat-hotel/">猫をペットホテルに預けるとき</a></li><li><a href="/guide/sitter-or-hotel/">ペットシッターとペットホテル、どちらがいい？</a></li><li><a href="/guide/grooming-hotel/">トリミング・ペットホテルへの送迎ガイド</a></li><li><a href="/pet-sitter/">全国のペットシッター</a></li><li><a href="/guide/cat-sitter/">猫の留守番とキャットシッター</a></li><li><a href="/guide/large-dog/">大型犬の移動のガイド</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{gen_grooming.JS}
""" + ctx["foot_noband"]()

def urls(SITE):
    return [f"{SITE}/{SLUG}/"]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))

# ── 都道府県ごとのページ（tools/gen_prefpages.py。「ペットホテル 大型犬 ◯◯」「猫 ペットホテル ◯◯」） ──
def _facts(rs):
    n = len(rs)
    return [f"{lab}と公式サイトに書いてある：{sum(bool(h.get(k)) for h in rs)}／{n}" for k, lab in CONDS if sum(bool(h.get(k)) for h in rs)]
def _faq(pf, rs, n):
    c = lambda k: sum(bool(h.get(k)) for h in rs)
    return [
     (f"{pf}で大型犬を泊められるペットホテルは？", f"この一覧の{pf}の{n}件のうち、大型犬を受けると公式サイトに書いているのは{c('large')}件です。体重の上限はカードでご確認ください。"),
     (f"{pf}に猫専用のペットホテルはありますか？", f"猫専用、または犬とは別の部屋・フロアで猫を預かると書いているのは{sum(bool(h.get('cat_only') or h.get('separate')) for h in rs)}件です。"),
     ("ペットホテルが登録を受けているかは、どう確かめられますか？", "ペットを預かる仕事には動物取扱業（保管）の登録が要り、登録番号と有効期限を店の標識とホームページなどの広告に出すことになっています。東京都・大阪府・埼玉県・千葉市・札幌市・北九州市などは、登録している業者の一覧を公開しています。このページのカードの「登録一覧に掲載」は、その一覧でも名前と番号が合ったホテルです。"),
     ("料金はいくらですか？", "公式サイトに料金が書いてあるホテルは、カードに料金の目安を出しています。体の大きさ・日数・季節で変わります。"),
     ("ホテルまでの送り迎えは？", f"送迎があると書いているのは{c('pickup')}件です。送迎の範囲や料金はホテルごとに違うので、公式サイトで確かめてください。"),
    ]
CAT = dict(slug=SLUG, name="ペットホテル", unit="件", h1=H1, items=J["hotels"], card=_card, checked=J["checked"], reviews=False,
  title_word="ペットホテル", title_tail="大型犬OK・猫専用・送迎・動物病院併設",
  desc_tail="ペットホテルを、大型犬を泊められるか・猫専用か・動物病院の併設・送迎・シニアの子・夜のスタッフとあわせて載せています。料金は公開しているホテルだけ載せ、順位は付けていません。",
  lede=lambda pf, n: f"{pf}のペットホテルを{n}件まとめました。大型犬OK・猫専用でもしぼれます。公式サイトに書いてある受け入れの条件だけを載せています。",
  facts=_facts, faq=_faq, before_title="ペットホテルに預ける前に確かめること", before=[], extra_after=lambda e, pf: checklist(e),
  taxi_h="ホテルへの送り迎えは、ペットタクシーで", taxi_p="大型犬やキャリーの猫も、飼い主さまと一緒に家の前からホテルの前まで移動できます。",
  links=[("大型犬を預けられるペットホテルの探し方", "/guide/large-dog-hotel/"), ("猫をペットホテルに預けるとき", "/guide/cat-hotel/"), ("ペットシッターとペットホテル、どちらがいい？", "/guide/sitter-or-hotel/"), ("トリミング・ペットホテルへの送迎ガイド", "/guide/grooming-hotel/"), ("全国のペットシッター", "/pet-sitter/")])

# 2026-11-22：件数は足りても中身が薄い県（新しい薄いページは作らない。全国のページには載る）。中身を足したら外す
CAT["no_page"] = ('青森県', '岐阜県', '山梨県', '愛媛県', '富山県', '山形県')
CAT["fact_cols"] = [("料金", ("料金",)), ("営業・受付時間", ("営業・受付時間",)), ("定休日", ("定休日",)), ("駐車場", ("駐車場",)), ("送迎", ("送迎",))]
CAT["price_title"] = "料金（公式サイトの表示どおり）"
CAT["table"] = [("大型犬", lambda h: (f'○（{h["max_kg"]}kgまで）' if h.get("max_kg") else "○") if h.get("large") else ""), ("猫", lambda h: "猫専用" if h.get("cat_only") else ("別室" if h.get("separate") else ("○" if h.get("cat") else ""))), ("病院併設", lambda h: "○" if h.get("vet") else ""), ("送迎", lambda h: h.get("pickup_comparison") or ("○" if h.get("pickup") else "")), ("シニア", lambda h: "○" if h.get("senior") else ""), ("夜のスタッフ", lambda h: "○" if h.get("night_staff") else "")]

# [B] 大阪府だけの比較。体重の目安・宿泊価格・夜間体制を同じ行で見せ、価格区分を受入上限にはしない。
_OSAKA_LARGE_STAYS = (
    ("Cube dog", "大阪市東成区", "大型犬1泊5,500円（税込）。年末年始などは1泊1頭につき1,100円加算。",
     "大型犬の体重上限と夜間スタッフの有無は要確認。初回はシャンプーコースか3時間以上の一時預かりが必要。",
     "https://www.cube-dog.com/hotel/"),
    ("ドッグホテル レトノワ", "大阪市西区", "大型犬7,700円から・超大型犬8,800円から（24時間）。初回登録料1,100円。繁忙期は基本料金の案内に10%加算。",
     "夜間も預かり先の人と過ごす方式。大型・超大型の体重上限と税の扱いは要確認。",
     "https://intopet.jp/retonowa/price/"),
    ("DOG FIRST", "大阪市北区", "20kg以上の大型犬は24時間11,000円（税込）。通常は9時から18時。営業時間外の預け・引き取りと24時間超過は原則30分ごと500円（長時間の延長は幼稚園の1日料金が安い場合に適用）。",
     "夜もオーナーと同室。20kgは料金区分の下限で、受け入れられる最大体重は要確認。",
     "https://dogfirst-osaka.com/hotel/"),
    ("犬の総合施設 BLISS", "大阪市北区", "大型犬24時間：スタンダード6,000円、プレミアム11,000円（税抜）。非会員は10%加算。体験入園と特別繁忙期の割増は別。",
     "スタンダードは20時～翌9時に人が不在で施設側のカメラ見守り。プレミアムは夜間にスタッフがいるプラン。スタンダードを選んでもプレミアムの預かりと重なる日はプレミアム料金。大型犬の体重上限は要確認。",
     "https://blissdog.jp/?page_id=81"),
)


def _osaka_large_stays(e):
    items = "".join(
        f'<dt>{e(name)}（{e(place)}）</dt><dd><b>{e(price)}</b><br>{e(conditions)} '
        f'<a href="{e(source)}" target="_blank" rel="noopener">料金・利用条件の出典</a></dd>'
        for name, place, price, conditions, source in _OSAKA_LARGE_STAYS
    )
    return (
        '<div class="emg-tips" id="osaka-large-stay">'
        '<h2>大阪の大型犬ペットホテル：1泊料金と夜間の見守りを比べる</h2>'
        '<p>大型犬と書かれていても、料金の区分と受け入れられる体重の上限は同じではありません。'
        '夜間に人がいるプラン、施設側がカメラで見守るプラン、夜間体制を確認してから選ぶホテルを分けて載せています。</p>'
        '<h3>大阪市で大型犬を預けるなら、夜に人がいるプランはいくら？</h3>'
        '<p>大阪市北区のDOG FIRSTは夜もオーナーと同室で、20kg以上の料金は24時間11,000円（税込）です。'
        '同じ北区のBLISSでは、夜間にスタッフがいるプレミアムが大型犬24時間11,000円（税抜）。'
        '6,000円（税抜）のスタンダードは20時から翌9時まで施設側のカメラ見守りで、スタッフは不在です。'
        '同額に見えるときも、税込の総額、預ける犬の体重上限、時間外の加算を確認してください。</p>'
        f'<dl>{items}</dl>'
        '<p class="emg-tips-note">基本料金と主な追加条件の例（2026年11月27日確認）。'
        '空きや受け入れを保証するものではありません。施設側のカメラ見守りは、飼い主が映像を見られるという意味ではありません。</p></div>'
    )


CAT["pref_overrides"] = {
    "大阪府": {
        "section": '<p class="emg-tips-note"><a href="#osaka-large-stay">大型犬の料金と夜間の見守りを比較する</a></p>',
        "extra_after": _osaka_large_stays,
        "title": "大阪府のペットホテル｜大型犬の料金・夜間スタッフ｜ペットのくらし窓口",
        "desc": "大阪のペットホテルを、大型犬の宿泊料金、初回条件、時間外・繁忙期の加算で比較。夜間にスタッフがいるプランと、夜は施設側がカメラで見守るプランを区別して確認できます。",
    },
}
