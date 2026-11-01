#!/usr/bin/env python3
"""公式サイトとデータベースの照合（Nori 2026-11-01「定期的にサイトの情報とDBの情報があっているかをチェックする運用」）。
tools/site_watch.json にある公式サイトのページを開いて、データベースのもとにした文と料金の数字が、いまもページにあるかを確かめる。
何も送らない・何も書き換えない。結果は Markdown で出す（.github/workflows/site-watch.yml が Issue にまとめる）。
使い方：python3 tools/site_watch.py [出力.md]   外部ライブラリ不要。
"""
import html, json, re, sys, time, unicodedata, urllib.request, urllib.parse, urllib.error, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = json.load(open(os.path.join(ROOT, 'tools/site_watch.json')))['pages']
# ふつうのブラウザと同じ名乗りにする（ロボットの名乗りだと 403 を返すサイトがあるため）
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
UA2 = 'Mozilla/5.0 (compatible; pet-shiokonbu-sitewatch/1.0; +https://pet.shiokonbu.com/)'

def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'[\s　]+', '', s)
    return s.replace('〜', '~').replace('～', '~').replace('ー', 'ー')

def iri(url):
    # 日本語の入ったURL（/料金表/ など）をそのまま開けるようにする
    u = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((u.scheme, u.netloc.encode('idna').decode(), urllib.parse.quote(u.path, safe='/%'),
                                    urllib.parse.quote(u.query, safe='=&%'), urllib.parse.quote(u.fragment, safe='%')))

def get(url, ua):
    req = urllib.request.Request(iri(url), headers={'User-Agent': ua, 'Accept-Language': 'ja,en;q=0.5',
                                                    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read(), r.headers.get_content_charset()

def fetch(url):
    try:
        raw, cs = get(url, UA)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        time.sleep(3)
        raw, cs = get(url, UA2)   # もう1回だけ、名乗りを変えて試す
    cs = cs or (re.search(rb'charset=["\']?([\w-]+)', raw[:3000]) or [None, b'utf-8'])[1].decode()
    t = raw.decode(cs, 'replace')
    t = re.sub(r'(?s)<!--.*?-->', ' ', t)
    vis = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', t)
    global CHUNKS
    # 近い文をさがすための、ページの文のかたまり（タグや改行で区切ったもの）
    CHUNKS = [c for c in (norm(html.unescape(x)) for x in re.split(r'<[^>]+>|\n', vis)) if len(c) >= 4]
    vis = norm(html.unescape(re.sub(r'<[^>]+>', ' ', vis)))
    # 画面を後から作るページ（Wix など）は、本文が script の中のデータに入っているので、そこも見る
    data = ' '.join(re.findall(r'(?is)<script[^>]*>(.*?)</script>', t))
    data = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), data)
    data = norm(html.unescape(re.sub(r'<[^>]+>', ' ', data.replace('\\n', ' ').replace('\\/', '/'))))
    return vis, data

CHUNKS = []

def nearest(q):
    # データベースの文にいちばん近いページの文（となりの2つまでつなげて見る）。直すときの参考に Issue に出す
    q = norm(q)
    qg = {q[i:i + 2] for i in range(len(q) - 1)}
    if not qg: return ''
    best, score = '', 0.0
    for i in range(len(CHUNKS)):
        for j in range(i + 1, min(i + 4, len(CHUNKS) + 1)):
            c = ''.join(CHUNKS[i:j])
            if len(c) > 200: break
            cg = {c[k:k + 2] for k in range(len(c) - 1)}
            hit = len(qg & cg)
            if not hit: continue
            f = 2 * hit / (len(qg) + len(cg))
            if f > score: best, score = c, f
    return best if score >= 0.3 else ''

NUM = re.compile(r'\d[\d,]*(?:\.\d+)?')

def close_enough(part, text):
    # 文をそのまま写していない（要約した）ものもあるので、数字がすべてページにあり、
    # 4文字ずつ区切った断片の7割以上がページにあれば「ある」とみる。数字が変わったときは必ず拾う。
    nums = {n.replace(',', '') for n in NUM.findall(part)}
    flat = text.replace(',', '')
    if any(not re.search(r'(?<!\d)' + re.escape(n) + r'(?!\d)', flat) for n in nums): return False
    grams = {part[i:i + 4] for i in range(len(part) - 3)}
    if not grams: return part in text
    return sum(g in text for g in grams) / len(grams) >= 0.7

