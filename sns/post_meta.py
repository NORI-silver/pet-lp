#!/usr/bin/env python3
"""Instagram と Threads に、毎日1本ずつ出す（ペットのくらし窓口：Instagram pet.kurashi・Threads）。

[B] SNS。2026-11-13 Nori「無料枠でやって」→ Meta の公式のしくみ（無料）で自動にする。
- sns/posts.json の投稿を、まだ出していない順に1本出す（Xとは別に数える）。記録は sns/state.json の "ig"・"threads"。
- 写真はサイトの写真（https://pet.shiokonbu.com/<photo>）。文字やロゴ入りの画像は使わない（Nori 2026-11-02）。
- リンクは貼らない（Nori 2026-11-02）。文の決まりは schedule_x.py の BAN で確かめる。
- キーは GitHub の Secret（META_IG_TOKEN・META_THREADS_TOKEN）。ないときは何もしないで終わる。
- Instagram と Threads は予約ができないので、毎日20時に GitHub Actions がその場で出す（.github/workflows/sns-meta.yml）。

使い方: python3 sns/post_meta.py [--dry] [--only ig|threads] [--check]
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from schedule_x import BAN, pick  # noqa: E402

SITE = "https://pet.shiokonbu.com/"
JST = dt.timezone(dt.timedelta(hours=9))
IG = "https://graph.instagram.com/v21.0"
TH = "https://graph.threads.net/v1.0"
HANDLES = {"ig": {"pet.kurashi"}, "threads": {"pet.kurashi"}}


def call(method, url, params):
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        url, data = url + "?" + data.decode(), None
    r = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            return json.loads(f.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:400]
        sys.exit(f"{method} {url.split('?')[0]}: {e.code} {body}")


def caption_ig(p, common):
    body = "\n".join(l for l in p["x"].split("\n") if not l.startswith("#"))
    tags = list(dict.fromkeys(common + p.get("ig_extra", []) + [w for w in p["x"].split() if w.startswith("#")]))
    parts = [body]
    if p.get("ig_add"):
        parts.append(p["ig_add"])
    parts.append(" ".join(tags[:10]))
    return "\n\n".join(parts)


def check(text):
    bad = [w for w in BAN if w in text]
    if bad:
        sys.exit(f"使わない言葉があります: {bad}")


def post_ig(token, p, common):
    me = call("GET", f"{IG}/me", {"fields": "username", "access_token": token})
    if me.get("username") not in HANDLES["ig"]:
        sys.exit(f"Instagram のアカウントが違います: {me.get('username')}")
    cap = caption_ig(p, common)
    check(cap)
    c = call("POST", f"{IG}/me/media", {"image_url": SITE + p["photo"], "caption": cap,
                                         "alt_text": p.get("alt") or p["tag"], "access_token": token})
    for _ in range(30):
        st = call("GET", f"{IG}/{c['id']}", {"fields": "status_code", "access_token": token}).get("status_code")
        if st == "FINISHED":
            break
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram の画像の取り込みに失敗: {st}")
        time.sleep(5)
    return call("POST", f"{IG}/me/media_publish", {"creation_id": c["id"], "access_token": token}).get("id")


def text_threads(p):
    """Threads は文だけで出す。ハッシュタグは最初の1つだけ（Threads はトピックが1つ）。"""
    lines = p["x"].split("\n")
    tags = [w for l in lines if l.startswith("#") for w in l.split() if w.startswith("#")]
    body = "\n".join(l for l in lines if not l.startswith("#"))
    return body + ("\n" + tags[0] if tags else "")


def post_threads(token, p):
    me = call("GET", f"{TH}/me", {"fields": "username", "access_token": token})
    if me.get("username") not in HANDLES["threads"]:
        sys.exit(f"Threads のアカウントが違います: {me.get('username')}")
    text = text_threads(p)
    check(text)
    # 豆知識は文だけ（Threads は文が中心）。ほかは写真つき
    if p.get("kind") == "tip":
        args = {"media_type": "TEXT", "text": text}
    else:
        args = {"media_type": "IMAGE", "image_url": SITE + p["photo"], "text": text, "alt_text": p.get("alt") or p["tag"]}
    c = call("POST", f"{TH}/me/threads", {**args, "access_token": token})
    for _ in range(30):
        st = call("GET", f"{TH}/{c['id']}", {"fields": "status", "access_token": token}).get("status")
        if st == "FINISHED":
            break
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"Threads の画像の取り込みに失敗: {st}")
        time.sleep(5)
    return call("POST", f"{TH}/me/threads_publish", {"creation_id": c["id"], "access_token": token}).get("id")


def main():
    dry = "--dry" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    data = json.load(open(os.path.join(HERE, "posts.json"), encoding="utf-8"))
    sp = os.path.join(HERE, "state.json")
    state = json.load(open(sp, encoding="utf-8"))
    now = dt.datetime.now(JST).isoformat(timespec="minutes")
    tokens = {"ig": os.environ.get("META_IG_TOKEN"), "threads": os.environ.get("META_THREADS_TOKEN")}
    for kind in ("ig", "threads"):
        if only and kind != only:
            continue
        done = state.setdefault(kind, {})
        nxt = next(iter(pick(data["posts"], list(done))), None)
        if not nxt:
            print(kind, "出せる投稿が残っていません")
            continue
        if dry:
            print(f"== {kind} {nxt['no']} {nxt['tag']} {SITE + nxt['photo']}")
            print(caption_ig(nxt, data["ig_tags_common"]) if kind == "ig" else text_threads(nxt))
            continue
        if not tokens[kind]:
            print(kind, "のキーがまだありません（何もしない）")
            continue
        if "--check" in sys.argv:  # キーが使えるか、アカウントが合っているかだけ見る（出さない）
            base = IG if kind == "ig" else TH
            me = call("GET", f"{base}/me", {"fields": "username", "access_token": tokens[kind]})
            ok = me.get("username") in HANDLES[kind]
            print(kind, "キーは使えます" if ok else "アカウントが違います", me.get("username"))
            continue
        pid = post_ig(tokens[kind], nxt, data["ig_tags_common"]) if kind == "ig" else post_threads(tokens[kind], nxt)
        done[str(nxt["no"])] = now
        print(kind, "出した", nxt["no"], nxt["tag"], pid)
        json.dump(state, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
