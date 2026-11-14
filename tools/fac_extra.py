# [B] SEO 2026-11-14（Nori「内容が薄いページを全面的に強化してほしい」「めちゃめちゃ濃くして」）：
# 施設1つずつのページ（ドッグラン・火葬・夜間の病院・犬と泊まれる宿・犬と入れるカフェ）に、
# すでに公式サイトで確かめてあるデータだけから作る節を足す。作り話・確かめていない数字は入れない。
#  1) その県の夜間・救急の動物病院（tools/emergency.json。火葬のページには出さない）
#  2) 行く前に確かめること（分野ごとのチェックリスト。事実ではなく確かめる項目の案内）
#  3) ペットタクシーの枠の中に、その県に来てくれる会社の料金表で計算した運賃の目安（概算・確定料金ではありません）
import os, re, json, html

CATS = {
    "dogrun": dict(hosp=True, check=[
        "その日に開いているか（雨・強風・芝の手入れ・イベントで閉まることがあります）",
        "利用登録がいるか、いるなら当日その場でできるか（郵送で何日もかかるところもあります）",
        "ワクチンの証明は原本か、写しや写真でもよいか",
        "犬の大きさでエリアが分かれているか（体重か体高か）",
        "1人で何頭まで連れて入れるか、おもちゃや食べ物を持ちこめるか",
        "駐車場からドッグランまでの道のり（歩いて何分か、坂があるか）",
        "水飲み場・足洗い場・日かげがあるか（夏は水を多めに）",
        "フンを入れる袋・水・タオル・リード（外ではずっと付けるので長すぎないもの）"]),
    "inu-cafe": dict(hosp=True, check=[
        "犬が入れるのは店内か、テラス席だけか",
        "大きな犬も入れるか、何頭まで入れるか",
        "椅子や床に下ろしてよいか（キャリーやカートの中だけのお店もあります）",
        "マナーベルトやマナーパンツがいるか、ワクチンの証明を見せるか",
        "犬用のメニューや水の器があるか",
        "混む時間（週末の昼どき）と予約ができるか",
        "駐車場があるか、お店の前で乗り降りできるか"]),
    "inu-yado": dict(hosp=True, check=[
        "犬が入れるのは部屋だけか、食事どころや館内もいっしょに歩けるか",
        "大きさ・頭数・犬種の決まりと、犬の宿泊料金",
        "ワクチンの証明や、ノミ・ダニの予防の証明がいるか",
        "部屋のベッドやソファに上げてよいか、持っていくもの（ケージ・敷物・トイレシート）",
        "犬だけを部屋に残して出かけてよいか",
        "近くの動物病院（下の夜間・救急の病院も見ておくと安心です）",
        "チェックイン・アウトの時刻と、駐車場から部屋までの道のり"]),
    "sougi": dict(hosp=False, check=[
        "火葬のしかた（ほかの子といっしょ・個別・立ち会い）と、お骨を返してもらえるか",
        "料金が体重で決まるか、何kgごとに変わるか、ほかにかかる費用（骨つぼ・お迎えなど）",
        "お迎えに来てもらえるか、こちらから連れて行くか",
        "予約がいるか、いつまで受け付けているか（その日や夜でもよいか）",
        "納骨・霊園・合同のお墓があるか、そのときの費用",
        "市区町村の受付（自治体の火葬・引き取り）とどちらにするか",
        "ご遺体を安置するあいだの保冷（保冷剤やタオルでおなかと頭を冷やす）"]),
    "hospital": dict(hosp=True, check=[
        "行く前に電話で、受け付けている時間と、いまの症状で診てもらえるかを確かめる",
        "診察の料金の目安（夜間・休日は料金が上がることが多い）と、払い方",
        "ふだんの病院の名前、飲んでいる薬、ワクチンの記録、症状が始まった時刻のメモ",
        "吐いたもの・便などを持っていくとよいか",
        "車で行けるか、駐車場があるか。抱っこでの移動ならキャリーやバスタオル",
        "帰りの足（夜中に終わることがあります）"]),
}
ROOT_ = "."


def _prefs_from_dogrun():
    import gen_dogrun as G
    return {v: k for k, v in G.PSLUG.items()}  # slug -> 県名


