import json
p='tools/rojin.json'
R=json.load(open(p,encoding='utf-8')); n=0
for h in R['homes']:
    for f in h.get('facts',[]):
        if f.get('checked')=='2026-11-26' and f.get('by')!='x':
            f['show']=True; n+=1
open(p,'w',encoding='utf-8').write(json.dumps(R,ensure_ascii=False,indent=1)+"\n"); print('show flags',n)
g='tools/gen_rojin.py'; s=open(g,encoding='utf-8').read()
a='''"定休日", "駐車場") and not (f["k"] == "見学・面会" and h.get("visit")):'''
assert s.count(a)==1
b='''"定休日", "駐車場") and not (f["k"] == "見学・面会" and h.get("visit"))) or (f.get("show") and not (f["k"] in ("見学", "面会") and h.get("visit"))):'''
s=s.replace(a,b)
c='''        if f["k"] in ("料金",'''
assert s.count(c)==1
s=s.replace(c,'''        if (f["k"] in ("料金",''')
open(g,'w',encoding='utf-8').write(s)
