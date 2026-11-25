import json
P='tools/vet_clinics.json'
d=json.load(open(P,encoding='utf-8'))
n=0
d['clinics']=[c for c in d['clinics'] if not (c.get('checked')=='2026-11-25' and c.get('src_name')=='病院の公式サイト' and c['name']=='木場パークサイド動物病院')]
print('kiba dropped; clinics',len(d['clinics']))
for c in d['clinics']:
    if c.get('src_name')=='病院の公式サイト' and c.get('checked')=='2026-11-25' and 'その他は公式サイトで確認' in c['animals']:
        c['animals']=c['animals'].replace('その他は公式サイトで確認','その他は要確認'); n+=1
print('tail changed',n)
json.dump(d,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
