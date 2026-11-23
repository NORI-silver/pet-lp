#!/usr/bin/env python3
"""ex*.json（extract.py の出力）から、分野ごとの新しい掲載候補を作る。使い方: build.py <pet-lp> <out.json> <ex.json>..."""
import json, re, sys, unicodedata, urllib.parse, collections, importlib.util, os
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pick', HERE + '/pick.py'); pk = importlib.util.module_from_spec(spec); spec.loader.exec_module(pk)

STRONG = {
    'hotel': re.compile(r'ペットホテル|1泊|一泊|宿泊|お泊ま?り|ホテル料金|ホテルのご利用'),
    'trainer': re.compile(r'しつけ教室|しつけ方教室|ドッグトレーニング|ドッグトレーナー|家庭犬訓練|訓練所|ドッグスクール|しつけレッスン|出張トレーニング|パピー教室|預かり訓練'),
    'sitter': re.compile(r'ペットシッター|キャットシッター|散歩代行|お散歩代行'),
    'grooming': re.compile(r'出張トリミング|訪問トリミング|トリミングカー|移動トリミング|出張シャンプー'),
    'rojin': re.compile(r'老犬ホーム|老猫ホーム|老犬介護施設|終生預かり|終身預かり'),
}
NEED = {'hotel': 2, 'trainer': 2, 'sitter': 2, 'grooming': 1, 'rojin': 1}
NOTPET = re.compile(r'建設|工務店|不動産|リフォーム|歯科|美容室(?!.*(犬|ペット|ドッグ))|ネイル|整骨|税理士|司法書士|塗装|株式会社リーベ')
SERV = {'hotel': 'ペットホテル', 'trainer': '犬のしつけ', 'sitter': 'ペットシッター', 'grooming': '出張トリミング', 'rojin': '老犬ホーム・老猫ホーム'}


def norm(s):
    return pk.norm(s)


def existing(root):
    names, hosts = set(), set()
    for f, k in [('trainers', 'trainers'), ('hotels', 'hotels'), ('sitters', 'sitters'), ('grooming', 'groomers'), ('rojin', 'homes')]:
        for x in json.load(open(f'{root}/tools/{f}.json'))[k]:
            names.add((f, norm(x['name'])))
            u = x.get('url') or ''
            p = urllib.parse.urlparse(u)
            hosts.add((f, p.netloc.replace('www.', '')))
    return names, hosts

FILE = {'hotel': 'hotels', 'trainer': 'trainers', 'sitter': 'sitters', 'grooming': 'grooming', 'rojin': 'rojin'}


def main():
    root = sys.argv[1]
    names, hosts = existing(root)
    recs = []
    for f in sys.argv[3:]:
        recs += json.load(open(f))
    snaps = {}
    out = []
    why = collections.Counter()
    for r in recs:
        host = urllib.parse.urlparse(r['url']).netloc
        if pk.PORTAL.search(host):
            why['portal'] += 1; continue
        if r['flags']['bad']:
            why['closed?'] += 1; continue
        GEN = re.compile(r'^(ペット|サロン|ドッグ|トリミング|ホテル|ショップ|ハウス|dog|salon|pet|shop|house|ペットショップ|ペットサロン|ドッグサロン|トリミングサロン|ペットホテル|ペットシッター|シッター|千葉|店|本店|の|犬の美容室|美容室|わんちゃん|ワンちゃん|ねこ|cat|trimming|hotel|and|the|株式会社|有限会社|合同会社)$')
        toks = [t for t in pk.key_tokens(r['name']) if not GEN.match(t) and len(t) >= 2]
        full = norm(pk.CORP.sub('', unicodedata.normalize('NFKC', r['name'])))
        hay = norm(r['title']) + ' ' + norm(r.get('alltext', '')[:6000])
        if not (full in hay or any(t in hay for t in toks)):
            why['name not on page'] += 1; continue
        if NOTPET.search(r['title']):
            why['not pet'] += 1; continue
        txt = r.get('alltext', '')
        head = r['name'] + ' ' + r['title']
        cnt = {c: len(rx.findall(txt)) for c, rx in STRONG.items()}
        cats = []
        if re.search(r'ホテル|預かり|お泊ま?り', head) or re.search(r'(1泊|一泊|宿泊).{0,20}[\d,]{3,}円', txt):
            if cnt['hotel'] >= 2 and not re.search(r'シッター', head): cats.append('hotel')
        elif (txt.count('ペットホテル') >= 2 or cnt['hotel'] >= 4) and not re.search(r'シッター', head): cats.append('hotel')
        if '訓練' in r['types'] or re.search(r'しつけ|躾|トレーニング|トレーナー|訓練|ドッグスクール|dog ?school|training', head, re.I):
            if cnt['trainer'] >= 2: cats.append('trainer')
        if re.search(r'シッター|sitter', head, re.I) and cnt['sitter'] >= 2: cats.append('sitter')
        if re.search(r'出張|訪問|トリミングカー|移動', head) and cnt['grooming'] >= 1: cats.append('grooming')
        if re.search(r'老犬|老猫|シニア', head) and cnt['rojin'] >= 1 or cnt['rojin'] >= 4: cats.append('rojin')
        if not cats:
            why['no category'] += 1; continue
        for c in cats:
            p = urllib.parse.urlparse(r['url'])
            if (FILE[c], norm(r['name'])) in names or ((FILE[c], p.netloc.replace('www.', '')) in hosts and not re.search(r'aeonpet|happybell|pet-ss|petsitter\.co|intopet|oneluke|toukatu|olympic|nekobeya|penguinsitter|ts-alamode|pet-onelove|onedo|dogschool\.co|pechika', p.netloc)):
                why['already ' + c] += 1; continue
            facts = list(r['facts'])
            if c in r['prices']:
                facts.insert(0, r['prices'][c])
            if c != 'hotel':
                facts = [f for f in facts if f['k'] != '送迎' or c == 'trainer']
            out.append({'cat': c, 'cid': r['cid'], 'name': r['name'], 'city': r['city'], 'url': r['url'], 'title': r['title'],
                        'facts': facts, 'flags': r['flags'], 'types': r['types']})
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
    print(len(out), collections.Counter(x['cat'] for x in out), dict(why))


if __name__ == '__main__':
    main()
