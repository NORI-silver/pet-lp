# お金を取らない情報ページ「全国のドッグラン」（/dogrun/、都道府県ごとの /dogrun/<slug>/、記事 /dogrun/<記事>/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「全部マネタイズじゃなくていい。SEO的なコンテンツでもいい」「どんどん進めて」→ 同日「内容薄すぎじゃない？SEOちゃんとやってよ」で
# 都道府県ごとのページと、各ドッグランの料金・時間・休み・エリア・登録・必要なもの・駐車場・アクセスを足した。
# 同日「網羅性弱すぎ。ドッグランは公営以外も。一覧表は一覧でいいけど、記事も拡充してね」で、民間（お店・商業施設・レジャー施設）と
# 高速道路のSA・PAのドッグラン（kind）と、記事（ARTICLES）を足した。
# 守ること：順位・おすすめなし。電話番号なし。
# 公式ページで確かめたことだけ書く（書いていない項目は出さない）。データ：tools/dogrun.json（src は参考にした公式ページ）。
import json, os, re
from urllib.parse import quote
import prefkeep
from prefs import PREFS

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dogrun.json"), encoding="utf-8"))
RUNS = J["dogruns"]
NONE = J.get("none", {})
NONE_SRC = J.get("none_src", {})
CHECKED = J["checked"]

SLUG = "dogrun"
PSLUG = {x[1]: x[0] for x in PREFS}
PSLUG.update({"東京都": "tokyo", "神奈川県": "kanagawa", "埼玉県": "saitama", "千葉県": "chiba"})
BY = {}
for _d in RUNS:
    BY.setdefault(_d["pref"], []).append(_d)
TOTAL = len(RUNS)

# 種類（kind）。データに kind がなければ公営。
KINDS = [("公営", "公園などの公営のドッグラン", "公営", "国・都道府県・市町村の公園や施設にあるドッグランです。無料のところが多く、はじめに利用登録がいるところもあります。"),
         ("民間", "お店・施設のドッグラン", "お店・施設", "カフェ・ペット用品店・アウトレットなどの商業施設・牧場などにあるドッグランです。料金がかかるところが多く、その場で受付してワクチンの証明を見せます。"),
         ("高速道路", "高速道路のSA・PAのドッグラン", "高速道路SA・PA", "高速道路のサービスエリア・パーキングエリアにあるドッグランです。高速道路を通る人の休けい用で、外からは入れません。")]
KLAB = {k: short for k, _, short, _ in KINDS}
def kind(d): return d.get("kind", "公営")
def by_kind(rs, k): return [d for d in rs if kind(d) == k]

# 項目の名前（表示の順）
FIELDS = [("addr", "所在地"), ("place", "場所"), ("hours", "利用時間"), ("season", "開いている期間"), ("closed", "休み"),
          ("fee", "料金"), ("size", "エリア（犬の大きさ）"), ("reg", "利用登録"), ("need", "必要なもの・条件"),
          ("ng", "入れない犬など"), ("limit", "連れて入れる頭数"), ("parking", "駐車場"), ("access", "アクセス"), ("note", "ご注意")]

def fee_tag(d):
    f = d.get("fee", "")
    if not f: return None
    if f.startswith("無料"): return "無料"
    if f.startswith(("利用は無料", "ドッグランは無料")): return "利用は無料"
    return "有料"

def reg_tag(d):
    r = d.get("reg", "")
    if not r: return None
    return "登録なしで使える" if r.startswith("いらない") else "登録がいる"

def is_small(d): return "小型犬" in d.get("size", "")
def is_large(d):
    s = d.get("size", "")
    return any(w in s for w in ("大型犬", "全犬種", "犬種・体重の区別なし"))

def tags(d):
    t = [(KLAB[kind(d)], False)]
    f = fee_tag(d)
    if f: t.append((f, f != "有料"))
    r = reg_tag(d)
    if r: t.append((r, r == "登録なしで使える"))
    if is_small(d): t.append(("小型犬エリアあり", False))
    if d.get("season"): t.append(("開く期間が決まっている", False))
    if d.get("resident"): t.append(("住民向け", False))
    return t

def tags_html(e, d):
    return '<ul class="dr-tags">' + "".join(('<li class="ok">' if ok else "<li>") + e(x) + "</li>" for x, ok in tags(d)) + "</ul>"

def nfree(rs): return sum(1 for d in rs if fee_tag(d) in ("無料", "利用は無料"))
def nnoreg(rs): return sum(1 for d in rs if reg_tag(d) == "登録なしで使える")
def nsmall(rs): return sum(1 for d in rs if is_small(d))
def nvac(rs): return sum(1 for d in rs if "ワクチン" in d.get("need", ""))
def nseason(rs): return sum(1 for d in rs if d.get("season"))

def stats(rs):
    li = [("", len(rs))] + [(lab, len(by_kind(rs, k))) for k, _, lab, _ in KINDS] + \
         [(lab, f(rs)) for lab, f in (("利用料が無料", nfree), ("登録なしで使える", nnoreg), ("小型犬エリアあり", nsmall))]
    return '<ul class="dr-stats">' + "".join(f"<li>{lab} <b>{n}</b>か所</li>" if lab else f"<li><b>{n}</b>か所</li>" for lab, n in li if n or not lab) + "</ul>"

def href(pf):
    return f"/{SLUG}/{PSLUG[pf]}/"

def kind_counts_text(rs):
    return "・".join(f"{lab}{len(by_kind(rs, k))}" for k, _, lab, _ in KINDS if by_kind(rs, k))

# ── 地域ページ（/tokyo/ や /area/osaka/）から使う一文 ──
def area_snippet(pf, e):
    rs = BY.get(pf, [])
    if not rs:
        return f'<h3>{e(pf)}のドッグラン</h3><p>{e(NONE.get(pf, "公式ページで確かめられるドッグランは、まだ載せていません。"))}全国のドッグランは<a href="/{SLUG}/">全国のドッグランの一覧</a>にまとめています。</p>'
    names = "、".join(d["name"] for d in rs[:3])
    return (f'<h3>{e(pf)}のドッグラン</h3><p>{e(pf)}には、公式ページで確かめたドッグランが{len(rs)}か所あります（{e(kind_counts_text(rs))}。{e(names)}{"など" if len(rs) > 3 else ""}）。'
            f'料金・利用登録・利用時間・小型犬エリアの有無は<a href="{href(pf)}">{e(pf)}のドッグラン</a>にまとめています。</p>')

# ── 共通の本文 ──
BEFORE = [
 ("利用登録がいるか", "公営のドッグランは、はじめに利用登録（WEB申請・窓口・登録会や説明会）がいるところが多いです。登録なしで使えるところもあります。市や町に住んでいる人だけが登録できるところもあります。お店や施設のドッグランは、その日の受付で書類を見せるところが多いです。"),
 ("持っていく書類", "多くのドッグランで、犬の鑑札（またはマイクロチップの登録証明）と、その年度の狂犬病予防注射済票が必要です。1年以内の混合ワクチン（3種や5種以上）の接種証明を求めるところもあります。写しや写真でよいところもあります。"),
 ("入れない犬", "子犬（生後4か月や6か月未満など）、発情中の犬、病気やノミ・ダニのいる犬、人や犬をかむくせのある犬は、入れないことが多いです。犬種や頭数に決まりがあるところも。"),
 ("大きさのエリア", "小型犬用と中・大型犬用にエリアが分かれているところがあります。区切りは体重（8kg・10kgなど）や体高（25cm・40cm・50cmなど）で、場所ごとに違います。"),
 ("開いている日と時間", "日の出から日没まで、9時〜17時など、場所ごとに違います。開くのが土日だけのところや、雪の多い地域では冬に閉めるところ、夏の暑い時期に閉めるところもあります。"),
]
BRING = ["リード（ドッグランの外では必ずつけます）", "うんち袋・ペットシーツ（ふんは持ち帰るのが基本です）", "飲み水と器、タオル",
         "登録証・鑑札・狂犬病予防注射済票（求められる場所では身につけさせます）", "混合ワクチンの接種証明の写し（求められる場所）",
         "夏は保冷グッズ、雨のあとは足をふくもの"]
