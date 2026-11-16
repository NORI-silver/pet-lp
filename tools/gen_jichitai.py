# お金を取らない情報ページ「ペットの迷子・犬の登録・引取りの窓口」（/jichitai/）。gen_areas.py が読み込んで使う。
# Nori 2026-11-02「全部マネタイズじゃなくていい。SEO的なコンテンツでもいい」「どんどん進めて」。
# 守ること：公的な情報源だけ（環境省の自治体連絡先一覧と、各自治体の公式ページ）。電話番号は載せない。
# データ：tools/jichitai.json（都道府県47・政令指定都市20・中核市62。担当の分け方は環境省の一覧に合わせた）。
import json, os
import prefkeep

J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jichitai.json"), encoding="utf-8"))

SLUG = "jichitai"
TITLE = "ペットの迷子・犬の登録・引取りの窓口｜全国の動物愛護センター・保健所の一覧（47都道府県・129自治体）｜ペットタクシー予約窓口"
DESC = "犬や猫が迷子になったとき、保護したとき、犬の登録や狂犬病の予防注射、引っ越し、飼えなくなったときの相談先を、全国47都道府県と政令指定都市・中核市の動物愛護センター・保健所、都道府県警察の公式ページでまとめた無料の一覧です。窓口ごとに受け付けていることと、迷子のときにすることもわかります。"

# どこに連絡するか（どれも法律と各自治体の案内に書いてあること）
WHERE = [
 ("迷子の犬・猫をさがしている", "下の一覧の<b>動物愛護センター・保健所</b>（住んでいる所と、いなくなった所の両方）と、<b>警察</b>（遺失届）。市区町村の清掃の担当や近くの動物病院にも。くわしくは<a href=\"/guide/lost-pet/\">ペットが迷子になったら</a>（<a href=\"/guide/lost-cat/\">猫のさがし方</a>・<a href=\"/guide/lost-dog/\">犬のさがし方</a>・<a href=\"/guide/lost-flyer/\">チラシの作り方</a>）。"),
 ("迷子の犬・猫を見つけた・保護した", "首輪や鑑札がある子は<b>警察</b>へ。飼い主の分からない子は<b>動物愛護センター・保健所</b>に引き取りを求めることもできます。くわしくは<a href=\"/guide/found-pet/\">迷子の犬・猫を保護したら</a>。"),
 ("犬を飼い始めた（登録）・狂犬病の予防注射", "お住まいの<b>市区町村</b>。登録は一生に1回、予防注射は毎年1回です。くわしくは<a href=\"/guide/dog-registration/\">犬の登録と狂犬病の予防注射</a>。"),
 ("引っ越した・犬が亡くなった", "お住まいの<b>市区町村</b>に30日以内に届け出（引っ越しは新しい住所の市区町村へ）。マイクロチップを入れている子は、その登録の変更も。くわしくは<a href=\"/guide/moving-with-pet/\">ペットと引っ越すときの手続き</a>、<a href=\"/sougi/\">ペットが亡くなったら</a>。"),
 ("飼えなくなった・引取りの相談", "下の一覧の<b>動物愛護センター・保健所</b>。いきなり連れていくのではなく、まずは相談から。引き取りは有料のことが多く、理由によっては断られることもあります。くわしくは<a href=\"/guide/cant-keep-pet/\">ペットを飼えなくなったときの相談先</a>。"),
 ("夜間・休日に具合が悪い", "<a href=\"/hospital/night/\">夜間・救急の動物病院</a>へ。移動の手段がないときは<a href=\"/emergency/\">緊急のときの連絡先</a>も。"),
]

