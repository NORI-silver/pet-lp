# 一時の補助。外しすぎた写真を、外す前の状態から戻す。使い終わったら消す。
import json,os,subprocess
B='96005fc83'
OPS=[('hotel','PHkaf2c17'),('hotel','PHce74b04'),('hotel','PHcf246ea')]
sh=lambda *a:subprocess.check_output(list(a))
g=lambda f:json.loads(sh('git','show',f'{B}:tools/{f}'))
bph,bpp,bman=g('photos.json'),g('photo_permits.json'),g('curated_tokyo_small.json')
ph=json.load(open('tools/photos.json'));pp=json.load(open('tools/photo_permits.json'));man=json.load(open('tools/curated_tokyo_small.json'))
for cat,i in OPS:
    b=next(x for x in bph['items'] if x['cat']==cat and x['id']==i)
    d=f'img/fac/{cat}'
    for f in os.listdir(d):
        if f.startswith(i+'_'): os.remove(f'{d}/{f}')
    for p in b['photos']:
        open(p.lstrip('/'),'wb').write(sh('git','show',f'{B}:'+p.lstrip('/')))
    idx=[n for n,x in enumerate(ph['items']) if x['cat']==cat and x['id']==i]
    if idx: ph['items'][idx[0]]=b
    else: ph['items'].insert(min(bph['items'].index(b),len(ph['items'])),b)
    pp['permits']=[p for p in pp['permits'] if not(p['cat']==cat and p['id']==i)]+[p for p in bpp['permits'] if p['cat']==cat and p['id']==i]
    man[:]=[m for m in man if m.get('id')!=i]+[m for m in bman if m.get('id')==i]
    print(cat,i,'restored',len(b['photos']))
json.dump(ph,open('tools/photos.json','w'),ensure_ascii=False,indent=1);json.dump(pp,open('tools/photo_permits.json','w'),ensure_ascii=False,indent=1);json.dump(man,open('tools/curated_tokyo_small.json','w'),ensure_ascii=False,indent=1)
