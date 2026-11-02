# お金を取らない情報ページ「全国の出張トリミング・訪問トリミング」（/trimming/）。gen_areas.py が読み込んで使う。
# [A][B] SHIOKONBU Pet 構想 v1.0（Nori 2026-11-02）の「美容・生活：訪問トリミング」。SEO の入り口として、地域×条件（大型犬・猫・シニア）×目的でさがせる一覧。
# [C][E] 条件（large・cat・senior・car・in_home・max_kg）は公式サイトに書いてあるときだけ持つ Boolean/数値で、ページの「条件でしぼりこむ」に使う（書いていない＝不明で、対応しないという意味ではない）。
# 守ること：事業者からお金をもらわない。順位・おすすめをつけない。料金を書かない。電話番号を載せない。公式サイトで確かめたことだけ書く。
# データ：tools/grooming.json。口コミの星はまだ付けない（あとで EMG_REVIEWS に足せる形にしておく）。
import json, os
import prefkeep

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "grooming.json"), encoding="utf-8"))

SLUG = "trimming"
H1 = "全国の出張トリミング・訪問トリミング"
TITLE = "全国の出張トリミング・訪問トリミング｜トリミングカー・大型犬・シニア犬・猫に対応を都道府県でさがせる一覧｜ペットタクシー予約窓口"
DESC = "家の前まで来るトリミングカーや、家の中で施術する訪問トリミングを、都道府県ごとにまとめた無料の一覧です。公式サイトで確かめた出張エリア・内容と、大型犬・猫・シニア犬への対応で条件をしぼりこめます。料金や順位は載せていません。"

CONDS = [("large", "大型犬に対応"), ("senior", "シニア犬・介護中の子に対応"), ("cat", "猫に対応"), ("car", "トリミングカーで来る"), ("in_home", "家の中で施術")]

BEFORE = [
 ("トリミングカーと家の中での施術", "トリミングカー（車の中に台・浴槽・ドライヤーがある）で家の前で施術する形と、トリマーが道具を持って家に来て浴室などで施術する形があります。車を停める場所や、水・電気を家から借りるかは事業者ごとに違うので、最初に確かめてください。"),
 ("「登録」を受けた事業者か", "ペットの美容は、動物の愛護及び管理に関する法律の第一種動物取扱業の登録は不要な業種ですが、預かりを伴うときは「保管」の登録が必要です。登録番号を公式サイトに書いている事業者もあります。"),
 ("シニア犬・介護中の子", "立っていられる時間、持病、心臓や呼吸の不安、皮膚の状態を先に伝えましょう。短い時間に分ける、立たせずに寝たまま洗うなどの工夫をする事業者もあります。体調が心配なときは、かかりつけの動物病院に先に相談してください。"),
 ("大型犬・猫", "車の大きさや台の耐荷重で、受けられる体重に上限があることがあります。猫は受けない事業者も多いので、一覧の「条件」と公式サイトでご確認ください。"),
 ("当日までに準備すること", "車を停める場所（駐車場・家の前の道）、家の中で施術するなら浴室の広さと水回り、ワクチンやノミ・ダニ予防の状況、こわがり・かみつきの有無。"),
]

def _tags(g):
    t = [lab for k, lab in CONDS if g.get(k)]
    if g.get("max_kg"): t.append(f'{g["max_kg"]}kgまで')
    return t

def _card(e, g):
    flags = " ".join(k for k, _ in CONDS if g.get(k))
    extra = ""
    if g.get("services"): extra += f'<small>内容：{e(g["services"])}</small>'
    if g.get("area"): extra += f'<small>出張エリア：{e(g["area"])}</small>'
    tags = _tags(g)
    if tags: extra += '<small class="emg-spec">公式サイトに書いてある条件：' + e("・".join(tags)) + '</small>'
    city = f'<small>{e(g["city"])}</small>' if g.get("city") else ""
    return (f'<div class="emg-item emg-co" data-flags="{e(flags)}"><a href="{e(g["url"])}" target="_blank" rel="noopener"><b>{e(g["name"])}</b></a>'
            f'{city}{extra}</div>')

