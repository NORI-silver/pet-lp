#!/usr/bin/env python3
"""[G] 門（もん）＝送信の関所。外に出るメール・フォームは、全部ここを通ってから送る（Nori 2026-11-23「三体」＝要・作り手・門）。

なぜ：2026-11-23、Mac のメールのスレッドと提携のスレッドが同じ会社に同時に送り、ニャンワンクラブと PetTAXI24 に2通目が出た。
Nori「追って送るなよ、ややこしい」「メールのラリーが少なくなることを意識しろ」。1社1通で完結、追いメールなし、送るのは1か所だけ。
これまで問（とい）・鏡（かがみ）・関（せき）が送る前に見ていたことは、ここにまとめる（別の係にしない）。

使い方（送る係はこの順番だけ）:
  1) 見るだけ   python3 tools/mon.py check 本文.txt --company 会社名 --to 宛先 --method メール|フォーム --purpose 用件 [--gmail-sent 件数]
  2) 送る直前   python3 tools/mon.py take  本文.txt …（1と同じ）… --by 係の名前      → 通れば「受付番号」。台帳に「送信中」と書いて、ほかの係を止める
  3) 送ったあと python3 tools/mon.py done 受付番号 --result 送信済み|止めた|取りやめ [--note メモ]
  台帳を見る   python3 tools/mon.py log [--days 1] [--company 名前]
  受付番号のない送信は、送ってはいけない。take が止めたら送らない（Noriさんに見せる）。

--purpose（用件）: お誘い・再お誘い・写真のお願い・紹介の依頼・返事・その他。返事（相手から来たメールへの答え）は --reply も付ける。
--gmail-sent: 送る前に pettaxi.yoyaku の送信済みを「to:宛先 newer_than:7d」でさがした件数（メールのときは必ず）。
--nori 発言ID: Noriさんが「この会社にもう一度送って」「時間外でも送って」と言ったときだけ。同じ日の2通目・ほかの係が送信中のものは、これでも通さない。

台帳: 非公開の pet-db のブランチ claude/project-thread-yqaim8 の data/mon/ledger.tsv（日付をまたいで1本。Mac もクラウドも同じもの）。
  mon.py が ~/.mon-ledger にその枝だけを取ってきて、毎回 pull → 追記 → push する。push がぶつかったら取り直す（ロックの代わり）。
  変えるとき：MON_REPO（置き場）・MON_REMOTE（pet-db のURL）・MON_BRANCH。git を使わず1つのファイルにするときは MON_LEDGER。
連絡しない相手: 台帳と同じ所の data/mon/do_not_contact.json（Bande など）。読めなければ止める。
"""
import datetime as dt, json, os, re, secrets, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
GIT = "MON_LEDGER" not in os.environ
REPO = os.path.expanduser(os.environ.get("MON_REPO", "~/.mon-ledger"))
BRANCH = os.environ.get("MON_BRANCH", "claude/project-thread-yqaim8")
LEDGER = os.environ.get("MON_LEDGER") or os.path.join(REPO, "data", "mon", "ledger.tsv")


