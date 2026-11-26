import json,sys
P=json.load(open(sys.argv[1],encoding='utf-8'))
p='tools/sougi_facilities.json'; S=json.load(open(p,encoding='utf-8')); F=S['facilities']
have={f['id'] for f in F}; n=0
for e in P:
    e=dict(e); e.pop('_src',None)
    assert e['id'] not in have,e['id']
    F.append(e); have.add(e['id']); n+=1
open(p,'w',encoding='utf-8').write(json.dumps(S,ensure_ascii=False,indent=1)+"\n"); print('added',n,'total',len(F))