# 窓口ごとに受け付けていること（環境省・警察庁・厚生労働省・自治体の案内から）
ROLES = [
 ("動物愛護センター・保健所（都道府県・政令指定都市・中核市）",
  "迷子の届け出と、保護された犬・猫の情報（収容情報のページ）／保護された子の返還／飼い主の分からない犬・猫の引き取り／飼えなくなったときの相談と引き取り／新しい飼い主への譲渡（譲渡会）／けがをした犬・猫の収容／ペットショップなど動物取扱業の登録"),
 ("市区町村（区役所・市役所・町村役場）",
  "犬の登録と鑑札／狂犬病の予防注射の済票と集合注射／引っ越し・飼い主の変更・亡くなったときの届け出（30日以内）／道路で亡くなった犬・猫の引き取り（清掃事務所・環境事業センターなど）"),
 ("警察（警察署・交番）",
  "迷子の犬・猫の遺失届（多くの道府県はオンラインでも）／首輪や鑑札のある犬・猫を拾ったときの届け出／明らかに捨てられている動物の通報"),
 ("環境省のマイクロチップのデータベース",
  "マイクロチップの登録、飼い主の変更（オンライン400円など）、住所・連絡先の変更と亡くなったときの届け出（無料）"),
]

# 都道府県警察の落とし物の届け出・検索（警察庁「落とし物の届出・検索」のページにあるリンク。2026年11月2日に確認）
NPA_URL = "https://www.npa.go.jp/bureau/soumu/ishitsubutsu/ishitsu-todokedekensaku.html"
POLICE = {
 "東京都": ("警視庁「落とし物・忘れ物」", "https://www.keishicho.metro.tokyo.lg.jp/sodan/otoshimono/index.html"),
 "大阪府": ("大阪府警察の落とし物の公表（遺失届は警察署・交番の窓口で）", "http://www.otoshimono.police.pref.osaka.jp/"),
}

# ---- 見て分かる形（Nori 2026-11-16「これももっとリッチにして」）：窓口ごとにできることをアイコンで、住まいでどの窓口かを図で、ボタンは大きく ----
def _ic(p):
    return ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23c2410c' "
            "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E" + p + "%3C/svg%3E\")")
