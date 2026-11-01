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
# 今回は対象外（Nori 2026-11-01「LINE・電話・江戸川は今回対象外。サイトにも出てこないように」）：
# 電話だけ・LINEと電話だけの会社と、フォームが壊れているCOCOタク江戸川店
SKIP |= {'D0ff488e', 'D8001263', 'D59e83ab', 'Dbe5cb84', 'Dbffb89d', 'Dd8c07a8', 'D68a3be6', 'D7e284b0',
         'Dcda25a4', 'Da5a2701', 'D7138c0d', 'Dc46d194', 'Dea620d5'}
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
    'D25bac67': [34.985, 135.759], 'Dfc6c94f': [35.030, 135.750], 'D7d574bf': [34.762, 135.516], 'Db8bafea': [34.857, 135.548], 'D6125f28': [34.794, 135.452],
    'D7e284b0': [34.540, 135.560], 'D01478c8': [34.705, 135.498], 'Da9518d0': [34.814, 135.651], 'D66c4625': [34.540, 135.610], 'D874b316': [34.820, 135.610],
    'D1c2a5e3': [34.540, 135.470], 'D9f338ec': [34.705, 135.205], 'D154d458': [34.677, 135.835], 'D0a999a3': [34.680, 135.750], 'D0ff488e': [34.650, 133.910],
    'D225080e': [34.335, 132.528], 'D678e01f': [34.385, 132.420], 'D8001263': [34.374, 132.448], 'D7c41c5f': [34.135, 134.580], 'Df31960d': [33.645, 130.690],
    'Dbffb89d': [33.640, 130.805], 'D06b72ea': [35.354, 139.531], 'D72024d3': [34.735, 135.385], 'Db28bc5b': [33.584, 130.402], 'D7847612': [33.590, 130.420],
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
# 距離制の形に当てはまらない会社の料金のしくみ（会社ごとの式。Nori 2026-10-31「全ての事業所で違う計算式でもいい。正しい料金が出ることが一番」）
# 公式サイトの数字がはっきりしている会社だけ入れる。区切りや単価が読み取れない会社（レゴラスハウス・ZERO・冨士タクシーなど）は入れない
CUSTOM = {
    # ラッキーペットサービス（2026-10-31 公式サイトの「エリア・送迎料金」をNoriのMacで確認。税抜「合計金額に別途消費税」）
    # 5kmまで2,500円、6〜19km 1kmごと250円、20〜100km 200円、101km〜 150円。お迎え料金は西宮600円・芦屋800円・宝塚/尼崎/伊丹/東灘1,200円、
    # それ以外は尼崎市南武庫之荘から1kmごと150円 → 地域の定額は形にせず、お店からの距離×150円で計算（unsure）。待ち時間は20分無料、10分ごと250円。夜間の割増の記載なし（営業8:30-19:00）
    'D72024d3': {'base': [2500, 5], 'tiers': [[6, 19, 250], [20, 100, 200], [101, None, 150]], 'tax': '税抜',
                 # 市ごとの定額（西宮600〜宝塚・伊丹1,200円）と距離×150円を、「お店から4kmまで600円、そのあと1kmごと150円」で近づける（〜付き）
                 'pick': {'km': 4, 'yen': 600, 'per': 150, 'unsure': True}, 'wait': {'free': 20, 'unit': 10, 'yen': 250},
                 'src': 'https://lucky-pettaxi.jimdosite.com/%E3%82%A8%E3%83%AA%E3%82%A2%E3%83%BB%E9%80%81%E8%BF%8E%E6%96%99%E9%87%91/'},
    'Dc9d8a2b': {'base': [3300, 20], 'tiers': [[21, None, 110, 10]], 'tax': '税込', 'night': {'from': 21, 'to': 6, 'flat': 3300},
                 'src': 'https://j-pettaxi.com/'},  # 基本料金3,300円（20km・1時間以内）、21kmから10kmごと110円、21〜6時 3,300円
    'Dfc6c94f': {'kind': 'time', 'time': {'first': [60, 6280], 'unit': [30, 3140]}, 'tax': '税込',
                 'src': 'https://kitani11taxi.com/'},  # 時間貸切 1時間6,280円（最少1時間）、以降30分ごと3,140円
    'D44cfd16': {'kind': 'time', 'time': {'first': [20, 4400], 'unit': [10, 550], 'maxKm': 20}, 'off': {'from': 9, 'to': 18, 'perHour': 1650},
                 'pick': {'km': 3, 'yen': 0, 'per': 280}, 'tax': '税込',
                 'src': 'https://happywith.pet/price/'},  # 20分4,400円＋10分ごと550円（20kmまで）、9〜18時の外は1時間ごと1,650円、配車3kmまで無料・そのあと1kmごと280円
    'Db28bc5b': {'kind': 'zone', 'zone': {'city': '福岡市', 'one': 3000, 'round': 5000}, 'wait': {'free': 15, 'unit': 15, 'yen': 1000},
                 'night': {'from': 20, 'to': 8, 'flat': 5000}, 'pick': {'yen': 0}, 'back': {}, 'tax': '',
                 'src': 'https://wanwan.pet/'},  # 福岡市内→福岡市内 片道3,000円・往復5,000円、待ち15分無料・そのあと15分ごと1,000円、20〜8時 5,000円
    'De65cb2d': {'kind': 'table', 'table': [[5, 3850], [10, 4950], [15, 6050], [20, 7150], [25, 8250], [30, 9350], [35, 10450], [40, 11550], [45, 12650], [50, 13750]],
                 'roundTable': [[5, 6160], [10, 7920], [15, 9680], [20, 11440], [25, 13200], [30, 14960], [35, 16720], [40, 18480], [45, 20240], [50, 22000]],
                 'wait': {'free': 0, 'unit': 30, 'yen': 550}, 'tax': '', 'src': 'https://www.legolashouse.com/price'},  # 片道・往復の距離ごとの料金表（50kmまで）、待ち30分ごと550円
    'D945f580': {'kind': 'time', 'time': {'first': [90, 5720], 'unit': [15, 1430], 'discount': {'min': 120, 'rate': 0.05}},
                 'pick': {'km': 10, 'yen': 0, 'per': 825, 'unit': 10}, 'back': {'km': 10, 'yen': 0, 'per': 825, 'unit': 10}, 'tax': '税込',
                 'src': 'https://www.ikimonocare.com/'},  # 90分5,720円、15分ごと1,430円、2時間以上5%引き。移動は片道30分まで無料・そのあと30分ごと825円（1kmを3分とみて10km）
    'D6125f28': {'base': [4000, 10], 'tiers': [[11, None, 200]], 'pick': {'yen': 0, 'unknownOver': 5}, 'wait': {'free': 0, 'unit': 10, 'yen': 300}, 'tax': '税込',
                 'src': 'https://doghairstudioken.jp/'},  # 基本4,000円（お迎えと10kmまで込み）、そのあと1kmごと200円、待ち10分ごと300円。お店から5km超のお迎えは別料金（金額なし）
    'D40a4aa0': {'base': [3300, 5], 'tiers': [[6, 100, 165], [101, 200, 132], [201, None, 110]], 'pick': {'per': 165, 'unsure': True}, 'wait': {'free': 10, 'unit': 10, 'yen': 220}, 'tax': '税込',
                 'src': 'https://cocotaxi-saitama.com/'},  # お迎え165円/km（いまは50%OFFのセール中と書いてある→「〜」）
    'Dfcb8480': {'base': [3300, 5], 'tiers': [[6, 100, 165], [101, 200, 132], [201, None, 110]], 'pick': {'per': 165}, 'tax': '',
                 'src': 'https://pet-taxi-saitama-kawagoe.jp/'},
    'D3c85024': {'base': [1500, 5], 'tiers': [[6, None, 200]], 'pick': {'km': 5, 'yen': 0, 'per': 100}, 'tax': '',
                 'src': 'https://pearlno-shippo.com/'},  # 基本1,500円（5kmまで）・そのあと1kmごと200円、お迎え5kmまで無料・そのあと1kmごと100円、待ち30分まで無料
    # ↓ 2026-10-31 料金表をまだデータにしていなかった会社（公式サイトを読み直した）
    'Da5a2701': {'base': [1299, 1], 'tiers': [[2, 5, 650], [6, 100, 338], [101, 200, 156], [201, None, 130]], 'pick': {'per': 150},
                 'wait': {'free': 0, 'unit': 10, 'yen': 250}, 'night': {'from': 19, 'to': 5, 'unknown': True}, 'tax': '',
                 'src': 'https://pet-taxikarubi.com/'},  # 1kmまで1,299円、2〜5km 650円/km…、お迎え150円/km、19〜5時は時間外料金（金額は問い合わせ）
    'Dbe5cb84': {'base': [2000, 5], 'tiers': [[6, 10, 500, 5], [11, 100, 1000, 5], [101, 200, 170], [201, None, 130]],
                 'pick': {'base': [500, 5], 'tiers': [[6, 15, 1000, 5], [16, 100, 500, 5], [101, None, 300, 5]]},
                 'wait': {'free': 30, 'unit': 30, 'yen': 500}, 'tax': '税込', 'src': 'https://azul.fivedogs.jp/'},  # 乗車・お迎えとも5kmごとの加算
    'D7138c0d': {'base': [0, 0], 'tiers': [[1, None, 500]], 'pick': {'yen': 2000}, 'wait': {'free': 0, 'unit': 15, 'yen': 300},
                 'night': {'from': 22, 'to': 8, 'rate': 0.2}, 'longDiscount': [[5000, 0.1], [10000, 0.2], [15000, 0.3]], 'tax': '税込',
                 'src': 'https://pettaxi-tokyo.jp/'},  # 迎車2,000円＋1kmごと500円、22〜8時2割増、5,000円〜10%・10,000円〜20%・15,000円〜30%引き
    'Dc46d194': {'kind': 'table', 'table': [[5, 3000]], 'pick': {'per': 160}, 'back': {'km': 30, 'yen': 0, 'over': 3000},
                 'wait': {'free': 20, 'unit': 10, 'yen': 200}, 'night': {'from': 20, 'to': 6, 'flat': 4000}, 'tax': '',
                 'src': 'https://pettakun.com/service'},  # 5kmまで3,000円（その先の単価は書いていない→5km超はお見積もり）、お迎え160円/km、回送30km以上3,000円、20〜6時4,000円
    'De3f35f2': {'base': [550, 3], 'tiers': [[4, None, 110]], 'pick': {'km': 3, 'yen': 550, 'per': 110}, 'back': {'bands': [[4, 0], [10, 550]], 'halfRide': True},
                 'wait': {'first': [20, 550], 'free': 0, 'unit': 10, 'yen': 110, 'after': [60, 220]},
                 'night': {'bands': [[20, 22, 1100], [22, 24, 2200], [0, 5, 3300], [5, 7, 2200], [7, 8, 1100]]}, 'tax': '税込',
                 'src': 'https://pettaxi.jp/'},  # 基本料金なし。送迎3kmまで550円・そのあと110円/km、帰社5km未満無料・10kmまで550円・その先は送迎料金の半額
    'D68a3be6': {'base': [2200, 5], 'tiers': [[6, 100, 220], [101, 200, 170], [201, None, 130]], 'pick': {'yen': 1000, 'unsure': True}, 'back': {},
                 'wait': {'free': 0, 'unit': 10, 'yen': 300}, 'tax': '税込', 'src': 'https://pet-taxi.jp/charge/'},  # お迎え1,000円〜（地域で違う）、回送無料
    'D4adf70b': {'base': [2900, 5], 'tiers': [[6, 50, 160], [51, None, 140]], 'pick': {'yen': 1000, 'unknownOver': 10}, 'pickEachLeg': True,
                 'wait': {'free': 100000, 'unit': 10, 'yen': 0}, 'night': {'from': 20, 'to': 8, 'flat': 3000}, 'tax': '',
                 'src': 'https://petrip.co.jp/'},  # お迎え片道1,000円（往復2,000円、前日までなら半額）、10km超は相談、待機料金なし、20〜8時3,000円
    'Db8bafea': {'base': [3000, 5], 'tiers': [[6, None, 180]], 'pick': {'per': 180}, 'back': {}, 'wait': {'free': 0, 'unit': 10, 'yen': 300},
                 'night': {'from': 21, 'to': 7, 'flat': 4500}, 'tax': '税抜', 'src': 'https://comasuke.com/'},  # 消費税は別。待機30分無料は前日までの病院往復のときだけ
    'D678e01f': {'kind': 'table', 'table': [[5, 2200], [10, 3300], [15, 4400], [20, 6600], [25, 8800], [30, 9900], [35, 11000], [40, 12100], [45, 14300], [50, 16500], [55, 18700], [60, 20900], [65, 23100]],
                 'pick': {'yen': 880, 'unsure': True}, 'wait': {'free': 0, 'unit': 10, 'yen': 220}, 'tax': '',
                 'src': 'https://pettaxihibiki.hp.peraichi.com/'},  # お迎え 市内880円・市外1,500円〜
    'D25bac67': {'base': [3000, 10], 'tiers': [[11, 100, 200], [101, 200, 120], [201, None, 100]], 'pick': {'km': 10, 'yen': 0, 'per': 100},
                 'wait': {'free': 20, 'unit': 10, 'yen': 300}, 'night': {'from': 21, 'to': 9, 'rate': 0.25}, 'tax': '税別',
                 'src': 'https://ten-rin.jp/taxi/'},  # 基本3,000円（迎車10km・乗車10km・待機20分込み）、迎車は京都駅から10km超100円/km、21〜9時25%増
    'D874b316': {'base': [2000, 5], 'tiers': [[6, 55, 230], [56, None, 110]], 'heavy': {'kg': 15, 'add': 500}, 'pick': {'km': 5, 'yen': 0, 'per': 110}, 'back': {},
                 'wait': {'free': 30, 'unit': 15, 'yen': 300}, 'night': {'bands': [[21, 24, 2000], [0, 6, 2000], [6, 8, 1000]]}, 'tax': '税込',
                 'src': 'https://my-family-takatsuki.com/price.html'},  # 基本2,000円（15kg以上2,500円）、乗車5km込み・そのあと230円/km（長距離110円）、お迎え5km込み・そのあと110円/km
    'Da9518d0': {'kind': 'zones', 'zones': [
                    {'label': '枚方市〜枚方市', 'a': '枚方市', 'b': '枚方市', 'one': 3300, 'round': 5500},
                    {'label': '枚方市〜寝屋川市・交野市・八幡市', 'a': '枚方市', 'b': '寝屋川市|交野市|八幡市', 'one': 4400, 'round': 6600},
                    {'label': '枚方市〜高槻市・茨木市・門真市', 'a': '枚方市', 'b': '高槻市|茨木市|門真市', 'one': 5500, 'round': 8800},
                    {'label': '枚方市〜京都市', 'a': '枚方市', 'b': '京都市', 'one': 7700, 'round': 11000},
                    {'label': '枚方市〜大阪市内', 'a': '枚方市', 'b': '大阪市', 'one': 8800, 'round': 11000},
                    {'label': '寝屋川市〜交野市・門真市・茨木市', 'a': '寝屋川市', 'b': '交野市|門真市|茨木市', 'one': 6600, 'round': 8800},
                    {'label': '寝屋川市・交野市・高槻市〜大阪市', 'a': '寝屋川市|交野市|高槻市', 'b': '大阪市', 'one': 7700, 'round': 11000},
                    {'label': '高槻市〜高槻市', 'a': '高槻市', 'b': '高槻市', 'one': 5500, 'round': 7700},
                    {'label': '高槻市〜茨木市', 'a': '高槻市', 'b': '茨木市', 'one': 6600, 'round': 8800}],
                 'pick': {'yen': 0, 'unknownOver': 10}, 'back': {}, 'wait': {'free': 30, 'unit': 30, 'yen': 660}, 'tax': '税込',
                 'src': 'https://carry-one.net/priceandflow/'},  # 区間ごとの定額。枚方の営業所から10km以上のお迎えは別料金
    'Dbffb89d': {'kind': 'table', 'table': [[3, 1800], [5, 2400], [10, 3500], [15, 4000], [20, 4500], [25, 5500], [30, 6000], [35, 6500], [40, 7000], [45, 7500], [50, 8500]],
                 'roundTable': [[3, 2800], [5, 3800], [10, 5600], [15, 6400], [20, 7200], [25, 8800], [30, 9600], [35, 10400], [40, 11200], [45, 12000], [50, 13600]],
                 'tableOver': 150, 'pick': {'per': 30}, 'back': {}, 'wait': {'free': 30, 'unit': 30, 'yen': 550}, 'tax': '',
                 'src': 'https://npet.jp/rinrin-t/price.html'},  # 距離ごとの片道・往復の料金表、50km超は1kmごと150円、出張料金1kmごと30円
    # ↓ 2026-10-31 画像の料金表を読んだ（Mac で取ってきた画像）
    'D0d611b0': {'base': [3300, 5], 'tiers': [[6, 100, 165], [101, 200, 132], [201, None, 110]], 'pick': {'per': 165}, 'back': {}, 'roundContinuous': True,
                 'wait': {'free': 10, 'unit': 10, 'yen': 220}, 'night': {'from': 22, 'to': 8, 'flat': 3300}, 'tax': '',
                 'src': 'https://www.cocotaku-shonan.com/料金プラン'},  # 乗車は総距離（往復はまとめて）、5kmまで3,300円…、お迎え165円/km、22〜5時・5〜8時 3,300円
    'D7847612': {'base': [2980, 5], 'tiers': [[6, 100, 165], [101, None, 132]], 'pick': {'per': 100}, 'back': {},
                 'wait': {'free': 60, 'unit': 10, 'yen': 200, 'cap': 1000}, 'night': {'from': 21, 'to': 8, 'flat': 3300}, 'tax': '',
                 'src': 'https://pettaxi-hakataku.wepage.com/'},  # 5kmまで2,980円、お迎え100円/km（前日までの予約で博多駅10km圏内は無料）、待機60分無料・200円/10分・上限1,000円、21〜8時3,300円
    'D06b72ea': {'base': [660, 0], 'tiers': [[1, None, 300]], 'perkmFromStart': True, 'pick': {'per': 300}, 'night': {'from': 21, 'to': 9, 'unknown': True}, 'tax': '',
                 'src': 'https://pets-taxi.net/ja/kamakurapettaxi'},  # 初乗り660円＋運搬300円/km、送迎300円/km（大船駅から）、9時前・21時以降は割増（金額なし）
}
# 見積もりの返事（2026-11-01 答え合わせ）で分かった、公式サイトにない計算のしかた。fare に上書きする（Nori 2026-11-01「料金回答あった会社はいけるんじゃない？」）
# night.by='start'＝乗る時刻だけで判定（ふつうは乗っているあいだに少しでも入れば全部にかける）、round＝10円未満切り捨て、kmMode＝距離の数え方
REPLY_FIX = {
    'Db405639': {'round': 10, 'pick': {'yen': 0}},                                   # D-RIDE：(2,980＋16km×150)×1.2＝6,456→6,450。お迎え料金なし
    'Db8bafea': {'round': 10},                                                       # Comasuke：②5,520×1.1＝6,072→6,070
    'D40a4aa0': {'pick': {'per': 165, 'rate': 0.5}},                                 # COCOタク さいたま南：お迎え半額セール（25km 1,875円＋税）。早朝料金は取っていない
    'D13b7c6f': {'night': {'from': 21, 'to': 9, 'flat': 3300, 'by': 'start'}},       # aiai：早朝（〜9時）も3,300円。20:50乗車は割増なし
    'D0a999a3': {'base': [3300, 0], 'tiers': [[1, 100, 165], [101, 200, 132], [201, None, 110]], 'night': {'from': 21, 'to': 8, 'flat': 3300, 'by': 'start'}},  # COCOタク奈良：基本3,300円＋お迎えと乗車の全km×165円。20:50乗車は割増なし
    'D355c31f': {'kmMode': 'exact', 'pick': {'per': 198, 'freeWithin': 3},           # サポっ人 中目黒：13.1km×198＝2,593円のように小数の距離。お店の近くはお迎え無料
                 'night': {'from': 22, 'to': 8, 'rate': 0.5, 'onAll': True}},        # 8時前・22時過ぎは50%増し
    'D225080e': {'night': {'from': 21, 'to': 7, 'flat': 3000}},                       # ペッタク：21〜7時は深夜料金3,000円
    'D678e01f': {'oneWayRate': 0.2, 'kmMode': 'floor', 'night': {'from': 22, 'to': 6, 'rate': 0.2}},  # 響：片道（乗り捨て）2割増し、25.9kmは25kmの料金、22〜6時2割増し
    'D44cfd16': {'time': {'first': [20, 4400], 'unit': [10, 550], 'maxKm': 20, 'maxTotalKm': 20}},  # HAPPY WITH：迎車と乗車で20km超は距離プラン（「18,000円〜」）→お見積もり
}
def fare(T, did):
    out = fare0(T, did)
    if out and did in REPLY_FIX: out = dict(out, **REPLY_FIX[did])
    return out
