#!/usr/bin/env python3
"""[B] 近畿の網羅用：tools/crawl/kinki/ の queue*.json を site_snap.snap で、reg*.json を reg_fetch.one で読む（site-snap-kinki.yml）。
queue の行に "raw": true があればページをそのまま置く（登録簿の一覧など）。何も送らない。"""
import concurrent.futures as cf, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap, reg_fetch

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
                    res.append(site_snap.snap(it)); time.sleep(12)
            else:
                with cf.ThreadPoolExecutor(12) as ex:
                    res = list(ex.map(site_snap.snap, items))
            json.dump(res, open(os.path.join(out, fn.replace('queue', 'snap')), 'w'), ensure_ascii=False, indent=1)
            print(fn, len(res), 'errors', sum(1 for x in res if x.get('error')))
        elif fn.startswith('reg') and fn.endswith('.json'):
            jobs += json.load(open(p))
    if jobs:
        with cf.ThreadPoolExecutor(8) as ex:
            logs = list(ex.map(lambda j: reg_fetch.one(j, out), jobs))
        json.dump(logs, open(os.path.join(out, 'reg_log.json'), 'w'), ensure_ascii=False, indent=1)
        print('reg', len(logs), 'files', sum(len(l['files']) for l in logs))

if __name__ == '__main__':
    main()
