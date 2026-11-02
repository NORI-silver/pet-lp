# ガイド記事の写真の差し替え（13枚）の指示書：使い回しをなくす

2026-11-02 作成。ChatGPT（画像生成）で作って、Claude のスレッドに貼ってください。サイズの調整（1200×800）・jpg と webp への変換・圧縮・差し替えはこちらでやります。
届くまでは今の写真のままです（ページは崩れません）。

**2026-11-02 更新：12枚を差し替え済み。残りは 7. pet-only.jpg だけです。**

## いまの状態（どこで使い回しているか）

ガイド記事26本のうち、13本がほかの記事の写真を借りています（写真は13枚だけ）。

| 今の写真 | 本来の記事 | 借りている記事 |
|---|---|---|
| what-is-pet-taxi.jpg（車内でキャリーの犬と飼い主） | /guide/what-is-pet-taxi/ | /guide/taxi-with-pet/・/guide/fare/・/guide/choose/ |
| hospital.jpg（夜の動物病院の前で猫と飼い主） | /guide/hospital/ | /guide/same-day/・/guide/jarmec-kawasaki-taxi/・/guide/jsamc-tokorozawa-taxi/ |
| cat.jpg（部屋のキャリーでくつろぐ猫） | /guide/cat/ | /guide/jarmec-tokyo-taxi/・/guide/jamc-shibuya-taxi/（病院への通院の記事なのに家の中の写真） |
| large-dog.jpg（スロープを上るラブラドール） | /guide/large-dog/ | /guide/multi-pet/（多頭の記事なのに1頭）・/guide/doggys-island-taxi/ |
| airport-moving.jpg（空港の前でダックスフンド） | /guide/airport-moving/ | /guide/long-distance/（長距離の記事なのに空港） |
| grooming-hotel.jpg（サロンの前でトイプードル） | /guide/grooming-hotel/ | /guide/pet-only/（飼い主が付き添えない日の記事なのに飼い主が写る） |
| senior.jpg（マットで休むシニア犬） | /guide/senior/ | /guide/wancott-taxi/ |

今の写真は本来の記事にそのまま残し、借りている13本に1枚ずつ新しい写真を作ります。
トップと東京・神奈川・千葉・埼玉・43道府県のページは、トップをそのまま写したページなので同じ写真で正しく、対象外です。

## ファイルの決まり

- ファイル名は下の表のとおり（記事のURLと同じ名前）。置き場所は `img/guide/`。
- 横長 3:2（ChatGPT の「横長」1536×1024 でOK）。こちらで 1200×800 の jpg と webp にして、1枚150KB前後に圧縮します。
- 施設名の記事（病院・ホテルなど6本）は「紹介施設の写真ではありません」と書いているので、**実在の建物・看板に見えないように**、建物は写さないかぼかしてください。

**共通のお願い（毎回いっしょに貼ってください）**

> 写真のようにリアルで、やわらかい自然光、温かみのある色調。清潔で明るい雰囲気。動物は安心して落ち着いた表情。人物は顔がはっきり写らない後ろ姿や手元だけ。文字・ロゴ・ナンバープレート・実在の会社名や施設名・看板は入れない。横長3:2。

> (English) Photorealistic, soft natural light, warm color tone, clean and bright atmosphere. Animals look calm and relaxed. People appear only from behind or as hands, with no clearly visible faces. No text, logos, license plates, real company or facility names, or signs. Landscape 3:2.

- 実在の会社のロゴや車、人の顔がはっきり写った画像は使えません。
- 使うサービスの利用規約で、商用利用ができるかを確認してください。

| # | ファイル名 | 使う記事 | 今借りている写真 |
|---|---|---|---|
| 1 | taxi-with-pet.jpg | /guide/taxi-with-pet/ タクシーに犬・猫は乗れる？ | what-is-pet-taxi.jpg |
| 2 | fare.jpg | /guide/fare/ ペットタクシーの料金相場 | what-is-pet-taxi.jpg |
| 3 | choose.jpg | /guide/choose/ ペットタクシーの選び方 | what-is-pet-taxi.jpg |
| 4 | same-day.jpg | /guide/same-day/ 当日でも予約できる？夜間・早朝の割増 | hospital.jpg |
| 5 | multi-pet.jpg | /guide/multi-pet/ 多頭飼いのペットタクシー | large-dog.jpg |
| 6 | long-distance.jpg | /guide/long-distance/ 長距離移動 | airport-moving.jpg |
| 7 | pet-only.jpg | /guide/pet-only/ ペットだけで乗せられる？ | grooming-hotel.jpg |
| 8 | jarmec-kawasaki-taxi.jpg | /guide/jarmec-kawasaki-taxi/ 日本動物高度医療センター川崎本院へ | hospital.jpg |
| 9 | jarmec-tokyo-taxi.jpg | /guide/jarmec-tokyo-taxi/ 日本動物高度医療センター東京病院へ | cat.jpg |
| 10 | jsamc-tokorozawa-taxi.jpg | /guide/jsamc-tokorozawa-taxi/ 日本小動物医療センター（所沢）へ | hospital.jpg |
| 11 | jamc-shibuya-taxi.jpg | /guide/jamc-shibuya-taxi/ 日本動物医療センター（渋谷）へ | cat.jpg |
| 12 | doggys-island-taxi.jpg | /guide/doggys-island-taxi/ ドギーズアイランドへ | large-dog.jpg |
| 13 | wancott-taxi.jpg | /guide/wancott-taxi/ WANCOTT（横浜のホテル・介護ケア）へ | senior.jpg |

