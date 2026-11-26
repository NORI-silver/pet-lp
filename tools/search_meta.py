"""Concise listing metadata, without volatile counts or one provider's price."""
import html
import re

BRAND_SUFFIX = "｜ペットのくらし窓口"

# Keys correspond to still-published listing categories, not individual articles.
LISTINGS = {
    "pet-hotel": ("ペットホテル", "大型犬・猫・夜間のお世話",
                  "大型犬や猫の受け入れ、夜間スタッフ、個室・多頭同室、宿泊料金や送迎の条件を比べられます。"),
    "pet-sitter": ("ペットシッター", "訪問エリア・料金・対応動物",
                   "自宅に来て食事や散歩、留守中のお世話を頼める事業者を探せます。訪問エリアや料金、犬・猫・小動物への対応を比べられます。猫専門のキャットシッターも探せます。"),
    "trimming": ("出張トリミング・トリミングサロン", "店舗・出張・シニア犬",
                 "店舗、トリミングカー、自宅に来る施術を比較。犬種・体重・年齢の条件や料金、送迎の有無を確認できます。"),
    "dog-trainer": ("ドッグトレーナー・犬のしつけ教室", "出張・パピークラス・教室・預かり",
                    "吠えや散歩の困りごと、子犬のパピークラスを相談できる事業者を探せます。教室・訪問・預かりの違い、体験、資格、公開料金を確認できます。"),
    "sougi": ("ペット葬儀・火葬・霊園", "個別火葬・立ち会い・返骨",
              "個別火葬と合同火葬の違い、立ち会い・返骨、体重別の費用や納骨の条件を比較。自治体の受付案内も確認できます。"),
    "dogrun": ("ドッグラン", "室内・料金・犬の大きさ・利用条件",
               "犬の体重制限、利用・登録料、営業時間、貸切やワクチンの条件を確認できます。雨の日も使える室内・屋内のドッグランも探せます。"),
    "hospital": ("動物病院", "診療対象・夜間救急・往診",
                 "動物の種類や往診、夜間・救急などの条件で探せます。受け入れの範囲、受付や施設の案内を確認できます。"),
    "hinan": ("ペットと避難", "同行避難・避難所の受け入れ条件",
              "地域ごとに、ペットを連れて避難するときの受け入れ条件や必要な持ち物を、自治体の案内をもとに確認できます。"),
    "jichitai/maigo": ("ペットが迷子になったら", "届け先・探し方・ペット探偵",
                       "犬や猫が迷子になったときに、地域の届け先、今日やること、迷子チラシ、ペット探偵の捜索方法と料金を確認できます。"),
    "jichitai/tebanasu": ("ペットを飼い続けるのが難しいとき", "預け先と相談窓口",
                          "ペットの世話を続けにくくなったとき、短期の預け先や老犬ホーム、自治体の相談窓口と、相談前にできることを確認できます。"),
}

def listing(slug, place=None):
    if slug not in LISTINGS:
        return None
    name, points, answer = LISTINGS[slug]
    if slug in ("jichitai/maigo", "jichitai/tebanasu", "hinan") and not place:
        return f"{name}｜{points}{BRAND_SUFFIX}", answer
    if place:
        return f"{place}の{name}｜{points}{BRAND_SUFFIX}", f"{place}で{name}を探す方へ。{answer}"
    return f"全国の{name}｜{points}{BRAND_SUFFIX}", f"{name}を都道府県ごとに探せます。{answer}"

def rewrite_hub(markup, route):
    spec = listing(route)
    if not spec:
        return markup
    title, desc = map(lambda x: html.escape(x, quote=True), spec)
    markup = re.sub(r"<title>[^<]*</title>", lambda _: f"<title>{title}</title>", markup, count=1)
    for label, value in (('name="description"', desc), ('property="og:title"', title),
                         ('property="og:description"', desc)):
        markup = re.sub(r'<meta ' + label + r' content="[^"]*">',
                        lambda _: f'<meta {label} content="{value}">', markup, count=1)
    return markup
