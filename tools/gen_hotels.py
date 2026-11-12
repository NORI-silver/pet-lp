# [B] SEO：お金を取らない情報ページ「大型犬OK・猫専用のペットホテル」（/pet-hotel/、県ごとの /pet-hotel/<県>/）。gen_areas.py が読み込んで使う。
# 「ペットホテル」は全国 月110,000回（キーワードプランナー 2026-11-02、docs/seo-agents.md）で、大手の比較サイトが強い。全部を網羅せず、
# 比べにくい条件（大型犬を泊められる・猫だけのホテル）でしぼった一覧にする（Nori 2026-11-02「SEOと相性がよいものを優先」）。
# [C] 条件（large・cat_only・cat・vet・pickup・senior・night_staff・camera・run・max_kg）は公式サイトにはっきり書いてあるときだけ持つ（ない＝不明）。
# 守ること：ホテルからお金をもらわない。順位・おすすめなし。料金・電話番号なし。公式サイトで確かめたことだけ。データ：tools/hotels.json。
import json, os
import gen_grooming

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotels.json"), encoding="utf-8"))

SLUG = "pet-hotel"
H1 = "大型犬OK・猫専用のペットホテル"
TITLE = "大型犬OK・猫専用のペットホテル｜大型犬を泊められるホテルと猫だけのキャットホテルを都道府県でさがせる一覧｜ペットタクシー予約窓口"
DESC = "大型犬を泊められるペットホテルと、猫だけを預かる猫専用のホテル（キャットホテル）を、都道府県ごとにまとめた無料の一覧です。公式サイトで確かめた内容だけで、動物病院の併設・送迎・シニアの子・夜のスタッフでもしぼりこめます。料金や順位は載せていません。"

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

def _flags(h):
    return [k for k, _ in CONDS + EXTRA if h.get(k)]

def _card(e, h):
    flags = " ".join(_flags(h))
    tags = [lab for k, lab in CONDS + EXTRA if h.get(k)]
    if h.get("max_kg"): tags.append(f'{h["max_kg"]}kgまで')
    if h.get("separate"): tags.append(h["separate"])
    extra = ""
    if h.get("services"): extra += f'<small>内容：{e(h["services"])}</small>'
    if tags: extra += '<small class="emg-spec">公式サイトに書いてある条件：' + e("・".join(tags)) + '</small>'
    city = f'<small>{e(h["city"])}</small>' if h.get("city") else ""
    return (f'<div class="emg-item emg-co" data-flags="{e(flags)}"><a href="{e(h["url"])}" target="_blank" rel="noopener"><b>{e(h["name"])}</b></a>{city}{extra}</div>')

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
                inner = f'<p class="emg-none">{e(pf)}の大型犬OK・猫専用のペットホテルは、まだ載せていません。見つけしだい足します。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    conds = "".join(f'<label><input type="checkbox" value="{k}"> {e(lab)}</label>' for k, lab in CONDS)
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    faq = [
      ("大型犬を泊められるペットホテルはどうさがせばいいですか？", f"この一覧では、大型犬を受けると公式サイトにはっきり書いているホテルを{nl}件載せています。「条件でしぼりこむ」で「大型犬を泊められる」をえらび、都道府県でしぼってください。体重の上限が書いてあるホテルは、カードに「◯kgまで」と出ます。"),
      ("猫専用のペットホテル（キャットホテル）はありますか？", f"猫だけを預かるホテルと、犬とは別のフロア・部屋で猫を預かるホテルを、あわせて{nc}件載せています。「猫専用のホテル」でしぼりこめます。"),
      ("ペットホテルの料金はいくらですか？", "この一覧には料金を載せていません。体の大きさ・日数・季節（連休や年末年始）で変わり、散歩やおやつ、送迎が別料金のこともあります。"),
      ("ペットホテルとペットシッター、どちらがいいですか？", "家から出ると落ち着かない子や猫はシッター、人やほかの動物に慣れている子や長い日数はホテル、などが目安です。記事「ペットシッターとペットホテル、どちらがいい？」にまとめました。"),
      ("ホテルまでの送り迎えはどうすれば？", "送迎をしているホテルもあります（「送迎がある」でしぼりこめます）。送迎の範囲や料金はホテルごとに違うので、公式サイトで確かめてください。"),
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
<style>.trim-cond{{display:flex;flex-wrap:wrap;gap:6px 14px;margin:6px 0 12px}}.trim-cond label{{font-size:14px;display:flex;align-items:center;gap:4px}}#trimCount{{font-size:13px;color:#666}}</style>
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › {e(H1)}</nav>
    <h1><small>全国{total}件（大型犬OK {nl}件・猫専用 {nc}件）・条件でしぼりこめます</small>{e(H1)}</h1>
    <p class="lede">「大型犬は泊められません」と断られた、猫を犬と同じ部屋に預けるのが心配。ペットホテルは数が多いぶん、条件に合うところをさがすのが大変です。大型犬を泊められるホテルと猫専用のホテルにしぼって、公式サイトで確かめた内容だけでまとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。ホテルからお金をもらっていません。順番は都道府県ごとで、おすすめ順や点数順ではありません。料金は載せていないので、それぞれのホテルに直接おたずねください。すべてのペットホテルではなく、大型犬OKと猫専用のホテルだけを載せています。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      <div class="f"><span>条件でしぼりこむ（公式サイトに書いてある条件だけで判定しています）</span><div class="trim-cond">{conds}</div><span id="trimCount" aria-live="polite"></span></div>
      {body}
      <div class="emg-tips"><h4>ペットホテルに預ける前に確かめること</h4><dl>{before}</dl></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">当サイトとは別の事業者です（{e(J["checked"])}に公式サイトで確かめた情報）。受け入れの条件は変わることがあるので、預ける前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
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
     ("料金はいくらですか？", "この一覧には料金を載せていません。体の大きさ・日数・季節で変わります。"),
     ("ホテルまでの送り迎えは？", f"送迎があると書いているのは{c('pickup')}件です。送迎の範囲や料金はホテルごとに違うので、公式サイトで確かめてください。"),
    ]
