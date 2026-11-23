#!/usr/bin/env python3
"""[B] 掲載の候補の公式サイトを読んで、確かめに要る文だけを抜き出す（Nori 2026-11-22「漏れなく掲載して」）。
tools/crawl/queue.json（[{"cat","pref","url"}...]）の各URLと、同じサイトの中の「料金・アクセス・会社概要」などのページ（最大4つ）を開き、
住所・料金・サービス・受け入れの条件などの行を tools/crawl/ の外の out/<名前>.json に書く。何も送らない・サイトは書き換えない。
載せるかどうかは人（AI）が行を読んで決め、各分野のデータ（hotels.json など）に出どころつきで入れる。
.github/workflows/site-snap.yml から動かす（コンテナからは各社のサイトに届かないため）。
"""
import concurrent.futures as cf, html, json, os, re, sys, urllib.parse, urllib.request

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
KEY = re.compile(r'〒|住所|所在地|[都道府県].{1,8}[市区町村郡]|円|料金|営業|定休|受付|時間|対象|受け入れ|お預かり|預かり|ホテル|訓練|トレーニング|しつけ|トリミング|出張|訪問|対応エリア|地域|老犬|介護|大型|猫|うさぎ|登録|動物取扱|第\d+号|資格|送迎|閉店|休業|終了|移転|駐車|ワクチン|狂犬病|混合|支払|カード|現金|PayPay|kg|ｋｇ|キロ|頭まで|見学|面会|夜間|当日|予約|持ち物|用意|キャンセル|送り迎え|お迎え')
SUB = re.compile(r'price|fee|ryokin|料金|menu|メニュー|access|アクセス|about|company|会社|店舗|shop|info|概要|hotel|ホテル|training|しつけ|trim|service|サービス|area|エリア|faq|qa|よくある|質問|flow|流れ|guide|利用|plan|プラン|system|システム', re.I)


def get(url):
    # 日本語のURL（tvma.or.jp/clinic/◯◯/ など）・日本語ドメインも開けるようにする
    u = urllib.parse.urlsplit(url)
    try:
        host = u.hostname.encode('idna').decode() if u.hostname else ''
    except Exception:
        host = u.hostname or ''
    netloc = host + (f':{u.port}' if u.port else '')
    url = urllib.parse.urlunsplit((u.scheme, netloc, urllib.parse.quote(u.path, safe='/%:@!$&\'()*+,;=~-._'),
                                   urllib.parse.quote(u.query, safe='=&%+/:;,~-._'), ''))
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja'})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read(1_500_000)
        ct = r.headers.get('Content-Type', '')
        final = r.geturl()
    enc = 'utf-8'
    m = re.search(r'charset=([\w-]+)', ct) or re.search(rb'charset=["\']?([\w-]+)', raw[:3000])
    if m:
        enc = m.group(1) if isinstance(m.group(1), str) else m.group(1).decode()
    try:
        return raw.decode(enc, 'replace'), final
    except LookupError:
        return raw.decode('utf-8', 'replace'), final


def text_of(h):
    h = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', h)
    h = re.sub(r'(?i)<br\s*/?>|</(p|div|li|tr|h\d|dt|dd|td|th|section|article)>', '\n', h)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', h))
    lines = []
    for l in t.split('\n'):
        l = re.sub(r'[ \t　]+', ' ', l).strip()
        if l and l not in lines:
            lines.append(l)
    return lines


def title_of(h):
    m = re.search(r'(?is)<title[^>]*>(.*?)</title>', h)
    return html.unescape(re.sub(r'\s+', ' ', m.group(1))).strip() if m else ''


def links_of(h, base):
    host = urllib.parse.urlparse(base).netloc
    out = []
    for href, label in re.findall(r'(?is)<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', h):
        try:
            u = urllib.parse.urljoin(base, href)
            p = urllib.parse.urlparse(u)
        except ValueError:  # 全角の＃など、URLにならないリンクは飛ばす
            continue
        if p.netloc != host or re.search(r'\.(jpg|png|pdf|gif|zip)$', p.path, re.I):
            continue
        lab = re.sub(r'<[^>]+>', '', label)
        if (SUB.search(p.path) or SUB.search(lab)) and u not in out and u.rstrip('/') != base.rstrip('/'):
            out.append(u)
    return out[:4]


def search(item):
    """q だけの行は検索の結果のURLと見出しを返す（候補さがし。結果は人が見て公式サイトかを決める）。"""
    r = dict(item)
    try:
        h, _ = get('https://html.duckduckgo.com/html/?kl=jp-jp&q=' + urllib.parse.quote(item['q']))
        res = []
        for href, label in re.findall(r'(?is)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
            m = re.search(r'uddg=([^&]+)', href)
            u = urllib.parse.unquote(m.group(1)) if m else href
            res.append([html.unescape(re.sub(r'<[^>]+>', '', label)).strip(), u])
        r['results'] = res[:10]
    except Exception as e:
        r['error'] = str(e)[:200]
    return r


def snap(item):
    if 'q' in item and 'url' not in item:
        return search(item)
    url = item['url']
    if item.get('alive'):
        # 開けるかだけ見る（Nori 2026-11-22「サイト開けなくて問い合わせないところは掲載しない」）。2回ためす
        r = dict(item)
        for _ in range(2):
            try:
                h, final = get(url)
                r.pop('error', None)
                r['final'] = final
                r['title'] = title_of(h)[:80]
                r['size'] = len(h)
                break
            except Exception as e:
                r['error'] = str(e)[:200]
        return r
    if item.get('raw'):
        # 一覧のページ（獣医師会の会員一覧など）は、ページをそのまま置いて、コンテナで読み分ける
        r = dict(item)
        try:
            h, final = get(url)
            r['final'] = final
            r['html'] = h
        except Exception as e:
            r['error'] = str(e)[:200]
        return r
    r = dict(item)
    try:
        h, final = get(url)
    except Exception as e:
        r['error'] = str(e)[:200]
        return r
    r['final'] = final
    r['title'] = title_of(h)
    pages = [{'url': final, 'lines': [l for l in text_of(h) if KEY.search(l) and len(l) < 220][:80]}]
    for u in links_of(h, final):
        try:
            hh, f2 = get(u)
            pages.append({'url': f2, 'title': title_of(hh), 'lines': [l for l in text_of(hh) if KEY.search(l) and len(l) < 220][:60]})
        except Exception as e:
            pages.append({'url': u, 'error': str(e)[:120]})
    r['pages'] = pages
    return r


def snap_safe(item):
    try:
        return snap(item)
    except Exception as e:  # 1件の失敗で全体を止めない
        r = dict(item); r['error'] = str(e)[:200]; return r


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
    os.makedirs(out, exist_ok=True)
    qdir = os.path.join(root, 'tools', 'crawl')
    for fn in sorted(os.listdir(qdir)):
        if not (fn.startswith('queue') and fn.endswith('.json')):
            continue
        items = json.load(open(os.path.join(qdir, fn)))
        with cf.ThreadPoolExecutor(12) as ex:
            res = list(ex.map(snap_safe, items))
        json.dump(res, open(os.path.join(out, fn.replace('queue', 'snap')), 'w'), ensure_ascii=False, indent=1)
        print(fn, len(res), 'errors', sum(1 for x in res if x.get('error')))


if __name__ == '__main__':
    main()
