# AIエージェント向けの入口（WebMCP と llms.txt）のデータを作る。gen_areas.py の最後に呼ばれる。
# Nori 2026-11-02「Web MCPにも対応できる？」。
# - /webmcp/data.json：サイトに載せている一覧（名前・市区町村・公式サイト・このサイトのページ）だけを短くまとめたもの。
#   電話番号・口コミ・順位は入れない。webmcp.js（ブラウザのAIエージェント用の道具）が読む。
# - 道具はすべて「見るだけ」。会社への問い合わせ・送信はしない（送信の再開は Nori さんの「再開して」まで）。
import json, os, re

SITE = "https://pet.shiokonbu.com"

# (カテゴリのID, 日本語の名前, このサイトのページ)
CATS = [
    ("night_vet", "夜間・救急の動物病院", "/emergency/"),
    ("emergency_transport", "緊急の搬送をしているペットタクシー会社", "/emergency/"),
    ("home_visit_vet", "往診の動物病院", "/hospital/visit/"),
    ("cat_vet", "猫の専門病院", "/hospital/cat/"),
    ("exotic_vet", "エキゾチックアニマルの専門病院", "/hospital/exotic/"),
    ("large_facility_vet", "大型犬の設備がある動物病院", "/hospital/large/"),
    ("dog_run", "ドッグラン", "/dogrun/"),
    ("senior_dog_home", "老犬ホーム・老猫ホーム", "/rojin-home/"),
    ("pet_sitter", "ペットシッター", "/pet-sitter/"),
    ("dog_trainer", "ドッグトレーナー・しつけ教室", "/dog-trainer/"),
    ("pet_hotel", "ペットホテル（大型犬OK・猫専用）", "/pet-hotel/"),
    ("mobile_grooming", "出張トリミング", "/trimming/"),
    ("pet_funeral", "ペット火葬・霊園・納骨堂（民間）", "/sougi/"),
    ("city_animal_office", "自治体の動物愛護センター・保健所（迷子・登録・引取り）", "/jichitai/"),
]

def _j(root, name):
    with open(os.path.join(root, "tools", name), encoding="utf-8") as f:
        return json.load(f)

def _row(pref, x, note=""):
    r = {"pref": pref, "name": x["name"]}
    if x.get("city"): r["city"] = x["city"]
    if x.get("area"): r["area"] = x["area"]
    if note: r["note"] = note
    r["url"] = x.get("url") or x.get("u")
    return r

def _multi(items, note_keys=()):
    out = []
    for x in items:
        note = "・".join(str(x[k]) for k in note_keys if isinstance(x.get(k), str) and x.get(k))
        for pf in x.get("prefs") or [x.get("pref")]:
            if pf: out.append(_row(pf, x, note))
    return out

def pref_pages():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from prefs import PREFS
    m = {x[1]: f"/area/{x[0]}/" for x in PREFS}
    m.update({"東京都": "/tokyo/", "神奈川県": "/kanagawa/", "埼玉県": "/saitama/", "千葉県": "/chiba/"})
    assert len(m) == 47
    return m

