# [B] いったんサイトから外している分野（Nori 2026-11-16「ペットと泊まれるホテルは1回落とす。サイトにも出ないようにする。あとカフェも」）。
# ここに入れた分野は、ページを作らず（前のページは消して 404 にし、検索から外す）、メニュー・トップの入口・サイトマップに出さず、
# ほかのページに残ったリンクは tidy.py が文字だけにする。戻すときはここから外して gen_areas.py を実行する。
import os, re, shutil

TRAVEL_PAUSED = ("inu-yado", "pet-yado", "inu-cafe")
# [E] Nori 2026-11-27：犬の登録と里親・譲渡を非公開。ソースは残し、配信しない。
PAUSED = (*TRAVEL_PAUSED, "jichitai/touroku", "joto")
_RX = "|".join(re.escape(p) for p in PAUSED)


def is_paused(url):
    u = re.sub(r"^https?://[^/]+", "", url or "").split("?", 1)[0].split("#", 1)[0]
    return any(u.startswith("/" + p + "/") or u == "/" + p for p in PAUSED)

def remove_outputs(root):
    """Depublish the generated site outputs only; retain their generation sources."""
    for d in ("jichitai/touroku", "joto"):
        if is_paused("/" + d):
            path = os.path.join(root, d)
            if os.path.isdir(path):
                shutil.rmtree(path)
    if is_paused("/joto/"):
        path = os.path.join(root, "find-data", "joto")
        if os.path.isdir(path):
            shutil.rmtree(path)

_HREF = r'/(?:%s)(?:[/?#][^"]*)?' % _RX
_ANCHOR = r'<a [^>]*href="(?:https?://[^/"]+)?%s"[^>]*>((?:(?!</a>).)*)</a>' % _HREF

def unlink(h):
    """Remove retired-category navigation, preserving words in inline prose."""
    h = re.sub(r'<nav[^>]*>.*?</nav>', lambda m: re.sub(_ANCHOR, "", m[0], flags=re.S), h, flags=re.S)
    h = re.sub(r'<li[^>]*>\s*' + _ANCHOR + r'\s*</li>', "", h, flags=re.S)
    return re.sub(_ANCHOR, lambda m: re.sub(r"<[^>]+>", "", m[1]), h, flags=re.S)