MANNER = ["飼い主はいっしょに入り、犬から目を離さない。犬だけを残さない。", "入口の二重扉は、片方が閉まってから次を開ける。", "ふんは持ち帰り、おしっこは水で流す（水道がある場所）。",
          "おやつやおもちゃは、禁止のところが多いので決まりを確かめる。", "はじめての場所では、まず外から様子を見て、混んでいたら短い時間にする。", "ほかの犬とけんかになりそうなときは、すぐにリードをつけて外に出る。"]

def faq_common(e):
    rs = RUNS
    nk = {k: len(by_kind(rs, k)) for k, _, _, _ in KINDS}
    return [
      ("どんなドッグランを載せていますか？", f"公園などの公営のドッグラン{nk['公営']}か所、お店・施設のドッグラン{nk['民間']}か所、高速道路のSA・PAのドッグラン{nk['高速道路']}か所の、あわせて{TOTAL}か所です。どれも公式ページで確かめたことだけを書いていて、おすすめ順ではありません。見つけしだい足していきます。"),
      ("ドッグランを使うのに必要なものは？", f"多くのドッグランで、犬の鑑札と、その年度の狂犬病予防注射済票が必要です。この一覧の{TOTAL}か所のうち{nvac(rs)}か所は、混合ワクチンの接種（証明）も条件にしています。事前の利用登録がいるところも多いので、行く前に公式ページを確かめてください。"),
      ("無料のドッグランはありますか？", f"あります。この一覧の{TOTAL}か所のうち、公式ページに利用料が無料と書いてあるのは{nfree(rs)}か所です（登録料や公園の入園料・駐車料、高速道路の料金が別にかかるところを含みます）。くわしくは「無料で使えるドッグラン」の記事にまとめています。"),
      ("登録なしで使えるドッグランはありますか？", f"あります。この一覧では{nnoreg(rs)}か所が、公式ページに登録はいらないと書いています。都道府県ごとのページでは「登録なしで使える」の印をつけています。"),
      ("鑑札と狂犬病予防注射済票はどこでもらえますか？", "犬の登録をすると市区町村から鑑札が、毎年の狂犬病予防注射を受けると注射済票がもらえます。くわしくは「ペットの迷子・犬の登録・引取りの窓口」のページにまとめています。"),
      ("小型犬と大型犬でエリアは分かれていますか？", f"この一覧の{TOTAL}か所のうち{nsmall(rs)}か所に、小型犬用のエリアがあります。区切りは体重や体高で、場所ごとに違います。"),
      ("冬も使えますか？", f"雪の多い地域では、冬に閉めるドッグランがあります。この一覧では{nseason(rs)}か所に、開いている期間の決まりがあります。"),
    ]

def faq_pref(e, pf, rs):
    q = []
    nk = [(lab, len(by_kind(rs, k))) for k, _, lab, _ in KINDS if by_kind(rs, k)]
    q.append((f"{pf}にはどんなドッグランがありますか？", f"この一覧では、{'、'.join(f'{lab}が{n}か所' for lab, n in nk)}です。公式ページで確かめたものだけを載せていて、見つけしだい足していきます。"))
    fr = [d["name"] for d in rs if fee_tag(d) in ("無料", "利用は無料")]
    if fr:
        q.append((f"{pf}で無料のドッグランは？", f"公式ページに利用料が無料と書いてあるのは、{'、'.join(fr)}です（登録料や駐車料、高速道路の料金が別にかかるところもあります）。"))
    nr = [d["name"] for d in rs if reg_tag(d) == "登録なしで使える"]
    if nr:
        q.append((f"{pf}で登録なしで使えるドッグランは？", f"公式ページに登録はいらないと書いてあるのは、{'、'.join(nr)}です。鑑札や注射済票などの条件はあるので、行く前に確かめてください。"))
    sm = [d["name"] for d in rs if is_small(d)]
    if sm:
        q.append((f"{pf}で小型犬エリアがあるドッグランは？", f"{'、'.join(sm)}に小型犬用のエリアがあります。区切りの体重や体高は場所ごとに違います。"))
    se = [d["name"] for d in rs if d.get("season")]
    if se:
        q.append((f"{pf}のドッグランは一年中使えますか？", f"{'、'.join(se)}は、開いている期間が決まっています。そのほかも、天気や工事・イベントで閉めることがあります。"))
    q.append((f"{pf}のドッグランへ、車がなくても行けますか？", "公共交通機関で行けるところもありますが、犬を連れて乗れるかは交通機関ごとに決まりがあります。出かける前に、使う交通機関の決まりを確かめてください。"))
    return q

def ld_json(objs):
    return '<script type="application/ld+json">\n' + json.dumps(objs, ensure_ascii=False, indent=1) + "\n</script>"

