"""確認済み施設自身のGoogle Mapsへのリンク。Places APIを呼ばず、口コミ数・点数・本文を保存しない。"""
from html import escape
from urllib.parse import urlencode

# 2026-11-25。公開の公式所在地・会社名/支店名と照合し、地図に口コミが1件以上ある施設のみ。
# 同じ店名でも住所が違うSOS渋谷店・口コミ0件の箱・ドックは含めない。
_PLACES = {
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
    label = {"company": "会社全体の口コミ（Google Maps）↗", "facility": "施設全体の口コミ（Google Maps）↗"}.get(scope, "Google Maps の口コミ ↗")
    return f'<a class="{escape(cls, quote=True)}" href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{label}</a>'
