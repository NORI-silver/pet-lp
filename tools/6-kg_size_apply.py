p = "tools/prefkeep.py"
s = open(p, encoding="utf-8").read()
assert "_lite" not in s
s += '''

def _lite(s):
    """行頭の空白と空行を落として軽くする（/hosp.js・/find.js は 24KB まで）。動きは変わらない。"""
    return "\\n".join(l.strip() for l in s.split("\\n") if l.strip()) + "\\n"


FN = _lite(FN)
GUESS = _lite(GUESS)
'''
open(p, "w", encoding="utf-8").write(s)
