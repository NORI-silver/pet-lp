# 一時の補助（広告・文字入りの写真を外す）。使い終わったら消す。
import json,os,sys
R=json.loads(open('tools/rm_list.json').read())   # {"hotel:PH005":[1], ...}
ph=json.load(open('tools/photos.json'));pp=json.load(open('tools/photo_permits.json'));man=json.load(open('tools/curated_tokyo_small.json'))
for key,nums in R.items():
    cat,i=key.split(':',1)
    it=next(x for x in ph['items'] if x['cat']==cat and x['id']==i)
    old=it['photos'];rat=it.get('ratio',[]);keepidx=[k for k in range(len(old)) if (k+1) not in nums]
    for k in range(len(old)):
        if k not in keepidx: os.remove(old[k].lstrip('/'))
    newp=[];newr=[];tmp=[]
    for n,k in enumerate(keepidx,1):
        src=old[k].lstrip('/');dst=f'img/fac/{cat}/{i}_{n}.webp';tmp.append((src,dst))
    for s,d in tmp:
        os.rename(s,s+'.tmp')
    for (s,d),k in zip(tmp,keepidx):
        os.rename(s+'.tmp',d);newp.append('/'+d);newr.append(rat[k]) if rat else None
    mf={('/'+m['file']):m for m in man if m.get('id')==i}
    rm_files={old[k] for k in range(len(old)) if k not in keepidx}
    man[:]=[m for m in man if not (m.get('id')==i and '/'+m['file'] in rm_files)]
    byold={old[k]:n for n,k in enumerate(keepidx,1)}
    for m in man:
        if m.get('id')==i and '/'+m['file'] in byold: m['file']=f'img/fac/{cat}/{i}_{byold["/"+m["file"]]}.webp'
    if newp:
        it['photos']=newp
        if rat: it['ratio']=newr
        if 'source_photos' in it: it['source_photos']=[s for n,s in enumerate(it['source_photos'],1) if n-1 in keepidx]
    else:
        ph['items'].remove(it);pp['permits']=[p for p in pp['permits'] if not(p['cat']==cat and p['id']==i)]
    print(key,'removed',nums,'left',len(newp))
json.dump(ph,open('tools/photos.json','w'),ensure_ascii=False,indent=1);json.dump(pp,open('tools/photo_permits.json','w'),ensure_ascii=False,indent=1);json.dump(man,open('tools/curated_tokyo_small.json','w'),ensure_ascii=False,indent=1)
