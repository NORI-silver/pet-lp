#!/usr/bin/env python3
"""[C] 写真の候補（ブランチ photo-cand。tools/photo_harvest.py が作る）から、採る写真を img/fac/ と tools/photos.json に入れる。

使い方：python3 tools/photo_import.py <photo-cand を置いたフォルダ> [--drop 分野:id_番号 ...] [--keep 分野:id_番号 ...] [--only 分野:id ...]
- 人の顔・人の印（flag）の付いた写真は入れない。一覧で人が写っていないと確かめた写真だけ --keep で入れる。
- permit（事業者の許可）と ok（サイトの決まりで転載可）の写真を入れる。check・no・none は入れない。
- 一覧（sheet_*.jpg）を見て、施設と関係ない写真（ロゴ・文字だけ・別の場所）は --drop で外す。
- 同じ事業者の前の写真（by が permit / license のもの）は置きかえる。owner（事業者が登録した写真）には触らない。
"""
import json, os, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    a = sys.argv[1:]
    src = a.pop(0)
    S = {"--drop": set(), "--keep": set(), "--only": set()}
    mode = None
    for x in a:
        if x in S: mode = x; continue
        S[mode].add(x)
    drop, keep_flag, only = S["--drop"], S["--keep"], S["--only"]
    auth = json.load(open(os.path.join(HERE, "photo_permits.json"), encoding="utf-8"))
    PM = {f'{x["cat"]}:{x["id"]}': x for x in auth["permits"]}
    off = {f'{x["cat"]}:{x["id"]}' for k in ("declined", "waiting") for x in auth.get(k, [])}
    rows = json.load(open(os.path.join(src, "index.json"), encoding="utf-8"))
    pj = os.path.join(HERE, "photos.json")
    P = json.load(open(pj, encoding="utf-8"))
    keep = [x for x in P["items"] if x.get("by") == "owner"]
    old = {(x["cat"], x["id"]): x for x in P["items"] if x.get("by") != "owner"}
    n = 0
    for r in rows:
        if r["status"] not in ("permit", "ok") or not r.get("photos"): continue
        key = f'{r["cat"]}:{r["id"]}'
        if (only and key not in only) or key in off: continue
        pm = PM.get(key, {})
        if r["status"] == "permit" and not pm: continue
        allowed = {(x["page"], x["url"]) for x in pm.get("images", [])} if "images" in pm else None
        fs, sources = [], []
        for p in r["photos"]:
            if allowed is not None and (p.get("page"), p.get("src")) not in allowed: continue
            stem = os.path.splitext(os.path.basename(p["file"]))[0]
            if f'{r["cat"]}:{stem}' in drop: continue
            if p.get("flag") and f'{r["cat"]}:{stem}' not in keep_flag: continue  # 人が写っているかもしれない
            d = os.path.join(ROOT, "img", "fac", r["cat"]); os.makedirs(d, exist_ok=True)
            shutil.copy(os.path.join(src, p["file"]), os.path.join(d, os.path.basename(p["file"])))
            fs.append(f'/img/fac/{r["cat"]}/{os.path.basename(p["file"])}')
            if p.get("page") and p.get("src"):
                sources.append({"page":p["page"], "url":p["src"], **({"plate_masked":True} if p.get("plate_masked") else {})})
        if not fs: continue
        it = {"cat": r["cat"], "id": r["id"], "name": r["name"], "url": r["url"], "by": "permit" if r["status"] == "permit" else "license",
              "src": r.get("policy", ""), "checked": time.strftime("%Y-%m-%d"), "photos": fs}
        if sources: it["source_photos"] = sources
        if pm.get("credit"): it["credit"] = pm["credit"]  # 許可の条件で出どころを書く
        if it["by"] == "license":
            it.update(credit="出典：" + (r.get("owner") or r["name"])[:30], license=r.get("note", "")[:30], lic_url=r.get("policy", ""))
        old[(r["cat"], r["id"])] = it; n += 1
    P["items"] = keep + sorted(old.values(), key=lambda x: (x["cat"], x["id"]))
    json.dump(P, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("photo_import", n, "事業者")


if __name__ == "__main__":
    main()
