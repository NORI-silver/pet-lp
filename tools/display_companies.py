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

# 営業時間・当日予約（Nori 2026-10-31「翌日以降対応の事業者や営業時間が終わっている事業者は候補に上がらないように」）
# hours：受け付け・送迎の時間（"8-20"。24時間は "0-24"。分からなければ ""）。flex：時間外も相談できると書いてある（お迎えの時刻では外さない）
# closed：定休日（0=日〜6=土）。lead_days：何日前までの予約か（0=当日も可、1=前日まで、null=分からない）。cut：当日予約の締め切り時刻
WD = {'日': 0, '月': 1, '火': 2, '水': 3, '木': 4, '金': 5, '土': 6}
FIX = {  # 文の形がまちまちなものは、ダッシュボードの記載を見て手で直す
    'Dd8c07a8': {'hours': '8-18'},                      # 8〜12時・13〜18時
    'D3c85024': {'hours': '9-21', 'closed': [4]},       # 曜日で少し違う。木曜定休
    'D1f53c72': {'hours': '9-19', 'closed': [0, 6]},    # 当面は月〜金のみ
    'Daf1e25b': {'closed': [0, 6]},                     # 平日のみ
    'D1c2a5e3': {'closed': [0, 6]},                     # 平日のみ
    'D7847612': {'lead_days': None},                    # 平日は当日もありうる。日祝は前日まで
    'D8001263': {'lead_days': None},                    # 前日までは「ペットだけのとき」だけ
    'De3f35f2': {'lead_days': None},                    # 当日は「難しいことが多い」（できないとは書いていない）
    'Dcda25a4': {'lead_days': 1},                       # 原則前日まで
}

def schedule(c, did):
    h, l = c.get('hours', ''), c.get('lead', '')
    out = {'hours': '', 'flex': bool(re.search(r'相談|依頼で|事前予約で可|依頼があれば', h)), 'closed': [], 'lead_days': None, 'cut': None}
    if re.search(r'24時間', h) and not re.search(r'電話受付24時間|Web予約は24時間|緊急は24時間', h): out['hours'] = '0-24'
    else:
        m = re.search(r'(\d{1,2}):?(\d{2})?\s*[〜~-]\s*(\d{1,2}):?(\d{2})?', h)
        if m: out['hours'] = '%d-%d' % (int(m.group(1)), int(m.group(3)) + (1 if m.group(4) and m.group(4) != '00' else 0))
    for w in re.findall(r'([日月火水木金土])曜定休', h): out['closed'].append(WD[w])
    if re.search(r'当日[^。、]*?(可|対応|あり|相談)', l + h) and not re.search(r'不可|難しい', l): out['lead_days'] = 0
    if re.search(r'前日まで(に|の)?予約|^前日まで$|前日まで必須', l): out['lead_days'] = 1
    m = re.search(r'(\d)日前まで', l)
    if m: out['lead_days'] = int(m.group(1))
    m = re.search(r'当日[^）]*?(\d{1,2})時まで', l + h)
    if m: out['cut'] = int(m.group(1)); out['lead_days'] = 0
    out.update(FIX.get(did, {}))
    return out

def main(master, comp):
    ms = json.load(open(master, encoding='utf-8'))
    cs = {c['id']: c for c in json.load(open(comp, encoding='utf-8'))}
    out = []
    for m in ms:
        if m['status'] != '掲載候補' or m['id'] in SKIP: continue  # 全国の掲載候補（Nori 2026-10-31「全国にして。絞らないで」）
        c = cs.get(m['id'], {})
        row = {'id': m['id'], 'name': m['name'], 'pref': m['pref'], 'areas': areas(c, m) if m['book_area'] else [], 'pay': pay(c)}
        row.update(schedule(c, m['id']))
        assert not re.search(r'\d{2,4}-\d{2,4}-\d{3,4}|@', json.dumps(row, ensure_ascii=False)), row  # 電話番号・メールは入れない
        out.append(row)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'display_companies.json')
    json.dump({'_説明': '予約の候補カードに表示だけする会社（依頼は送れない）。tools/display_companies.py で作る。出すかどうかは booking/Code.gs の CONFIG.SHOW_ALL_CANDIDATES', 'companies': out},
              open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(out), '社', {p: sum(p in r['areas'] for r in out) for p in PREFS})

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
