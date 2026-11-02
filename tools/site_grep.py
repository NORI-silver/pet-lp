#!/usr/bin/env python3
"""公式サイトから、決まったことばのまわりの文を集める（Nori 2026-11-02「空港とか定額が載ってるならそれ使ってよ」）。
候補カードに出している会社の公式サイト（tools/site_watch.json と display_companies.json の料金の出どころ）と、
そのページからたどれる同じサイトの料金・空港のページ（1段だけ）を開き、ことばの前後の文を Markdown で出す。
何も送らない・何も書き換えない。.github/workflows/site-grep.yml から動かす（コンテナからは各社サイトに届かないため）。
使い方：python3 tools/site_grep.py 出力.md [ことばの正規表現]
"""
import html, json, os, re, sys, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_watch as sw

ROOT = sw.ROOT
WORDS = sys.argv[2] if len(sys.argv) > 2 else r'空港|羽田|成田|伊丹|関西国際|関空|新千歳|中部国際|セントレア|那覇|定額|一律|固定料金|均一|パック料金|区間料金'
PAT = re.compile(WORDS)
LINK = re.compile(r'料金|価格|運賃|プラン|空港|price|fee|fare|plan|airport|ryokin|cost', re.I)

def raw_page(url):
    try:
        raw, cs = sw.get(url, sw.UA)
    except Exception:
        time.sleep(2)
        raw, cs = sw.get(url, sw.UA2)
    cs = cs or (re.search(rb'charset=["\']?([\w-]+)', raw[:3000]) or [None, b'utf-8'])[1].decode()
    return raw.decode(cs, 'replace')

def text_of(t):
    t = re.sub(r'(?s)<!--.*?-->', ' ', t)
    vis = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', t)
    vis = html.unescape(re.sub(r'<[^>]+>', '\n', vis))
    data = ' '.join(re.findall(r'(?is)<script[^>]*>(.*?)</script>', t))
    data = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), data)
    data = html.unescape(re.sub(r'<[^>]+>', ' ', data.replace('\\n', '\n').replace('\\/', '/')))
    lines = []
    for s in (vis + '\n' + data).split('\n'):
        s = re.sub(r'[\s　]+', ' ', s).strip()
        if s and len(s) < 400: lines.append(s)
    return lines

def links(t, base):
    host = urllib.parse.urlsplit(base).netloc
    out = []
    for href, label in re.findall(r'(?is)<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', t):
        u = urllib.parse.urljoin(base, html.unescape(href))
        if urllib.parse.urlsplit(u).netloc != host or re.search(r'\.(jpg|jpeg|png|gif|pdf|webp|svg)$', u, re.I): continue
        lab = re.sub(r'<[^>]+>', '', label)
        if LINK.search(urllib.parse.unquote(u)) or LINK.search(lab): out.append(u)
    return out

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'grep.md'
    W = json.load(open(os.path.join(ROOT, 'tools/site_watch.json')))['pages']
    D = json.load(open(os.path.join(ROOT, 'tools/display_companies.json')))
    D = D if isinstance(D, list) else D['companies']
    name = {c['id']: c['name'] for c in D}
    urls = {}
    for p in W:
        for c in p['checks']:
            if c['id'] in name: urls.setdefault(c['id'], []).append(p['url'])
    for c in D:
        s = (c.get('fare') or {}).get('src')
        if s: urls.setdefault(c['id'], []).append(s)
    rep = ['# 公式サイトのことばさがし', '', f'ことば：`{WORDS}`', '']
    bad = []
    for cid in sorted(urls, key=lambda i: name[i]):
        seen, todo, hits = set(), list(dict.fromkeys(urls[cid])), []
        depth = {u: 0 for u in todo}
        while todo and len(seen) < 8:
            u = todo.pop(0)
            if u in seen: continue
            seen.add(u)
            try:
                t = raw_page(u)
            except Exception as e:
                bad.append(f'| {name[cid]} | {u} | {str(e)[:80]} |'); continue
            for i, s in enumerate(lines := text_of(t)):
                if PAT.search(s):
                    ctx = ' ／ '.join(lines[max(0, i - 1):i + 3])[:400]
                    if ctx not in [h[1] for h in hits]: hits.append((u, ctx))
            if depth[u] == 0:
                for v in links(t, u):
                    if v not in depth: depth[v] = 1; todo.append(v)
            time.sleep(1)
        if hits:
            rep += [f'## {name[cid]}（{cid}）', '']
            rep += [f'- {c}  \n  <{u}>' for u, c in hits[:25]]
            rep.append('')
    if bad: rep += ['## 開けなかったページ', '', '| 会社 | URL | 理由 |', '|---|---|---|'] + bad
    open(out, 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep))

if __name__ == '__main__':
    main()
