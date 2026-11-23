#!/usr/bin/env python3
"""[B] 近畿の網羅：登録簿の事業者の名前と市区町村で検索し、上位の結果（見出しとURL）だけを書く（site-search-kinki.yml）。
どれが公式サイトかは人（AI）が結果を見て決める。何も送らない。
2026-11-23：DuckDuckGo は Actions から全部空、Bing は語を無視した的外れの結果だったので、Yahoo! JAPAN の検索を使う
（tools/kinki_probe.py でためして、名前に合う結果が返ったのは Yahoo! JAPAN だけ）。
続けて空が 20 回出たら止める（何時間も空のまま回さない）。
使い方: python3 tools/kinki_search.py <chunk.json> <out.json> [間隔秒]"""
import json, sys, time, os, re, html, base64, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap


def _real(u):
    """Bing の転送リンク（/ck/a?...&u=a1<base64>）を元のURLにもどす。"""
    if 'bing.com/ck/a' in u:
        m = re.search(r'[?&]u=a1([^&]+)', html.unescape(u))
        if m:
            s = m.group(1)
            try:
                return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4)).decode('utf-8', 'replace')
            except Exception:
                return u
    return html.unescape(u)


def bing(q):
    h, _ = site_snap.get('https://www.bing.com/search?setlang=ja&cc=JP&q=' + urllib.parse.quote(q))
    return [[html.unescape(re.sub(r'<[^>]+>', '', lab)).strip(), _real(u)] for u, lab in
            re.findall(r'(?is)<li class="b_algo".*?<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h)][:10]


def yahoo(q):
    h, _ = site_snap.get('https://search.yahoo.co.jp/search?p=' + urllib.parse.quote(q))
    out, seen = [], set()
    for u, lab in re.findall(r'(?is)<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', h):
        u = html.unescape(u)
        host = urllib.parse.urlparse(u).netloc
        if 'yahoo.co.jp' in host or 'yimg.jp' in host or u in seen: continue
        t = html.unescape(re.sub(r'<[^>]+>', ' ', lab))
        t = re.sub(r'\s+', ' ', t).strip()
        if not t: continue
        seen.add(u); out.append([t[:120], u])
    return out[:10]


def one(q):
    r = {'q': q}
    try:
        r['results'] = yahoo(q); r['by'] = 'yahoo'
    except Exception as e:
        r['error'] = str(e)[:200]; r['results'] = []
    return r


def main():
    items = json.load(open(sys.argv[1]))
    gap = float(sys.argv[3]) if len(sys.argv) > 3 else 4
    out, empty_run = [], 0
    for it in items:
        r = one(it['q']); r['cid'] = it['cid']
        out.append(r)
        empty_run = 0 if r.get('results') else empty_run + 1
        if empty_run >= 20:
            print('空が20回つづいたので止める', len(out)); break
        time.sleep(gap)
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
    print(sys.argv[1], len(out), 'empty', sum(1 for x in out if not x.get('results')))


if __name__ == '__main__':
    main()
