"""タクシー以外の分野のページのサイト名（Nori 2026-11-09 決定カード「ペットのくらし窓口」）。
ペットタクシーの話はペットタクシーのページだけにする（「ランはラン、ドッグトレーナーはドッグトレーナーの話」）。
gen_areas.py の最後に動き、下の分野のフォルダのページの「ペットタクシー予約窓口」（タイトル・上の名前・パンくず・下の名前・構造化データ）を
「ペットのくらし窓口」（X・Instagram と同じ名前）に置きかえる。「ペットタクシーで行く」の案内の枠（taxi_cta.py）はそのまま残す。"""
import os

INFO_NAME = "ペットのくらし窓口"
TAXI_NAME = "ペットタクシー予約窓口"
INFO_DIRS = ["dogrun", "dog-trainer", "pet-sitter", "sougi", "hospital", "jichitai", "rojin-home",
             "trimming", "pet-hotel", "inu-yado", "inu-cafe", "emergency"]

def build(root):
    n = 0
    for d in INFO_DIRS:
        for dp, _, fs in os.walk(os.path.join(root, d)):
            for f in fs:
                if not f.endswith(".html"): continue
                p = os.path.join(dp, f)
                s = open(p, encoding="utf-8").read()
                if TAXI_NAME in s:
                    open(p, "w", encoding="utf-8").write(s.replace(TAXI_NAME, INFO_NAME)); n += 1
    return n