def fare0(T, did):
    if did in CUSTOM: return CUSTOM[did]
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

# カードのアピールポイント（Nori 2026-10-31「各事業者のアピールポイントをカード内に」）。
# 公式サイトの文（facts.json の by=site／会社の返事 by=reply、あいまい印なし）に書いてあることだけを短いことばにする。作らない・盛らない。最大4つ
POINT_RULES = [
    ('jutai', r'見積もりどおり', None, '渋滞でも追加料金なし'),  # Nori 2026-11-01「渋滞などが起こっても追加料金なしはアピールポイント」。公式サイトに渋滞で加算しないと書いてある会社だけ
    ('lead', r'当日[^。]*(可|OK|大丈夫|受け|承|対応|歓迎|できます)|当日のご連絡でも', r'当日[^。]*(お受けできない|できません)|可能な場合(も)?(あり|ございます)', '当日予約可'),  # Nori 2026-11-01「当日予約可はあってもいい」。ワクチン証明は外す（アピールポイントではない）
    ('hours', r'24時間', r'電話受付24時間|Web予約は24時間|緊急は24時間', '24時間受付'),
    ('hours', r'(深夜|早朝)[^。]*(相談|対応)', r'不可', '深夜・早朝も相談可'),
    ('night', r'割増(なし|はありません|無し)', None, '深夜・早朝の割増なし'),
    ('riders', r'同乗[^。]*無料|無料[^。]*同乗', None, '飼い主さんの同乗無料'),
    ('care', r'介護資格|ヘルパー|介助|担架', r'お断り', '介助のサポートあり'),
    ('large', r'大型犬', r'不可|お断り|できません', '大型犬OK'),
    ('large', r'スロープ', None, 'スロープつき'),
    ('cage', r'ケージ[^。]*無料|無料[^。]*ケージ', None, 'ケージを無料で使える'),
    ('pets', r'多頭', r'不可', '多頭OK'),
    ('cancel', r'前日[^。]*(キャンセル料は発生しません|キャンセルは無料|無料)', None, '前日までキャンセル無料'),
    ('pay', r'クレジット|カード', r'取り扱いは致しておりません|使えません|不可', 'カード払い可'),
    ('pay', r'PayPay', None, 'PayPay可'),
    ('extra', r'追加料金なし', None, '追加料金なし'),
    ('roundtrip', r'割引', None, '往復の割引あり'),
    ('cars', r'黒ナンバー|緑ナンバー', None, '運送の許可あり'),
]
def points(f):
    out = []
    for key, ok, ng, label in POINT_RULES:
        v = f.get(key) or {}
        if v.get('by') not in ('site', 'reply') or v.get('vague'): continue
        t = str(v.get('v') or '')
        if re.search(ok, t) and not (ng and re.search(ng, t)) and label not in out: out.append(label)
    if '渋滞でも追加料金なし' in out and '追加料金なし' in out: out.remove('追加料金なし')  # 同じことを2つ出さない
    return out[:4]
