# [B] 2026-11-14 Nori「葬儀、火葬、迷子、躾、ホテルとか他も全部犬種ごとにフィルターして、それぞれの情報があるほうがいいね」
# 記事の「うちの子で見る」（犬種・体重のしぼりこみ、tools/visual.py の breeds）で使う犬種の一覧。
#  - name・group・trait・url は ジャパンケネルクラブ（JKC）の犬種のページ（2026-11-14 に確認）。trait は「習性／性格」の文をそのまま。
#  - kg は体重の区分（小型・中型・大型など）に当てはめるためだけの目安。JKC が体重を書いている犬種は kg_src="JKC"、
#    書いていない犬種（体高だけ）は一般的な目安で kg_src="目安"。記事の金額などの計算には使わない（区分にだけ使う）。
#  - tags：短頭種（brachy）など、記事のカードを犬種のなかまで出すときの印。
# 犬種を足すときは JKC のページで確かめてから。猫は id="cat"（犬種ではないが、同じ選択欄に出す）。

JKC = "https://www.jkc.or.jp/breeds/"

BREEDS = [
 dict(id="tpoodle", name="トイ・プードル", kg=(2, 4.5), kg_src="目安", group=9, url=JKC + "poodle/",
      trait="忠誠心、学習能力及び訓練性能で知られており、そのためコンパニオン・ドッグとして非常に適している。"),
 dict(id="chihuahua", name="チワワ", kg=(1, 3), kg_src="JKC", group=9, url=JKC + "chihuahua/",
      trait="機敏で注意深く、活発であり、大変勇敢である。"),
 dict(id="dachs", name="ミニチュア・ダックスフンド", kg=(3.5, 6), kg_src="目安", group=4, url=JKC + "dachshund/",
      trait="生まれつき友好的で、落ち着きがあり、怖がりでも、攻撃的でもない。情熱的で、辛抱強く、優れた嗅覚を持ち、素早い狩猟を行う。"),
 dict(id="pome", name="ポメラニアン", kg=(1.5, 3.5), kg_src="目安", group=5, url=JKC + "pomeranian/",
      trait="常に注意深く、活発で、主人への忠誠心が非常に強い。たいへん学習能力が高く、訓練しやすい。"),
 dict(id="shiba", name="柴", kg=(7, 11), kg_src="目安", group=5, url=JKC + "shiba/", tags=["jp"],
      trait="忠実で、感覚鋭敏、警戒心に富んでいる。"),
 dict(id="mschnauzer", name="ミニチュア・シュナウザー", kg=(4, 8), kg_src="JKC", group=2, url=JKC + "miniature-schnauzer/",
      trait="利口で、怖いもの知らず、忍耐強く、敏捷である。"),
 dict(id="yorkie", name="ヨークシャー・テリア", kg=(1.5, 3.2), kg_src="JKC", group=3, url=JKC + "yorkshire-terrier/",
      trait="用心深く、利口なトイ・テリアである。気質は安定しており、勇敢である。"),
 dict(id="frenchie", name="フレンチ・ブルドッグ", kg=(8, 14), kg_src="JKC", group=9, url=JKC + "french-bulldog/", tags=["brachy"],
      trait="社交的、且つ、活発で、遊び好きで、独占欲が強く、鋭敏なコンパニオン・ドッグである。"),
 dict(id="shihtzu", name="シー・ズー", kg=(4.5, 8), kg_src="JKC", group=9, url=JKC + "shih-tzu/", tags=["brachy"],
      trait="理解力があり、活動的で、敏活である。友好的で、自立心がある。"),
 dict(id="maltese", name="マルチーズ", kg=(2, 4), kg_src="目安", group=9, url=JKC + "maltese/",
      trait="活発で、優美だがたくましく、気品がある（一般外貌より）。"),
 dict(id="papillon", name="パピヨン", kg=(2, 5), kg_src="目安", group=9, url=JKC + "papillon/",
      trait=""),
 dict(id="mpin", name="ミニチュア・ピンシャー", kg=(4, 6), kg_src="JKC", group=2, url=JKC + "miniature-pinscher/",
      trait="活発で、元気のよい、自信に満ちた穏やかな性格である。"),
 dict(id="pug", name="パグ", kg=(6.3, 8.1), kg_src="JKC", group=9, url=JKC + "pug/", tags=["brachy"],
      trait="かなりの愛嬌があり、威厳と理解力がある。安定した性格で、愉快で、活発な性格である。"),
 dict(id="cavalier", name="キャバリア・キング・チャールズ・スパニエル", kg=(5.4, 8), kg_src="JKC", group=9, url=JKC + "cavalier-king-charles-spaniel/",
      trait="運動好きで、愛情深く、恐れ知らずである。明るく、友好的で攻撃性はない。"),
 dict(id="jrt", name="ジャック・ラッセル・テリア", kg=(5, 6), kg_src="JKC", group=3, url=JKC + "jack-russell-terrier/",
      trait="活発であり、機敏で活動的なテリアである。大胆不敵。友好的だが、沈着冷静である。"),
 dict(id="beagle", name="ビーグル", kg=(8, 14), kg_src="目安", group=6, url=JKC + "beagle/",
      trait="狩猟を本来の機能とする快活なハウンドであり、臭跡をたどって主に野ウサギの猟を行う。用心深く、利口で、穏やかな性格である。"),
 dict(id="corgi", name="ウェルシュ・コーギー・ペンブローク", kg=(9, 12), kg_src="JKC", group=1, url=JKC + "welsh-corgi-pembroke/",
      trait="外見は大胆で、働き者。外向的で、友好的。神経質であったり、攻撃的ではない。"),
 dict(id="border", name="ボーダー・コリー", kg=(14, 22), kg_src="目安", group=1, url=JKC + "border-collie/",
      trait="鋭敏で、注意深い。又、責任感があり、聡明。神経質でも、攻撃的でもない。"),
 dict(id="golden", name="ゴールデン・レトリーバー", kg=(25, 36), kg_src="目安", group=8, url=JKC + "golden-retriever/",
      trait="従順で、利口で天賦の作業能力を備える。優しく、友好的で、自信に満ちている。"),
 dict(id="lab", name="ラブラドール・レトリーバー", kg=(25, 36), kg_src="目安", group=8, url=JKC + "labrador-retriever/",
      trait="気立てが良く、たいへん聡明である。理解力があり、鋭敏で、柔順で、人に喜ばれるのを好む。"),
 dict(id="bernese", name="バーニーズ・マウンテン・ドッグ", kg=(35, 50), kg_src="目安", group=2, url=JKC + "bernese-mountain-dog/",
      trait="日常生活では自信に満ち、注意深く、油断がなく、また怖いもの知らず。性格が良く飼い主には献身的で、他人に対しても穏やかで、自信を持って接する。"),
]
BY_ID = {b["id"]: b for b in BREEDS}

