#!/usr/bin/env python3
"""[C] ペットホテルの動物取扱業の登録を、自治体が公開している「第一種動物取扱業者の一覧」と照らし合わせる（Nori 2026-11-16「どこが信用できるかわからない」）。
tools/hotel_registries.json の一覧（Excel・PDF・CSV・ページ）を読み、tools/hotels.json の各ホテルの登録番号（trust.reg.no）と
名前・所在地の市区町村で行をさがし、見つかった行の文を出す（何も送らない・サイトは書き換えない）。
採るかどうかは人が行を読んで決め、hotels.json の trust.reg.registry に「どの一覧の、いつ時点か」を入れる。
.github/workflows/hotel-trust.yml から動かす（コンテナからは自治体のサイトに届かないため）。
"""
import io, json, os, re, sys, time, unicodedata, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'


def norm(s):
    s = unicodedata.normalize('NFKC', s or '')
    return re.sub(r'[\s　・･\-‐－ー―（）()「」『』【】\[\]]', '', s).lower()


def digits(s):
    return re.findall(r'\d+', unicodedata.normalize('NFKC', s or ''))


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(), r.headers.get('Content-Type', '')


def rows_of(url):
    raw, ct = fetch(url)
    low = url.lower()
    if low.endswith(('.xlsx', '.xlsm')) or 'spreadsheetml' in ct or raw[:2] == b'PK':
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        out = []
        for ws in wb.worksheets:
            for r in ws.iter_rows(values_only=True):
                cells = [str(c) for c in r if c not in (None, '')]
                if cells: out.append(' | '.join(cells))
        return out
    if low.endswith('.xls') or 'ms-excel' in ct:
        import xlrd
        wb = xlrd.open_workbook(file_contents=raw)
        return [' | '.join(str(c) for c in ws.row_values(i) if c not in ('', None)) for ws in wb.sheets() for i in range(ws.nrows)]
    if low.endswith('.pdf') or raw[:4] == b'%PDF':
        import pdfplumber
        out = []
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for p in pdf.pages:
                for t in p.extract_tables() or []:
                    for r in t:
                        cells = [str(c).replace('\n', '') for c in r if c]
                        if cells: out.append(' | '.join(cells))
                if not p.extract_tables():
                    out += [l for l in (p.extract_text() or '').split('\n') if l.strip()]
        return out
    for cs in ('utf-8', 'cp932'):
        try:
            t = raw.decode(cs); break
        except UnicodeDecodeError:
            continue
    t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', t)
    t = re.sub(r'</t[dh]>', ' | ', t)
    t = re.sub(r'<[^>]+>', '\n', t)
    return [l.strip() for l in t.split('\n') if l.strip()]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
    os.makedirs(out, exist_ok=True)
    R = json.load(open(os.path.join(ROOT, 'tools/hotel_registries.json'), encoding='utf-8'))
    H = json.load(open(os.path.join(ROOT, 'tools/hotels.json'), encoding='utf-8'))['hotels']
    md, res = ['# 自治体の一覧との照らし合わせ\n'], {}
    for auth, conf in R['registries'].items():
        rows = []
        for u in conf['files']:
            try:
                rows += rows_of(u)
            except Exception as ex:
                md.append(f'- !! {auth} {u} 開けない: {ex.__class__.__name__} {ex}')
            time.sleep(1)
        md.append(f'\n## {auth}（{len(rows)}行・{conf.get("asof", "")}）\n')
        nrows = [norm(r) for r in rows]
        for h in H:
            if conf.get('prefs') and not set(h['prefs']) & set(conf['prefs']): continue
            reg = (h.get('trust') or {}).get('reg') or {}
            keys = [norm(k) for k in [h['name']] + h.get('alias', []) if len(norm(k)) >= 3]
            # 名前の一部（「本店」「店」などを外した頭の部分）でも当たるように
            keys += [k[:max(4, len(k) // 2)] for k in list(keys) if len(k) >= 8]
            no = reg.get('no', '')
            nd = [d for d in digits(no) if len(d) >= 2]
            hits = []
            for r, n in zip(rows, nrows):
                by_no = nd and all(d in digits(r) for d in nd) and (not reg.get('auth') or True)
                by_name = any(k and k in n for k in keys)
                if (by_no and len(nd) >= 1 and (by_name or len(''.join(nd)) >= 4)) or by_name:
                    hits.append(('番号' if by_no else '') + ('名前' if by_name else '') + ' :: ' + r[:400])
            if hits:
                res.setdefault(h['id'], {})[auth] = hits[:6]
                md.append(f'- {h["id"]} {h["name"]}（{h.get("city", "")}・番号 {no or "なし"}）')
                for x in hits[:6]: md.append(f'  - {x}')
    json.dump(res, open(os.path.join(out, 'registry.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(out, 'registry.md'), 'w', encoding='utf-8').write('\n'.join(md))


if __name__ == '__main__':
    main()
