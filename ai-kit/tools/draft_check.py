#!/usr/bin/env python3
"""[G] メールの下書きを保存する前の点検（AI-KIT。どの事業でも同じ。事業ごとの言葉・署名はリポジトリの ai-kit.json）。
使い方: python3 tools/draft_check.py 下書き.txt [--to 会社|施設|提携先|団体|自治体（会社・施設・提携先なら、会社どうしの直接のお金・連絡も止める）] [--about 依頼した人 --replied 返事した日] [--read-latest]
        → 直すところがあれば終了コード1
--about：お客さま・提携先から頼まれた件で、ほかの人（会社・施設など）に連絡するとき。頼んだ人に先に
         「受け取りました、いま確認しています」と返事した日を --replied に入れないと止める（Nori 2026-11-22
         「加茂さんには先に返信すべきじゃない？」「この指摘とかさせるなよ」）。
--send --approved 承認した下書き：送る直前。Nori さんがOKした下書きと1字でもちがえば止める（穴を自分で埋めて送らない。
         Nori 2026-11-22 の事故：「下書きを全部見せて」を送ってよいと読み、穴を自分で埋め、手数料の約束まで書いて送った）。
--read-latest：送る相手から、まだ返事していない新しいメールがないかを読んだしるし。ないと止める（同日）。
見ること: ◯◯ などの穴、旅行業法の言葉、お金・手数料の話、「公式サイトで確かめた」、こちらの都合が先に立つ言い方、ツール名。
--for-nori：Nori さんに見せる下書き。全文（宛名から署名まで）でないと止め、問（とい）・鏡（かがみ）が読んだ日 --reviewed がないと止める
         （Nori 2026-11-22「部分的にドラフトだされてもはんだんできないって何回もいってるよね？」）。全文のチェックはいつでもする。
--confirmed：相手が言っていない前提・約束（「難しければ電車で」など）は、相手に確かめたときだけ付ける（Nori 2026-11-22「これとかなんで勝手につけるの？保証できる？」）。
--kind referral：会社に送客・紹介を頼むメール。だれが・なぜ・経路・日付・頼むこと・お支払い・連絡のしかたが全部あるか、
         料金はまず「目安（概算）」を聞いているかを見る（具体的な場所のあとの確定料金のときは --exact。Nori 2026-11-22「まずは、おおよそで…確定料金をだすとか」）。
--kind invite --terms 決めた条件のファイル：提携のお誘い・提携の内容の説明。Nori さんが決めたお金の条件の文（ファイルの1行と同じ行）だけは
         お金の話でも通す。条件は最初に書き、あとから出さない。ほかのお金の話は止める。条件のファイルは公開のリポジトリに置かない。
保存は、その事業の送る係のメールの下書きに（「下書きして」＝メールの下書き。ai-kit.json の sender）。送るのは Nori さんの「送って」のあと。
"""
import json, os, re, sys