def faq_ld(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

def crumbs(SITE, items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}

def guide_html(e):
    before = "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in BEFORE)
    bring = "".join(f"<li>{e(x)}</li>" for x in BRING)
    manner = "".join(f"<li>{e(x)}</li>" for x in MANNER)
    return f'''<div class="emg-tips"><h4>ドッグランに行く前に確かめること</h4><dl>{before}</dl>
<p class="emg-tips-note">決まりは場所ごとに違います。ここに書いたのは多くのドッグランに共通する目安です。必ずリンク先の公式ページでご確認ください。</p></div>
<div class="emg-tips"><h4>持っていくもの</h4><ul>{bring}</ul></div>
<div class="emg-tips"><h4>はじめてでも安心な使い方とマナー</h4><ul>{manner}</ul>
<p class="emg-tips-note">夏の昼間は地面が熱くなります。朝や夕方の涼しい時間に、水を飲ませながら短めに遊ばせてあげてください。</p></div>'''

# ── 記事（/dogrun/<slug>/） ──
# list: その記事で一覧にするドッグランの条件（None なら一覧なし）
def _p(*xs): return "".join(f"<p>{x}</p>" for x in xs)
def _h(t): return f"<h2>{t}</h2>"
def _ul(xs): return "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul>"

def _cost_examples(e):
    # 民間の料金の例（データからそのまま。おすすめ順ではない）
    ex = [d for d in by_kind(RUNS, "民間") if d.get("fee") and fee_tag(d) == "有料"][:6]
    return _ul([f'<a href="{href(d["pref"])}#{d["id"]}">{e(d["name"])}</a>（{e(d["pref"])}）：{e(d["fee"])}' for d in ex])


# [B] 2026-11-03「中身の薄いページを充実させる」：記事に、一覧のデータ（公式ページで確かめた各ランの項目）を数えた表を足す。
# 数えるのは公式ページに書いてあることだけ。書いていないランは分母に入れない（「書いていない」は「しない」ではない）。
_KCOLS = [("公営", "公営"), ("民間", "お店・施設"), ("高速道路", "SA・PA")]
def _cnt(rs, field, pat):
    w = [d for d in rs if d.get(field)]
    return sum(1 for d in w if re.search(pat, d[field])), len(w)
def _frac(a, b): return f"{a}／{b}" if b else "—"
def _count_table(e, field, rows, note):
    """rows=[(見出し, 正規表現)]。公営・お店・SA・PA・全体ごとに「当てはまる数／その項目を書いているランの数」。"""
    head = "<tr><th></th>" + "".join(f"<th>{lab}</th>" for _, lab in _KCOLS) + "<th>全体</th></tr>"
    body = ""
    for lab, pat in rows:
        cells = [_frac(*_cnt(by_kind(RUNS, k), field, pat)) for k, _ in _KCOLS] + [_frac(*_cnt(RUNS, field, pat))]
        body += f"<tr><th>{lab}</th>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"
    return (f'<div class="tbl"><table class="dr-tbl"><thead>{head}</thead><tbody>{body}</tbody></table></div>'
            f'<p class="small">{note}（{CHECKED}時点・一覧の{TOTAL}か所）。数字は「当てはまる数／その項目を公式ページに書いているランの数」です。</p>')

# [B] 11/14 Nori「ユーザが何を求めていて、それにたいするアンサーがあるのか」：「ドッグラン 必要なもの」（月110）・
# 「ドッグラン 狂犬病」（月70）・「ドッグラン ワクチン」（月50）の検索に、一覧の公式ページを数えた数で先に答える。
def _vac_answer():
    import re as _re
    w = [d for d in RUNS if d.get("need")]
    rab = sum(1 for d in w if _re.search(r"狂犬病|済票|済証", d["need"]))
    mix = sum(1 for d in w if _re.search(r"混合|[0-9]種", d["need"]))
    pup = sum(1 for d in RUNS if _re.search(r"生後|か月|ヶ月|ワクチンを受けて", d.get("ng", "") + d.get("limit", "")))
    qa = [("狂犬病の予防注射をしていないと、ドッグランに入れませんか？", f"必要なものを公式ページに書いている{len(w)}か所のうち、{"すべて" if rab == len(w) else f"{rab}か所"}が狂犬病予防注射の済票・証明を求めています。注射をしていない犬は、ほとんどのドッグランで入れないと考えてください。病気などで注射できないときの猶予証明を受け入れるかは場所ごとに違います。"),
          ("混合ワクチンの証明もいりますか？", f"同じ{len(w)}か所のうち、混合ワクチンの接種証明を求めるのは{mix}か所です。公園などの公営のランは狂犬病と鑑札だけのところが多く、お店や施設のランは混合ワクチンまで求めるところが多いです。"),
          ("子犬はいつからドッグランに行けますか？", f"子犬の月齢やワクチンからの日数を決まりにしているところが、一覧に{pup}か所あります。「生後◯か月から」「ワクチンを受けてから◯日」などで、場所によって違うので、行く前に公式ページで確かめてください。"),
          ("書類のほかに持っていくものは？", "・".join(x.split("（")[0] for x in BRING[:3]) + "です。持ち物とマナーは<a href=\"/dogrun/first/\">はじめてのドッグラン</a>にまとめました。")]
    return ('<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">ワクチンと証明書のポイント</h2><dl>' + "".join(f"<dt>{q}</dt><dd>{a}</dd>" for q, a in qa) + "</dl></div>")


# [B] 11/14：「ドッグラン 登録 不要」（月40〜70）の検索に、数えた数で先に答える。
def _noreg_answer():
    w = [d for d in RUNS if reg_tag(d)]
    n0 = sum(1 for d in w if reg_tag(d) == "登録なしで使える")
    sa = sum(1 for d in RUNS if d.get("kind") == "高速道路")
    qa = [("登録しなくても使えるドッグランはありますか？", f"あります。一覧の{TOTAL}か所のうち、登録について公式ページに書いてあるのは{len(w)}か所で、そのうち「登録はいらない」とはっきり書いてあるのは{n0}か所です。のこりの{len(w) - n0}か所は、はじめに利用登録や受付がいります。下に{n0}か所の一覧があります。"),
          ("今日すぐ使いたいときは？", f"高速道路のSA・PAのドッグラン（一覧に{sa}か所）は、公式ページに登録の決まりが書かれていません。お店や施設のドッグランは、その日の受付で書類を見せる形が多いです。公園などの公営のドッグランは、登録会や窓口での登録が先にいるところが多いので、前もって確かめてください。"),
          ("登録のときに何がいりますか？", "多いのは、犬の鑑札（またはマイクロチップの登録証明）、その年度の狂犬病予防注射済票、混合ワクチンの接種証明です。数は<a href=\"/dogrun/vaccine/\">ドッグランに必要な書類</a>にまとめました。")]
    return ('<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">登録がいらないドッグランのポイント</h2><dl>' + "".join(f"<dt>{q}</dt><dd>{a}</dd>" for q, a in qa) + "</dl></div>")

def _pct(a, b): return f"{round(a * 100 / b)}%" if b else "—"
def _kind_table(e):
    rows = [("載せている数", lambda rs: str(len(rs))),
            ("利用料が無料", lambda rs: _frac(sum(1 for d in rs if fee_tag(d) in ("無料", "利用は無料")), sum(1 for d in rs if fee_tag(d)))),
            ("はじめに利用登録がいる", lambda rs: _frac(sum(1 for d in rs if reg_tag(d) == "登録がいる"), sum(1 for d in rs if reg_tag(d)))),
            ("混合ワクチンの証明を求める", lambda rs: _frac(*_cnt(rs, "need", r"混合|[0-9]種"))),
            ("小型犬のエリアがある", lambda rs: _frac(sum(1 for d in rs if is_small(d)), sum(1 for d in rs if d.get("size")))),
            ("24時間使える", lambda rs: _frac(*_cnt(rs, "hours", r"24時間"))),
            ("休みの日・期間がある", lambda rs: _frac(sum(1 for d in rs if d.get("closed") or d.get("season")), len(rs))),
            ("駐車場のことを書いている", lambda rs: _frac(sum(1 for d in rs if d.get("parking")), len(rs)))]
    head = "<tr><th></th>" + "".join(f"<th>{lab}</th>" for _, lab in _KCOLS) + "</tr>"
    body = "".join(f"<tr><th>{lab}</th>" + "".join(f"<td>{f(by_kind(RUNS, k))}</td>" for k, _ in _KCOLS) + "</tr>" for lab, f in rows)
    return f'<div class="tbl"><table class="dr-tbl"><thead>{head}</thead><tbody>{body}</tbody></table></div>'

ARTICLES = [
 {"slug": "free", "short": "無料で使えるドッグラン",
  "title": lambda: f"無料で使えるドッグラン{nfree(RUNS)}か所｜都道府県別の一覧と、別にかかるお金",
  "desc": lambda: f"公式ページに利用料が無料と書いてあるドッグラン{nfree(RUNS)}か所を都道府県別にまとめました。公園の公営ドッグラン・高速道路のSA・PA・アウトレットなど。登録料や駐車料など、別にかかるお金も説明します。",
  "lede": "公園や高速道路のSA・PAには、無料で使えるドッグランがたくさんあります。ただ、利用料は無料でも、登録料や駐車料が別にかかることも。公式ページで確かめた無料のドッグランと、気をつけたいお金をまとめました。",
  "list": lambda d: fee_tag(d) in ("無料", "利用は無料"),
  "body": lambda e: _h("「無料」でも、別にかかるお金") + _ul([
      "<b>利用登録の手数料</b>：公営のドッグランで、年に1回の登録料がかかるところがあります。",
      "<b>駐車料金</b>：公園の駐車場が有料のことがあります。土日は早くうまることも。",
      "<b>入園料</b>：ドッグランは無料でも、公園や施設に入るのにお金がかかるところがあります。",
      "<b>高速道路の料金</b>：SA・PAのドッグランは無料ですが、高速道路を通らないと入れません。"]) +
      _h("無料のドッグランを気持ちよく使うために") + _p("無料のドッグランは、土日の昼に混みやすいです。はじめての日は、すいている平日の朝や夕方に行くと、犬も飼い主さんも落ち着いて過ごせます。",
      "ふんの持ち帰りや、入口の二重扉の閉め忘れに気をつけることが、ドッグランを続けてもらうことにつながります。")},
 {"slug": "noreg", "short": "登録なしで使えるドッグラン",
  "title": lambda: f"登録なしで使えるドッグラン{nnoreg(RUNS)}か所｜公営ドッグランの登録制も解説",
  "desc": lambda: f"公式ページに利用登録はいらないと書いてあるドッグラン{nnoreg(RUNS)}か所の一覧と、公営ドッグランの登録のしかた（WEB申請・窓口・登録会）や、登録で求められる書類を説明します。",
  "lede": "公営のドッグランは、はじめに利用登録がいるところが多く、「今日行きたい」ときに困ることがあります。公式ページで登録はいらないと確かめたドッグランと、登録のしくみをまとめました。",
  "list": lambda d: reg_tag(d) == "登録なしで使える",
  "body": lambda e: _noreg_answer() + _h("公営のドッグランの「利用登録」とは") + _p("公営のドッグランでは、事故やけんか、病気の広がりをふせぐため、はじめに犬と飼い主さんの登録をしてもらうところが多いです。登録すると、登録証やタグが配られ、ドッグランの中で身につけることもあります。") +
      _h("登録のしかたの例") + _ul(["<b>WEB申請</b>：インターネットで申しこみ、書類の写真をのせる。", "<b>窓口</b>：公園の管理事務所などで、書類を見せて登録する。", "<b>登録会・説明会</b>：決まった日の説明会に出て登録する（毎月1回など）。"]) +
      _p("登録で求められることが多いのは、犬の鑑札（またはマイクロチップの登録証明）、その年度の狂犬病予防注射済票、混合ワクチンの接種証明です。市や町に住んでいる人だけが登録できるところもあります。") +
      _h(f"登録のしかたを、一覧の{TOTAL}か所で数えると") + _count_table(e, "reg", [
          ("登録はいらない", r"^いらない"), ("インターネットで申しこめる", r"WEB|ウェブ|オンライン|電子申請|ネット|サイトで"), ("窓口で登録する", r"窓口|管理事務所|事務所|センターで"),
          ("登録会・説明会・講習に出る", r"登録会|説明会|講習|しつけ方教室"), ("住んでいる人だけ・市町村の登録が条件", r"住民|在住|住んで|市内|町内|区内"), ("毎年・年度ごとに登録しなおす", r"毎年|年度|有効期限|更新")],
          "各ドッグランの公式ページの「利用登録」を数えました") +
      _p("公営のドッグランは、窓口や登録会での登録が多く、平日の昼にしか受け付けないところもあります。行きたい日が決まっているときは、早めに登録をすませておくと安心です。") +
      _h("登録なしでも、条件はあります") + _p("登録がいらないドッグランでも、鑑札や注射済票をつけること、発情中や病気の犬は入れないことなどの決まりがあります。お店や施設のドッグランは、会員の登録はなくても、その日の受付でワクチンの証明を見せるところが多いです。")},
 {"slug": "sapa", "short": "高速道路のSA・PAのドッグラン",
  "title": lambda: f"高速道路のSA・PAのドッグラン{len(by_kind(RUNS, '高速道路'))}か所｜都道府県別・広さと小型犬エリア",
  "desc": lambda: f"東名・新東名・中央道・名神・北陸道・東北道などのサービスエリア・パーキングエリアにあるドッグラン{len(by_kind(RUNS, '高速道路'))}か所を、高速道路会社の公式ページで確かめてまとめました。広さ・小型犬エリア・冬の休み。犬との長いドライブの休けいのコツも。",
  "lede": "犬といっしょの長いドライブでは、休けいのたびに少し体を動かせると安心です。高速道路のSA・PAにあるドッグランを、高速道路会社の公式ページで確かめてまとめました。",
  "list": lambda d: kind(d) == "高速道路",
  "body": lambda e: _h("SA・PAのドッグランの使い方") + _ul(["高速道路を通る人の休けい用で、高速道路の外からは入れません（ドッグランは無料ですが、高速道路の料金がかかります）。",
      "上り線・下り線の片方にしかないことが多いので、通る向きを確かめてから出かけましょう。", "駐車場からドッグランまでは、必ずリードをつけます。車の出入りが多いので、抱っこやリードを短く持つと安心です。",
      "雪の多い地域では、冬に使えないところがあります。照明がなく、夜は使えないところもあります。"]) +
      _h("犬との長いドライブで気をつけたいこと") + _ul(["こまめに休けいをとり、水を飲ませ、トイレをすませる。", "夏は車の中がすぐ暑くなります。エンジンを止めた車に犬だけを残さない。", "車に酔いやすい犬は、出発の前のごはんを少なめにする。心配なときはかかりつけの動物病院に相談を。",
      "車の中ではクレートやキャリー、犬用のシートベルトで、急ブレーキでもけがをしないようにする。"]) +
      _p('大型犬で遠くへ行くときは、<a href="/guide/large-dog/">大型犬の移動のガイド</a>もご覧ください。')},
 {"slug": "first", "short": "はじめてのドッグラン",
  "title": lambda: "はじめてのドッグラン｜デビュー前の準備・当日の流れ・マナーと注意",
  "desc": lambda: "はじめてドッグランに行く前に知っておきたいことをまとめました。ワクチンや登録などの準備、呼び戻しの練習、当日の流れ、遊びとけんかの見分け方、帰ってからのケア、持ち物とマナー。全国のドッグランの一覧も。",
  "lede": "はじめてのドッグランは、犬も飼い主さんもどきどきします。行く前の準備と当日の流れを知っておくと、楽しい時間になりやすいです。",
  "list": None,
  "body": lambda e: _h("1. 行く前の準備") + _ul(["<b>ワクチンと書類</b>：狂犬病予防注射と、混合ワクチンの接種をすませておきます。鑑札・注射済票・接種証明の写しを用意します。子犬は、ワクチンのプログラムが終わってから。",
      "<b>呼び戻しの練習</b>：名前を呼んだら戻ってくる練習を、家や公園でリードをつけてしておくと、ドッグランで困ったときに助かります。",
      "<b>ほかの犬になれる</b>：散歩のときに、ほかの犬とあいさつする機会をつくっておくと安心です。", "<b>ノミ・ダニの予防</b>：ドッグランでは、ほかの犬からうつることがあります。かかりつけの動物病院で相談を。"]) +
      _h("2. 当日の流れ") + _ul(["受付や登録がある場所では、先に書類を見せます。", "まずはリードをつけたまま、外から中の様子を見ます。大きな犬が多い、走り回っている犬が多いときは、小型犬エリアやすいている時間にしても。",
      "入口の二重扉の中でリードを外し、外の扉が閉まってから中の扉を開けます。", "はじめは10〜15分ほど、短い時間にします。犬が楽しそうなら、少しずつのばしていきます。"]) +
      _h("3. 遊びとけんかの見分け方") + _p("体を低くしておしりを上げる、追いかけっこで役がかわる、などは遊びのサインです。しっぽを足の間に入れる、体がかたまる、うなり声が続く、片方だけが逃げ続けるときは、こわがっているかもしれません。そのときはすぐに呼び戻すか、リードをつけて休ませてあげてください。") +
      _h("4. 帰ってから") + _ul(["足の裏やつめ、体にけががないか見てあげます。", "体にノミやダニがついていないか、ブラッシングしながら確かめます。", "たくさん水を飲ませ、ゆっくり休ませます。"]) +
      _h("行く前に確かめたい「入れない犬」の決まり") + _count_table(e, "ng", [
          ("発情中の犬は入れない", r"発情"), ("病気・ノミ・ダニのある犬は入れない", r"病気|ノミ|ダニ|感染"), ("子犬の月齢・ワクチンからの日数の決まり", r"生後|か月|ヶ月|ワクチンを受けて"),
          ("かむ・攻撃するくせのある犬は入れない", r"かむ|攻撃|咬"), ("おやつ・食べ物・おもちゃの持ちこみの決まり", r"おやつ|食べ物|フード|おもちゃ|ボール")],
          "公式ページに「入れない犬など」を書いている各ドッグランを数えました") +
      _p("はじめての日は、とくに子犬の月齢とワクチンからの日数の決まりに気をつけてください。せっかく行っても入れないことがあります。") +
      _h("持ち物") + _ul([e(x) for x in BRING]) + _h("マナー") + _ul([e(x) for x in MANNER])},
 {"slug": "vaccine", "short": "ドッグランで求められる書類",
  "title": lambda: "ドッグランに必要な書類｜鑑札・狂犬病予防注射済票・混合ワクチン証明",
  "desc": lambda: f"ドッグランでよく求められる鑑札・狂犬病予防注射済票・混合ワクチンの接種証明について、どこでもらえるか、写しや写真でよいか、期限の考え方をまとめました。一覧の{TOTAL}か所のうち{nvac(RUNS)}か所が混合ワクチンも条件にしています。",
  "lede": "ドッグランの受付や登録で「鑑札と注射済票を見せてください」と言われて、あわてたことはありませんか。よく求められる書類と、そのもらい方をまとめました。",
  "list": None,
  "body": lambda e: _vac_answer() + _h("よく求められる書類") + "<dl>" + "".join(f"<dt>{t}</dt><dd>{x}</dd>" for t, x in [
      ("鑑札（かんさつ）", "犬の登録をすると、市区町村から交付される札です。マイクロチップを登録した犬は、登録証明書で代わりにするところもあります。"),
      ("狂犬病予防注射済票", "毎年1回の狂犬病予防注射を受けると、市区町村から交付されます。「その年度の済票」を求めるドッグランが多いです。"),
      ("混合ワクチンの接種証明", "動物病院で混合ワクチン（3種・5種以上など）を受けると、証明書がもらえます。「1年以内」を条件にするところが多く、「3年以内」のところもあります。"),
      ("狂犬病予防注射の猶予証明", "年をとっている、病気があるなどで注射ができないときに、獣医師が出す証明です。受け入れるかどうかはドッグランごとに違います。")]) + "</dl>" +
      _h(f"一覧の{TOTAL}か所で、求められている書類を数えると") + _count_table(e, "need", [
          ("鑑札（またはマイクロチップの登録証明）", r"鑑札|マイクロチップ"), ("狂犬病予防注射の済票・証明", r"狂犬病|済票|済証"),
          ("混合ワクチンの接種証明", r"混合|[0-9]種"), ("「1年以内」の決まりがある", r"1年以内"), ("「その年度」の済票", r"その年度|今年度|当年度"),
          ("写し・写真・画像でもよいと書いている", r"写し|コピー|写真でも|画像でも|写真で可|画像で可|データ"), ("注射ができない犬の証明（猶予・抗体）も書いている", r"猶予|抗体")],
          "各ドッグランの公式ページの「必要なもの・条件」を数えました") +
      _p("公営のドッグランは、狂犬病予防注射と鑑札（法律で決まっているもの）を確かめるところが中心で、お店・施設のドッグランは混合ワクチンの証明まで求めるところが多い、というちがいが数字にも出ています。行き先が決まったら、その場所の決まりを都道府県ごとのページで見てください。") +
      _h("写しや写真でもいい？") + _p("お店や施設のドッグランでは、証明書の写しやスマートフォンの写真でよいところがあります。公営のドッグランの登録では、原本を見せるところもあります。場所ごとの決まりは、都道府県ごとのページの「必要なもの・条件」と、それぞれの公式ページでご確認ください。") +
      _h("鑑札や済票をなくしたら") + _p('お住まいの市区町村で再交付を受けられます。窓口は<a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a>にまとめています。')},
 {"slug": "kouei-minkan", "short": "公営と民間のドッグランのちがい",
  "title": lambda: "公営と民間のドッグランのちがい｜料金・登録・設備・時間をくらべる",
  "desc": lambda: "公園などの公営のドッグランと、カフェ・商業施設・牧場などの民間のドッグラン、高速道路のSA・PAのドッグランのちがいを、料金・登録・設備・利用時間でくらべました。公式ページで確かめた料金の例も。",
  "lede": "ドッグランには、公園などの公営のもの、お店や施設のもの、高速道路のSA・PAのものがあります。どれを選ぶとよいか、ちがいをまとめました。",
  "list": None,
  "body": lambda e: '<div class="tbl"><table class="dr-tbl dr-cmp"><thead><tr><th></th><th>公営</th><th>お店・施設</th><th>高速道路SA・PA</th></tr></thead><tbody>' + "".join(
      f"<tr><th>{a}</th><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in [
       ("料金", "無料のところが多い（登録料・駐車料がかかることも）", "1頭ごとの料金がかかることが多い", "無料（高速道路の料金は別）"),
       ("登録", "はじめに利用登録がいるところが多い", "その日の受付で書類を見せることが多い", "公式ページに登録の決まりは書かれていない"),
       ("設備", "広い芝生や土。設備はシンプルなことが多い", "カフェ・シャワー・夜の照明・プールなど", "水飲み場やふん用のごみ箱があるところも"),
       ("時間", "日の出〜日没、9時〜17時など", "お店の営業時間", "24時間や日の出〜日没など")]) + "</tbody></table></div>" +
      _h(f"一覧の{TOTAL}か所を、種類ごとに数えると") + _p("上の表は大まかな傾向です。実際に公式ページに書いてあることを、種類ごとに数えました。数字は「当てはまる数／その項目を公式ページに書いているランの数」です。") + _kind_table(e) +
      f'<p class="small">{CHECKED}時点。「書いていない」は「しない」ではありません。</p>' +
      _h("お店・施設のドッグランの料金の例") + _p("公式ページに書いてある料金の例です（おすすめ順ではありません）。") + _cost_examples(e) +
      _h("どう選ぶ？") + _ul(["<b>はじめてで心配</b>：スタッフがいるお店や施設のドッグランだと、困ったときに相談しやすいです。", "<b>近くで気軽に</b>：公営のドッグランは、登録をすませておくと、散歩のついでに使えます。",
      "<b>小型犬で大きな犬がこわい</b>：小型犬エリアがあるところを選びましょう。", "<b>遠出のついでに</b>：高速道路のSA・PAのドッグランで、休けいしながら体を動かせます。"])},
 {"slug": "small-dog", "short": "小型犬エリアがあるドッグラン",
  "title": lambda: f"小型犬エリアがあるドッグラン{nsmall(RUNS)}か所｜都道府県別の一覧",
  "desc": lambda: f"小型犬用のエリアがあるドッグラン{nsmall(RUNS)}か所を、公式ページで確かめて都道府県別にまとめました。エリアの区切り（体重・体高）は場所ごとに違います。小型犬ではじめて行くときの注意も。",
  "lede": "小さな犬は、大きな犬に追いかけられるとこわい思いをすることがあります。小型犬用のエリアがあるドッグランをまとめました。",
  "list": is_small,
  "body": lambda e: _h("小型犬の区切りは場所ごとに違います") + _p("「小型犬」の区切りは、体重（5kg・8kg・10kgなど）や体高（25cm・40cmなど）で、ドッグランごとに違います。うちの子がどちらに入るか、行く前に公式ページで確かめておきましょう。") +
      _h("小型犬で行くときの注意") + _ul(["はじめは小型犬エリアがすいている時間に、短めに。", "ほかの犬に囲まれてこわがっていたら、抱っこして休ませてあげる。", "夏の地面は、体の低い小型犬ほど熱を受けやすいので、朝や夕方に。"])},
 {"slug": "large-dog", "short": "大型犬が遊べるドッグラン",
  "title": lambda: f"大型犬が遊べるドッグラン{sum(1 for d in RUNS if is_large(d))}か所｜大型犬・全犬種エリアの一覧",
  "desc": lambda: f"大型犬用や全犬種のエリアがあるドッグラン{sum(1 for d in RUNS if is_large(d))}か所を、公式ページで確かめて都道府県別にまとめました。大型犬で行くときの注意と、車がないときの移動のしかたも。",
  "lede": "大型犬が思いきり走れる場所は、近くにないことも多いです。大型犬用や全犬種のエリアがあるドッグランを、公式ページで確かめてまとめました。",
  "list": is_large,
  "body": lambda e: _h("大型犬で行くときの注意") + _ul(["大型犬は力が強いので、ほかの犬とのあいさつは、はじめはリードをつけたまま様子を見る。", "体の大きさの区切りや、入れない犬種の決まりがあるところもあるので、公式ページで確かめる。",
      "暑さに弱い犬種も多いので、夏は朝や夕方の涼しい時間に。"]) +
      _h("車がないときは") + _p('大型犬は電車やバスに乗れないことが多いです。<a href="/guide/large-dog/">大型犬の移動のガイド</a>もご覧ください。')},
 {"slug": "survey", "short": "全国のドッグランしらべ",
  "title": lambda: f"全国のドッグランしらべ{TOTAL}か所｜無料は{_pct(nfree(RUNS), sum(1 for d in RUNS if fee_tag(d)))}・登録やワクチンの条件を数えました",
  "desc": lambda: f"公式ページで確かめた全国のドッグラン{TOTAL}か所の料金・利用登録・ワクチンの条件・小型犬エリアを、公営・お店や施設・高速道路のSA・PAごとに数えました。都道府県ごとの数の表と、データの引用のしかたも。",
  "lede": "「ドッグランって無料なの？」「登録はいるの？」に、全国のドッグランの公式ページを1つずつ読んで数えた数字で答えます。数字は一覧のデータから自動で数えていて、ドッグランを足すとこのページも変わります。",
  "list": None,
  "body": lambda e: _survey_body(e, SURVEY_ORDER)},
]
# [B] SEO・AIO：独自データ記事「全国のドッグランしらべ」（2026-11-09、戦略担当の打ち手4・Nori「倍のスピードで」）。
# 数字はすべて dogrun.json（公式ページで確かめた各ランの項目）から生成のたびに数える。書いていない項目は分母に入れない。
SURVEY_ORDER = ("北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 "
                "岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 "
                "佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県").split()
