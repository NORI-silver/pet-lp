#!/usr/bin/env python3
"""[B] 千葉県の網羅：登録簿の事業所の名前と市区町村で検索し、上位の結果（見出しとURL）だけを書く（site-search-chiba.yml）。
検索は Yahoo! JAPAN（2.5秒おき）→ だめなら DuckDuckGo。どれが公式サイトかは人（AI）が結果を見て決める。何も送らない。
使い方: python3 tools/chiba_search.py <chunk.json> <out.json> [間隔秒]"""
import json, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import west_search as ws

def main():
    items = json.load(open(sys.argv[1]))
    gap = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
    out = []
    for it in items:
        r = dict(it)
        for name, fn in (('yahoo', ws.yahoo), ('ddg', ws.ddg)):
            try:
                got = fn(it['q'])
            except Exception as e:
                got = []; r.setdefault('err', []).append(name + ' ' + str(e)[:80])
            if got:
                r['engine'] = name; r['results'] = got[:10]; break
            time.sleep(gap)
        out.append(r)
        time.sleep(gap)
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
    print(sys.argv[1], len(out), 'empty', sum(1 for x in out if not x.get('results')))

if __name__ == '__main__':
    main()
