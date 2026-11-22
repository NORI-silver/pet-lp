#!/usr/bin/env python3
"""[A] ペットと避難：まだ読めていない市区町村の公式サイトを外から読む（Nori 2026-11-23「全然集まってない」）。
tools/crawl/hinan_queue.json（[{"pref","name","code","url"}...]）の各自治体について、
その自治体のドメインの中を「ペット 避難」で検索し、上位のページとPDF（最大5つ）を開いて、
ペット・同行避難にかかわる行だけを out/hinan/<code>.json に書く。何も送らない。
載せるかは AI が行を読んで決め、tools/hinan.json に出どころつきで入れる。
.github/workflows/hinan-snap.yml から動かす（コンテナからは自治体のサイトに届かないため）。
"""
import concurrent.futures as cf, html, json, os, re, subprocess, sys, tempfile, time, urllib.parse, urllib.request

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
KEY = re.compile(r'ペット|同行|同伴|動物|犬|猫|ケージ|キャリー|リード|飼い主|飼養|愛玩|小鳥|うさぎ|ウサギ|爬虫|特定動物|盲導|補助犬')


def get(url, limit=40_000_000):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read(limit), r.headers.get('Content-Type', ''), r.geturl()


def decode(raw, ct):
    m = re.search(r'charset=([\w-]+)', ct) or re.search(rb'charset=["\']?([\w-]+)', raw[:3000])
    enc = (m.group(1) if isinstance(m.group(1), str) else m.group(1).decode()) if m else 'utf-8'
    try:
        return raw.decode(enc, 'replace')
    except LookupError:
        return raw.decode('utf-8', 'replace')


def text_lines(h):
    h = re.sub(r'(?is)<(script|style|noscript|svg|header|footer|nav)[^>]*>.*?</\1>', ' ', h)
    h = re.sub(r'(?i)<br\s*/?>|</(p|div|li|tr|h\d|dt|dd|td|th|section|article)>', '\n', h)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', h))
    return [re.sub(r'[ \t　]+', ' ', l).strip() for l in t.split('\n')]


def pdf_lines(raw):
    with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
        f.write(raw); f.flush()
        out = subprocess.run(['pdftotext', '-layout', f.name, '-'], capture_output=True, timeout=120).stdout
    return [re.sub(r'[ \t　]+', ' ', l).strip() for l in out.decode('utf-8', 'replace').split('\n')]


def pick(lines):
    """ペットの話の行と、その前後1行。"""
    lines = [l for l in lines if l]
    keep = set()
    for i, l in enumerate(lines):
        if KEY.search(l):
            keep.update(range(max(0, i - 1), min(len(lines), i + 2)))
    out, seen = [], set()
    for i in sorted(keep):
        l = lines[i][:300]
        if l not in seen:
            seen.add(l); out.append(l)
    return out[:400]


def search(q):
    raw, ct, _ = get('https://html.duckduckgo.com/html/?kl=jp-jp&q=' + urllib.parse.quote(q))
    h = decode(raw, ct)
    res = []
    for href, label in re.findall(r'(?is)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
        m = re.search(r'uddg=([^&]+)', href)
        u = urllib.parse.unquote(m.group(1)) if m else href
        res.append([html.unescape(re.sub(r'<[^>]+>', '', label)).strip(), u])
    return res


def bing(q):
    raw, ct, _ = get('https://www.bing.com/search?setlang=ja&cc=JP&q=' + urllib.parse.quote(q))
    h = decode(raw, ct)
    return [[html.unescape(re.sub(r'<[^>]+>', '', lab)).strip(), u] for u, lab in
            re.findall(r'(?is)<li class="b_algo".*?<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h)]


NAV = re.compile(r'防災|災害|避難|ペット|動物|犬|猫|危機管理|安全|くらし|暮らし|生活|環境|bousai|bosai|saigai|hinan|kurashi|pet|animal', re.I)
HOT = re.compile(r'ペット|同行避難|動物')
PLAN = re.compile(r'防災計画|防災ガイド|防災マップ|ハザードマップ|防災ハンドブック|避難所運営|防災のしおり|防災手帳')
MAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.jp')


def crawl(home, limit=60, mails=None):
    """トップから「防災・避難・ペット」のリンクをたどり、ペットの話のあるページ・PDFのURLを集める。"""
    host = urllib.parse.urlparse(home).netloc
    todo, seen, hits = [home], set(), []
    while todo and len(seen) < limit:
        u = todo.pop(0)
        if u in seen:
            continue
        seen.add(u)
        try:
            raw, ct, final = get(u, 2_000_000)
        except Exception:
            continue
        if 'html' not in ct.lower():
            continue
        h = decode(raw, ct)
        if mails is not None and re.search(r'防災|危機管理|災害', h[:20000]):
            for a in MAIL.findall(html.unescape(h)):
                mails.setdefault(a, final)
        for href, label in re.findall(r'(?is)<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', h):
            v = urllib.parse.urljoin(final, href)
            pu = urllib.parse.urlparse(v)
            if pu.netloc != host:
                continue
            lab = re.sub(r'<[^>]+>|\s+', '', label)
            if v.lower().endswith('.pdf'):
                if (HOT.search(lab) or PLAN.search(lab)) and v not in hits:
                    hits.append(v)
                continue
            if HOT.search(lab) and v not in hits:
                hits.append(v)
            if (NAV.search(lab) or NAV.search(pu.path)) and v not in seen and v not in todo and len(todo) < 300:
                if re.search(r'防災|避難|ペット|災害|危機', lab):
                    todo.insert(0, v)
                else:
                    todo.append(v)
    return hits[:10]


def read(url):
    try:
        raw, ct, final = get(url)
        if 'pdf' in ct.lower() or final.lower().endswith('.pdf') or raw[:5] == b'%PDF-':
            lines, kind = pdf_lines(raw), 'pdf'
            mails = []
        else:
            h = decode(raw, ct)
            lines, kind = text_lines(h), 'html'
            mails = sorted(set(re.findall(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.jp', html.unescape(h))))
            m = re.search(r'(?is)<title[^>]*>(.*?)</title>', h)
            if m:
                lines.insert(0, '【title】' + html.unescape(re.sub(r'\s+', ' ', m.group(1))).strip())
        r = {'url': final, 'kind': kind, 'lines': pick(lines)}
        if kind == 'html' and mails:
            r['mails'] = mails[:6]
        return r
    except Exception as e:
        return {'url': url, 'error': str(e)[:200]}


def one(job):
    it, res, urls, out = job
    mails = {}
    try:
        for u in crawl(it['url'], mails=mails):
            if u not in urls:
                urls.append(u)
    except Exception as e:
        res.append(['crawl-error', str(e)[:100]])
    pages = [read(u) for u in urls[:12]]
    json.dump({**it, 'mails': mails, 'pages': pages}, open(f"{out}/{it['code']}.json", 'w'), ensure_ascii=False, indent=1)
    return it['name'], len(urls), sum(len(p.get('lines', [])) for p in pages)


def main(out):
    q = json.load(open('tools/crawl/hinan_queue.json'))
    os.makedirs(out, exist_ok=True)
    jobs = []
    for it in q:  # 検索は順番に、間をあける
        host = urllib.parse.urlparse(it['url']).netloc
        res = []
        urls = []
        for lab, u in res:
            if u.startswith('http') and urllib.parse.urlparse(u).netloc == host and u not in urls:
                urls.append(u)
        jobs.append((it, res, urls[:5], out))
    with cf.ThreadPoolExecutor(12) as ex:
        for r in ex.map(one, jobs):
            print(*r, flush=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'out')
