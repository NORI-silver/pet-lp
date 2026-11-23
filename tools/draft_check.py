#!/usr/bin/env python3
"""[G] メールの下書きを保存する前の点検（AGENTS.md「品質の決まり」C。Nori 2026-11-16）。
使い方: python3 tools/draft_check.py 下書き.txt [--to 会社|施設|団体|自治体]   → 直すところがあれば終了コード1
見ること: ◯◯ などの穴、費用の一文（FEE_LINE だけ）、旅行業法の言葉、お金・手数料の話、「公式サイトで確かめた」、こちらの都合が先に立つ言い方、ツール名。
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
]


# ほかの会社の名前を出さない（Nori 2026-11-23「ペッタくの名前は出さない。これも前に指摘したよね」）。
# 宛名（「様・さま」の行まで）に出てくる会社は相手なのでよい。ほかの提携先・事業者の名前があれば止める。
ALIASES = ["ペッタク", "BOOM", "加茂"]  # 表示名にない呼び名（ペッタク広島＝BOOM 加茂さま）


def other_names(text):
    import json, os
    names = set(ALIASES)
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "display_companies.json")
    try:
        cs = json.load(open(p, encoding="utf-8"))["companies"]
        for c in (cs if isinstance(cs, list) else cs.values()):
            n = re.sub(r"[（(【].*?[）)】]", "", c.get("name") or "").strip()
            for part in re.split(r"[\s　]+", n):
                if len(part) >= 3 and part not in ("ペットタクシー", "ペット", "タクシー", "COCOタク", "ココタク", "CoCoタク"):
                    names.add(part)
            if len(n) >= 3: names.add(n)
    except Exception:
        pass
    lines = [l for l in text.splitlines() if l.strip()]
    k = next((i for i, l in enumerate(lines[:4]) if re.search(r"様|さま|御中|ご担当", l)), 0)
    head = "\n".join(lines[:k + 1])
    out = []
    for n in sorted(names, key=len, reverse=True):
        if n in head: continue
        i = text.find(n)
        if i >= 0:
            out.append(f"{text.count(chr(10), 0, i) + 1}行目「{n}」: ほかの会社の名前を相手に出さない（「提携先の会社さま」と書く）")
    return out


# 費用の一文はこれだけ（Nori 2026-11-23「少なくとも30日前には」「ご連絡して、継続利用の有無についてはその時に判断」）。
# この文はそのまま通し、ほかの「費用」の書き方（30日前がない・ご相談してから・有料にする など）は止める。
FEE_LINE = "今後費用をいただく形にする場合は、少なくとも30日前にご連絡いたします。続けてご利用いただくかどうかは、その時点でご判断いただけます。"
FEE_OTHER = (r"費用をいただ|有料に(?:する|なる|な)|費用が(?:かか|発生|出)|費用について[^。]*(?:ご相談|お知らせ)", "費用の文は決まった一文だけ：「" + FEE_LINE + "」")


def check(text):
    out = other_names(text)
    text = text.replace(FEE_LINE, "　" * len(FEE_LINE))  # 決まった一文は通す（行の番号は変えない）
    for pat, why in RULES + [FEE_OTHER]:
        for m in re.finditer(pat, text):
            line = text.count("\n", 0, m.start()) + 1
            out.append(f"{line}行目「{m.group()}」: {why}")
    if len(text) > 1200: out.append(f"{len(text)}字。長い（相手が読むのは最初の数行。短くする）")
    return out


if __name__ == "__main__":
    t = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 and sys.argv[1] != "-" else sys.stdin.read()
    res = check(t)
    for r in res: print("直す:", r)
    print("OK" if not res else f"{len(res)}か所")
    sys.exit(1 if res else 0)
