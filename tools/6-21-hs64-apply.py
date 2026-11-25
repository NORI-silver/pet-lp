import json,re
P='tools/vet_clinics.json'
D=json.load(open([f for f in __import__('glob').glob('tools/*20-vets64.json')][0],encoding='utf-8'))
d=json.load(open(P,encoding='utf-8')); cl=d['clinics']
CODE={'東京都':'13','大阪府':'27','神奈川県':'14','滋賀県':'25','愛媛県':'38','長崎県':'42','宮崎県':'45','千葉県':'12','栃木県':'09','埼玉県':'11','愛知県':'23','香川県':'37'}
HOLD={'木場パークサイド動物病院'}  # 江東区の薄いページを作ってしまうため、今回は入れない（保留）
TAIL='・その他は要確認'
def animals(x):
    a=x['animals_confirmed'].replace('(','（').replace(')','）').replace('兎','うさぎ')
    a=a.replace('犬・猫（のみ）','犬・猫')
    a=re.sub(r'（待合室[^）]*）','',a)
    a=a.replace('犬・猫（隔週木曜はエキゾチック）','犬・猫・エキゾチックアニマル（隔週木曜）')
    if re.search(r'その他|など',a): return a
    return a+TAIL
def city(x):
    m=re.match(r'(?:神奈川県|愛知県)(?:横浜市|川崎市|名古屋市)([^\d０-９]{1,4}?区)',x['addr'])
    if x['city'] in('横浜市','川崎市','名古屋市'):
        assert m,x['name']; return m.group(1)
    return x['city']
have_url={re.sub(r'^https?://(www\.)?|/$','',c['url']) for c in cl}
have_name={(c['pref'],c['name']) for c in cl}
have_addr={re.sub(r'[\s　\-−ー－]','',c['addr']) for c in cl}
n=0;held=[]
for x in D:
    if x['name'] in HOLD: held.append(x['name']); continue
    u=re.sub(r'^https?://(www\.)?|/$','',x['url']); ad=x['addr'].replace('−','-').replace('－','-')
    assert u not in have_url and (x['pref'],x['name']) not in have_name and re.sub(r'[\s　\-−ー－]','',ad) not in have_addr,('dup',x['name'])
    pc=CODE[x['pref']]
    seq=max([int(c['id'][3:]) for c in cl if c['id'].startswith('G'+pc)]+[0])+1
    cl.append({'id':f'G{pc}{seq:03d}','name':x['name'],'pref':x['pref'],'city':city(x),'addr':ad,'hours':'','closed':'','animals':animals(x),'services':'','pay':'','url':x['url'],'src':x['url'],'checked':'2026-11-25','src_name':'病院の公式サイト'})
    n+=1
json.dump(d,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('added',n,'held',held,'total',len(cl))