def _survey_pref_table(e, order):
    head = "<tr><th>都道府県</th><th>載せている数</th><th>公営</th><th>お店・施設</th><th>SA・PA</th><th>利用料が無料</th><th>小型犬エリアあり</th></tr>"
    body = ""
    for pf in [p for p in order if p in BY]:
        rs = BY[pf]
        body += (f'<tr><th><a href="{href(pf)}">{e(pf)}</a></th><td>{len(rs)}</td>' + "".join(f"<td>{len(by_kind(rs, k))}</td>" for k, _ in _KCOLS) +
                 f"<td>{nfree(rs)}</td><td>{nsmall(rs)}</td></tr>")
    return f'<div class="tbl"><table class="dr-tbl"><thead>{head}</thead><tbody>{body}</tbody></table></div>'
def _survey_body(e, order):
    nfee = sum(1 for d in RUNS if fee_tag(d)); nreg = sum(1 for d in RUNS if reg_tag(d)); nsz = sum(1 for d in RUNS if d.get("size"))
    nv, nvw = _cnt(RUNS, "need", r"混合|[0-9]種")
    cite = "ペットタクシー予約窓口「全国のドッグランしらべ（2026年11月）」https://pet.shiokonbu.com/dogrun/survey/"
    return (_p(f'<b>まとめ</b>：公式ページで確かめた全国のドッグラン{TOTAL}か所（{len(BY)}都道府県）をしらべました。利用料が無料なのは、料金を書いている{nfee}か所のうち{nfree(RUNS)}か所（{_pct(nfree(RUNS), nfee)}）。'
               f'はじめに利用登録がいるのは、登録のことを書いている{nreg}か所のうち{nreg - nnoreg(RUNS)}か所（{_pct(nreg - nnoreg(RUNS), nreg)}）。小型犬のエリアがあるのは、エリアの区分を書いている{nsz}か所のうち{nsmall(RUNS)}か所（{_pct(nsmall(RUNS), nsz)}）。混合ワクチンの証明を求めるのは、必要なものを書いている{nvw}か所のうち{nv}か所（{_pct(nv, nvw)}）でした。')
            + _h("公営・お店や施設・高速道路のSA・PAでくらべる") + _kind_table(e)
            + _p(f"数字は「当てはまる数／その項目を公式ページに書いているランの数」です（{e(CHECKED)}時点）。公式ページに書いていないことは「しない」と数えず、分母から外しています。")
            + _h("料金のかたち") + _count_table(e, "fee", [
                ("利用料は無料", r"^(無料|利用は無料|ドッグランは無料)"), ("登録料・会員料がかかる", r"登録|会員|年会費|わんパス"),
                ("1回・1日いくら", r"1回|1日|1頭[0-9]|1頭目|1匹"), ("時間ごと（30分・1時間など）", r"30分|1時間|2時間|3時間"),
                ("2頭目から安くなる", r"2頭目|追加の犬|追加1頭"), ("貸し切りができる", r"貸切|貸し切り|プライベート"), ("土日祝は高くなる", r"土日祝")],
                "各ドッグランの公式ページの「料金」を数えました")
            + _h("利用登録のしかた") + _count_table(e, "reg", [
                ("登録はいらない", r"^いらない"), ("インターネットで申しこめる", r"WEB|ウェブ|オンライン|電子申請|ネット|サイトで"),
                ("窓口で登録する", r"窓口|管理事務所|事務所|センターで"), ("登録会・説明会・講習に出る", r"登録会|説明会|講習|しつけ方教室"),
                ("住んでいる人だけ・市町村の登録が条件", r"住民|在住|住んで|市内|町内|区内"), ("毎年・年度ごとに登録しなおす", r"毎年|年度|有効期限|更新")],
                "各ドッグランの公式ページの「利用登録」を数えました")
            + _h("必要なもの・条件") + _count_table(e, "need", [
                ("狂犬病予防注射（済票）", r"狂犬病"), ("混合ワクチン", r"混合|[0-9]種"), ("鑑札・犬の登録", r"鑑札|犬の登録|登録番号|マイクロチップ"),
                ("年齢（生後◯か月以上など）", r"生後|か月|ヶ月|歳"), ("不妊・去勢、発情中は入れない", r"発情|去勢|避妊|不妊")],
                "各ドッグランの公式ページの「必要なもの・条件」を数えました")
            + _h("都道府県ごとの数") + _p("公式ページで確かめられたところから載せているので、実際にある数ではなく、このしらべに入っている数です。数が0の種類は、まだ見つけられていないか、公式ページで確かめられていないものです。")
            + _survey_pref_table(e, order)
            + _h("しらべ方と、このデータの引用") + _p(f"それぞれのドッグランの公式ページ（自治体・公園の管理者・高速道路会社・お店）に書いてあることを、項目ごとに読み取って数えました（{e(CHECKED)}）。口コミやまとめサイトは使っていません。電話番号やおすすめの順位は載せていません。",
                f"このページの数字は、出どころを書いていただければ引用していただいてかまいません。例：{e(cite)}"))

