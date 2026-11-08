# [B][F] 情報ページ（ペット火葬・霊園／ペットシッター／ドッグトレーナー）のカードに付ける印と、しぼりこみのタグ。
# Nori 2026-11-08「ペットタクシーと同じように、SEOもそうだけどマネタイズを意識して」。動きは /facility.js（手書き）。
# タグは公式サイトに書いてあること（データの services・kinds・animals、グループの説明）だけから作る。書いていない＝タグなし（「しない」ではない）。
# 提携した事業者はデータに "partner": true を入れる → カードにオレンジの丸にチェックのアイコンだけが付く（文字なし。ペットタクシーと同じ）。
# 問い合わせを当サイトから事業者へ送るしくみはまだない（許可のない事業者に転送しない）。
import re

SCRIPT = '<script src="/facility.js" defer></script>'

SOUGI_CHIPS = ["個別火葬", "立ち会い", "お迎え・訪問火葬", "霊園・納骨", "料金を公開"]
TRAINER_CHIPS = ["出張・訪問", "教室・グループ", "パピー", "幼稚園・保育園", "預かり訓練", "オンライン"]
SITTER_CHIPS = ["猫", "小動物", "鳥", "散歩"]


def sougi_tags(f):
    s = set(f.get("kinds", [])) | set(f.get("services", []))
    t = []
    if "個別火葬" in s: t.append("個別火葬")
    if "立ち会い火葬" in s: t.append("立ち会い")
    if "お迎え" in s or "訪問火葬" in s: t.append("お迎え・訪問火葬")
    if s & {"霊園", "納骨", "納骨堂"}: t.append("霊園・納骨")
    if f.get("price"): t.append("料金を公開")
    return t


_TR = [
    ("出張・訪問", r"出張|訪問|お家|自宅|家庭へ|ご自宅"),
    ("教室・グループ", r"教室|グループ|クラス|スクール|学校"),
    ("パピー", r"パピー|子犬|仔犬"),
    ("幼稚園・保育園", r"幼稚園|保育園|ようちえん|ほいくえん|デイケア"),
    ("預かり訓練", r"預かり訓練|預かりトレーニング|お預かり訓練|寄宿|預託訓練|預かりしつけ|預かり|お預かり"),
    ("オンライン", r"オンライン"),
]


def trainer_tags(t):
    s = t.get("services", "") + " " + t.get("spec", "")
    out = []
    for lab, rx in _TR:
        if lab == "預かり訓練":
            # 「一時預かり」「お預かり（ホテル）」だけはトレーニングではないので、訓練・トレーニング・しつけと一緒に書いてあるときだけ
            if re.search(r"預かり(訓練|トレーニング)は(しない|していない|なし|ありません)", s): continue
            if not re.search(r"預かり(訓練|トレーニング|しつけ)|寄宿|預託|(訓練|トレーニング|しつけ)[^、。]{0,6}預かり", s): continue
        elif not re.search(rx, s):
            continue
        out.append(lab)
    return out


def sitter_tags(s, chains):
    ch = chains.get(s.get("chain"), {})
    txt = s.get("animals", "") + " " + (ch.get("note", "") if s.get("chain") != "indie" else "")
    out = []
    if "猫" in txt: out.append("猫")
    if re.search(r"小動物|うさぎ|ハムスター|フェレット", txt): out.append("小動物")
    if re.search(r"鳥|インコ", txt): out.append("鳥")
    if "散歩" in txt: out.append("散歩")
    return out


def attrs(e, cat, item, tags, name, to="", to_label=""):
    a = f' data-cat="{e(cat)}" data-fid="{e(item.get("id", ""))}" data-name="{e(name)}" data-tags="{e("|".join(tags))}"'
    if item.get("partner"): a += ' data-partner="1"'
    if to: a += f' data-to="{e(to[:80])}" data-to-label="{e(to_label)}"'
    return a


def chips(e, labels, pf=""):
    return (f'<div class="fac-filter" data-fac-chips="{e("|".join(labels))}"' + (f' data-pref="{e(pf)}"' if pf else '') +
            '><p class="emg-tips-note" style="margin:8px 0 0">条件でしぼりこむ（公式サイトに書いてあることだけで判定します）</p></div>')


def biz(e, word):
    return ('<div class="emg-tips"><h4>' + e(word) + 'の事業者のみなさまへ</h4><p style="font-size:.88rem;margin:4px 0">'
            'この一覧への掲載は無料で、順位や掲載を売ることはしません。公式サイトへのリンクには当サイトから来たことが分かる印（utm_source=pet.shiokonbu.com）を付けています。'
            '掲載の内容の直しや、当サイトから直接問い合わせを受け付ける形（準備中）にご関心がありましたら、<a href="/contact/">お問い合わせ</a>からお知らせください。</p></div>')
