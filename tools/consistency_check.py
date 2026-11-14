#!/usr/bin/env python3
"""[D] サイト・データ・提携先の食い違いの自動点検（Nori 2026-11-14「こんごこのようなことがないようにたいさくしてください」）。

2026-11-14 の全体点検で見つかった食い違いが、もう一度起きたら止める。PRごとに .github/workflows/seo-check.yml で動く。
何も送らない・何も書き換えない。NG が1件でもあれば終了コード1。

  python3 tools/consistency_check.py .

見ること：
 1. 受付中の提携先（booking/Code.gs の OPEN_PARTNERS）が、候補カードのデータ（display_companies.json）にあり、
    料金表に税込・税別が入っていて（料金表があるとき）、お店の場所があり、
    運送の届出（黒ナンバー・緑ナンバー）が licenses.json に入っている（白ナンバーとは提携しない。Nori 2026-11-12）
 2. 申し込みで答えてもらったお迎えの範囲（display_companies.py の PROVIDER の radius_km）と、お迎えの都道府県（areas）が合っている
    （お店の県でもなく、県庁所在地がお店から 範囲＋60km より遠い県は届かない県として NG。PROVIDER の areas_ok に入れた県は、Nori さんの判断待ちなどで見送る）
 3. ページの「全国◯社」「◯社のうち」の社数が、いまのデータの数とずれていない（手で書いた社数が古くなるのを止める）
 4. 迎えに行ける会社が1社もない県（トップの選択欄から消える県）の県ページに、「上のフォームでさがせます」と書いていない
 5. 提携先の候補カード（CO_SITE・CREDS）に、受付中の提携先の届出が入っている
"""
import json, math, os, re, sys, html

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
T = os.path.join(ROOT, "tools")
sys.path.insert(0, T)
NG, WARN = [], []

def load(p): return json.load(open(os.path.join(T, p), encoding="utf-8"))
D = load("display_companies.json")["companies"]
DI = {c["id"]: c for c in D}
LIC = load("licenses.json")["companies"]
gs = open(os.path.join(ROOT, "booking", "Code.gs"), encoding="utf-8").read()
m = re.search(r"OPEN_PARTNERS:\s*\{([^}]*)\}", gs)
OPEN = dict(re.findall(r"'([^']+)'\s*:\s*'([^']+)'", m.group(1))) if m else {}
import display_companies as DC
PROVIDER = getattr(DC, "PROVIDER", {})

# 県庁所在地（だいたいの位置）
from prefs import PREFS
if True:
    CAP = {"北海道": (43.06, 141.35), "青森": (40.82, 140.74), "岩手": (39.70, 141.15), "宮城": (38.27, 140.87), "秋田": (39.72, 140.10), "山形": (38.24, 140.36),
           "福島": (37.75, 140.47), "茨城": (36.34, 140.45), "栃木": (36.57, 139.88), "群馬": (36.39, 139.06), "埼玉": (35.86, 139.65), "千葉": (35.61, 140.12),
           "東京": (35.69, 139.69), "神奈川": (35.45, 139.64), "新潟": (37.90, 139.02), "富山": (36.70, 137.21), "石川": (36.59, 136.63), "福井": (36.07, 136.22),
           "山梨": (35.66, 138.57), "長野": (36.65, 138.18), "岐阜": (35.39, 136.72), "静岡": (34.98, 138.38), "愛知": (35.18, 136.91), "三重": (34.73, 136.51),
           "滋賀": (35.00, 135.87), "京都": (35.02, 135.76), "大阪": (34.69, 135.52), "兵庫": (34.69, 135.18), "奈良": (34.69, 135.83), "和歌山": (34.23, 135.17),
           "鳥取": (35.50, 134.24), "島根": (35.47, 133.05), "岡山": (34.66, 133.93), "広島": (34.40, 132.46), "山口": (34.19, 131.47), "徳島": (34.07, 134.56),
           "香川": (34.34, 134.04), "愛媛": (33.84, 132.77), "高知": (33.56, 133.53), "福岡": (33.61, 130.42), "佐賀": (33.25, 130.30), "長崎": (32.74, 129.87),
           "熊本": (32.79, 130.74), "大分": (33.24, 131.61), "宮崎": (31.91, 131.42), "鹿児島": (31.56, 130.56), "沖縄": (26.21, 127.68)}

def km(a, b):
    r = math.pi / 180
    x = (b[1] - a[1]) * r * math.cos((a[0] + b[0]) / 2 * r); y = (b[0] - a[0]) * r
    return math.hypot(x, y) * 6371
