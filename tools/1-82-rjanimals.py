import json
p='tools/rojin.json'
d=json.load(open(p,encoding='utf-8'))
n=0
for h in d['homes']:
    if h['id'] in ('R-B14-003','R-B14-005','R-B14-007','R-B14-008','R-B14-009'):
        assert h['animals']=='犬',h; h['animals']='犬（ほかの動物は公式サイトで確認）'; n+=1
print('animals relabeled',n)
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
