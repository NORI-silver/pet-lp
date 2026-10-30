"""pet-lp のエリア別ページ・sitemap・robots・404・style.css を作る。
使い方: python3 gen_areas.py /home/claude/pet-lp
"""
import json, os, re, sys, html

ROOT = sys.argv[1]
SITE = "https://pet.shiokonbu.com"
TODAY = "2026-10-28"  # 更新日（sitemap と記事の dateModified）
PUBLISHED = "2026-10-27"  # ガイド記事の公開日

# 料金の目安（片道）。提携先ごとの料金表とエリアの対応は tools/fares.json にまとめている。
# 会社を足したら fares.json を直してこのスクリプトを実行すると、トップの料金表・フォームの概算・エリアページがまとめて変わる。
import math
FARES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fares.json"), encoding="utf-8"))
CO = FARES["companies"]
ALL_PREFS = list(FARES["areas"])
def cos_for(pref=None):
    keys = FARES["areas"][pref] if pref else [k for p in ALL_PREFS for k in FARES["areas"][p]]
    return [CO[k] for k in dict.fromkeys(keys)]
def ride(c, km):
    km = max(1, math.ceil(km)); f = c["base"]; frm = c["base_km"]
    for upto, add in c["tiers"]:
        upto = upto if upto is not None else float("inf")
        if km > frm: f += add * (min(km, upto) - frm)
        frm = upto
    return f
def total(c, km, round_trip=False):
    rf = c.get("round_flat")
    if round_trip and rf and km * 2 <= rf[0]: return rf[1] + c["pick"] + c["back"]
    return ride(c, km) * (2 if round_trip else 1) + c["pick"] + c["back"]
def yen(n): return f"{n:,}円"
# 夜間・早朝の割増（会社ごと）。料金表・エリアページ・よくある質問で同じ文を使う
def night_text(pref=None):
    parts = []
    for c in cos_for(pref):
        if c.get("night", 1) > 1 and c.get("night_hours"):
            h0, h1 = c["night_hours"]; pct = round((c["night"] - 1) * 10)
            parts.append(f"{c['label']}は、{h0}時〜朝{h1}時のお迎えで乗車料金が{pct}割増し")
        else:
            parts.append(f"{c['label']}は、夜間の割増が料金表にありません")
    return "、".join(parts) + "。"
def fare_text(km, pref=None, round_trip=False):
    v = sorted({total(c, km, round_trip) for c in cos_for(pref)})
    return yen(v[0]) + "〜" if len(v) == 1 else f"{v[0]:,}〜{yen(v[-1])}"
def fare_note(pref=None):
    cs = cos_for(pref)
    head = "片道の目安です。" + ("依頼先のペットタクシーの料金表で計算しています。" if len(cs) == 1 else f"依頼先のペットタクシー{len(cs)}社の料金表で計算していて、どの会社が引き受けるかで変わります。")
    tail = "目安には高速代・駐車場代は入っていません。確定料金（税込）は、お迎えが決まったときに引き受けた会社から、一般道の場合と高速道路を使う場合の両方をお知らせします。運賃は当日、ペットタクシーへ直接お支払いください（当サイトへのお支払いはありません）。" + "".join(c.get("pay", "") for c in cs)
    return head + "".join(c["note"] for c in cs) + FARES.get("area_note", {}).get(pref or "", "") + tail
# フォームの概算（index.html）に渡す料金データ
FARE_JS = "var FARES = " + json.dumps({k: {x: c.get(x) for x in ("label","base_km","base","tiers","pick","back","night","night_hours","round_flat","wait","shop","pick_free_km","pick_over")} for k, c in CO.items()}, ensure_ascii=False) + ";\n  var REVIEWS = " + json.dumps({c["partner_id"]: c["review_url"] for c in CO.values() if c.get("partner_id") and c.get("review_url")}, ensure_ascii=False) + ";\n  var AREA_FARES = " + json.dumps(FARES["areas"], ensure_ascii=False) + ";"

# 予約側も同じ料金データを使う（Code.gs を貼り直すときに含まれる）。
booking_path = os.path.join(ROOT, "booking", "Code.gs")
booking_src = open(booking_path, encoding="utf-8").read()
booking_src = re.sub(r"/\*SELECTION_FARES\*/.*?/\*/SELECTION_FARES\*/", lambda m: "/*SELECTION_FARES*/var SELECTION_FARES = " + json.dumps({k: {x: v for x, v in c.items() if x != "review_url"} for k, c in CO.items()}, ensure_ascii=False) + ";/*/SELECTION_FARES*/", booking_src, count=1, flags=re.S)
open(booking_path, "w", encoding="utf-8").write(booking_src)

src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
# トップの料金表とフォームの概算を fares.json から書き込む
TOP_TABLE = f"""        <h3>距離ごとの目安</h3>
        <dl>
""" + "".join(f'          <div class="row"><dt>{k}km</dt><dd>{fare_text(k)}</dd></div>\n' for k in (5, 10, 20, 30, 50)) + f"""        </dl>
        <h3>たとえば</h3>
        <dl>
          <div class="row"><dt>世田谷区 → 羽田空港<br>（約18km）</dt><dd>{fare_text(18, '東京都')}</dd></div>
          <div class="row"><dt>松戸市 → 柏市<br>（約8km）</dt><dd>{fare_text(8, '千葉県')}</dd></div>
        </dl>
      </div>
    </div>
    <p class="fare-flag"><b>確定料金ではありません。</b>上の金額は目安です。確定料金（税込）は、お迎えが決まったときに引き受けた会社からメールでお知らせします。</p>
    <p class="fare-night"><b>🌙 夜間・早朝の割増</b>上の目安は昼間の料金です。{night_text()}</p>
    <p class="small">{fare_note()}エリアごとの目安は、各エリアのページにまとめています。</p>"""
