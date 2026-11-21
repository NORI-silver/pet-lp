# [B] SEO：ペットと避難（同行避難）の一覧 /hinan/ と、都道府県ごとのページ /hinan/<県>/。gen_areas.py が読み込んで使う。
# Nori 2026-11-14「シェルターとか避難所に関する記事を書いて。地域ごとも」「受け入れ可能な動物、サイズの規定とかも含めて」。
# 守ること：都道府県・市区の公式ページの情報だけ（tools/hinan.json、出どころと確認日つき）。書いていないことは「書いていない」。
#   避難所の一覧は作らない（公式の一覧・地図へのリンクだけ）。電話番号は載せない。順位・おすすめなし。
#   ペットタクシーの話は、下の「前もって預け先へ移すとき」の節だけ（tools/taxi_cta.py がボタンを足す）。
# 人口の多い県から順に足す（第1弾 2026-11-14：東京都・神奈川県・大阪府・愛知県・埼玉県）。
import json, os, re
import gen_dogrun
import visual as V
import hinan_ans as HA
from guides_hinan import HINAN_GUIDES, ITEMS, CHECKED, MARK, table_rows, N, N_CAGE, SIZES, BREEDS, SEIREI

SLUG = "hinan"
PSLUG = gen_dogrun.PSLUG
PUBLISHED = "2026-11-14"
MODIFIED = "2026-11-14"

FLAG_TXT = {"yes": "受け入れる", "no": "受け入れない", "hard": "むずかしい場合がある", "cond": "条件つき・一部は受け入れない", None: "不明"}
KINDS = [("dog", "犬"), ("large", "大型犬"), ("cat", "猫"), ("small", "うさぎ・ハムスターなど"), ("bird", "小鳥"), ("reptile", "爬虫類")]

def by_pref():
    out = {}
    for it in ITEMS:
        out.setdefault(it["pref"], []).append(it)
    return out

def href(pf):
    return f"/{SLUG}/{PSLUG[pf]}/"

# 全国の市区町村（tools/municipalities.json、Code for FUKUI の localgovjp・CC0 から。slug は読みのローマ字）
MUNI = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "municipalities.json"), encoding="utf-8"))
CSLUG = {(m["pref"], m["name"]): m["slug"] for m in MUNI}
MUNI_ORDER = {(m["pref"], m["name"]): i for i, m in enumerate(MUNI)}
CHUKAKU = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jichitai.json"), encoding="utf-8")).get("_chukaku", [])) or {
    c["city"] for c in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jichitai.json"), encoding="utf-8"))["cities"] if c["kind"] == "中核市"}
_HJ = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hinan.json"), encoding="utf-8"))
NONE = [tuple(x[:2]) for x in _HJ.get("none", [])]  # しらべたが、ペットと避難のページが見つからなかった市区町村 [県, 名前, 理由]

# 薄いページを作らない（Nori 2026-11-14「薄い記事は撲滅させてね。全部濃い記事にして」）。
# 中身の点数＝受け入れる動物・動物ごとの印・ケージ・飼う場所・大きさ／受け入れない動物・決まり2つ以上・避難所の一覧 の数（7点まで）。
# 市区町村は RICH_CITY 点以上で1ページ、足りなければ県のページの中に短く載せる。県のページは県と市区町村の合計が RICH_PREF 点以上で出す。
RICH_CITY, RICH_PREF = 5, 6
def score(it):
    return sum([bool(it.get("animals")), any(v for v in it["flags"].values()), bool(it.get("cage")), bool(it.get("place")),
                bool(it.get("size") or it.get("no")), len(it.get("rules") or []) >= 2, bool(it.get("map"))])
# Nori 2026-11-14「てか、そもそも薄い記事作らないで」：点数が足りても、書き出したあと tools/thin_gate.py で
# そのページだけの字数（ひな形の文を除く）を数え、足りないページは作らない（市区町村は県のページの中へ、県は一覧で「まだ」）。
THIN, PREF_THIN = set(), set()
def has_page(it):
    return it["kind"] == "city" and score(it) >= RICH_CITY and (it["pref"], it["name"]) not in THIN
def pref_ok(its):
    return sum(score(x) for x in its) >= RICH_PREF and its[0]["pref"] not in PREF_THIN

def href_city(it):
    return f"/{SLUG}/{PSLUG[it['pref']]}/{CSLUG[(it['pref'], it['name'])]}/"

CSS = """<style>
.hn-card{background:#fff;border:1.5px solid var(--line);border-radius:18px;padding:14px 16px 8px;margin:0 0 14px}
.hn-card h3{margin:0 0 8px;font-size:1.08rem}
.hn-more>summary{cursor:pointer;font-weight:700;color:var(--o-d,#c2410c);font-size:.9rem;padding:8px 0}
.hn-more[open]>summary{margin-bottom:4px}
.hn-card dl{margin:0;display:grid;grid-template-columns:1fr;gap:2px 0}
.hn-card dt{font-size:.74rem;font-weight:700;color:var(--ink-3);margin-top:8px}
.hn-card dd{margin:0;line-height:1.75;font-size:.92rem}
.hn-card ul{margin:2px 0 0;padding-left:1.2em;line-height:1.75;font-size:.92rem}
.hn-flags{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0!important;margin:4px 0 0!important}
.hn-flags li{font-size:.78rem;border-radius:999px;padding:2px 10px;background:#f3f1ee;color:#3c4043}
.hn-flags li.yes{background:#e6f4ea;color:#1e7d4f}.hn-flags li.no{background:#fde8e6;color:#b3261e}
.hn-flags li.hard,.hn-flags li.cond{background:#fff4e0;color:#8a5300}
.hn-wsel{width:100%;font-size:1rem;padding:10px;border:1.5px solid var(--line);border-radius:12px;background:#fff;margin:6px 0 0}
.hn-src{font-size:.74rem;color:var(--ink-3);margin:10px 0 4px;line-height:1.6}
.hn-src a{color:var(--ink-3)}
.hn-reg{margin:0;padding:5px 0;border-bottom:1px solid var(--line);font-size:.86rem;line-height:1.9}
.hn-reg b{display:inline-block;min-width:6.5em;color:var(--ink-3,#777);font-size:.76rem;font-weight:700}
.hn-reg a{margin-right:.9em;white-space:nowrap}
.hn-reg a[aria-current]{font-weight:800;color:var(--ink,#222);text-decoration:none}
.hn-pref{display:flex;flex-wrap:wrap;gap:4px 6px;list-style:none;padding:0;margin:6px 0 14px}
.hn-pref a{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 10px;background:#fff;font-size:.84rem;font-weight:700;text-decoration:none}
.hn-none{font-size:.84rem;color:var(--ink-3);line-height:1.7}
</style>"""

def _flags(e, it):
    return '<ul class="hn-flags">' + "".join(
        f'<li class="{it["flags"].get(k) or "unk"}">{e(lab)}：{e(FLAG_TXT[it["flags"].get(k)])}</li>' for k, lab in KINDS) + "</ul>"

# [B] Nori 2026-11-16「文字ばかりで辛いからアイコンなどVisualでわかりやすく」：動物ごとの決まりはアイコンのマスで見せる（文字は残す・JSなし）
ICON = {"dog": "🐕", "large": "🦮", "cat": "🐈", "small": "🐇", "bird": "🐦", "reptile": "🦎"}
SHORT = {"dog": "犬", "large": "大型犬", "cat": "猫", "small": "うさぎ・ハムスター", "bird": "小鳥", "reptile": "爬虫類"}
MK = {"yes": ("○", "受け入れる", "yes"), "no": ("×", "受け入れない", "no"), "hard": ("△", "むずかしい場合あり", "hard"),
      "cond": ("△", "条件つき", "cond"), None: ("？", "不明", "unk")}