IC = {
 "search": "%3Ccircle cx='11' cy='11' r='6'/%3E%3Cpath d='M20 20l-4.5-4.5'/%3E",
 "home": "%3Cpath d='M4 11l8-7 8 7v9h-5v-6H9v6H4z'/%3E",
 "hand": "%3Cpath d='M12 20s-7-4.3-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.7-7 10-7 10z'/%3E",
 "talk": "%3Cpath d='M4 5h16v11H9l-5 4z'/%3E%3Cpath d='M8 9.5h8M8 12.5h5'/%3E",
 "doc": "%3Cpath d='M6 3.5h8l4 4v13H6z'/%3E%3Cpath d='M9 12h6M9 16h6'/%3E",
 "move": "%3Cpath d='M3 13h11V6H3zM14 9h4l3 3v4h-7'/%3E%3Ccircle cx='7' cy='17' r='1.8'/%3E%3Ccircle cx='17' cy='17' r='1.8'/%3E",
 "police": "%3Cpath d='M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6z'/%3E%3Cpath d='M9.5 11.5l2 2 3.5-3.5'/%3E",
 "moon": "%3Cpath d='M19 14.5A7.5 7.5 0 0 1 9.5 5a7.5 7.5 0 1 0 9.5 9.5z'/%3E",
 "pin": "%3Cpath d='M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z'/%3E%3Ccircle cx='12' cy='10' r='2.3'/%3E",
 "list": "%3Cpath d='M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01'/%3E",
 "out": "%3Cpath d='M14 5h5v5M19 5l-8 8M17 14v5H5V7h5'/%3E",
 "city": "%3Cpath d='M4 20V9l5-3v14M9 20V4l7 3v13M16 20v-9l4 2v7M3 20h18'/%3E",
}
CSS = ("<style>.jc-ic{display:inline-block;width:22px;height:22px;flex:0 0 22px;background:center/22px no-repeat}"
 + "".join(f".jc-ic.i-{k}{{background-image:{_ic(v)}}}" for k, v in IC.items()) +
 ".jc-tiles{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:6px 0 0}"
 "@media(min-width:640px){.jc-tiles{grid-template-columns:1fr 1fr 1fr}}"
 ".jc-tile{display:flex;flex-direction:column;gap:6px;background:#fff;border:1px solid #f1e3d6;border-radius:14px;padding:10px}"
 ".jc-tile .jc-ic{width:34px;height:34px;flex-basis:34px;border-radius:50%;background-color:#fff1e6;background-size:20px}"
 ".jc-tt{display:block;font-size:.8rem;color:#6b5a4e;line-height:1.4}.jc-ta{display:block;font-size:.92rem;font-weight:700;line-height:1.4;margin-top:2px}"
 ".jc-tile details{margin-top:auto;padding:0!important;background:none!important;border:0!important;box-shadow:none!important}.jc-tile details>summary{all:unset;display:inline-block;font-size:.78rem;color:#c2410c;cursor:pointer;text-decoration:underline;padding:2px 0}.jc-tile details>summary::after,.jc-tile details>summary::before{display:none!important;content:none!important}.jc-tile details>summary::-webkit-details-marker{display:none}.jc-tile p{margin:4px 0 0;font-size:.82rem;line-height:1.6;color:#4a3d34}"
 ".jc-map{background:#fff;border:1px solid #f1e3d6;border-radius:16px;padding:14px;margin:10px 0}"
 ".jc-map h5{margin:0 0 8px;font-size:1rem;display:flex;gap:6px;align-items:center}"
 ".jc-q{font-size:.85rem;color:#6b5a4e;font-weight:700;margin:0 0 6px}"
 ".jc-br{display:grid;gap:6px}.jc-br>div{display:grid;grid-template-columns:1fr auto 1fr;gap:6px;align-items:center}"
 ".jc-br .w{background:#fff7ed;border-radius:10px;padding:8px 10px;font-size:.88rem;line-height:1.5}"
 ".jc-br .a{color:#c2410c;font-weight:700}.jc-br .t{background:#c2410c;color:#fff;border-radius:10px;padding:8px 10px;font-size:.88rem;font-weight:700;line-height:1.45}"
 ".jc-br .t.c2{background:#2b211b}"
 ".jc-find{display:flex;gap:6px;margin:10px 0 0}.jc-find input{flex:1;min-width:0;padding:10px 12px;border:1px solid #e5d5c8;border-radius:10px;font-size:1rem}"
 ".jc-ans{margin:8px 0 0;font-size:.92rem;color:#2b211b}.jc-ans:empty{display:none}.jc-ans button{margin:4px 4px 0 0;padding:8px 12px;border:1px solid #c2410c;border-radius:999px;background:#fff;color:#c2410c;font-weight:700;font-size:.9rem}"
 ".jc-q1{background:#fff;border:2px solid #c2410c;border-radius:16px;padding:12px 14px;margin:6px 0 10px}.jc-q1 label{display:flex;gap:6px;align-items:center;font-weight:700;margin:0 0 6px}.jc-sub{margin:0 0 8px;font-size:.84rem;color:#4a3d34;line-height:1.6}.jc-q1 input{width:100%;box-sizing:border-box;padding:12px;border:1px solid #e5d5c8;border-radius:10px;font-size:1rem}"
 ".jc-card{background:#fff;border:1px solid #f1e3d6;border-radius:16px;padding:14px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,.04)}"
 ".jc-card.hit,.cs.jc-card.hit{border:2px solid #c2410c}"
 ".jc-hd{display:flex;gap:10px;align-items:center}.jc-hd .jc-ic{width:40px;height:40px;flex-basis:40px;border-radius:12px;background-color:#fff1e6;background-size:24px}"
 ".jc-hd b{display:block;font-size:1.02rem;line-height:1.4}.jc-hd small{display:block;color:#6b5a4e;font-size:.82rem}"
 ".jc-can{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}.jc-can span{display:inline-flex;gap:4px;align-items:center;background:#fff7ed;border-radius:999px;padding:4px 10px 4px 6px;font-size:.82rem}"
 ".jc-can .jc-ic{width:18px;height:18px;flex-basis:18px;background-size:18px}"
 ".jc-btns{display:flex;flex-wrap:wrap;gap:8px}.jc-btns a{flex:1 1 140px;display:flex;gap:6px;justify-content:center;align-items:center;padding:11px 10px;border-radius:12px;font-weight:700;font-size:.9rem;text-decoration:none;border:1px solid #e5d5c8;color:#2b211b;background:#fff}"
 ".jc-btns a.p{background:#2b211b;color:#fff;border-color:#2b211b}.jc-btns a .jc-ic{width:18px;height:18px;flex-basis:18px;background-size:18px}"
 ".jc-btns a.p .jc-ic{filter:brightness(0) invert(1)}"
 ".jc-pol{display:flex;gap:10px;align-items:center;background:#f5f7ff;border-radius:14px;padding:12px;margin:10px 0}.jc-pol p{margin:0;font-size:.88rem}"
 ".jc-pol b{display:block}</style>")