ART = {a["slug"]: a for a in ARTICLES}
assert not set(ART) & set(PSLUG.values())

def art_links(e, skip=None):
    return '<ul class="other">' + "".join(f'<li><a href="/{SLUG}/{a["slug"]}/">{e(a["short"])}</a></li>' for a in ARTICLES if a["slug"] != skip) + "</ul>"

def art_list_html(e, cond, order):
    out = ""
    for pf in [p for p in order if p in BY]:
        rs = [d for d in BY[pf] if cond(d)]
        if not rs: continue
        inner = "".join(f'<div class="dr-row"><a href="{href(pf)}#{d["id"]}">{e(d["name"])}</a><small>{e(d.get("city", ""))}</small>{tags_html(e, d)}</div>' for d in rs)
        out += f'<section class="emg-pref" data-pref="{e(pf)}"><h3>{e(pf)}<small>（{len(rs)}か所）</small></h3>{inner}</section>\n'
    return out

def render_article(ctx, a):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/{a['slug']}/"
    title = a["title"]() + "｜ペットタクシー予約窓口"
    desc = a["desc"]()
    lst = ""
    items = []
    if a["list"]:
        sel = [d for d in RUNS if a["list"](d)]
        lst = (f'<h2>{e(a["short"])}の一覧（{len(sel)}か所）</h2><p>都道府県の順で、おすすめ順ではありません。名前を押すと、料金・時間・条件のくわしい情報を見られます。</p>'
               + art_list_html(e, a["list"], [p for _, ps in ctx["emg_regions"] for p in ps]))
        items = [{"@type": "ListItem", "position": i + 1, "url": SITE + href(d["pref"]) + "#" + d["id"], "name": d["name"]} for i, d in enumerate(sel)]
    objs = [crumbs(SITE, [("ペットタクシー予約窓口", SITE + "/"), ("全国のドッグラン", f"{SITE}/{SLUG}/"), (a["short"], url)]),
            {"@context": "https://schema.org", "@type": "Article", "headline": a["title"](), "description": desc, "dateModified": "2026-11-02",
             "author": {"@type": "Organization", "name": "ペットタクシー予約窓口"}, "mainEntityOfPage": url}]
    if a["slug"] == "survey":  # [B] AIO 11/9：独自データ記事は Dataset としても伝える
        objs.append({"@context": "https://schema.org", "@type": "Dataset", "name": "全国のドッグランしらべ", "description": desc, "url": url, "inLanguage": "ja",
                     "creator": {"@type": "Organization", "name": "ペットタクシー予約窓口"}, "spatialCoverage": "日本",
                     "variableMeasured": ["利用料（無料・有料）", "利用登録", "必要なもの・条件", "小型犬エリア", "利用時間", "都道府県ごとの数"]})
    if items:
        objs.append({"@context": "https://schema.org", "@type": "ItemList", "name": a["short"], "numberOfItems": len(items), "itemListElement": items})
    return ctx["head"](title, desc, url, ld_json(objs)) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{SLUG}/">全国のドッグラン</a> › {e(a["short"])}</nav>
    <h1><small>全国のドッグラン</small>{e(a["title"]().split("｜")[0])}</h1>
    <p class="lede">{e(a["lede"])}</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    {a["body"](e)}
    {lst}
    <p class="emg-note">{e(CHECKED)}に公式ページで確かめた情報です。料金や決まりは変わることがあるので、行く前に必ずそれぞれの公式ページでご確認ください。掲載の内容の誤りや、載せてほしいドッグランは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    <h2>ドッグランの記事</h2>
    {art_links(e, a["slug"])}
    <p><a href="/{SLUG}/">全国のドッグラン（都道府県の一覧）</a></p>
  </article></div>