CODE = {"yes": "y", "no": "n", "hard": "h", "cond": "c", None: "-"}
AG_CSS = """<style>
.hn-ag{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;list-style:none;padding:0!important;margin:8px 0 10px!important}
.hn-ag li{border-radius:14px;padding:10px 4px 8px;text-align:center;background:#f3f1ee;color:#3c4043;line-height:1.3}
.hn-ag .i{font-size:1.9rem;display:block;line-height:1.15}
.hn-ag b{display:block;font-size:.8rem;margin:2px 0}
.hn-ag .m{display:block;font-size:.78rem;font-weight:700}
.hn-ag .m::before{content:attr(data-k);display:block;font-size:1.15rem;line-height:1.1}
.hn-ag li.yes{background:#e6f4ea;color:#1e7d4f}.hn-ag li.no{background:#fde8e6;color:#b3261e}
.hn-ag li.hard,.hn-ag li.cond{background:#fff4e0;color:#8a5300}.hn-ag li.unk{color:#80868b}
.hn-rows{list-style:none;padding:0!important;margin:6px 0 4px!important}
.hn-rows li{display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-top:1px dashed var(--line);font-size:.92rem;line-height:1.7}
.hn-rows li:first-child{border-top:0}
.hn-rows .i{font-size:1.4rem;line-height:1.2;flex:0 0 1.8em;text-align:center}
.hn-sum{font-size:.8rem;color:var(--ink-3);line-height:1.7;margin:6px 0 0}
.hn-rows b{display:inline-block;font-size:.78rem;color:var(--ink-3);margin-right:.5em;white-space:nowrap}
.hn-rows li{padding:6px 0;font-size:.88rem;line-height:1.55}
.hn-n{font-size:.8rem;color:var(--ink-3);white-space:nowrap;font-weight:600}
.art ul.hn-terms,.hn-terms{list-style:none;padding:0!important;margin:8px 0 16px;border-top:1px solid var(--line)}
.hn-terms li{display:flex;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid var(--line);line-height:1.5;font-size:.84rem;color:#3c4043;margin:0}
.hn-terms .i{flex:0 0 3.2em;font-size:1.15rem;line-height:1;text-align:center;letter-spacing:-.1em}
.hn-terms b{flex:0 0 6.6em;font-size:.88rem;color:var(--ink,#222)}
.hn-terms li.wide{grid-column:auto}
@media(min-width:720px){.hn-ag{grid-template-columns:repeat(6,minmax(0,1fr))}}
</style>"""

CSS = CSS + AG_CSS

def agrid(e, it):
    f = it["flags"]
    ks = [k for k, _ in KINDS if f.get(k)]
    if not ks:  # 書いていないことは出さない（Nori 2026-11-16 佐倉市のスクショ「分からない」の箱はいらない）
        return ""
    return '<ul class="hn-ag">' + "".join(
        f'<li class="{MK[f.get(k)][2]}"><span class="i" aria-hidden="true">{ICON[k]}</span><b>{e(SHORT[k])}</b>'
        f'<span class="m" data-k="{MK[f.get(k)][0]}">{e(MK[f.get(k)][1])}</span></li>' for k in ks) + "</ul>"

# 短い行にする：最初の1文だけ（くわしくは下の決まりの欄に全文）。「危険な動物は不可」のようなどこでも同じことは出さない
def first(t, n=60):
    if not t: return ""
    t = t.split("。")[0] + ("。" if "。" in t else "")
    return t if len(t) <= n else t[:n - 1] + "…"

GENERIC_NO = re.compile(r"^(人に危害を[^。]*|危険な動物|特定動物（危険な動物）|特定動物)(は|を)?[^。、]{0,20}(できない|受け入れない|できません|対象外)。?$")

def no_text(t):
    return "" if (not t or GENERIC_NO.match(t.strip())) else first(t)

def arows(e, it):
    cage = "持っていく（ケージの中で飼う）" if it.get("cage_req") else first(it.get("cage"))
    lk, la = large_answer(it)
    rows = [("🦮", "大型犬は？", large_short(it)), ("🧺", "ケージ", cage), ("🏠", "飼う場所", first(it.get("place"))),
            ("⚠️", "受け入れない動物", no_text(it.get("no")))]
    rows = [r for r in rows if r[2]]
    if not rows: return ""
    return '<ul class="hn-rows">' + "".join(f'<li><span class="i" aria-hidden="true">{i}</span><span><b>{e(t)}</b>{e(v)}</span></li>' for i, t, v in rows) + "</ul>"

# 市区町村の名前のリンク（#名前）で来たら、その市区町村のたたんだ決まりを開く
HN_OPEN = "<script>(function(){function o(){try{var t=document.getElementById(decodeURIComponent(location.hash.slice(1)));var d=t&&t.querySelector('details.hn-more');if(d)d.open=true}catch(e){}}o();addEventListener('hashchange',o)})();</script>"

def card(e, it, fold=False, grid=True):
    def row(t, v):
        return f"<dt>{e(t)}</dt><dd>{e(v)}</dd>" if v else ""
    rules = ("<dt>そのほかの決まり・備え</dt><dd><ul>" + "".join(f"<li>{e(r)}</li>" for r in it["rules"]) + "</ul></dd>") if it.get("rules") else ""
    if it.get("details"):  # 公式ページに書いてある、そのほかのこと（在宅避難・協定・受付のしかたなど）
        rules += "<dt>そのほかのこと</dt><dd><ul>" + "".join(f"<li>{e(r)}</li>" for r in it["details"]) + "</ul></dd>"
    links = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></li>' for t, u in it.get("links") or [])
    # 自治体にメールでたずねて分かったこと（Nori 2026-11-16「知りたい情報がしれたのなら記事に反映」）：出どころは「◯◯市の回答（2026年11月）」
    if it.get("reply"): links = f'<li>{e(it["reply"])}</li>' + links
    mp = f'<dt>避難所の場所</dt><dd><a href="{e(it["map"][1])}" target="_blank" rel="noopener">{e(it["map"][0])}</a></dd>' if it.get("map") else ""
    # fold：県のページの「ほかの市区町村」は、印（受け入れる動物）だけ見せて、くわしい決まりはたたむ（2026-11-16 見直し「1ページが長すぎる」。中身はHTMLに残す）
    return (f'<section class="hn-card" id="{e(it["name"])}"><h3>{e(it["name"])}</h3>{agrid(e, it) if grid else ""}'
            + ('<details class="hn-more"><summary>くわしい決まりと出どころを見る</summary>' if fold else '') + '<dl>'
            + row("考え方", it.get("policy")) + row("受け入れる動物", it.get("animals"))
            + (row("受け入れない・むずかしい動物", it["no"]) if it.get("no") else "")
            + row("大きさの決まり", it.get("size")) + row("ケージ・リード", it.get("cage")) + row("避難所で飼う場所", it.get("place"))
            + rules + mp + "</dl>"
            + f'<p class="hn-src">出どころ（{e(CHECKED)}時点）：</p><ul class="hn-src">{links}</ul>' + ('</details>' if fold else '') + '</section>')

