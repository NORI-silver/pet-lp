#!/usr/bin/env python3
"""[B] 地域の網羅：登録簿の事業者の名前と市区町村で検索し、上位の結果（見出しとURL）だけを書く（site-search-nkt.yml）。
どれが公式サイトかは人（AI）が結果を見て決める。何も送らない。
使い方: python3 tools/region_search.py <chunk.json> <out.json> [間隔秒]"""
import json, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap

def main():
    items = json.load(open(sys.argv[1]))
    gap = float(sys.argv[3]) if len(sys.argv) > 3 else 5
    out = []
    for it in items:
        r = site_snap.search({'q': it['q']})
        r['cid'] = it['cid']
        if not r.get('results') and not r.get('error'):
            time.sleep(gap * 4)  # 空なら少し待ってもう一度
            r2 = site_snap.search({'q': it['q']}); r2['cid'] = it['cid']; r2['retry'] = 1; r = r2
        out.append(r)
        time.sleep(gap)
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
    print(sys.argv[1], len(out), 'empty', sum(1 for x in out if not x.get('results')))

if __name__ == '__main__':
    main()
