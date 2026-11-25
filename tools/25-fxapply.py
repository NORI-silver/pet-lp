# 一時の補助（T-HT066 が photos.json・photo_permits.json・curated_tokyo_small.json に2つずつ入ったのを1つにする）。使い終わったら消す。
import json
def dedupe(path, key, top=None):
    d = json.load(open(path, encoding='utf-8'))
    lst = d[top] if top else d
    seen, out, rm = set(), [], 0
    for x in lst:
        k = key(x)
        if k in seen: rm += 1; continue
        seen.add(k); out.append(x)
    if top: d[top] = out
    else: d = out
    if rm: json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1 if path.endswith('photos.json') else 1)
    print(path, 'removed', rm)
    return rm
# 元の書き方をそのまま保つため、重複が無いファイルは触らない
import re
def raw_dedupe(path, key, top):
    s = open(path, encoding='utf-8').read()
    d = json.loads(s)
    lst = d[top] if top else d
    seen, out = set(), []
    for x in lst:
        k = key(x)
        if k in seen: continue
        seen.add(k); out.append(x)
    print(path, len(lst), '->', len(out))
    if len(out) == len(lst): return
    if top: d[top] = out
    else: d = out
    # 元の整形（indent・ensure_ascii）を推定して合わせる
    ind = 1 if re.search(r'^\{\n \"', s) or s.startswith('[\n {') or s.startswith('[\n  {') else None
    m = re.match(r'[\[{]\n( +)', s)
    ind = len(m.group(1)) if m else None
    open(path, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=ind) + ('\n' if s.endswith('\n') else ''))
raw_dedupe('tools/photos.json', lambda x: (x['cat'], x['id']), 'items')
raw_dedupe('tools/photo_permits.json', lambda x: (x['cat'], x['id']), 'permits')
raw_dedupe('tools/curated_tokyo_small.json', lambda x: (x['id'], x['file']), None)
