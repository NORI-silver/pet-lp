#!/usr/bin/env python3
"""snap の行から、分野と facts（公式サイトの文のまま）を取り出す。使い方: extract.py <biz.json> <out.json> <snap.json>..."""
import json, re, sys, unicodedata

CHK = '2026-11-23'
CATRX = {
    'hotel': re.compile(r'ペットホテル|ホテル|お預かり|宿泊|お泊ま?り|一時預かり|ペットシッターホテル'),
    'trainer': re.compile(r'しつけ|躾|トレーニング|訓練|ドッグスクール|パピー教室|犬の幼稚園|保育園'),
    'sitter': re.compile(r'ペットシッター|シッター|お散歩代行|訪問ケア'),
    'grooming': re.compile(r'出張トリミング|訪問トリミング|トリミングカー|移動トリミング|出張シャンプー|移動式'),
    'rojin': re.compile(r'老犬ホーム|老猫ホーム|老犬介護|終生飼養|終生預かり|長期預かり'),
}
BADV = re.compile(r'詳細は|詳しくは|くわしくは|各施設|施設によって異な|店舗によって異な|お問い?合わせください|リンク先')
BAD = re.compile(r'閉店(いた)?しました|閉店のお知らせ|閉業(いた)?しました|営業を終了(いた)?しました|(サービス|営業)を終了させていただ|新規.{0,6}(受付|受け付け|ご予約).{0,6}(停止|中止|終了|お休み)|現在.{0,4}休業(いた)?しております|移転(いた)?しました')

def nz(s):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', s)).strip()

def short(s, n=90):
    s = nz(s)
    return s if len(s) <= n else s[:n].rstrip() + '…'

LABEL = {
    '営業・受付時間': (re.compile(r'^.{0,6}(営業|受付|受け付け)時間'), re.compile(r'^\s*[:：]?\s*.{0,12}\d{1,2}[:：時]')),
    '定休日': (re.compile(r'^.{0,4}(定休日|休業日|店休日)'), re.compile(r'^\s*[:：]?\s*(毎週|第?[1-5１-５]?)?.{0,3}[月火水木金土日祝]|^\s*[:：]?\s*(年中無休|不定休|なし|無休|年末年始)')),
    '駐車場': (re.compile(r'^.{0,4}(駐車場|駐車スペース|パーキング)'), re.compile(r'^\s*[:：]?\s*.{0,10}(あり|有り|有|\d+台|完備|無料|なし|無し|ございません|コインパーキング)')),
    '用意するもの': (re.compile(r'(狂犬病|混合)?ワクチン.{0,25}(証明書?|接種証)'), re.compile(r'(ご?持参|お持ち|必要|ご提示|ご用意|お願い|確認|お預かりできません|お断り)')),
    '送迎': (re.compile(r'送迎'), re.compile(r'\d+円|無料|km|キロ|エリア内')),
    '対応エリア': (re.compile(r'^.{0,6}(対応|出張|訪問|サービス|営業)(エリア|地域|範囲)'), re.compile(r'[市区町村]|全域|km')),
    'お支払い': (re.compile(r'^.{0,6}(お?支払い?方法|お?支払い?|決済方法|お会計)'), re.compile(r'カード|PayPay|現金|電子マネー|QR|交通系|振込')),
}
PRICE = {
    'hotel': re.compile(r'(1泊|一泊|宿泊|ホテル|お預かり|1日|一日).{0,25}?[\d,]{3,}円|[\d,]{3,}円.{0,10}(1泊|一泊|/泊|／泊)'),
    'trainer': re.compile(r'(レッスン|1回|一回|訓練|トレーニング|しつけ|教室|預かり訓練|月額|入会).{0,25}?[\d,]{3,}円'),
    'sitter': re.compile(r'(1回|一回|基本|訪問|お世話|30分|60分|1時間).{0,25}?[\d,]{3,}円'),
    'grooming': re.compile(r'(シャンプー|カット|トリミング|コース|小型|中型|大型).{0,25}?[\d,]{3,}円'),
    'rojin': re.compile(r'(月額|1ヶ月|1か月|ひと月|入居|1日|年額|終生).{0,25}?[\d,]{3,}円'),
}
CITYRX = re.compile(r'(千葉県)?(.+?郡.+?[町村]|千葉市.+?区|.+?[市町村])')


def lines_of(rec):
    out = []
    for p in rec.get('pages') or []:
        ls = p.get('lines') or []
        for i, l in enumerate(ls):
            out.append((nz(l), nz(ls[i + 1]) if i + 1 < len(ls) else '', p.get('url') or rec.get('final')))
    return out


def find(ls, lab, val, k=''):
    for l, nxt, u in ls:
        if lab.search(l):
            m = lab.search(l)
            rest = l[m.end():]
            if lab.pattern.startswith('(狂犬病') :
                if val.search(l) and len(l) <= 90 and not re.search(r'手伝|代行|連れて行', l):
                    return short(l), u
                continue
            if k == 'お支払い' and re.search(r'ポイント|キャンセル|返金|お返し|場合', l):
                continue
            if rest.strip(' :：') and val.search(rest) and len(l) <= 90:
                return short(l), u
            if not rest.strip(' :：') and nxt and val.search(nxt) and not lab.search(nxt) and len(nxt) <= 80:
                return short(l.rstrip(' :：') + '：' + nxt), u
    return None


def extract(rec, biz):
    ls = lines_of(rec)
    alltext = ' '.join(l for l, _, _ in ls) + ' ' + (rec.get('title') or '')
    cats = [c for c, rx in CATRX.items() if len(rx.findall(alltext)) >= (1 if c in ('grooming', 'rojin') else 2)]
    facts = []
    for k, (lab, val) in LABEL.items():
        r = find(ls, lab, val, k)
        if r:
            facts.append({'k': k, 'v': r[0], 'src': r[1], 'by': 'site', 'checked': CHK})
    prices = {}
    for c, rx in PRICE.items():
        for l, nxt, u in ls:
            if rx.search(l) and len(l) <= 80 and not re.search(r'場合|追加|延長|キャンセル|交通費|割引|オフ', l):
                prices[c] = {'k': '料金', 'v': short(l), 'src': u, 'by': 'site', 'checked': CHK}
                break
    flags = {
        'large': bool(re.search(r'大型犬', alltext)),
        'cat': bool(re.search(r'猫|ねこ|ネコ|キャット', alltext)),
        'senior': bool(re.search(r'シニア|老犬|高齢', alltext)),
        'pickup': bool(re.search(r'送迎', alltext)),
        'bad': bool(BAD.search(alltext)),
    }
    flags['alltext']=alltext[:30000]
    return cats, facts, prices, flags


def main():
    biz = {b['cid']: b for b in json.load(open(sys.argv[1]))}
    out = []
    for f in sys.argv[3:]:
        for rec in json.load(open(f)):
            if rec.get('error') or rec['cid'] not in biz:
                continue
            b = biz[rec['cid']]
            cats, facts, prices, flags = extract(rec, b)
            m = CITYRX.match(nz(b['addr']))
            out.append({'cid': rec['cid'], 'name': b['name'], 'addr': b['addr'], 'city': m.group(2) if m else '',
                        'types': b['types'], 'url': rec.get('final') or rec['url'], 'title': rec.get('title', ''),
                        'cats': cats, 'facts': facts, 'prices': prices, 'alltext': flags.pop('alltext'), 'flags': flags})
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
    import collections
    print(len(out), collections.Counter(c for x in out for c in x['cats']), 'bad', sum(x['flags']['bad'] for x in out))


if __name__ == '__main__':
    main()