## そのまま使える指示文

**1. taxi-with-pet.jpg（ふつうのタクシーに犬・猫は乗れる？）**
> ふつうのセダン型タクシーの後部座席。飼い主のひざの上に、ふたを閉めたソフトタイプのキャリーバッグ（中にポメラニアン、メッシュ越しに顔が見える）。飼い主は両手でキャリーを支えている。座席には汚れ防止の薄いシートを敷いている。窓の外は昼の街並みでぼかし。車内の表示・料金メーター・文字は写さない。

> (English) The back seat of an ordinary sedan taxi. On the owner's lap is a closed soft-sided pet carrier with a Pomeranian visible through the mesh. The owner holds the carrier steady with both hands. A thin protective sheet is laid on the seat. Daytime city street blurred outside the window. Do not show any in-car displays, fare meter, or text.

**2. fare.jpg（料金相場と安い会社の見分け方）**
> 明るいリビングのテーブルの上。画面を伏せて置いたスマートフォン、小さな財布と硬貨、メモ用紙とペン（文字は書かない）。その奥の床に扉を閉めたハードキャリーがあり、中から柴犬がこちらをのぞいている。飼い主の手がペンを持っている。落ち着いて準備している雰囲気。

> (English) A table in a bright living room. A smartphone lying face down, a small wallet with a few coins, and a blank notepad with a pen (no writing). Behind it on the floor is a closed hard carrier with a Shiba Inu peeking out. The owner's hand holds the pen. A calm, planning-ahead mood.

**3. choose.jpg（選び方・確認ポイント）**
> 玄関の上がりかまちに、出かける前の持ち物を並べたところ。扉の閉まるハードキャリー（中にサバトラの猫）、たたんだブランケット、ペットシーツ、小さなファイル（表紙に文字なし）。しゃがんだ飼い主の手が、持ち物を一つずつ確かめている。朝のやわらかい光。

> (English) Items laid out on the step of a Japanese entryway before going out: a closed hard carrier with a silver tabby cat inside, a folded blanket, pet pads, and a small document folder with no text on the cover. The crouching owner's hands are checking the items one by one. Soft morning light.

**4. same-day.jpg（当日・夜間・早朝）**
> 夜明け前、空がうっすら青い住宅街。家の前に止まったワゴン車の後部ドアが開き、車内の明かりがあたたかく灯っている。飼い主がキャリーバッグ（中にトイプードル）を両手で抱えて車に向かう後ろ姿。街灯がやさしく光る静かな早朝。急いでいるが落ち着いた雰囲気。

> (English) A residential street just before dawn with a faint blue sky. A van is parked in front of a house with its rear door open and warm interior lights on. The owner, seen from behind, carries a pet carrier with a Toy Poodle inside in both arms toward the van. Streetlights glow softly on a quiet early morning. Hurried but calm.

**5. multi-pet.jpg（多頭飼い）**
> 広いワゴン車の荷室。清潔なマットの上に、並べて固定した2つのケージ。片方には柴犬が2頭、もう片方には茶トラの猫が入ったキャリー。どの子も落ち着いて座っている。後部ドアの外から飼い主の手がケージの扉を確かめている。昼の自然光、背景の住宅街はぼかし。

> (English) The cargo area of a spacious van. On a clean mat, two crates are secured side by side: one holds two Shiba Inus, the other holds a carrier with an orange tabby cat. All the animals sit calmly. From outside the open rear door, the owner's hand checks a crate door. Daytime natural light, residential street blurred in the background.

**6. long-distance.jpg（長距離の移動・引っ越し・帰省）**
> 高速道路を走るワゴン車の車内から見た様子。後部座席に固定した大きめのクレートの中で、ゴールデン・レトリーバーが伏せて安心して眠っている。窓の外には流れる山並みと青空（ぼかし）。そばに水のボトルとたたんだタオル。長い旅でもゆったりした雰囲気。道路標識や文字は写さない。

> (English) Inside a van driving on an expressway. In a large crate secured on the back seat, a Golden Retriever lies down, sleeping peacefully. Outside the window, mountains and blue sky stream by, blurred. A water bottle and a folded towel sit nearby. A relaxed mood on a long trip. No road signs or text.

**7. pet-only.jpg（ペットだけで乗せる）**
> 玄関先で、ペットタクシーのスタッフ（無地のポロシャツ、顔は写らない、手元と胴だけ）が、扉の閉まったハードキャリー（中にミニチュア・シュナウザー）を両手でていねいに受け取っている。家の人の手がキャリーから離れるところ。スタッフの服に文字やロゴはなし。昼のやわらかい光、信頼できる雰囲気。