def build(root):
    emg = _j(root, "emergency.json"); hos = _j(root, "hospitals.json")
    data = {}
    data["night_vet"] = [_row(pf, x, x.get("hours", "")) for pf, xs in emg["hospitals"].items() for x in xs]
    taxis = emg["taxis"]
    taxis = [x for xs in taxis.values() for x in xs] if isinstance(taxis, dict) else taxis
    data["emergency_transport"] = _multi(taxis, ("note",))
    data["home_visit_vet"] = _multi(hos["visit"], ("animals", "hours"))
    data["cat_vet"] = _multi(hos["cat"], ("spec",))
    data["exotic_vet"] = _multi(hos["exotic"], ("animals", "spec"))
    data["large_facility_vet"] = _multi(hos["large"], ("spec",))
    data["dog_run"] = _multi(_j(root, "dogrun.json")["dogruns"], ("kind", "hours", "fee"))
    import gen_dogrun_fac  # 施設ページがある施設は page を足す
    for r in data["dog_run"]:
        x = next((d for d in gen_dogrun_fac.PAGES if d["url"] == r.get("url") and d["name"] == r.get("name")), None)
        if x: r["page"] = SITE + gen_dogrun_fac.href(x)
    data["senior_dog_home"] = _multi(_j(root, "rojin.json")["homes"], ("animals",))
    data["pet_sitter"] = _multi(_j(root, "sitters.json")["sitters"])
    data["dog_trainer"] = _multi(_j(root, "trainers.json")["trainers"], ("services",))
    data["pet_hotel"] = _multi(_j(root, "hotels.json")["hotels"], ("services",))
    data["mobile_grooming"] = _multi(_j(root, "grooming.json")["groomers"], ("services",))
    sf = _j(root, "sougi_facilities.json")["facilities"]
    data["pet_funeral"] = [_row(x["pref"], x, "・".join(x.get("kinds", [])) + (("／" + x["price"]) if x.get("price") else "")) for x in sf]
    import gen_sougi_fac  # 施設ページがある施設は page を足す（docs/facility-page.md）
    for x, r in zip(sf, data["pet_funeral"]):
        if x["id"] in gen_sougi_fac.IDS: r["page"] = SITE + gen_sougi_fac.href(x)
    jc = _j(root, "jichitai.json")
    data["city_animal_office"] = [_row(x["pref"], x) for x in jc["prefs"]] + [_row(x["pref"], x) for x in jc["cities"]]
    for k, v in data.items():
        for r in v:
            assert r["url"], (k, r)
    out = {
        "site": "ペットタクシー予約窓口",
        "note": "公式サイトで確かめたことだけを載せた一覧です。順位はつけていません。最新の内容は各公式サイトでご確認ください。",
        "categories": [{"id": c, "label": l, "page": p, "count": len(data[c])} for c, l, p in CATS],
        "pref_pages": pref_pages(),
        "items": data,
    }
    d = os.path.join(root, "webmcp"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "data.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(root, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(llms(out))
    return out

def llms(out):
    L = ["# ペットタクシー予約窓口", "",
         "> 全国のペットタクシー会社をさがして、公式サイトの料金表から計算した料金の目安をくらべ、空き状況と料金を無料で問い合わせられるサイトです。"
         "あわせて、夜間・救急の動物病院や、ドッグラン・老犬ホーム・ペットシッターなど、ペットとのくらしに役立つ全国の一覧を載せています。", "",
         "- 料金は各社の公式サイトの料金表をもとに計算した概算で、確定料金ではありません。当日の道順・渋滞・待ち時間などで変わります。",
         "- 一覧は公式サイトで確かめたことだけを載せています。順位はつけていません。",
         "- ブラウザのAIエージェント向けに、見るだけの道具（WebMCP）を用意しています。一覧のデータは /webmcp/data.json です。", "",
         "## 料金をくらべる", "",
         f"- [料金をくらべる・問い合わせる（無料）]({SITE}/#form): お迎えの場所・行き先・日時・ペットの情報を入れると、条件に合う会社と料金の目安が出ます",
         f"- [全国の都道府県のページ]({SITE}/area/)",
         f"- [ガイド]({SITE}/guide/): ペットタクシーの使い方・料金・ふつうのタクシーに犬は乗れるか など", "",
         "## 独自のしらべ（引用してよいデータ。出どころの記載をお願いします）", "",
         f"- [全国のペットタクシー料金しらべ]({SITE}/guide/pet-taxi-fare-survey/): 全国のペットタクシー会社の公式の料金表を同じ式で計算した、距離ごと・都道府県ごとの運賃、お迎え料金・夜間割増・待ち時間の数",
         f"- [全国のドッグランしらべ]({SITE}/dogrun/survey/): 公式ページで確かめた全国のドッグランの料金・利用登録・ワクチンの条件・小型犬エリアを、公営・お店や施設・高速道路のSA・PAごとに数えたもの", "",
         "## ペットとのくらしの一覧", ""]
    for c in out["categories"]:
        L.append(f"- [{c['label']}]({SITE}{c['page']}): {c['count']}件。URL の最後に #pref=東京都 のように付けると、その都道府県でしぼれます")
    # [B] AI検索（ChatGPT・Perplexity・AI による概要など）が答えに引用しやすいように、ガイドを1行の要約つきで並べる（2026-11-08）。
    # 要約は各ガイドの説明文（ページの description と同じ）なので、ページと内容がずれない。
    from guides import GUIDES
    for cat, head in ((None, "ガイド：ペットタクシーの料金・選び方・使い方（当サイトで各社の公式サイトを数えたデータつき）"),
                      ("facility", "ガイド：専門の動物病院・夜間救急へ犬・猫と行くには"),
                      ("procedure", "ガイド：迷子・登録・引っ越し・亡くなったときの手続き"),
                      ("care", "ガイド：老犬ホーム・ペットシッター・ペットホテル・しつけ"),
                      ("money", "ガイド：病院代とペット保険（保険会社の公式の診療費の例と保険料表で計算）")):
        gs = [g for g in GUIDES if g.get("category") == cat]
        if not gs:
            continue
        L += ["", f"## {head}", ""]
        for g in gs:
            d = re.sub(r"\s+", " ", g["desc"]).strip()
            L.append(f"- [{g['title']}]({SITE}/guide/{g['slug']}/): {d}（更新 {g.get('modified', '')}）".replace("（更新 ）", ""))
    L += ["", "## そのほか", "",
          f"- [利用規約]({SITE}/terms/)", f"- [お問い合わせ]({SITE}/contact/)", f"- [サイトマップ]({SITE}/sitemap.xml)", ""]
    return "\n".join(L)

if __name__ == "__main__":
    import sys
    o = build(sys.argv[1] if len(sys.argv) > 1 else ".")
    print({c["id"]: c["count"] for c in o["categories"]})
