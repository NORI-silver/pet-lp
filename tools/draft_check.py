#!/usr/bin/env python3
"""[G] メールの下書きを保存する前の点検（AGENTS.md「品質の決まり」C。Nori 2026-11-16）。
使い方: python3 tools/draft_check.py 下書き.txt [--to 会社|施設|提携先|団体|自治体（会社・施設・提携先なら、会社どうしの直接のお金・連絡も止める）] [--about 依頼した人 --replied 返事した日] [--read-latest]
        → 直すところがあれば終了コード1
--about：お客さま・提携先から頼まれた件で、ほかの人（会社・施設など）に連絡するとき。頼んだ人に先に
         「受け取りました、いま確認しています」と返事した日を --replied に入れないと止める（Nori 2026-11-22
         「加茂さんには先に返信すべきじゃない？」「この指摘とかさせるなよ」）。
--send --approved 承認した下書き：送る直前。Nori さんがOKした下書きと1字でもちがえば止める（穴を自分で埋めて送らない。
         Nori 2026-11-22 の事故：「下書きを全部見せて」を送ってよいと読み、穴を自分で埋め、手数料の約束まで書いて送った）。
--read-latest：送る相手から、まだ返事していない新しいメールがないかを読んだしるし。ないと止める（同日）。
見ること: ◯◯ などの穴、旅行業法の言葉、お金・手数料の話、「公式サイトで確かめた」、こちらの都合が先に立つ言い方、ツール名。
保存は pettaxi.yoyaku の Gmail の下書きに（「下書きして」＝Gmail の下書き）。送るのは Nori さんの「送って」のあと。
"""
import re, sys

RULES = [
    (r"[◯○〇]{2,}|ＸＸ|XXX|TODO|\[[^\]]*(?:名前|日付|会社|施設)[^\]]*\]|【(?:名前|日付|会社名|施設名)】", "穴が残っている（宛名・日付・名前を具体的に入れる）"),
    (r"手配|取り次|取次|代理|お客さまに代わって|に代わって", "旅行業法の言葉（AGENTS.md）"),
    (r"手数料|紹介料|掲載料|成約|課金|費用をいただ|料金をいただ|お支払いいただ", "当サイトのお金の話は書かない"),
    (r"公式(?:サイト|ページ)[^。]{0,8}(?:で|を)(?:確かめ|確認し)|公式(?:サイト|ページ)に書いて(?:ある|あった)こと", "「公式サイトで確かめた」と書かない"),
    (r"くらべられ|比較でき|比較サイト", "こちらの都合（くらべる）を前に出さない（相手の立場で）"),
    (r"Google|Gmail|スプレッドシート|Apps Script|GAS\b|Claude|ChatGPT|AI(?:が|で|に)", "ツール名・AIの話を出さない"),
    (r"使える会社", "「条件に合う会社」と書く"),
    # 2026-11-18 GA：「（https://pet.shiokonbu.com/hinan/）を個人で…」の「）を…」までリンクになり、存在しないページに飛んでいた
    (r"https?://[\x21-\x7e]+(?=[^\s\x21-\x7e])", "URLの直後に空白か改行を入れる（日本語や「）」がつながるとリンクが壊れる。URLは1行に1つだけ書く）"),
]


def check(text):
    out = []
    for pat, why in RULES:
        for m in re.finditer(pat, text):
            line = text.count("\n", 0, m.start()) + 1
            out.append(f"{line}行目「{m.group()}」: {why}")
    if len(text) > 1200: out.append(f"{len(text)}字。長い（相手が読むのは最初の数行。短くする）")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(k):
        return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None
    t = open(a[0], encoding="utf-8").read() if a and a[0] != "-" else sys.stdin.read()
    res = check(t)
    if opt("--about") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", opt("--replied") or ""):
        res.append(f"「{opt('--about')}」さんの件でほかの人に連絡する前に、{opt('--about')}さんへ先に「受け取りました、いま確認しています」と返事する（返事した日を --replied YYYY-MM-DD で）")
    # 会社・施設どうしで直接やりとりさせない（Nori 2026-11-22「事業者同士にやらせたら…うちの介在価値なくなるやろ」）
    if (opt("--to") or "") in ("会社", "施設", "提携先"):
        for m in re.finditer(r"直接(?:ご連絡|連絡|やり取り|やりとり|ご請求|請求|精算|お支払い|お振込|振込|お受け取り)|(?:連絡先|メールアドレス|電話番号|口座)(?:を|も)?(?:お伝え|お知らせ|共有|お渡し)|事業者(?:様)?同士|会社(?:様)?同士|ご紹介先(?:様)?(?:へ|に|と)", t):
            res.append(f"「{m.group()}」: 会社どうしで直接お金・連絡のやりとりをさせない（請求・受け取り・連絡は当サイトを通す）")
    if "--send" in a:
        ap = opt("--approved")
        if not ap:
            res.append("送るときは --approved にNoriさんがOKした下書きのファイルを入れる（OKの文のまま送る）")
        elif open(ap, encoding="utf-8").read().strip() != t.strip():
            res.append("NoriさんがOKした下書きと文がちがう（穴を埋める・直すなら、もう一度OKをもらう）")
    if "--read-latest" not in a:
        res.append("送る相手から、まだ返事していない新しいメールがないかを読んでから送る（読んだら --read-latest を付ける）")
    for r in res: print("直す:", r)
    print("OK" if not res else f"{len(res)}か所")
    sys.exit(1 if res else 0)
