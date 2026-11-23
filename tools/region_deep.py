#!/usr/bin/env python3
"""[B] 地域の網羅スレッド用：候補の公式サイトを、トップと「料金・ホテル・アクセス・よくある質問」などのページ（最大10）まで読み、
確かめに要る行だけを書き出す。site_snap.py の読み方を使う（site_snap.py は変えない）。何も送らない。
使い方: python3 tools/region_deep.py <in.json [{cid,url}]> <out.json>"""
import concurrent.futures as cf, json, re, sys, os, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap as S

SUB = re.compile(r'price|fee|ryokin|料金|menu|メニュー|access|アクセス|about|company|会社|店舗|shop|info|概要|hotel|ホテル|stay|お泊|預か|training|しつけ|school|lesson|レッスン|trim|groom|service|サービス|area|エリア|faq|qa|よくある|質問|flow|流れ|guide|利用|plan|プラン|system|システム|course|コース|sitter|シッター|care|介護|老犬|rule|規約|注意', re.I)

def links(h, base):
    host = urllib.parse.urlparse(base).netloc.replace('www.', '')
    out = []
    for href, label in re.findall(r'(?is)<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', h):
        u = urllib.parse.urljoin(base, href)
        p = urllib.parse.urlparse(u)
        if p.netloc.replace('www.', '') != host or re.search(r'\.(jpg|jpeg|png|pdf|gif|zip|webp)$', p.path, re.I):
            continue
        lab = re.sub(r'<[^>]+>', '', label)
        if (SUB.search(urllib.parse.unquote(p.path)) or SUB.search(lab)) and u not in out and u.rstrip('/') != base.rstrip('/'):
            out.append(u)
    return out

def page(u):
    h, f = S.get(u)
    return h, f, {'url': f, 'title': S.title_of(h), 'lines': [l for l in S.text_of(h) if S.KEY.search(l) and len(l) < 240][:150]}

def one(item):
    r = dict(item); pages = []; seen = set(); cand = []
    p = urllib.parse.urlparse(item['url'])
    for u in [item['url'], f'{p.scheme}://{p.netloc}/']:
        if u.rstrip('/') in seen: continue
        try:
            h, f, pg = page(u)
        except Exception as e:
            pages.append({'url': u, 'error': str(e)[:120]}); continue
        seen.add(u.rstrip('/')); seen.add(f.rstrip('/')); pages.append(pg)
        cand += [x for x in links(h, f) if x not in cand]
    for u in cand:
        if len(pages) >= 12: break
        if u.rstrip('/') in seen: continue
        seen.add(u.rstrip('/'))
        try:
            pages.append(page(u)[2])
        except Exception as e:
            pages.append({'url': u, 'error': str(e)[:120]})
    r['pages'] = pages
    return r

if __name__ == '__main__':
    items = json.load(open(sys.argv[1]))
    with cf.ThreadPoolExecutor(10) as ex:
        res = list(ex.map(one, items))
    json.dump(res, open(sys.argv[2], 'w'), ensure_ascii=False)
    print(len(res), 'pages', sum(len(x['pages']) for x in res))