# 住まいの市区町村を入れる → その人の窓口のカード1枚だけを出す（Nori 2026-11-16「どこの窓口って書いてあるところが何を言ってるかわからない」）。
# 対応の図（住まい → 窓口）はやめた。市区町村の一覧は /jichitai/munis.json（入れはじめたときだけ読む。都道府県は名前から自動で選ぶ）
FIND_JS = """<script>(function(){var i=document.getElementById('jcQ'),o=document.getElementById('jcA'),sel=document.getElementById('hospPref'),D=null;if(!i)return;
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function show(pf,nm){if(sel.value!==pf){sel.value=pf;sel.dispatchEvent(new Event('change'))}var s=document.querySelector('.emg-pref[data-pref="'+pf+'"]');if(!s)return;var hit=null;
s.querySelectorAll('.jc-card[data-city]').forEach(function(c){if(c.getAttribute('data-city')===nm)hit=c});if(!hit)hit=s.querySelector('.jc-card[data-main]');
s.querySelectorAll('.jc-card').forEach(function(c){c.hidden=c!==hit;c.classList.toggle('hit',c===hit)});o.innerHTML='<b>'+esc(pf+nm)+'</b>の迷子・保護の窓口です。';if(hit){var c=hit.cloneNode(true);c.hidden=false;c.removeAttribute('data-city');c.removeAttribute('data-main');o.appendChild(c)}try{gtag('event','jichitai_find',{pref:pf})}catch(e){}}
function reset(){document.querySelectorAll('.emg-pref .jc-card').forEach(function(c){c.hidden=false;c.classList.remove('hit')});o.textContent=''}
function go(){var v=i.value.replace(/[\\s　]/g,'');if(!v){reset();return}if(!D){fetch('/jichitai/munis.json').then(function(r){return r.json()}).then(function(j){D=j;go()});return}
var h=[];Object.keys(D).forEach(function(pf){var w=v.indexOf(pf)===0?v.slice(pf.length):v;if(!w)return;D[pf].split(',').forEach(function(n){if(w===n||w.indexOf(n)===0||(w.length>=2&&n.indexOf(w)===0))h.push([pf,n])})});
var ex=h.filter(function(x){return x[1]===v||x[0]+x[1]===v});if(ex.length===1)h=ex;
if(h.length===1)return show(h[0][0],h[0][1]);reset();
if(h.length>1&&h.length<=8){o.innerHTML='どちらですか？ '+h.map(function(x,k){return '<button type="button" data-k="'+k+'">'+esc(x[0]+x[1])+'</button>'}).join(' ');o.querySelectorAll('button').forEach(function(b){b.onclick=function(){var x=h[+b.getAttribute('data-k')];i.value=x[1];show(x[0],x[1])}})}
else if(h.length>8)o.textContent='続けて入れてください';else o.textContent='見つかりません。市区町村の名前で入れてください（例：佐倉市）';}
i.addEventListener('input',go);})();</script>"""