src = re.sub(r"<!--FARE_TABLE-->.*?<!--/FARE_TABLE-->", lambda m: "<!--FARE_TABLE-->" + TOP_TABLE + "<!--/FARE_TABLE-->", src, count=1, flags=re.S)
EMG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "emergency.json"), encoding="utf-8"))
EMG = {"checked": EMG["checked"], "taxis": EMG["taxis"], "hospitals": EMG["hospitals"]}
src = re.sub(r"/\*EMG\*/.*?/\*/EMG\*/", lambda m: "/*EMG*/var EMG = " + json.dumps(EMG, ensure_ascii=False) + ";/*/EMG*/", src, count=1, flags=re.S)
src = re.sub(r"/\*FARES\*/.*?/\*/FARES\*/", lambda m: "/*FARES*/" + FARE_JS + "/*/FARES*/", src, count=1, flags=re.S)
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(src)
css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
extra_css = """
/* エリア別ページ */
.crumb{font-size:.78rem;color:var(--ink-3);padding:14px 0 0}
.crumb a{color:var(--ink-3);text-decoration:none}
.crumb a:hover{text-decoration:underline}
.area-hero{background:radial-gradient(90% 70% at 100% 0%,#ffe2cc 0%,rgba(255,226,204,0) 60%),var(--cream);padding:24px 0 56px}
.area-hero h1{font-family:var(--round);font-size:1.6rem;font-weight:800;line-height:1.4;margin:18px 0 14px}
.area-hero h1 small{display:block;font-size:.95rem;color:var(--o-d);margin-bottom:6px}
.area-hero .lede{color:var(--ink-2);margin:0 0 22px}
.prose{max-width:780px;margin:0 auto}
.prose h2{font-size:1.4rem;margin:0 0 16px}
.prose h3{font-size:1.08rem;margin:26px 0 8px}
.prose p{color:var(--ink-2)}
.terms h2{font-size:1.1rem!important;margin:30px 0 10px!important}
.terms ul{color:var(--ink-2);padding-left:1.2em}
.terms .small{font-size:.8rem;color:var(--ink-3);margin-top:30px}
.count{display:flex;gap:14px;align-items:center;background:#fff;border-radius:var(--r);padding:18px 20px;box-shadow:var(--shadow);margin:22px 0}
.count b{font-family:var(--round);font-size:2.2rem;color:var(--o-d);line-height:1}
.count span{font-size:.88rem;color:var(--ink-2);line-height:1.6}
.other{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:0;justify-content:center}
.other a{display:block;border:1px solid var(--line);border-radius:999px;padding:8px 16px;font-size:.88rem;font-weight:700;color:var(--ink);text-decoration:none;background:#fff}
.other a:hover{border-color:var(--o);color:var(--o-d)}
/* ガイド */
.art{max-width:760px;margin:0 auto}
.art h2{font-size:1.35rem;margin:44px 0 14px;padding-left:14px;border-left:5px solid var(--o);line-height:1.45}
.art p{color:var(--ink-2);margin:0 0 16px}
.art ul,.art ol{color:var(--ink-2);padding-left:1.4em;margin:0 0 18px}
.art li{margin:6px 0}
.art .tip{background:var(--o-l);border-radius:18px;padding:16px 18px;color:var(--ink);font-weight:600;margin:0 0 18px}
.art .tip::before{content:"POINT";display:block;font-size:.72rem;letter-spacing:.12em;color:var(--o-d);font-weight:800;margin-bottom:4px}
.art .tbl{overflow-x:auto;margin:0 0 18px}
.art table{border-collapse:collapse;width:100%;font-size:.78rem;line-height:1.5;background:#fff}
.art th,.art td{border:1px solid var(--line);padding:8px 4px;text-align:center}
@media (min-width:600px){.art table{font-size:.88rem}.art th,.art td{padding:10px 8px}}
.art th{background:#f7f4f1}
.art td:last-child,.art th:last-child{background:var(--o-l);font-weight:700}
.art .btn{margin:8px 0 18px}
.art-img{margin:0 0 8px;border-radius:24px;overflow:hidden;aspect-ratio:3/2;background:var(--cream)}
.art-img img{width:100%;height:100%;object-fit:cover;display:block}
.src{font-size:.8rem;color:var(--ink-3);border-top:1px solid var(--line);margin-top:36px;padding-top:16px}
.src ul{padding-left:1.2em}
.src a{color:var(--ink-3)}
@media (min-width:760px){.art h2{font-size:1.55rem}}
@media (min-width:760px){.area-hero{padding:32px 0 80px}.area-hero h1{font-size:2.5rem}.prose h2{font-size:1.7rem}}
"""
open(os.path.join(ROOT, "style.css"), "w", encoding="utf-8").write(css.strip() + "\n" + extra_css.strip() + "\n")

