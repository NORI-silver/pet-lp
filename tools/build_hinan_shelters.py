"""[B] Nori 2026-11-16「具体的な避難場所の情報ないし」：全国の指定避難所を市区町村ごとの小さなJSONにする。
元は国土地理院「指定緊急避難場所・指定避難所データ」（https://www.gsi.go.jp/bousaichiri/hinanbasho.html）。
団体コードごとに分けた写し（github.com/motohasystem/jp-shelter-api、MIT）の docs/api/v0/evacuation を読む。
使い方：python3 tools/build_hinan_shelters.py <jp-shelter-api のフォルダ> .
出力：hinan/s/<団体コード>.json ＝ [[名前, 住所（県・市区町村を除く）, 緯度, 経度, 区, ペットの書きこみ], ...]
ペットの受け入れは、元のデータの「受入対象者」「備考」に「ペット」とあるときだけ（ほかは市区町村の決まりを見る）。電話番号は元のデータにない。
"""
import json, glob, os, re, sys, collections, unicodedata
N = lambda x: unicodedata.normalize("NFKC", x or "").replace("\u2212", "-")

FIX = {"梼原町": "檮原町"}

def main(src, root):
    M = json.load(open(os.path.join(root, "tools", "municipalities.json"), encoding="utf-8"))
    byp = collections.defaultdict(list)
    for m in M: byp[m["pref"]].append(m)
    out, seen = collections.defaultdict(list), set()
    for f in sorted(glob.glob(os.path.join(src, "docs", "api", "v0", "evacuation", "*.json"))):
        for ft in json.load(open(f, encoding="utf-8")).get("features", []):
            p = ft["properties"]; s = p["都道府県名及び市町村名"]
            for a, b in FIX.items(): s = s.replace(a, b)
            pf = next((x for x in byp if s.startswith(x)), None)
            if not pf: continue
            rest = s[len(pf):]
            cands = [m for m in byp[pf] if rest.startswith(m["name"])]
            if not cands: continue
            m = max(cands, key=lambda m: len(m["name"]))
            key = (m["code"], p.get("共通ID") or (p["施設・場所名"], p["住所"]))
            if key in seen: continue
            seen.add(key)
            lng, lat = ft["geometry"]["coordinates"][:2]
            addr = N(p["住所"]).strip()
            for a, b in FIX.items(): addr = addr.replace(a, b)
            for pre in (pf + m["name"], m["name"], pf):
                if addr.startswith(pre): addr = addr[len(pre):]; break
            note = " ".join(x for x in [p.get("受入対象者") or "", p.get("備考") or ""] if x).strip()
            pet = note[:60] if "ペット" in note else ""
            out[m["code"]].append([N(p["施設・場所名"]).strip(), addr, round(lat, 5), round(lng, 5), rest[len(m["name"]):], pet])
    merge_sites(root, M, out)
    d = os.path.join(root, "hinan", "s"); os.makedirs(d, exist_ok=True)
    for c, v in out.items():
        open(os.path.join(d, c + ".json"), "w", encoding="utf-8").write(json.dumps(v, ensure_ascii=False, separators=(",", ":")))
    print(len(out), "市区町村", sum(map(len, out.values())), "か所")

def _key(n, muni, pf):
    n = N(n).replace(" ", "").replace("　", "")
    for pre in (muni + "立", muni, pf + "立", pf, "市立", "町立", "村立", "区立"):
        if n.startswith(pre): n = n[len(pre):]
    return re.sub(r"[（(].*?[）)]", "", n).replace("高等学校", "高校")

def merge_sites(root, M, out):
    """tools/hinan_sites.json（市区町村が公開している、避難所ごとのペットの居場所）を、避難所のカードの🐾の行に入れる"""
    f = os.path.join(root, "tools", "hinan_sites.json")
    if not os.path.exists(f): return
    code = {(m["pref"], m["name"]): m["code"] for m in M}
    for k, v in json.load(open(f, encoding="utf-8")).items():
        pf, nm = k.split("|"); c = code.get((pf, nm))
        if not c or c not in out: continue
        idx = {_key(n, nm, pf): pl for n, pl in v["sites"].items()}
        hit = 0
        for r in out[c]:
            pl = idx.get(_key(r[0], nm, pf))
            if not pl: continue
            hit += 1
            a, b = (pl + [pl[0]])[:2] if isinstance(pl, list) else (pl, pl)
            r[5] = ("ペットの場所：" + a) if (a == b or not v.get("cols")) else f"ペットの場所：{v['cols'][0]}は{a}／{v['cols'][1]}は{b}"
        out[c].sort(key=lambda r: not r[5])  # ペットの場所が分かる避難所を先に
        print(nm, "避難所ごとのペットの場所", hit, "/", len(v["sites"]))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".")
