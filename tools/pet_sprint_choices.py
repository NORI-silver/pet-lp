"""Source-checked, local comparison examples for selected existing routes."""
from html import escape

CHECKED = "2026年11月27日"

def choice(key, title, intro, rows, next_link=""):
    entries = "".join(
        f'<dt><strong>{escape(name)}</strong></dt><dd>{escape(body)} '
        f'<a href="{escape(url)}">掲載元・利用条件</a></dd>'
        for name, body, url in rows
    )
    return (
        f'<section class="emg-tips" id="{escape(key)}"><h2>{escape(title)}</h2>'
        f'<p>{escape(intro)}</p><dl>{entries}</dl>'
        f'<p>{CHECKED}確認。条件が書かれていない場合は、利用可・追加料金なしとは限りません。</p>{next_link}</section>'
    )

AICHI_OUTDOOR = choice(
    "aichi-outdoor-choices", "愛知の屋外ドッグラン：大型犬・貸切・事前登録で選ぶ",
    "ほかの犬と会わずに遊びたいときは貸切、料金を抑えたいときは公園も候補です。体重の区分、予約や証明書の有無まで確認しましょう。",
    [
        ("大型犬の時間帯が分かる：山田農園 FARM＆DOGS（岡崎市）",
         "10kg以上は毎時30分から。同行者1人・2頭まで1日660円（税込）。受付でリストバンドを受け取り、狂犬病・混合ワクチンの接種証明を持参します。",
         "https://mitsui-shopping-park.com/mop/okazaki/special/pets/pdf/kiyaku.pdf"),
        ("他の犬と時間を分けたい：アミューズワン（豊田市）",
         "完全貸切の屋外ラン。大型犬も利用でき、1区画は1時間2,000円（税込）。完全予約制で、1年以内の狂犬病予防接種と5種以上の混合ワクチン接種が条件です。",
         "https://www.amuse-wan.jp/guide/"),
        ("先に登録して無料で使う：蘇南公園（江南市）",
         "利用・登録とも無料。事前登録と年1回の更新が必要です。新規は犬の登録証明、狂犬病・混合ワクチンの証明、全身写真を用意します。",
         "https://www.city.konan.lg.jp/kurashi/kouen/1005732/1003911.html"),
    ],
)
SAITAMA_TRAINING = choice(
    "saitama-training-choices", "埼玉で犬のしつけを頼む：訪問・通学と最初の費用",
    "家で吠える困りごとなら、どんな場面で起きるかを家で見てもらえる訪問が候補です。まず飼い主さんと一緒に試したいなら、通学の個別体験も選べます。相談だけとレッスン込みの料金は分けて比較してください。",
    [
        ("訪問で吠えや散歩の引っ張りを相談：ドッグトレーニング ノイ（所沢市）",
         "相談のみは5,000円に交通費が加わります。吠えや引っ張りを扱う訪問の基本コースは10回48,000円。初回の相談だけで、コースを受ける費用は含みません。",
         "https://noynao.com/tokorozawa-dogtraining/"),
        ("通学の個別体験：ペットフェリーチェ 大宮見沼",
         "家族も参加できるマンツーマンの体験は初回5,500円。困っている場面を相談して、家で続ける練習方法も確認できます。",
         "https://petfelice-shelter.jp/training/"),
    ],
)
OSAKA_GROOMING = choice(
    "osaka-grooming-cost", "大阪の出張トリミング：出張費と犬の条件を比較",
    "同じコースでも、出張料と実費で支払いが変わります。施術場所、犬の体重・年齢、当日に加わる費用を先に確認しましょう。",
    [
        ("自宅前の車内：THE DOG Salon Trimming Wagon 枚方店",
         "小型犬・中型犬。枚方、交野、寝屋川、高槻、四條畷を案内。場所によって出張費が加わるため、住所と犬種を伝えて総額を確認してください。",
         "https://thedog-wagon.jp/area/s0013/"),
        ("自宅内：Dog trim MARU（守口市近郊）",
         "小型犬向けで年齢の一律制限なし。守口市から片道15km以内かつ車で30分以内。美容代に出張費1,100〜2,200円と、有料道路・駐車場を使う場合の実費が加わります。訪問は女性のお客様が在宅の日が条件です。",
         "https://dogtrimmaru.crayonsite.info/p/2/"),
        ("大型犬の訪問例：ペットケアステーション大阪",
         "堺市堺区を中心に堺市・大阪市南部へ。ラブラドールのシャンプーは基本6,000円＋出張料8,800円で14,800円（税込）。交通費・駐車代などの実費や、毛のもつれによる追加料金は別です。",
         "https://petcare-station.com/trim/visit-triming/"),
    ],
    '<p><a href="#ffPlace">大阪の事業者を地域・受け入れ条件で絞り込む</a></p>',
)
