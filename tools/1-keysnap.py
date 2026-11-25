import re, os, json, sys, html
# 全ページのカード（data-ffi）ごとに、find.js が作る「条件の集まり」を出す
def snap(root):
    out = {}
    for d, _, fs in os.walk(root):
        if any(x in d for x in ('/.git', '/node_modules', '/tools', '/tests')): continue
        if 'index.html' not in fs: continue
        p = os.path.join(d, 'index.html')
        h = open(p, encoding='utf-8').read()
        n = 0
        for m in re.finditer(r'<[a-z]+[^>]*\sdata-ffi[\s>][^>]*>', h):
            t = m.group(0)
            def a(name):
                x = re.search(r'\s%s="([^"]*)"' % name, t)
                return html.unescape(x.group(1)) if x else ''
            ex = [x.strip().replace(' ', '_') for x in (a('data-ft') + '|' + a('data-tags')).split('|') if x.strip()]
            ks = a('data-k').split() + ex
            out['%s#%d' % (p, n)] = [sorted(set(ks)), a('data-no'), a('data-q')]
            n += 1
    return out
if __name__ == '__main__':
    json.dump(snap(sys.argv[1]), open(sys.argv[2], 'w'), ensure_ascii=False)
    print(len(json.load(open(sys.argv[2]))), 'cards')
