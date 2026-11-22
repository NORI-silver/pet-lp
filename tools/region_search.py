#!/usr/bin/env python3
"""[B] 地域の網羅：登録簿の事業者の名前と市区町村で検索し、上位の結果（見出しとURL）だけを書く（site-search-nkt.yml）。
どれが公式サイトかは人（AI）が結果を見て決める。何も送らない。
使い方: python3 tools/region_search.py <chunk.json> <out.json> [間隔秒]"""
import json, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap, html, re, urllib.parse

def get(url):
    return site_snap.get(url)[0]

def strip(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()

def yahoo(q):
    h = get('https://search.yahoo.co.jp/search?ei=UTF-8&p=' + urllib.parse.quote(q))
    res = []
    for m in re.finditer(r'(?is)<a[^>]+href="(https?://[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*<h3[^>]*>(.*?)</h3>', h):
        u = html.unescape(m.group(1))
        if 'yahoo.co.jp' in u: continue
        res.append([strip(m.group(2)), u])
    if not res:
        for m in re.finditer(r'(?is)<h3[^>]*>\s*<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', h):
            u = html.unescape(m.group(1))
            if 'yahoo.co.jp' not in u: res.append([strip(m.group(2)), u])
    return res



def main():
    items = json.load(open(sys.argv[1]))
    gap = float(sys.argv[3]) if len(sys.argv) > 3 else 5
    out = []
    for it in items:
        r = {'q': it['q']}
        try: r['results'] = yahoo(it['q'])[:10]
        except Exception as e: r['error'] = str(e)[:200]
        if not r.get('results'): r = site_snap.search({'q': it['q']})
        r['cid'] = it['cid']
        if not r.get('results') and not r.get('error'):
            time.sleep(gap * 4)  # 空なら少し待ってもう一度
            r2 = site_snap.search({'q': it['q']}); r2['cid'] = it['cid']; r2['retry'] = 1; r = r2
        out.append(r)
        time.sleep(gap)
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
    print(sys.argv[1], len(out), 'empty', sum(1 for x in out if not x.get('results')))

if __name__ == '__main__':
    main()
