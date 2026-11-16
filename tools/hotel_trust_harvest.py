#!/usr/bin/env python3
"""[C] ペットホテルの「安心して預けられるか」の材料を、各ホテルの公式サイトから集める（Nori 2026-11-16「どこが信用できるかわからない」）。
tools/hotels.json の各ホテルの公式ページと、そこからたどれる同じサイトの会社概要・店舗情報・特定商取引法の表記・よくある質問・
ご利用案内のページ（1段だけ、8ページまで）を開き、動物取扱業の登録・夜のスタッフ・病院・様子の報告・見学・お試し・部屋・
ワクチンのことばのまわりの文を JSON と Markdown で出す（何も送らない・サイトは書き換えない）。
採るかどうかは人が文を読んで決め、tools/hotels.json の `trust` に出どころ（src・quote・checked）つきで入れる。
.github/workflows/hotel-trust.yml から動かす（コンテナからは各社サイトに届かないため）。結果はブランチ hotel-trust-cand。
"""
import json, os, re, sys, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_grep as sg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUB = re.compile(r'会社概要|会社案内|会社情報|店舗情報|店舗案内|施設案内|施設紹介|特定商取引|特商法|運営|概要|アクセス|よくある|FAQ|Q&A|ご利用|利用案内|利用規約|ご案内|ホテル|宿泊|お預かり|料金|ルール|注意|初めて|はじめて|about|company|profile|shop|store|access|faq|qa|guide|rule|policy|tokusho|law|hotel|stay|price|info', re.I)
CATS = {
    'reg': r'動物取扱|取扱業|登録番号|第一種動物|動物取扱責任者|有効期[間限]|登録年月日',
    'night': r'夜間|夜も|深夜|24時間|常駐|泊まり込み|宿直|スタッフが(?:い|在)|夜通し|巡回',
    'vet': r'獣医|動物病院|提携病院|併設|かかりつけ|急変|体調.{0,6}(?:悪|崩)',
    'report': r'写真|動画|LINE|ライン|報告|お便り|レポート|日記|ブログ|インスタ|様子',
    'camera': r'カメラ|ライブ配信|見守り|モニター',
    'visit': r'見学|内覧|下見',
    'trial': r'お試し|体験|慣らし|プレ宿泊|はじめての方|初めての方|日帰り',
    'room': r'個室|ケージ|サークル|フリー|部屋|ルーム|広さ|一頭ずつ|1頭ずつ|多頭',
    'vaccine': r'ワクチン|狂犬病|予防接種|証明書|ノミ|ダニ|フィラリア|健康診断',
    'walk': r'散歩|お散歩|運動|ラン',
}
CATS = {k: re.compile(v) for k, v in CATS.items()}


def page(url):
    try:
        t = sg.raw_page(url)
        return t, sg.text_of(t)
    except Exception as ex:
        return None, [f'!! 開けない: {ex.__class__.__name__}']


def sub_links(t, base):
    host = urllib.parse.urlsplit(base).netloc
    out = []
    for href, label in re.findall(r'(?is)<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', t):
        u = urllib.parse.urljoin(base, sg.html.unescape(href)).split('#')[0]
        if urllib.parse.urlsplit(u).netloc != host or re.search(r'\.(jpg|jpeg|png|gif|pdf|webp|svg|zip)$', u, re.I): continue
        lab = re.sub(r'<[^>]+>', '', label)
        if SUB.search(urllib.parse.unquote(u)) or SUB.search(lab):
            if u not in out: out.append(u)
    return out


def snippets(lines, pat, n=8):
    out = []
    for i, s in enumerate(lines):
        if pat.search(s):
            ctx = ' / '.join(lines[max(0, i - 1):i + 2])[:300]
            if ctx not in out: out.append(ctx)
            if len(out) >= n: break
    return out


def harvest(h):
    base = h['url']
    root = '{0.scheme}://{0.netloc}/'.format(urllib.parse.urlsplit(base))
    seen, queue, res = set(), [base, root], {'id': h['id'], 'name': h['name'], 'url': base, 'pages': {}}
    first = True
    while queue and len(seen) < 9:
        u = queue.pop(0)
        if u in seen: continue
        seen.add(u)
        t, lines = page(u)
        hit = {k: snippets(lines, p) for k, p in CATS.items()}
        hit = {k: v for k, v in hit.items() if v}
        if t is None: hit = {'error': lines}
        res['pages'][u] = hit
        if t is not None and (first or u == root):
            for l in sub_links(t, u):
                if l not in seen and l not in queue: queue.append(l)
        first = False
        time.sleep(0.7)
    return res


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
    only = set(sys.argv[2:])
    os.makedirs(out, exist_ok=True)
    H = json.load(open(os.path.join(ROOT, 'tools/hotels.json'), encoding='utf-8'))['hotels']
    allres = []
    for h in H:
        if only and h['id'] not in only: continue
        r = harvest(h)
        allres.append(r)
        print(h['id'], h['name'], len(r['pages']), 'pages', flush=True)
    json.dump(allres, open(os.path.join(out, 'hotel_trust.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    md = []
    for r in allres:
        md.append(f"## {r['id']} {r['name']}\n")
        for u, hit in r['pages'].items():
            if not hit: continue
            md.append(f"- {u}")
            for k, v in hit.items():
                for s in v[:4]: md.append(f"  - [{k}] {s}")
        md.append('')
    open(os.path.join(out, 'hotel_trust.md'), 'w', encoding='utf-8').write('\n'.join(md))
    n = sum(1 for r in allres if any('reg' in hit for hit in r['pages'].values()))
    open(os.path.join(out, 'summary.md'), 'w', encoding='utf-8').write(f'# ペットホテルの信頼の材料\n\n{len(allres)}件のうち、動物取扱業のことばがあったのは{n}件\n')


if __name__ == '__main__':
    main()
