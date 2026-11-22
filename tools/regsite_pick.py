#!/usr/bin/env python3
"""[B] 登録一覧の事業所の公式サイトさがし（tools/regsite.py の結果）から、載せる候補を分野ごとに分ける（Nori 2026-11-22「漏れ一切なくね」）。
公式サイトと決めるのは、読んだページに登録一覧の住所（町名まで）か、事業所名がそのまま書いてあるときだけ。
分野（ホテル・シッター・しつけ・老犬ホーム・出張トリミング）は公式サイトの文の言葉で決め、
料金・営業時間・定休日・駐車場・ワクチン・対応エリアなどの行は公式サイトの文のまま facts の候補にする（推測で埋めない）。
何も送らない・書き換えない。出力は人（AI）が確かめてから各分野のデータに入れる。
使い方：python3 tools/regsite_pick.py <結果のフォルダ> <出力.json>
"""
import json, os, re, sys, unicodedata, glob

def N(s):
    return unicodedata.normalize('NFKC', s or '')

def norm(s):
    return re.sub(r'[\s・･\-‐－ー―()（）「」『』【】\[\]〜~!！?？.,、。]', '', N(s)).lower()

CAT = {
    'sitter': re.compile(r'ペットシッター|キャットシッター|シッターサービス|訪問(?:して|で)?お世話|お留守番.*(?:訪問|伺)'),
    'trainer': re.compile(r'しつけ教室|しつけ方教室|ドッグトレーニング|ドッグトレーナー|家庭犬(?:の)?(?:しつけ|訓練)|出張(?:しつけ|トレーニング|訓練)|預(?:け|かり)訓練|パピー(?:クラス|教室)|訓練所'),
    'hotel': re.compile(r'ペットホテル|ドッグホテル|キャットホテル|猫(?:の)?ホテル|犬(?:の)?ホテル|ホテル(?:料金|利用|のご案内)|お預かり(?:料金|サービス)|1泊|一泊'),
    'rojin': re.compile(r'老犬ホーム|老猫ホーム|終生(?:飼養|預かり|お預かり)|介護(?:の)?お預かり|シニア(?:犬)?ホーム'),
    'grooming': re.compile(r'出張トリミング|訪問トリミング|移動トリミング|トリミングカー|出張シャンプー|訪問美容'),
}
CLOSED = re.compile(r'閉店(?:しました|いたしました)|閉業|営業を終了|サービスを終了|休業(?:中|しております)|新規(?:の)?(?:お客様|受付|ご予約).{0,8}(?:停止|中止|終了|お断り)')
FACT = [
    ('料金', re.compile(r'(?:[0-9,，]{3,}|[0-9]+,[0-9]{3})\s*円|円(?:\(税|（税)|料金')),
    ('営業時間', re.compile(r'営業時間|受付時間|営業[:：]|OPEN|[0-9]{1,2}[:：][0-9]{2}\s*[〜~～\-－]\s*[0-9]{1,2}[:：][0-9]{2}')),
    ('定休日', re.compile(r'定休日|休業日|お休み[:：]|定休')),
    ('駐車場', re.compile(r'駐車場|駐車スペース|パーキング')),
    ('ワクチン', re.compile(r'ワクチン|狂犬病|予防接種|混合')),
    ('対応エリア', re.compile(r'対応エリア|対応地域|サービスエリア|訪問エリア|出張エリア|対象エリア|対応区域')),
    ('送迎', re.compile(r'送迎|お迎え|送り迎え')),
    ('受ける動物', re.compile(r'大型犬|中型犬|小型犬|超大型|kg|ｋｇ|キロ|猫|うさぎ|ウサギ|小動物|鳥')),
]

def addr_keys(addr):
    a = N(addr)
    m = re.match(r'(?:東京都|神奈川県|埼玉県|千葉県|茨城県|栃木県|群馬県)?(.+?[市区町村])(.+?)(?:[0-9一二三四五六七八九十]|丁目|$)', a)
    if not m:
        return []
    city, town = m.group(1), m.group(2)
    town = re.sub(r'[0-9０-９丁目番地号の\-－‐]+$', '', town)
    keys = []
    if len(town) >= 2:
        keys.append(norm(city.split('市')[-1] if False else city) + norm(town))
        keys.append(norm(town))
    return keys

def official(it, s):
    text = ' '.join(' '.join(p.get('lines', [])) + ' ' + p.get('title', '') for p in s.get('pages', []) if not p.get('error'))
    t = norm(text)
    nm = norm(it['name'])
    keys = addr_keys(it['addr'])
    by_addr = any(k and k in t for k in keys[:1]) or (len(keys) > 1 and keys[1] in t and norm(it.get('city', '')) in t)
    by_name = len(nm) >= 4 and nm in t
    return by_addr, by_name, text

def facts_of(s):
    out = {}
    for p in s.get('pages', []):
        for l in p.get('lines', []) or []:
            l = l.strip()
            if len(l) < 4 or len(l) > 200:
                continue
            for k, rx in FACT:
                if rx.search(l):
                    out.setdefault(k, [])
                    if len(out[k]) < 6 and all(l != x['v'] for x in out[k]):
                        out[k].append({'v': l, 'src': p.get('url')})
    return out

def main():
    src, dst = sys.argv[1], sys.argv[2]
    items = []
    for fn in sorted(glob.glob(os.path.join(src, '**', 'regq_*.json'), recursive=True)):
        items += json.load(open(fn))
    res = []
    stat = {'all': len(items), 'search_error': 0, 'no_cand': 0, 'not_official': 0, 'closed': 0, 'official': 0}
    for it in items:
        if it.get('search_error'):
            stat['search_error'] += 1
        snaps = [s for s in it.get('snaps', []) if not s.get('error')]
        if not snaps:
            stat['no_cand'] += 1
            res.append({**{k: it[k] for k in ('id', 'pref', 'city', 'name', 'addr', 'types')}, 'state': 'no_site'})
            continue
        best = None
        for s in snaps:
            a, n, text = official(it, s)
            if a or n:
                best = (s, a, n, text)
                break
        if not best:
            stat['not_official'] += 1
            res.append({**{k: it[k] for k in ('id', 'pref', 'city', 'name', 'addr', 'types')}, 'state': 'unsure', 'cands': [s.get('final') or s.get('url') for s in snaps]})
            continue
        s, a, n, text = best
        cats = [c for c, rx in CAT.items() if rx.search(text)]
        closed = bool(CLOSED.search(text))
        stat['closed' if closed else 'official'] += 1
        res.append({**{k: it[k] for k in ('id', 'pref', 'city', 'name', 'addr', 'types')},
                    'state': 'closed' if closed else 'official', 'match': ('addr' if a else '') + ('name' if n else ''),
                    'url': s.get('final') or s.get('url'), 'title': s.get('title', ''), 'cats': cats, 'facts': facts_of(s)})
    json.dump(res, open(dst, 'w'), ensure_ascii=False, indent=0)
    import collections
    c = collections.Counter(c for r in res if r['state'] == 'official' for c in (r['cats'] or ['none']))
    print(stat, dict(c))

if __name__ == '__main__':
    main()