</section>
{taxi_band(e)}
</main>
""" + ctx["foot_noband"]()

# ── 全国のページ（/dogrun/） ──
def render_hub(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    npref = len(BY)
    title = f"全国のドッグラン{TOTAL}か所｜公園・お店・高速道路SA・PAを都道府県別に｜ペットタクシー予約窓口"
    desc = (f"公園などの公営のドッグラン、カフェや商業施設・牧場などのドッグラン、高速道路のSA・PAのドッグラン{TOTAL}か所を、{npref}都道府県ごとにまとめた無料の一覧です。"
            "料金・利用登録・利用時間・小型犬エリアを公式ページで確かめて載せています。")
    if len(desc) > 160: desc = desc[:158] + "。"
    grid = ""
    for lab, prefs in ctx["emg_regions"]:
        cells = "".join((f'<li><a href="{href(pf)}">{e(pf)}<small>{len(BY[pf])}か所</small></a></li>' if pf in BY
                         else f'<li><span>{e(pf)}<small>—</small></span></li>') for pf in prefs)
        grid += f'<h3 class="dr-region">{e(lab)}</h3><ul class="dr-prefs">{cells}</ul>\n'
    kinds = "".join(f"<dt>{e(name)}（{len(by_kind(RUNS, k))}か所）</dt><dd>{e(text)}</dd>" for k, name, _, text in KINDS)
    body = ""
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            rs = BY.get(pf, [])
            if rs:
                inner = "".join(f'<div class="dr-row"><a href="{href(pf)}#{d["id"]}">{e(d["name"])}</a><small>{e(d.get("city", ""))}</small>{tags_html(e, d)}</div>' for d in rs)
                inner += f'<p class="emg-all"><a href="{href(pf)}">{e(pf)}のドッグラン（料金・時間・登録のくわしい表）</a></p>'
            else:
                inner = f'<p class="emg-none">{e(NONE.get(pf, "まだ載せていません。"))}見つけしだい足します。</p>'
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}</section>\n'
    faq = faq_common(e)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    ld = ld_json([
        crumbs(SITE, [("ペットタクシー予約窓口", SITE + "/"), ("全国のドッグラン", url)]),
        {"@context": "https://schema.org", "@type": "ItemList", "name": "都道府県別のドッグラン", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": f"{pf}のドッグラン", "url": SITE + href(pf)} for i, pf in enumerate(p for _, ps in ctx["emg_regions"] for p in ps if p in BY)]},
        faq_ld(faq)])
    return ctx["head"](title, desc, url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › 全国のドッグラン</nav>
    <h1><small>{npref}都道府県・{TOTAL}か所</small>全国のドッグラン</h1>
    <p class="lede">思いきり走らせてあげたい。でも、どこにあるの？　公園などの公営のドッグラン、お店や施設のドッグラン、高速道路のSA・PAのドッグランを、料金・利用登録・利用時間・エリアの区分つきで都道府県ごとにまとめました。</p>
    {stats(RUNS)}
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <p class="emg-free">この一覧は無料の情報です。どれも公式ページで確かめたことだけを書いています。順番は都道府県ごとで、おすすめ順ではありません。お店や施設のドッグランは、公式ページで確かめられたところから順に足しています。</p>
      <h2 class="emg-h">都道府県からさがす</h2>
      {grid}
      <h2 class="emg-h">ドッグランの記事</h2>
      {art_links(e)}
      <div class="emg-tips"><h4>ドッグランの種類</h4><dl>{kinds}</dl><p class="emg-tips-note">くわしいちがいは「<a href="/{SLUG}/kouei-minkan/">公営と民間のドッグランのちがい</a>」にまとめています。</p></div>
      {guide_html(e)}
      <h2 class="emg-h">全国のドッグランの一覧</h2>
      <div class="f"><label for="hospPref">都道府県でしぼりこむ</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">{e(CHECKED)}に公式ページで確かめた情報です。工事やイベント、天気で閉まることがあり、利用の方法も変わることがあるので、行く前に必ずリンク先でご確認ください。掲載の内容の誤りや、載せてほしいドッグランは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
{taxi_band(e)}
</main>
{prefkeep.LIST_JS}
""" + ctx["foot_noband"]()

