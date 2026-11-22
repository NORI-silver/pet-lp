#!/usr/bin/env python3
"""[B] 登録一覧の事業所の公式サイトをさがして読む（関東の各スレッド共通。Nori 2026-11-22「漏れ一切なくね」）。
tools/crawl/regq_*.json（[{id,pref,city,name,addr,types}]）のうち、シャード SHARD/NSHARD の分だけ、
DuckDuckGo の検索結果（名前＋市区町村）を取り、まとめサイト以外の上位2件を site_snap と同じ形で読む。
何も送らない・書き換えない。載せるかは人（AI）が文を読んで決める。
"""
import json, os, re, sys, time, random, urllib.parse
import concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__))
import site_snap as ss

SKIP = re.compile(r'goodbreeder|ekiten|hotpepper|beauty\.|instagram|facebook|twitter|x\.com|tiktok|youtube|amebaownd\.com/posts|ameblo\.jp/.+/entry|minkou|petlife|caloo|mapion|itp\.ne|navitime|jpnumber|tabelog|google\.|yahoo\.|bing\.|wikipedia|townpage|petpet|pet-home|epark|jalan|rakuten|amazon|indeed|baitoru|mynavi|townwork|en-gage|doda|jobs?\.|recruit|kyujin|houjin|catr\.jp|alarmbox|baseconnect|nikkei|irbank|zehitomo|dog-ruffian|animals-peace|bodik|ckan|\.lg\.jp|\.go\.jp|metro\.tokyo|pref\.|city\.|dogfoodlab|minnano|petsitter-search|torepet|uchinoshippo|rouken|ozmall|retty|gnavi|petspot|mapfan|ekitan|travel|trip|holiday|ikyu|pethotel-navi|dog-hotel\.jp|petsearch|dogrun|inutoissho|wannyan|dogbook|lifull|homes\.co|suumo|chintai|pinterest|line\.me|note\.com|hatena|fc2\.com/blog|livedoor\.jp|goo\.ne', re.I)

def yahoo(q):
    h, _ = ss.get('https://search.yahoo.co.jp/search?ei=UTF-8&p=' + urllib.parse.quote(q))
    res = []
    for m in re.finditer(r'(?is)<a[^>]+href="(https?://[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*<h3[^>]*>(.*?)</h3>', h):
        u = ss.html.unescape(m.group(1))
        if 'yahoo.co.jp' in u: continue
        res.append([ss.html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip(), u])
    if not res:
        for m in re.finditer(r'(?is)<h3[^>]*>\s*<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', h):
            u = ss.html.unescape(m.group(1))
            if 'yahoo.co.jp' not in u: res.append([ss.html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip(), u])
    return res

def search(q):
    """Yahoo! JAPAN を先に（Actions から DuckDuckGo・Bing は止められやすい。中国四国九州スレッドの試し 2026-11-22）。"""
    for i in range(2):
        try:
            r = yahoo(q)
            if r: return r[:10], None
        except Exception as e:
            err = str(e)[:100]
        time.sleep(4)
    return ddg(q)

def ddg(q):
    for i in range(1):
        try:
            h, _ = ss.get('https://html.duckduckgo.com/html/?kl=jp-jp&q=' + urllib.parse.quote(q))
            res = []
            for href, label in re.findall(r'(?is)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
                m = re.search(r'uddg=([^&]+)', href)
                u = urllib.parse.unquote(m.group(1)) if m else href
                res.append([ss.html.unescape(re.sub(r'<[^>]+>', '', label)).strip(), u])
            if res or 'result--no-result' in h or 'No results' in h:
                return res[:10], None
            err = 'empty'
        except Exception as e:
            err = str(e)[:100]
        time.sleep(5 + 10 * i)
    return [], err

def find(it):
    r = dict(it)
    q = f"{it['name']} {it['city']}"
    res, err = search(q)
    r['q'], r['results'] = q, res
    if err: r['search_error'] = err
    time.sleep(2.5)
    return r

def one(r):
    cands = [u for _, u in res if u.startswith('http') and not SKIP.search(u)][:2]
    r['snaps'] = []
    for u in cands:
        s = ss.snap({'url': u})
        s.pop('cat', None)
        r['snaps'].append(s)
    return r

def main():
    out = sys.argv[1]; shard, n = int(os.environ.get('SHARD', 0)), int(os.environ.get('NSHARD', 1))
    os.makedirs(out, exist_ok=True)
    base = os.path.join(os.path.dirname(__file__), 'crawl')
    for fn in sorted(os.listdir(base)):
        if not (fn.startswith('regq_') and fn.endswith('.json')): continue
        items = [x for i, x in enumerate(json.load(open(os.path.join(base, fn)))) if i % n == shard]
        found = [find(x) for x in items]  # 検索は1件ずつ、2.5秒おき
        with cf.ThreadPoolExecutor(8) as ex:
            res = list(ex.map(one, found))
        json.dump(res, open(os.path.join(out, fn.replace('.json', f'_s{shard}.json')), 'w'), ensure_ascii=False)
        print(fn, shard, len(res), 'search_err', sum(1 for x in res if x.get('search_error')))

if __name__ == '__main__':
    main()
