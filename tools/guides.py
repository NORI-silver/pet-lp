# ガイドの組み立て。本文・検索意図は guide_editorial.py、施設固有情報と料金は専用ファイルを参照。
import json
from pathlib import Path
from guide_editorial import BASIC_GUIDES, improve_details
from facility_guides import FACILITY_GUIDES
from care_guides import CARE_GUIDES

_BASE_META = {'what-is-pet-taxi': {'img': 'what-is-pet-taxi.jpg', 'img_alt': 'ペットタクシーの後部座席でキャリーに入って休む犬と、そばに座る飼い主'},
 'taxi-with-pet': {'img': 'what-is-pet-taxi.jpg', 'img_alt': 'ペットタクシーの後部座席でキャリーに入って休む犬と、そばに座る飼い主'},
 'hospital': {'img': 'hospital.jpg', 'img_alt': '動物病院の前でペットタクシーから降りる、キャリーに入った猫と飼い主'},
 'cat': {'img': 'cat.jpg', 'img_alt': '毛布を敷いたキャリーの中でくつろぐ猫'},
 'senior': {'img': 'senior.jpg', 'img_alt': '車内のやわらかいマットの上で、ブランケットをかけて休むシニア犬'},
 'large-dog': {'img': 'large-dog.jpg', 'img_alt': 'スロープを歩いてワゴン車に乗り込むラブラドール・レトリーバー'},
 'airport-moving': {'img': 'airport-moving.jpg', 'img_alt': '空港の前で、スーツケースとケージに入ったダックスフンドを車から降ろす飼い主'},
 'small-animals': {'img': 'small-animals.jpg',
                   'img_alt': '車の後部座席でシートベルトに固定したキャリーの中で休むうさぎと、キャリーに手を添える飼い主',
                   'published': '2026-10-31'},
 'birds-reptiles': {'img': 'birds-reptiles.jpg',
                    'img_alt': '車の後部座席で、布をかけた鳥かごの中のセキセイインコと、透明なケースに入ったリクガメ',
                    'published': '2026-10-31'},
 'farewell': {'img': 'farewell.jpg',
              'img_alt': '車の後部座席で、白いブランケットにくるんだ小さな犬を両腕でそっと抱く飼い主',
              'published': '2026-10-31'},
 'nervous-pet': {'img': 'nervous-pet.jpg',
                 'img_alt': '車の後部座席で、布をかけたキャリーの中から外を見る小型犬と、扉の格子越しに指を差し出す飼い主',
                 'published': '2026-10-31'},
 'discharge-transfer': {'img': 'discharge-transfer.jpg',
                        'img_alt': '病院の前に止めた車の荷室で、術後の服を着てマットに横になる柴犬に、飼い主がブランケットをかけている様子',
                        'published': '2026-10-31'},
 'grooming-hotel': {'img': 'grooming-hotel.jpg',
                    'img_alt': 'お店の前で、リードをつけたトイ・プードルが車の後部座席に乗り込もうとしている様子',
                    'published': '2026-10-31'},
 'new-family': {'img': 'new-family.jpg',
                'img_alt': '車の後部座席で、毛布を敷いたキャリーから外をのぞく子猫と、そばに置かれたおもちゃ',
                'published': '2026-10-31'}}
_LINK_LABELS = {'what-is-pet-taxi': 'ペットタクシーとは？電車・タクシー・マイカーとの違い',
 'taxi-with-pet': 'ふつうのタクシーに犬・猫は乗れる？',
 'hospital': '動物病院への通院にペットタクシーを',
 'cat': '猫の移動をやさしく。キャリーの慣らし方と車での過ごし方',
 'senior': 'シニア犬・シニア猫、介護中の子の移動',
 'large-dog': '大型犬の移動に、ペットタクシーという選択',
 'airport-moving': '引っ越し・空港への送迎。ペットと一緒の大移動',
 'small-animals': 'うさぎ・フェレット・ハムスターもペットタクシーで',
 'birds-reptiles': '鳥・爬虫類・魚の移動。ペットタクシーで頼めること',
 'farewell': 'お別れのとき、火葬場や霊園まで一緒に',
 'nervous-pet': '怖がり・吠える・車酔いする子の移動',
 'discharge-transfer': '退院・転院、遠くの大学病院へ通うとき',
 'grooming-hotel': 'トリミング・ペットホテルの送り迎え',
 'new-family': '新しい家族を迎えに行くとき（譲渡会・保護団体・ブリーダー）'}
for guide in BASIC_GUIDES:
    guide['link_title'] = _LINK_LABELS[guide['slug']]
    guide.update(_BASE_META[guide['slug']])
    guide.setdefault('published', '2026-10-27')
improve_details(FACILITY_GUIDES + CARE_GUIDES)
GUIDES = BASIC_GUIDES + FACILITY_GUIDES + CARE_GUIDES

# 記事写真は全記事で個別に登録し、重複や割り当て漏れを検出する。
_images = json.loads(Path(__file__).with_name('article_images.json').read_text(encoding='utf-8'))
if set(_images) != {g['slug'] for g in GUIDES}:
    raise ValueError('記事と写真の登録が一致していません')
if len({v['img'] for v in _images.values()}) != len(GUIDES):
    raise ValueError('記事写真が重複しています')
for guide in GUIDES:
    guide.update(_images[guide['slug']])
