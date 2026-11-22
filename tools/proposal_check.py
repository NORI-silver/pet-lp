#!/usr/bin/env python3
"""[G] Nori さんに出す前の「問（とい）の先回り」点検（Nori 2026-11-22「振込手数料とかのこと考えてるのか？」「言ったことしかできないのか」「考えたらわからない？なぜやらない？」）。

提案・計画・下書きの説明（.md か .html）を Nori さんに出す前に必ず通す。関（せき）がここで止める。
- Nori さんが聞きそうなことに、先に答えているか（`docs/ai/framework/toi-questions.md` の問い。種類ごとに必須がちがう）
- 図があるか（箱と矢印・表・svg・mermaid。文字だけの提案は出さない）
使い方: python3 tools/proposal_check.py 提案.md [--reviewed 鏡と問が読んだ日] [--saku 策が読んだ日 --soroban 算が読んだ日（money・partner は必須）] --type money|partner|page|mail|system   → 足りなければ終了コード1
書き方: 見出し「## 先回りの答え」の下に「- お金の流れ：…」のように1行ずつ。答えが「なし」でも理由を書く（「未定」「TODO」「あとで」は答えではない）。
"""
import re, sys

COMMON = ["目的", "4つのバランス", "リスク", "例外", "Noriさんが決めること"]
BY_TYPE = {
    # お金がからむもの（紹介料・手数料・請求・値引き）
    "money": ["お金の流れ", "手数料", "振込手数料", "いつ", "うちを通す", "法律", "相手の気持ち", "税・インボイス", "返金・取り消し", "当日の追加料金", "事故・トラブル", "うちの取り分"],
    "partner": ["相手の得", "相手の手間", "相手の気持ち", "うちを通す", "前のやりとり", "法律"],
    "page": ["ペルソナ", "最初の1画面", "集客", "提携先への影響"],
    "mail": ["前のやりとり", "相手の気持ち", "先に返事", "送る係", "法律"],
    "system": ["外の事例", "だれが動かす", "止めるしくみ", "ほかのAI"],
}
BAD = re.compile(r"^(?:未定|TODO|あとで|後で|検討中|わからない|不明|[-ー—…]+|（[^）]*）|\([^)]*\))?$|…")  # 型のまま（かっこだけ・…）も答えではない


def check(text, kind):
    out = []
    if not re.search(r"<svg|```mermaid|<img|<table|^\|.+\|\s*$", text, re.M):
        out.append("図がない（箱と矢印・表・svg・mermaid のどれかを先に。Nori 2026-11-22「図解して」）")
    m = re.search(r"#+\s*先回りの答え(.*?)(?=\n#+\s|\Z)", text, re.S)
    if not m:
        return out + ["「## 先回りの答え」がない（Noriさんが聞きそうなことに先に答える。toi-questions.md）"]
    sec = m.group(1)
    for k in COMMON + BY_TYPE.get(kind, []):
        a = re.search(r"^[-・*]?\s*" + re.escape(k) + r"\s*[：:]\s*(.*)$", sec, re.M)
        if not a:
            out.append(f"「{k}」に答えていない")
        elif BAD.match(a.group(1).strip()) or len(a.group(1).strip()) < 4:
            out.append(f"「{k}」の答えが空・未定（{a.group(1).strip() or '空'}）")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0].startswith("--"):
        print(__doc__); sys.exit(2)
    kind = a[a.index("--type") + 1] if "--type" in a else "system"
    if kind not in BY_TYPE:
        print(f"--type は {sorted(BY_TYPE)} のどれか"); sys.exit(2)
    res = check(open(a[0], encoding="utf-8").read(), kind)
    # 鏡（かがみ）と問（とい）が「Noriさんならどこで突っこむか」を読んだしるし（Nori 2026-11-22「こういうことが起こらないように体制組んでるのじゃないの？」）
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", (a[a.index("--reviewed") + 1] if "--reviewed" in a and a.index("--reviewed") + 1 < len(a) else "")):
        res.append("鏡（かがみ）と問（とい）が「Noriさんならどこで突っこむか」を読み、直す所0にしてから --reviewed YYYY-MM-DD を付ける")
    # お金・提携の案は 策（さく）→ 算（そろばん）→ 問・鏡 の順に通す（2026-11-22 体制：策は戦略の関門、算はお金・契約・法律）
    if kind in ("money", "partner"):
        for flag, who in (("--saku", "策（さく）が戦略（目標の鎖のどこを動かすか・ほかの案とのくらべ）"), ("--soroban", "算（そろばん）がお金・契約・法律")):
            v = a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else ""
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                res.append(f"{who}を読んでから {flag} YYYY-MM-DD を付ける（順は 策→算→問・鏡→Noriさん）")
    for r in res: print("直す:", r)
    print("OK" if not res else f"{len(res)}か所（関で止めています。答えてから出す）")
    sys.exit(1 if res else 0)
