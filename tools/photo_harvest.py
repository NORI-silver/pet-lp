#!/usr/bin/env python3
"""[C] 事業者カードの写真の候補を、各事業者の公式サイトから集める（Nori 2026-11-16「事業者カードへの写真表示 実装指示」）。

- 何も送らない・どこにも書き込まない（公式サイトを読むだけ）。コンテナからは各社のサイトに届かないので、
  .github/workflows/photo-harvest.yml（GitHub Actions）で動かし、結果をブランチ photo-cand に置く。
- 使ってよいか（利用許諾）が確かめられた写真だけを「候補」にする。無断転載はしない。
  permit: 事業者が「サイトの写真を使ってよい」と言ってくれた（tools/photo_permits.json に、いつ・どの範囲で・どうやっての記録）。
          → 公式サイト（と許可のページ）から写真を取り、ロゴ・地図・一色の画像を外して5枚まで縮める（人の顔らしいものは印を付け、入れるかは人が見て決める）
  ok    : サイトの決まり（著作権・サイトポリシーのページ、またはページの rel=license）に、
          CC BY / CC BY-SA / CC0 / 政府標準利用規約 / 公共データ利用規約 で使ってよいと書いてあり、
          写真がその対象から外されていない（「写真は除く」などがない）。→ 写真を縮めて候補にする（人が見て採る）
  check : 「転載自由」「ご自由にお使いください」など。言い方があいまいなので、人が読んでから決める（写真は取らない）
  no    : 「無断転載を禁じます」などがはっきり書いてある
  none  : 何も書いていない（著作権法では、書いていない＝使ってはいけない）
  fail  : 開けなかった
- 有料のAPI・サービスは使わない（各サイトを直接読むだけ）。
- 結果：OUT/index.json（全件の判定と出どころ）、OUT/summary.md（分野ごとの数）、OUT/img/<分野>/<id>_<n>.webp（ok の写真、520×347）、
  OUT/sheet_<n>.jpg（人が見て選ぶための一覧）。採った写真は tools/photo_import.py で img/fac/ と tools/photos.json に入れる。

使い方：python3 tools/photo_harvest.py OUT [分野 ... | 分野:id ...]
  permit の行に "no_people": true があれば、顔だけでなく人の体・上半身が写る写真も外す（人の写る写真は使わない、という条件の許可）。
  index.json の skipped に、使わなかった写真と理由（小さい・縦長・人の顔など）を残す。
"""
import html, io, json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
W, H = 520, 347

# 分野 → (ファイル, リストのキー, URL のキー)
SRC = {
    "taxi": ("display_companies.json", "companies", "url"),
    "emergency": ("emergency.json", "taxis", "url"),
    "sougi": ("sougi_facilities.json", "facilities", "u"),
    "rojin": ("rojin.json", "homes", "url"),
    "trainer": ("trainers.json", "trainers", "url"),
    "sitter": ("sitters.json", "sitters", "url"),
    "trimming": ("grooming.json", "groomers", "url"),
    "hotel": ("hotels.json", "hotels", "url"),
    "hospital": ("vet_clinics.json", "clinics", "url"),
    "night": ("night_hospital_facts.json", "items", "url"),
    "dogrun": ("dogrun.json", "dogruns", "url"),
}

OK = re.compile(r'クリエイティブ・?コモンズ[^。]{0,60}(表示|BY|ＢＹ)|CC[ \-]?BY|creativecommons\.org/(licenses/by(-sa)?/|publicdomain)|政府標準利用規約|公共データ利用規約|(?-i:\bCC0\b)', re.I)
NC = re.compile(r'by-nc|by-nd|非営利|改変禁止|NC[ \-]?ND|BY-NC|BY-ND', re.I)
PHOTO_EXCL = re.compile(r'(写真|画像|イラスト|図版)[^。]{0,60}(除|対象外|含まれ(ません|ない)|適用され(ません|ない)|別途|第三者)')
FREE = re.compile(r'転載(は|も)?(自由|可|OK|歓迎)|自由に(ご)?(利用|使用|転載)|ご自由にお使い|フリー素材')
FORBID = re.compile(r'無断(で|の)?(転載|複製|使用|転用|利用)|(転載|複製|転用)(を|は)?(禁|お断り|ご遠慮)|All rights reserved', re.I)
POLICY_LINK = re.compile(r'著作権|サイトポリシー|サイトのご利用|ご利用にあたって|このサイトについて|当サイトについて|ホームページについて|利用規約|リンク[・･]?著作権|免責|copyright|site ?policy|privacy|プライバシー', re.I)
BAD_IMG = re.compile(r'logo|icon|bnr|banner|btn|button|arrow|map|title|header|footer|spacer|qr|sns|line|twitter|facebook|insta|youtube|ttl|nav|bg_|/bg|blank|loading|sprite|favicon|badge|stamp|tel|mail|pdf|ロゴ|バナー', re.I)