# JKC のグループ（犬種のなかま）。説明は JKC の各グループのページの文。
GROUPS = {
 1: ("1G 牧羊犬・牧畜犬", "家畜の群れを誘導・保護する犬", JKC + "breed_category/01g/"),
 2: ("2G 使役犬", "番犬、警護、作業をする犬", JKC + "breed_category/02g/"),
 3: ("3G テリア", "", JKC + "breed_category/03g/"),
 4: ("4G ダックスフンド", "地面の穴に住むアナグマや兎用の猟犬", JKC + "breed_category/04g/"),
 5: ("5G 原始的な犬・スピッツ", "日本犬を含む、スピッツ(尖ったの意)系の犬", JKC + "breed_category/05g/"),
 6: ("6G 嗅覚ハウンド", "大きな吠声と優れた嗅覚で獲物を追う獣猟犬", JKC + "breed_category/06g/"),
 8: ("8G 7グループ以外の鳥猟犬", "レトリーバー、フラッシング・ドッグ、ウォーター・ドッグ", JKC + "breed_category/08g/"),
 9: ("9G 愛玩犬", "家庭犬、伴侶や愛玩目的の犬", JKC + "breed_category/09g/"),
}

# 体重の区分（ミックスの子や、一覧にない犬種はこちらで選ぶ）。(キー, 表示, 下限kg, 上限kg（未満）)
SIZES = [
 ("s", "小型犬（10kg未満）", 0, 10),
 ("m", "中型犬（10〜25kg）", 10, 25),
 ("l", "大型犬（25kg以上）", 25, 200),
]

def keys_of(b):
    """犬種のカードに当たるキー：犬種のid・グループ（g1 など）・tags"""
    return [b["id"], f"g{b['group']}"] + list(b.get("tags", []))
