# [A][B] 迷子・犬の登録・飼えなくなったとき を、それぞれの人の不安から答えるページに分ける（Nori 2026-11-17
# 「これだけ？迷子になったら、飼い主はどうしたいと思ってると思う？迷子と登録と引き取りって全然違うテーマ」
# 「自治体の情報を転記するだけとかやめて」「各かてごりで民間のプレイヤーもいるよね？」）。
#   /jichitai/maigo/     迷子：市区町村と犬か猫かを入れると、その町で今日やることが順番に出る（連絡先・民間の捜索・チラシ作り・1/3/7日目）
#   /jichitai/touroku/   犬の登録：いつまでに・どこで・いくら・何を持って（迎えた日から期限を出す。主な市の手数料とマイクロチップの扱いをくらべる）
#   /jichitai/tebanasu/  飼えなくなったとき：手放す前の道（預ける・老犬ホーム・新しい家族）を先に、センターは最後の相談先
# 自治体の情報は根拠として使い、ページの中心は「次に何をするか」と、くらべて決めるための材料にする。
# 動き：/jichitai/jc.js（元は tools/jichitai.js）、データ：/jichitai/data.json（このファイルが作る）。電話番号は載せない。
import json, os, re
from facility_review_links import link as review_link

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT0 = os.path.dirname(HERE)
CHECKED = "2026年11月17日"

def _j(name, default=None):
    p = os.path.join(HERE, name)
    if not os.path.exists(p): return default
    return json.load(open(p, encoding="utf-8"))

J = _j("jichitai.json")
MUNIS = _j("municipalities.json")
PRIV = _j("maigo_private.json", {}) or {}

# 民間の迷子捜索（ペット探偵）：tools/maigo_private.json（各社の公式サイトの情報、出どころ src つき）を、ページで使う形にそろえる
PREF47 = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
          "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
          "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
          "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"]
REGION = {"関東": PREF47[7:14], "関西": PREF47[24:30], "近畿": PREF47[24:30], "東海": ["静岡県", "愛知県", "岐阜県", "三重県"]}
def _areas(d):
    t = (d.get("area") or "")
    if "全国" in t: return ["全国"]
    if t in ("", "記載なし"): t = d.get("base") or ""
    out = [p for p in PREF47 if p in t or p[:-1] in t and len(p) > 2]
    for k, v in REGION.items():
        if k in t: out += v
    return sorted(set(out), key=PREF47.index)
def _yen(p):
    y = p.get("yen")
    if not y: return "無料"
    tax = p.get("tax") or ""
    return f"{y:,}円" + ("〜" if p.get("from") else "") + ("" if tax == "税込" else "（税別）" if tax == "税別" else "（税の記載なし）")
def detectives():
    out = []
    for d in PRIV.get("detectives", []):
        plans = [p for p in d.get("plans", []) if p.get("yen") is not None][:4]
        txt = "／".join(f'{p.get("name", "")} {_yen(p)}' for p in plans)
        ex = [p.get("extra") for p in d.get("plans", []) if p.get("extra")] + [x.get("text") for x in d.get("extra_fees", []) if isinstance(x, dict) and x.get("text")]
        ex = [x for x in ex if len(x) <= 50 and "記載なし" not in x and "預かる" not in x]
        if ex: txt += "。" + "。".join(dict.fromkeys(ex))
        ar = _areas(d)
        out.append({"name": d["name"], "url": d.get("price_url") or d.get("url"), "areas": ar, "plan": txt,
                    "review_html": review_link("detective", d, "jc-src", scope="company"), "animals": "" if "明記なし" in d.get("animals", "") else d.get("animals", ""), "near": d.get("near") or [], "pref_url": d.get("pref_url") or "", "near_note": d.get("near_note") or "", "area_text": "全国" if ar == ["全国"] else (d.get("area") if d.get("area") not in (None, "", "記載なし") else d.get("base", ""))})
    return out

# 警察の遺失届（警察庁「落とし物の届出・検索」2026-11-17 時点：46道府県は警察庁の共通のオンラインの受付、東京都は警視庁の受付）
NPA_ONLINE = "https://lostproperty.pcf.npa.go.jp/ZDSERVFP/SZDSA0101"
NPA_PAGE = "https://www.npa.go.jp/bureau/soumu/ishitsubutsu/ishitsu-todokedekensaku.html"
POLICE = {"東京都": "https://www.keishicho-gto.metro.tokyo.lg.jp/keishicho-u/"}
ENV_LINK = "https://www.env.go.jp/nature/dobutsu/aigo/shuyo/link.html"
CHIP = "https://reg.mc.env.go.jp/"

# 保護された子を待ってもらえる日数と、迎えるときの費用（自治体の公式ページにある例。tools/guides_jichitai.py の出どころと同じ）
WAIT = [("東京都", "収容期限は7日間。保護した子の情報はページに出していないので、電話で問い合わせる", "https://www.hokeniryo.metro.tokyo.lg.jp/shisetsu/jigyosyo/douso/sissou/sissou"),
        ("新潟県（下越）", "収容は通常1〜2週間ほど。その間に飼い主が現れないと、譲渡か致死処分", "https://www.pref.niigata.lg.jp/sec/shibata_kenkou/1235937705722.html"),
        ("栃木県", "迷子の動物の情報のページへの掲載は14日間", "https://www.douai.pref.tochigi.lg.jp/work/custody-lostanimal/"),
        ("群馬県", "県の動物愛護センターは猫を収容していない（猫は自分でさがすことがより大切）", "https://www.pref.gunma.jp/page/660168.html"),
        ("愛知県", "返還の手数料2,600円と、収容中の飼養管理費1日400円", "https://www.pref.aichi.jp/soshiki/doukan-c/inugainakunatta.html"),
        ("滋賀県", "返還の手数料1頭3,530円と、飼養管理費1日350円", "https://www.pref.shiga.lg.jp/doubutsuhogo/14448.html")]

# 犬の登録：主な市の手数料と、マイクロチップの扱い（各市の公式ページ、2026-11-17 時点）
FEES = [("横浜市", "3,000円", "550円", "—", "https://www.city.yokohama.lg.jp/naka/kurashi/sumai_kurashi/pet_dobutsu/first.html"),
        ("名古屋市", "3,000円", "550円", "区の保健センターのほか、市が頼んでいる動物病院・電子申請でも登録できる", "https://www.city.nagoya.jp/kurashi/pet/1015199/1034043/1015210.html"),
        ("福岡市", "3,000円", "550円", "2023年3月1日からのマイクロチップの登録で鑑札の代わりになり、窓口の登録はいらない", "https://www.city.fukuoka.lg.jp/hofuku/dobutsukanri/life/owner_dog.html"),
        ("千葉市", "3,000円", "550円", "マイクロチップの特例に参加していないので、チップが入っていても窓口で登録", "https://www.city.chiba.jp/faq/hokenfukushi/iryoeisei/seikatsueisei/dobutsuhogo/509.html"),
        ("杉並区", "3,000円", "550円", "マイクロチップの登録が鑑札の代わりになり、区の窓口での申請はいらない", "https://www.city.suginami.tokyo.jp/guide/kenko/doubutsu/1026924.html")]


