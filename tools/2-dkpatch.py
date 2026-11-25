import re, sys
p = 'tools/uikit.py'
s = open(p, encoding='utf-8').read()
# 1) 共通の関数
helper = '''
def _dedupe_k(t, ks):
    """find.js はカードの data-k に data-ft・data-tags を足して条件にする。足されるものは data-k に書かない（結果は同じ・容量だけ減る）。"""
    ex = {x.strip().replace(" ", "_") for x in (_ATTR(t, "data-ft") + "|" + _ATTR(t, "data-tags")).split("|") if x.strip()}
    return [k for k in ks if k not in ex]

def _keys(t, cat, url=""):'''
assert s.count('\ndef _keys(t, cat, url=""):') == 1
s = s.replace('\ndef _keys(t, cat, url=""):', helper, 1)
# 2) 1つ目のカード
a = '''        return t[:-1] + f' data-ffi data-k="{e(" ".join(ks))}"{no}>\''''
assert s.count(a) == 1
s = s.replace(a, '''        ks = _dedupe_k(t, ks)
        return t[:-1] + " data-ffi" + (f' data-k="{e(" ".join(ks))}"' if ks else "") + f"{no}>"''')
# 3) 2つ目のカード
b = '''        return t[:-1] + " data-ffi" + (f' data-k="{e(" ".join(ks))}"' if ks else "") + (f' data-no="{e(" ".join(no))}"' if no else "") + ">"'''
assert s.count(b) == 1
s = s.replace(b, '''        ks = _dedupe_k(t, ks)
        return t[:-1] + " data-ffi" + (f' data-k="{e(" ".join(ks))}"' if ks else "") + (f' data-no="{e(" ".join(no))}"' if no else "") + ">"''')
open(p, 'w', encoding='utf-8').write(s)
