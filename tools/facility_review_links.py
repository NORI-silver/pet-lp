"""確認済み施設自身のGoogle Mapsへのリンク。Places APIを呼ばず、口コミ数・点数・本文を保存しない。"""
from html import escape
from urllib.parse import urlencode

# 2026-11-25。公開の公式所在地・会社名/支店名と照合し、地図に口コミが1件以上ある施設のみ。
# 同じ店名でも住所が違うSOS渋谷店・口コミ0件の箱・ドックは含めない。
_PLACES = {
    ("sougi", "S06fda3"): ("八千代ペット霊園 方丈苑妙見寺", "ChIJK03V3Rt-ImARq3hMbg4sH18"),  # https://ypet.info/price 八千代市吉橋1457
    ("sougi", "S3f9df6"): ("平和会ペットメモリアルパーク", "ChIJgU4Pyv_5GGARomAhA1JZyyg"),  # https://www.heiwakai.co.jp/about/access/ 隣接する青葉区・麻生区の両住所と電話が同じ
    ("sougi", "S0b9ae7"): ("海岸寺ペット霊園やすらぎの里", "ChIJBzMpw4Z8UTURnqmUyzc3uTA"),  # https://kagawa-pet.com/pages/19/ https://www.aeonlife-petsou.jp/reien/kagawa-pet 多度津の霊園。高松事務所は別
    ("emergency", "E04"): ("ペットタクシーAnimals", "ChIJnW8VOENbGGARfeJAug75NII"),  # https://h12150825.wixsite.com/taxi-animals 公式と屋号・電話が一致
    ("emergency", "E15"): ("ペットタクシーZERO", "ChIJ3fhbnrBxAWARfATSlLlORiE"),  # https://zero808.co.jp/pettaxi/ 公式と所在地・電話が一致
    ("rojin", "R048"): ("まるねこ", "ChIJHXNDl1lhGGAROzTX8FtPFKk"),  # https://maruneco.jp/cathotel/ 羽田3-16-10 白山荘104（施設全体）
    ("rojin", "R105"): ("ペットケアサロンえがお", "ChIJ81wI9zmHImARhtAOqSSG7xo"),  # https://pet-care-egao.com/about 佐倉市井野1327-2と電話が一致（施設全体）
    ("dogrun", "D143"): ("WANCOTT", "ChIJVVUVd-RcGGAR376zrJ0zJSs"),  # https://www.wancott.com/access/ 山下町168-1・電話一致（施設全体）
    ("dogrun", "D187"): ("ワクワクドッグランド神戸六甲（ドッグラン＆ドッグホテル）", "ChIJTVTQiK-JAGARI2DufzCQoYI"),  # https://wakuwaku-dogland.com/indoor_dogrun.html 屋号・ドッグランの電話一致（施設全体）
    ("dogrun", "D212"): ("DOG RUN TOKYO", "ChIJoSot0FaNGGARoXZIbEUghKw"),  # https://dogrun-tokyo.jp/access/ 千駄ケ谷3丁目50-3・アーバンノット原宿1階
    ("dogrun", "D213"): ("ペテモ幕張新都心店", "ChIJNREpmeWBImAR81oonEvodm0"),  # https://www.aeonpet.com/shop/p_makuhari/access/ 豊砂1-8の同店舗、屋外と室内の口コミは分けない
    ("dogrun", "D217"): ("ペテモ千葉ニュータウン店", "ChIJmU9lvjx8ImARiXYOSowmu90"),  # https://www.aeonpet.com/shop/chibanewtown/index.html 中央北2-2と電話一致
    ("dogrun", "D218"): ("ペテモピアシティ稲毛海岸店", "ChIJf_QXGbuDImARyZuLJqiQNo4"),  # https://aeonpet.com/shop/pia-city-inagekaigan/access/index.html B棟1階と用品店の電話一致、併設病院・サロンは別
    ("dogrun", "D001"): ("代々木公園ドッグラン", "ChIJN9-qU7SMGGARhCpTp43adx8"),  # https://www.yoyogidogrun.jp/home/アクセス
    ("sitter", "St4e0359d"): ("キャットシッターねこやま", "ChIJp4doO8NZGGARsPlc6CkFydk"),  # https://www.necoyama.net/ 同じ屋号、横浜市旭区本村町、電話番号
    ("trainer", "T111"): ("犬のようちえん 代官山教室", "ChIJTyI_woyLGGARR0-YqFtqYUg"),  # https://animalplaza.co.jp/class/daikanyama.html 恵比寿南3-7-7
    ("trim", "G002"): ("ドックシャンプー わん", "ChIJYc_CNmspC18RoCnfuc0T_5U"),  # https://www.dogshampoo.jp/ 北9条東9丁目2-36、電話番号
    ("hotel", "PH053"): ("ドッグガーデン HAMA&WAN", "ChIJlbutbtneGmARbsSAhplZP4Y"),  # https://www.hama-wan.com/ 富塚町5117、電話番号、複合施設
    ("detective", "https://catpro.jp/"): ("キャットプロ株式会社", "ChIJ1f2BlwqYkAoRc_PsfmBj0QA"),  # https://catpro.jp/company/ 東京本社・大阪支店、会社全体の口コミ
}


def link(category, row, cls="fc-a fc-a-star", *, scope=None):
    # 検索語・住所から自動推測しない。探偵には事業者の正式URL、それ以外は掲載IDを使う。
    index = row.get("url") if category == "detective" else row.get("id")
    hit = _PLACES.get((category, index))
    if not hit:
        return ""
    name, place_id = hit
    url = "https://www.google.com/maps/search/?" + urlencode(
        {"api": 1, "query": name, "query_place_id": place_id})
    label = {"company": "会社全体の口コミ（Google Maps）↗", "facility": "施設全体の口コミ（Google Maps）↗", "store": "店舗全体の口コミ（Google Maps）↗"}.get(scope, "Google Maps の口コミ ↗")
    return f'<a class="{escape(cls, quote=True)}" href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{label}</a>'