def data(ROOT, pref_slug):
    """市区町村 → 窓口・警察・役所・近くの情報のページ（/jichitai/data.json）。"""
    C = {}
    for p in J["prefs"]:
        C[p["pref"]] = [p["name"], p["url"], (p["links"][0]["u"] if p["links"] else ""), p["pref"] + "のどの市町村も"]
    city_of = {}
    for c in J["cities"]:
        k = c["pref"] + c["city"]
        C[k] = [c["name"], c["url"], (c["links"][0]["u"] if c["links"] else ""), c["city"]]
        city_of[k] = k
    def has(*p): return os.path.isdir(os.path.join(ROOT, *p))
    P = {}
    for pf, sl in pref_slug.items():
        P[pf] = {"s": sl, "pol": POLICE.get(pf, NPA_ONLINE),
                 "h": f"/hospital/{sl}/" if has("hospital", sl) else "/hospital/#pref=" + pf,
                 "n": f"/hospital/night/{sl}/" if has("hospital", "night", sl) else "/hospital/night/",
                 "r": f"/rojin-home/{sl}/" if has("rojin-home", sl) else "",
                 "o": f"/pet-hotel/{sl}/" if has("pet-hotel", sl) else "",
                 "t": f"/pet-sitter/{sl}/" if has("pet-sitter", sl) else "",
                 "j": f"/joto/{sl}/" if has("joto", sl) else "",
                 "sg": f"/sougi/{sl}/" if has("sougi", sl) else "/sougi/"}
    M = []
    for m in MUNIS:
        pf, nm = m["pref"], m["name"]
        k = pf + nm
        if k not in C:  # 政令市の区など：市の窓口に寄せる
            for c in J["cities"]:
                if c["pref"] == pf and nm.startswith(c["city"]): k = pf + c["city"]; break
            else: k = pf
        sl = pref_slug.get(pf, "")
        hv = f"/hospital/{sl}/{m['slug']}/" if sl and has("hospital", sl, m["slug"]) else ""
        M.append([pf, nm, m.get("kana", ""), m.get("url", ""), k, hv])
    D = []
    for d in detectives():
        x = {"areas": d["areas"], "near": d["near"]}
        if d["pref_url"]: x["u"] = {pf: d["pref_url"].format(slug=sl) for pf, sl in pref_slug.items()}  # 県ごとのページがある会社
        D.append(x)
    return {"c": C, "p": P, "m": M, "d": D}


