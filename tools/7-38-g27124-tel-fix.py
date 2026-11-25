import json
P='tools/vet_clinics.json'
d=json.load(open(P,encoding='utf-8'))
n=0
for c in d['clinics']:
    if c['id']=='G27124':
        assert c['addr']=='大阪府寝屋川市打上元町9-10' and c['tel']=='072-820-0799'
        # 公式ページ: 東寝屋川医療センター(打上元町9-10)は 072-824-0799、072-820-0799 は本院(中木田町13-10)の番号
        c['tel']='072-824-0799'; c['tel_src']='https://www.himawari-ah.jp/medcenter.html'; n+=1
assert n==1
json.dump(d,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('G27124 tel corrected')
