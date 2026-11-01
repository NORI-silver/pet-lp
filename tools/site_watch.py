#!/usr/bin/env python3
"""公式サイトとデータベースの照合（Nori 2026-11-01「定期的にサイトの情報とDBの情報があっているかをチェックする運用」）。
tools/site_watch.json にある公式サイトのページを開いて、データベースのもとにした文と料金の数字が、いまもページにあるかを確かめる。
何も送らない・何も書き換えない。結果は Markdown で出す（.github/workflows/site-watch.yml が Issue にまとめる）。
使い方：python3 tools/site_watch.py [出力.md]   外部ライブラリ不要。
"""
import html, json, re, sys, time, unicodedata, urllib.request, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = json.load(open(os.path.join(ROOT, 'tools/site_watch.json')))['pages']
UA = 'Mozilla/5.0 (compatible; pet-shiokonbu-sitewatch/1.0; +https://pet.shiokonbu.com/)'

def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'[\s　]+', '', s)
    return s.replace('〜', '~').replace('～', '~').replace('ー', 'ー')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja'})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        cs = r.headers.get_content_charset() or (re.search(rb'charset=["\']?([\w-]+)', raw[:3000]) or [None, b'utf-8'])[1].decode()
    t = raw.decode(cs, 'replace')
    t = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', t)
    t = re.sub(r'(?s)<!--.*?-->', ' ', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    return norm(html.unescape(t))

def quote_ok(q, text):
    parts = [norm(p) for p in re.split(r'…|･･･|\.\.\.|（[^）]*?食い違い[^）]*）|→', q) if len(norm(p)) >= 6]
    if not parts: return True, ''
    miss = [p for p in parts if p not in text]
    if not miss: return True, ''
    # 句読点で区切った文ごとにも見る（句点の位置が変わっただけを拾わない）
    sents = [s for p in miss for s in re.split(r'[。！!？?]', p) if len(s) >= 6]
    still = [s for s in sents if s not in text]
    return (not still), (still[0] if still else '')

def yen_ok(n, text):
    return any(f in text for f in ('{:,}'.format(n), str(n)))

def main():
    out_md = sys.argv[1] if len(sys.argv) > 1 else ''
    bad, noread, ok = [], [], 0
    for i, p in enumerate(W):
        try:
            text = fetch(p['url'])
        except Exception as e:
            noread.append((p, '開けない（%s）' % str(e)[:80])); continue
        if len(text) < 300:
            noread.append((p, 'ページの文がほとんど読めない（画面を後から作るページの可能性）')); continue
        for c in p['checks']:
            if 'quote' in c:
                good, miss = quote_ok(c['quote'], text)
                if good: ok += 1
                else: bad.append((p, c, '文が見つからない：「%s」' % (miss[:60] or c['quote'][:60])))
            else:
                miss = [n for n in c['nums'] if not yen_ok(n, text)]
                if miss: bad.append((p, c, '料金の数字が見つからない：' + '、'.join('{:,}円'.format(n) for n in miss)))
                else: ok += 1
        time.sleep(1)
    lines = ['# 公式サイトとデータベースの照合', '', '確かめた日：%s（日本時間）' % time.strftime('%Y-%m-%d %H:%M', time.gmtime(time.time() + 9 * 3600)), '',
             '- 合っていた：%d 件' % ok, '- 公式サイトから消えた・変わった：%d 件' % len(bad), '- ページを読めなかった：%d ページ' % len(noread), '']
    if bad:
        lines += ['## 公式サイトから消えた・変わったもの（データベースを直す候補）', '', '| 会社 | 項目 | 見つからないもの | ページ |', '|---|---|---|---|']
        lines += ['| %s | %s | %s | %s |' % (c['name'], c['key'], why.replace('|', '／'), p['url']) for p, c, why in bad]
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