# ---------- 見た目（共通のカード .cs は cardskin.py。ここは手順の線・チェック・チラシ） ----------
CSS = ("<style>"
 ".jc-actions{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:4px 0 8px}.jc-actions a{display:flex;flex-direction:column;justify-content:center;min-height:64px;padding:8px 5px;text-align:center;border:1px solid #d9c9bb;border-radius:12px;color:#2b2622;background:#fff;text-decoration:none;line-height:1.3;overflow-wrap:anywhere}.jc-actions a.jc-primary{background:#a9390b;color:#fff;border-color:#a9390b}.jc-actions b{font-size:clamp(.8rem,3.4vw,1rem)}.jc-actions small{font-size:.72rem;margin-top:4px}.jc-short{display:flex;flex-wrap:wrap;gap:0 14px;align-items:center;margin-bottom:10px}.jc-short a{display:inline-flex;align-items:center;min-height:44px;font-size:.9rem}.jc-panel,#pro,#found,#jcFly{scroll-margin-top:90px}.jc-panel{margin-bottom:16px}.jc-panel h2{font-size:1.15rem;margin:0 0 7px}.jc-intro{font-size:.88rem;margin:0 0 7px;color:#4a3d34}.jc-local h3{font-size:.97rem;margin:10px 0 4px}.jc-local ul{margin:4px 0 0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.jc-local a{display:flex;align-items:center;min-height:44px;line-height:1.35;padding:6px 8px;border:1px solid #e5d5c8;border-radius:8px;font-size:.85rem;overflow-wrap:anywhere}.jc-local small{display:block;margin-top:6px}.jc-an-label{font-size:.85rem;margin:10px 0 0}.jc-an-label+.jc-an{margin-top:4px}@media(max-width:639px){.jc-maigo-hero{padding-top:10px;padding-bottom:10px}.jc-maigo-hero .crumb{margin-top:0;margin-bottom:4px}.jc-maigo-hero h1{margin:3px 0 6px}.jc-panel{margin-bottom:12px}.jc-short{margin-bottom:4px}}@media(min-width:640px){.jc-actions a{min-height:72px;padding:10px}.jc-actions small{font-size:.85rem}.jc-local ul{grid-template-columns:repeat(3,minmax(0,1fr))}}"
 ".jc-3{list-style:none;margin:4px 0 10px;padding:12px 14px;background:#fff;border:1px solid #efe0d3;border-radius:16px;display:grid;gap:8px}"
 ".jc-3 li{display:flex;gap:10px;align-items:center;font-size:1rem;line-height:1.45;font-weight:700;color:#2b2622}"
 ".jc-3 i{flex:0 0 30px;width:30px;height:30px;border-radius:50%;background:#c2410c;color:#fff;font-style:normal;font-weight:800;display:flex;align-items:center;justify-content:center}"
 ".jc-3 small{display:block;font-weight:400;font-size:.82rem;color:#5a4a3f}"
 ".jc-q1{background:#fff;border:2px solid #c2410c;border-radius:16px;padding:12px 14px;margin:6px 0 12px}"
 ".jc-q1 label{display:block;font-weight:800;margin:0 0 6px}.jc-q1 input[type=text]{width:100%;box-sizing:border-box;padding:12px;border:1px solid #e5d5c8;border-radius:10px;font-size:1rem}"
 ".jc-sg{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 0}.jc-sg:empty{display:none}.jc-sg button{padding:8px 12px;border:1px solid #c2410c;border-radius:999px;background:#fff;color:#c2410c;font-weight:700;font-size:.9rem}"
 ".jc-an{display:flex;gap:8px;margin:10px 0 0}.jc-an button{flex:1;padding:10px;border:1px solid #d9c9bb;border-radius:12px;background:#fff;font-weight:800;font-size:.95rem;color:#2b2622}.jc-an button[aria-pressed=true]{background:#2b2622;color:#fff;border-color:#2b2622}"
 ".jc-hd{font-size:.95rem;margin:10px 0 0;color:#2b2622}.jc-hd b{color:#c2410c}"
 ".jc-tl{list-style:none;margin:8px 0 0;padding:0;border-left:3px solid #f3d3bd;margin-left:9px}"
 ".jc-tl>li{position:relative;padding:0 0 14px 18px}.jc-tl>li::before{content:'';position:absolute;left:-9px;top:3px;width:15px;height:15px;border-radius:50%;background:#c2410c;box-shadow:0 0 0 3px #fff}"
 ".jc-when{display:inline-block;font-size:.78rem;font-weight:800;color:#fff;background:#c2410c;border-radius:999px;padding:2px 10px;margin:0 0 4px}"
 ".jc-tl h3{font-size:1.05rem;margin:2px 0 6px;line-height:1.45}"
 ".jc-ck{list-style:none;margin:0;padding:0;display:grid;gap:8px}"
 ".jc-ck>li{background:#fff;border:1px solid #efe0d3;border-radius:14px;padding:10px 12px}"
 ".jc-ck label{display:flex;gap:10px;align-items:flex-start;font-weight:800;line-height:1.45;cursor:pointer}.jc-ck input{width:20px;height:20px;flex:0 0 20px;margin:1px 0 0;accent-color:#c2410c}"
 ".jc-ck li.done{opacity:.6}.jc-ck p{margin:4px 0 0 30px;font-size:.88rem;line-height:1.65;color:#4a3d34}"
 ".jc-ck .jc-go{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 0 30px}.jc-go a{display:inline-flex;align-items:center;padding:8px 12px;border-radius:10px;background:#2b2622;color:#fff!important;font-weight:800;font-size:.86rem;text-decoration:none}.jc-go a.l{background:#fff;color:#2b2622!important;border:1px solid #d9c9bb}"
 "[data-a]{display:none}.jc-dog [data-a=dog],.jc-cat [data-a=cat]{display:block}li[data-a]{display:none}.jc-dog li[data-a=dog],.jc-cat li[data-a=cat]{display:list-item}"
 ".jc-cmp+.jc-src,.tbl+.jc-src{margin-bottom:22px}.tbl{margin-bottom:18px}.jc-cmp{width:100%;border-collapse:collapse;font-size:.88rem}.jc-cmp th,.jc-cmp td{border-bottom:1px solid #f1e3d6;padding:8px 6px;text-align:left;vertical-align:top;line-height:1.55}"
 ".jc-cmp th{font-weight:700;white-space:nowrap}.jc-src{font-size:.78rem;color:#6b5a4e}.jc-src a{color:#6b5a4e}"
 ".jc-vs{display:grid;grid-template-columns:1fr 1fr;gap:8px}.jc-vs>div{background:#fff7ed;border-radius:14px;padding:10px 12px}.jc-vs h4{margin:0 0 6px;font-size:1rem}.jc-vs ul{margin:0;padding-left:1.1em;font-size:.86rem;line-height:1.6}"
 ".jc-opt{display:grid;gap:8px}.jc-opt>div{background:#fff;border:1px solid #efe0d3;border-radius:14px;padding:12px}.jc-opt h3{margin:0 0 4px;font-size:1rem}.jc-opt p{margin:0;font-size:.88rem;line-height:1.65}.jc-opt .jc-go{margin:8px 0 0}"
 ".jc-due{background:#fff7ed;border-radius:14px;padding:12px;margin:10px 0 0;font-size:.95rem;line-height:1.7}.jc-due:empty{display:none}.jc-due b{color:#c2410c;font-size:1.05rem}"
 ".jc-fly{background:#fff;border:1px solid #efe0d3;border-radius:14px;padding:12px;margin:8px 0 0}.jc-fly>summary{font-weight:800;cursor:pointer;color:#c2410c}"
 ".jc-ff{display:grid;gap:8px;margin:10px 0 0}.jc-ff label{font-size:.85rem;font-weight:700;display:grid;gap:4px}.jc-ff input,.jc-ff textarea{padding:10px;border:1px solid #e5d5c8;border-radius:10px;font-size:1rem;font-family:inherit}"
 ".jc-ff button{padding:12px;border:0;border-radius:12px;background:#c2410c;color:#fff;font-weight:800;font-size:1rem}"
 "#jcPrint{display:none}"
 "@media print{body>*:not(#jcPrint){display:none!important}#jcPrint{display:block!important;font-family:sans-serif;color:#000}"
 "#jcPrint h1{font-size:44pt;text-align:center;margin:0 0 6mm;letter-spacing:.1em}#jcPrint .ph{display:flex;gap:4mm;justify-content:center}#jcPrint .ph img{max-width:88mm;max-height:80mm;object-fit:cover}"
 "#jcPrint .nm{font-size:26pt;text-align:center;margin:5mm 0}#jcPrint table{width:100%;font-size:15pt;border-collapse:collapse}#jcPrint th{width:34mm;text-align:left;vertical-align:top;padding:2mm}#jcPrint td{padding:2mm;border-bottom:1px solid #999}"
 "#jcPrint .ask{font-size:15pt;margin:5mm 0;border:2px solid #000;padding:3mm}#jcPrint .ct{font-size:20pt;text-align:center;font-weight:bold}@page{size:A4;margin:12mm}}"
 "</style>")


def _crumb(e, here):
    return (f'<nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットのくらし窓口</a> › <a href="/jichitai/">迷子・登録・飼えなくなったとき</a> › {e(here)}</nav>')

