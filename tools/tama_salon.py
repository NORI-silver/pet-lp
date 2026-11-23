"""東京多摩・島しょ＋神奈川：店舗のトリミングサロン（Nori 2026-11-23「載せる」）を tama_add.json の groomers に shop:true で足す。
元：regsite_pick.py の結果（公式サイトと決まった事業所）のうち、タイトルか短い行にトリミング・サロンの言葉があるもの。
facts は公式サイトの文のまま（tama_build.facts_of）。千葉（#682）と同じ形：services「トリミングサロン」・shop true・cat（猫と書いてあれば）。
  python3 tools/tama_salon.py <pick.json ...>
"""
import json, os, re, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tama_build as B
from urllib.parse import urlparse
HERE = os.path.dirname(os.path.abspath(__file__))
SALON = re.compile(r'トリミング|グルーミング|ドッグサロン|ペットサロン|キャットサロン|犬の美容|dog ?salon|pet ?salon|trimming|grooming', re.I)
def main():
    picks = []
    for fn in sys.argv[1:]: picks += json.load(open(fn))
    out = os.path.join(HERE, 'tama_add.json'); d = json.load(open(out))
    have = {r['id'] for r in d.get('groomers', [])}
    seen, n = set(), 0
    for x in picks:
        if x.get('state') != 'official': continue
        u = x['url']; h = urlparse(u).netloc
        if B.NOT_OFFICIAL.search(h) or B.NOT_OFFICIAL.search(u): continue
        lines = x.get('lines', [])
        if not (SALON.search(x.get('title', '')) or any(len(l) <= 30 and SALON.search(l) for l in lines)): continue
        k = h + urlparse(u).path
        if k in seen: continue
        seen.add(k)
        rid = 'Gt' + hashlib.sha1((x['name'] + x['addr']).encode()).hexdigest()[:7]
        if rid in have: continue
        full, city = B.fix_addr(x)
        text = ' '.join(lines) + ' ' + x.get('title', '')
        row = {'id': rid, 'name': re.sub(r'\s+', ' ', x['name']).strip(), 'prefs': [x['pref']], 'city': city, 'url': u,
               'services': 'トリミングサロン', 'shop': True, 'facts': B.facts_of(x, 'groomers'), 'checked': B.TODAY}
        if re.search(r'猫(?:ちゃん)?(?:の)?(?:トリミング|シャンプー|カット)|キャット(?:トリミング|サロン)|猫(?:ちゃん)?.{0,4}(?:OK|可)', text): row['cat'] = True
        d.setdefault('groomers', []).append(row); have.add(rid); n += 1
    json.dump(d, open(out, 'w'), ensure_ascii=False, indent=1)
    print('salons +', n)
if __name__ == '__main__':
    main()
