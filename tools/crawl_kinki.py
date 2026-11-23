#!/usr/bin/env python3
"""[B] 近畿の網羅用：tools/crawl/kinki/ の queue*.json を site_snap.snap で、reg*.json を reg_fetch.one で読む（site-snap-kinki.yml）。
queue の行に "raw": true があればページをそのまま置く（登録簿の一覧など）。何も送らない。"""
import concurrent.futures as cf, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap, reg_fetch

_orig_links = site_snap.links_of
def _safe_links(h, base):
    try:
        return _orig_links(h, base)
    except Exception:
        return []
site_snap.links_of = _safe_links

def safe_snap(it):
    try:
        return site_snap.snap(it)
    except Exception as e:
        return dict(it, error=str(e)[:200])

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
    os.makedirs(out, exist_ok=True)
    qdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crawl', 'kinki')
    jobs = []
    for fn in sorted(os.listdir(qdir)):
        p = os.path.join(qdir, fn)
        if fn.startswith('queue') and fn.endswith('.json'):
            items = json.load(open(p))
            if fn.startswith('queue_q'):  # 検索はひとつずつ間をあけて（続けて聞くと結果が空になる）
                res = []
                for it in items:
                    res.append(safe_snap(it)); time.sleep(12)
            else:
                with cf.ThreadPoolExecutor(12) as ex:
                    res = list(ex.map(safe_snap, items))
            json.dump(res, open(os.path.join(out, fn.replace('queue', 'snap')), 'w'), ensure_ascii=False, indent=1)
            print(fn, len(res), 'errors', sum(1 for x in res if x.get('error')))
        elif fn.startswith('post') and fn.endswith('.json'):  # POST で配るオープンデータ（京都市）
            import urllib.request, urllib.parse
            for it in json.load(open(p)):
                try:
                    req = urllib.request.Request(it['url'], data=urllib.parse.urlencode(it['form']).encode(), headers={'User-Agent': site_snap.UA})
                    raw = urllib.request.urlopen(req, timeout=60).read()
                    d = os.path.join(out, 'reg', it['key']); os.makedirs(d, exist_ok=True)
                    open(os.path.join(d, it['name']), 'wb').write(raw); print('post', it['key'], len(raw))
                except Exception as e:
                    print('post', it['key'], e)
        elif fn.startswith('reg') and fn.endswith('.json'):
            jobs += json.load(open(p))
    if jobs:
        with cf.ThreadPoolExecutor(8) as ex:
            logs = list(ex.map(lambda j: reg_fetch.one(j, out), jobs))
        json.dump(logs, open(os.path.join(out, 'reg_log.json'), 'w'), ensure_ascii=False, indent=1)
        print('reg', len(logs), 'files', sum(len(l['files']) for l in logs))

if __name__ == '__main__':
    main()
