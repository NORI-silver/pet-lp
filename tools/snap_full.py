#!/usr/bin/env python3
"""[B] 掲載の候補の公式サイトを、表の行をつなげた全文で読む（料金表の「小型犬｜1泊｜3,000円」を1行にするため）。
入口のページと、同じサイトの料金・ホテル・アクセス・よくある質問などのページ（最大6つ）の文を out に書く。何も送らない。"""
import html, re, urllib.parse, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_snap

SUB = re.compile(r'price|fee|ryokin|ryoukin|料金|menu|メニュー|access|アクセス|about|company|会社|店舗|shop|info|概要|hotel|ホテル|azukari|預|stay|training|しつけ|lesson|trim|grooming|service|サービス|area|エリア|faq|qa|q-a|よくある|質問|flow|流れ|guide|利用|plan|プラン|system|course|コース|price', re.I)

def text_rows(h):
    h = re.sub(r'(?is)<(script|style|noscript|svg|header|nav)[^>]*>.*?</\1>', ' ', h)
    h = re.sub(r'(?i)</t[dh]>', ' ｜ ', h)
    h = re.sub(r'(?i)<br\s*/?>|</(p|div|li|tr|h\d|dt|dd|section|article|table|ul|ol)>', '\n', h)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', h))
    out = []
    for l in t.split('\n'):
        l = re.sub(r'[ \t　]+', ' ', l).strip(' ｜')
        if l and (not out or out[-1] != l):
            out.append(l)
    return out

def links(h, base):
    host = urllib.parse.urlparse(base).netloc
    res = []
    for href, label in re.findall(r'(?is)<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', h):
        try:
            u = urllib.parse.urljoin(base, href); p = urllib.parse.urlparse(u)
        except ValueError:
            continue
        if p.netloc != host or re.search(r'\.(jpg|jpeg|png|pdf|gif|zip|mp4)$', p.path, re.I):
            continue
        lab = re.sub(r'<[^>]+>', '', label)
        if (SUB.search(urllib.parse.unquote(p.path)) or SUB.search(lab)) and u not in res and u.rstrip('/') != base.rstrip('/'):
            res.append(u)
    return res[:6]

def full(item):
    r = dict(item)
    try:
        h, final = site_snap.get(item['url'])
    except Exception as e:
        r['error'] = str(e)[:150]; return r
    r['final'] = final; r['title'] = site_snap.title_of(h)
    pages = [{'url': final, 'lines': text_rows(h)[:500]}]
    for u in links(h, final):
        try:
            hh, f2 = site_snap.get(u)
            pages.append({'url': f2, 'title': site_snap.title_of(hh), 'lines': text_rows(hh)[:500]})
        except Exception as e:
            pages.append({'url': u, 'error': str(e)[:100]})
    r['pages'] = pages
    return r