AREAS = [
 dict(slug="tokyo", pref="東京都", short="東京", count=17,
  title="東京のペットタクシー｜犬・猫のタクシーを手配料0円で予約（世田谷・渋谷・23区）",
  desc="東京都のペットタクシーを手配料0円でおまかせ手配。世田谷・渋谷・新宿・墨田など23区から八王子・町田まで、犬のタクシー・猫のタクシーをお探しします。動物病院への通院、お引っ越し、羽田空港への送迎にも。完全予約制です。",
  lede="23区の動物病院への通院から、お引っ越し、羽田空港への送迎まで。東京のペットタクシーを、フォーム1回で探してお迎えの時間をお知らせします。",
  body=[
   ("東京でペットタクシーを使う理由", "東京23区は動物病院の数が多い一方、電車やバスにペットを乗せるにはキャリーに入れる決まりがあり、大型犬はそもそも乗れません。一般のタクシーも、ペット連れだと断られることがあります。ペット専用のタクシーなら、ケージや介護用のマットを積んだ車で、犬も猫もそのまま乗れます。"),
   ("犬のタクシー・猫のタクシー、東京で多い使い方", "世田谷区や目黒区から専門の動物病院への通院、お引っ越しのときの長距離移動、羽田空港からの国内線での帰省などが多い使い方です。飼い主さんが仕事で付き添えない日に、ペットだけを病院やペットホテルへ送ることもできます。"),
  ],
  cities=["世田谷区","墨田区","渋谷区","新宿区","港区","目黒区","品川区","大田区","杉並区","練馬区","江東区","江戸川区","足立区","板橋区","中野区","八王子市","町田市","府中市","調布市","立川市"],
  route=("世田谷区 → 羽田空港", 18),
  faq=[
   ("東京23区内の動物病院まで、ペットタクシーはいくらですか？", f"距離で決まることが多く、依頼先の料金表で計算すると、5kmで{fare_text(5)}、10kmで{fare_text(10)}が片道の目安です。お迎えの時間と一緒に、依頼先の料金にもとづく目安をお伝えします。"),
   ("羽田空港への送迎はできますか？", f"はい。世田谷区から羽田空港（約18km）で{fare_text(18)}が片道の目安です。飛行機に乗せる場合は、航空会社のペット預かりの受付時間に間に合うよう、メモ欄にフライトの時刻を書いてください。"),
   ("東京で夜間や早朝のお迎えも頼めますか？", "フォームは24時間送れますが、完全予約制で、連絡はすべてメールです。夜間・早朝は引き受けられる会社が見つからないこともあるため、早めのご予約をおすすめします。" + night_text("東京都") + "急な体調不良で一刻を争うときは、まず動物病院に電話してください。"),
  ]),
 dict(slug="kanagawa", pref="神奈川県", short="神奈川・横浜", count=5,
  title="神奈川・横浜のペットタクシー｜犬・猫のタクシーを手配料0円で予約",
  desc="神奈川県（横浜・川崎・相模原・藤沢など）のペットタクシーを手配料0円でおまかせ手配。犬のタクシー・猫のタクシーで、動物病院への通院や羽田空港への送迎、都内への移動にも対応します。",
  lede="横浜・川崎から湘南エリアまで。動物病院への通院や、都内の専門病院への移動、羽田空港への送迎に、神奈川のペットタクシーをお探しします。",
  body=[
   ("神奈川でペットタクシーを使う理由", "横浜市や川崎市は坂道や丘の上の住宅地が多く、大型犬やシニアの子を連れて歩いたり、公共交通で移動したりするのは大変です。ペットタクシーなら玄関先まで迎えに来てくれるので、抱っこやキャリーで長く歩かせる必要がありません。"),
   ("横浜・川崎から都内への移動も", "神奈川から東京の専門病院や二次診療の動物病院へ通う方も多くいます。県をまたぐ移動も、東京と神奈川の両方のペットタクシーに声をかけて、空いている車をお探しします。"),
  ],
  cities=["横浜市","川崎市","相模原市","藤沢市","横須賀市","鎌倉市","茅ヶ崎市","大和市","厚木市","平塚市","海老名市","小田原市"],
  route=("横浜駅周辺 → 羽田空港", 25),
  faq=[
   ("横浜から都内の動物病院まで頼めますか？", f"はい。県をまたぐ移動にも対応しています。横浜から都内までの20〜30kmなら、20kmで{fare_text(20)}、30kmで{fare_text(30)}が片道の目安です。"),
   ("湘南エリア（藤沢・茅ヶ崎・鎌倉）でも使えますか？", "はい。神奈川県内全域に対応しています。地域によって空いている車が少ないことがあるので、日にちに余裕をもってご依頼ください。"),
   ("大型犬をスロープ付きの車で運んでもらえますか？", "フォームに体重と犬種を入れていただくと、大型犬が乗れる車とスロープのあるペットタクシーを選んでお声がけします。"),
  ]),
 dict(slug="chiba", pref="千葉県", short="千葉", count=4,
  title="千葉のペットタクシー｜犬・猫のタクシーを手配料0円で予約（船橋・松戸・佐倉・成田）",
  desc="千葉県（千葉市・船橋・松戸・柏・佐倉・四街道・成田など）のペットタクシーを手配料0円でおまかせ手配。犬のタクシー・猫のタクシーで、動物病院への通院や成田空港・都内への移動に対応します。",
  lede="船橋・松戸・柏の住宅街から、佐倉・四街道・成田まで。動物病院への通院や成田空港への送迎に、千葉のペットタクシーをお探しします。",
  body=[
   ("千葉でペットタクシーを使う理由", "千葉県は車での移動が中心の地域が多く、車を持っていないご家庭や、運転できない日には通院の手段が限られます。佐倉・四街道・富里などでは、近くに夜間の動物病院が少なく、離れた病院まで移動することもあります。ペットタクシーなら、自宅から病院まで直接送ってもらえます。"),
   ("成田空港・都内への長距離移動にも", "成田空港からの帰省やお引っ越し、都内の専門病院への通院など、長い距離の移動も多い地域です。千葉に拠点のあるペットタクシーと、千葉まで来てくれる東京のペットタクシーの両方からお探しします。"),
  ],
  cities=["千葉市","船橋市","松戸市","柏市","市川市","浦安市","佐倉市","四街道市","成田市","八千代市","習志野市","富里市","印西市","流山市"],
  route=("船橋市 → 成田空港", 45),
  faq=[
   ("佐倉や四街道からでもペットタクシーは来てくれますか？", "はい。四街道市や富里市に拠点のあるペットタクシーもあります。空きがないときは、近くのエリアのペットタクシーにもお声がけします。"),
   ("成田空港まで運んでもらえますか？", f"はい。船橋市から成田空港までの約45kmなら、{fare_text(45, '千葉県')}が片道の目安です。フライトの時刻をメモ欄に書いてください。"),
   ("千葉から都内の病院へ通えますか？", "はい。県をまたぐ移動にも対応しています。病院への往復なら「往復」を選んで、帰りの時刻（診察が終わるころ）を入れてください。待っていてもらうか、あらためて迎えに来てもらうかは、安いほうを引き受けた会社がご案内します。"),
  ]),
 dict(slug="saitama", pref="埼玉県", short="埼玉", count=3,
  title="埼玉のペットタクシー｜犬・猫のタクシーを手配料0円で予約（さいたま・川口・川越）",
  desc="埼玉県（さいたま市・川口・越谷・所沢・川越など）のペットタクシーを手配料0円でおまかせ手配。犬のタクシー・猫のタクシーで、動物病院への通院や都内への移動に対応します。",
  lede="さいたま市・川口から川越・所沢まで。動物病院への通院や都内の専門病院への移動に、埼玉のペットタクシーをお探しします。",
  body=[
   ("埼玉でペットタクシーを使う理由", "埼玉県は都内へ通う方が多く、平日の昼間は家族が付き添えないことがよくあります。ペットタクシーなら、飼い主さんが乗れない日でも、ペットだけを病院やトリミング、ペットホテルへ送ってもらえます。"),
   ("さいたま市から都内の専門病院へ", "大宮・浦和から都内の二次診療の動物病院へ通う方もいます。県をまたぐ移動は、埼玉と東京の両方のペットタクシーにお声がけして、空いている車をお探しします。"),
  ],
  cities=["さいたま市","川口市","越谷市","所沢市","川越市","草加市","春日部市","戸田市","上尾市","熊谷市"],
  route=("大宮駅周辺 → 新宿区", 30),
  faq=[
   ("さいたま市から都内まで頼めますか？", f"はい。大宮周辺から新宿までの約30kmなら、{fare_text(30)}が片道の目安です。"),
   ("飼い主が乗らずにペットだけ運んでもらえますか？", "はい。フォームの「一緒に乗る人数」で「0人（ペットだけ）」を選んでください。ペットだけの送迎ができるペットタクシーをお探しします。"),
   ("埼玉の北部（熊谷など）でも使えますか？", "はい。埼玉県内全域に対応しています。エリアによって空いている車が少ないこともあるので、日にちに余裕をもってご依頼ください。"),
  ]),
]

