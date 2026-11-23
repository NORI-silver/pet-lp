#!/usr/bin/env python3
"""[B] 地域の網羅スレッド用：登録一覧の事業所を検索し（Yahoo! JAPAN → DuckDuckGo → DuckDuckGo lite → Bing の順に、空なら次へ）、
まとめサイト以外の上位2件の公式サイトらしいページを site_snap と同じ形で読む。何も送らない。
使い方: python3 tools/region_find.py <chunk.json（[{cid,q}]）> <out.json> [間隔秒]"""
import json, os, re, sys, time, html, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap as ss

SKIP = re.compile(r'goodbreeder|ekiten|hotpepper|beauty\.|instagram|facebook|twitter|x\.com|tiktok|youtube|ameblo\.jp/.+/entry|minkou|petlife|caloo|mapion|itp\.ne|navitime|jpnumber|tabelog|google\.|yahoo\.|bing\.|duckduckgo|wikipedia|townpage|petpet|pet-home|epark|jalan|rakuten|amazon|indeed|baitoru|mynavi|townwork|en-gage|doda|jobs?\.|recruit|kyujin|houjin|catr\.jp|alarmbox|baseconnect|nikkei|irbank|zehitomo|bodik|ckan|\.lg\.jp|\.go\.jp|pref\.|city\.|minnano|petsitter-search|torepet|uchinoshippo|rouken|ozmall|retty|gnavi|petspot|mapfan|ekitan|travel|trip|ikyu|pethotel-navi|petsearch|inutoissho|wannyan|dogbook|lifull|homes\.co|suumo|chintai|pinterest|line\.me|note\.com|hatena|goo\.ne|curama|coconala|jobmedley|kakaku|breeder|wanchan|minpet|salesnow|musubu|jigyosha|kaisha|nttbj|i-town|loco\.', re.I)

def _ddg(h):
    res = []
    for href, label in re.findall(r'(?is)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
        m = re.search(r'uddg=([^&]+)', href)
        res.append([html.unescape(re.sub(r'<[^>]+>', '', label)).strip(), urllib.parse.unquote(m.group(1)) if m else href])
    return res

def _lite(h):
    res = []
    for href, label in re.findall(r"(?is)<a[^>]+href=\"([^\"]+)\"[^>]*class=['\"]result-link['\"][^>]*>(.*?)</a>", h):
        m = re.search(r'uddg=([^&]+)', href)
        res.append([html.unescape(re.sub(r'<[^>]+>', '', label)).strip(), urllib.parse.unquote(m.group(1)) if m else href])
    return res

def _bing(h):
    res = []
    for blk in re.findall(r'(?is)<li class="b_algo".*?</h2>', h):
        m = re.search(r'(?is)<h2[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', blk)
        if m: res.append([html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip(), html.unescape(m.group(1))])
    return res

def _yahoo(h):
    res = []
    for m in re.finditer(r'(?is)<a[^>]+href="(https?://[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*<h3[^>]*>(.*?)</h3>', h):
        u = html.unescape(m.group(1))
        if 'yahoo.co.jp' not in u: res.append([html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip(), u])
    if not res:
        for m in re.finditer(r'(?is)<h3[^>]*>\s*<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', h):
            u = html.unescape(m.group(1))
            if 'yahoo.co.jp' not in u: res.append([html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip(), u])
    return res

ENG = [('yahoo', 'https://search.yahoo.co.jp/search?ei=UTF-8&p=', _yahoo),
       ('ddg', 'https://html.duckduckgo.com/html/?kl=jp-jp&q=', _ddg),
       ('lite', 'https://lite.duckduckgo.com/lite/?kl=jp-jp&q=', _lite),
       ('bing', 'https://www.bing.com/search?setlang=ja&cc=JP&q=', _bing)]

def search(q):
    errs = []
    for name, base, parse in ENG:
        try:
            h, _ = ss.get(base + urllib.parse.quote(q))
            res = [r for r in parse(h) if r[1].startswith('http')]
            if res: return res[:10], name, errs
            errs.append(name + ':empty')
        except Exception as e:
            errs.append(name + ':' + str(e)[:60])
    return [], None, errs

def main():
    items = json.load(open(sys.argv[1])); gap = float(sys.argv[3]) if len(sys.argv) > 3 else 6
    out = []
    for it in items:
        r = dict(it)
        res, eng, errs = search(it['q'])
        r['results'], r['engine'] = res, eng
        if errs: r['errs'] = errs
        cands = [u for _, u in res if not SKIP.search(u)][:2]
        r['snaps'] = []
        for u in cands:
            s = ss.snap({'url': u})
            r['snaps'].append(s)
        out.append(r)
        time.sleep(gap)
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False)
    import collections
    print(sys.argv[1], len(out), 'empty', sum(1 for x in out if not x['results']), collections.Counter(x['engine'] for x in out))

if __name__ == '__main__':
    main()