CAT = dict(slug=SLUG, name="大型犬OK・猫専用のペットホテル", unit="件", h1=H1, items=J["hotels"], card=_card, checked=J["checked"], reviews=False,
  title_word="大型犬OK・猫専用のペットホテル", title_tail="動物病院併設・送迎・シニア",
  desc_tail="大型犬を泊められるホテルと猫だけのホテルを、動物病院の併設・送迎・シニアの子・夜のスタッフとあわせて載せています。料金や順位は載せていません。",
  lede=lambda pf, n: f"{pf}で、大型犬を泊められるペットホテルと猫専用のホテルを{n}件まとめました。公式サイトで確かめた受け入れの条件だけを載せています。",
  facts=_facts, faq=_faq, before_title="ペットホテルに預ける前に確かめること", before=BEFORE,
  taxi_h="ホテルへの送り迎えは、ペットタクシーで", taxi_p="大型犬やキャリーの猫も、飼い主さまと一緒に家の前からホテルの前まで移動できます。",
  links=[("大型犬を預けられるペットホテルの探し方", "/guide/large-dog-hotel/"), ("猫をペットホテルに預けるとき", "/guide/cat-hotel/"), ("ペットシッターとペットホテル、どちらがいい？", "/guide/sitter-or-hotel/"), ("トリミング・ペットホテルへの送迎ガイド", "/guide/grooming-hotel/"), ("全国のペットシッター", "/pet-sitter/")])

CAT["table"] = [("大型犬", lambda h: (f'○（{h["max_kg"]}kgまで）' if h.get("max_kg") else "○") if h.get("large") else ""), ("猫", lambda h: "猫専用" if h.get("cat_only") else ("別室" if h.get("separate") else ("○" if h.get("cat") else ""))), ("病院併設", lambda h: "○" if h.get("vet") else ""), ("送迎", lambda h: "○" if h.get("pickup") else ""), ("シニア", lambda h: "○" if h.get("senior") else ""), ("夜のスタッフ", lambda h: "○" if h.get("night_staff") else "")]
