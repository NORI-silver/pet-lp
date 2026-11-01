#!/usr/bin/env python3
"""SEOと文言ルールの自動チェック（外部ライブラリ不要）。
使い方: python3 tools/seo_check.py .   → NG があれば終了コード1。
エリア担当のSEO Agent（docs/seo-agents.md）は、PRを出す前にこれを通す。
"""
import os, re, sys, collections
from html.parser import HTMLParser

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SITE = "https://pet.shiokonbu.com"
# 画面に出してはいけない言葉（AGENTS.md）。「Google Maps」は口コミ・候補の出どころ表示として例外。
BAN = ["Gmail", "スプレッドシート", "Apps Script", "まるっと", "代理予約", "取り次", "お取次", "手配サービス", "お客さまに代わって", "空いている車をさがす", "空いている車をお探し"]
TEL_OK = ("emergency/", "area/")  # 緊急の搬送会社の電話だけ例外（tools/emergency.json の tel）
PHONE = re.compile(r"0\d{1,4}-\d{1,4}-\d{3,4}|0120-?\d{3}-?\d{3}")

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.title = ""; s.desc = None; s.canon = None; s.h1 = 0
        s.robots = ""; s._t = False; s._skip = 0; s.text = []; s.tel = []
    def handle_starttag(s, tag, a):
        a = dict(a)
        if tag == "title": s._t = True
        elif tag in ("script", "style"): s._skip += 1
        elif tag == "meta" and a.get("name") == "description": s.desc = a.get("content", "")
        elif tag == "meta" and a.get("name") == "robots": s.robots = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical": s.canon = a.get("href")
        elif tag == "h1": s.h1 += 1
        elif tag == "a" and (a.get("href") or "").startswith("tel:"): s.tel.append(a["href"])
    def handle_endtag(s, tag):
        if tag == "title": s._t = False
        elif tag in ("script", "style"): s._skip -= 1
    def handle_data(s, d):
        if s._t: s.title += d
        elif not s._skip: s.text.append(d)

def main():
    locs = re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read())
    ng, warn, titles = [], [], collections.defaultdict(list)
    for u in locs:
        rel = u.replace(SITE, "").lstrip("/")
        f = os.path.join(ROOT, rel, "index.html") if (rel == "" or rel.endswith("/")) else os.path.join(ROOT, rel)
        if not os.path.exists(f):
            ng.append(f"{u}: sitemap にあるのにファイルがない"); continue
        p = P(); p.feed(open(f, encoding="utf-8").read())
        t = p.title.strip(); titles[t].append(u)
        if not t: ng.append(f"{u}: title がない")
        elif len(t) > 70: warn.append(f"{u}: title が長い（{len(t)}字）")
        if not p.desc: ng.append(f"{u}: description がない")
        elif not 50 <= len(p.desc) <= 160: warn.append(f"{u}: description の長さ {len(p.desc)}字（50〜160字が目安）")
        if p.canon != u: ng.append(f"{u}: canonical が {p.canon}")
        if "noindex" in p.robots: ng.append(f"{u}: noindex なのに sitemap にある（県ページも検索に出す決まり）")
        if p.h1 != 1: ng.append(f"{u}: h1 が {p.h1} 個")
        body = "".join(p.text)
        for w in BAN:
            if w in body: ng.append(f"{u}: 使わない言葉「{w}」")
        if re.search(r"Google(?! Maps)", body): ng.append(f"{u}: 「Google」（Google Maps の出どころ表示以外）")
        if re.search(r"\d[\d,]*円まで", body): ng.append(f"{u}: 「◯円まで」の上限表示")
        if not rel.startswith(TEL_OK):
            if p.tel: ng.append(f"{u}: 電話リンク {p.tel[:2]}")
            if PHONE.search(body): ng.append(f"{u}: 電話番号らしき文字 {PHONE.search(body).group()}")
    for t, us in titles.items():
        if t and len(us) > 1: ng.append(f"title が重複「{t}」: {', '.join(us)}")
    for w in warn: print("注意:", w)
    for n in ng: print("NG:", n)
    print(f"{len(locs)}ページを確認。NG {len(ng)}件・注意 {len(warn)}件")
    sys.exit(1 if ng else 0)

main()