PAW = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="6" cy="9" r="2.2"/><circle cx="10" cy="5.5" r="2.2"/><circle cx="14" cy="5.5" r="2.2"/><circle cx="18" cy="9" r="2.2"/><path d="M12 11c-3 0-6 3.6-6 6.2 0 1.8 1.5 2.8 3 2.8 1.2 0 2-.6 3-.6s1.8.6 3 .6c1.5 0 3-1 3-2.8C18 14.6 15 11 12 11z"/></svg>'
ARROW = '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h12M11 5l5 5-5 5"/></svg>'
CHECK = '<span><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8.5l3 3 7-7"/></svg></span>'
e = html.escape

def area_links(cur=None):
    return '<ul class="other">' + ''.join(
        f'<li><a href="/{a["slug"]}/">{e(a["short"])}のペットタクシー</a></li>' for a in AREAS if a["slug"] != cur) + '</ul>'

def head(title, desc, url, extra_ld, og_img="/img/hero.jpg", og_w=1200, og_h=900):
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="max-image-preview:large">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="ペットタクシー予約窓口">
<meta property="og:locale" content="ja_JP">
<meta property="og:image" content="{SITE}{og_img}">
<meta property="og:image:width" content="{og_w}">
<meta property="og:image:height" content="{og_h}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#ff6a1a">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
{extra_ld}
</head>
<body>
<header class="top">
  <div class="wrap">
    <a class="logo" href="/"><i>{PAW}</i>ペットタクシー予約窓口</a>
    <nav><a href="/#how">使い方</a><a href="/#area">エリア</a><a href="/#price">料金</a><a href="/guide/">ガイド</a><a href="/#faq">よくある質問</a></nav>
    <a class="mini" href="/#form">予約する</a>
  </div>
</header>
'''

PARTNER_BAND = '''<aside class="partner-band"><div class="wrap"><p><b>ペットタクシー会社の方へ</b>東京・神奈川・千葉・埼玉で、いっしょにペットと飼い主さんをお迎えしてくださる会社を探しています。</p><a href="/partner/">提携のご案内</a></div></aside>
'''

def foot(cta_href, band=True):
    return (PARTNER_BAND if band else '') + f'''<footer>
  <div class="wrap">
    <nav><a href="/">トップ</a><a href="/#how">使い方</a><a href="/#price">料金の目安</a><a href="/guide/">ペットの移動ガイド</a><a href="/#faq">よくある質問</a><a href="/#policy">キャンセルについて</a><a href="/#privacy">個人情報の取り扱い</a><a href="/terms/">利用規約</a><a href="/#operator">運営者情報</a><a href="/contact/">お問い合わせ</a><a href="/partner/">提携をご希望の会社さま</a></nav>
    <nav>{''.join(f'<a href="/{a["slug"]}/">{e(a["short"])}</a>' for a in AREAS)}</nav>
    <p>ペットタクシー予約窓口（東京・神奈川・千葉・埼玉）</p>
    <p>&copy; 2026 ペットタクシー予約窓口</p>
  </div>
</footer>
<div class="sticky"><a class="btn" href="{cta_href}">ペットタクシーを予約する</a></div>
</body>
</html>
'''

# ガイド（/guide/）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guides import GUIDES
GBY = {g["slug"]: g for g in GUIDES}

def guide_cards(slugs, cls=""):
    return f'<ul class="gcards {cls}">' + "".join(
        f'<li><a href="/guide/{s}/"><b>{e(GBY[s]["title"])}</b><span>{e(GBY[s]["lede"])}</span></a></li>' for s in slugs) + '</ul>'

for a in AREAS:
    url = f'{SITE}/{a["slug"]}/'
    cta = f'/?pref={a["pref"]}#form'
    ld = [
      {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":a["short"]+"のペットタクシー","item":url}]},
      {"@context":"https://schema.org","@type":"Service","name":a["short"]+"のペットタクシー手配","serviceType":"ペットタクシーの手配（犬のタクシー・猫のタクシー）","url":url,
       "description":a["desc"],"provider":{"@type":"Organization","name":"ペットタクシー予約窓口","url":SITE+"/"},
       "areaServed":{"@type":"AdministrativeArea","name":a["pref"]},
       "offers":{"@type":"Offer","price":"0","priceCurrency":"JPY","description":"手配料無料（運賃は事業者へ直接お支払い）"}},
      {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":ans}} for q,ans in a["faq"]]},
    ]
    ld_html = "\n".join('<script type="application/ld+json">\n' + json.dumps(x, ensure_ascii=False, indent=1) + '\n</script>' for x in ld)
    body = "".join(f'<h2>{e(h)}</h2><p>{e(p)}</p>' if i == 0 else f'<h3>{e(h)}</h3><p>{e(p)}</p>' for i,(h,p) in enumerate(a["body"]))
    page = head(a["title"], a["desc"], url, ld_html) + f'''
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › {e(a["short"])}のペットタクシー</nav>
    <h1><small>犬のタクシー・猫のタクシー</small><span style="white-space:nowrap">{e(a["short"])}の</span><span style="white-space:nowrap">ペットタクシー。</span><br>手配料0円でおまかせ。</h1>
    <p class="lede">{e(a["lede"])}</p>
    <ul class="pills"><li>{CHECK}手配料 0円</li><li>{CHECK}完全予約制</li><li>{CHECK}多頭もOK</li><li>{CHECK}アプリ不要</li></ul>
    <a class="btn" href="{cta}">{e(a["short"])}でペットタクシーを予約する{ARROW}</a>
  </div>
