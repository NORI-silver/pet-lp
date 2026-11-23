# [C] 施設名とリンク先の題の突き合わせ（2026-11-23。「わんず」のリンク先が別の方のサイトだった件から）。
# 使い方：tools/crawl/queue_namecheck.json（全分野の url・name、alive）を push → crawl-out の snap_namecheck.json を
#   python3 tools/name_check.py <snap_namecheck.json> で読み、名前の言葉がリンク先の題にもアドレスにも1つも出てこない行を出す。
# 出た行は人（AI）がリンク先を見て決める：別の施設・乗っ取られたアドレス → 外すか url を消す（tools/delisted.json に記録）。
import json, re, sys, unicodedata
GENERIC = "ペットホテル 動物病院 ペットクリニック ペットシッター トリミング ドッグ サロン しつけ 教室 老犬ホーム ペット霊園 ペット火葬 ドッグラン 株式会社 有限会社 dog hotel pet clinic animal hospital"
def norm(s): return unicodedata.normalize("NFKC", s).lower()
def grams(s):
    s = norm(s); out = set(re.findall(r"[a-z0-9]{3,}", s))
    for j in re.split(r"[\sa-z0-9・\-ー_（）()「」【】|｜/,、。.!！?？&＆]+", s):
        out |= {j[i:i+2] for i in range(len(j) - 1)}
    return out
GEN = grams(GENERIC)
def main(p):
    bad = []
    for x in json.load(open(p, encoding="utf-8")):
        if x.get("error"): continue
        g = grams(x["name"]) - GEN
        host = re.sub(r"^https?://(www\.)?", "", x.get("final") or x["url"]).split("/")[0]
        hay = re.sub(r"\s+", "", norm(x.get("title", ""))) + " " + host
        if g and not any(w in hay for w in g):
            bad.append(x)
    for x in bad: print(x["cat"], x.get("id", ""), x["name"], "|", x.get("title", "")[:60], "|", x.get("final") or x["url"])
    print(len(bad), "件（名前とリンク先の題が合わない候補）", file=sys.stderr)
if __name__ == "__main__": main(sys.argv[1])
