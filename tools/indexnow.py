# [B] IndexNow：本文が変わったページのURLを検索エンジン（Bing など）に知らせる（2026-11-08）。
# .github/workflows/pages.yml の公開のあとに動く。sitemap.xml の前の版とくらべて、lastmod が変わった・増えたURLだけを送る。
# 送るのはページのURLだけ。鍵はサイトの /<鍵>.txt に置いてある公開の値。
#   python3 tools/indexnow.py <前のコミット>   … そのコミットとくらべて送る（空なら1つ前のコミット）
#   python3 tools/indexnow.py --all            … sitemap の全部を送る（はじめの1回や、手で送り直すとき）
#   python3 tools/indexnow.py <前> --dry       … 送らずに一覧だけ出す
import glob, json, os, re, subprocess, sys, urllib.request

HOST = "pet.shiokonbu.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def key():
    for f in glob.glob(os.path.join(ROOT, "*.txt")):
        k = os.path.basename(f)[:-4]
        if re.fullmatch(r"[0-9a-f]{32}", k) and open(f).read().strip() == k:
            return k
    raise SystemExit("鍵のファイルがありません")

def entries(text):
    return dict(re.findall(r"<loc>(.*?)</loc><lastmod>(.*?)</lastmod>", text))

def git_show(rev, path):
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None

def changed(before):
    now = entries(open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read())
    if not before or set(before) == {"0"}:
        before = "HEAD~1"
    old_text = git_show(before, "sitemap.xml")
    if old_text is None:
        return []
    old = entries(old_text)
    urls = [u for u, d in now.items() if old.get(u) != d]
    if git_show(before, "llms.txt") != open(os.path.join(ROOT, "llms.txt"), encoding="utf-8").read():
        urls.append(f"https://{HOST}/llms.txt")
    return urls

def send(urls, k):
    for i in range(0, len(urls), 10000):
        body = json.dumps({"host": HOST, "key": k, "keyLocation": f"https://{HOST}/{k}.txt", "urlList": urls[i:i + 10000]}).encode()
        req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow", r.status, len(urls[i:i + 10000]), "件")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all" in sys.argv:
        urls = list(entries(open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read())) + [f"https://{HOST}/llms.txt"]
    else:
        urls = changed(args[0] if args else "")
    print("\n".join(urls[:30]) + (f"\n…ほか{len(urls) - 30}件" if len(urls) > 30 else ""))
    if not urls:
        print("変わったページはありません"); sys.exit(0)
    if "--dry" in sys.argv:
        sys.exit(0)
    send(urls, key())