def write_munis():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = {}
    for m in json.load(open(os.path.join(root, "tools", "municipalities.json"), encoding="utf-8")):
        out.setdefault(m["pref"], []).append(m["name"])
    os.makedirs(os.path.join(root, SLUG), exist_ok=True)
    open(os.path.join(root, SLUG, "munis.json"), "w", encoding="utf-8").write(
        json.dumps({k: ",".join(v) for k, v in out.items()}, ensure_ascii=False, separators=(",", ":")))


def _maps(name):
    from urllib.parse import quote
    return "https://www.google.com/maps/search/?api=1&query=" + quote(name)

def _card(e, d, sub="", city="", joto=""):
    # ほかの分野と同じ共通のカード（tools/cardskin.py の .cs。Nori 2026-11-16「タクシー以外のカードは共通のやつにして」）：
    # 太字の名前・小さな受け持ちの行・札・大きいボタン2つ（公式ページ／地図）・小さな文字のリンク1行
    # 迷子・保護・返還・飼えなくなったときの相談はどの窓口も受けるので札にしない（当たり前のことは出さない）。ちがいの出る譲渡だけ
    tags = '<li class="ok">譲渡もしている</li>' if joto else ""
    small = [f'<a href="{e(l["u"])}" target="_blank" rel="noopener" title="{e(l["t"])}">保護情報 ↗</a>' for l in d["links"][:1]]
    if joto: small.append(f'<a href="{e(joto)}">譲渡の条件</a>')
    attr = f' data-city="{e(city)}"' if city else " data-main"
    return (f'<div class="jc-card cs"{attr}><a class="ux-c-n" href="{e(d["url"])}" target="_blank" rel="noopener"><b>{e(d["name"])}</b></a>'
            f'<p class="ux-c-m">{e(sub)}</p>' + (f'<ul class="dr-tags">{tags}</ul>' if tags else "") +
            f'<div class="ux-c-a"><a href="{e(d["url"])}" target="_blank" rel="noopener">公式ページ ↗</a>'
            f'<a class="l" href="{e(_maps(d["name"]))}" target="_blank" rel="noopener">地図を見る</a></div>'
            + (f'<p class="ux-c-s">{"　".join(small)}</p>' if small else "") + '</div>')

def _police(e, pf):
    t, u = POLICE.get(pf, (f"{pf}警察の遺失届・落とし物の検索（警察庁のページから{pf}を選ぶ）", NPA_URL))
    return (f'<div class="jc-pol"><i class="jc-ic i-police"></i><p><b>警察（遺失届）</b><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></p></div>')

def _route(e, pf, cs):
    """住まい → 窓口 の図。"""
    if cs:
        names = "・".join(c["city"] for c in cs)
        rows = (f'<div><span class="w">{e(names)}に住んでいる</span><span class="a">→</span><span class="t">市の窓口</span></div>'
                f'<div><span class="w">{e(pf)}のそのほかの市町村</span><span class="a">→</span><span class="t">{e(pf)}の窓口</span></div>')
    else:
        rows = f'<div><span class="w">{e(pf)}のどの市町村でも</span><span class="a">→</span><span class="t">{e(pf)}の窓口</span></div>'
    rows += '<div><span class="w">犬の登録・予防注射・引っ越し</span><span class="a">→</span><span class="t c2">お住まいの市区町村</span></div>'
    find = ""
    if cs:
        find = (f'<div class="jc-find"><input type="text" inputmode="text" placeholder="お住まいの市区町村（例：{e(cs[0]["city"])}）" aria-label="お住まいの市区町村"></div>'
                '<p class="jc-ans" aria-live="polite"></p>')
    return (f'<div class="jc-map"><h5><i class="jc-ic i-pin"></i>どの窓口？</h5><p class="jc-q">迷子・保護・引き取りの相談</p>'
            f'<div class="jc-br">{rows}</div>{find}</div>')