def get(url, timeout=25, binary=False):
    u = urllib.parse.urlsplit(url)
    url = urllib.parse.urlunsplit((u.scheme, u.netloc.encode('idna').decode(), urllib.parse.quote(u.path, safe='/%:@!$&\'()*+,;=~'),
                                   urllib.parse.quote(u.query, safe='=&%:/?+,;~'), ''))
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja,en;q=0.5'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(6_000_000)
        if binary: return raw, r.headers.get_content_type()
        cs = r.headers.get_content_charset() or (re.search(rb'charset=["\']?([\w-]+)', raw[:3000]) or [None, b'utf-8'])[1].decode()
        try: return raw.decode(cs, 'replace'), r.geturl()
        except LookupError: return raw.decode('utf-8', 'replace'), r.geturl()


def text(t):
    t = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', t)
    return re.sub(r'[\s　]+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t)))


def permits():
    """事業者が「サイトの写真を使ってよい」と言ってくれた記録（tools/photo_permits.json）。キーは "分野:id"。"""
    p = os.path.join(HERE, "photo_permits.json")
    if not os.path.exists(p): return {}
    return {f'{x["cat"]}:{x["id"]}': x for x in json.load(open(p, encoding="utf-8"))["permits"]}


_FACE = None
def has_face(im):
    """人の顔が写った写真は使わない（正面・横顔）。opencv がなければ調べられないので、使わない側に倒す。"""
    global _FACE
    try:
        import cv2, numpy as np
        cv2.CascadeClassifier
    except Exception:
        return True
    if _FACE is None:
        _FACE = [cv2.CascadeClassifier(cv2.data.haarcascades + n) for n in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml")]
    g = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2GRAY)
    return any(len(c.detectMultiScale(g, 1.1, 6, minSize=(max(24, im.width // 25),) * 2)) for c in _FACE)


_BODY = None
def has_person(im):
    """人が写っている写真（顔のほか、体・上半身）。「人の写る写真は使わない」という条件つきの許可のとき。"""
    global _BODY
    if has_face(im): return True
    import cv2, numpy as np  # has_face が False なら opencv はある
    if _BODY is None:
        _BODY = [cv2.CascadeClassifier(cv2.data.haarcascades + n) for n in ("haarcascade_fullbody.xml", "haarcascade_upperbody.xml")]
    g = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2GRAY)
    return any(len(c.detectMultiScale(g, 1.05, 5, minSize=(max(40, im.width // 10),) * 2)) for c in _BODY)


def items(cats):
    out = []
    for cat in cats:
        f, key, uk = SRC[cat]
        d = json.load(open(os.path.join(HERE, f), encoding='utf-8'))[key]
        for x in d:
            u = x.get(uk) or x.get('url')
            if isinstance(u, list): u = u[0] if u else None
            if not u or not str(u).startswith('http'): continue
            out.append({"cat": cat, "id": x.get("id") or "", "name": x.get("name", ""), "url": u})
    return out


def judge(t, base):
    """ページと、同じサイトの決まりのページを読んで判定する。"""
    txt = text(t)
    lic = re.findall(r'(?is)<(?:a|link)[^>]+rel=["\']?license["\']?[^>]*href=["\']([^"\']+)', t) + \
          re.findall(r'(?is)<(?:a|link)[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']?license', t)
    pages = [(base, txt + ' ' + ' '.join(lic))]
    host = urllib.parse.urlsplit(base).netloc
    seen = set()
    for href, lab in re.findall(r'(?is)<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', t):
        lab = re.sub(r'<[^>]+>', '', lab)
        u = urllib.parse.urljoin(base, html.unescape(href))
        if urllib.parse.urlsplit(u).netloc != host or u in seen: continue
        if POLICY_LINK.search(lab) or re.search(r'policy|copyright|chosakuken|sitepolicy|riyou|kiyaku', u, re.I):
            seen.add(u)
            if len(seen) > 3: break
            try:
                pt, _ = get(u)
                pages.append((u, text(pt)))
            except Exception:
                pass
    for u, tx in pages:
        m = OK.search(tx)
        if m:
            win = tx[max(0, m.start() - 300): m.end() + 600]
            if NC.search(win): return "check", u, "非営利・改変禁止の条件つき：" + NC.search(win).group(0)
            if PHOTO_EXCL.search(tx): return "check", u, "写真が対象外の書き方：" + PHOTO_EXCL.search(tx).group(0)[:120]
            return "ok", u, m.group(0)
    for u, tx in pages:
        m = FREE.search(tx)
        if m: return "check", u, tx[max(0, m.start() - 60): m.end() + 60]
    for u, tx in pages:
        m = FORBID.search(tx)
        if m: return "no", u, m.group(0)
    return "none", pages[-1][0] if len(pages) > 1 else base, ""


def imgs(t, base, deep=False):
    """ページの写真のURL。deep（事業者の許可がある）のときは srcset・背景の画像・ページの中に書かれた画像のURLも拾う。"""
    out = []
    for m in re.findall(r'(?is)<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', t):
        out.append(m)
    for tag in re.findall(r'(?is)<(?:img|source)\b[^>]*>', t):
        a = dict((k.lower(), v) for k, v in re.findall(r'([\w-]+)=["\']([^"\']*)["\']', tag))
        if BAD_IMG.search(a.get('alt', '')) or BAD_IMG.search(a.get('class', '')): continue
        try:
            if int(a.get('width', '999')) < 300: continue
        except ValueError:
            pass
        ss = a.get('data-srcset') or a.get('srcset') or ''
        if ss:  # いちばん大きいもの
            c = [x.strip().split() for x in ss.split(',') if x.strip()]
            c = sorted(c, key=lambda x: float(re.sub(r'[^\d.]', '', x[1]) or 0) if len(x) > 1 else 0)
            if c: out.append(c[-1][0])
        s = a.get('data-src') or a.get('data-lazy-src') or a.get('data-original') or a.get('src') or ''
        if s and not s.startswith('data:'): out.append(s)
    if deep:
        out += re.findall(r'(?is)background(?:-image)?\s*:[^;"]*url\(\s*["\']?([^"\')]+)', t)
        out += re.findall(r'(?is)data-(?:bg|background|image)=["\']([^"\']+)', t)
        out += re.findall(r'https?:(?:\\?/){2}[^"\'\s<>()]+?\.(?:jpe?g|png|webp)', t, re.I)
    res = []
    for s in out:
        u = urllib.parse.urljoin(base, html.unescape(s.replace('\\/', '/')))
        if BAD_IMG.search(urllib.parse.urlsplit(u).path): continue
        if re.search(r'\.(jpe?g|png|webp)(\?|$|/)', u, re.I) and u not in res: res.append(u)
    return res[:40 if deep else 8]


def shrink(raw, no_people=False):
    """(縮めた webp, 人の印) を返す。使わないときは理由の文字列を返す。
    人の顔・体の見分け（opencv）は犬や猫の顔でも反応し、後ろ姿は見のがすので、ここでは外さずに印（"face"／"person"）を付ける。
    印のある写真は photo_import.py が入れない（人が一覧を見て、写っていないと確かめたものだけ --keep で入れる）。"""
    from PIL import Image, ImageStat
    im = Image.open(io.BytesIO(raw)); im.load()
    if im.width < 480 or im.height < 300: return f"小さい {im.width}x{im.height}"
    r = im.width / im.height
    if not (1.0 <= r <= 2.4): return f"縦長・細長 {im.width}x{im.height}"
    im = im.convert('RGB')
    if max(ImageStat.Stat(im.resize((32, 32))).stddev) < 18: return "一色に近い"  # 背景・飾り
    flag = ("person" if has_person(im) else "") if no_people else ("face" if has_face(im) else "")
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    # カードの枠（横3：縦2）にきれいに収まるように切る。まん中ではなく、写っているもの（輪郭の多いところ）が入る位置を選ぶ
    from PIL import ImageFilter
    e = im.convert("L").filter(ImageFilter.FIND_EDGES)
    best, x, y = -1, 0, 0
    for k in range(9):
        cx, cy = (im.width - W) * k // 8, (im.height - H) * k // 8
        v = sum(e.crop((cx, cy, cx + W, cy + H)).resize((26, 17)).getdata())
        v *= 1.0 - abs(k - 4) * 0.04  # まん中を少しだけ優先
        if v > best: best, x, y = v, cx, cy
    im = im.crop((x, y, x + W, y + H))
    b = io.BytesIO(); im.save(b, 'WEBP', quality=62, method=6)
    return b.getvalue(), flag


PERMITS = {}


def one(it, out):
    try:
        t, real = get(it["url"])
    except Exception as e:
        return dict(it, status="fail", note=str(e)[:80])
    pm = PERMITS.get(f'{it["cat"]}:{it["id"]}')
    title = re.search(r'(?is)<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)', t) or re.search(r'(?is)<title[^>]*>(.*?)</title>', t)
    owner = re.sub(r'\s+', ' ', html.unescape(title.group(1))).strip()[:40] if title else ""
    if pm:  # 事業者の許可がある：許可の範囲（pages があればそのページ、なければ公式サイト）から取る
        st, pol, note = "permit", pm.get("date", ""), f'{pm.get("by", "")}・{pm.get("scope", "")}'
    else:
        st, pol, note = judge(t, real)
    r = dict(it, status=st, policy=pol, note=note, owner=owner, photos=[], skipped=[])
    if st not in ("ok", "permit"): r.pop("skipped"); return r
    d = os.path.join(out, "img", it["cat"]); os.makedirs(d, exist_ok=True)
    cand = imgs(t, real, deep=bool(pm))
    if pm:
        for pg in pm.get("pages") or []:
            try:
                pt, preal = get(pg); cand += [u for u in imgs(pt, preal, deep=True) if u not in cand]
            except Exception as e:
                r["skipped"].append([pg, "ページを開けない " + str(e)[:60]])
    if not cand: r["skipped"].append([real, "写真のURLが見つからない（ページを動かすプログラムが出す写真かもしれない）"])
    no_people = bool(pm and pm.get("no_people"))
    for u in cand[:40 if pm else 16]:
        if len(r["photos"]) >= (5 if pm else 3): break
        try:
            raw, ct = get(u, binary=True)
            w = shrink(raw, no_people)
        except Exception as e:
            r["skipped"].append([u, "開けない " + str(e)[:60]]); continue
        if isinstance(w, str):
            r["skipped"].append([u, w]); continue
        w, flag = w
        fn = f'{it["id"]}_{len(r["photos"]) + 1}.webp'
        open(os.path.join(d, fn), "wb").write(w)
        r["photos"].append({"file": f'img/{it["cat"]}/{fn}', "src": u, "page": real, **({"flag": flag} if flag else {})})
    return r


def sheets(out, rows):
    from PIL import Image, ImageDraw
    pics = [(r, p) for r in rows for p in r.get("photos", [])]
    for k in range(0, len(pics), 24):
        part = pics[k:k + 24]
        sh = Image.new("RGB", (4 * 260, ((len(part) + 3) // 4) * 200), "white")
        dr = ImageDraw.Draw(sh)
        for i, (r, p) in enumerate(part):
            im = Image.open(os.path.join(out, p["file"])).resize((260, 173))
            x, y = (i % 4) * 260, (i // 4) * 200
            sh.paste(im, (x, y)); dr.text((x + 4, y + 176), f'{k + i} {r["cat"]}:{r["id"]}', fill="black")
        sh.save(os.path.join(out, f"sheet_{k // 24 + 1}.jpg"), quality=80)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "photo-cand"
    args = sys.argv[2:]
    only = {a for a in args if ":" in a}  # 「分野:id」で1社だけやり直す
    cats = [a for a in args if ":" not in a] or sorted({a.split(":")[0] for a in only}) or list(SRC)
    os.makedirs(out, exist_ok=True)
    PERMITS.update(permits())
    its = [it for it in items(cats) if not only or f'{it["cat"]}:{it["id"]}' in only]
    t0 = time.time()
    with ThreadPoolExecutor(16) as ex:
        rows = list(ex.map(lambda it: one(it, out), its))
    json.dump(rows, open(os.path.join(out, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sheets(out, rows)
    L = ["# 事業者カードの写真の候補（公式サイトの利用許諾）", "",
         f"{time.strftime('%Y-%m-%d')}・{len(rows)}件・{int(time.time() - t0)}秒", "",
         "| 分野 | 件数 | permit（事業者の許可） | ok（使ってよい） | check（人が読む） | no（転載禁止と明記） | none（書いていない） | fail（開けない） | 写真 |", "|---|---|---|---|---|---|---|---|---|"]
    for c in cats:
        rs = [r for r in rows if r["cat"] == c]
        n = {s: sum(r["status"] == s for r in rs) for s in ("permit", "ok", "check", "no", "none", "fail")}
        L.append(f'| {c} | {len(rs)} | {n["permit"]} | {n["ok"]} | {n["check"]} | {n["no"]} | {n["none"]} | {n["fail"]} | {sum(len(r.get("photos", [])) for r in rs)} |')
    L += ["", "## permit・ok・check", "", "| 分野 | id | 名前 | 判定 | 決まりのページ | 根拠 | 写真 |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["status"] in ("permit", "ok", "check"):
            L.append(f'| {r["cat"]} | {r["id"]} | {r["name"]} | {r["status"]} | {r.get("policy", "")} | {r.get("note", "")[:100].replace("|", "／")} | {len(r.get("photos", []))} |')
    for r in rows:
        if r["status"] == "permit":
            L += ["", f'### {r["cat"]}:{r["id"]} {r["name"]}（写真 {len(r["photos"])}枚）', ""] + [f'- {u} … {why}' for u, why in r.get("skipped", [])[:30]]
    open(os.path.join(out, "summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
