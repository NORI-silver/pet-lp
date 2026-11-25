import json,re
p='tools/rojin.json'
d=json.load(open(p,encoding='utf-8'))
n=0
for h in d['homes']:
    if h['animals']=='犬（ほかの動物は公式サイトで確認）': h['animals']='犬（ほかの動物は要確認）'; n+=1
assert n==5,n
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
g=open('tools/gen_rojin.py',encoding='utf-8').read()
old='長期・終生か月ごとのお預かりかは施設ごとに違うので、公式サイトでご確認ください。'
new='預かり方（長期・終生・月ごと）は施設ごとに違います。'
assert g.count(old)==1
g=g.replace(old,new)
open('tools/gen_rojin.py','w',encoding='utf-8').write(g)
m=re.search(r'^DESC = "(.*)"',g,re.M); print('animals fixed',n,'DESC len',len(m.group(1)))