def taxi_band(e, pf=None, pref_href=None):
    area = f'<li><a href="{pref_href(pf)}">{e(pf)}のペットタクシー</a></li>' if pf and pref_href else ""
    jich = f'/jichitai/#pref={quote(pf)}' if pf else "/jichitai/"
    night = f'/hospital/night/#pref={quote(pf)}' if pf else "/hospital/night/"
    return f'''<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>大型犬や多頭で、遠くのドッグランへ</h2><p>車がないとき、大型犬や何頭もいっしょのときは、ペットタクシーを予約できます（乗せられる犬の大きさや頭数は会社ごとに違います）。各社の公式サイトの料金表から計算した概算で、料金をくらべられます。当日の依頼もできます。</p></div>
    <ul class="other">{area}<li><a href="/#form">ペットタクシーの料金をくらべる（無料）</a></li><li><a href="{jich}">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="{night}">夜間・救急の動物病院</a></li><li><a href="/guide/large-dog/">大型犬の移動のガイド</a></li><li><a href="/guide/multi-pet/">多頭で乗れるペットタクシー</a></li></ul>
  </div>
</section>'''

# ── 都道府県のページ（/dogrun/<slug>/） ──
def _fac_link(e, d):
    import gen_dogrun_fac  # 施設ごとのページ（試しの30施設）があれば、カードからつなぐ
    return f'<p class="dr-links"><a href="{gen_dogrun_fac.href(d)}">{e(d["name"])}のくわしい情報（くらべる表・ここまでのペットタクシー）→</a></p>' if d["id"] in gen_dogrun_fac.IDS else ""

