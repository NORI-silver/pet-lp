#!/usr/bin/env python3
"""[B] 近畿の網羅：どの検索サービスが Actions から使えるかを少しだけためす（5語ずつ）。何も送らない。"""
import json, sys, os, re, html, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap
Q = ["ドッグサロン ムーン 八尾市", "空港ドッグセンター 豊中", "ペットシッター シュヌッフィ 高槻", "犬のようちえん 高槻教室", "猫シッター てつにゃぼ 此花区"]
ENG = {
 'yahoo': ('https://search.yahoo.co.jp/search?p=', r'(?is)<a[^>]+href="(https?://(?!search\.yahoo|[^"]*yahoo\.co\.jp)[^"]+)"[^>]*>(.*?)</a>'),
 'brave': ('https://search.brave.com/search?q=', r'(?is)<a[^>]+href="(https?://(?![^"]*brave\.com)[^"]+)"[^>]*>(.*?)</a>'),
 'mojeek': ('https://www.mojeek.com/search?q=', r'(?is)<a[^>]+class="ob"[^>]+href="([^"]+)"[^>]*>(.*?)</a>'),
 'bing': ('https://www.bing.com/search?form=QBLH&mkt=ja-JP&q=', r'(?is)<li class="b_algo".*?<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>'),
 'ddg_lite': ('https://lite.duckduckgo.com/lite/?kl=jp-jp&q=', r'(?is)<a[^>]+class=.result-link.[^>]*href="([^"]+)"[^>]*>(.*?)</a>'),
 'startpage': ('https://www.startpage.com/do/search?q=', r'(?is)<a[^>]+class="[^"]*result-title[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>'),
}
out = {}
for name, (base, rx) in ENG.items():
    rows = []
    for q in Q:
        try:
            h, _ = site_snap.get(base + urllib.parse.quote(q))
            res = [[html.unescape(re.sub(r'<[^>]+>', '', l)).strip()[:60], u[:120]] for u, l in re.findall(rx, h)][:5]
            rows.append({'q': q, 'n': len(h), 'res': res})
        except Exception as e:
            rows.append({'q': q, 'err': str(e)[:120]})
        time.sleep(3)
    out[name] = rows
json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
