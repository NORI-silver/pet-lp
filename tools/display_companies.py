#!/usr/bin/env python3
"""予約の候補カードに「表示だけ」で出す会社の一覧を作る（Nori 2026-10-31「候補の事業者を全部出して。依頼は送れないように」）。

  python3 tools/display_companies.py <事業者マスター master.json> <ダッシュボード companies.json>
  → tools/display_companies.json を書き直す。そのあと python3 tools/gen_areas.py . で Code.gs に入る。

ここに入る会社は予約の依頼を受けられない（提携先シートに無いので、送信の対象にならない）。
名前・対応する都県・お支払い方法だけを入れる。電話番号・メールなどの連絡先は入れない（リポジトリは公開）。
"""
import json, os, re, sys

PREFS = ['東京', '神奈川', '埼玉', '千葉']
# 予約の提携先（提携先シートの P002・P003）と同じ会社は、本物のカードがあるので入れない
SKIP = {'Dbcb8b8d', 'Da968571'}
WORDS = {'東京': ['東京', '23区', '多摩', '町田'], '神奈川': ['神奈川', '横浜', '川崎', '湘南', '相模原'],
         '埼玉': ['埼玉', '所沢', '朝霞', '和光', '川口'], '千葉': ['千葉', '松戸', '柏', '流山', '野田']}
ALL = ['首都圏', '関東', '全国']

def areas(c, m):
    own = m['pref'].rstrip('都府県')
    text = re.sub(r'（[^）]*シートより）|緊急は全国', '', c.get('area', ''))
    out = {own}
    if any(w in text for w in ALL): out |= set(PREFS)
    for p, ws in WORDS.items():
        if any(w in text for w in ws): out.add(p)
    return [p for p in PREFS if p in out]

def pay(c):
    t = c.get('pay', '')
    return '' if not t or re.search(r'不明|未転記|見積', t) else t

def main(master, comp):
    ms = json.load(open(master, encoding='utf-8'))
    cs = {c['id']: c for c in json.load(open(comp, encoding='utf-8'))}
    out = []
    for m in ms:
        if m['status'] != '掲載候補' or not m['book_area'] or m['id'] in SKIP: continue
        c = cs.get(m['id'], {})
        row = {'id': m['id'], 'name': m['name'], 'areas': areas(c, m), 'pay': pay(c)}
        assert not re.search(r'\d{2,4}-\d{2,4}-\d{3,4}|@', json.dumps(row, ensure_ascii=False)), row  # 電話番号・メールは入れない
        out.append(row)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'display_companies.json')
    json.dump({'_説明': '予約の候補カードに表示だけする会社（依頼は送れない）。tools/display_companies.py で作る。出すかどうかは booking/Code.gs の CONFIG.SHOW_ALL_CANDIDATES', 'companies': out},
              open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(out), '社', {p: sum(p in r['areas'] for r in out) for p in PREFS})

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
