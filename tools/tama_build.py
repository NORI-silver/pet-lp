#!/usr/bin/env python3
"""[B] 東京多摩・島しょ＋神奈川：登録一覧の事業所の公式サイトさがしの結果（regsite_pick.py の出力）から、各分野に足す行を作る。
- 公式サイトと決めたもの（住所の町名か事業所名がページにある）だけ。情報サイト・求人・予約サイト・ブログの記事・SNS は使わない。
- 分野は公式サイトの文の言葉で決める（ホテル・シッター・しつけ・老犬ホーム・出張トリミング）。トリミングだけのお店は今は足さない。
- facts は公式サイトの文のまま（出どころ src・確認日つき）。推測で埋めない。
出力は tools/tama_add.json（kinki_add.json と同じ形）。入れるのは tools/tama_add.py。
  python3 tools/tama_build.py <regsite_pick の出力.json> [...]
"""
import json, os, re, sys, hashlib, datetime
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().isoformat()
NOT_OFFICIAL = re.compile(r'yamatopi|toredog|pigcat|feedon\.jp/shop/$|maruone\.com/blog|anc\.jp|goguynet|seesaa|town-info|salesnow|yapy|mizumono|maruone\.com/blog|forestsquare|bohseipharmacy|pcareer|stroker|unicoffee|karatoto|tenseien|rairai\.net|localstyle|pet-hotel-japan|npet\.jp|happytry|pet-systems|intopet|kawaii-wanko|inumado\.com/.|wonderfuldogfield|mamacook|microbubble|cheriee|dogoo|dog-shitsuke-portal|ikeruwan|y-petnavi|machitoku|anipita|snacknavi|keizai\.biz|pet-miru|licopa|mall|shopping|tenant|floor|shop-?list|stanby|localplace|animalcampus|ameblo\.jp|trimtrim|japanpetsalon|wanstown|scarecrow-inc|pet2211|takashimadairatown|dog-shitsuke-portal|trimmingwan|zpk\.or\.jp|prtimes|olivesitter|airrsv|select-type|machinavi|dogspecialist-navi|allets|edogawa-jikan|microbubble|jalan|hotpepper|curama|zehitomo|meetsmore|itsumo\.dog|petpet|torepet|petsitter-search|petokoto|pet-home\.jp|jmty|satoya-boshu|omusubi-pet|godog-run|dogrun-uzuz|animaru-navi|animalpark-pv|uchinoshippo|rouken|rou-ken|olddogcat|iconia|rakuten|ikyu|tabelog|retty|e-sogi|anicom-page|breeder-navi|minnanobreeder|goodbreeder|ekiten|ipet|petlife|caloo|mapion|navitime|townpage|epark|instagram|facebook|twitter|x\.com|tiktok|youtube|line\.me|note\.com|hatenablog|fc2\.com|livedoor|goo\.ne\.jp|indeed|baitoru|mynavi|townwork|en-gage|doda|recruit|kyujin|houjin|baseconnect|wikipedia|lg\.jp|go\.jp|google\.|yahoo\.|bing\.|navi|portal|matome|ranking|hikaku|kuchikomi|review|machiserch|kurashippo|equall\.jp|kumorinochihare|athome\.co\.jp|dogdrop|trimmingfan|trimmer-agent|doging\.com|ckc\.tokyo|inukatsu|pomeranian-festival|ivry\.jp|safely\.co\.jp|jpss-saiyo|pevie|petri\.pet|tokubai|1link\.jp|cross-animal|companydata|iko-yo|music\.apple|lovegreen|rakuraku\.or\.jp', re.I)
CATS = {
    'hotels': re.compile(r'ペットホテル|ドッグホテル|キャットホテル|猫(?:の|ちゃんの)?ホテル|犬(?:の)?ホテル|ホテル(?:料金|利用|のご案内|サービス|メニュー)'),
    'sitters': re.compile(r'ペットシッター|キャットシッター|シッターサービス|訪問(?:して|で)?(?:の)?お世話'),
    'trainers': re.compile(r'しつけ教室|しつけ方教室|ドッグトレーニング|ドッグトレーナー|家庭犬(?:の)?(?:しつけ|訓練)|出張(?:しつけ|トレーニング|訓練)|預(?:け|かり)訓練|パピー(?:クラス|教室)|訓練所|しつけ(?:レッスン|トレーニング)'),
    'homes': re.compile(r'老犬ホーム|老猫ホーム'),
    'groomers': re.compile(r'出張トリミング|訪問トリミング|移動トリミング|トリミングカー'),
}
SVC = [('ペットホテル', 'hotels'), ('ペットシッター', 'sitters'), ('しつけ', 'trainers'), ('老犬ホーム', 'homes'), ('出張トリミング', 'groomers')]
PFX = {'hotels': 'PHt', 'sitters': 'St', 'trainers': 'Tt', 'homes': 'Rt', 'groomers': 'Gt'}
FACT = [
    ('営業・受付時間', re.compile(r'(営業|受付)時間|OPEN|営業[:：]'), re.compile(r'[0-9]{1,2}[:：時]')),
    ('定休日', re.compile(r'定休日|休業日|定休'), re.compile(r'[月火水木金土日]曜|無休|不定休|祝')),
    ('料金', re.compile(r'(?:ホテル|お預かり|宿泊|1泊|一泊|シッター|訪問|レッスン|トレーニング|しつけ|入会|入居|月額|基本料金|料金)'), re.compile(r'[0-9][0-9,，]*\s*円')),
    ('駐車場', re.compile(r'駐車場|駐車スペース|パーキング'), re.compile(r'[0-9０-９]+台|完備|あり|有り|ございます|ありません|ございません|なし|無し|コインパーキング|近くの')),
    ('用意するもの', re.compile(r'ワクチン|狂犬病|予防接種'), re.compile(r'証明|1年以内|一年以内|接種(?:済|して|が必要|していない)|必要|お持ち')),
    ('対応エリア', re.compile(r'対応エリア|対応地域|サービスエリア|訪問エリア|出張エリア|対象エリア|対応区域|エリア[:：]'), re.compile(r'[区市町村]|km|ｋｍ|キロ')),
    ('送迎', re.compile(r'送迎|送り迎え'), re.compile(r'円|無料|km|ｋｍ|キロ|エリア|[区市]内|片道|往復')),
    ('お支払い', re.compile(r'お支払|支払い方法|クレジットカード|PayPay|現金のみ'), re.compile(r'現金|カード|PayPay|ペイペイ|振込|電子マネー|QR|交通系')),
]
NOISE = re.compile(r'-->|<!--|^例|例[0-9１-９]+[）)]|受けていない|ていない(?:こと|子|方)?[。、]?$|できません|お断り|ご遠慮|円まで|手配|Google|グーグル|[？?]\s*$|[0-9０-９]{2,4}[-－‐ー][0-9０-９]{2,4}[-－‐ー][0-9０-９]{3,4}|@|TEL|Tel|FAX|電話|LINE|キャンセル|求人|採用|スタッフ募集|アルバイト|Copyright|©|cookie|ログイン|カート|送料|通販|商品|フード|ブログ|ニュース|お知らせ|\d{4}[./年]\d{1,2}[./月]\d{1,2}')


