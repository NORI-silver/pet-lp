#!/usr/bin/env python3
"""[G] Nori さんへの返信の点検（いちばん上の決まり。Nori 2026-11-22「図でまとめて、説明は要所で何回いえばわかるの？100回？」）。

どのスレッドも、Nori さんへのまとめ・計画・お金の説明を送る前に通す。関（せき）が止める。
- 文字だけの返信は5行まで（空行・リンクだけの行は数えない）。
- まとめ・計画・お金・流れ・くらべ・手順の話は、図（スマホ1画面のsvg・画像・アーティファクト）を付け、文字は要所に1〜2行。
  図は `node tools/report_check.cjs <図.html>` を通したもの。
使い方: python3 tools/reply_check.py 返信.txt [--diagram 図のファイルかURL]   → 直すところがあれば終了コード1
"""
import re, sys

TOPIC = re.compile(r"まとめ|計画|案|プラン|ロードマップ|流れ|しくみ|仕組み|体制|お金|手数料|振込|請求|入金|円|売上|くらべ|比較|手順|ステップ|選択肢")
MAX_LINES = 5


def check(text, diagram):
    lines = [l for l in text.splitlines() if l.strip() and not re.fullmatch(r"\s*(?:https?://\S+|\[[^\]]*\]\([^)]*\))\s*", l)]
    out = []
    if TOPIC.search(text) and not diagram:
        out.append("まとめ・計画・お金・流れの話は図を付ける（--diagram に report_check を通した図）。文字は要所に1〜2行")
    lim = 3 if diagram else MAX_LINES
    if len(lines) > lim:
        out.append(f"文字が{len(lines)}行。{'図があるときは' if diagram else ''}{lim}行までにして、残りは図に入れる")
    if any(len(l) > 90 for l in lines):
        out.append("1行が長い（90字まで。スマホで2行に収める）")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(2)
    d = a[a.index("--diagram") + 1] if "--diagram" in a and a.index("--diagram") + 1 < len(a) else ""
    t = open(a[0], encoding="utf-8").read() if a[0] != "-" else sys.stdin.read()
    res = check(t, d)
    for r in res: print("直す:", r)
    print("OK" if not res else f"{len(res)}か所（関で止めています）")
    sys.exit(1 if res else 0)
