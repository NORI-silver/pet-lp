#!/usr/bin/env python3
"""[A] ペットと避難：問い合わせ先（防災の担当課のメール・お問い合わせフォーム）を集める（Nori 2026-11-23「漏れ一切なく」）。
tools/crawl/hinan_contact_queue.json（[{"pref","name","code","url","pages":[...]}]）の各自治体で、
防災・避難のページと、トップから「防災・危機管理」のリンクをたどったページを開き、
メールアドレス（mailto）とお問い合わせフォームのリンクを out/<code>.json に書く。何も送らない。
.github/workflows/hinan-contact.yml から動かす（コンテナからは自治体のサイトに届かないため）。
"""
import concurrent.futures as cf, html, json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from hinan_snap import get, decode

FORM_T = re.compile(r'(お)?問い?合わ?せ(フォーム)?|問合せ|メールフォーム|メールでのお問い合わせ|ご意見')
FORM_U = re.compile(r'inquiry|toiawase|otoiawase|mailform|formmail|contact|form|enquete|cgi-bin', re.I)
MAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.(?:lg\.jp|jp)')
DEPT_W = os.environ.get('DEPT_WORDS', '危機管理|防災|地域安全|安全安心|安心安全|総務')
DEPT = re.compile(r'([^\s　「」（）()、。:：]{0,12}(?:' + DEPT_W + r')[^\s　「」（）()、。:：]{0,8}(?:課|室|係|局|部|センター|保健所))')
NAV = re.compile(os.environ.get('NAV_WORDS', '防災|危機管理|災害|避難'))


def scan(u, host):
    try:
        raw, ct, final = get(u, 3_000_000)
    except Exception:
        return None
    if 'html' not in ct.lower():
        return None
    h = decode(raw, ct)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', h)))
    links, forms, mails = [], [], []
    for href, lab in re.findall(r'(?is)<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', h):
        lab = re.sub(r'<[^>]+>|\s+', '', html.unescape(lab))
        if href.lower().startswith('mailto:'):
            mails.append(href[7:].split('?')[0].strip()); continue
        v = urllib.parse.urljoin(final, href)
        pu = urllib.parse.urlparse(v)
        if FORM_T.search(lab) and (FORM_U.search(v) or '問' in lab):
            forms.append([v, lab[:30]])
        if pu.netloc.endswith(host.split('.', 1)[-1]) and NAV.search(lab):
            links.append(v)
    mails += MAIL.findall(t)
    dept = DEPT.findall(t[:200000])
    return {'url': final, 'bousai': bool(NAV.search(t[:5000])), 'forms': forms[:8], 'mails': sorted(set(mails)),
            'dept': dept[-1] if dept else None, 'links': links[:40]}


def one(job):
    host = urllib.parse.urlparse(job['url']).netloc
    todo = [p for p in job.get('pages', []) if not p.lower().endswith('.pdf')][:6] + [job['url']]
    seen, out = set(), []
    while todo and len(seen) < 14:
        u = todo.pop(0)
        if u in seen:
            continue
        seen.add(u)
        r = scan(u, host)
        if not r:
            continue
        for l in r.pop('links'):
            if l not in seen and l not in todo and len(todo) < 30:
                todo.append(l)
        if r['forms'] or r['mails'] or r['dept']:
            out.append(r)
    return {k: job[k] for k in ('pref', 'name', 'code', 'url')} | {'found': out}


def main(dst):
    q = json.load(open(os.environ.get('QUEUE', 'tools/crawl/hinan_contact_queue.json')))
    os.makedirs(dst, exist_ok=True)
    with cf.ThreadPoolExecutor(16) as ex:
        for r in ex.map(one, q):
            json.dump(r, open(f"{dst}/{r['code']}.json", 'w'), ensure_ascii=False, indent=0)
            print(r['name'], sum(len(f['forms']) for f in r['found']), sum(len(f['mails']) for f in r['found']), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
