#!/usr/bin/env python3
"""検索結果から公式サイトらしいURLを1つ選ぶ。使い方: pick.py <biz.json> <search_dir> <out.json>"""
import json, sys, re, glob, unicodedata, urllib.parse
PORTAL = re.compile(r'ekiten|hotpepper|epark|instagram|facebook|twitter|x\.com|tiktok|youtube|ameblo\.jp/(?!)|'
    r'mapion|navitime|itp\.ne\.jp|jorudan|goo\.ne|yahoo|google|petlife|pepy|ペット|wikipedia|tabelog|retty|'
    r'townwork|indeed|baitoru|mynavi|rikunabi|en-japan|doda|job|kyujin|biz-maps|houjin|kaisha|navi|'
    r'pet-hotel\.jp|petsitter-search|torepet|dogrun|oyakudachi|minkou|caloo|byoinnavi|animal-hospital|'
    r'uchinoshippo|rouken-care|ペットホテル|petpet|shiori|hellowork|line\.me|lit\.link|linktr|'
    r'jpnumber|telnavi|jp\.ub|ubereats|amazon|rakuten|minimo|beauty\.|salonboard|ipros|nikkei|'
    r'env\.go\.jp|pref\.|city\.|town\.|lg\.jp|hatena|note\.com|fc2|livedoor|duckduckgo|bing|'
    r'syokuba|ichiba|kakaku|cheaper|alarmbox|gbiz|catr\.jp|ikyu|jalan|tripadvisor|haltaro|dogfriend|'
    r'trimming-salon|dogsalon-search|kurashi|zehitomo|meetsmore|minnano|rehome|pet-home|jmty|'
    r'goodbreeder|town-guide|sewakl|anica|wanyan|1-2-pet|pet-hotel|mypl\.net|petgo|cocole|pet-sos|shitsuke|hotel-search|sitter-search|pet-hotel|epark|hotpepper|petstation|itsumo\.dog|nekojalala|pet-salon\.net|petter\.jp|findglocal|worldorgs|ikeruwan|sorou|dogparkjp|tekuteku|pethomeweb|e-shops\.jp|inudia|baseconnect|pochica|shufoo|toredog|shisetsu-zukan|pet-coo|scarecrow|mintoku|anipita|hug-u|chiicomi|moff-moff|pettosugosu|24u\.jp|spotify|comott|catgroomer|dogportal|dogdrop|petoffice|natural-harvest|pet-ld|wanchan|nyanchan|petsalon-search|petfamily|jobmedley|guppy|dog-life|trimmer|minna|ranking|osusume|matome|hikaku|kuchikomi|1-2-pet|michi-biki|vets-s\.com|shitsuke-portal|trimtrim|localplace|trimmingfan|petmi\.jp|pet-miru|nicozon|pet-hotel-japan|dogoo|petal-pet|homes\.co\.jp|wan-time|pet-systems|rairai|tsujigawa|japanpetsalon|tellogs|kensetumap|onionworld|epark|hotpepper|ekiten|minkou|pet-ld|dogsalon\.jp|pethotel-navi|petsitter-navi|ペット|careshop|houjin|corporation|company|kensaku|search|mapfan|tabelog|navi|map|biz|data|info-|kigyou|jpnumber|trimmingwan|data-link-plus|moshicom|ibiz|salon-pet|petpe|kamiya|dog-trainer-search|inunavi|wanpedia|mapfan|hitosara|homemate|navit-j|'
    r'r\.goope\.jp/(?!)|aeon\.com|petsfirst|coo-and-riku|petplus|ozpet|petcity|wanlife|pecolife', re.I)

def norm(s):
    s = unicodedata.normalize('NFKC', s).lower()
    return re.sub(r'[\s・()（）「」\[\]\-ー_.,、。!！?？\'’&＆/|｜:：~〜]', '', s)

CORP = re.compile(r'株式会社|有限会社|合同会社|一般社団法人|npo法人|特定非営利活動法人|\(株\)|\(有\)')

def key_tokens(name):
    n = unicodedata.normalize('NFKC', name)
    n = CORP.sub(' ', n)
    parts = [norm(p) for p in re.split(r'[\s　・/()（）]+', n) if len(norm(p)) >= 2]
    return parts

def pick(biz, res):
    toks = key_tokens(biz['name'])
    best = None
    for i, (title, url) in enumerate(res):
        host = urllib.parse.urlparse(url).netloc
        if PORTAL.search(host) or PORTAL.search(url.split('?')[0][:60]):
            continue
        t = norm(title) + norm(host)
        hit = [k for k in toks if k in t]
        score = sum(len(k) for k in hit)
        if not hit:
            continue
        if best is None or score > best[0]:
            best = (score, i, title, url)
    return best

def main():
    biz = {b['cid']: b for b in json.load(open(sys.argv[1]))}
    out = []
    for f in sorted(glob.glob(sys.argv[2] + '/s_*')):
        for r in json.load(open(f)):
            b = biz.get(r['cid'])
            if not b:
                continue
            p = pick(b, r.get('results') or [])
            out.append({'cid': r['cid'], 'name': b['name'], 'addr': b['addr'], 'types': b['types'],
                        'n_res': len(r.get('results') or []), 'pick': p and {'title': p[2], 'url': p[3], 'score': p[0]}})
    json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False, indent=0)
    print('items', len(out), 'empty', sum(1 for x in out if not x['n_res']), 'picked', sum(1 for x in out if x['pick']))

if __name__ == '__main__':
    main()