def build(ROOT, EMG, pref_fare, night_href=None):
    """pref_fare(県名) -> [(km, '6,600円（3,000〜11,800円）', 根拠)] ／ night_href(県名, 病院id) -> その病院の施設ページのURLか None"""
    global ROOT_
    ROOT_ = ROOT
    S2P = _prefs_from_dogrun()
    e = html.escape
    n = 0
    for cat in CATS:
        base = os.path.join(ROOT, *(["hospital", "night"] if cat == "hospital" else [cat]))
        if not os.path.isdir(base): continue
        for ps in os.listdir(base):
            pf = S2P.get(ps)
            if not pf: continue
            for fid in os.listdir(os.path.join(base, ps)):
                f = os.path.join(base, ps, fid, "index.html")
                if not os.path.isfile(f): continue
                h = open(f, encoding="utf-8").read()
                if "data-fac-extra" in h or "<main" not in h: continue
                h2 = _inject(h, cat, pf, fid, EMG, pref_fare, night_href, e)
                if h2 != h:
                    open(f, "w", encoding="utf-8").write(h2); n += 1
    return n


def _inject(h, cat, pf, fid, EMG, pref_fare, night_href, e):
    C = CATS[cat]
    blocks = []
    if C["hosp"] and not (cat == "hospital" and "ほかの夜間・救急の動物病院とくらべる" in h):
        hs = [x for x in EMG["hospitals"].get(pf, []) if (x.get("id") or "").lower() != fid.lower()]
        if hs:
            li = ""
            for x in hs[:6]:
                u = None
                if x.get("id") and os.path.isfile(os.path.join(ROOT_, "hospital", "night", _slug(pf), x["id"].lower(), "index.html")):
                    u = f"/hospital/night/{_slug(pf)}/{x['id'].lower()}/"
                nm = f'<a href="{e(u)}">{e(x["name"])}</a>' if u else f'<a href="{e(x["url"])}" target="_blank" rel="noopener">{e(x["name"])} ↗</a>'
                meta = "・".join(v for v in (x.get("city", ""), x.get("hours", "")) if v)
                li += f"<li>{nm}{('（' + e(meta) + '）') if meta else ''}</li>"
            ttl = (f"{pf}のほかの夜間・救急の動物病院" if cat == "hospital" else f"ケガや急な体調の変化のときに：{pf}の夜間・救急の動物病院")
            blocks.append(f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">{e(ttl)}</h2><ul class="other">{li}</ul>'
                          f'<p class="emg-tips-note">各病院の公式サイトで確かめた名前と受付の時間です（変わることがあります）。行く前に必ず電話で受け付けているか確かめてください。'
                          f'<a href="/hospital/night/{e(_slug(pf))}/">{e(pf)}の夜間・救急の動物病院をすべて見る</a></p></div>')
    chk = "".join(f"<li>{e(x)}</li>" for x in C["check"])
    blocks.append(f'<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">行く前に確かめること</h2><ul class="fac-pts">{chk}</ul>'
                  '<p class="emg-tips-note">上の表に書いていないことは、公式サイトに書いていないことです。行く前に施設に確かめてください。</p></div>')
    add = "".join(blocks)
    m = re.search(r'<div class="emg-tips"><h2[^>]*>関連するページ</h2>', h)
    if m: h = h[:m.start()] + add + h[m.start():]
    else: h = h.replace("</main>", f'<section><div class="wrap"><div class="emg">{add}</div></div></section></main>', 1)
    # ペットタクシーの枠（下）に運賃の目安を足す
    rows = pref_fare(pf)
    if rows:
        tr = "".join(f"<tr><td>{km}km</td><td>{v}</td></tr>" for km, v, _ in rows)
        basis = rows[0][2]
        fare = (f'<div data-fac-extra="1" style="max-width:520px;margin:10px auto 0"><table class="pp-tbl"><thead><tr><th>乗る距離（片道）</th><th>運賃の目安（まんなか・安い〜高い）</th></tr></thead><tbody>{tr}</tbody></table>'
                f'<p class="emg-tips-note">{e(basis)}の公式サイトの料金表をもとに計算した、乗った距離の運賃の概算です。確定料金ではありません。お迎え料金・夜間の割増・待ち時間・高速代は入っておらず、当日の道順・渋滞などで変わります。</p></div>')
        mm = list(re.finditer(r'<div class="sh"><h2>[^<]*ペットタクシーで</h2>.*?</div>', h, re.S))
        if mm:
            x = mm[-1]; h = h[:x.end()] + fare + h[x.end():]
    if "data-fac-extra" not in h:
        h = h.replace('<div class="emg-tips"><h2 style="font-size:1.05em;margin:0 0 6px">行く前に確かめること', '<div class="emg-tips" data-fac-extra="1"><h2 style="font-size:1.05em;margin:0 0 6px">行く前に確かめること', 1)
    return h


def _slug(pf):
    import gen_dogrun as G
    return G.PSLUG[pf]