# 条件のタグ（Nori 2026-11-01「大型犬2頭までOKとか、多頭OKとか、逆に飼い主様1人まで、2人までとか、現金のみとか、そういうのも入れていって」）
# 良いことに限らず、乗れる人数・頭数・お支払いの決まりを短く書く。公式サイトの文（by=site／reply）から数字を拾うだけ。最大3つ。カードでは灰色で出す
Z2H = str.maketrans('０１２３４５６７８９～〜', '0123456789~~')
def _t(f, key):
    v = f.get(key) or {}
    if v.get('by') not in ('site', 'reply') or v.get('vague'): return ''
    return str(v.get('v') or '').translate(Z2H)
def limits(f):
    out = []
    # 大型犬の頭数
    lg, pe = _t(f, 'large'), _t(f, 'pets')
    m = re.search(r'大型犬[^。]*?(\d)頭(には)?対応していない', lg)
    if m and m.group(1) != '1': out.append('大型犬は%d頭まで' % (int(m.group(1)) - 1))
    elif '食い違い' not in lg:
        ms = re.findall(r'大型犬[^。（]*?(\d)\s*(?:頭|匹)(まで)?', lg + '。' + pe)
        if ms:
            n, upto = max(ms, key=lambda x: int(x[0]))
            out.append('大型犬%s頭%s' % (n, 'まで' if upto else 'OK'))
    # 頭数
    m = re.search(r'(\d)\s*~\s*(\d)\s*頭', pe)
    if m: out.append('%s〜%s頭OK' % (m.group(1), m.group(2)))
    elif re.search(r'(\d)\s*頭(でも|を一度に)', pe): out.append('%s頭OK' % re.search(r'(\d)\s*頭(でも|を一度に)', pe).group(1))
    elif re.search(r'何頭でも|頭数(に関係なく|による追加料金はありません)|複数でも追加料金|多頭飼いも追加料金なし|匹数[^。]*関係なく', pe): out.append('頭数で料金は変わらない')
    # 同乗の人数
    r = _t(f, 'riders')
    ns = [int(x) for x in re.findall(r'(\d)\s*(?:名|人)(?:様)?(?:まで|迄)', r) + re.findall(r'定員\s*(\d)\s*名', r) + re.findall(r'(\d)\s*名様?まで', r)]
    if ns: out.append('同乗は%d人まで' % max(ns))
    # お支払い
    py = _t(f, 'pay')
    if re.search(r'現金(のみ|にて|で)', py) and not re.search(r'クレジット|カード|クレカ|PayPay|paypay|QR|電子|振込|振り込み', py): out.append('現金のみ')
    elif re.search(r'クレジットカードの取り扱いは致しておりません', py): out.append('カード払い不可')
    return out[:3]
