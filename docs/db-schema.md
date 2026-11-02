# 事業者DBの型 v0（[C] DB ／ [D] 検証）

SHIOKONBU Pet 構想（`docs/concept.md`）の [C]「共通項目＋サービス固有項目」を、検索・計算できる形にした最初の型。2026-11-02 作成。
[D] でペットタクシー20〜30社を入れながら直す前提の **たたき台**。直したら下の「変更の記録」に書く。

- 本体の置き場所：運営用のスプレッドシート（「ペットタクシー 事業者データベース」。IDはリポジトリに書かない）。1行＝1事業者×1サービス。
- サイトへは「公開」の層の列だけを JSON に書き出す（手で直さない）。「非公開」の列はリポジトリに出さない（リポジトリは公開のため）。
- どの値にも **出どころ**（`src_url`・`src_quote`・`by`＝site／reply／provider／tariff）と **確認日**（`checked`）を付ける。値がない＝「分からない」で、「しない」ではない。
- 型：`bool`（はい／いいえ／空欄＝不明）・`int`・`num`・`enum`・`date`・`geo`（緯度経度）・`text`（自由記述は補足だけ）。

## 公開の層（構想 [E]「AIへの情報公開レイヤー」）

| 層 | 例 |
|---|---|
| 公開 | 名前・サービス種別・対応地域・料金の概要・大型犬対応・掲載情報確認状態 |
| マッチング経由で返す | 空き・最短お迎え時刻・詳細条件の適合・見積もりの条件 |
| 非公開 | 運営メモ・内部スコア・需要データ・連絡先の担当者・DB全件 |

## 共通項目（すべてのサービス）

| キー | 型 | 層 | 中身 |
|---|---|---|---|
| `provider_id` | text | 公開 | 事業者のID（同じ事業者の別サービスは同じID） |
| `name` | text | 公開 | 屋号 |
| `service` | enum | 公開 | taxi／rojin_home／trainer／sitter／grooming／hotel／cremation／home_care … |
| `prefs` | enum[] | 公開 | 対応する都道府県（お迎え・訪問できる県） |
| `area_text` | text | 公開 | 公式サイトの対応地域の文 |
| `base_geo` | geo | マッチング | 拠点（お店・車庫）の位置。公開は約1kmにまるめる |
| `max_km` | num | マッチング | 拠点から受ける最大の距離 |
| `hours` | text | 公開 | 営業時間の文 |
| `open_days` | enum[] | マッチング | 営業する曜日 |
| `open_from` / `open_to` | time | マッチング | 受付・営業の時刻 |
| `same_day` | bool | 公開 | 当日も受けると公式サイト・返事にはっきり書いてある |
| `lead_hours` | num | マッチング | 何時間前までに頼む必要があるか |
| `fare_model` | enum | 公開 | 距離制／時間制／定額／見積もり |
| `pay_methods` | enum[] | 公開 | 現金／カード／電子マネー／振込 |
| `pay_timing` | enum | 公開 | 乗る前／降りるとき／後日 |
| `cancel_rule` | text | 公開 | キャンセル規定の文 |
| `insurance` | bool | 公開 | 賠償の保険に入っていると書いてある |
| `license_kind` | enum[] | 公開 | 動物取扱業（保管・訓練・譲受飼養…）、一般乗用旅客自動車運送事業（緑ナンバー）など |
| `license_no` | text | 公開 | 登録番号（公式サイトに書いてあるもの） |
| `license_expiry` | date | 公開 | 登録の有効期限 |
| `qualifications` | text[] | 公開 | 愛玩動物看護師・トリマー・CPDT など |
| `contact_channel` | enum[] | 非公開 | メール／フォーム／LINE／電話（電話番号はサイトに出さない） |
| `verify_status` | enum | 公開 | 未確認／公式サイトで確認／事業者本人が確認（「掲載情報確認済み」バッジの元。認定ではない） |
| `verify_items` | enum[] | 公開 | 料金／車両／保険／資格 のうち本人が確認したもの |
| `verified_at` | date | 公開 | 事業者本人が確認した日 |
| `memo` | text | 非公開 | 運営メモ |

## ペットタクシー（`service=taxi`）

