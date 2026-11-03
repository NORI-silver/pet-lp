#!/usr/bin/env python3
"""Xの予約投稿（ペットのくらし窓口。旧 @pettaxi_yoyaku）。

Nori 2026-11-02「僕の作業はゼロにしたい」「無料でもう1つ（週2回）」。
sns/posts.json の投稿を、まだ予約していない順に、火曜と金曜の20時（日本時間）へ予約する。
予約したものは sns/state.json に記録し、同じ投稿を二度入れない。
予約先はペットタクシー用の無料 Typefully（APIキーは GitHub の Secret TYPEFULLY_API_KEY）。
ユーザー名が pettaxi_yoyaku のアカウントにだけ入れる（ほかのアカウントには絶対に入れない）。

使い方: TYPEFULLY_API_KEY=... python3 sns/schedule_x.py [件数(既定2)] [--dry]
"""
import json, os, subprocess, sys, time, datetime as dt, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
API = "https://api.typefully.com/v2"
HANDLES = {"pettaxi_yoyaku", "pet_kurashi", "petkurashi_mado"}  # ユーザー名を変えても同じアカウントに入れる
JST = dt.timezone(dt.timedelta(hours=9))
SLOTS = {1: 20, 4: 20}  # 火曜(1)・金曜(4) の20時
# 文の決まり（AGENTS.md）。1つでも入っていたら予約しない。
BAN = ["http", "www.", "手配", "取り次", "取次", "代理", "代わって", "完全予約制", "手配料", "今すぐ", "すぐ来", "24時間",
       "Google", "Gmail", "スプレッドシート", "くらい", "円まで", "予約できます"]


def req(method, path, key, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            return json.loads(f.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"Typefully {method} {path}: {e.code} {e.read().decode()[:500]}")


def social_set(key):
    sets = req("GET", "/social-sets?limit=50", key)["results"]
    sid = next((s["id"] for s in sets if (s.get("username") or "").lower() in HANDLES), None)
    if not sid:
        sys.exit(f"{HANDLES} のアカウントが Typefully に見つかりません: {[s.get('username') for s in sets]}")
    return sid


def next_slots(after, n):
    out, d = [], after.astimezone(JST)
    day = d.replace(hour=0, minute=0, second=0, microsecond=0)
    while len(out) < n:
        if day.weekday() in SLOTS:
            t = day.replace(hour=SLOTS[day.weekday()])
            if t > d:
                out.append(t)
        day += dt.timedelta(days=1)
    return out


def main():
    n = int(next((a for a in sys.argv[1:] if a.isdigit()), 2))
    dry = "--dry" in sys.argv
    if "--status" in sys.argv:  # 予約・投稿のようすを出すだけ（何も変えない）
        key = os.environ.get("TYPEFULLY_API_KEY") or sys.exit("TYPEFULLY_API_KEY がありません")
        sid = social_set(key)
        for d in req("GET", f"/social-sets/{sid}/drafts?limit=10&order_by=-updated_at", key)["results"]:
            print(d.get("status"), d.get("scheduled_date"), d.get("published_at"), d.get("x_published_url"), (d.get("preview") or "")[:30].replace("\n", " "))
        return 0
    hold = "--hold" in sys.argv  # 予約ずみ（まだ出ていない）ものを消して、入れ直さない
    redo = "--redo" in sys.argv or hold  # 予約ずみ（まだ出ていない）ものを消して入れ直す
    posts = json.load(open(os.path.join(HERE, "posts.json"), encoding="utf-8"))["posts"]
    sp = os.path.join(HERE, "state.json")
    state = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {"x": {}}
    key = os.environ.get("TYPEFULLY_API_KEY")
    if redo and not dry:
        if not key:
            sys.exit("TYPEFULLY_API_KEY がありません")
        sid = social_set(key)
        now = dt.datetime.now(JST)
        gone = 0
        for d in req("GET", f"/social-sets/{sid}/drafts?status=scheduled&limit=50", key)["results"]:
            req("DELETE", f"/social-sets/{sid}/drafts/{d['id']}", key)
            gone += 1
        state["x"] = {k: v for k, v in state["x"].items() if dt.datetime.fromisoformat(v) <= now}
        n = max(n, gone)
        print("予約を消した:", gone)
        if hold:
            json.dump(state, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            return 0
    todo = [p for p in posts if str(p["no"]) not in state["x"]][:n]
    if not todo:
        print("予約できる投稿が残っていません。posts.json に新しい投稿を足してください。")
        return 2
    for p in todo:
        bad = [w for w in BAN if w in p["x"]]
        if bad:
            sys.exit(f"投稿{p['no']}に使わない言葉があります: {bad}")
        w = sum(1 if ord(c) < 0x1100 else 2 for c in p["x"])
        if w > 280:
            sys.exit(f"投稿{p['no']}が長すぎます（{w}/280）")
    last = max([dt.datetime.fromisoformat(v) for v in state["x"].values()], default=None)
    start = max(filter(None, [dt.datetime.now(JST) + dt.timedelta(hours=2), last]))
    slots = next_slots(start, len(todo))
    if dry:
        for p, t in zip(todo, slots):
            print(t.isoformat(), p["no"], p["tag"])
        return 0

    if not key:
        sys.exit("TYPEFULLY_API_KEY がありません")
    sid = social_set(key)

    for p, t in zip(todo, slots):
        # 画像は文字やロゴを入れない写真だけ（Nori 2026-11-02「コマーシャル感強い」）
        img = os.path.join(ROOT, p["photo"])
        up = req("POST", f"/social-sets/{sid}/media/upload", key,
                 {"file_name": os.path.basename(img), "alt_text": p.get("alt") or p["head"].replace("\n", "")})
        # 署名つきURLへは、余計なヘッダーなしで中身だけ送る（urllib は Content-Type を足して 403 になる）
        subprocess.run(["curl", "-sS", "-f", "-T", img, up["upload_url"]], check=True, timeout=120)
        for _ in range(30):
            st = req("GET", f"/social-sets/{sid}/media/{up['media_id']}", key)
            if st.get("status") == "ready":
                break
            if st.get("status") == "failed":
                sys.exit(f"画像の取り込みに失敗: {img}")
            time.sleep(2)
        d = req("POST", f"/social-sets/{sid}/drafts", key, {
            "draft_title": f"ペットタクシー {p['no']} {p['tag']}",
            "platforms": {"x": {"enabled": True, "posts": [{"text": p["x"], "media_ids": [up["media_id"]]}]}},
            "publish_at": t.isoformat(),
        })
        state["x"][str(p["no"])] = t.isoformat()
        print("予約", t.isoformat(), p["no"], p["tag"], d.get("id"))
        json.dump(state, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