def _ld(SITE, url, name, faq):
    return '<script type="application/ld+json">\n' + json.dumps([
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ペットのくらし窓口", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "迷子・登録・飼えなくなったとき", "item": SITE + "/jichitai/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": url}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
        ensure_ascii=False, indent=1) + "\n</script>"

def _faq(e, faq):
    return "<dl>" + "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq) + "</dl>"

def _ask(kind, label, ph, animal=False):
    an = ('<p class="jc-an-label" aria-hidden="true">さがしているのは？</p><div class="jc-an" role="group" aria-label="どの子？"><button type="button" data-an="dog" aria-pressed="true">犬</button>'
          '<button type="button" data-an="cat" aria-pressed="false">猫</button></div>') if animal else ""
    local = '<div id="jcLocal" class="jc-local" aria-live="polite" hidden></div>' if kind == "maigo" else ""
    return (f'<div class="jc-q1" data-jc="{kind}"><label for="jcQ">{label}</label>'
            f'<input id="jcQ" type="text" placeholder="{ph}" autocomplete="address-level2" enterkeyhint="search">'
            f'<div class="jc-sg" id="jcS" aria-live="polite"></div>{an}<p class="jc-hd" id="jcH" hidden></p>{local}</div>')

def _three(head, steps):
    """最初の画面で「何をすればいいか」が3行で分かる箱（Nori 2026-11-23「迷子登録のページがわかりにくい」）。"""
    li = "".join(f'<li><i>{n}</i><span>{t}<small>{s}</small></span></li>' for n, (t, s) in enumerate(steps, 1))
    return f'<ol class="jc-3" aria-label="{head}">{li}</ol>'

def _li(slot, title, body, go="", a=""):
    aa = f' data-a="{a}"' if a else ""
    return (f'<li data-ck="{slot}"{aa}><label><input type="checkbox">{title}</label><p data-slot="{slot}-t">{body}</p>'
            f'<div class="jc-go" data-slot="{slot}">{go}</div></li>')


# ============ 迷子 ============
MAIGO_FAQ = [
 ("迷子になった犬・猫は、どこに連絡すればいいですか？", "いなくなった場所の動物愛護センター・保健所（住んでいる所と違えば両方）、警察（遺失届。46道府県は警察庁の共通の受付からオンラインで、東京都は警視庁の受付から出せます）、市区町村、近くの動物病院です。このページで市区町村を入れると、その町の窓口が順番に出ます。"),
 ("保護された子は、何日待ってもらえますか？", "自治体ごとに違います。東京都は収容期限を7日間としています。日数がすぎると譲渡などに回ることがあるので、届け出はその日のうちに出し、問い合わせは7日以上あけないでください。"),
 ("ペット探偵に頼むと、いくらかかりますか？", "公式サイトに料金を出している会社では、1日8時間で1万円台後半から6万円台、3日間のまとめで9万円台から17万円台と、会社とやり方で大きく違います。見つかったときだけの成功報酬がある会社もあります。交通費・チラシ代・延長の料金が別のこともあるので、見積もりで総額を確かめてください。アニコム損保・ソニー損保のペット保険の契約者は、3日間の捜索と出張料が無料です。"),
 ("猫が外に出てしまいました。遠くまで行っていますか？", "室内飼いの猫は、家のまわりの狭くて暗い場所にじっと隠れていることが多いと、環境省は案内しています。まず家の中、次に物置・室外機の下・縁の下など、家の近くから順にさがしてください。"),
 ("迷子のチラシには何を書けばいいですか？", "全身と顔の写真、いなくなった日時と場所（丁目まで）、種類・毛色・大きさ・性別・年齢、首輪や目立つ特徴、見かけたときのお願い、連絡先です。このページのチラシ作りに入れると、そのまま印刷できます。入れた内容と写真はどこにも送られません。"),
 ("マイクロチップが入っていれば、連絡は来ますか？", "センター・保健所・警察が番号を読み取り、登録の連絡先に連絡します。引っ越しや電話番号の変更で登録が古いと届かないので、迷子に気づいたら登録の連絡先がいまの番号かを確かめてください。住所・連絡先の変更は無料です。"),
]

def maigo(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/jichitai/maigo/"
    title = "ペットが迷子になったら：今日やること｜市区町村ごとの届け出先・さがし方・チラシ・ペット探偵の料金｜ペットのくらし窓口"
    desc = "犬や猫が迷子になったら、いなくなった市区町村を入れるだけで、その町の動物愛護センター・保健所、警察のオンラインの遺失届、市役所、近くの動物病院と、今日・2日目・3日目・7日目にやることが順番に出ます。犬と猫のさがし方のちがい、印刷できる迷子チラシ、ペット探偵の料金のくらべも。"
    dets = detectives()
    wait = "".join(f'<tr><th>{e(a)}</th><td>{e(b)} <a class="jc-src" href="{e(u)}" target="_blank" rel="noopener">公式ページ ↗</a></td></tr>' for a, b, u in WAIT)
    det_rows = "".join(
        f'<tr><th><a href="{e(d.get("price_url") or d["url"])}" target="_blank" rel="noopener">{e(d["name"])}</a>{("<br>" + d["review_html"]) if d["review_html"] else ""}</th>'
        f'<td>{e(d["plan"])}' + (f'<br><small>{e(d["animals"])}</small>' if d["animals"] else "") + '</td>'
        f'<td>{e(d["area_text"])}' + (f'<br><small>{e(d["near_note"])}</small>' if d["near_note"] else "") + '</td></tr>' for d in dets)
    det_tbl = (f'<div class="tbl"><table class="jc-cmp"><thead><tr><th>会社</th><th>料金と受ける動物</th><th>来てくれる地域</th></tr></thead><tbody>{det_rows}</tbody></table></div>'
               f'<p class="jc-src">金額は税込（税別・税の記載がない会社は印つき）。各社の公式サイトの掲載情報をもとに、最低料金は「〜」で表示しています。順番に意味はありません。発見率など会社の発表の数字は、くらべ方がそろっていないので載せていません。</p>') if dets else ""
    ins = [i for i in PRIV.get("insurance", []) if not i.get("doubt")]
    ins_html = "".join(f'<li><a href="{e(i["src"])}" target="_blank" rel="noopener">{e(i["name"])}</a>：{e(i.get("who", ""))}は、{e(i.get("free", ""))}が無料（{e(i.get("paid", ""))}）</li>' for i in ins)
    boards = PRIV.get("boards", [])
    boards_go = "".join(f'<a class="l" href="{e(b["url"])}" target="_blank" rel="noopener">{e(re.sub(r"（.*?）", "", b["name"]))} ↗</a>' for b in boards)
    body = f"""
<main>
<section class="area-hero jc-maigo-hero">
  <div class="wrap">
    {_crumb(e, "迷子になったら")}
    <h1>ペットが迷子になったら</h1>
  </div>
</section>
<section style="padding-top:4px">
  <div class="wrap">
    <nav class="jc-actions" aria-label="迷子のときにできること">
      <a class="jc-primary" href="#first"><b>まず何をするか</b><small>今日やることを確認</small></a>
      <a href="#report"><b>地域の届け先</b><small>市区町村から調べる</small></a>
      <a href="#pro"><b>ペット探偵</b><small>民間の捜索・料金を比較</small></a>
    </nav>
    <div class="jc-short"><a href="#jcFly">チラシを作る</a><a href="#found">迷子の子を保護した方へ</a></div>
    <div class="jc-panel" id="first" tabindex="-1">
      <h2>まず、この3つ</h2>
    {_three("まず、この3つ", [("家のまわりを、近い所からさがす", "猫は家のすぐ近くに隠れていることが多い"), ("センター・警察・市役所に届ける", "市区町村を入れると窓口が出ます"), ("近所や動物病院にチラシを配る", "このページで作って印刷できます")])}
    </div>
    <div class="jc-panel" id="report" tabindex="-1">
      <h2>地域の届け先を調べる</h2>
      <p class="jc-intro">いなくなった市区町村を選んでください。</p>
    {_ask("maigo", "いなくなった場所の市区町村", "例：佐倉市・世田谷区", True)}
    </div>
    <h2>捜索と届け出のチェックリスト</h2>
    <div id="jcR" class="jc-dog">
    <ol class="jc-tl">
      <li><span class="jc-when">いなくなってすぐ</span><h3>家のまわりから、順番にさがす</h3>
        <ul class="jc-ck">
          <li data-ck="near" data-a="dog"><label><input type="checkbox">いなくなった場所を中心に、円をえがくように広げる</label><p>犬は、においをたどって散歩道やいつもの公園に向かうことがあります。大型犬は1日に何十kmも動くことがあるので、車や自転車の人と手分けを。見つけても追いかけず、しゃがんで名前を呼び、おやつの袋の音で待ちます。</p></li>
          <li data-ck="near" data-a="cat"><label><input type="checkbox">まず家の中、次に家のまわりの狭くて暗い場所</label><p>室内飼いの猫は、こわくて動けず、家のすぐ近くでじっとしていることが多いです。押し入れ・家具のすき間・洗濯機の裏、外なら物置・エアコンの室外機の下・植え込み・縁の下・車の下。静かになる夜や早朝に、懐中電灯で目の光をさがし、小さな声で呼びます。</p></li>
          <li data-ck="photo"><label><input type="checkbox">写真を2〜3枚えらび、家族で手分けする</label><p>全身・顔・模様が分かる写真を。届け出とチラシに使います。だれか1人は家に残ります（自分で帰ってくることがあります）。</p></li>
        </ul></li>
      <li><span class="jc-when">今日のうちに</span><h3>5か所に届け出る</h3>
        <p class="jc-src">見つけた人がどこに届けるかは分かりません。センター・警察・市役所の全部に出しておくのが、いちばんの近道です。</p>
        <ul class="jc-ck">
          {_li("center", "動物愛護センター・保健所に迷子の届け出", "いま保護されていないかも、その場で聞けます。住んでいる所といなくなった所が違う市なら、両方に。", '<a href="#jcQ">市区町村を入れると窓口が出ます</a>')}
          {_li("police", "警察に遺失届を出す", "犬・猫は、法律では「落とし物」として警察に届けられることがあります。46道府県は警察庁の共通の受付から、東京都は警視庁の受付から、オンラインで出せます。", f'<a href="{NPA_ONLINE}" target="_blank" rel="noopener">遺失届をオンラインで出す ↗</a><a class="l" href="{POLICE["東京都"]}" target="_blank" rel="noopener">東京都はこちら ↗</a>')}
          {_li("city", "市区町村に知らせ、清掃の担当にも確かめる", "道路で亡くなった犬・猫は、市区町村の清掃の担当が引き取っています。つらい確認ですが、首輪の色などを伝えておくと、もしものときに連絡をもらえることがあります。", "")}
          {_li("vet", "近くの動物病院に知らせる", "けがをした子が運ばれたり、見つけた人がまず動物病院に連れていったりします。チラシを貼らせてもらえることも。", '<a href="/hospital/">近くの動物病院をさがす</a>')}
          {_li("chip", "マイクロチップの登録の連絡先を確かめる", "保護されると、センターや警察がチップの番号から登録の連絡先に連絡します。引っ越しや電話番号の変更をしていないかを確かめ、古ければ変えます（住所・連絡先の変更は無料）。", f'<a href="{CHIP}" target="_blank" rel="noopener">マイクロチップの登録を確かめる ↗</a>')}
        </ul></li>
      <li><span class="jc-when">今日のうちに</span><h3>迷子チラシを作って、近所に配る</h3>
        <ul class="jc-ck"><li data-ck="flyer"><label><input type="checkbox">チラシを作って、近所と動物病院・お店に</label>
          <p data-a="cat">猫は家を中心にした近い範囲に、たくさん。物置や車庫の中を見てもらうお願いも書きます。</p><p data-a="dog">犬は散歩道・駅・公園まで広めに。毎日同じ道を通る人（配達・通学の見守り）にも声をかけます。</p>
          <details class="jc-fly" id="jcFly"><summary>迷子チラシをここで作る（A4で印刷）</summary>
          <div class="jc-ff">
            <label>写真（2枚まで。どこにも送られません）<input type="file" accept="image/*" multiple id="ffPh"></label>
            <label>名前<input id="ffNm" placeholder="例：モモ"></label>
            <label>種類・毛色・模様<input id="ffKd" placeholder="例：柴犬・赤毛／茶トラの猫"></label>
            <label>大きさ・性別・年齢<input id="ffSz" placeholder="例：8kg・メス（避妊済み）・5歳"></label>
            <label>首輪・目立つ特徴<input id="ffFt" placeholder="例：赤い首輪、しっぽが短い"></label>
            <label>いなくなった日時と場所（丁目まで）<input id="ffWh" placeholder="例：11月17日の夜、本町2丁目の公園のあたり"></label>
            <label>見かけた人へのお願い<textarea id="ffAk" rows="2">こわがりです。追いかけずに、見かけた場所と時間を教えてください。</textarea></label>
            <label>連絡先（自宅の住所は書かない）<input id="ffCt" placeholder="迷子のために作ったメールなど"></label>
            <button type="button" id="ffGo">印刷する</button>
          </div></details></li></ul></li>
      <li><span class="jc-when">2日目から毎日</span><h3>保護された子の情報を毎日見て、少しでも似ていたら問い合わせる</h3>
        <ul class="jc-ck">
          {_li("hogo", "センター・保健所の保護情報を見る", "写真の毛色や年齢は見た目からの目安です。少しでも似ていたら、問い合わせてください。となりの市や県の情報も。", f'<a href="{ENV_LINK}" target="_blank" rel="noopener">全国の自治体の保護情報 ↗</a>')}
          {_li("lost", "警察の落とし物の情報も見る", "遺失届と同じ受付で、届けられた落とし物を検索できます。", f'<a href="{NPA_PAGE}" target="_blank" rel="noopener">落とし物をさがす ↗</a>')}
          <li data-ck="net"><label><input type="checkbox">迷子の掲示板・地域のSNSに、チラシと同じ内容を出す</label><p>無料で迷子・保護・目撃の情報を出し合える掲示板があります。自宅の住所や個人の電話番号は書かないほうが安心です。保護された子の情報を伝えるときは、画像を転載せず、そのページのURLを伝えます。</p><div class="jc-go">{boards_go}</div></li>
        </ul></li>
      <li><span class="jc-when">3日目</span><h3>見つからなければ、プロの捜索も考える</h3>
        <ul class="jc-ck">{_li("pro", "ペット探偵（迷子捜索の会社）に相談する", "捕獲器やカメラでの見張り、チラシの配り方など、家族だけでは難しいことを頼めます。料金は1日8時間で1万円台後半から6万円台、3日間のまとめで9万円台から17万円台と大きく違い、見つかったときだけの成功報酬（5万円・10万円）がある会社もあるので、交通費・チラシ代・延長をふくめた総額で見くらべます。", '<a class="l" href="#pro">料金をくらべる</a>')}
          <li data-ck="ins"><label><input type="checkbox">ペット保険の契約を見直す</label><p>アニコム損保・ソニー損保のペット保険の契約者は、3日間の捜索と出張料が無料です（4日目からは自己負担）。ほかの保険も、証券やマイページで確かめてください。</p></li></ul></li>
      <li><span class="jc-when">7日目</span><h3>問い合わせを続け、さがす範囲を広げる</h3>
        <ul class="jc-ck"><li data-ck="wide"><label><input type="checkbox">となりの市・県の窓口と警察にも届け出る</label><p>東京都は収容期限を7日間としています。問い合わせは7日以上あけず、届け出の内容が古くなっていないかも確かめます。チラシは雨でにじんだら貼りなおします。</p></li></ul></li>
      <li><span class="jc-when">見つかったら</span><h3>迎えに行き、出した届け出を取り下げる</h3>
        <ul class="jc-ck"><li data-ck="back"><label><input type="checkbox">迎えに行く・届け出を取り下げる・動物病院でみてもらう</label><p>写真や鑑札・マイクロチップの番号など飼い主と分かるもの、本人確認の書類、キャリーを持っていきます。返還の手数料がかかることが多いです。警察・センター・市区町村に出した届け出を取り下げ、チラシをはがしてお礼を。けががなくても、ノミ・ダニや脱水がないか動物病院で一度みてもらいます。</p></li></ul></li>
    </ol>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>保護された子は、何日待ってもらえる？町によってちがいます</h2></div>
    <p>待ってもらえる日数、迎えるときの費用、猫を収容するかどうかは、自治体ごとにかなり違います。届け出をその日のうちに出し、毎日問い合わせる理由はここにあります。</p>
    <div class="tbl"><table class="jc-cmp"><tbody>{wait}</tbody></table></div>
    <div class="sh" id="pro" tabindex="-1"><h2>ペット探偵を比較する</h2></div>
    <p>迷子の捜索をしている会社は、料金のしくみ（1日ごと・数日のまとめ）も、交通費やチラシ代が入っているかも違います。<a href="#report">いなくなった市区町村を入力する</a>と、対応地域の会社だけを表示します。</p>
    <div id="jcPro">{det_tbl}</div>
    {f'<h3>ペット保険の契約者が使える捜索</h3><ul>{ins_html}</ul>' if ins_html else ""}
    <div class="sh"><h2>犬と猫で、さがし方がちがう</h2></div>
    <div class="jc-vs"><div><h4>犬</h4><ul><li>いなくなった場所から円をえがくように広げる</li><li>散歩道・公園・駅まで</li><li>大型犬は1日に何十kmも動くことがある</li><li>首輪や鑑札があれば、警察に届けられることもある</li></ul></div>
    <div><h4>猫</h4><ul><li>まず家の中を、もう一度</li><li>家の近くの狭くて暗い場所</li><li>夜や早朝に、小さな声で</li><li>猫を収容しない自治体もある</li></ul></div></div>
    <div class="sh" id="found" tabindex="-1"><h2>迷子の犬・猫を見つけた・保護した方へ</h2></div>
    <p>首輪や鑑札がある子は、飼い主がさがしているはずです。見つけた場所の警察に届けるか、動物愛護センター・保健所に連絡します。上で見つけた場所の市区町村を入れると、その町の窓口が出ます。けがをしているときは、近くの動物病院へ。くわしい流れは<a href="/guide/found-pet/">迷子の犬・猫を保護したら</a>に。</p>
    <div class="emg-tips"><h4>よくある質問</h4>{_faq(e, MAIGO_FAQ)}</div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>保護された子のお迎えや、動物病院への移動に</h2><p>動物愛護センターや動物病院への移動は、ケージごと乗れるペットタクシーも使えます。</p></div>
    <ul class="other"><li><a href="/guide/lost-cat/">迷子の猫のさがし方</a></li><li><a href="/guide/lost-dog/">迷子の犬のさがし方</a></li><li><a href="/guide/lost-flyer/">迷子のチラシの書き方</a></li><li><a href="/guide/microchip/">マイクロチップの登録を確かめる・変更する</a></li></ul>
    <p class="emg-note">窓口は環境省の地方自治体連絡先一覧の受け持ちに合わせ、各自治体と警察庁・警視庁の公式ページの情報をもとに（{CHECKED}時点）。電話番号は各窓口のページでご確認ください。</p>
  </div>
</section>
<div id="jcPrint" aria-hidden="true"></div>
</main>
"""
    return ctx["head"](title, desc, url, _ld(SITE, url, "迷子になったら", MAIGO_FAQ)).replace("</head>", CSS + "</head>", 1) + body + '<script src="/jichitai/jc.js" defer></script>\n' + ctx["foot_noband"]()


# ============ 犬の登録 ============
TOUROKU_FAQ = [
 ("犬の登録はいつまでにすればいいですか？", "飼い始めてから30日以内です。生後90日以内の子犬は、生後90日をすぎてから30日以内に、住んでいる市区町村で登録します。登録は一生に1回です。このページで迎えた日を入れると、期限の日が出ます。"),
 ("犬の登録の手数料はいくらですか？", "横浜市・名古屋市・福岡市・千葉市・杉並区はどこも、登録が3,000円、狂犬病の予防注射済票の交付が550円です（注射そのものの料金は動物病院ごと）。"),
 ("マイクロチップが入っていれば、登録はいりませんか？", "住んでいる市区町村が特例に参加していれば、マイクロチップの登録が犬の登録の代わりになり、窓口に行く必要はありません。福岡市や杉並区はこの形です。千葉市は参加していないので、チップが入っていても窓口で登録します。"),
 ("狂犬病の予防注射はいつ受けますか？", "毎年4月1日〜6月30日の間に1回です。この期間の外で飼い始めたときは、飼い始めてから30日以内に受けます。動物病院か、市区町村の集合注射で受けられます。"),
 ("引っ越しや、亡くなったときは？", "30日以内に市区町村へ届け出ます（引っ越しは新しい住所の市区町村へ）。マイクロチップの登録も、住所の変更・死亡の届け出をします（無料）。"),
]

def touroku(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/jichitai/touroku/"
    title = "犬の登録と狂犬病の予防注射：いつまでに・どこで・いくら｜迎えた日から期限がわかる｜ペットのくらし窓口"
    desc = "子犬や保護犬を迎えたら、迎えた日と住んでいる市区町村を入れるだけで、登録と予防注射の期限の日と窓口が出ます。主な市の手数料（登録3,000円・注射済票550円）と、マイクロチップで登録が済む市・済まない市のちがいも。"
    fees = "".join(f'<tr><th><a href="{e(u)}" target="_blank" rel="noopener">{e(c)}</a></th><td>{e(a)}</td><td>{e(b)}</td><td>{e(n)}</td></tr>' for c, a, b, n, u in FEES)
    body = f"""
<main>
<section class="area-hero">
  <div class="wrap">
    {_crumb(e, "犬の登録と予防注射")}
    <h1>犬を迎えたら：登録と予防注射の期限と窓口</h1>
  </div>
</section>
<section style="padding-top:4px">
  <div class="wrap">
    {_three("やることは3つ", [("30日以内に、市区町村で登録する", "一生に1回。主な市は3,000円"), ("毎年4〜6月に、狂犬病の予防注射", "動物病院か、市区町村の集合注射で"), ("もらった鑑札と注射済票を首輪につける", "迷子のとき、飼い主が分かります")])}
    {_ask("touroku", "住んでいる市区町村", "例：佐倉市・世田谷区")}
    <div class="jc-q1" style="border-width:1px"><div class="jc-ff" style="margin:0"><label>迎えた日<input id="jcD" type="date"></label><label>生まれた日（生後90日より前に迎えたときだけ）<input id="jcB" type="date"></label></div>
      <p class="jc-due" id="jcDue" aria-live="polite"></p></div>
    <div id="jcR">
    <ol class="jc-tl">
      <li><span class="jc-when">まず確かめる</span><h3>どこから迎えた？で、やることが変わる</h3>
        <div class="jc-vs"><div><h4>ペットショップ・ブリーダー</h4><ul><li>マイクロチップが入っている（2022年6月から義務）</li><li>環境省の登録の飼い主の変更をする</li><li>市区町村が特例に参加していれば、窓口の登録はいらない</li></ul></div>
        <div><h4>保護犬・知人から</h4><ul><li>チップが入っていないこともある</li><li>前の飼い主の鑑札があれば、新しい市区町村に届け出</li><li>なければ市区町村の窓口で新しく登録</li></ul></div></div></li>
      <li><span class="jc-when">30日以内</span><h3>市区町村で登録して、鑑札をもらう</h3>
        <ul class="jc-ck">
          {_li("city", "市区町村の窓口で登録する（一生に1回）", "持ちものは、手数料（横浜市・名古屋市・福岡市・千葉市・杉並区はどれも3,000円）と、マイクロチップの番号が分かるもの。名古屋市のように、市が頼んでいる動物病院や電子申請で登録できる市もあります。", "")}
          {_li("chip", "マイクロチップが入っている子は、飼い主の変更をする", "ショップやブリーダーから受け取った登録証明書の番号で、環境省の登録サイトから。住所・連絡先の変更は無料です。", f'<a href="{CHIP}" target="_blank" rel="noopener">マイクロチップの登録サイト ↗</a>')}
        </ul></li>
      <li><span class="jc-when">毎年4〜6月</span><h3>狂犬病の予防注射を受けて、注射済票をもらう</h3>
        <ul class="jc-ck">
          {_li("vet", "動物病院か、市区町村の集合注射で受ける", "動物病院で受けたら、注射済証を市区町村に出して注射済票（上の5つの市・区はどれも550円）をもらいます。動物病院で済票まで受け取れる市もあります。", '<a href="/hospital/">近くの動物病院をさがす</a>')}
          <li data-ck="tag"><label><input type="checkbox">鑑札と注射済票を首輪につける</label><p>迷子のとき、鑑札の番号から飼い主が分かります。なくしたら再交付（名古屋市・福岡市は鑑札1,600円・済票340円）。</p></li>
        </ul></li>
      <li><span class="jc-when">そのあと</span><h3>引っ越し・飼い主が変わる・亡くなったときは30日以内に届け出</h3>
        <ul class="jc-ck"><li data-ck="move"><label><input type="checkbox">市区町村と、マイクロチップの登録の両方を変える</label><p>引っ越しは新しい住所の市区町村へ、前の鑑札を持って。マイクロチップの住所・連絡先の変更と死亡の届け出は無料です。</p></li></ul></li>
    </ol>
    </div>
    <div class="sh"><h2>手数料は登録3,000円・注射済票550円。ちがうのは「チップで済むか」と「どこで出せるか」</h2></div>
    <div class="tbl"><table class="jc-cmp"><thead><tr><th>市・区</th><th>登録</th><th>注射済票</th><th>ちがうところ</th></tr></thead><tbody>{fees}</tbody></table></div>
    <p class="jc-src">各市・区の公式ページの情報をもとに（{CHECKED}時点）。注射そのものの料金は、動物病院ごとに決まっています。</p>
    <div class="emg-tips"><h4>よくある質問</h4>{_faq(e, TOUROKU_FAQ)}</div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>予防注射や登録の日の移動に</h2><p>動物病院や窓口への移動は、ペットタクシーも使えます。</p></div>
    <ul class="other"><li><a href="/guide/dog-registration/">犬の登録と狂犬病の予防注射（くわしい決まり）</a></li><li><a href="/guide/microchip/">マイクロチップの登録を確かめる・変更する</a></li><li><a href="/guide/moving-with-pet/">ペットと引っ越すときの手続き</a></li></ul>
  </div>
</section>
</main>
"""
    return ctx["head"](title, desc, url, _ld(SITE, url, "犬の登録と予防注射", TOUROKU_FAQ)).replace("</head>", CSS + "</head>", 1) + body + '<script src="/jichitai/jc.js" defer></script>\n' + ctx["foot_noband"]()


# ============ 飼えなくなったとき ============
TEBANASU_FAQ = [
 ("ペットを飼えなくなったら、どこに相談すればいいですか？", "入院や出張など一時的なら預け先（ペットホテル・シッター）、介護が理由なら老犬ホーム・老猫ホームやかかりつけの動物病院、新しい家族をさがすなら知人や譲渡の活動をしている団体です。どうしても難しいときは、動物愛護センター・保健所に相談できます。"),
 ("保健所や動物愛護センターは、必ず引き取ってくれますか？", "必ずではありません。年をとった・病気になったという理由や、新しい飼い主をさがす取り組みを先にしていないときなどは、断ることができると法律で決まっています。引き取りは有料のことが多く、事前の相談がいります。"),
 ("老犬ホームの費用は？", "入所のとき・月ごと・医療費・終生の一括払いの4つでできていて、施設ごとにまったく違います。都道府県ごとの老犬ホームのページで、公式サイトに出ている金額を見くらべられます。"),
 ("捨てたらどうなりますか？", "犬や猫を捨てることは動物愛護管理法で禁じられていて、1年以下の拘禁刑または100万円以下の罰金です。追いつめられる前に、相談してください。"),
]

def tebanasu(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/jichitai/tebanasu/"
    title = "ペットを飼えなくなったら：手放す前にできること｜預ける・老犬ホーム・新しい家族・センターへの相談｜ペットのくらし窓口"
    desc = "入院、介護、引っ越し、家族の事情。犬や猫を飼い続けるのが難しくなったときに、理由ごとにできることを順番に。住んでいる市区町村を入れると、近くのペットホテル・シッター・老犬ホーム・譲渡の窓口と、動物愛護センター・保健所が出ます。センターが引き取りを断ることがある理由も。"
    body = f"""
<main>
<section class="area-hero">
  <div class="wrap">
    {_crumb(e, "飼えなくなったとき")}
    <h1>ペットを飼えなくなりそうなとき：手放す前にできること</h1>
  </div>
</section>
<section style="padding-top:4px">
  <div class="wrap">
    {_ask("tebanasu", "住んでいる市区町村", "例：佐倉市・世田谷区")}
    <div id="jcR">
    <div class="sh"><h2>理由によって、相談するところが違います</h2></div>
    <div class="jc-opt">
      <div><h3>入院・出張・介護で、しばらく世話ができない</h3><p>手放さずに、その間だけ預けられます。家族や知人のほか、ペットホテル、家に来てくれるペットシッター。</p><div class="jc-go" data-slot="tmp"><a href="/pet-hotel/">ペットホテル</a><a class="l" href="/pet-sitter/">ペットシッター</a></div></div>
      <div><h3>年をとって、介護が難しくなった</h3><p>老犬ホーム・老猫ホームは、月ごとの預かりから終生の預かりまであります。費用は施設ごとにまったく違うので、見学して見くらべます。かかりつけの動物病院にも相談を。</p><div class="jc-go" data-slot="rojin"><a href="/rojin-home/">老犬ホーム・老猫ホーム</a><a class="l" href="/guide/rojin-home-cost/">費用のしくみ</a></div></div>
      <div><h3>ほえる・かむなど、困りごとがある</h3><p>手放す理由が行動なら、直せることがあります。動物病院か、ドッグトレーナーに相談します。</p><div class="jc-go"><a href="/dog-trainer/">ドッグトレーナー</a></div></div>
      <div><h3>どうしても、新しい家族をさがすしかない</h3><p>まず家族・親せき・友人に。譲渡の活動をしている団体は、団体ごとに受ける条件があります。ネットの里親募集を使うときは、相手と会い、飼う環境を確かめてから。</p><div class="jc-go" data-slot="joto"><a href="/joto/">譲渡の窓口と団体</a></div></div>
      <div><h3>それでも難しいとき：動物愛護センター・保健所に相談</h3><p>いきなり連れていくのではなく、まず相談から。引き取りは有料のことが多く、次のような理由では断られることがあります。</p><div class="jc-go" data-slot="center"></div></div>
    </div>
    </div>
    <div class="sh"><h2>センター・保健所が引き取りを断ることがある理由</h2></div>
    <ol><li>年をとった、病気になった、という理由のとき</li><li>新しい飼い主をさがす取り組みを、先にしていないとき</li><li>引き取りを何度もくり返し求めるとき</li><li>繁殖を制限するように言われたのに従わず、生まれた子を引き取ってほしいとき</li><li>犬猫の販売業者からの求め</li><li>飼うことが難しいとは認められない理由のとき</li></ol>
    <p class="jc-src">動物愛護管理法と、神奈川県動物愛護センターの案内をもとに。神奈川県では、事前の相談なしに持ち込んでも引き取らず、家族全員の同意がいるとしています。</p>
    <div class="sh"><h2>新しい家や施設に送るときに渡すもの</h2></div>
    <ul><li>ワクチン・不妊去勢手術・病気の記録、ふだんのごはんと量、性格や苦手なこと</li><li>マイクロチップの登録証明書（新しい飼い主が変更登録をする）</li><li>犬は鑑札。新しい飼い主の市区町村でも届け出がいります</li></ul>
    <div class="emg-tips"><h4>よくある質問</h4>{_faq(e, TEBANASU_FAQ)}</div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>預け先や新しい家までの移動に</h2><p>ホテル・老犬ホーム・新しい家族の家までは、飼い主さんも一緒に乗れるペットタクシーで移動できます。</p></div>
    <ul class="other"><li><a href="/guide/cant-keep-pet/">ペットを飼えなくなったときの相談先（くわしく）</a></li><li><a href="/guide/rojin-home/">老犬ホームを見学するときに確かめること</a></li><li><a href="/guide/senior/">シニア犬・シニア猫の移動</a></li></ul>
  </div>
</section>
</main>
"""
    return ctx["head"](title, desc, url, _ld(SITE, url, "飼えなくなったとき", TEBANASU_FAQ)).replace("</head>", CSS + "</head>", 1) + body + '<script src="/jichitai/jc.js" defer></script>\n' + ctx["foot_noband"]()


PAGES = {"maigo": maigo, "touroku": touroku, "tebanasu": tebanasu}

def urls(SITE):
    return [f"{SITE}/jichitai/{k}/" for k in PAGES]

def write_all(ROOT, ctx):
    for k, f in PAGES.items():
        os.makedirs(os.path.join(ROOT, "jichitai", k), exist_ok=True)
        open(os.path.join(ROOT, "jichitai", k, "index.html"), "w", encoding="utf-8").write(f(ctx))
    open(os.path.join(ROOT, "jichitai", "data.json"), "w", encoding="utf-8").write(
        json.dumps(data(ROOT, ctx["pref_slug"]), ensure_ascii=False, separators=(",", ":")))
    src = os.path.join(HERE, "jichitai.js")
    open(os.path.join(ROOT, "jichitai", "jc.js"), "w", encoding="utf-8").write(open(src, encoding="utf-8").read())
