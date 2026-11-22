#!/usr/bin/env python3
"""[B] 都道府県・政令市が公開している「第一種動物取扱業の登録一覧」をそのまま取ってくる（Nori 2026-11-22「漏れ一切なくね」）。
tools/crawl/reg*.json（[{"key":"千葉県","url":"…"}]）のページを開き、ページそのものと、ページの中の PDF・Excel・CSV の一覧ファイル
（リンクの文字か名前に「動物取扱」「登録」「一覧」「名簿」など）を out/reg/<key>/ に置く。掲載に足りない事業者を数える元にする。
何も送らない・書き換えない。.github/workflows/site-snap.yml から動かす。
"""
import concurrent.futures as cf, html, json, os, re, sys, urllib.parse, urllib.request
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
FILE = re.compile(r'\.(pdf|xlsx?|csv)(\?|$)', re.I)
WANT = re.compile(r'動物取扱|取扱業|登録|一覧|名簿|業者|第一種|保管|訓練|販売')

def get(url, n=30_000_000):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read(n), r.geturl(), r.headers.get('Content-Type', '')

def one(job, out):
    key, url = job['key'], job['url']
    d = os.path.join(out, 'reg', re.sub(r'[^\w一-龥ぁ-んァ-ン]', '_', key)); os.makedirs(d, exist_ok=True)
    log = {'key': key, 'url': url, 'files': []}
    try:
        raw, final, ct = get(url)
    except Exception as e:
        log['error'] = str(e)[:120]; return log
    if FILE.search(final) or 'pdf' in ct or 'sheet' in ct or 'excel' in ct:
        fn = os.path.basename(urllib.parse.urlparse(final).path) or 'file'
        open(os.path.join(d, fn), 'wb').write(raw); log['files'].append(final); return log
    h = raw.decode('utf-8', 'replace')
    if 'charset=shift_jis' in h[:3000].lower() or 'charset=shift-jis' in h[:3000].lower(): h = raw.decode('cp932', 'replace')
    open(os.path.join(d, 'page.html'), 'w').write(h)
    links = []
    for m in re.finditer(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', h):
        href, txt = m.group(1), html.unescape(re.sub(r'<[^>]+>', '', m.group(2)))
        if FILE.search(href) and (WANT.search(txt) or WANT.search(urllib.parse.unquote(href))):
            links.append(urllib.parse.urljoin(final, href))
    for u in list(dict.fromkeys(links))[:25]:
        try:
            raw2, f2, _ = get(u)
            fn = os.path.basename(urllib.parse.urlparse(f2).path) or 'file'
            open(os.path.join(d, fn), 'wb').write(raw2); log['files'].append(u)
        except Exception as e:
            log.setdefault('errs', []).append(u + ' ' + str(e)[:60])
    return log

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
    base = os.path.join(os.path.dirname(__file__), 'crawl')
    jobs = []
    for fn in sorted(os.listdir(base)):
        if fn.startswith('reg_') and fn.endswith('.json'): jobs += json.load(open(os.path.join(base, fn)))
    if not jobs: return
    with cf.ThreadPoolExecutor(8) as ex:
        logs = list(ex.map(lambda j: one(j, out), jobs))
    os.makedirs(out, exist_ok=True)
    json.dump(logs, open(os.path.join(out, 'reg_log.json'), 'w'), ensure_ascii=False, indent=1)
    print('reg', len(logs), 'files', sum(len(l['files']) for l in logs))

if __name__ == '__main__':
    main()
