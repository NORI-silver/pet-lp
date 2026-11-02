# お金を取らない情報ページ「全国のペットシッター（自宅に来てお世話・散歩代行）」（/pet-sitter/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「老犬ホーム、トレーナー、シッター」「今どんどん拡大していってよ」（拡充の3つめ。散歩代行・ペットホテルの話も入れる）。
# 守ること：シッターからお金をもらわない。順位・おすすめをつけない。料金を書かない。電話番号を載せない。
# 各グループの公式サイトの店舗一覧に載っていることだけ書く（店舗名・対応エリア・店舗ページ）。データ：tools/sitters.json。口コミの星は出さない（訪問型で店舗がない）。
import json, os
import prefkeep

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitters.json"), encoding="utf-8"))

SLUG = "pet-sitter"
H1 = "全国のペットシッター（自宅に来てお世話・散歩代行）"
TITLE = "全国のペットシッター｜留守中に自宅へ来てお世話・散歩代行をしてくれるシッターを都道府県でさがせる一覧｜ペットタクシー予約窓口"
DESC = "旅行や出張、入院のあいだ、ペットを家に残したまま自宅に来てお世話や散歩をしてくれるペットシッターを、都道府県ごとにまとめた無料の一覧です。各グループの公式サイトで確かめた対応エリアと、頼む前に確かめたいこと（登録・保険・事前の打ち合わせ）、ペットホテルとの違いをまとめました。料金や順位は載せていません。"

BEFORE = [
 ("ペットシッターとペットホテルの違い", "ペットシッターは、ペットを家に残したまま、シッターが自宅に来て食事・トイレ・散歩・遊びをします。環境が変わらないので、猫や高齢の子、ほかの動物が苦手な子に向きます。ペットホテルは施設にあずける形で、人の目が長い時間あるのが利点です。長い留守のときは、両方を組み合わせることもあります。"),
 ("「登録」と保険", "ペットシッターは動物の愛護及び管理に関する法律の第一種動物取扱業（保管）の登録が必要です。登録番号と、ペットシッター保険（お世話中の事故やけがにそなえる保険）に入っているかを確かめてください。この一覧の2つのグループは、公式サイトで全店の登録と保険加入を書いています。"),
 ("事前の打ち合わせ", "初めて頼むときは、シッターが自宅に来て、性格・食事・薬・散歩のコース・トイレ・緊急時の連絡先と動物病院を確かめる打ち合わせがあります。留守の直前ではなく、余裕をもって頼んでください。"),
 ("鍵の預け方と報告", "鍵は手渡し・キーボックス・宅配などの方法があります。お世話のたびに写真や報告が届くかも確かめておくと安心です。"),
 ("散歩代行だけでも", "留守ではなくても、仕事や体調で散歩に行けない日に、散歩代行だけを頼めるシッターもあります。対応しているかは店舗ごとに違います。"),
]

def _card(e, s):
    ch = J["chains"][s["chain"]]
    extra = f'<small>対応エリア：{e(s["area"])}</small>'
    if s.get("animals"): extra += f'<small>対象：{e(s["animals"])}</small>'
    extra += f'<small>{e(ch["name"])}の店舗一覧より</small>'
    return (f'<div class="emg-item emg-co"><a href="{e(s["url"])}" target="_blank" rel="noopener"><b>{e(s["name"])}</b></a>{extra}</div>')

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    rows = {}
    for s in J["sitters"]:
        for pf in s["prefs"]:
            rows.setdefault(pf, []).append(s)
    total = len(J["sitters"])
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            ss = rows.get(pf, [])
            inner = "".join(_card(e, s) for s in ss) or f'<p class="emg-none">{e(pf)}のペットシッターは、まだ載せていません。見つけしだい足します。各グループの公式サイトから近くの店舗をさがすこともできます。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    chains = "".join(f'<dt><a href="{e(c["url"])}" target="_blank" rel="noopener">{e(c["name"])}</a></dt><dd>{e(c["note"])}</dd>' for c in J["chains"].values())
    faq = [
      ("ペットシッターの料金はいくらですか？", "この一覧には料金を載せていません。1回の訪問の時間と頭数で決まり、初回の打ち合わせ料や交通費、早朝・夜間の割増が別のことがあります。それぞれの店舗ページでご確認ください。"),
      ("猫だけ、犬だけのシッターはありますか？", "猫専門のキャットシッターや、犬だけを受ける店舗があります。一覧の「対象」や店舗ページでご確認ください。"),
      ("当日や前日でも頼めますか？", "初めての店舗は事前の打ち合わせが必要なので、急には頼めないことが多いです。2回目からは店舗によって前日の依頼も受けています。"),
      ("シッターが来る日に動物病院へ連れて行ってほしいときは？", "通院を受ける店舗もありますが、車での移動が必要なときはペットタクシーを頼めます。前もって店舗に相談しておくと安心です。"),
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
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › ペットシッター</nav>
    <h1><small>全国{total}店舗・都道府県でしぼりこめます</small>{e(H1)}</h1>
    <p class="lede">旅行や出張、入院のあいだ、いつもの家で待っていてほしい。ペットを家に残したまま、シッターが自宅に来て食事や散歩をしてくれるペットシッターを、各グループの公式サイトの店舗一覧で確かめて都道府県ごとにまとめました。頼む前に確かめたいことも一緒にどうぞ。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。シッターからお金をもらっていません。順番は都道府県ごとで、おすすめ順ではありません。料金は載せていないので、それぞれの店舗ページでご確認ください。</p>
      <div class="emg-tips" style="margin-top:0"><h4>ペットシッターを頼む前に確かめること</h4><dl>{before}</dl>
      <p class="emg-tips-note">ここに書いたのは一般的な目安です。決まりは店舗ごとに違うので、必ず店舗ページでご確認ください。</p></div>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>一覧に載せているグループ</h4><dl>{chains}</dl></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">当サイトとは別の事業者です（{e(J["checked"])}に各グループの公式サイトの店舗一覧で確かめた情報）。店舗や対応エリアは変わることがあるので、頼む前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>ペットホテルへの送り迎えや通院は、ペットタクシーで</h2><p>あずけに行く日や迎えに行く日、留守中の通院に、ペットタクシーを予約できます。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    <ul class="other"><li><a href="/guide/grooming-hotel/">トリミング・ペットホテルへの送迎ガイド</a></li><li><a href="/dog-trainer/">ドッグトレーナー・しつけ教室</a></li><li><a href="/hospital/visit/">往診専門の動物病院</a></li><li><a href="/guide/cat/">猫の移動のガイド</a></li></ul>
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