| キー | 型 | 中身 |
|---|---|---|
| `fare_base_yen` / `fare_base_km` | int / num | 初乗りの料金と距離 |
| `fare_step_yen` / `fare_step_km` | int / num | 加算の料金と距離 |
| `pickup_fee` | int or 表 | 迎車料金（定額・距離表・市区町村ごと） |
| `return_fee` | int or 表 | 回送料金 |
| `wait_yen_per_min` | num | 待機の料金 |
| `night_rate` / `night_from` / `night_to` / `night_by` | num / time / time / enum | 深夜・早朝の割増と時間帯、乗る時刻だけで決めるか |
| `same_day_fee` | int | 当日の追加料金 |
| `toll` | enum | 高速代：実費／含む |
| `tax` | enum | 税込／税別 |
| `vehicle_type` | text | 車種 |
| `vehicle_size` | enum | 軽／普通／ワゴン／ハイエース級 |
| `max_kg` | num | 1頭の最大の体重 |
| `large_dog` / `giant_dog` | bool | 大型犬／超大型犬（40kg以上など）を乗せる |
| `max_pets` | int | 何頭まで |
| `max_riders` | int | 飼い主の同乗は何人まで |
| `pet_only` | bool | ペットだけで乗せる |
| `crate` | enum | ケージ必須／なしでよい／貸し出しあり |
| `stretcher` / `slope` / `lift` / `cart` / `harness` / `big_crate` | bool | 設備（あれば耐荷重 `*_kg`・大きさ `*_cm`） |
| `assist_boarding` / `assist_lift_large` / `staff_two` | bool | 乗り降りの介助／大型犬の持ち上げ／スタッフ2名 |
| `care_senior` / `care_walk_difficulty` / `care_bedridden` / `care_postop` | bool | シニア／歩行困難／寝たきり／術後 |
| `prep_min` | int | 依頼から出発できるまでの準備時間（[E] 最短お迎え時刻） |

## ほかのサービス（いまの一覧のデータから）

| サービス | 主なキー（bool はすべて公式サイトに書いてあるときだけ） |
|---|---|
| 老犬ホーム `rojin_home` | `animals`（enum[]：犬・猫・小動物）、`large_dog`、`bedridden`、`visit_rule`、`contract`（保管／譲受飼養）、`max_kg` |
| 訪問介護 `home_care` | `bedridden`・`toilet_care`・`feeding_care`・`medication`・`large_dog_care`・`night`・`visit_from`/`visit_to`・`max_kg` |
| 出張トレーナー `trainer` | `breeds`、`max_kg`、`issue_bark`・`issue_bite`・`issue_pull`・`issue_separation`・`puppy`、`method`（enum：ほめる中心…）、`travel_area`、`first_fee`・`continue_fee`、`next_available` |
| シッター `sitter` | `animals`、`walk_only`、`medication`、`key_keep` |
| 出張トリミング `grooming` | `large`・`cat`・`senior`・`car`・`in_home`・`max_kg`（tools/grooming.json） |
| ペットホテル `hotel` | `large`・`large_basis`・`large_from_kg`・`max_kg`・`cat_only`・`separate`・`vet`・`pickup`・`senior`・`night_staff`・`camera`・`run`・`private_room`（tools/hotels.json） |
| 火葬・霊園 `cremation` | `kinds`（火葬・霊園・納骨堂）、`services`（合同・個別・立ち会い・お迎え・訪問火葬・納骨）、`price_example` |

## いまのデータとの対応

- ペットタクシー：事業者マスターの facts（26項目、出典つき）→ 上の共通項目とタクシーの項目へ移す。`area`→`prefs`/`area_text`、`hours`→`hours`/`open_*`、`lead`→`same_day`/`lead_hours`、`large`→`large_dog`/`max_kg`、`riders`→`max_riders`、`petonly`→`pet_only`、`cage`→`crate`、`care`→`care_*`・`assist_*`、`fare`/`pick`/`wait`/`night`/`nightspan`/`toll`→料金の列、`pay`/`paytime`/`cancel`→共通、`plate`→`license_kind`。
- 料金の数字は tariffs（料金表を数字にしたもの）から。
- ほかのサービスは `tools/*.json` の列をそのまま使う。

## [D] で確かめること

- 取れない項目（公式サイトにほぼ書いていない：設備の耐荷重、`prep_min`、`max_km`、保険）
- 会社ごとに定義が違う項目（「大型犬」の体重、夜間の時間帯、迎車料金の決め方）
- マッチングに効く項目と、要らない項目

## 変更の記録

- v0（2026-11-02）：たたき台。