# 都道府県の選択（prefkeep）と、条件のしぼりこみを合わせて動かす
JS = "<script>\n(function(){" + prefkeep.FN + r"""
  var sel = document.getElementById("hospPref");
  var boxes = [].slice.call(document.querySelectorAll(".trim-cond input"));
  function apply(){
    var v = sel.value, need = boxes.filter(function(b){ return b.checked; }).map(function(b){ return b.value; });
    var shown = 0;
    document.querySelectorAll(".emg-pref").forEach(function(s){
      var hideP = !!v && s.dataset.pref !== v, n = 0;
      s.querySelectorAll(".emg-item").forEach(function(c){
        var f = (c.dataset.flags || "").split(" ");
        var ok = need.every(function(k){ return f.indexOf(k) >= 0; });
        c.hidden = !ok; if (ok) n++;
      });
      var none = s.querySelector(".trim-none");
      if (none) none.hidden = !(need.length && n === 0 && s.querySelector(".emg-item"));
      s.hidden = hideP || (!v && need.length > 0 && n === 0);
      if (!s.hidden) shown += n;
    });
    document.querySelectorAll(".emg-region").forEach(function(h){ h.hidden = !!v || need.length > 0; });
    var c = document.getElementById("trimCount");
    if (c) c.textContent = need.length || v ? "表示中：" + shown + "件" : "";
  }
  boxes.forEach(function(b){ b.addEventListener("change", apply); });
  prefKeep(sel, apply);
  apply();
""" + "})();\n</script>"

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    rows = {}
    for g in J["groomers"]:
        for pf in g["prefs"]:
            rows.setdefault(pf, []).append(g)
    total = len(J["groomers"])
    npref = len(rows)
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            gs = rows.get(pf, [])
            if gs:
                inner = "".join(_card(e, g) for g in gs) + '<p class="emg-none trim-none" hidden>えらんだ条件をすべて公式サイトに書いている事業者は、この県ではまだ載せていません。条件を減らすか、各事業者に直接おたずねください。</p>'
            else:
                inner = f'<p class="emg-none">{e(pf)}の出張トリミングは、まだ載せていません。見つけしだい足します。近くの県の事業者が出張エリアに入れていることもあります。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    conds = "".join(f'<label><input type="checkbox" value="{k}"> {e(lab)}</label>' for k, lab in CONDS)
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    faq = [
      ("出張トリミングの料金はいくらですか？", "この一覧には料金を載せていません。犬種・体重・毛の長さ・コースのほかに、出張費や駐車の費用が別になることがあります。それぞれの公式サイトか、申し込みのときにご確認ください。"),
      ("大型犬でも出張トリミングを頼めますか？", "大型犬に対応すると公式サイトに書いている事業者は、一覧の「条件でしぼりこむ」で「大型犬に対応」をえらぶと出てきます。車の大きさや台の耐荷重で体重の上限がある事業者もあります。"),
      ("寝たきりやシニアの犬でも大丈夫ですか？", "シニア犬・介護中の子に対応すると書いている事業者があります。体調や持病を先に伝え、短い時間に分けるなどの方法を相談してください。体調が心配なときは、先にかかりつけの動物病院にご相談ください。"),
      ("猫の出張トリミングはありますか？", "猫を受ける事業者は「猫に対応」でしぼりこめます。猫は受けない事業者も多いので、公式サイトでご確認ください。"),
      ("条件のしぼりこみで出てこない事業者は、対応していないのですか？", "そうとは限りません。ここでは公式サイトにはっきり書いてある条件だけを付けています。書いていない条件は「分からない」の扱いなので、気になるときは事業者に直接おたずねください。"),
      ("サロンに連れていきたいけど車がないときは？", "大型犬やシニアの子は、ペットタクシーで家の前からサロンの前まで移動できます。記事「トリミング・ペットホテルへの送迎ガイド」もどうぞ。"),
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
    <h1><small>全国{total}件・{npref}都道府県・条件でしぼりこめます</small>{e(H1)}</h1>
    <p class="lede">サロンまで連れていくのが大変な大型犬、車に長く乗るのがつらいシニアの子、外がこわい子。トリマーさんが家まで来てくれる出張トリミング・訪問トリミングを、公式サイトで確かめた内容だけで都道府県ごとにまとめました。大型犬・シニア犬・猫への対応でもしぼりこめます。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。事業者からお金をもらっていません。順番は都道府県ごとで、おすすめ順や点数順ではありません。料金は載せていないので、それぞれの事業者に直接おたずねください。</p>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      <div class="f"><span>条件でしぼりこむ（公式サイトに書いてある条件だけで判定しています）</span><div class="trim-cond">{conds}</div><span id="trimCount" aria-live="polite"></span></div>
      {body}
      <div class="emg-tips"><h4>出張トリミングを頼む前に確かめること</h4><dl>{before}</dl>
      <p class="emg-tips-note">ここに書いたのは一般的な目安です。犬や猫の様子にあわせて、事業者や動物病院に相談してください。</p></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">当サイトとは別の事業者です（{e(J["checked"])}に公式サイトで確かめた情報）。出張エリアや内容は変わることがあるので、頼む前に必ずリンク先でご確認ください。掲載の内容の誤りや、掲載をやめたいご希望は、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>サロンへの送り迎えは、ペットタクシーで</h2><p>大型犬やシニアの子も、飼い主さまと一緒に家の前からサロンの前まで移動できます。当日の依頼もできますが、会社にメールで確認するため、お迎えは依頼から3時間以上あとになります。</p></div>
    <ul class="other"><li><a href="/guide/grooming-hotel/">トリミング・ペットホテルへの送迎ガイド</a></li><li><a href="/guide/senior/">シニア犬・シニア猫、介護中の子の移動</a></li><li><a href="/guide/large-dog/">大型犬の移動のガイド</a></li><li><a href="/pet-sitter/">全国のペットシッター</a></li><li><a href="/rojin-home/">老犬ホーム・老猫ホーム</a></li><li><a href="/hospital/visit/">往診専門の動物病院</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{JS}
""" + ctx["foot_noband"]()

def urls(SITE):
    return [f"{SITE}/{SLUG}/"]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))