def host(u):
    return urlparse(u).netloc.lower().replace('www.', '')


def fix_addr(x):
    a = re.sub(r'^(東京都|神奈川県)', '', x['addr'])
    a = re.sub(r'^(横浜市|川崎市|相模原市)\1', r'\1', a)
    m = re.match(r'(横浜市|川崎市|相模原市)(.{1,4}区)', a)
    city = m.group(1) + m.group(2) if m else x['city']
    return x['pref'] + a, city


def facts_of(x, cat):
    out = []
    for k, rx, need in FACT:
        if k == '料金' and cat == 'hotels':
            rxk = re.compile(r'ホテル|お預かり|宿泊|1泊|一泊|1日|デイケア')
        elif k == '料金' and cat == 'sitters':
            rxk = re.compile(r'シッター|訪問|お世話|1回|基本')
        elif k == '料金' and cat == 'trainers':
            rxk = re.compile(r'レッスン|トレーニング|しつけ|訓練|教室|入会|1回')
        elif k == '料金' and cat == 'homes':
            rxk = re.compile(r'月額|入居|入所|預かり|1日|年')
        elif k == '料金' and cat == 'groomers':
            rxk = re.compile(r'出張|トリミング|カット|シャンプー')
        else:
            rxk = rx
        best = None
        for c in x['facts'].get({'営業・受付時間': '営業時間', '用意するもの': 'ワクチン'}.get(k, k), []) + \
                 (x['facts'].get('料金', []) if k == '料金' else []):
            v = c['v'].strip()
            if NOISE.search(v) or not rxk.search(v) or (need and not need.search(v)):
                continue
            if k == '料金' and re.search(r'[×✖︎xX＝=＋+※]|追加|割増|特別|割引|延長|約|オプション|お散歩|ポイント|クーポン|オフ|OFF|合計|総額.*総額', v):
                continue
            if re.search(r'[:：]\s*$', v) or (k == '営業・受付時間' and len(v) > 60) or (k == '用意するもの' and (len(v) < 12 or not re.search(r'証明|必要|済|お持ち|提示|接種(?:して|を)', v))):
                continue
            if 6 <= len(v) <= 160 and (best is None or len(v) < len(best['v'])):
                best = c
        if best:
            out.append({'k': k, 'v': best['v'].strip(), 'src': best['src'], 'by': 'site', 'checked': TODAY})
    return out