</section>

<section>
  <div class="wrap prose">
    {body}
    <div class="count"><b>0<small style="font-size:.9rem">円</small></b><span>当サイトの手配料です。完全予約制で、引き受ける会社が決まったらメールでお知らせします。運賃はペットタクシーへ直接お支払いください。</span></div>
  </div>
</section>

<section class="scenes">
  <div class="wrap">
    <div class="sh"><span class="eyebrow">AREA</span><h2>{e(a["short"])}の対応エリア</h2><p>{e(a["pref"])}の全域に対応しています。下は主な市区です。ここにない地域も、お気軽にどうぞ。</p></div>
    <div class="area" style="background:#fff;max-width:780px;margin:0 auto"><h3>{e(a["pref"])}</h3><ul class="chips">{''.join(f'<li>{e(c)}</li>' for c in a["cities"])}</ul></div>
  </div>
</section>

<section class="price">
  <div class="wrap">
    <div class="sh"><span class="eyebrow">PRICE</span><h2>{e(a["short"])}のペットタクシー料金の目安</h2><p>お支払いはペットタクシーの運賃だけ。手配料は0円です。</p></div>
    <div class="price-wrap">
      <div class="free"><div class="t"><b>手配料</b>何度使っても</div><div class="v">0<small>円</small></div></div>
      <div class="fare">
        <h3>距離ごとの目安</h3>
        <dl>
          <div class="row"><dt>5km</dt><dd>{fare_text(5, a["pref"])}</dd></div>
          <div class="row"><dt>10km</dt><dd>{fare_text(10, a["pref"])}</dd></div>
          <div class="row"><dt>20km</dt><dd>{fare_text(20, a["pref"])}</dd></div>
          <div class="row"><dt>30km</dt><dd>{fare_text(30, a["pref"])}</dd></div>
          <div class="row"><dt>50km</dt><dd>{fare_text(50, a["pref"])}</dd></div>
        </dl>
        <h3>たとえば</h3>
        <dl><div class="row"><dt>{e(a["route"][0])}<br>（約{a["route"][1]}km）</dt><dd>{fare_text(a["route"][1], a["pref"])}</dd></div></dl>
      </div>
    </div>
    <p class="fare-flag"><b>確定料金ではありません。</b>上の金額は目安です。確定料金（税込）は、お迎えが決まったときに引き受けた会社からメールでお知らせします。</p>
    <p class="fare-night"><b>🌙 夜間・早朝の割増</b>上の目安は昼間の料金です。{night_text(a["pref"])}</p>
    <p class="small">{fare_note(a["pref"])}</p>
  </div>
</section>

<section class="faq">
  <div class="wrap">
    <div class="sh"><span class="eyebrow">FAQ</span><h2>{e(a["short"])}のペットタクシー よくある質問</h2></div>
    <div class="faq-list">
      {''.join(f'<details><summary>{e(q)}</summary><div class="a">{e(ans)}</div></details>' for q,ans in a["faq"])}
    </div>
    <p style="text-align:center;margin-top:20px"><a href="/#faq">そのほかのよくある質問を見る</a></p>
  </div>
</section>

<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>ペットの移動ガイド</h2></div>
    {guide_cards(["what-is-pet-taxi", "hospital", "airport-moving"])}
    <p class="more"><a href="/guide/">ほかのガイドも見る</a></p>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sh"><h2>ほかのエリアのペットタクシー</h2></div>
    {area_links(a["slug"])}
  </div>
</section>

<section style="padding-top:0">
  <div class="wrap">
    <div class="last">
      <h2>{e(a["short"])}で、大切な家族の移動にやさしい一台を。</h2>
      <p>完全予約制・手配料0円。フォームを送ったら、あとは決まるのを待つだけ。</p>
      <a class="btn center" href="{cta}">ペットタクシーを予約する{ARROW}</a>
    </div>
  </div>
