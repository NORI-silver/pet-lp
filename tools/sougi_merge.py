# 民間のペット火葬・霊園の追加分（/mnt/project-files/sougi-coverage/add-*.json）を tools/sougi_facilities.json に入れる。
# 使い方：python3 tools/sougi_merge.py <add-*.json ...>
# 決まり：公式サイトで確かめた名前・市区町村・できること・料金だけ。電話番号・番地は入れない。同じ公式サイト・同じ名前は足さない。
import hashlib, json, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
P = ROOT / "sougi_facilities.json"
KINDS = {"火葬", "霊園", "納骨堂"}
SERVICES = {"合同火葬", "個別火葬", "立ち会い火葬", "お迎え", "訪問火葬", "納骨"}
PREFS = None
BAN = re.compile(r"\d{2,4}-\d{2,4}-\d{3,4}|0120|手配|取り次|代理|公式サイトで確かめ|くらい|約\d|まで\s*$")

def norm(s):
    return re.sub(r"[\s・（）()【】「」]", "", s or "")

def host(u):
    m = re.match(r"https?://([^/]+)(/[^?#]*)?", u or "")
    return (m.group(1).lower().removeprefix("www."), (m.group(2) or "/").rstrip("/")) if m else ("", "")

def main(paths):
    D = json.loads(P.read_text())
    F = D["facilities"]
    names = {(f["pref"], norm(f["name"])) for f in F}
    urls = {host(f["u"]) for f in F}
    sites = {(f["pref"], f["city"], host(f["u"])[0]) for f in F}
    added, skipped = 0, []
    for p in paths:
        for f in json.loads(pathlib.Path(p).read_text()):
            why = []
            for k in ("pref", "name", "city", "kinds", "services", "u"):
                if not f.get(k): why.append("no " + k)
            if set(f.get("kinds", [])) - KINDS: why.append("kinds")
            if set(f.get("services", [])) - SERVICES: why.append("services")
            if f.get("price") and BAN.search(f["price"]): why.append("price words")
            if re.search(r"\d+[-－]\d+", f.get("city", "")): why.append("番地")
            if (f.get("pref"), norm(f.get("name"))) in names: why.append("same name")
            if host(f.get("u")) in urls: why.append("same url")
            if (f.get("pref"), f.get("city"), host(f.get("u"))[0]) in sites: why.append("same site and city")
            if why:
                skipped.append((f.get("pref"), f.get("name"), why)); continue
            rec = {k: f[k] for k in ("pref", "name", "city", "kinds", "services")}
            rec["price"] = f.get("price") or None
            rec["u"] = f["u"]
            rec["id"] = "S" + hashlib.md5((f["pref"] + f["name"]).encode()).hexdigest()[:6]
            rec["review_query"] = f"{f['name']} {f['city']}"
            rec["review_name"] = f.get("review_name") or f["name"]
            if f.get("checked"): rec["checked"] = f["checked"]
            F.append(rec); names.add((rec["pref"], norm(rec["name"]))); urls.add(host(rec["u"])); sites.add((rec["pref"], rec["city"], host(rec["u"])[0])); added += 1
    P.write_text(json.dumps(D, ensure_ascii=False, indent=1) + "\n")
    print("added", added, "total", len(F))
    for s in skipped: print("skip", *s)

if __name__ == "__main__":
    main(sys.argv[1:])