def _cfg():
    for d in (os.getcwd(), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
        p = os.path.join(d, "ai-kit.json")
        if os.path.exists(p): return json.load(open(p, encoding="utf-8"))
    return {}
CFG = _cfg()

MONEY = CFG.get("money_words", r"手数料|紹介料|掲載料|成約|課金|費用をいただ|料金をいただ|お支払いいただ")
RULES = [
    (r"[◯○〇]{2,}|ＸＸ|XXX|TODO|\[[^\]]*(?:名前|日付|会社|施設)[^\]]*\]|【(?:名前|日付|会社名|施設名)】", "穴が残っている（宛名・日付・名前を具体的に入れる）"),
    (MONEY, "当サイトのお金の話は書かない"),
    (r"公式(?:サイト|ページ)[^。]{0,8}(?:で|を)(?:確かめ|確認し)|公式(?:サイト|ページ)に書いて(?:ある|あった)こと", "「公式サイトで確かめた」と書かない"),
    # 2026-11-18 GA：「（https://…/）を…」の「）を…」までリンクになり、存在しないページに飛んでいた
    (r"https?://[\x21-\x7e]+(?=[^\s\x21-\x7e])", "URLの直後に空白か改行を入れる（日本語や「）」がつながるとリンクが壊れる。URLは1行に1つだけ書く）"),
] + [tuple(r) for r in CFG.get("ban", [])]  # 事業ごとの使わない言葉（ai-kit.json の ban：[[正規表現, 理由], ...]）


# 相手が言っていない前提・約束（Nori 2026-11-22「難しければ、飼い主さまは電車で浜松へ向かい これとかなんで勝手につけるの？保証できる？」）
HYPO = r"難しければ|難しい(?:場合|とき)は|(?:場合|とき)は[^。\n]{0,24}(?:向かい|向かって|行って|お持ち|ご用意|お越し|お連れ)|おそらく|はずです|かもしれません|と思われます|になると思います"
# 全文：宛名と署名（Nori 2026-11-22「部分的にドラフトだされてもはんだんできない」）
HEAD = r"様|御中|ご担当|各位"
SIGN = CFG.get("sign", r"様$^")  # 署名に入る言葉（ai-kit.json の sign）
# 送客・紹介の依頼に要るもの（全部あって、それ以上は書かない）
REFERRAL = [
    (r"お客さま|お客様|飼い主", "だれが頼んでいるか（お客さま・飼い主さま）"),
    (r"ため|ので|ご希望|ご依頼", "なぜ（何のための移動か）"),
    (r"→|から[^。\n]{0,30}まで|経由", "経路（どこから・どこへ、順に）"),
    (r"\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2}|日程|日にち", "日付"),
    (r"お願い|いただけますか|いただけますでしょうか|ご回答", "頼むこと"),
    (r"お支払い|料金|お代", "お支払いのしかた"),
    (r"ご連絡|ご返信|返信|お知らせください", "連絡のしかた（当サイトを通す）"),
]


def check(text):
    out = []
    ref = "--kind" in sys.argv and "referral" in sys.argv
    # 提携のお誘い・提携の内容の説明では、Noriさんが決めたお金の条件の文だけはそのまま通す（Nori 2026-11-22「お金の条件は最初に伝える・あとからは絶対ない」）。
    # 条件の文は率をふくむので公開のリポジトリに置かず、--terms に pet-db などのファイルを渡す。お客さま・自治体・被リンクのお願いでは今までどおり止める。
    ok_lines = set()
    if "--kind" in sys.argv and "invite" in sys.argv and "--terms" in sys.argv:
        i = sys.argv.index("--terms")
        if i + 1 < len(sys.argv):
            ok_lines = {l.strip() for l in open(sys.argv[i + 1], encoding="utf-8").read().splitlines() if l.strip()}
    for pat, why in RULES:
        if ref and why.startswith("当サイトのお金"):
            pat = pat.replace("|お支払いいただ", "").replace("お支払いいただ|", "")  # 送客の依頼では、飼い主さまから会社へのお支払いのしかたは書く（要るもの）
        for m in re.finditer(pat, text):
            if why.startswith("当サイトのお金") and ok_lines:
                ln = text[text.rfind("\n", 0, m.start()) + 1: (text.find("\n", m.start()) + 1 or len(text) + 1) - 1].strip()
                if ln in ok_lines: continue
            line = text.count("\n", 0, m.start()) + 1
            out.append(f"{line}行目「{m.group()}」: {why}")
    for m in re.finditer(HYPO, text):
        if "--confirmed" not in sys.argv:
            out.append(f"{text.count(chr(10), 0, m.start()) + 1}行目「{m.group()}」: 相手が言っていない前提・約束を足さない（相手に確かめたら --confirmed）")
    body = [l for l in text.strip().splitlines() if l.strip()]
    if not body or not re.search(HEAD, "\n".join(body[:3])) or not re.search(SIGN, "\n".join(body[-4:])):
        out.append("全文でない（宛名から署名まで全部を見せる・保存する。変えたところだけは出さない）")
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
    if opt("--kind") == "referral":
        for pat, what in REFERRAL:
            if not re.search(pat, t): res.append(f"送客の依頼に「{what}」がない（相手が決めるのに要るものは全部書く。それ以上は書かない）")
        if "--exact" not in a and not re.search(r"目安|概算|おおよそ", t):
            res.append("料金はまず目安（概算）を聞く。場所と日時が決まってから確定料金（そのときは --exact）")
    if "--for-nori" in a and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", opt("--reviewed") or ""):
        res.append("Noriさんに見せる前に問（とい）・鏡（かがみ）が読む（読んだ日を --reviewed YYYY-MM-DD）")
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