def quote_ok(q, text):
    # 「／」「…」などでつないだ文は、別々の場所から取った文なので分けて見る
    raw = re.split(r'…|･･･|\.\.\.|（[^）]*?(?:食い違い|書き方)[^）]*）|→|／|/(?!\d)', q)
    parts = [norm(p) for p in raw if len(norm(p)) >= 6]
    if not parts: return True, ''
    miss = [p for p in parts if p not in text]
    if not miss: return True, ''
    # 句読点で区切った文ごとにも見る（句点の位置が変わっただけを拾わない）
    sents = [s for p in miss for s in re.split(r'[。！!？?]', p) if len(s) >= 6]
    still = [s for s in sents if s not in text and not close_enough(s, text)]
    return (not still), (still[0] if still else '')

def yen_ok(n, text):
    return any(f in text for f in ('{:,}'.format(n), str(n)))

def main():
    out_md = sys.argv[1] if len(sys.argv) > 1 else ''
    bad, noread, ok = [], [], 0
    for i, p in enumerate(W):
        try:
            vis, data = fetch(p['url'])
        except Exception as e:
            noread.append((p, '開けない（%s）' % str(e)[:80])); continue
        text = vis + '|' + data
        if len(text) < 300:
            noread.append((p, 'ページの文がほとんど読めない（画面を後から作るページの可能性）')); continue
        here_ok, here_bad = 0, []
        for c in p['checks']:
            if 'quote' in c:
                good, miss = quote_ok(c['quote'], text)
                if good: here_ok += 1
                else:
                    near = nearest(miss or c['quote'])
                    here_bad.append((p, c, '文が見つからない：「%s」' % (miss[:60] or c['quote'][:60]), near[:120]))
            else:
                miss = [n for n in c['nums'] if not yen_ok(n, text)]
                if miss: here_bad.append((p, c, '料金の数字が見つからない：' + '、'.join('{:,}円'.format(n) for n in miss), ''))
                else: here_ok += 1
        if here_bad and not here_ok and len(p['checks']) >= 2:
            # 1つも合わないページは、サイトが変わったより、ページの中身を読めていない（後から画面を作る等）ことが多い
            noread.append((p, 'どの項目も見つからない（ページの中身を読めていない可能性。%d文字読めた）' % len(text))); continue
        ok += here_ok; bad += here_bad
        time.sleep(1)
    lines = ['# 公式サイトとデータベースの照合', '', '確かめた日：%s（日本時間）' % time.strftime('%Y-%m-%d %H:%M', time.gmtime(time.time() + 9 * 3600)), '',
             '- 合っていた：%d 件' % ok, '- 公式サイトから消えた・変わった：%d 件' % len(bad), '- ページを読めなかった：%d ページ' % len(noread), '']
    if bad:
        lines += ['## 公式サイトから消えた・変わったもの（データベースを直す候補）', '', '| 会社 | 項目 | 見つからないもの | ページにある近い文 | ページ |', '|---|---|---|---|---|']
        lines += ['| %s | %s | %s | %s | %s |' % (c['name'], c['key'], why.replace('|', '／'), near.replace('|', '／'), p['url']) for p, c, why, near in bad]
        lines.append('')
    if noread:
        lines += ['## 読めなかったページ（人の目で確かめる）', '', '| ページ | 理由 | 会社 |', '|---|---|---|']
        lines += ['| %s | %s | %s |' % (p['url'], why, '、'.join(sorted({c['name'] for c in p['checks']}))) for p, why in noread]
        lines.append('')
    lines += ['直しかた：事業者マスター（facts.json）と条件のデータベース（conditions.json）を直してから、`tools/display_companies.py` と `tools/gen_areas.py` を動かします。']
    md = '\n'.join(lines)
    if out_md: open(out_md, 'w').write(md)
    print(md)

if __name__ == '__main__':
    main()