def main():
    picks = []
    for fn in sys.argv[1:]:
        picks += json.load(open(fn))
    add = {k: [] for _, k in SVC}
    stat = {'official': 0, 'not_official_host': 0, 'out_of_scope': 0}
    seen = set()
    for x in picks:
        if x.get('state') != 'official':
            continue
        stat['official'] += 1
        u = x['url']
        if NOT_OFFICIAL.search(host(u)) or NOT_OFFICIAL.search(urlparse(u).path.split('/')[1] if '/' in urlparse(u).path else ''):
            stat['not_official_host'] += 1
            continue
        lines = [l for l in x.get('lines', []) if not re.search(r'おすすめ|お勧め|お薦め|紹介|一覧|件のサロン|件の', l)]
        text = ' '.join(lines) + ' ' + x.get('title', '')
        cats = [k for _, k in SVC if CATS[k].search(text)]
        if 'trainers' in cats and '訓練' not in x.get('types', []):
            # しつけは「訓練」の登録がある事業所だけ（登録のないしつけは受けられないため）
            cats.remove('trainers')
        if 'homes' in cats and not (re.search(r'老犬ホーム|老猫ホーム|老犬・老猫ホーム', x.get('title', '')) or any(len(l) <= 25 and re.search(r'老犬ホーム|老猫ホーム|老犬・老猫ホーム', l) and not re.search(r'られ|に預け|では', l) for l in lines)):
            # 老犬ホームは、その名前でサービスを出している施設だけ（「老犬ホームに預けられた」などの文だけでは入れない）
            cats.remove('homes')
        if not cats:
            stat['out_of_scope'] += 1
            continue
        svc = '、'.join(n for n, k in SVC if k in cats)
        for k in cats:
            if (k, host(u) + urlparse(u).path) in seen:
                continue
            seen.add((k, host(u) + urlparse(u).path))
            h = hashlib.sha1((x['name'] + x['addr']).encode()).hexdigest()[:7]
            full, city = fix_addr(x)
            row = {'id': PFX[k] + h, 'name': re.sub(r'\s+', ' ', x['name']).strip(), 'prefs': [x['pref']], 'city': city,
                   'url': u, 'services': svc, 'facts': facts_of(x, k), 'checked': TODAY}
            fa = {f['k']: f['v'] for f in row['facts']}
            if k == 'sitters':
                hh = host(u)
                row['chain'] = 'nihon' if 'pet-ss.com' in hh else 'SOS' if 'petsitter-sos' in hh or 'SOS' in x['name'] else 'penguin' if 'penguinsitter' in hh else 'intopet' if 'intopet' in hh else 'indie'
                row['area'] = fa.get('対応エリア', city + 'とその周り')
            if k == 'trainers':
                row['addr'] = full
                row['src'] = u
            if k == 'groomers':
                row['area'] = fa.get('対応エリア', city + 'とその周り')
                if re.search(r'トリミングカー|移動トリミング車|専用車', text): row['car'] = True
            if k == 'hotels':
                if re.search(r'猫(?:ちゃん)?(?:の|も)?(?:お預かり|ホテル)|キャットホテル|猫(?:ちゃん)?.{0,4}(?:OK|可)', text): row['cat'] = True
                if '送迎' in fa and not re.search(r'行っておりません|ありません|しておりません|不可|なし|無し|できません', fa['送迎']): row['pickup'] = True
            if k == 'homes':
                row['spec'] = svc
                row['addr'] = full
                row['animals'] = '犬・猫' if re.search(r'老猫|猫の(?:お預かり|ホーム|介護)', text) else '犬'
            add[k].append(row)
    out = os.path.join(HERE, 'tama_add.json')
    old = json.load(open(out)) if os.path.exists(out) else {}
    for k, L in add.items():
        ids = {r['id'] for r in old.get(k, [])}
        old.setdefault(k, []).extend(r for r in L if r['id'] not in ids)
    json.dump(old, open(out, 'w'), ensure_ascii=False, indent=1)
    print(stat, {k: len(v) for k, v in add.items()})


if __name__ == '__main__':
    main()
