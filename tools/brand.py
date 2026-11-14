"""タクシー以外の分野のページのサイト名（Nori 2026-11-09 決定カード「ペットのくらし窓口」）。
ペットタクシーの話はペットタクシーのページだけにする（「ランはラン、ドッグトレーナーはドッグトレーナーの話」）。
gen_areas.py の最後に動き、下の分野のフォルダのページの「ペットタクシー予約窓口」（タイトル・上の名前・パンくず・下の名前・構造化データ）を
「ペットのくらし窓口」（X・Instagram と同じ名前）に置きかえる。「ペットタクシーで行く」の案内の枠（taxi_cta.py）はそのまま残す。"""
import os

INFO_NAME = "ペットのくらし窓口"
TAXI_NAME = "ペットタクシー予約窓口"
INFO_DIRS = ["dogrun", "dog-trainer", "pet-sitter", "sougi", "hospital", "jichitai", "rojin-home",
             "trimming", "pet-hotel", "inu-yado", "inu-cafe", "emergency"]

import re

# 上の名前の横のメニューも、その分野の人が次に見たいところにする（2026-11-14 Nori「ユーザーのインテントをちゃんと理解してよ」）。
# タクシーの「使い方・料金をくらべる・問い合わせる」はタクシーのページだけ。
INFO_NAV = ('<nav><a href="/hospital/">動物病院</a><a href="/sougi/">亡くなったら</a><a href="/jichitai/">迷子・登録</a>'
            '<a href="/pet-hotel/">預け先</a><a href="/dogrun/">ドッグラン</a></nav>\n    <a class="mini" href="/emergency/">緊急のとき</a>')
_TAXI_NAV = re.compile(r'<nav><a href="/#how">使い方</a>.*?</nav>\s*<a class="mini" href="/#form">問い合わせる<span class="lg">（無料）</span></a>', re.S)

def to_info(s):
    s = s.replace(TAXI_NAME, INFO_NAME)
    s = _TAXI_NAV.sub(INFO_NAV, s, count=1)
    s = re.sub(r'<aside class="partner-band">.*?</aside>\n?', "", s, count=1, flags=re.S)  # ペットタクシー会社さま向けの帯
    return s

def build(root, guide_slugs=()):
    """タクシー以外の分野のフォルダのページと、タクシー以外の記事（guide_slugs）を「ペットのくらし窓口」の見た目にする"""
    n = 0
    paths = [os.path.join(dp, f) for d in INFO_DIRS for dp, _, fs in os.walk(os.path.join(root, d)) for f in fs if f.endswith(".html")]
    paths += [os.path.join(root, "guide", g, "index.html") for g in guide_slugs]
    for p in paths:
        s = open(p, encoding="utf-8").read()
        t = to_info(s)
        if t != s:
            open(p, "w", encoding="utf-8").write(t); n += 1
    return n
