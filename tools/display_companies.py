#!/usr/bin/env python3
"""予約の候補カードに「表示だけ」で出す会社の一覧を作る（Nori 2026-10-31「候補の事業者を全部出して。依頼は送れないように」）。

  python3 tools/display_companies.py <事業者マスター master.json> <ダッシュボード companies.json> [<料金表 tariffs.json>] [<出典つきマスター facts.json>]
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
ALL = ['首都圏', '関東']  # 「全国」はお迎えの都県には入れない（長距離の輸送のこと。Nori 2026-10-31「大阪で全国の会社が出た」）
# 1都3県のほかの道府県（お迎えの都道府県でしぼる。Nori 2026-10-31「住所に合う会社を料金つきで」）
PREF47 = ['北海道', '青森', '岩手', '宮城', '秋田', '山形', '福島', '茨城', '栃木', '群馬', '埼玉', '千葉', '東京', '神奈川', '新潟', '富山', '石川', '福井', '山梨', '長野', '岐阜',
          '静岡', '愛知', '三重', '滋賀', '京都', '大阪', '兵庫', '奈良', '和歌山', '鳥取', '島根', '岡山', '広島', '山口', '徳島', '香川', '愛媛', '高知', '福岡', '佐賀', '長崎', '熊本',
          '大分', '宮崎', '鹿児島', '沖縄']
KANSAI = ['大阪', '京都', '兵庫', '奈良', '滋賀', '和歌山']
WORDS2 = {'兵庫': ['神戸', '西宮', '芦屋', '宝塚', '尼崎', '川西'], '京都': ['宇治', '亀岡', '木津川'], '茨城': ['古河', '坂東', '五霞', '牛久'],
          '栃木': ['小山', '野木'], '群馬': ['館林'], '千葉': ['下総']}
# お店（営業所）のおおよその位置（市区町村・町名の代表点）。迎車・回送の距離と、遠すぎる会社を外すのに使う。分からない会社は入れない
SHOP = {
    'D400f012': [35.735, 139.475], 'Dea620d5': [35.684, 139.876], 'D1e44e13': [35.588, 139.672], 'Da5a2701': [35.688, 139.787], 'D355c31f': [35.643, 139.698],
    'D7c32399': [35.548, 139.753], 'Dbe5cb84': [35.659, 139.684], 'D0d1c8b4': [35.775, 139.804], 'D692c9a6': [35.802, 139.808], 'D7138c0d': [35.616, 139.653],
    'D7922e74': [35.690, 139.692], 'D0d611b0': [35.352, 139.497], 'De65cb2d': [35.513, 139.433], 'D63b09f7': [35.604, 139.507], 'D945f580': [35.420, 139.660],
    'D5598693': [35.441, 139.528], 'D5604536': [35.508, 139.676], 'Dc7b4703': [35.568, 139.655], 'Dc46d194': [35.307, 139.622], 'D68f9d95': [35.400, 139.591],
    'D8da1ced': [35.339, 139.490], 'Daed391e': [35.441, 139.364], 'D0437ae3': [35.319, 139.551], 'Daf1e25b': [35.264, 139.152], 'D0b50c1a': [35.335, 139.349],
    'D40a4aa0': [35.846, 139.660], 'Dfcb8480': [35.981, 139.479], 'D853ae97': [35.960, 139.770], 'D3cc1cce': [35.808, 139.724], 'De3f35f2': [35.787, 139.903],
    'Dd8c07a8': [35.670, 140.168], 'D3c85024': [35.607, 140.106], 'D68a3be6': [35.868, 139.976], 'Dc28c19e': [36.400, 139.060], 'Db405639': [42.990, 141.450],
    'D13b7c6f': [43.050, 141.405], 'D1f53c72': [39.667, 141.142], 'D30e1838': [38.270, 140.850], 'D59e83ab': [37.915, 139.058], 'Da40f372': [35.620, 138.555],
    'Dd472236': [34.993, 138.385], 'D44cfd16': [35.135, 136.840], 'Dcda25a4': [35.150, 136.932], 'D1834601': [35.030, 135.995], 'Dc9d8a2b': [34.737, 135.820],
    'D25bac67': [34.996, 135.778], 'Dfc6c94f': [35.030, 135.750], 'D7d574bf': [34.762, 135.516], 'Db8bafea': [34.857, 135.548], 'D6125f28': [34.794, 135.452],
    'D7e284b0': [34.540, 135.560], 'D01478c8': [34.705, 135.498], 'Da9518d0': [34.814, 135.651], 'D66c4625': [34.540, 135.610], 'D874b316': [34.820, 135.610],
    'D1c2a5e3': [34.540, 135.470], 'D9f338ec': [34.705, 135.205], 'D154d458': [34.677, 135.835], 'D0a999a3': [34.680, 135.750], 'D0ff488e': [34.650, 133.910],
    'D225080e': [34.335, 132.528], 'D678e01f': [34.385, 132.420], 'D8001263': [34.374, 132.448], 'D7c41c5f': [34.135, 134.580], 'Df31960d': [33.645, 130.690],
    'Dbffb89d': [33.640, 130.805], 'Db28bc5b': [33.584, 130.402], 'D7847612': [33.590, 130.420],
}

def areas(c, m):
    own = m['pref'] if m['pref'] == '北海道' else m['pref'].rstrip('都府県')
    text = re.sub(r'（[^）]*シートより）|（[^）]*(不可|除く)[^）]*）|緊急は全国|伊丹空港|北広島|柏原', '', c.get('area', ''))
    out = {own}
    if any(w in text for w in ALL): out |= set(PREFS)
    if re.search(r'関西|近畿', text): out |= set(KANSAI)
    for p, ws in list(WORDS.items()) + list(WORDS2.items()):
        if any(w in text for w in ws): out.add(p)
    t2 = text.replace('東京', '')  # 「東京都」の中の「京都」を拾わない
    for p in PREF47:
        if p in (t2 if p == '京都' else text): out.add(p)
    return [p for p in PREF47 if p in out]

# 料金表（問い合わせの下書きで使っている tariffs.json）から、候補カードで料金を計算するのに要る所だけ取り出す
# pick／back：迎車・回送 {km: ここまでは yen 円, per: そのあと unit km ごとの円, cap: 上限, over: km を超えたら一律, unsure: 金額がはっきりしない}
PICK = {  # 文で書かれた迎車・回送を形にしたもの（tariffs.json の pick.text・kaiso_text の写し）
    'D5598693': {'pick': {'km': 8, 'yen': 0, 'per': 100}},                       # 緑園都市駅から8km以上は1kmごと100円
    'D7c32399': {'pick': {'km': 5, 'yen': 1500, 'per': 150}},                    # 5kmまで1,500円、そのあと1kmごと150円
    'D68f9d95': {'pick': {'km': 3, 'yen': 0, 'per': 400, 'unit': 2}, 'back': {}}, # 3km圏内無料、そのあと2kmごと400円。回送無料
    'Dedcfcd2': {'pick': {'per': 250}},                                          # 出張料金 1kmごと250円
    'D01478c8': {'pick': {'km': 10, 'yen': 0, 'per': 100, 'unsure': True}},     # 10kmまで無料、11kmから100円加算（1kmごとか一律か未確認）
    'D7d574bf': {'pick': {'km': 10, 'yen': 0, 'per': 110}},                      # 吹田市の中心部から10kmまで無料、そのあと1kmごと110円
    'D66c4625': {'pick': {'km': 5, 'yen': 1500, 'per': 100}, 'back': {}},        # 5kmまで1,500円、そのあと1kmごと100円。回送なし
    'Dc28c19e': {'pick': {'km': 5, 'yen': 1600, 'per': 260}, 'back': {'km': 5, 'yen': 1600, 'per': 260}},  # お迎え・回送 5km以内1,600円、超えた分1kmごと260円
    'Df31960d': {'pick': {'per': 175, 'cap': 1100}, 'back': {}},                 # 1kmごと175円、30km圏内なら1,100円で打ち止め。回送無料
    'Db405639': {'pick': {'yen': 0, 'unsure': True}},                            # 札幌市内は無料（市外は未確認）
    'D9f338ec': {'back': {'km': 10, 'yen': 0, 'over': 500}},                     # お店からご自宅まで10kmを超えると回送500円
    'D7e284b0': {'pick': {'per': 280}},                                          # お迎えの距離にも1kmごと280円
}
def fare(T, did):
    if not T or not T.get('base') or not T.get('tiers'): return None
    P, out = T.get('pick'), {'base': T['base'], 'tiers': T['tiers'], 'tax': T.get('tax') or '', 'src': T.get('src', '')}
    if P and 'perkm' in P: out['pick'] = {'per': P['perkm']}
    elif P and 'yen' in P and not P.get('km'): out['pick'] = {'yen': P['yen'], 'unsure': bool(P.get('min'))}
    elif P: out['pick'] = {'unsure': True}  # 文だけで形にしていない
    kt = T.get('kaiso_text') or ''
    if re.search(r'無|かからない|無し', kt): out['back'] = {}
    out.update({k: v for k, v in PICK.get(did, {}).items()})
    if T.get('wait') and T['wait'].get('unit'): out['wait'] = T['wait']
    if T.get('night'): out['night'] = T['night']
    return out

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

# 犬・猫のほかの動物（Nori 2026-10-31「犬、猫以外の動物の利用もできる事業者さんがいると思うから、それにフォームも対応する」）
# facts.json の animals（公式サイトの文）から読む。ok＝乗せられると書いてある種類、no＝断ると書いてある種類、
# all＝「種類を問わず」などと書いてある、only＝「犬・猫のみ」と書いてある。どれも無ければ分からない（候補には出して「確認中」と書く）
KINDS = {'small': r'小動物|うさぎ|ウサギ|ハムスター|フェレット|モルモット|リス|りす|チンチラ',
         'bird': r'鳥|インコ|オウム|文鳥', 'reptile': r'爬虫類|亀|カメ|両生類|トカゲ|ヘビ', 'fish': r'魚|錦鯉|金魚'}
ALL_OK = r'種類を問わず|どんな種類|法的に問題ない|飼育が認められている|あらゆるペット|ほとんどのペット|犬猫に限らず|出来る限りのご要望'
ANIMAL_FIX = {  # 文の形で読み違えるものは手で直す
    'Dc9d8a2b': {'ok': ['small'], 'no': ['bird', 'reptile']},   # 「※爬虫類と小鳥などは、お断りしております」
}

def animals(f):
    a = f.get('animals') or {}
    t = '' if a.get('vague') else a.get('v', '')
    out = {'all': bool(re.search(ALL_OK, t)), 'only': bool(re.search(r'犬・猫のみ|ワンちゃん・ネコちゃんのみ|犬猫のみ', t)),
           'ok': [k for k, r in KINDS.items() if re.search(r, t)], 'no': []}
    out.update(ANIMAL_FIX.get(f.get('_id'), {}))
    return out

def main(master, comp, tariffs=None, facts_path=None):
    ms = json.load(open(master, encoding='utf-8'))
    cs = {c['id']: c for c in json.load(open(comp, encoding='utf-8'))}
    ts = json.load(open(tariffs, encoding='utf-8')) if tariffs else {}
    facts = json.load(open(facts_path, encoding='utf-8')) if facts_path else {}
    out = []
    for m in ms:
        if m['status'] != '掲載候補' or m['id'] in SKIP: continue  # 全国の掲載候補（Nori 2026-10-31「全国にして。絞らないで」）
        c = cs.get(m['id'], {})
        at = re.sub(r'（[^）]*シートより）', '', c.get('area', ''))
        row = {'id': m['id'], 'name': m['name'], 'pref': m['pref'], 'areas': areas(c, m), 'area_text': '' if at.startswith('不明') else at[:70],
               'shop': SHOP.get(m['id']), 'fare': fare(ts.get(m['id']), m['id']), 'pay': pay(c)}
        row.update(schedule(c, m['id']))
        row['animals'] = animals(dict(facts.get(m['id'], {}), _id=m['id']))
        assert not re.search(r'\d{2,4}-\d{2,4}-\d{3,4}|@', json.dumps(row, ensure_ascii=False)), row  # 電話番号・メールは入れない
        out.append(row)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'display_companies.json')
    json.dump({'_説明': '予約の候補カードに表示だけする会社（依頼は送れない）。tools/display_companies.py で作る。出すかどうかは booking/Code.gs の CONFIG.SHOW_ALL_CANDIDATES', 'companies': out},
              open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(out), '社', '料金つき', sum(1 for r in out if r['fare']), {p: sum(p in r['areas'] for r in out) for p in PREF47 if any(p in r['areas'] for r in out)})
    print('犬・猫のほか', {k: sum(r['animals']['all'] or k in r['animals']['ok'] for r in out) for k in KINDS}, '犬・猫のみ', sum(r['animals']['only'] for r in out))

if __name__ == '__main__':
    main(*sys.argv[1:5])