def fit_rows(its):
    """県のページの「うちの子で見る」：大きさ・種類ごとに、その県の自治体の記載をならべる"""
    def line(it, txt): return f"{it['name']}：{txt}"
    def large(it):
        f = it["flags"].get("large")
        if it.get("size"): return it["size"]
        if f == "yes": return "受け入れると書いている"
        return "大型犬・大きさについては書いていない（市区町村・避難所に確かめる）"
    def small(it):
        fs, fb = it["flags"].get("small"), it["flags"].get("bird")
        if fs in ("yes",) or fb in ("yes",): return it.get("animals") or "受け入れると書いている"
        if fs or fb: return FLAG_TXT[fs or fb] + (f"（{it['no']}）" if it.get("no") else "")
        return "書いていない（市区町村・避難所に確かめる）"
    def flag(it, k):
        return FLAG_TXT[it["flags"].get(k)] + ("" if it["flags"].get(k) else "（市区町村・避難所に確かめる）")
    def known(rows):  # 書いていない自治体の行は並べない
        for r in rows:
            r["items"] = [x for x in r["items"] if x] or ["書いている自治体はありませんでした。避難所でご確認ください。"]
        return rows
    return known([
        {"k": ["s"], "h": "小型犬（10kg未満）", "items": [line(it, flag(it, "dog")) for it in its if it["flags"].get("dog")]},
        {"k": ["m", "l"], "h": "中型犬・大型犬（10kg以上）", "items": [line(it, large_short(it)) for it in its]},
        {"k": ["cat"], "h": "猫", "items": [line(it, flag(it, "cat")) for it in its if it["flags"].get("cat")]},
        {"k": ["all"], "tag": "ほかの動物", "h": "うさぎ・ハムスター・小鳥・爬虫類", "items": [line(it, small(it)) for it in its if it["flags"].get("small") or it["flags"].get("bird")]},
    ])

# 大型犬はどうなる？（Nori 2026-11-16「飼い主は自分の子はどうなるんだろうを心配してる。それに回答が得られるようにしないと意味ない」）
# 自治体の文から、大型犬についての答えを1つに決める。犬のことと読めないもの（「大型の動物」だけ）は、犬について言い切らない。
_DOG = r"(?:大型犬|中型犬|特定犬|大型の犬|\d+kg|体高|秋田犬|土佐犬)"
def large_answer(it):
    """(種類, 答えの文)。種類：ok つないで受け入れ／cage ケージに入る大きさまで／no 大型犬は受け入れない／hard 大型の動物はむずかしい／small 小型が対象／none 書いていない"""
    if it.get("large_ans"):  # 問い合わせのお答えや、読んで決めた答え
        return it.get("large_kind", "ok"), it["large_ans"]
    nm = it["name"]; s = it.get("size") or ""; no = it.get("no") or ""; t = s + "／" + no
    f = it["flags"].get("large")
    m = re.search(_DOG + r"[^。]*?(?:受け入れ(?:ない|できない|られない)|対象外|同行避難できない|入れない|断る|禁止)", t) or re.search(r"(?:受け入れ(?:ない|できない))[^。]*" + _DOG, t)
    if m:
        why = next((x for x in re.split(r"(?<=。)", t.replace("／", "。")) if re.search(_DOG, x)), "")
        may = re.search(r"(?:こと|場合)がある", why or m.group(0))
        return "no", f"{nm}は、大型犬を避難所で受け入れ{'ないことがある' if may else 'ない'}としています。" + (f"（{why.strip('。')}）" if why else "")
    if re.search(r"(?:ケージ|キャリー|クレート)[^。]{0,12}(?:入る|入れられる|入りきら)|片手で持ち運べる|ケージに入れることが条件|入ることが条件|入るか", s):
        return "cage", f"{nm}は、ケージやキャリーに入る大きさの子までとしています。入らない大型犬は、避難所に入れないことがあります。"
    if f == "no" or re.search(r"大型(?:の)?(?:動物|ペット)[^。]*(?:受け入れ(?:ない|できない)|断る|不可|連れて行けない|入れない)", t):
        return "nobig", f"{nm}は「大型の動物は避難所で受け入れない」としています。大型犬がこれにあたるかは書いていないので、入れないこともあると考えておきましょう。"
    if re.search(r"(?:大型犬|入らない(?:子|犬|ペット|大型))[^。]*(?:つな|係留|リード)|大きさの(?:決まり|上限|制限)は(?:ない|ありません)|大型犬用|中型犬以上の犬が対象|小型犬と大型犬で場所を分け|大きさに関わらず|大型犬も", s) or f == "yes":
        return "ok", f"{nm}は、大型犬も同行避難の対象です。ケージに入らない子は、決められた場所にリードでつなぐ形になります。"
    if re.search(r"大型の(?:動物|ペット)|大型動物", t) or f in ("hard", "cond"):
        return "hard", f"{nm}は「大型の動物は避難所での受け入れがむずかしい」としていて、大型犬が入れるかは、はっきり書いていません。"
    if re.search(r"小型", s):
        return "small", f"{nm}は「比較的小型の動物」を対象にしていて、大型犬が入れるかは、はっきり書いていません。"
    return "none", f"{nm}は、ペットの体の大きさの決まりを書いていません。国の手引きでは、同行避難の対象は「犬や猫など」で、大きさの区別はありません。"

def large_short(it):
    """大型犬の答えを1文で（一覧の行・さがす欄用）。「書いていません」とは言わない"""
    k, a = large_answer(it)
    if k == "none": return "犬の大きさによる区別はありません。"
    return a.split("。")[0].replace(it["name"] + "は、", "") + "。"

LARGE_TIP = {
    "allowed": "持ち物と過ごす場所は、開設する避難所の案内に従いましょう。",
    "check": "受け入れと過ごす場所を確認し、必要なら別の預け先も考えておきましょう。",
    "ok": "じょうぶなリード（つなぐ用の長いもの）・マット・ふんの袋を持って行きましょう。屋外につなぐことが多いので、雨や暑さ・寒さの対策もしておくと安心です。",
    "cage": "大型犬は、車の中で過ごす・親戚や知人の家・ペットホテルや動物病院など、避難所のほかの行き先を前もって決めておきましょう。",
    "nobig": "大型犬は、車の中で過ごす・親戚や知人の家・ペットホテルや動物病院など、避難所のほかの行き先を前もって決めておきましょう。",
    "no": "大型犬は、車の中で過ごす・親戚や知人の家・ペットホテルや動物病院など、避難所のほかの行き先を前もって決めておきましょう。",
    "hard": "入れないときに備えて、車の中で過ごす・親戚や知人の家・ペットホテルなどの行き先も決めておきましょう。連れて行くときは、じょうぶなリードとクレートを持って行きます。",
    "small": "入れないときに備えて、車の中で過ごす・親戚や知人の家・ペットホテルなどの行き先も決めておきましょう。連れて行くときは、じょうぶなリードとクレートを持って行きます。",
    "none": "避難所では、人と別の場所でケージに入れるか、リードでつなぐ形がほとんどです。大型犬はケージに入らないことが多いので、じょうぶなリードを持って行き、入れないときの行き先（車・親戚や知人の家・ペットホテル）も決めておきましょう。",
}

