"""tama_add で足した行（id が PHt/St/Tt/Rt/Gt）の facts の雑音を落とす。何度動かしても同じ。"""
import json, re, sys
FILES = ['tools/tama_add.json', 'tools/hotels.json', 'tools/trainers.json', 'tools/sitters.json', 'tools/grooming.json', 'tools/rojin.json']
IDRE = re.compile(r'^(PHt|St|Tt|Rt|Gt)[0-9a-f]{7}$')
BAD = re.compile(r'…|やること|オープンした|◎|空き室|ショッピング|はい。|^A[.:．：]?\s*はい|お引き受けしております')
NEED = {
    '送迎': re.compile(r'可|無料|円|km|ｋｍ|キロ|エリア内|範囲|まで|対応'),
    '用意するもの': re.compile(r'証明|ワクチン|狂犬病|お持ち|ご持参|準備|必要'),
    '駐車場': re.compile(r'駐車|パーキング|台'),
    '営業・受付時間': re.compile(r'[0-9０-９]{1,2}[:：時]'),
    '定休日': re.compile(r'休|無休'),
    'お支払い': re.compile(r'現金|カード|PayPay|ペイペイ|振込|振り込み|電子マネー|QR|交通系'),
}
def tidy_fact(f):
    v = re.sub(r'^\s*(Q|A)[.:．：]\s*', '', f.get('v', '')).strip()
    v = re.sub(r'\s*詳しい対応エリアはこちら\s*$', '', v)
    if len(v) < 8 or BAD.search(v): return None
    n = NEED.get(f.get('k'))
    if n and not n.search(v): return None
    if f.get('k') == '営業・受付時間' and re.search(r'1泊は|営業時間外', v): return None
    f['v'] = v
    return f
def walk(x):
    if isinstance(x, dict):
        if IDRE.match(str(x.get('id', ''))) and isinstance(x.get('facts'), list):
            x['facts'] = [g for g in (tidy_fact(f) for f in x['facts']) if g]
        for v in x.values(): walk(v)
    elif isinstance(x, list):
        for v in x: walk(v)
# まとめ・紹介のページ（店の公式サイトではない）。ホストだけでは分からないものはURL全体で見る
DENY_URL = re.compile(r'inumado\.com/.|maruone\.com/blog|feedon\.jp/shop/$|biz-maps|pochica|petstation\.jp/shop|rairai|intopet|kawaii-wanko|localstyle|happytry|pet-systems|npet\.jp|toredog|goguynet|bohseipharmacy|yamatopi|pigcat|trimmingfan|ivry\.jp|chirashi\.ne\.jp|townnews|safely\.co\.jp|min-breeder|trimmer-agent|a-japan\.jp|we-love-animals|dshugd\.com/access|trimeet\.jp', re.I)
# 分野の検索（相模原・横須賀は登録一覧が公開されていない）で見つけた店は、公式サイトの文を読んで決めた分野だけに入れる
CAT_FIX = {
 'Dog Salon LULUN': 'hotels', '動物病院ヘルスペット しつけ教室': 'trainers', 'CATSPAW': 'hotels sitters', '動物病院ヘルスペット 老犬ホーム': 'homes',
 'MKPわんこホーム': 'homes hotels', '老犬ホーム ちびたんの家': 'homes', 'しっぽフリフリ': 'homes', 'Sweeties': 'sitters', '木下動物病院': 'hotels',
 '犬の保育園 Allenatore': 'trainers', 'ドッグスクール ユナイテッド': 'trainers', 'ドギーベリー': 'hotels', 'ペテモどうぶつ医療センター相模原 しつけ教室': 'trainers',
 'PAW HOUSE POPPY ROAD／日本ペットシッターサービス横須賀中央店': 'sitters', 'TrimmingCar FANBO': 'groomers', 'Dog Salon ACO': 'groomers',
 'トリミングカー バリー': 'groomers', 'Trimmingcar Wish': 'groomers',
}
def fix_cats(d, cat_of_file):
    if not isinstance(d, dict): return
    for k, v in d.items():
        if not isinstance(v, list): continue
        cat = cat_of_file or k
        d[k] = [x for x in v if not (isinstance(x, dict) and IDRE.match(str(x.get('id', ''))) and
                (DENY_URL.search(x.get('url', '')) or (x.get('name') in CAT_FIX and cat not in CAT_FIX[x['name']].split())))]
SITTER_NAME = re.compile(r'シッター|sitter', re.I)
def drop_sitters_as_hotels(d):
    """名前がシッターでホテルと名乗っていない事業者は、ホテルの一覧に入れない（シッターのページの「ホテルとちがって」の文で分野をまちがえるため）。"""
    def bad(x): return isinstance(x, dict) and str(x.get('id', '')).startswith('PHt') and SITTER_NAME.search(x.get('name', '')) and not re.search(r'ホテル|hotel|預か', x.get('name', ''), re.I)
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, list): d[k] = [x for x in v if not bad(x)]
for fn in FILES:
    s = open(fn).read(); d = json.loads(s); walk(d); drop_sitters_as_hotels(d); fix_cats(d, {'tools/hotels.json': 'hotels', 'tools/trainers.json': 'trainers', 'tools/sitters.json': 'sitters', 'tools/grooming.json': 'groomers', 'tools/rojin.json': 'homes'}.get(fn))
    t = json.dumps(d, ensure_ascii=False, indent=1)
    # 元の書き方（インデント）を保つため、変わったときだけ書く
    if json.loads(t) != json.loads(s):
        open(fn, 'w').write(t + ('\n' if s.endswith('\n') else ''))
        print('tidied', fn)