def short(p): return p if p == "北海道" else p[:-1]

# 1. 受付中の提携先
for pid, did in OPEN.items():
    c = DI.get(did)
    if not c: NG.append(f"受付中の提携先 {pid}（{did}）が display_companies.json にない"); continue
    nm = c["name"]
    if c.get("fare") and not re.search("税込|税抜|税別", c["fare"].get("tax") or ""):
        NG.append(f"{nm}：料金表に税込・税別が入っていない（申し込みで料金の入力をとばした会社は、税を確かめてから REPLY_FIX に入れる）")
    if not c.get("shop"): NG.append(f"{nm}：お店の場所（SHOP）がない。お迎えの範囲で候補をしぼれない")
    t = (LIC.get(did) or {}).get("transport")
    if t not in ("黒ナンバー", "緑ナンバー", "届出"):
        NG.append(f"{nm}：運送の届出（黒ナンバー・緑ナンバー）が licenses.json にない。申し込みの答えか公式サイトで確かめて入れる（白ナンバーとは提携しない）")

# 2. お迎えの範囲と都道府県
for did, pv in PROVIDER.items():
    r = pv.get("radius_km"); c = DI.get(did)
    if not r or not c or not c.get("shop"): continue
    home = short(c["pref"])
    for a in c["areas"]:
        if a == home or a in pv.get("areas_ok", []) or a not in CAP: continue
        d = km(c["shop"], CAP[a])
        if d > r + 60:
            NG.append(f"{c['name']}：お迎えは{r}kmまでなのに、お迎えの都道府県に{a}が入っている（県庁まで{d:.0f}km）。届かない県は外すか、Noriさんに確かめて areas_ok に入れる")
for pid, did in OPEN.items():
    if did in DI and not (PROVIDER.get(did) or {}).get("radius_km"):
        WARN.append(f"{DI[did]['name']}：申し込みのお迎えの範囲（km）が PROVIDER の radius_km に入っていない")

# 3. 手で書いた社数（ガイドの元の .py で、データから数えずに書いた「全国◯社」「◯社のうち」。日付つきの「◯月◯日時点」のしらべは除く）
import glob
for p in sorted(glob.glob(os.path.join(T, "guides*.py")) + [os.path.join(T, "facility_guides.py"), os.path.join(T, "gen_areas.py")]):
    for i, l in enumerate(open(p, encoding="utf-8"), 1):
        for mm in re.finditer(r"(?<![{\w])(?:全国の?(?:ペットタクシー)?(?:会社)?\d+社|\d+社(?:のうち|中))", l):
            seg = l[max(0, mm.start() - 80):mm.end() + 80]
            if "# 決まった日のしらべ" in l: continue  # 行の終わりにこの印がある行は、日付つきのしらべの数
            if re.search(r"時点|\d+年\d+月|\d+月\d+日|くらべた|例", seg): continue  # 日付つきのしらべ・100の例のしらべ
            NG.append(f"{os.path.relpath(p, ROOT)}:{i}：「{mm.group(0)}」を手で書いている。会社を足すとずれるので、guides_fare_survey.py・guides_counts.py の数に置きかえる（決まった日のしらべなら「◯月◯日時点」と書く）")

# 4. 迎えに行ける会社がない県のページ
local = {a for c in D for a in c.get("areas", [])} | {"東京", "神奈川", "埼玉", "千葉"}
far = {a for c in D for a in c.get("far", [])}
for slug, name, *_ in PREFS:
    k = short(name)
    if k in local or k in far: continue
    p = os.path.join(ROOT, "area", slug, "index.html")
    if os.path.exists(p) and "からのお迎えも、上のフォームでさがせます" in open(p, encoding="utf-8").read():
        NG.append(f"/area/{slug}/：迎えに行ける会社がない県なのに「上のフォームでさがせます」と書いている")

# 5. 公開するページに届出が入っているか
top = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
mc = re.search(r"/\*CREDS\*/var CREDS = (\{.*?\});/\*/CREDS\*/", top, re.S)
creds = json.loads(mc.group(1)) if mc else {}
for pid, did in OPEN.items():
    if did in LIC and LIC[did].get("transport") and not (creds.get(pid) or {}).get("transport"):
        NG.append(f"{pid}：licenses.json に届出があるのに、トップの CREDS に入っていない（gen_areas.py を実行していない）")

for w in WARN: print("注意：" + w)
for n in NG: print("NG：" + n)
print(f"食い違いの点検：NG {len(NG)}件・注意 {len(WARN)}件（受付中の提携先 {len(OPEN)}社）")
sys.exit(1 if NG else 0)
