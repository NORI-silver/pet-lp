#!/usr/bin/env python3
"""[B] 地域の網羅スレッド用：site_snap.py・reg_fetch.py を、指定したフォルダの queue*.json・reg*.json で動かす。
共通の site-snap（tools/crawl/ 直下）とは別の置き場にするため。何も送らない。
使い方: python3 tools/region_snap.py <out> <フォルダ>"""
import concurrent.futures as cf, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap, reg_fetch

def main():
    out, qdir = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    regs = []
    for fn in sorted(os.listdir(qdir)):
        p = os.path.join(qdir, fn)
        if fn.startswith('queue') and fn.endswith('.json'):
            with cf.ThreadPoolExecutor(12) as ex:
                res = list(ex.map(site_snap.snap, json.load(open(p))))
            json.dump(res, open(os.path.join(out, fn.replace('queue', 'snap')), 'w'), ensure_ascii=False, indent=1)
            print(fn, len(res), 'errors', sum(1 for x in res if x.get('error')))
        elif fn.startswith('reg') and fn.endswith('.json'):
            regs += json.load(open(p))
    if regs:
        with cf.ThreadPoolExecutor(8) as ex:
            logs = list(ex.map(lambda j: reg_fetch.one(j, out), regs))
        json.dump(logs, open(os.path.join(out, 'reg_log.json'), 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