def card(e, d):
    rows = "".join(f"<dt>{e(lab)}</dt><dd>{e(d[k])}</dd>" for k, lab in FIELDS if d.get(k))
    srcs = [u for u in d.get("src", []) if u != d["url"]]
    more = ("<small>あわせて確かめたページ：" + "、".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{i + 1}</a>' for i, u in enumerate(srcs)) + "</small>") if srcs else ""
    return (f'<section class="dr-card" id="{d["id"]}"><h3>{e(d["name"])}</h3><p class="dr-city">{e(d["pref"])}{e(d.get("city", ""))}</p>{tags_html(e, d)}'
            f'<dl>{rows}</dl><p class="dr-links"><a href="{e(d["url"])}" target="_blank" rel="noopener">公式ページで最新の情報を見る ↗</a>{more}</p>' + _fac_link(e, d) + '</section>')

# [B] 2026-11-14 Nori「答えみたいなことからはじめて、もっと視覚的に」：県のページの最初に「先に答え」（よくある質問の答え）と数字のタイル
def _answer(e, pf, rs, faq):
    import visual as _V
    n = len(rs)
    kv = "".join(f'<li><b class="k">{e(q)}</b>{e(a)}</li>' for q, a in faq[:-1][:4])
    tiles = [(f"{n}か所", f"{pf}で公式ページを確かめたドッグラン")]
    for v, lab in [(nfree(rs), "利用料が無料と書いてある"), (nnoreg(rs), "登録なしで使えると書いてある"), (nsmall(rs), "小型犬のエリアがある")]:
        if v: tiles.append((f"{v}か所", lab))
    return f'<div class="answer"><h2 id="answer">{e(pf)}のドッグランのポイント</h2><ul class="kv">{kv}</ul></div>' + _V.stats(tiles[:4])

def render_pref(ctx, pf, rs):
    e, SITE = ctx["e"], ctx["SITE"]
    url = SITE + href(pf)
    n = len(rs)
    cities = []
    for d in rs:
        for c in d.get("city", "").split("・"):
            if c and c not in cities: cities.append(c)
    ctext = "・".join(cities[:3])
    # [B] SEO 11/9：愛知「ドッグラン」4.8位でもクリック0。題名に数（無料・小型犬エリア）を先に出す。
    _tf, _ts = nfree(rs), nsmall(rs)
    _tx = "・".join(x for x in [f"無料{_tf}か所" if _tf else "", f"小型犬エリア{_ts}か所" if _ts else ""] if x) or "料金・登録・利用時間"
    title = f"{pf}のドッグラン{n}か所｜{_tx}" + (f"（{ctext}）" if ctext and len(ctext) <= 14 else "") + "｜ペットタクシー予約窓口"
    names = "、".join(d["name"] for d in rs[:2])
    desc = (f"{pf}のドッグラン{n}か所（{kind_counts_text(rs)}。{names}{'など' if n > 2 else ''}）を、公式ページで確かめた料金・利用登録・利用時間・"
            f"エリアの区分つきでまとめました。利用料が無料は{nfree(rs)}か所。")
    if len(desc) > 160: desc = desc[:158] + "。"
    table = "".join(f'<tr><td><a href="#{d["id"]}">{e(d["name"])}</a><br><small>{e(d.get("city", ""))}</small></td><td>{e(KLAB[kind(d)])}</td><td>{e(fee_tag(d) or "—")}</td><td>{e({"登録なしで使える": "いらない", "登録がいる": "いる"}.get(reg_tag(d), "—"))}</td></tr>' for d in rs)
    cards = ""
    for k, name, _, text in KINDS:
        ks = by_kind(rs, k)
        if not ks: continue
        cards += f'<h2>{e(pf)}の{e(name)}（{len(ks)}か所）</h2><p>{e(text)}</p>' + "".join(card(e, d) for d in ks)
    faq = faq_pref(e, pf, rs)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    region = next((ps for _, ps in ctx["emg_regions"] if pf in ps), [])
    near = "".join(f'<li><a href="{href(p)}">{e(p)}のドッグラン</a></li>' for p in region if p != pf and p in BY)
    items = [{"@type": "ListItem", "position": i + 1, "url": f"{url}#{d['id']}", "name": d["name"]} for i, d in enumerate(rs)]
    ld = ld_json([
        crumbs(SITE, [("ペットタクシー予約窓口", SITE + "/"), ("全国のドッグラン", f"{SITE}/{SLUG}/"), (f"{pf}のドッグラン", url)]),
        {"@context": "https://schema.org", "@type": "ItemList", "name": f"{pf}のドッグラン", "numberOfItems": n, "itemListElement": items},
        faq_ld(faq)])
    pref_href = ctx["pref_href"]
    return ctx["head"](title, desc, url, ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{SLUG}/">全国のドッグラン</a> › {e(pf)}</nav>
    <h1><small>{n}か所・公式ページで確かめた情報</small>{e(pf)}のドッグラン</h1>
    <p class="lede">{e(pf)}の公園などの公営のドッグランや、お店・施設、高速道路のSA・PAのドッグランを、料金・利用登録・利用時間・エリアの区分つきでまとめました。行く前に、それぞれの公式ページで最新の情報を確かめてください。</p>
    {stats(rs)}
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    {_answer(e, pf, rs, faq)}
    <p class="emg-free">この一覧は無料の情報です。順番はおすすめ順ではありません。書いていない項目は、公式ページに書いていなかったものです。お店や施設のドッグランは、公式ページで確かめられたところから順に足しています。</p>
    <div class="tbl"><table class="dr-tbl"><thead><tr><th>ドッグラン（市町村）</th><th>種類</th><th>料金</th><th>登録</th></tr></thead><tbody>{table}</tbody></table></div>
    {cards}
    {guide_html(e)}
    <div class="emg-tips"><h4>{e(pf)}のドッグラン よくある質問</h4><dl>{faq_html}</dl></div>
    <p class="emg-note">{e(CHECKED)}に公式ページで確かめた情報です。工事やイベント、天気で閉まることがあり、利用の方法や料金も変わることがあるので、行く前に必ずリンク先でご確認ください。掲載の内容の誤りや、載せてほしいドッグランは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    <h2>ドッグランの記事</h2>
    {art_links(e)}
    <h2>ほかの地域のドッグラン</h2>
    <ul class="other">{near}<li><a href="/{SLUG}/">全国のドッグラン（都道府県の一覧）</a></li></ul>
  </article></div>
</section>
{taxi_band(e, pf, pref_href)}
</main>
{prefkeep.LINKS_JS}
""" + ctx["foot_noband"]()

def urls(SITE):
    return [f"{SITE}/{SLUG}/"] + [f"{SITE}/{SLUG}/{a['slug']}/" for a in ARTICLES] + [SITE + href(pf) for pf in BY]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render_hub(ctx))
    for pf, rs in BY.items():
        d = os.path.join(ROOT, SLUG, PSLUG[pf])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render_pref(ctx, pf, rs))
    for a in ARTICLES:
        d = os.path.join(ROOT, SLUG, a["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render_article(ctx, a))
