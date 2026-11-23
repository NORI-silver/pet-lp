#!/usr/bin/env python3
"""[B] 千葉県の網羅スレッド専用：tools/crawl/chiba/ の queue*.json（公式サイトを読む）と reg*.json（登録一覧を取る）を動かす。
中身は tools/site_snap.py・tools/reg_fetch.py と同じ。何も送らない・書き換えない。site-snap-chiba.yml から動かす。
使い方: python3 tools/chiba_crawl.py <out>"""
import concurrent.futures as cf, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap, reg_fetch

def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crawl', 'chiba')
    jobs = []
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        if fn.startswith('queue') and fn.endswith('.json'):
            items = json.load(open(p))
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
        print('reg', len(logs))

if __name__ == '__main__':
    main()
