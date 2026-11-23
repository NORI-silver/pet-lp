#!/usr/bin/env python3
"""候補を pet-lp の tools/*.json に足す。使い方: apply.py <pet-lp> <cand.json> <ex_fb.json> <fb_sel.json> <csv>"""
import json, re, sys, urllib.parse, unicodedata, os, csv
root, candf, exfb, fbsel, csvf = sys.argv[1:6]
CHK = '2026-11-23'
FILES = {'hotel': ('hotels', 'hotels', 'PHC'), 'trainer': ('trainers', 'trainers', 'TC'), 'sitter': ('sitters', 'sitters', 'SC'),
         'grooming': ('grooming', 'groomers', 'GC'), 'rojin': ('rojin', 'homes', 'RC')}
LABEL = {'hotel': 'ペットホテル', 'trainer': 'ドッグトレーナー', 'sitter': 'ペットシッター', 'grooming': '出張トリミング', 'rojin': '老犬ホーム'}

cands = json.load(open(candf))
ex = {x['cid']: x for x in json.load(open(exfb))}
for cid, cats in json.load(open(fbsel)):
    x = ex.get(cid)
    if not x or x['flags']['bad']:
        continue
    for c in cats:
        facts = list(x['facts'])
        if c in x['prices']:
            facts.insert(0, x['prices'][c])
        cands.append({'cat': c, 'cid': cid, 'name': x['name'], 'city': x['city'], 'url': x['url'], 'title': x['title'],
                      'facts': facts, 'flags': x['flags'], 'types': [], 'alltext': x.get('alltext', '')})
# alltext for registry candidates
allt = {}
for f in sys.argv[6:]:
    for x in json.load(open(f)):
        allt[x['cid']] = x.get('alltext', '')


def host(u):
    return urllib.parse.urlparse(u).netloc.replace('www.', '')

data = {c: json.load(open(f'{root}/tools/{f}.json')) for c, (f, k, p) in FILES.items()}
CHAIN = re.compile(r'aeonpet|happybell|pet-ss|petsitter\.co|intopet|oneluke|toukatu|olympic|nekobeya|penguinsitter|ts-alamode|pet-onelove|onedo|dogschool\.co|pechika|ahb\.jpn|pepica|lowevivi|news-dog|ks-product|wiz-dog')
seen = {}
for c, (f, k, p) in FILES.items():
    for x in data[c][k]:
        if '千葉県' in (x.get('prefs') or []) or True:
            h = host(x.get('url') or '')
            if h and not CHAIN.search(h):
                seen[(c, h)] = 1
            seen[(c, unicodedata.normalize('NFKC', x['name']).replace(' ', ''))] = 1
added = []
rows = []
num = {c: 0 for c in FILES}
for c, (f, k, p) in FILES.items():
    num[c] = sum(1 for x in data[c][k] if str(x['id']).startswith(p))
for x in cands:
    c = x['cat']; f, k, p = FILES[c]
    h = host(x['url']); nm = unicodedata.normalize('NFKC', x['name']).replace(' ', '')
    if (c, nm) in seen or (not CHAIN.search(h) and (c, h) in seen):
        continue
    seen[(c, nm)] = 1; seen[(c, h)] = 1
    num[c] += 1
    t = x.get('alltext') or allt.get(x['cid'], '')
    facts = []
    ks = set()
    for ft in x['facts']:
        if ft['k'] in ks:
            continue
        ks.add(ft['k']); facts.append(ft)
    city = x['city']
    e = {'id': f'{p}{num[c]:03d}', 'name': x['name'], 'prefs': ['千葉県']}
    if c == 'sitter':
        area = next((ft['v'] for ft in facts if ft['k'] == '対応エリア'), '')
        e.update({'area': city if not area else city, 'url': x['url'], 'chain': 'indie'})
    else:
        e.update({'city': city, 'url': x['url']})
    if c == 'hotel':
        e['services'] = 'ペットホテル'
        if re.search(r'猫.{0,12}(ホテル|お預かり|宿泊|1泊|一泊)|(ホテル|お預かり|宿泊|1泊|一泊).{0,15}(猫|ねこ|ネコ)', t):
            e['cat'] = True
        if re.search(r'大型犬.{0,20}(\d[\d,]*円|OK|ＯＫ|可能|お預かり)', t) and not re.search(r'大型犬.{0,12}(不可|お断り|ご相談|できません|お受けして(い)?ません)', t):
            e['large'] = True; e['large_basis'] = '文'
        if re.search(r'送迎', t):
            if any(ft['k'] == '送迎' for ft in facts):
                e['pickup'] = True
    elif c == 'trainer':
        sv = [w for w in ['しつけ教室', 'パピー教室', '出張トレーニング', '預かり訓練', '犬の幼稚園', '問題行動の相談'] if w in t or (w == '問題行動の相談' and re.search(r'問題行動|噛み|吠え', t))]
        e['services'] = '、'.join(sv) or '犬のしつけ'
        e['src'] = x['url']; e['checked'] = CHK
    elif c == 'grooming':
        area = next((ft['v'] for ft in facts if ft['k'] == '対応エリア'), '')
        e['area'] = area or (city + 'と周辺')
        e['services'] = '出張トリミング'
        if re.search(r'トリミングカー|トリミング車|移動式', t):
            e['car'] = True
    elif c == 'rojin':
        e['animals'] = [a for a in ['犬', '猫'] if a in t] or ['犬']
    e['facts'] = facts
    e['checked'] = CHK
    data[c][k].append(e)
    added.append(e)
    rows.append([LABEL[c], e['id'], e['name'], '千葉県', city, x['url'], CHK])
for c, (f, k, p) in FILES.items():
    json.dump(data[c], open(f'{root}/tools/{f}.json', 'w'), ensure_ascii=False, indent=1)
    open(f'{root}/tools/{f}.json', 'a').write('\n')
with open(csvf, 'a', newline='') as fh:
    csv.writer(fh).writerows(rows)
import collections
print(len(added), collections.Counter(r[0] for r in rows))
