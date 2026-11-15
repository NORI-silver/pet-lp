#!/usr/bin/env python3
"""SNS の投稿（あるある・クイズ・実用ワザ・調べた数字）を sns/posts.json に足す。

[B] SNS。2026-11-15 Nori「SNSの投稿がほんとに面白くない」「写真か動画は絶対いれて」→ 決定カード「1〜4を日がわりで全部」。
- 4つの形（kind）：aru（あるある）・quiz（クイズ）・howto（保存したくなる実用ワザ）・data（サイトで調べた数字）。
  schedule_x.py の pick が aru → quiz → howto → data の順に日がわりで出す。
- 予約・ペットタクシーの話は入れない。リンクなし。最後にひとこと問いかける。
- 体の具合や決まりの話は、広く知られていて確かめられることだけ。数字はサイトのしらべ（tools/ のデータ）と同じものだけ。
- 写真は投稿ごとにちがうもの（sns/img/<名前>.jpg）。写真のない投稿は出さない（post_meta.py）。
  写真は sns-photos（GitHub Actions）が無料で使える写真（CC0・パブリックドメイン）の候補を集め、合うものを選んで入れる。
- クイズ：Threads では問いだけを出し、答えは次の日にその投稿への返信で出す（th と answer）。X と Instagram は答えも同じ投稿に入れる（x）。

使い方: python3 sns/feed.py [--dry]
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from schedule_x import BAN  # noqa: E402

# (kind, 名前, 本文, 写真をさがすことば(英語), クイズの答え)
FEED = [
    # 1週目
    ("aru", "cat-laptop", "猫あるある🐈\n・パソコンを開くと、キーボードの上に来る\n・高いベッドより、届いた段ボール箱\n・呼んでも来ないのに、トイレに入るとドアの前で鳴く\nおうちの子のあるある、ひとつ教えてください\n#猫のいる暮らし", "cat lying on laptop keyboard", None),
    ("quiz", "dog-spin", "Q. 犬がうんちの前にクルクル回るのはなぜ？\nA. 地面をならしている\nB. 南北の向きをそろえている\nC. まわりを確かめている\nどれだと思いますか？🐕\n#犬のいる暮らし", "dog sniffing grass", "答え：どれも説がありますが、Bには研究があります。\n犬は、地磁気が落ち着いているとき、体を南北に向けて用を足すことが多かったという2013年の研究です。ふしぎですね🧭"),
    ("howto", "car-trip", "【保存版】犬と車で出かける前の5つ🚗\n1. 出発の2時間前から、ごはんは控えめに\n2. 窓は顔が出ない高さまで\n3. 1〜2時間ごとに休けい\n4. 水とトイレシートは手の届く所に\n5. 夏も冬も、車内に置いていかない\n#犬とお出かけ", "dog in car back seat", None),
    ("data", "dogrun-free", "全国のドッグラン194か所の公式ページを、ひとつずつ読みました。\n料金を書いている146か所のうち、96か所（66%）が無料。\n高速道路のサービスエリアのランは、料金を書いている25か所すべて無料でした🐾\nお気に入りのランはありますか？\n#ドッグラン", "dogs playing in dog park", None),
    ("aru", "dog-walk-word", "犬あるある🐕\n・「さんぽ」の「さ」で、もう玄関にいる\n・おやつの袋の音だけは、どこにいても聞こえる\n・お風呂の気配を感じると、急にいなくなる\nうちの子だけ？と思ったら、いいねで教えてください\n#犬のいる暮らし", "dog waiting at door with leash", None),
    ("quiz", "cat-ancestor", "Q. 猫の祖先といわれる動物は？\nA. ライオン\nB. リビアヤマネコ\nC. トラ\nわかりますか？🐈\n#猫のいる暮らし", "tabby cat portrait", "答え：B. リビアヤマネコ\n砂漠に近い場所でくらしていたので、猫には水をあまり飲まない子が多いと言われます。器を何か所かに置くと、飲む量が増えることも💧"),
    ("howto", "winter-walk", "【保存版】冬のさんぽの4つ❄️\n1. 出る前に、部屋で少し体を動かす\n2. 帰ったら足をふく（道にまかれた融雪剤で、肉球が荒れることがあります）\n3. 暗い時間は、光るものを首輪やリードに\n4. 短毛やシニアの子は服も\n#犬の散歩", "dog walking in snow", None),
    # 2週目
    ("data", "dogrun-touroku", "ドッグランは「行けばすぐ入れる」とは限りません。\n公式ページで登録のことを書いている96か所のうち、92か所（96%）が先に利用登録がいるところでした。\n毎年登録しなおすところは31か所。\n行く前に、公式ページを見ておくと安心です🐕\n#ドッグラン", "dog behind fence dog park", None),
    ("aru", "cat-busy", "猫あるある2🐈\n・高いおもちゃより、丸めたレシート\n・忙しいときに限って、甘えてくる\n・ごはんの5分前から、じっと見つめてくる\n「わかる」と思ったら、いいねしてください\n#猫のいる暮らし", "cat staring at camera", None),
    ("quiz", "dog-sweat", "Q. 犬が汗をかくのは、体のどこ？\nA. 全身\nB. 肉球\nC. 舌\n答えはあした🐾\n#犬のいる暮らし", "dog paw close up", "答え：B. 肉球\n舌は汗ではなく、ハァハァする息で体の熱を外に出しています。暖房の効いた部屋や車の中では、ハァハァが多くないか見てあげてください🌡"),
    ("howto", "cat-vet", "【保存版】猫を動物病院へ連れていくコツ🐈\n1. キャリーは、ふだんから部屋に出しておく\n2. 上が開くキャリーだと出し入れがらく\n3. タオルをかけて、外を見えなくする\n4. 待合室では、床ではなくひざや椅子の上に\n#猫のいる暮らし", "cat in pet carrier", None),
    ("data", "night-hospital", "夜間・救急の動物病院を、全国で公式サイトから確かめました。\n県の中で確かめられたのは107か所。\n47都道府県のうち10県では、県の中で確かめられる夜間の病院が見つかりませんでした。\nいざという時の病院、今のうちに調べておきませんか🏥\n#動物病院", "veterinarian examining dog", None),
    ("aru", "big-dog", "大型犬あるある🐕\n・自分のことを、小型犬だと思っている\n・ソファの半分が、いつのまにかほぼ全部\n・しっぽで、テーブルの上の物を落とす\nおうちの子は、どれでしたか？\n#大型犬のいる暮らし", "large dog lying on sofa", None),
    ("quiz", "cat-sweet", "Q. 猫は、甘い味を感じる？\nA. 人と同じように感じる\nB. ほとんど感じない\nC. 人より強く感じる\nどっちでしょう🐈\n#猫のいる暮らし", "cat sniffing food", "答え：B. ほとんど感じない\n甘みを感じるしくみが、体の中で働いていないと言われています。おやつに夢中なのは、においや食感のほう🍗"),
    # 3週目
    ("howto", "lost-prep", "【保存版】迷子にそなえて、今日できること🔖\n1. 首輪に名前と連絡先\n2. マイクロチップの登録が、今の住所になっているか確かめる\n3. 顔・全身・模様がわかる写真を数枚\n4. 住んでいる地域の保健所・動物愛護センターを調べておく\n#犬のいる暮らし #猫のいる暮らし", "dog collar name tag", None),
    ("data", "dogrun-shorui", "ドッグランで求められるもの、全国で数えました（必要なものを書いている103か所）。\n・狂犬病の予防注射の済票 97か所\n・鑑札（犬の登録）59か所\n・混合ワクチンの証明 51か所\n出かける前に、カバンに入っているか見てみてください📄\n#ドッグラン", "dog vaccination veterinarian", None),
    ("aru", "rabbit", "うさぎあるある🐇\n・うれしいと、ジャンプしながら体をひねる\n・鼻が、ずっとヒクヒク\n・ケージを掃除した直後に、そこでトイレ\nうちの子のかわいいところ、教えてください\n#うさぎのいる暮らし", "rabbit on grass", None),
    ("quiz", "dog-colors", "Q. 犬が見分けにくい色は？\nA. 青\nB. 黄色\nC. 赤と緑\nわかりますか？🐕\n#犬のいる暮らし", "dog with red ball on grass", "答え：C. 赤と緑\n青と黄色は見分けやすいと言われます。芝生の上で赤いボールを見失うのは、そのせいかも。おもちゃは青か黄色が見つけやすいですよ🎾"),
    ("howto", "disaster-kit", "【保存版】災害にそなえて、ペットのために用意したいもの🎒\n・フードと水（少なくとも5日分）\n・薬・療法食\n・キャリーやケージ\n・トイレ用品\n・うちの子の写真（はぐれたとき用）\n#ペット防災", "dog with backpack", None),
    ("data", "joto", "保護犬・保護猫を迎える条件を、全国128の自治体の公式ページで読みました。\n・講習会を受ける 64\n・不妊・去勢の手術を約束 65\n・60〜70歳などの年齢にふれている 45\n迎えたい人は、お住まいの自治体のページを先に見ておくとスムーズです🏠\n#保護犬 #保護猫", "shelter dog looking at camera", None),
    ("aru", "winter-pet", "冬のペットあるある❄️\n・ストーブの前の一等地は、もう取られている\n・こたつに入ると、中に先客\n・毛布をたたむと、その上で寝る\nおうちの冬の定位置はどこですか？\n#猫のいる暮らし #犬のいる暮らし", "cat sleeping on blanket", None),
    # 4週目
    ("quiz", "rabbit-teeth", "Q. うさぎの歯は、大人になってものびる？\nA. のびつづける\nB. 子どものうちだけ\nC. 冬だけのびる\nどれでしょう🐇\n#うさぎのいる暮らし", "rabbit eating hay", "答え：A. のびつづける\nだから牧草をたくさん食べて、歯をすり減らすことが大事なんです🌾"),
    ("howto", "weigh", "【保存版】ペットの体重を家で量るには⚖️\n・抱っこして一緒に量り、自分の体重を引く\n・小さい子はキッチンスケールで\n・同じ時間帯に量ると、変化がわかりやすい\n体重の変化は、体調の変化に気づくヒントになります\n#犬のいる暮らし #猫のいる暮らし", "small dog in arms", None),
    ("data", "dogrun-kogata", "小型犬のエリアがあるドッグランは、どれだけある？\nエリアの区分を書いている130か所のうち、85か所（65%）に小型犬のエリアがありました。\n大きな子とぶつかるのが心配な子も、エリアが分かれていれば遊ばせやすくなります🐶\n#ドッグラン #小型犬", "small dog running", None),
    ("aru", "photo", "ペットの写真あるある📷\n・カメラを向けると、目をそらす\n・いちばんいい顔のとき、スマホが手元にない\n・スマホの写真の9割が、うちの子\nうちの子の自慢の1枚、ありますか？\n#ペットのいる暮らし", "dog looking away", None),
    ("quiz", "hamster", "Q. ハムスターのほお袋は、どこまでのびる？\nA. あごまで\nB. 肩のあたりまで\nC. しっぽまで\nどれでしょう🐹\n#ハムスターのいる暮らし", "hamster cheeks", "答え：B. 肩のあたりまで\n食べものを運んで、安心できる場所にためておくためのものです。パンパンのほっぺ、かわいいですね🌻"),
    ("howto", "winter-room", "【保存版】冬の部屋で気をつけたいこと🔥\n・暖房の前でずっと寝ていると、低温やけどになることも\n・こたつやホットカーペットの上は、のどが渇きやすいので水を近くに\n・暖房器具のコードをかじらないように\n#猫のいる暮らし #犬のいる暮らし", "cat near fireplace", None),
    ("data", "dogrun-ryokin", "お金がかかるドッグランの料金のかたち（料金を書いている146か所）\n・1回・1日いくら 41か所\n・時間ごと 17か所\n・2頭目から安くなる 12か所\n・土日祝は高くなる 6か所\n多頭の子は、2頭目からの料金も見てみてください🐕🐕\n#ドッグラン", "two dogs running together", None),
]
KINDS = ["aru", "quiz", "howto", "data"]


def width(s):
    return sum(1 if ord(c) < 0x1100 else 2 for c in s)


def x_text(text, answer):
    """X と Instagram 用。クイズは答えも入れる（ハッシュタグの前に）。"""
    if not answer:
        return text
    lines = text.split("\n")
    tags = [l for l in lines if l.startswith("#")]
    body = [l for l in lines if not l.startswith("#") and not l.startswith("答えはあした")]
    short = answer.split("\n")[0]
    return "\n".join(body + [short] + tags)


def main():
    dry = "--dry" in sys.argv
    pj = os.path.join(HERE, "posts.json")
    data = json.load(open(pj, encoding="utf-8"))
    posts = data["posts"]
    have = {p.get("key") for p in posts}
    no = max(p["no"] for p in posts)
    bad, new = [], []
    for kind, name, text, q, ans in FEED:
        x = x_text(text, ans)
        for label, t, lim in (("x", x, 280), ("th", text, 1000), ("ans", ans or "", 1000)):
            ng = [b for b in BAN if b in t]
            if width(t) > lim or ng:
                bad.append((name, label, width(t), ng))
        key = f"{kind}:{name}"
        if key in have:
            continue
        no += 1
        p = {"no": no, "key": key, "kind": kind, "x": x, "tag": f"{kind}・{name}", "head": text.split("\n")[0],
             "photo_q": q, "alt": q}
        if ans:
            p["th"] = text
            p["answer"] = ans
        photo = f"sns/img/{name}.jpg"
        if os.path.exists(os.path.join(os.path.dirname(HERE), photo)):
            p["photo"] = photo
        new.append(p)
    for b in bad:
        print("長すぎるか使わない言葉:", b)
    print("足す", len(new))
    if bad:
        return 1
    if dry:
        return 0
    posts.extend(new)
    json.dump(data, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(pj, "a", encoding="utf-8").write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
