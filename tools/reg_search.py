#!/usr/bin/env python3
"""[B] 登録一覧の事業者の公式サイトをさがす（Nori 2026-11-22「漏れ一切なくね」）。
tools/crawl/search_*.json（[{"id","q"}...]）を、シャード（argv[2]/argv[3]）ごとに1件ずつ検索して、見出しとURLを out/search_<shard>.json に書く。
何も送らない。結果のどれが公式サイトかは人（AI）が決める。.github/workflows/reg-search.yml から動かす。
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja,en;q=0.5'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(800_000).decode('utf-8', 'replace')

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
    h = get('https://html.duckduckgo.com/html/?kl=jp-jp&q=' + urllib.parse.quote(q))
    res = []
    for href, label in re.findall(r'(?is)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
        m = re.search(r'uddg=([^&]+)', href)
        res.append([strip(label), urllib.parse.unquote(m.group(1)) if m else href])
    return res

def bing(q):
    h = get('https://www.bing.com/search?setlang=ja&cc=JP&mkt=ja-JP&count=10&q=' + urllib.parse.quote(q))
    res = []
    for blk in re.findall(r'(?is)<li class="b_algo".*?</li>', h):
        m = re.search(r'(?is)<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', blk)
        if m:
            u = html.unescape(m.group(1))
            mm = re.search(r'[?&]u=a1([^&]+)', u)
            if mm:
                import base64
                try:
                    s = mm.group(1); u = base64.urlsafe_b64decode(s + '=' * (-len(s) % 4)).decode()
                except Exception:
                    pass
            sn = re.search(r'(?is)<p[^>]*>(.*?)</p>', blk)
            res.append([strip(m.group(2)), u, strip(sn.group(1))[:160] if sn else ''])
    return res

def brave(q):
    h = get('https://search.brave.com/search?source=web&q=' + urllib.parse.quote(q))
    res = []
    for blk in re.findall(r'(?is)<div[^>]+class="[^"]*snippet[^"]*"[^>]*data-type="web".*?</div>\s*</div>', h):
        m = re.search(r'(?is)<a[^>]+href="(https?://[^"]+)"', blk)
        t = re.search(r'(?is)class="[^"]*title[^"]*"[^>]*>(.*?)</', blk)
        if m:
            res.append([strip(t.group(1)) if t else '', html.unescape(m.group(1)), ''])
    return res


ENGINES = (('yahoo', yahoo), ('ddg', ddg))  # Actions からは Bing・Brave が使えない（2026-11-22）


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
        for name, fn in ENGINES:
            if fails[name] >= 8:
                continue
            try:
                got = fn(j['q'])
            except Exception as e:
                got = []; r.setdefault('err', []).append(name + ' ' + str(e)[:80])
            if got:
                r['engine'] = name; r['results'] = got[:8]; fails[name] = 0
                break
            fails[name] += 1
        res.append(r)
        time.sleep(2.5)
    json.dump(res, open(os.path.join(out, f'search_{shard}.json'), 'w'), ensure_ascii=False, indent=0)
    print('shard', shard, len(res), 'found', sum(1 for r in res if r.get('results')))

if __name__ == '__main__':
    main()
