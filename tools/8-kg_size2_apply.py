p = "tools/hosp_find.py"
s = open(p, encoding="utf-8").read()
for a in ('json.dumps(pslug, ensure_ascii=False)', 'json.dumps(LABEL, ensure_ascii=False)',
          'json.dumps({"y:" + n: ds for n, ds in SYMPTOMS}, ensure_ascii=False)'):
    assert s.count(a) == 1, a
    s = s.replace(a, a[:-1] + ', separators=(",", ":"))')
open(p, "w", encoding="utf-8").write(s)
