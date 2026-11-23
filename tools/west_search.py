#!/usr/bin/env python3
"""[B] 中国・四国・九州沖縄：登録一覧の事業所の公式サイトを検索でさがす（Nori 2026-11-22「漏れ一切なくね」）。
tools/crawl/search_*.json（[{"id","q"}...]）をシャードに分け、日本語の検索（Yahoo! JAPAN → DuckDuckGo lite → Bing）で1件ずつ調べ、
見出しとURLを out/search_<shard>.json に書く。何も送らない。どれが公式サイトかは人（AI）が決める。
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja,en;q=0.5'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(1_000_000).decode('utf-8', 'replace')

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

def ddg(q):
    h = get('https://lite.duckduckgo.com/lite/?kl=jp-jp&q=' + urllib.parse.quote(q))
    res = []
    for href, label in re.findall(r"(?is)<a[^>]+href=\"([^\"]+)\"[^>]*class=['\"]result-link['\"][^>]*>(.*?)</a>", h):
        m = re.search(r'uddg=([^&]+)', href)
        res.append([strip(label), urllib.parse.unquote(m.group(1)) if m else href])
    return res

def main():
    out = sys.argv[1]; shard = int(sys.argv[2]); n = int(sys.argv[3])
    os.makedirs(out, exist_ok=True)
    base = os.path.join(os.path.dirname(__file__), 'crawl')
    jobs = []
    for fn in sorted(os.listdir(base)):
        if fn.startswith('search') and fn.endswith('.json'):
            jobs += json.load(open(os.path.join(base, fn)))
    jobs = jobs[shard::n]
    res = []; fails = {'yahoo': 0, 'ddg': 0}
    for j in jobs:
        r = dict(j)
        for name, fn in (('yahoo', yahoo), ('ddg', ddg)):
            if fails[name] >= 6: continue
            try:
                got = fn(j['q'])
            except Exception as e:
                got = []; r.setdefault('err', []).append(name + ' ' + str(e)[:80])
                if '429' in str(e):
                    time.sleep(40)
                    try: got = fn(j['q'])
                    except Exception: got = []
            if got:
                r['engine'] = name; r['results'] = got[:8]; fails[name] = 0
                break
            fails[name] += 1
        res.append(r)
        time.sleep(4)
    json.dump(res, open(os.path.join(out, f'search_{shard}.json'), 'w'), ensure_ascii=False, indent=0)
    print('shard', shard, len(res), 'found', sum(1 for r in res if r.get('results')))

if __name__ == '__main__':
    main()