</section>
</main>
''' + foot(cta)
    os.makedirs(os.path.join(ROOT, a["slug"]), exist_ok=True)
    open(os.path.join(ROOT, a["slug"], "index.html"), "w", encoding="utf-8").write(page)

def block(b):
    if isinstance(b, str): return f"<p>{e(b)}</p>"
    k, v = b
    if k in ("ul", "ol"): return f"<{k}>" + "".join(f"<li>{e(x)}</li>" for x in v) + f"</{k}>"
    if k == "tip": return f'<p class="tip">{e(v)}</p>'
    if k == "cta": return f'<a class="btn" href="/#form">{e(v)}{ARROW}</a>'
    if k == "table":
        h, *rows = v
        return '<div class="tbl"><table><thead><tr>' + "".join(f"<th>{e(x)}</th>" for x in h) + '</tr></thead><tbody>' + \
          "".join("<tr>" + "".join((f"<th>{e(x)}</th>" if i == 0 else f"<td>{e(x)}</td>") for i, x in enumerate(r)) + "</tr>" for r in rows) + '</tbody></table></div>'
    raise ValueError(k)

for g in GUIDES:
    url = f'{SITE}/guide/{g["slug"]}/'
    ld = [
      {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"ペットの移動ガイド","item":SITE+"/guide/"},
        {"@type":"ListItem","position":3,"name":g["title"],"item":url}]},
      {"@context":"https://schema.org","@type":"Article","headline":g["title"],"description":g["desc"],"url":url,
       "image":f'{SITE}/img/guide/{g["img"]}',"datePublished":PUBLISHED,"dateModified":TODAY,"inLanguage":"ja",
       "author":{"@id":SITE+"/#org"},"publisher":{"@id":SITE+"/#org"},"mainEntityOfPage":url},
    ]
    if g.get("faq"):
        ld.append({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
          {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":ans}} for q,ans in g["faq"]]})
    ld_html = "\n".join('<script type="application/ld+json">\n' + json.dumps(x, ensure_ascii=False, indent=1) + '\n</script>' for x in ld)
    body = "".join(f'<h2>{e(h)}</h2>' + "".join(block(b) for b in bs) for h, bs in g["sections"])
    faq = ""
    if g.get("faq"):
        faq = '<h2>よくある質問</h2><div class="faq-list">' + "".join(f'<details><summary>{e(q)}</summary><div class="a">{e(ans)}</div></details>' for q,ans in g["faq"]) + '</div>'
    src = '<div class="src"><b>参考にした情報</b><ul>' + "".join(f'<li><a href="{e(u)}" rel="noopener" target="_blank">{e(n)}</a></li>' for n,u in g["sources"]) + '</ul><p>内容は公開日時点のものです。ルールや料金は変わることがあるため、ご利用の前に各社の案内をご確認ください。</p></div>'
    page = head(g["seo_title"] + "｜ペットタクシー予約窓口", g["desc"], url, ld_html, f'/img/guide/{g["img"]}', 1200, 800) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › <a href="/guide/">ペットの移動ガイド</a> › {e(g["title"])}</nav>
    <h1>{e(g["title"])}</h1>
    <p class="lede">{e(g["lede"])}</p>
    <figure class="art-img"><picture><source srcset="/img/guide/{g["img"][:-4]}.webp" type="image/webp"><img src="/img/guide/{g["img"]}" alt="{e(g["img_alt"])}" width="1200" height="800" fetchpriority="high" onerror="this.closest('figure').remove()"></picture></figure>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap"><article class="art">
    {body}
    {faq}
    {src}
  </article></div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>あわせて読みたい</h2></div>
    {guide_cards(g["related"], "three")}
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="last">
      <h2>大切な家族の移動に、やさしい一台を。</h2>
      <p>完全予約制・手配料0円。フォームを送ったら、あとは決まるのを待つだけ。</p>
      <a class="btn center" href="/#form">ペットタクシーを予約する{ARROW}</a>
    </div>
  </div>
</section>
</main>
""" + foot("/#form")
    os.makedirs(os.path.join(ROOT, "guide", g["slug"]), exist_ok=True)
    open(os.path.join(ROOT, "guide", g["slug"], "index.html"), "w", encoding="utf-8").write(page)

hub_url = SITE + "/guide/"
hub_ld = '<script type="application/ld+json">\n' + json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"ペットタクシー予約窓口","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"ペットの移動ガイド","item":hub_url}]}, ensure_ascii=False, indent=1) + '\n</script>'
hub = head("ペットの移動ガイド｜犬・猫の通院、引っ越し、空港への移動とペットタクシー｜ペットタクシー予約窓口",
  "犬や猫と一緒に移動するときの悩みと、その解決のしかたをまとめたガイドです。動物病院への通院、猫のキャリーの慣らし方、シニア・介護中の子、大型犬、引っ越しや空港への送迎まで。", hub_url, hub_ld) + f"""
<main>
<section class="area-hero">
  <div class="wrap">
    <nav class="crumb" aria-label="パンくずリスト"><a href="/">ペットタクシー予約窓口</a> › ペットの移動ガイド</nav>
    <h1><small>犬・猫と、安心して出かけるために</small>ペットの移動ガイド</h1>
    <p class="lede">通院、引っ越し、帰省、お別れのとき。家族の一員だからこそ、移動もその子にとって楽な方法を選んであげたい。そのためのヒントをまとめました。</p>
  </div>
</section>
<section style="padding-top:8px">
  <div class="wrap">{guide_cards([g["slug"] for g in GUIDES])}</div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <div class="sh"><h2>エリアからさがす</h2></div>
    {area_links()}
  </div>
</section>
</main>
""" + foot("/#form")
open(os.path.join(ROOT, "guide", "index.html"), "w", encoding="utf-8").write(hub)

# 利用規約（/terms/）
from terms import TERMS, TERMS_DATE
def terms_block(v):
    if isinstance(v, tuple) and v[0] == "ul": return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in v[1]) + "</ul>"
    if isinstance(v, tuple) and v[0] == "html": return f"<p>{v[1]}</p>"
    return f"<p>{e(v)}</p>"
terms_url = SITE + "/terms/"
tp = head("利用規約｜ペットタクシー予約窓口", "ペットタクシー予約窓口（東京・神奈川・千葉・埼玉のペットタクシー手配）の利用規約です。サービスの内容、予約の成立、料金とお支払い、キャンセル、責任の範囲などを定めています。", terms_url, "") + f"""
<main>
<section class="area-hero"><div class="wrap"><h1>利用規約</h1><p class="lede">ペットタクシー予約窓口をご利用いただく前に、お読みください。</p></div></section>
<section><div class="wrap prose terms">
{''.join(f'<h2>{e(h)}</h2>' + ''.join(terms_block(v) for v in body) for h, body in TERMS)}
<p class="small">{TERMS_DATE} 制定</p>
</div></section>
</main>
""" + foot("/#form")
os.makedirs(os.path.join(ROOT, "terms"), exist_ok=True)
open(os.path.join(ROOT, "terms", "index.html"), "w", encoding="utf-8").write(tp)

# お問い合わせ（/contact/）。送り先はトップのフォームと同じ受付の仕組み（kind=contact）
gas = re.search(r'var GAS_URL = "([^"]+)"', open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()).group(1)
contact_url = SITE + "/contact/"
cp = head("お問い合わせ｜ペットタクシー予約窓口", "ペットタクシー予約窓口へのお問い合わせフォームです。ご予約やキャンセル、料金についてのご質問、ペットタクシー会社の方からの提携のご相談はこちらからどうぞ。", contact_url, "") + f"""
<main>
<section class="area-hero"><div class="wrap"><h1>お問い合わせ</h1><p class="lede">ご質問やご相談はこちらからどうぞ。お返事はメールでお送りします。</p></div></section>
<section><div class="wrap" style="max-width:640px">
<div class="form-card">
<form id="contactForm" novalidate>
  <div aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden"><label>空欄のままにしてください<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
  <div class="f"><label for="c_kind">お問い合わせの種類</label>
    <select id="c_kind" name="topic" required><option value="">選んでください</option><option>ご予約について</option><option>キャンセル・変更について</option><option>料金について</option><option>ペットタクシー会社の方（提携のご相談）</option><option>その他</option></select></div>
  <div class="f"><label for="c_name">お名前</label><input type="text" id="c_name" name="name" required autocomplete="name" placeholder="例：山田 花子"></div>
  <div class="f"><label for="c_email">メールアドレス</label><input type="email" id="c_email" name="email" required autocomplete="email" placeholder="例：hanako@example.com"></div>
  <div class="f"><label for="c_id">受付番号<span class="any">わかれば</span></label><input type="text" id="c_id" name="req_id" placeholder="例：PT00042" autocomplete="off"></div>
  <div class="f"><label for="c_msg">お問い合わせ内容</label><textarea id="c_msg" name="message" required rows="6" maxlength="2000"></textarea></div>
  <label class="agree"><input type="checkbox" id="c_agree" required><span><a href="/#privacy">個人情報の取り扱い</a>を確認し、同意します。</span></label>
  <p id="c_err" role="alert" style="display:none;color:#c0392b;font-size:.88rem"></p>
  <button class="btn" type="submit">送信する{ARROW}</button>
  <p class="form-foot">お返事まで数日いただくことがあります。急ぎのご予約の変更は、受付メールのリンクからどうぞ。</p>
</form>
<div id="c_done" style="display:none;text-align:center"><h2 style="font-size:1.2rem">お問い合わせを受け付けました</h2><p>内容を確認して、メールでお返事します。</p></div>
</div>
</div></section>
</main>
<script>
(function(){{
  var GAS_URL = "{gas}";
  var f = document.getElementById("contactForm"), err = document.getElementById("c_err");
  f.addEventListener("submit", function(e){{
    e.preventDefault(); err.style.display = "none";
    if (!f.checkValidity()) {{ var bad = f.querySelector(":invalid"); err.textContent = bad && bad.id === "c_agree" ? "確認のチェックを入れてください。" : "まだ入力されていない項目があります。"; err.style.display = "block"; if (bad) bad.focus(); return; }}
    var body = new URLSearchParams(new FormData(f)); body.append("kind", "contact");
    var btn = f.querySelector("button"); btn.disabled = true;
    fetch(GAS_URL, {{method: "POST", body: body}}).then(function(r){{ return r.json(); }}).then(function(r){{
      if (!r || !r.ok) throw 0;
      f.style.display = "none"; document.getElementById("c_done").style.display = "block";
    }}).catch(function(){{
      btn.disabled = false;
      err.textContent = "うまく送れませんでした。時間をおいてもう一度お試しください。ご予約中の方は、受付メールにご返信いただいてもかまいません。"; err.style.display = "block";
    }});
  }});
}})();
</script>
""" + foot("/#form")
os.makedirs(os.path.join(ROOT, "contact"), exist_ok=True)
open(os.path.join(ROOT, "contact", "index.html"), "w", encoding="utf-8").write(cp)

# 提携のご案内（/partner/）。受け口はお問い合わせと同じ（kind=contact, topic=提携のお申し込み）。項目は message にまとめて送る
partner_url = SITE + "/partner/"
PREFS4 = ["東京都", "神奈川県", "千葉県", "埼玉県"]
PAYS = ["現金", "クレジットカード", "電子マネー・QR決済", "請求書・振込"]
pp = head("ペットタクシー会社の方へ 提携のご案内｜ペットタクシー予約窓口", "東京・神奈川・千葉・埼玉のペットタクシー会社さま向けの提携のご案内です。飼い主さんからのご予約の依頼をメールでお届けします。お申し込みはこのページのフォームからどうぞ。", partner_url, "") + f"""
<main>
<section class="area-hero"><div class="wrap"><h1>ペットタクシー会社の方へ<br>提携のご案内</h1><p class="lede">ペットタクシー予約窓口は、ペットの移動に困っている飼い主さんと、近くのペットタクシー会社をおつなぎしています。東京・神奈川・千葉・埼玉で、いっしょにお迎えしてくださる会社を探しています。</p></div></section>
<section><div class="wrap" style="max-width:640px">
<h2 style="font-size:1.2rem">ご予約の依頼が届く流れ</h2>
<ol class="plist">
  <li>飼い主さんがこのサイトから予約を申し込むと、エリアと日時が合う会社さまへ、依頼のメールが届きます。</li>
  <li>受けられるときは、メールのリンクから確定の料金（一般道のとき・高速を使うとき）を入れて「引き受ける」を押してください。</li>
  <li>引き受けると、飼い主さんのお名前と連絡先が届きます。そのあとのやり取りとお支払いは、会社さまと飼い主さんで直接お願いします。</li>
  <li>受けられないときは、返信するか、そのままにしておいてください。</li>
</ol>
<p style="color:var(--ink-2);font-size:.92rem">お電話の対応はいりません。メールが受け取れれば大丈夫です。費用や細かい条件は、お申し込みのあとメールでご案内します。</p>
<h2 style="font-size:1.2rem;margin-top:36px">提携のお申し込み</h2>
<div class="form-card">
<form id="partnerForm" novalidate>
  <div aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden"><label>空欄のままにしてください<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
  <div class="f"><label for="p_co">会社名・屋号</label><input type="text" id="p_co" data-k="会社名・屋号" required autocomplete="organization"></div>
  <div class="f"><label for="p_name">ご担当者のお名前</label><input type="text" id="p_name" name="name" required autocomplete="name"></div>
  <div class="f"><label for="p_email">メールアドレス<span class="any">ご予約の依頼もここに届きます</span></label><input type="email" id="p_email" name="email" required autocomplete="email"></div>
  <div class="f"><span class="lbl">お迎えできる都県</span><div class="checks" id="p_prefs">{''.join(f'<label><input type="checkbox" value="{p}">{p}</label>' for p in PREFS4)}</div></div>
  <div class="f"><label for="p_city">お迎えできる市区町村など<span class="any">わかれば</span></label><input type="text" id="p_city" data-k="市区町村など" placeholder="例：世田谷区・目黒区・川崎市"></div>
  <div class="f"><label for="p_car">車の台数と種類</label><input type="text" id="p_car" data-k="車" required placeholder="例：2台（ワンボックス、軽バン）"></div>
  <div class="f"><label for="p_fare">料金</label><textarea id="p_fare" data-k="料金" required rows="4" placeholder="例：初乗り5kmまで2,200円、以降1kmごとに220円、深夜2割増。料金ページがあればURLだけでも大丈夫です。"></textarea></div>
  <div class="f"><label for="p_hours">受けられる曜日・時間帯</label><input type="text" id="p_hours" data-k="受けられる時間帯" required placeholder="例：毎日 8:00〜20:00"></div>
  <div class="f"><label for="p_emg">夜間や急ぎの依頼</label><select id="p_emg" data-k="夜間・急ぎ"><option>受けていない</option><option>夜間なら受けられる</option><option>急ぎ（当日すぐ）も受けられる</option><option>24時間受けられる</option></select></div>
  <div class="f"><span class="lbl">お支払い方法</span><div class="checks" id="p_pays">{''.join(f'<label><input type="checkbox" value="{p}">{p}</label>' for p in PAYS)}</div></div>
  <div class="f"><label for="p_reg">動物取扱業の登録番号<span class="any">わかれば</span></label><input type="text" id="p_reg" data-k="動物取扱業の登録番号" autocomplete="off"></div>
  <div class="f"><label for="p_url">ホームページ<span class="any">あれば</span></label><input type="url" id="p_url" data-k="ホームページ" placeholder="https://"></div>
  <div class="f"><label for="p_msg">ほかに伝えたいこと<span class="any">あれば</span></label><textarea id="p_msg" data-k="そのほか" rows="4" maxlength="1000"></textarea></div>
  <label class="agree"><input type="checkbox" id="p_agree" required><span><a href="/#privacy">個人情報の取り扱い</a>を確認し、同意します。</span></label>
  <p id="p_err" role="alert" style="display:none;color:#c0392b;font-size:.88rem"></p>
  <button class="btn" type="submit">申し込む{ARROW}</button>
  <p class="form-foot">内容を確認して、数日以内にメールでご連絡します。</p>
</form>
<div id="p_done" style="display:none;text-align:center"><h2 style="font-size:1.2rem">お申し込みを受け付けました</h2><p>内容を確認して、メールでご連絡します。ありがとうございます。</p></div>
</div>
</div></section>
</main>
<script>
(function(){{
  var GAS_URL = "{gas}";
  var f = document.getElementById("partnerForm"), err = document.getElementById("p_err");
  function picked(id){{ return [].map.call(document.querySelectorAll("#" + id + " input:checked"), function(x){{ return x.value; }}); }}
  f.addEventListener("submit", function(e){{
    e.preventDefault(); err.style.display = "none";
    var bad = f.querySelector(":invalid");
    if (!bad && !picked("p_prefs").length) bad = document.querySelector("#p_prefs input");
    if (bad) {{ err.textContent = bad.id === "p_agree" ? "確認のチェックを入れてください。" : bad.type === "checkbox" ? "お迎えできる都県を選んでください。" : bad.type === "url" && bad.value ? "ホームページはhttps://から入れてください。" : "まだ入力されていない項目があります。"; err.style.display = "block"; bad.focus(); return; }}
    var lines = [], co = "";
    f.querySelectorAll("[data-k]").forEach(function(x){{
      if (x.id === "p_co") co = x.value.trim();
      if (x.value.trim()) lines.push("【" + x.dataset.k + "】" + x.value.trim());
      if (x.id === "p_city") lines.splice(lines.length - (x.value.trim() ? 1 : 0), 0, "【都県】" + picked("p_prefs").join("・"));
      if (x.id === "p_emg") lines.push("【お支払い方法】" + (picked("p_pays").join("・") || "未選択"));
    }});
    var body = new URLSearchParams();
    body.append("kind", "contact"); body.append("topic", "提携のお申し込み（" + co + "）");
    body.append("name", document.getElementById("p_name").value.trim() + "（" + co + "）");
    body.append("email", document.getElementById("p_email").value.trim());
    body.append("message", lines.join("\\n"));
    body.append("website", f.website.value);
    var btn = f.querySelector("button"); btn.disabled = true;
    fetch(GAS_URL, {{method: "POST", body: body}}).then(function(r){{ return r.json(); }}).then(function(r){{
      if (!r || !r.ok) throw 0;
      f.style.display = "none"; document.getElementById("p_done").style.display = "block";
    }}).catch(function(){{
      btn.disabled = false;
      err.textContent = "うまく送れませんでした。時間をおいてもう一度お試しください。"; err.style.display = "block";
    }});
  }});
}})();
</script>
""" + foot("/#form", band=False)
os.makedirs(os.path.join(ROOT, "partner"), exist_ok=True)
open(os.path.join(ROOT, "partner", "index.html"), "w", encoding="utf-8").write(pp)

# sitemap / robots / 404
urls = [SITE + "/"] + [f'{SITE}/{a["slug"]}/' for a in AREAS] + [hub_url] + [f'{SITE}/guide/{g["slug"]}/' for g in GUIDES] + [terms_url, contact_url, partner_url]
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  "".join(f'  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls) + '</urlset>\n')
open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\nDisallow: /tools/\nDisallow: /booking/\nDisallow: /docs/\n\nSitemap: {SITE}/sitemap.xml\n")
nf = head("ページが見つかりません｜ペットタクシー予約窓口", "お探しのページは見つかりませんでした。", SITE + "/404.html", '<meta name="robots" content="noindex">') + f'''
<main><section class="area-hero"><div class="wrap" style="text-align:center">
<h1>ページが見つかりませんでした</h1><p class="lede">URLが変わったか、削除された可能性があります。</p>
<a class="btn center" href="/">トップページへ{ARROW}</a></div></section>
<section><div class="wrap"><div class="sh"><h2>エリアからさがす</h2></div>{area_links()}</div></section></main>
''' + foot("/#form")
open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(nf)
print("ok", len(AREAS), "areas")