PARTNER_SAME = {'P002': 'Dbcb8b8d', 'P003': 'Da968571'}  # 提携先シートの会社と、事業者マスターの同じ会社

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
        # 口コミの星を取り寄せるための、地図で場所を探すことばと、見つかった場所の名前に入っているはずのことば（ダッシュボードと同じ。点数そのものは入れない）
        if c.get('review_q') and c.get('review_name'): row['review_q'], row['review_name'] = c['review_q'], c['review_name']
        row.update(schedule(c, m['id']))
        row['animals'] = animals(dict(facts.get(m['id'], {}), _id=m['id']))
        pts = points(facts.get(m['id'], {}))
        lim = limits(facts.get(m['id'], {}))
        if lim: row['limits'] = lim
        if any(x.startswith('大型犬') for x in lim): pts = [x for x in pts if x != '大型犬OK']  # 頭数つきのほうを出す
        if any('頭' in x and not x.startswith('大型犬') for x in lim): pts = [x for x in pts if x != '多頭OK']
        if pts: row['points'] = pts
        assert not re.search(r'\d{2,4}-\d{2,4}-\d{3,4}|@', json.dumps(row, ensure_ascii=False)), row  # 電話番号・メールは入れない
        out.append(row)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'display_companies.json')
    json.dump({'_説明': '予約の候補カードに表示だけする会社（依頼は送れない）。tools/display_companies.py で作る。出すかどうかは booking/Code.gs の CONFIG.SHOW_ALL_CANDIDATES', 'companies': out,
               'partner_points': {pid: points(facts.get(did, {})) for pid, did in PARTNER_SAME.items() if points(facts.get(did, {}))},
               'partner_limits': {pid: limits(facts.get(did, {})) for pid, did in PARTNER_SAME.items() if limits(facts.get(did, {}))}},
              open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(out), '社', '料金つき', sum(1 for r in out if r['fare']), {p: sum(p in r['areas'] for r in out) for p in PREF47 if any(p in r['areas'] for r in out)})
    print('犬・猫のほか', {k: sum(r['animals']['all'] or k in r['animals']['ok'] for r in out) for k in KINDS}, '犬・猫のみ', sum(r['animals']['only'] for r in out))

if __name__ == '__main__':
    main(*sys.argv[1:5])