def faq_for(pf, its):
    """飼い主が知りたいこと（うちの子は連れて行ける？どこで過ごす？何を持って行く？）に、そのまま答える。引用の「…とされています」は使わない"""
    out = []
    for it in its:
        nm = it["name"]
        if it.get("policy"):
            out.append((f"{nm}では、ペットと一緒に避難できますか？", f"{nm}では、{it['policy']}"))
        k, ans = large_answer(it)
        out.append((f"{nm}の避難所に、大型犬は連れて行けますか？", ans + LARGE_TIP[k]))
        if it.get("place"):
            out.append((f"{nm}の避難所で、ペットはどこで過ごしますか？",
                        f"{nm}では、{it['place']}" + ("" if "避難所ごと" in it["place"] else "くわしい場所は避難所ごとに決まります。")))
        if it.get("cage") or it.get("cage_req"):
            out.append((f"{nm}の避難所に、ケージは持って行きますか？", f"{nm}では、" + (it.get("cage") or "ケージを持って行きます。")))
        a = it.get("animals")
        if a:
            out.append((f"{nm}の避難所には、どんな動物を連れて行けますか？", f"{nm}では、{a}" + (f"なお、{it['no']}" if it.get("no") else "")))
        elif it.get("no"):
            out.append((f"{nm}の避難所に連れて行けない動物はいますか？", f"{nm}では、{it['no']}"))
    return out[:12]

def _ld(SITE, url, title, desc, crumbs, faq):
    items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(crumbs)]
    d = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items},
         {"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "datePublished": PUBLISHED,
          "dateModified": MODIFIED, "mainEntityOfPage": url, "inLanguage": "ja",
          "author": {"@type": "Organization", "name": "ペットタクシー予約窓口", "url": SITE + "/"},
          "publisher": {"@type": "Organization", "name": "ペットタクシー予約窓口", "url": SITE + "/"}}]
    if faq:
        d.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    return '<script type="application/ld+json">\n' + json.dumps(d, ensure_ascii=False, indent=1) + "\n</script>"

def _taxi(e, where=""):
    # tools/taxi_cta.py がこの節（見出しに「ペットタクシー」）の後ろに、その県のフォームへのボタンを足す
    return f"""<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>台風の前などに、預け先へ移すとき（ペットタクシー）</h2><p>前もって分かる災害では、早めに親せきの家やペットホテルへ移っておくと、ペットにも家族にも負担が少なくなります。車がないときは、ペットタクシーで移る方法もあります（災害のさなかは道路や車の状況で動けないことがあります）。</p></div>
  </div>
</section>"""

def _guides(e):
    return '<ul class="other">' + "".join(f'<li><a href="/guide/{e(g["slug"])}/">{e(g["title"])}</a></li>' for g in HINAN_GUIDES) + "</ul>"

def _pref_links(e, done, cur=None, regions=None, title="都道府県のページから見る"):
    # [B] Nori 2026-11-16「うざい、もっとこんぱくとに」：47の大きなボタンはやめ、地方ごと1行の小さな文字のリンクをたたむ
    regions = regions or [("", done)]
    rows = "".join(
        f'<p class="hn-reg">' + (f'<b>{e(r)}</b>' if r else "") + "".join(
            (f'<a href="{href(pf)}"' + (' aria-current="page"' if pf == cur else "") + f'>{e(pf.rstrip("県府都") if pf != "北海道" else pf)}</a>')
            for pf in ps if pf in done) + "</p>"
        for r, ps in regions if any(pf in done for pf in ps))
    return f'<details class="hn-more hn-prefs"><summary>{e(title)}</summary>{rows}</details>'

