# [B] いったんサイトから外している分野（Nori 2026-11-16「ペットと泊まれるホテルは1回落とす。サイトにも出ないようにする。あとカフェも」）。
# ここに入れた分野は、ページを作らず（前のページは消して 404 にし、検索から外す）、メニュー・トップの入口・サイトマップに出さず、
# ほかのページに残ったリンクは tidy.py が文字だけにする。戻すときはここから外して gen_areas.py を実行する。
import re

PAUSED = ("inu-yado", "pet-yado", "inu-cafe")
_RX = "|".join(re.escape(p) for p in PAUSED)


def is_paused(url):
    u = re.sub(r"^https?://[^/]+", "", url or "")
    return any(u.startswith("/" + p + "/") or u == "/" + p for p in PAUSED)


def unlink(h):
    """外した分野へのリンクを消す：リンクだけの li・p は行ごと、文の中のリンクは文字だけにする。"""
    h = re.sub(r'<li[^>]*>\s*<a [^>]*href="(?:https?://[^/"]+)?/(?:%s)/[^"]*"[^>]*>(?:(?!</a>).)*</a>\s*</li>' % _RX, "", h, flags=re.S)
    h = re.sub(r'<a [^>]*href="(?:https?://[^/"]+)?/(?:%s)/[^"]*"[^>]*>((?:(?!</a>).)*)</a>' % _RX,
               lambda m: re.sub(r"<[^>]+>", "", m.group(1)), h, flags=re.S)
    return h
