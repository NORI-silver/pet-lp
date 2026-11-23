#!/usr/bin/env python3
"""[B] 登録一覧の事業所の公式サイトをさがして読む（関東の各スレッド共通。Nori 2026-11-22「漏れ一切なくね」）。
tools/crawl/regq_*.json（[{id,pref,city,name,addr,types}]）のうち、シャード SHARD/NSHARD の分だけ、
Yahoo! JAPAN の検索結果（名前＋市区町村、2.5秒おき）を取り、まとめサイト以外の上位2件を site_snap と同じ形で読む。
何も送らない・書き換えない。載せるかは人（AI）が文を読んで決める。
"""
import json, os, re, sys, time, random, urllib.parse
import concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__))
import site_snap as ss

SKIP = re.compile(r'goodbreeder|ekiten|hotpepper|beauty\.|instagram|facebook|twitter|x\.com|tiktok|youtube|amebaownd\.com/posts|ameblo\.jp/.+/entry|minkou|petlife|caloo|mapion|itp\.ne|navitime|jpnumber|tabelog|google\.|yahoo\.|bing\.|wikipedia|townpage|petpet|pet-home|epark|jalan|rakuten|amazon|indeed|baitoru|mynavi|townwork|en-gage|doda|jobs?\.|recruit|kyujin|houjin|catr\.jp|alarmbox|baseconnect|nikkei|irbank|zehitomo|dog-ruffian|animals-peace|bodik|ckan|\.lg\.jp|\.go\.jp|metro\.tokyo|pref\.|city\.|dogfoodlab|minnano|petsitter-search|torepet|uchinoshippo|rouken|ozmall|retty|gnavi|petspot|mapfan|ekitan|travel|trip|holiday|ikyu|pethotel-navi|dog-hotel\.jp|petsearch|dogrun|inutoissho|wannyan|dogbook|lifull|homes\.co|suumo|chintai|pinterest|line\.me|note\.com|hatena|fc2\.com/blog|livedoor\.jp|goo\.ne', re.I)

def _strip(x):
    return ss.html.unescape(re.sub(r'<[^>]+>', '', x)).strip()

def yahoo(q):
    """Yahoo! JAPAN の検索（Actions からは DuckDuckGo・Bing が使えないため。中国四国九州スレッドの west_search.py と同じ読み方）。"""
    h, _ = ss.get('https://search.yahoo.co.jp/search?ei=UTF-8&p=' + urllib.parse.quote(q))
    res = []
    for m in re.finditer(r'(?is)<a[^>]+href="(https?://[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*<h3[^>]*>(.*?)</h3>', h):
        u = ss.html.unescape(m.group(1))
        if 'yahoo.co.jp' not in u: res.append([_strip(m.group(2)), u])
    if not res:
        for m in re.finditer(r'(?is)<h3[^>]*>\s*<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', h):
            u = ss.html.unescape(m.group(1))
            if 'yahoo.co.jp' not in u: res.append([_strip(m.group(2)), u])
    return res[:10]

STOP = [False]
T0 = time.time()
BUDGET = int(os.environ.get('REG_BUDGET_SEC', 1500))

def search(it):
    """1つのIPで約40回を超えると 429 になるので、1つのシャードは少ない件数にし、429 が2回続いたらそのシャードは止める（残りは not_searched で次に回す）。"""
    r = dict(it)
    q = it.get('q2') or f"{it['name']} {it['city']}"
    r['q'] = q
    if STOP[0] or time.time() - T0 > BUDGET:
        r['results'] = []; r['search_error'] = 'not_searched'; return r
    for i in range(2):
        try:
            res = yahoo(q)
            r['results'] = res; r.pop('search_error', None)
            if not res: r['search_error'] = 'empty'
            break
        except Exception as e:
            r['results'] = []; r['search_error'] = 'not_searched:' + str(e)[:80]
            if i == 0: time.sleep(30)
    else:
        STOP[0] = True
    time.sleep(3 + random.random() * 2)
    return r

def snaps(r):
    cands = [u for _, u in r.get('results', []) if u.startswith('http') and not SKIP.search(u)][:2]
    r['snaps'] = []
    for u in cands:
        s = ss.snap({'url': u}); s.pop('cat', None); r['snaps'].append(s)
    return r

def main():
    out = sys.argv[1]; shard, n = int(os.environ.get('SHARD', 0)), int(os.environ.get('NSHARD', 1))
    os.makedirs(out, exist_ok=True)
    base = os.path.join(os.path.dirname(__file__), 'crawl')
    for fn in sorted(os.listdir(base)):
        if not (fn.startswith('regq_') and fn.endswith('.json')): continue
        items = [x for i, x in enumerate(json.load(open(os.path.join(base, fn)))) if i % n == shard]
        res = [search(x) for x in items]
        with cf.ThreadPoolExecutor(8) as ex:
            res = list(ex.map(snaps, res))
        json.dump(res, open(os.path.join(out, fn.replace('.json', f'_s{shard}.json')), 'w'), ensure_ascii=False)
        print(fn, shard, len(res), 'search_err', sum(1 for x in res if x.get('search_error')))

if __name__ == '__main__':
    main()