TILE_IC = ["search", "hand", "doc", "move", "talk", "moon"]
TILE_SHORT = ["動物愛護センター・保健所と警察", "首輪・鑑札あり→警察／なし→センター", "お住まいの市区町村", "市区町村へ30日以内に", "センター・保健所に相談", "夜間・救急の動物病院"]

def render(ctx):
    e, SITE = ctx["e"], ctx["SITE"]
    url = f"{SITE}/{SLUG}/"
    P = {p["pref"]: p for p in J["prefs"]}
    C = {}
    for c in J["cities"]:
        C.setdefault(c["pref"], []).append(c)
    body = ""
    slug = ctx.get("pref_slug", {})
    JOTO = {}
    try:
        for x in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "joto.json"), encoding="utf-8"))["centers"]:
            JOTO[(x["pref"], x.get("city") or "")] = x
    except Exception:
        pass
    for lab, prefs in ctx["emg_regions"]:
        body += f'<h3 class="emg-region">{e(lab)}</h3>\n'
        for pf in prefs:
            cs = C.get(pf, [])
            js = JOTO.get((pf, ""))
            jurl = f'/joto/{slug.get(pf)}/' if js and slug.get(pf) else ""
            others = "・".join(c["city"] for c in cs)
            inner = _card(e, P[pf], (f"{others}以外の{pf}にお住まいの方" if cs else f"{pf}のどの市町村にお住まいの方も"), "", jurl)
            for c in cs:
                cj = f'/joto/{slug.get(pf)}/' if JOTO.get((pf, c["city"])) and slug.get(pf) else ""
                inner += _card(e, c, f'{c["city"]}にお住まいの方', c["city"], cj)
            body += f'<section class="emg-pref" data-pref="{e(pf)}"><h4>{e(pf)}</h4>{inner}{_police(e, pf)}</section>\n'
    where = "".join(f'<div class="jc-tile"><i class="jc-ic i-{TILE_IC[n]}"></i><div><span class="jc-tt">{e(t)}</span><span class="jc-ta">{e(TILE_SHORT[n])}</span><details><summary>くわしく</summary><p>{d}</p></details></div></div>' for n, (t, d) in enumerate(WHERE))
    roles = "".join(f"<tr><th>{e(t)}</th><td>{e(d)}</td></tr>" for t, d in ROLES)
    faq = [
      ("迷子の犬・猫は、どこに連絡すればいいですか？", "住んでいる所と、いなくなった所の動物愛護センター・保健所（政令指定都市・中核市なら市の窓口）と、警察（遺失届）です。あわせて、市区町村の清掃の担当と近くの動物病院にも連絡しておくと安心です。このページの一覧から、各自治体の迷子の情報のページに行けます。"),
      ("保健所と動物愛護センターは、どちらに連絡すればいいですか？", "自治体によって、動物愛護センターが受け持つ地域と、保健所が受け持つ地域があります。このページの一覧は、住んでいる都道府県・市の窓口の公式ページにつながっているので、そこで受け持ちを確かめてください。"),
      ("保護された子は、いつまで待っていてもらえますか？", "保護してから飼い主をさがす期間は自治体ごとに決まっていて、すぎると新しい飼い主さがしなどに回ることがあります。日数は自治体ごとに違うので、いなくなったらできるだけ早く届け出てください。"),
      ("保護された子を迎えに行くときは、何がいりますか？", "飼い主と分かるもの（写真、鑑札やマイクロチップの番号）と本人確認の書類です。返還には手数料がかかることが多く、金額や必要なものは自治体ごとに違うので、行く前に窓口で確かめてください。"),
      ("迷子の犬を保護しました。警察と保健所のどちらに届けますか？", "首輪や鑑札がある、飼われていたと思われる犬は、警察に届けます。飼い主の分からない犬・猫は、動物愛護センター・保健所に引き取りを求めることもできます。"),
      ("犬の登録や狂犬病の予防注射は、どこでしますか？", "お住まいの市区町村です。登録は飼い始めてから30日以内に一生に1回、予防注射は毎年4月1日〜6月30日の間に1回です。"),
      ("猫にも登録はありますか？", "猫には犬のような登録の決まりはありません。ただ、ペットショップなどから迎えた猫はマイクロチップが入っていることがあり、飼い主の変更登録が必要です。"),
      ("飼えなくなったら、保健所は必ず引き取ってくれますか？", "必ずではありません。年をとった・病気になったという理由や、新しい飼い主をさがす取り組みを先にしていないときなどは、断ることができると法律で決められています。まずは窓口に相談してください。"),
    ]
    faq_html = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in faq)
    guides = [("ペットが迷子になったら：すぐにすること・届け出先・さがし方", "/guide/lost-pet/"),
              ("迷子の猫のさがし方", "/guide/lost-cat/"),
              ("迷子の犬のさがし方", "/guide/lost-dog/"),
              ("迷子のチラシの作り方", "/guide/lost-flyer/"),
              ("迷子の犬・猫を見つけた・保護したら", "/guide/found-pet/"),
              ("マイクロチップの登録を確かめる・変更する", "/guide/microchip/"),
              ("犬の登録と狂犬病の予防注射（いつ・どこで・いくら）", "/guide/dog-registration/"),
              ("ペットと引っ越すときの手続き", "/guide/moving-with-pet/"),
              ("ペットを飼えなくなったときの相談先", "/guide/cant-keep-pet/"),
              ("ペットが亡くなったら（火葬・葬儀と自治体の受付）", "/sougi/")]
    guides_html = "".join(f'<li><a href="{u}">{e(t)}</a></li>' for t, u in guides)
    ld = '<script type="application/ld+json">\n' + json.dumps([
      {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ペットタクシー予約窓口", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "ペットの迷子・犬の登録・引取りの窓口", "item": url}]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}],
      ensure_ascii=False, indent=1) + "\n</script>"
    return ctx["head"](TITLE, DESC, url, ld).replace("</head>", CSS + "</head>", 1) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › ペットの迷子・犬の登録・引取りの窓口</nav>
    <h1><small>全国47都道府県・政令指定都市・中核市（129自治体）</small>ペットの迷子・犬の登録・引取りの窓口</h1>
    <p class="lede">迷子・保護・犬の登録・引っ越しのとき、どこに連絡するかが分かります。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">
    <div class="emg">
      <div class="jc-q1"><label for="jcQ"><i class="jc-ic i-pin"></i>迷子をさがす・保護したときの窓口</label><p class="jc-sub">飼い主さんはお住まいの、保護した人は見つけた場所の市区町村を入れてください。</p><input id="jcQ" type="text" placeholder="市区町村（例：佐倉市）" autocomplete="address-level2"><p id="jcA" class="jc-ans" aria-live="polite"></p></div>
      <div class="f"><label for="hospPref">都道府県</label><select id="hospPref">{ctx["emg_opts"]}</select></div>
      {body}
      <div class="emg-tips"><h4>窓口ごとに受け付けていること</h4>
      <div class="tbl"><table><thead><tr><th>窓口</th><th>おもに受け付けていること</th></tr></thead><tbody>{roles}</tbody></table></div>
      <p class="emg-tips-note">迷子・保護・引き取りは都道府県（政令指定都市・中核市は市）、犬の登録と予防注射は市区町村、と受け持ちが分かれています。迷子のときは、動物愛護センター・保健所と警察の両方に届け出てください。見つけた人がどちらに届けるか分からないからです。</p></div>
      <div class="emg-tips"><h4>こんなときは、ここへ</h4><div class="jc-tiles">{where}</div></div>
      <div class="emg-tips"><h4>迷子になったら、まずすること</h4><ol>
        <li><b>すぐにさがし始める</b><br>猫は家の中と、家のまわりの狭くて暗い場所（物置、室外機の下、植え込み、縁の下）。犬はいなくなった場所を中心に円をえがくように広げます。</li>
        <li><b>その日のうちに届け出る</b><br>動物愛護センター・保健所（住んでいる所と、いなくなった所）、警察（遺失届）、市区町村の清掃の担当、近くの動物病院。マイクロチップの登録の連絡先がいまのものかも確かめます。</li>
        <li><b>収容情報のページを毎日見る</b><br>東京都は収容期限を7日間としているので、問い合わせの間をあけすぎないように。上の一覧の「迷子・保護」のリンクや、<a href="https://www.env.go.jp/nature/dobutsu/aigo/shuyo/link.html" target="_blank" rel="noopener">環境省の自治体リンク一覧</a>から。となりの市や県も。</li>
        <li><b>チラシ・掲示板・SNSで知らせる</b><br>写真、いなくなった日時と場所、特徴、連絡先（自宅の住所は書かない）。</li>
      </ol><p class="emg-tips-note">さがし方・チラシの書き方・犬と猫のちがい・見つかったあとの手続きは<a href="/guide/lost-pet/">ペットが迷子になったら</a>にまとめています。</p></div>
      <div class="emg-tips"><h4>保護された子を迎えに行くとき</h4><dl>
        <dt>持っていくもの</dt><dd>飼い主と分かるもの（写真、鑑札やマイクロチップの番号）と、本人確認の書類。リードやキャリーも。</dd>
        <dt>手数料</dt><dd>返還には手数料がかかることが多く、金額は自治体ごとに違います。行く前に窓口に確かめてください。</dd>
        <dt>迎えに行ったあと</dt><dd>警察やほかの窓口に出した届け出を取り下げ、動物病院で一度みてもらうと安心です。動物愛護センターは駅から遠いこともあるので、移動はケージごと乗れる車が便利です。</dd>
      </dl></div>
      <div class="emg-tips"><h4>手続きと相談のガイド</h4><ul class="other">{guides_html}</ul></div>
      <div class="emg-tips"><h4>よくある質問</h4><dl>{faq_html}</dl></div>
      <p class="emg-note">どの自治体がどの地域を受け持つかは、環境省の<a href="{e(J["source"])}" target="_blank" rel="noopener">地方自治体連絡先一覧</a>に合わせています。リンク先は各自治体と警察の公式ページです（{e(J["checked"])}に確認）。ページの場所や受付の方法は変わることがあるので、つながらないときは自治体のサイトの中でさがしてください。電話番号は各自治体のページでご確認ください。掲載の内容の誤りは、<a href="/contact/">お問い合わせ</a>からお知らせください。</p>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>保護された子のお迎えや、通院の移動に</h2><p>動物愛護センターや動物病院への移動は、ペットタクシーを予約できます。当日の依頼もできます。</p></div>
    <ul class="other"><li><a href="/joto/">保護犬・保護猫を迎える（譲渡の窓口と条件）</a></li><li><a href="/hospital/">条件でさがす動物病院</a></li><li><a href="/emergency/">緊急のときの連絡先</a></li><li><a href="/guide/hospital/">動物病院への通院の送迎ガイド</a></li><li><a href="/dogrun/">全国のドッグラン</a></li></ul>
    {ctx["area_links"]()}
  </div>
</section>
</main>
{prefkeep.LIST_JS}
{FIND_JS}
""" + ctx["foot_noband"]()

def urls(SITE):
    return [f"{SITE}/{SLUG}/"]

def write_all(ROOT, ctx):
    os.makedirs(os.path.join(ROOT, SLUG), exist_ok=True)
    open(os.path.join(ROOT, SLUG, "index.html"), "w", encoding="utf-8").write(render(ctx))
    write_munis()