> (English) At a front door, a pet taxi staff member (plain polo shirt, face not shown, only hands and torso) carefully receives a closed hard carrier with a Miniature Schnauzer inside, using both hands. The family member's hands are just letting go of the carrier. No text or logos on the staff's clothing. Soft daytime light, a trustworthy mood.

**8. jarmec-kawasaki-taxi.jpg（専門病院への通院・川崎）**
> ワンボックスカーの後部座席。シートに固定したハードキャリーの中で、ミックスの中型犬が伏せて落ち着いている。飼い主のひざの上には通院用のトートバッグと、検査結果を入れた透明なクリアファイル（中の紙の文字は読めない）。窓の外は昼の都市の道路でぼかし。病院の建物や看板は写さない。

> (English) The back seat of a minivan. In a hard carrier secured to the seat, a mixed-breed medium-sized dog lies calmly. On the owner's lap are a tote bag for the vet visit and a clear plastic folder holding test results (the paper text is unreadable). A daytime city road blurred outside the window. No hospital building or signs.

**9. jarmec-tokyo-taxi.jpg（専門病院への通院・東京）**
> 朝、住宅街の家の前。止まったワゴン車の開いた後部ドアから、飼い主がキャリーバッグ（中に白黒のハチワレ猫）を後部座席に乗せ、シートベルトで固定しているところの手元。猫はキャリーの中で落ち着いている。朝のさわやかな光、背景の家並みはぼかし。

> (English) Morning, in front of a house on a residential street. Through the open rear door of a parked van, the owner's hands place a carrier holding a black-and-white tuxedo cat onto the back seat and fasten it with the seatbelt. The cat is calm inside. Fresh morning light, houses blurred in the background.

**10. jsamc-tokorozawa-taxi.jpg（専門病院への通院・所沢）**
> 郊外の広い駐車場（建物は写さないか、遠くでぼかす）。止まったワゴン車の荷室から、スロープを使ってゆっくり降りるシニアのゴールデン・レトリーバー。飼い主の手がリードを短く持って支えている。木々の緑が見える、晴れた昼の穏やかな雰囲気。

> (English) A large suburban parking lot (no buildings, or only far away and blurred). A senior Golden Retriever slowly walks down a ramp from the cargo area of a parked van. The owner's hand holds the leash short for support. Green trees visible, a calm sunny midday.

**11. jamc-shibuya-taxi.jpg（専門病院への通院・渋谷）**
> 都会の道路わき（背景のビル街は大きくぼかす、看板の文字なし）。止まった車の後部ドアを開け、飼い主がキャリーバッグ（中にミニチュア・ダックスフンド）を胸の前で大切に抱えて降りるところの手元と足元。歩道の端で、乗り降りに気をつけている様子。昼のやわらかい光。

> (English) A roadside in the city (office buildings heavily blurred, no readable signs). The rear door of a stopped car is open; only the owner's hands and feet are shown as they step out, holding a carrier with a Miniature Dachshund carefully against their chest. They are getting out with care at the edge of the sidewalk. Soft daytime light.

**12. doggys-island-taxi.jpg（犬と泊まれるリゾートへ）**
> 緑の多い郊外の道（建物は写さない）。止まったワゴン車の開いた荷室から、リードをつけたボーダー・コリーとトイ・プードルがうれしそうに外を見ている。荷室には旅行用のバッグとおもちゃ。飼い主の手がリードを持っている。晴れた昼、わくわくするお出かけの雰囲気。

> (English) A green suburban road (no buildings). From the open cargo area of a parked van, a Border Collie and a Toy Poodle on leashes look out happily. Travel bags and toys are in the cargo area. The owner's hand holds the leashes. Sunny midday, an exciting outing mood.

**13. wancott-taxi.jpg（犬のホテル・介護ケアへ）**
> 夕方、落ち着いた建物のエントランス前（大きくぼかす、看板の文字なし）。止まったワゴン車の後部ドアの前で、飼い主の手がシニアのトイ・プードル（口元の毛が白い）をそっと抱いて、ブランケットを敷いたペット用カートに乗せているところ。あたたかい夕方の光、やさしく見守る雰囲気。

> (English) Early evening in front of the entrance of a calm building (heavily blurred, no readable signs). At the open rear door of a parked van, the owner's hands gently lift a senior Toy Poodle with a white muzzle into a pet stroller lined with a blanket. Warm evening light, a gentle, caring mood.

## 届いたあと（Claude がやること）

1. 1200×800 にして `img/guide/<ファイル名>.jpg` と `.webp` を作る。
2. `tools/guides.py`・`tools/guides_data.py`・`tools/facility_guides.py` の `img` と `img_alt`（写真の説明）を新しい写真に合わせて直す。
3. `python3 tools/gen_areas.py .` で作り直して PR → マージ。