def _remote():
    if os.environ.get("MON_REMOTE"): return os.environ["MON_REMOTE"]
    sib = os.path.join(HERE, "..", "..", "pet-db")  # となりの pet-db と同じ取り先
    if os.path.isdir(os.path.join(sib, ".git")):
        r = subprocess.run(["git", "-C", sib, "remote", "get-url", "origin"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip(): return r.stdout.strip()
    return "https://github.com/NORI-silver/pet-db.git"


def g(*a, check=True):
    r = subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
    if check and r.returncode: sys.exit(f"git {' '.join(a)} が失敗：{(r.stderr or r.stdout).strip()[:300]}\n台帳が取れないので送らない")
    return r


def pull():
    """台帳を最新にする（手元の変更は捨てて、GitHub のものに合わせる。台帳は mon.py しか書かない）"""
    if not GIT: return
    if not os.path.isdir(os.path.join(REPO, ".git")):
        r = subprocess.run(["git", "clone", "-q", "--depth", "1", "--single-branch", "-b", BRANCH, _remote(), REPO], capture_output=True, text=True)
        if r.returncode: sys.exit(f"台帳を取ってこられない：{r.stderr.strip()[:300]}\n送らない")
    g("fetch", "-q", "--depth", "1", "origin", BRANCH)
    g("reset", "-q", "--hard", "FETCH_HEAD")


def push(msg):
    """追記を送る。ほかの係が先に送っていたら False（取り直してもう一度）"""
    if not GIT: return True
    g("add", "data/mon/ledger.tsv")
    g("-c", "user.name=mon", "-c", "user.email=mon@pet.shiokonbu.com", "commit", "-q", "-m", msg)
    return g("push", "-q", "origin", f"HEAD:{BRANCH}", check=False).returncode == 0


def locked(work):
    """git のときは pull → work → push を、ぶつからなくなるまで（5回まで）くり返す。ファイルのときは鍵"""
    if not GIT:
        with Lock(): return work()
    for _ in range(5):
        pull()
        res = work()
        if res is None: return None
        ok, msg = res
        if not ok or push(msg): return res
        time.sleep(1 + secrets.randbelow(3))
    sys.exit("台帳がほかの係とぶつかり続けた。少し待ってもう一度（送らない）")
COLS = ["受付番号", "日時", "状態", "会社", "宛先", "方法", "用件", "係", "メモ"]
JST = dt.timezone(dt.timedelta(hours=9))
DAY_LIMIT = 500         # プロジェクト側の1日のメール上限（Gmail側の上限は別）
HOURS = (6, 21)         # 送ってよい時間（JST）。6:00から21:00未満
QUIET_DAYS = 7          # 同じ会社に、返事以外で続けて送らない日数（相手の返事を待つ）
DONE = ("送信済み", "止めた", "取りやめ")

# 費用の一文はこれだけ（Nori 2026-11-23「200回言ってる」）。前半の「いまは費用はかかりません。」もこのまま。
FEE_LINE = "今後費用をいただく形にする場合は、少なくとも30日前にご連絡いたします。続けてご利用いただくかどうかは、その時点でご判断いただけます。"
FEE_WORDS = r"費用|手数料|紹介料|掲載料|利用料|有料|成約|課金|料金をいただ|お支払いいただ|[0-9０-９]+\s*(?:%|％)|[0-9０-９一二三四五六七八九十]+\s*割(?!引|り|増)"
# 1通で完結：追いメールの言い方（Nori 2026-11-23「追って送るなよ」）
FOLLOW = r"追って|追送|追伸で|先ほど(?:の)?(?:メール|ご連絡|お送り)|送り忘れ|書き忘れ|抜けて(?:い)?ました|漏れて(?:い)?ました|補足(?:です|いたします|させて)|改めてお送り|別途(?:お送り|ご連絡)|後ほど[^。\n]{0,8}(?:お送り|ご連絡)|あらためて(?:お送り|ご連絡いたします)"
LINK_WORDS = r"リンク|URL|下記のページ|こちらのページ|確認ページ|申し込みのページ|申し込みページ"
ALIASES = ["ペッタク", "BOOM", "加茂"]  # 表示名にない呼び名（相手にほかの会社の名前を出さない）
GENERIC = {"ペットタクシー", "ペット", "タクシー", "COCOタク", "ココタク", "CoCoタク", "ペット送迎", "ペット霊園", "動物病院"}


def now():
    return dt.datetime.now(JST)


# ---------- 台帳 ----------
def read_ledger():
    if not os.path.exists(LEDGER): return []
    rows = []
    for ln in open(LEDGER, encoding="utf-8").read().splitlines()[1:]:
        f = ln.split("\t")
        if len(f) >= 8: rows.append(dict(zip(COLS, f + [""] * (len(COLS) - len(f)))))
    return rows


def latest(rows):
    """受付番号ごとに最後の行（状態）だけ"""
    d = {}
    for r in rows: d[r["受付番号"]] = {**d.get(r["受付番号"], dict.fromkeys(COLS, "")), **{k: v for k, v in r.items() if v}}
    return list(d.values())


class Lock:
    """ネットワークのフォルダでも効くように、ファイルを作れたら鍵を持てる形（O_EXCL）"""
    def __init__(self): self.p = LEDGER + ".lock"
    def __enter__(self):
        for _ in range(100):
            try:
                os.close(os.open(self.p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)); return self
            except FileExistsError:
                if time.time() - os.path.getmtime(self.p) > 120: os.remove(self.p)  # 2分より古い鍵は落ちたもの
                time.sleep(0.2)
        sys.exit("台帳の鍵が取れない（ほかの係が書いている）。少し待ってもう一度")
    def __exit__(self, *a):
        try: os.remove(self.p)
        except FileNotFoundError: pass


def append(row):
    new = not os.path.exists(LEDGER)
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        if new: f.write("\t".join(COLS) + "\n")
        f.write("\t".join(str(row.get(c, "")).replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")


def norm(s):
    s = re.sub(r"[（(【].*?[）)】]", "", s or "")
    return re.sub(r"[\s　・]+", "", s).lower()


def same(r, company, to):
    a, b = norm(r["会社"]), norm(company)
    if a and b and (a == b or (min(len(a), len(b)) >= 4 and (a in b or b in a))): return True
    return bool(to) and r["宛先"].strip().lower() == to.strip().lower()


# ---------- 本文 ----------
def names():
    ns = set(ALIASES)
    try:
        for c in json.load(open(os.path.join(HERE, "display_companies.json"), encoding="utf-8"))["companies"]:
            n = re.sub(r"[（(【].*?[）)】]", "", c.get("name") or "").strip()
            if len(n) >= 3 and n not in GENERIC: ns.add(n)
            for p in re.split(r"[\s　]+", n):
                if len(p) >= 3 and p not in GENERIC: ns.add(p)
    except Exception:
        pass
    return ns


def body_checks(t, company, to):
    out = []
    lines = [l for l in t.splitlines() if l.strip()]
    # 全文（宛名から署名まで）
    try:
        import draft_check as dc
        rules, head, sign, hypo = dc.RULES, dc.HEAD, dc.SIGN, dc.HYPO
    except Exception:
        rules, head, sign, hypo = [], r"様|さま|御中|ご担当|各位", r"塩田", r"(?!)"
    if not lines or not re.search(head + r"|さま", "\n".join(lines[:3])) or not re.search(sign, "\n".join(lines[-4:])):
        out.append("全文でない（宛名から署名まで。署名は「塩田」）")
    # ほかの会社の名前（宛名の行までに出る相手の名前はよい）
    k = next((i for i, l in enumerate(lines[:4]) if re.search(r"様|さま|御中|ご担当", l)), 0)
    headtxt = "\n".join(lines[:k + 1]) + "\n" + (company or "")
    for n in sorted(names(), key=len, reverse=True):
        if n in headtxt or norm(n) in norm(company): continue
        if n in t:
            out.append(f"「{n}」: ほかの会社の名前を相手に出さない（「提携先の会社さま」と書く）")
    # 費用の一文
    masked = t.replace(FEE_LINE, "＿" * len(FEE_LINE)).replace("いまは費用はかかりません。", "＿" * 13)
    for m in re.finditer(FEE_WORDS, masked):
        ln = masked.count("\n", 0, m.start()) + 1
        out.append(f"{ln}行目「{m.group()}」: 費用・手数料・率の話は決まった一文だけ（「いまは費用はかかりません。{FEE_LINE}」）")
    if re.search(r"費用", t) and FEE_LINE not in t:
        out.append("費用にふれるなら、決まった一文をそのまま入れる")
    # draft_check の言葉の決まり（お金の行は上で見たので外す）
    for pat, why in rules:
        if "お金" in why: continue
        for m in re.finditer(pat, masked):
            out.append(f"{masked.count(chr(10), 0, m.start()) + 1}行目「{m.group()}」: {why}")
    for m in re.finditer(hypo, t):
        out.append(f"「{m.group()}」: 相手が言っていない前提・約束を足さない")
    # 1通で完結
    for m in re.finditer(FOLLOW, t):
        out.append(f"「{m.group()}」: 追いメールの言い方。1通で完結させる（前のメールにたよらず、要るものを全部この1通に）")
    if re.search(LINK_WORDS, t) and not re.search(r"https?://", t):
        out.append("リンク・ページの話があるのにURLがない（1通で完結：URLも入れる）")
    if not re.search(r"ください|いただけ|お願い|でしょうか|？|\?", t):
        out.append("相手に頼むこと・聞くことがない（何をしてほしいかを1通に）")
    if len(t) > 1200: out.append(f"{len(t)}字。長い（短く、でも要るものは全部）")
    return out


# ---------- 相手・時間・回数 ----------
def blocked_contacts():
    for p in (os.path.join(os.path.dirname(LEDGER), "do_not_contact.json"),
              os.path.join(HERE, "..", "..", "pet-db", "data", "contacts", "do_not_contact.json")):
        if os.path.exists(p): return json.load(open(p, encoding="utf-8")).get("items", [])
    return None


def host(u):
    m = re.search(r"(?:https?://)?(?:[^@/\s]*@)?([^/\s:]+)", u or "")
    return (m.group(1).lower().removeprefix("www.") if m else "")


def gate(a, t):
    out = []
    company, to, method, purpose = a.get("company", ""), a.get("to", ""), a.get("method", ""), a.get("purpose", "")
    reply, nori = "reply" in a, a.get("nori", "")
    if not company or not to: out.append("--company（会社名）と --to（宛先のメール・フォームのURL）を入れる")
    if method not in ("メール", "フォーム"): out.append("--method は メール か フォーム")
    if not purpose: out.append("--purpose（用件：お誘い・再お誘い・写真のお願い・紹介の依頼・返事・その他）を入れる")
    # 連絡しない相手（Bande など。Noriさんが決めた相手）
    dnc = blocked_contacts()
    if dnc is None: out.append("連絡しない相手の一覧が読めない（pet-db か /mnt/project-files/mon/do_not_contact.json）。読めるまで送らない")
    for d in dnc or []:
        nm = norm(re.sub(r"[（(].*?[）)]", "", d.get("name", ""))) or "\0"
        kana = re.findall(r"[（(](.*?)[）)]", d.get("name", ""))
        hs = {host(d.get("url", ""))} - {""}
        if nm in norm(company) or any(k and k in company for k in kana) or (host(to) and host(to) in hs) \
                or any(h and h.split(".")[0] in to.lower() for h in hs):
            out.append(f"連絡しない相手（{d.get('name')}・{d.get('where', '')}、{d.get('by', '')} {d.get('date', '')}「{d.get('why', '')}」）。送らない")
    # 時間
    n = now()
    if not (HOURS[0] <= n.hour < HOURS[1]) and not nori:
        out.append(f"いま{n:%H:%M}。送るのは{HOURS[0]}時から{HOURS[1]}時まで（Noriさんが時間外でもと言ったら --nori 発言ID）")
    # 台帳：送信中・同じ日・同じ用件・7日
    rows = latest(read_ledger())
    mine = [r for r in rows if same(r, company, to)]
    for r in mine:
        when = r["日時"][:16]
        if r["状態"] == "送信中":
            out.append(f"{r['係']}が{when}から送信中（{r['受付番号']}）。二重に送らない。送った・送っていないを送信済みで確かめて done を書く")
        elif r["状態"] == "送信済み":
            day = r["日時"][:10]
            if day == f"{n:%Y-%m-%d}":
                out.append(f"今日すでに送っている（{when}・{r['用件']}・{r['係']}）。同じ日の2通目は送らない（--nori でも通さない）")
            elif r["用件"] == purpose and not reply and not nori:
                out.append(f"同じ用件「{purpose}」をもう送っている（{when}）。くり返し送らない（Noriさんが決めたら --nori 発言ID）")
            elif day >= f"{n - dt.timedelta(days=QUIET_DAYS):%Y-%m-%d}" and not reply and not nori:
                out.append(f"{when}に送ったばかり（{r['用件']}）。相手の返事を待つ（返事への答えなら --reply）")
    # Gmail の送信済み（台帳の外で送ったものも見つける）
    if method == "メール":
        g = a.get("gmail-sent")
        if g is None or not str(g).isdigit():
            out.append("送る前に pettaxi.yoyaku の送信済みを「to:宛先 newer_than:7d」でさがし、件数を --gmail-sent に入れる")
        elif int(g) > 0 and not reply and not nori:
            out.append(f"送信済みに、この宛先へのメールが7日以内に{g}通ある（台帳にないもの）。送らない。台帳に足す")
        sent_today = sum(1 for r in rows if r["方法"] == "メール" and r["状態"] in ("送信済み", "送信中") and r["日時"][:10] == f"{n:%Y-%m-%d}")
        if sent_today >= DAY_LIMIT:
            out.append(f"今日のメールが{sent_today}通。1日{DAY_LIMIT}通まで（明日にする）")
    return out + body_checks(t, company, to)


# ---------- コマンド ----------
def parse(argv):
    a, pos, i = {}, [], 0
    while i < len(argv):
        x = argv[i]
        if x.startswith("--"):
            k = x[2:]
            if "=" in k: k, v = k.split("=", 1); a[k] = v
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--"): a[k] = argv[i + 1]; i += 1
            else: a[k] = True
        else: pos.append(x)
        i += 1
    return a, pos


def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    cmd, (a, pos) = sys.argv[1], parse(sys.argv[2:])
    if cmd in ("check", "take"):
        if not pos: sys.exit("本文のファイルを入れる（フォームでも、送る文を全部ファイルに）")
        t = open(pos[0], encoding="utf-8").read()
        if cmd == "take":
            if not a.get("by"): sys.exit("--by に送る係の名前（例：文・結）")
            box = {}
            def work():
                box["res"] = res = gate(a, t)
                if res: return (False, "")
                box["no"] = no = f"M{now():%m%d-%H%M}-{secrets.token_hex(2)}"
                append({"受付番号": no, "日時": now().isoformat(timespec="minutes"), "状態": "送信中", "会社": a["company"], "宛先": a["to"],
                        "方法": a["method"], "用件": a["purpose"], "係": a["by"], "メモ": ("Nori " + a["nori"]) if a.get("nori") else ""})
                return (True, f"門 take {no} {a['company']} {a['by']}")
            locked(work)
            res, no = box["res"], box.get("no")
        else:
            pull()
            res = gate(a, t)
        for r in res: print("止める:", r)
        if res: print(f"{len(res)}か所。送らない"); sys.exit(1)
        print(f"通る。受付番号 {no}（送ったら: python3 tools/mon.py done {no} --result 送信済み）" if cmd == "take" else "通る（送る直前に take で受付番号をもらう）")
    elif cmd == "done":
        if not pos or a.get("result") not in DONE: sys.exit("python3 tools/mon.py done 受付番号 --result 送信済み|止めた|取りやめ")
        def work():
            if pos[0] not in {r["受付番号"] for r in read_ledger()}: sys.exit("その受付番号は台帳にない")
            append({"受付番号": pos[0], "日時": now().isoformat(timespec="minutes"), "状態": a["result"], "メモ": a.get("note", "")})
            return (True, f"門 done {pos[0]} {a['result']}")
        locked(work)
        print("台帳に書いた:", pos[0], a["result"])
    elif cmd == "log":
        pull()
        days = int(a.get("days", 1)); since = f"{now() - dt.timedelta(days=days - 1):%Y-%m-%d}"
        for r in sorted(latest(read_ledger()), key=lambda r: r["日時"]):
            if r["日時"][:10] >= since and (not a.get("company") or same(r, a["company"], "")):
                print("\t".join(r.get(c, "") for c in COLS))
    else:
        print(__doc__); sys.exit(2)


if __name__ == "__main__":
    main()