def render_top(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    bp = by_pref()
    done = [pf for _, ps in ctx["emg_regions"] for pf in ps if pf in bp and pref_ok(bp[pf])]
    rest = [pf for _, ps in ctx["emg_regions"] for pf in ps if pf not in done]
    title = "ペットの同行避難と避難所の決まり｜受け入れる動物・大型犬・ケージ（都道府県・市区ごと）｜ペットタクシー予約窓口"
    desc = (f"ペットと避難するときの「同行避難」と「同伴避難」のちがい、避難所で受け入れる動物（犬・猫・うさぎ・小鳥・爬虫類）、大型犬の扱い、ケージの決まりを、"
            f"{len(done)}都道府県・{N}の自治体ごとにまとめました。")
    faq = HINAN_GUIDES[0]["faq"][:6]
    ld = _ld(SITE, url, "ペットの同行避難と避難所の決まり", desc, [("ペットタクシー予約窓口", "/"), ("ペットと避難", f"/{SLUG}/")], faq)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › ペットと避難</nav>
    <h1><small>同行避難・同伴避難・避難所で受け入れる動物の決まり</small>ペットと避難するとき</h1>
    <p class="lede">市区町村をえらぶと、避難所に連れて行ける動物とケージの決まりがすぐ分かります。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    {finder(e, [p for _, ps in ctx["emg_regions"] for p in ps])}
    <h2 id="answer">まず知っておきたいこと</h2>
    <ul class="hn-terms">
    <li><span class="i" aria-hidden="true">🐕‍🦺🏫</span><b>同行避難</b>いっしょに避難所まで逃げること。同じ部屋とは限らない</li>
    <li><span class="i" aria-hidden="true">🏠🐈</span><b>同伴避難</b>避難所で飼い主が世話をすること。これも同じ部屋とは限らない</li>
    <li><span class="i" aria-hidden="true">🐕🐈</span><b>犬・猫</b>多くの自治体が受け入れる</li>
    <li><span class="i" aria-hidden="true">🐇🐦🦎</span><b>うさぎ・小鳥など</b>市区町村ごとに違う</li>
    <li><span class="i" aria-hidden="true">🦮</span><b>大型犬</b>決まりを書く自治体は少ない。預け先も決めておく</li>
    <li><span class="i" aria-hidden="true">🧺</span><b>ケージ</b>飼い主が持っていく。避難所に用意はないことが多い</li>
    </ul>
    <p class="hn-x">ペットと過ごせる動物避難所（民間の施設をふくむ）は、NPO法人が運営する<a href="https://uchitoko.jp/" target="_blank" rel="noopener">うちトコ動物避難所マップ</a>でもさがせます。</p>
    {_pref_links(e, done, regions=ctx["emg_regions"])}
  </article></div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="emg">
      <div class="emg-tips" id="faq"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">{e(CHECKED)}時点の情報です。避難所の決まりは変わることがあり、災害の状況や避難所ごとにも違います。必ずリンク先と、お住まいの市区町村でご確認ください。誤りは<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>くわしい記事</h2><p>避難のしかたと、日ごろの備えを記事でまとめています。</p></div>
    {_guides(e)}
    <div class="sh"><h2>ほかの窓口の案内</h2><p>はぐれたときの届け出先や、預け先もまとめています。</p></div>
    <ul class="other"><li><a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="/guide/lost-pet/">ペットが迷子になったら</a></li><li><a href="/pet-hotel/">大型犬OK・猫専用のペットホテル</a></li><li><a href="/hospital/night/">夜間・救急の動物病院</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li></ul>
  </div>
</section>
{_taxi(e)}
</main>
""" + ctx["foot_noband"]()

def render_pref(ctx, pf, its, done):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}{href(pf)}"
    prefs_it = [it for it in its if it["kind"] == "pref"]
    allc = sorted([it for it in its if it["kind"] == "city"], key=lambda x: MUNI_ORDER.get((pf, x["name"]), 9999))
    cities = [x for x in allc if has_page(x)]
    small = [x for x in allc if not has_page(x)]
    big = [x for x in allc if x["name"] in SEIREI or x["name"] in CHUKAKU]
    head_names = "・".join(x["name"] for x in (big or allc)[:3])
    title = (f"{pf}のペット同行避難｜市区町村ごとの避難所の決まり（{head_names}など）｜ペットタクシー予約窓口" if allc else
             f"{pf}のペット同行避難｜避難所で受け入れる動物・大型犬・ケージの決まり｜ペットタクシー予約窓口")
    desc = (f"{pf}でペットと避難するときの決まりを、{pf}と{len(allc)}の市区町村ごとにまとめました。避難所で受け入れる動物（犬・猫・うさぎ・小鳥・爬虫類）、"
            f"大型犬の扱い、ケージ・リード、避難所で飼う場所、受付の手続き、ペットを受け入れる避難所の調べ方。" if allc else
            f"{pf}でペットと避難するときの決まりを、{pf}の決まりをまとめました。避難所で受け入れる動物、大型犬の扱い、ケージ・リード、避難所で飼う場所、ペットを受け入れる避難所の調べ方。")
    faq = faq_for(pf, prefs_it + big[:3] if big else prefs_it + allc[:3])
    ld = _ld(SITE, url, f"{pf}のペット同行避難と避難所の決まり", desc,
             [("ペットタクシー予約窓口", "/"), ("ペットと避難", f"/{SLUG}/"), (pf, href(pf))], faq)
    show = prefs_it + allc
    rows = [["自治体", "犬", "大型犬", "猫", "小動物・鳥", "爬虫類", "ケージ持参"]] + [
        [it["name"], MARK[it["flags"].get("dog")], MARK[it["flags"].get("large")], MARK[it["flags"].get("cat")],
         MARK[it["flags"].get("small") or it["flags"].get("bird")], MARK[it["flags"].get("reptile")], "要" if it.get("cage_req") else "—"] for it in show]
    fit_its = prefs_it + sorted(big or allc, key=lambda x: -sum(1 for v in x["flags"].values() if v))[:10]
    fit = "" if not any(any(x["flags"].values()) or x.get("size") for x in fit_its) else V.block(("breeds", {"title": f"うちの子の大きさ・種類で、{pf}の決まりを見る", "rows": fit_rows(fit_its), "sizes": SIZES, "breeds": BREEDS,
                              "lead": f"{'・'.join(it['name'] for it in fit_its)}の決まりを、大きさ・種類ごとに並べました。"
                                      + ("ほかの市区町村は、下のそれぞれのページで見られます。" if len(allc) > len(fit_its) - len(prefs_it) else ""),
                              "note": "書いていない自治体も「受け入れない」という意味ではありません。避難所ごとの決まりもあるので、お住まいの市区町村で確かめてください。"}))
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    lede = "市区町村をえらぶと、その市区町村の決まりがすぐ分かります。"
    pol = (prefs_it[0].get("policy") if prefs_it else None) or (allc[0].get("policy") if allc else "") or ""
    city_links = ('<ul class="hn-pref">' + "".join(f'<li><a href="{href_city(it)}">{e(it["name"])}</a></li>' for it in cities) + "</ul>") if cities else ""
    if len(cities) > 12: city_links = f'<details class="hn-more" open><summary>市区町村のページ（{len(cities)}）</summary>{city_links}</details>'
    nf = [n for (p_, n) in NONE if p_ == pf]
    rest = [m["name"] for m in MUNI if m["pref"] == pf and m["name"] not in {x["name"] for x in allc} and m["name"] not in nf]
    oth = nf + rest
    cov = (f'<details class="hn-more"><summary>ほかの市区町村（{len(oth)}）</summary><p class="hn-none">{e("・".join(oth))}。避難所の決まりは、それぞれの市区町村の防災の担当にご確認ください。</p></details>') if oth else ""
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{SLUG}/">ペットと避難</a> › {e(pf)}</nav>
    <h1><small>避難所で受け入れる動物・大型犬・ケージの決まり</small>{e(pf)}のペット同行避難</h1>
    <p class="lede">{e(lede)}</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    {finder(e, [p for _, ps in ctx["emg_regions"] for p in ps], pf)}
    {HA.block(e, prefs_it[0], pf, large_answer(prefs_it[0]), title=f"うちの子は、{pf}の避難所でどうなる？") if prefs_it else ""}
    <div class="answer"><h2 id="answer">{e(pf)}の決まり</h2>{(agrid(e, prefs_it[0]) + '<p class="hn-none">' + e(pol) + '</p>') if prefs_it else '<p>' + e(pol) + '</p>'}</div>
    {('<h2 id="city">市区町村ごとのページ</h2>' + city_links) if cities else ""}
    {cov}
    {fit}
    {('<h2 id="detail">' + e(pf) + 'が出している決まりの全文と出どころ</h2>' + "".join(card(e, it) for it in prefs_it)) if prefs_it else ""}
    {('<h2 id="more">ほかの市区町村の決まり</h2>' + "".join(card(e, it, True) for it in small) + HN_OPEN) if small else ""}
    <h2 id="faq">よくある質問</h2>
    <dl class="emg-tips">{faq_html}</dl>
    <p class="emg-note">{e(CHECKED)}時点の情報です。避難所の決まりは変わることがあり、災害の状況や避難所ごとにも違います。必ずリンク先でご確認ください。誤りは<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
  </article></div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>くわしい記事</h2><p>同行避難と同伴避難のちがい、持ち出し品のリストなど。</p></div>
    {_guides(e)}
    {_pref_links(e, done, pf, ctx["emg_regions"], "ほかの都道府県の決まりを見る")}
    <ul class="other"><li><a href="/{SLUG}/">ペットと避難するとき（全国の一覧）</a></li><li><a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="/guide/lost-pet/">ペットが迷子になったら</a></li></ul>
  </div>
</section>
{_taxi(e, pf)}
</main>
""" + ctx["foot_noband"]()

def _answer(it):
    """市区町村のページの「ポイント」：受け入れる動物・大型犬・ケージを一文ずつ"""
    f = it["flags"]
    acc = [lab for k, lab in KINDS if f.get(k) == "yes" and k != "large"]
    out = []
    if it.get("policy"): out.append(it["policy"])
    if acc: out.append("受け入れる動物：" + "・".join(acc) + "。")
    cnd = [lab for k, lab in KINDS if f.get(k) in ("cond", "hard") and k != "large"]
    if cnd: out.append("条件つき・むずかしい場合があると書いてある動物：" + "・".join(cnd) + (f"（{it['no']}）" if it.get("no") else "") + "。")
    ng = [lab for k, lab in KINDS if f.get(k) == "no" and k != "large"]
    if ng: out.append("受け入れないと書いてある動物：" + "・".join(ng) + "。")
    if it.get("size") or f.get("large"): out.append("大型犬：" + (it.get("size") or FLAG_TXT[f.get("large")]))
    if it.get("cage_req") or it.get("cage"): out.append("ケージ・キャリー：" + ("持っていく、またはケージの中で飼うと書いてある。" if it.get("cage_req") else it["cage"]))
    return out

def render_city(ctx, pf, it, sibs, done):
    e, SITE = ctx["e"], ctx["SITE"]
    nm = it["name"]
    url = f"{SITE}{href_city(it)}"
    title = f"{nm}のペット同行避難｜避難所で受け入れる動物・大型犬・ケージ（{pf}）｜ペットタクシー予約窓口"
    acc = [lab for k, lab in KINDS if it["flags"].get(k) == "yes" and k != "large"]
    desc = (f"{pf}{nm}でペットと避難するときの決まりをまとめました。"
            + (f"避難所で受け入れると書いてある動物（{'・'.join(acc)}）、" if acc else "避難所で受け入れる動物、")
            + "大型犬の扱い、ケージ・リード、避難所で飼う場所、ペットを受け入れる避難所の調べ方。")
    faq = faq_for(pf, [it])
    ld = _ld(SITE, url, f"{nm}のペット同行避難と避難所の決まり", desc,
             [("ペットタクシー予約窓口", "/"), ("ペットと避難", f"/{SLUG}/"), (pf, href(pf)), (nm, href_city(it))], faq)
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    pol = f'<p style="margin:0 0 4px">{e(it["policy"])}</p>' if it.get("policy") else ""
    summ = e(" ".join(_answer(it)[1 if it.get("policy") else 0:]))
    others = [x for x in sibs if x is not it]
    sib = ('<ul class="hn-pref">' + "".join(f'<li><a href="{href_city(x)}">{e(x["name"])}</a></li>' for x in others) + "</ul>") if others else ""
    if len(others) > 12: sib = f'<details class="hn-more"><summary>{e(pf)}のほかの市区町村（{len(others)}）</summary>{sib}</details>'
    return ctx["head"](title, desc, url, ld) + CSS + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/{SLUG}/">ペットと避難</a> › <a href="{href(pf)}">{e(pf)}</a> › {e(nm)}</nav>
    <h1><small>避難所で受け入れる動物・大型犬・ケージの決まり</small>{e(nm)}のペット同行避難</h1>
    <p class="lede">うちの子をえらぶと、{e(nm)}の避難所に連れて行けるか・どこで過ごすか・今日やる準備が分かります。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    {HA.block(e, it, pf, large_answer(it), shelter_note=has_sh_place(pf, it))}
    {shelters_html(e, pf, it)}
    <h2 id="detail">{e(nm)}の決まり（上の答えのもと）</h2>
    <div class="answer">{pol}{agrid(e, it)}{arows(e, it)}</div>
    <details class="hn-more"><summary>{e(nm)}が出している決まりの全文と出どころ</summary>{card(e, it, grid=False)}</details>
    <h2 id="faq">よくある質問</h2>
    <dl class="emg-tips">{faq_html}</dl>
    <p class="emg-note">{e(CHECKED)}時点の情報です。避難所の決まりは変わることがあり、災害の状況や避難所ごとにも違います。必ずリンク先でご確認ください。誤りは<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
  </article></div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>{e(pf)}のほかの市区町村</h2><p>{e(pf)}の決まりと、ほかの市区町村の決まりです。</p></div>
    <ul class="other"><li><a href="{href(pf)}">{e(pf)}のペット同行避難（県の決まりと一覧）</a></li></ul>
    {sib}
    <div class="sh"><h2>くわしい記事</h2><p>同行避難と同伴避難のちがい、持ち出し品のリストなど。</p></div>
    {_guides(e)}
    <ul class="other"><li><a href="/{SLUG}/">ペットと避難するとき（全国の一覧）</a></li><li><a href="/jichitai/">ペットの迷子・犬の登録・引取りの窓口</a></li><li><a href="/guide/lost-pet/">ペットが迷子になったら</a></li></ul>
  </div>
</section>
{_taxi(e, pf)}
</main>
""" + ctx["foot_noband"]()

def urls(SITE):
    bp = by_pref()
    ok = [pf for pf in bp if pref_ok(bp[pf])]
    return [f"{SITE}/{SLUG}/"] + [f"{SITE}{href(pf)}" for pf in ok] + [f"{SITE}{href_city(it)}" for pf in ok for it in bp[pf] if has_page(it)]

def write_all(ROOT, ctx):
    try:
        import thin_gate as TG
    except ImportError:
        TG = None
    for _ in range(4):
        _write(ROOT, ctx)
        if not TG: break
        mine = [p for p in TG.all_pages(ROOT) if p.startswith(f"/{SLUG}/") and p != f"/{SLUG}/"]
        n = TG.measure(ROOT, TG.all_pages(ROOT))
        low = [p for p in mine if n.get(p, 0) < TG.MIN_CHARS]
        if not low: break
        rev_p = {PSLUG[pf]: pf for pf in PSLUG}
        rev_c = {(PSLUG[pf], CSLUG[(pf, nm)]): (pf, nm) for (pf, nm) in CSLUG if pf in PSLUG}
        for p in low:
            parts = [x for x in p.split("/") if x]
            if len(parts) == 3 and (parts[1], parts[2]) in rev_c: THIN.add(rev_c[(parts[1], parts[2])])
            elif len(parts) == 2 and parts[1] in rev_p: PREF_THIN.add(rev_p[parts[1]])
    write_finder(ROOT)

def _write(ROOT, ctx):
    bp = by_pref()
    done = [pf for _, ps in ctx["emg_regions"] for pf in ps if pf in bp and pref_ok(bp[pf])]
    import shutil
    for d in os.listdir(os.path.join(ROOT, SLUG)) if os.path.isdir(os.path.join(ROOT, SLUG)) else []:
        if d != "s" and os.path.isdir(os.path.join(ROOT, SLUG, d)): shutil.rmtree(os.path.join(ROOT, SLUG, d))  # 前の作り直しの残り（薄くて外したページ）を消す
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    page = render_top(ctx)
    if "data-bf" in page: page = _bf(page)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(page)
    for pf in done:
        d = os.path.join(ROOT, SLUG, PSLUG[pf]); os.makedirs(d, exist_ok=True)
        page = _bf(render_pref(ctx, pf, bp[pf], done))
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)
        cities = sorted([x for x in bp[pf] if has_page(x)], key=lambda x: MUNI_ORDER.get((pf, x["name"]), 9999))
        for it in cities:
            cd = os.path.join(ROOT, SLUG, PSLUG[pf], CSLUG[(pf, it["name"])]); os.makedirs(cd, exist_ok=True)
            open(os.path.join(cd, "index.html"), "w", encoding="utf-8").write(_bf(render_city(ctx, pf, it, cities, done)))


# ── 具体的な避難所（[B] Nori 2026-11-16「具体的な避難場所の情報ないし」） ──
# 元は国土地理院「指定緊急避難場所・指定避難所データ」。tools/build_hinan_shelters.py が /hinan/s/<団体コード>.json に分ける。
SH_SRC = ('<p class="hn-src">避難所の一覧：<a href="https://www.gsi.go.jp/bousaichiri/hinanbasho.html" target="_blank" rel="noopener">国土地理院「指定緊急避難場所・指定避難所データ」</a>'
          '（2026年11月時点）を加工して作成。開く避難所は災害の種類や状況で変わります。</p>')
MCODE = {(m["pref"], m["name"]): m["code"] for m in MUNI}
SH_CSS = """<style>
.hn-sh{list-style:none;padding:0!important;margin:6px 0 0!important}
.hn-sh li{display:grid;grid-template-columns:1fr auto;gap:2px 10px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line);margin:0}
.hn-sh li b{font-size:.92rem;line-height:1.45}
.hn-sh li span{grid-column:1;font-size:.8rem;color:#5f6368;line-height:1.4}
.hn-sh li em{grid-column:1;font-style:normal;font-size:.78rem;font-weight:700;color:#1e7a45}
.hn-sh li a{grid-column:2;grid-row:1/span 3;font-size:.82rem;font-weight:700;white-space:nowrap;border:1px solid var(--line);border-radius:999px;padding:4px 10px;text-decoration:none;background:#fff}
.hn-sh li i{font-style:normal;font-size:.76rem;color:var(--accent,#e8590c);font-weight:700}
.hn-shw{border:1.5px solid var(--line);border-radius:16px;padding:10px 14px;margin:14px 0;background:#fff}
.hn-shw h2{margin:2px 0 4px!important;font-size:1.1rem}
.hn-shw .hn-near{display:block;width:100%;margin:6px 0 2px;padding:10px;border-radius:12px;border:0;background:var(--ink,#2b2622);color:#fff;font-weight:700;font-size:.92rem}
.hn-ward>summary{cursor:pointer;font-weight:700;font-size:.9rem;padding:7px 0;border-bottom:1px solid var(--line)}
.hn-wsel{width:100%;font-size:1rem;padding:10px;border:1.5px solid var(--line);border-radius:12px;background:#fff;margin:6px 0 0}
.hn-src{font-size:.74rem;color:#5f6368;margin:8px 0 0;line-height:1.5}
.hn-shn{font-size:.82rem;color:#3c4043;margin:0 0 4px}
</style>"""
NEAR_JS = r"""<script>(function(){if(window.hnNearOn)return;window.hnNearOn=1;document.addEventListener('click',function(ev){var b=ev.target.closest&&ev.target.closest('.hn-near');if(!b)return;var w=b.closest('.hn-shw'),o=w.querySelector('.hn-nearout');if(!navigator.geolocation){o.textContent='この端末では位置が使えません。';return}
b.disabled=true;b.textContent='位置をたしかめています…';navigator.geolocation.getCurrentPosition(function(p){var la=p.coords.latitude,ln=p.coords.longitude,a=[];w.querySelectorAll('.hn-sh li[data-ll]').forEach(function(li){var q=li.getAttribute('data-ll').split(','),dy=(q[0]-la)*111,dx=(q[1]-ln)*91;a.push([Math.sqrt(dx*dx+dy*dy),li])});a.sort(function(x,y){return x[0]-y[0]});
var ol=document.createElement('ol');ol.className='hn-sh';a.slice(0,5).forEach(function(x){var c=x[1].cloneNode(true),i=document.createElement('i');i.textContent='ここから'+(x[0]<1?Math.round(x[0]*1000)+'m':x[0].toFixed(1)+'km')+'（直線）';c.hidden=false;c.insertBefore(i,c.children[1]);ol.appendChild(c)});o.innerHTML='<p class="hn-shn"><b>近い避難所</b></p>';o.appendChild(ol);b.textContent='近い順に並べました';try{gtag('event','hinan_near',{})}catch(e){}},function(){b.disabled=false;b.textContent='📍 近い避難所をさがす';o.textContent='位置が使えませんでした。下の一覧からさがしてください。'},{timeout:10000,maximumAge:300000})})})();</script>"""

def _ward(r):
    if r[4]: return r[4]
    m = re.match(r"^([^0-9０-９\-]{1,5}?区)", r[1])
    return m.group(1) if m else ""

def _sh_li(e, r):
    q = f"{r[2]},{r[3]}"
    return (f'<li data-ll="{q}"><b>{e(r[0])}</b><span>{e(r[1])}</span>' + (f'<em>🐾 {e(r[5])}</em>' if r[5] else "")
            + f'<a href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">地図 ↗</a></li>')

def load_shelters(pf, nm):
    c = MCODE.get((pf, nm))
    f = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), SLUG, "s", f"{c}.json")
    return json.load(open(f, encoding="utf-8")) if c and os.path.exists(f) else []

_SITES = None
def site_src(pf, nm):
    """避難所ごとのペットの場所の出どころ（tools/hinan_sites.json）"""
    global _SITES
    if _SITES is None:
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hinan_sites.json")
        _SITES = json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {}
    return _SITES.get(f"{pf}|{nm}")

def has_sh_place(pf, it):
    return any(r[5] for r in load_shelters(pf, it["name"]))

def shelters_html(e, pf, it):
    nm = it["name"]; rs = load_shelters(pf, nm)
    if not rs: return ""
    pets = sum(1 for r in rs if r[5])
    head = (f'<div class="hn-shw" id="shelters"><h2>🏫 {e(nm)}の指定避難所 <small class="hn-n">{len(rs)}か所</small></h2>'
            f'<p class="hn-shn">ペットを連れて行けるかは、上の{e(nm)}の決まりのとおりです。飼う場所は避難所ごとに違うことがあります。'
            + (f'🐾の印は、ペットの受け入れが書いてある避難所（{pets}か所）です。' if pets else "") + '</p>'
            '<button type="button" class="hn-near">📍 近い避難所をさがす</button><div class="hn-nearout" aria-live="polite"></div>')
    wards = {}
    for r in rs: wards.setdefault(_ward(r), []).append(r)
    if len(wards) >= 3 and len(wards.get("", [])) < len(rs) / 4:
        # 区の多い市は、区をえらぶ欄＋その区の一覧（ほかの区はHTMLに残して隠す）
        ws = sorted(wards.items(), key=lambda x: (x[0] == "", x[0]))
        opts = "".join(f'<option value="{i}">{e(w or "そのほか")}（{len(v)}か所）</option>' for i, (w, v) in enumerate(ws))
        body = (f'<select class="hn-wsel" aria-label="区をえらぶ" onchange="var o=this.parentNode.querySelectorAll(\'.hn-wl\');for(var i=0;i<o.length;i++)o[i].hidden=(i!=this.value)">{opts}</select>'
                + "".join(f'<ol class="hn-sh hn-wl"{" hidden" if i else ""}>' + "".join(_sh_li(e, r) for r in v) + "</ol>" for i, (w, v) in enumerate(ws)))
    else:
        top, rest = rs[:8], rs[8:]
        body = '<ol class="hn-sh">' + "".join(_sh_li(e, r) for r in top) + "</ol>"
        if rest: body += f'<details class="hn-ward"><summary>ほかの{len(rest)}か所</summary><ol class="hn-sh">' + "".join(_sh_li(e, r) for r in rest) + "</ol></details>"
    v = site_src(pf, nm) if pets else None
    src2 = (f'<p class="hn-src">🐾ペットの場所：<a href="{e(v["src"])}" target="_blank" rel="noopener">{e(v["title"])}</a>をもとに作成。</p>') if v else ""
    return SH_CSS + head + body + src2 + SH_SRC + "</div>" + NEAR_JS

def _bf(page):
    return page.replace("</head>", V.BF_CSS + "\n</head>", 1).replace("</body>", V.BF_JS + "\n</body>", 1)

# [B] Nori 2026-11-14「地域でフィルターして連絡できるようにしたほうがいいんじゃない？もしくはリンク貼ってそっちに飛ばすとか」：
# 都道府県 → 市区町村をえらぶと、全国1,741の市区町村のどれでも、当サイトのページ（あれば）か、確かめた公式ページ、
# なければその市区町村の公式サイトへ案内する。一覧は /hinan/munis.json（ページの重さに入れない。えらんだときだけ読む）。電話番号は出さない。
def write_finder(ROOT):
    bp = by_pref()
    have = {(it["pref"], it["name"]): it for its in bp.values() for it in its if it["kind"] == "city"}
    pref_page = {pf for pf in bp if pref_ok(bp[pf])}
    nf = set(NONE)
    out = {}
    for m in MUNI:
        pf, nm, top = m["pref"], m["name"], m.get("url") or ""
        it = have.get((pf, nm))
        fc = ("".join(CODE[it["flags"].get(k)] for k, _ in KINDS) + ("1" if it.get("cage_req") else "0")) if it else ""
        if it and has_page(it) and pf in pref_page: row = [nm, "page", href_city(it), top, "", fc]
        elif it and pf in pref_page: row = [nm, "card", href(pf) + "#" + nm, top, "", fc]
        elif it and it.get("links"): row = [nm, "link", it["links"][0][1], top, it["links"][0][0], fc]
        elif it: row = [nm, "link", top, top, it.get("reply") or nm, fc]
        elif (pf, nm) in nf: row = [nm, "none", "", top, "", ""]
        else: row = [nm, "todo", "", top, "", ""]
        row.append(m["code"] if os.path.exists(os.path.join(ROOT, SLUG, "s", m["code"] + ".json")) else "")
        if it:  # 書いてあること（考え方・ケージ・飼う場所・受け入れない動物）を短く。分からない項目は空
            row.append(["", "" if it.get("cage_req") else first(it.get("cage")), first(it.get("place")), no_text(it.get("no")),
                        large_short(it)])
        v = site_src(pf, nm)
        if v:
            if len(row) < 8: row.append([])
            row.append([v["title"], v["src"]])
        out.setdefault(pf, []).append(row)
    open(os.path.join(ROOT, SLUG, "munis.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))

FINDER_CSS = """<style>
.hn-find{background:#fff;border:2px solid var(--accent,#e8590c);border-radius:18px;padding:14px 16px;margin:12px 0 18px}
.hn-find h2{font-size:1.15rem;margin:0 0 10px}
.hn-find .out>a{display:block;text-align:center;background:var(--accent,#e8590c);color:#fff;border-radius:12px;padding:12px;margin-top:6px;text-decoration:none}
.hn-find .row{display:flex;flex-wrap:wrap;gap:8px}
.hn-find select{flex:1 1 140px;min-width:0;font-size:1rem;padding:10px;border:1.5px solid var(--line);border-radius:12px;background:#fff}
.hn-find .out{margin-top:10px;line-height:1.8;font-size:.95rem}
.hn-find .out a{font-weight:700}
</style>"""

def finder(e, prefs, pf=None):
    opts = "".join(f'<option{" selected" if p == pf else ""}>{e(p)}</option>' for p in prefs)
    SH_SRC_JS = SH_SRC.replace("'", "\\'")
    return FINDER_CSS + f"""<div class="hn-find" id="find"><h2>📍 お住まいの市区町村をえらぶ</h2>
<div class="row"><select id="hnP" aria-label="都道府県"><option value="">都道府県をえらぶ</option>{opts}</select>
<select id="hnM" aria-label="市区町村" disabled><option value="">市区町村をえらぶ</option></select></div>
<div class="out" id="hnO" aria-live="polite"></div></div>
<script>(function(){{var P=document.getElementById('hnP'),M=document.getElementById('hnM'),O=document.getElementById('hnO'),D=null;
function esc(s){{return String(s).replace(/[&<>"]/g,function(c){{return{{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]}})}}
function fill(){{M.innerHTML='<option value="">市区町村をえらぶ</option>';O.innerHTML='';var L=D&&D[P.value]||[];L.forEach(function(r,i){{var o=document.createElement('option');o.value=i;o.textContent=r[0];M.appendChild(o)}});M.disabled=!L.length}}
function load(cb){{if(D)return cb();fetch('/{SLUG}/munis.json').then(function(r){{return r.json()}}).then(function(j){{D=j;cb()}}).catch(function(){{O.textContent='読み込めませんでした。時間をおいてお試しください。'}})}}
P.addEventListener('change',function(){{load(fill)}});if(P.value)load(fill);
M.addEventListener('change',function(){{var r=(D[P.value]||[])[M.value];if(!r){{O.innerHTML='';return}}var n=esc(r[0]),top=r[3]?'<a href="'+esc(r[3])+'" target="_blank" rel="noopener">'+n+'の公式サイト ↗</a>':'',h='';
if(r[1]=='page'||r[1]=='card')h='<a href="'+esc(r[2])+'">'+n+'の決まりをくわしく →</a>';
else if(r[1]=='link')h=n+'の決まり：<a href="'+esc(r[2])+'" target="_blank" rel="noopener">'+esc(r[4]||'ペットと避難')+' ↗</a>';
else if(r[1]=='none')h=n+'では、ペットと避難の決まりが見つかりませんでした。'+top+'の防災のページか、お問い合わせ（防災・危機管理の担当）でご確認ください。';
else h=n+'の決まりは、まだまとめていません。'+top+'で「ペット 避難」とさがすか、お問い合わせ（防災・危機管理の担当）でご確認ください。';
if(r[5]){{var K=[['🐕','犬'],['🦮','大型犬'],['🐈','猫'],['🐇','うさぎ・ハムスター'],['🐦','小鳥'],['🦎','爬虫類']],Mm={{y:['○','受け入れる','yes'],n:['×','受け入れない','no'],h:['△','むずかしい場合あり','hard'],c:['△','条件つき','cond']}},g='',t=r[7]||[],w='';
K.forEach(function(k,i){{var m=Mm[r[5].charAt(i)];if(m)g+='<li class="'+m[2]+'"><span class="i">'+k[0]+'</span><b>'+k[1]+'</b><span class="m" data-k="'+m[0]+'">'+m[1]+'</span></li>'}});
g=g?'<ul class="hn-ag">'+g+'</ul>':'';
function rw(i,b,v){{if(v)w+='<li><span class="i">'+i+'</span><span><b>'+b+'</b>'+esc(v)+'</span></li>'}}
rw('🦮','大型犬は？',t[4]);rw('🧺','ケージ',r[5].charAt(6)=='1'?'持っていく（ケージの中で飼う）':t[1]);rw('🏠','飼う場所',t[2]);rw('⚠️','受け入れない動物',t[3]);
h=g+(w?'<ul class="hn-rows">'+w+'</ul>':'')+h}}
O.innerHTML=h;if(r[6]){{var sw=document.createElement('div');sw.className='hn-shw';sw.innerHTML='<p class="hn-shn">避難所の一覧を読みこんでいます…</p>';O.appendChild(sw);
fetch('/{SLUG}/s/'+r[6]+'.json').then(function(x){{return x.json()}}).then(function(L){{function li(s){{var q=s[2]+','+s[3];return '<li data-ll="'+q+'"><b>'+esc(s[0])+'</b><span>'+esc(s[1])+'</span>'+(s[5]?'<em>🐾 '+esc(s[5])+'</em>':'')+'<a href="https://www.google.com/maps/search/?api=1&amp;query='+q+'" target="_blank" rel="noopener">地図 ↗</a></li>'}}
var t='<h2>🏫 '+n+'の指定避難所 <small class="hn-n">'+L.length+'か所</small></h2><button type="button" class="hn-near">📍 近い避難所をさがす</button><div class="hn-nearout" aria-live="polite"></div><ol class="hn-sh">'+L.slice(0,5).map(li).join('')+'</ol>';
if(L.length>5)t+=(r[1]=='page'?'<p class="hn-shn"><a href="'+esc(r[2])+'#shelters">'+n+'の避難所をすべて見る（'+L.length+'か所）→</a></p><ol class="hn-sh" hidden>'+L.slice(5).map(li).join('')+'</ol>':'<details class="hn-ward"><summary>ほかの'+(L.length-5)+'か所</summary><ol class="hn-sh">'+L.slice(5).map(li).join('')+'</ol></details>');
sw.innerHTML=t+(r[8]?'<p class="hn-src">🐾ペットの場所：<a href="'+esc(r[8][1])+'" target="_blank" rel="noopener">'+esc(r[8][0])+'</a>をもとに作成。</p>':'')+'{SH_SRC_JS}'}}).catch(function(){{sw.innerHTML='<p class="hn-shn">避難所の一覧を読みこめませんでした。</p>'}})}}
try{{gtag('event','hinan_find',{{pref:P.value,status:r[1]}})}}catch(e){{}}}})}})();</script>""" + SH_CSS + NEAR_JS
