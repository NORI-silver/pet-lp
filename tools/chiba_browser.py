#!/usr/bin/env python3
"""[B] 千葉県の網羅スレッド専用：ふつうの読み方（site_snap.py）で 403・時間切れになった公式サイトを、
本物のブラウザ（Chrome）で開いて読み直す。tools/crawl/chiba/browser*.json（[{"cid","url"}...]）を読み、
結果は site_snap.snap と同じ形（final・title・pages[].lines）で <out>/bsnap*.json に書く。何も送らない・書き換えない。
使い方: python3 tools/chiba_browser.py <out>"""
import json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_snap import KEY, SUB
from playwright.sync_api import sync_playwright


def lines_of(page):
    t = page.evaluate('document.body ? document.body.innerText : ""')
    out = []
    for l in t.split('\n'):
        l = re.sub(r'[ \t　]+', ' ', l).strip()
        if l and l not in out and KEY.search(l) and len(l) < 220:
            out.append(l)
    return out


def sublinks(page, base):
    host = urllib.parse.urlparse(base).netloc
    links = page.evaluate('Array.from(document.querySelectorAll("a[href]")).map(a=>[a.href,(a.innerText||"").slice(0,40)])')
    out = []
    for u, lab in links:
        p = urllib.parse.urlparse(u.split('#')[0])
        u = p.geturl()
        if p.netloc != host or re.search(r'\.(jpg|png|pdf|gif|zip)$', p.path, re.I):
            continue
        if (SUB.search(p.path) or SUB.search(lab)) and u not in out and u.rstrip('/') != base.rstrip('/'):
            out.append(u)
    return out[:4]


def one(ctx, item):
    r = dict(item)
    page = ctx.new_page()
    try:
        resp = page.goto(item['url'], timeout=45000, wait_until='domcontentloaded')
        page.wait_for_timeout(2500)
        if resp and resp.status >= 400:
            r['error'] = f'HTTP {resp.status}'
            return r
        r['final'] = page.url
        r['title'] = page.title()
        pages = [{'url': page.url, 'lines': lines_of(page)[:80]}]
        for u in sublinks(page, page.url):
            try:
                page.goto(u, timeout=30000, wait_until='domcontentloaded')
                page.wait_for_timeout(1500)
                pages.append({'url': page.url, 'title': page.title(), 'lines': lines_of(page)[:60]})
            except Exception as e:
                pages.append({'url': u, 'error': str(e)[:120]})
        r['pages'] = pages
    except Exception as e:
        r['error'] = str(e)[:200]
    finally:
        page.close()
    return r


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crawl', 'chiba')
    files = [f for f in sorted(os.listdir(d)) if f.startswith('browser') and f.endswith('.json')]
    if not files:
        return
    with sync_playwright() as p:
        br = p.chromium.launch(channel='chrome', headless=True)
        ctx = br.new_context(locale='ja-JP', ignore_https_errors=True,
                             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36')
        for fn in files:
            res = [one(ctx, it) for it in json.load(open(os.path.join(d, fn)))]
            json.dump(res, open(os.path.join(out, 'b' + fn.replace('browser', 'snap')), 'w'), ensure_ascii=False, indent=1)
            print(fn, len(res), 'errors', sum(1 for x in res if x.get('error')))
        br.close()


if __name__ == '__main__':
    main()
