import json,os
DROP={'St41a014c','St6e99243','Stbee5495'}
KEEP={'St3da275b':[2],'Stcfa7546':[1]}
ph=json.load(open('tools/photos.json'));pp=json.load(open('tools/photo_permits.json'));man=json.load(open('tools/curated_tokyo_small.json'))
def fn(i,k): return f'img/fac/sitter/{i}_{k}.webp'
# manifest
newman=[];
for m in man:
    i=m['id']
    if m['file'].startswith('img/fac/sitter/') and i in DROP: continue
    if i in KEEP and m['file'].startswith('img/fac/sitter/'):
        k=int(m['file'].rsplit('_',1)[1].split('.')[0])
        if k not in KEEP[i]: continue
        m=dict(m);m['file']=fn(i,KEEP[i].index(k)+1)
    newman.append(m)
items=[]
for x in ph['items']:
    i=x['id']
    if x['cat']=='sitter' and i in DROP: continue
    if x['cat']=='sitter' and i in KEEP:
        x=dict(x);x['photos']=['/'+fn(i,n+1) for n in range(len(KEEP[i]))];x['ratio']=[x['ratio'][k-1] for k in KEEP[i]]
    items.append(x)
ph['items']=items
pp['permits']=[p for p in pp['permits'] if not(p['cat']=='sitter' and p['id'] in DROP)]
# files
for i in DROP:
    for k in range(1,7):
        if os.path.exists(fn(i,k)): os.remove(fn(i,k))
for i,ks in KEEP.items():
    tmp={}
    for n,k in enumerate(ks,1):
        tmp[n]=open(fn(i,k),'rb').read()
    for k in range(1,7):
        if os.path.exists(fn(i,k)): os.remove(fn(i,k))
    for n,b in tmp.items(): open(fn(i,n),'wb').write(b)
json.dump(ph,open('tools/photos.json','w'),ensure_ascii=False,indent=1);json.dump(pp,open('tools/photo_permits.json','w'),ensure_ascii=False,indent=1);json.dump(newman,open('tools/curated_tokyo_small.json','w'),ensure_ascii=False,indent=1)
print('ok')
