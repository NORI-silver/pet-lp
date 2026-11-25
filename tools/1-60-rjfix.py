import json
p='tools/rojin.json'
d=json.load(open(p,encoding='utf-8'))
rv={
 'R-B14-001':('老猫ハウス横浜','老猫ハウス横浜 横浜市南区'),
 'R-B14-002':('terra-pa','さかがみ家 老犬老猫ホーム terra-pa 君津市'),
 'R-B14-005':('Azul','老犬介護ホーム Azul 宗像市'),
 'R-B14-006':('Kaipooh','保護猫カフェ＆老犬老猫ホーム Kaipooh 福岡市早良区'),
 'R-B14-007':('ani TERRACE','老犬ホーム ani TERRACE 多気町'),
 'R-B14-008':('フルエスト','老犬介護ハイム フルエスト 呉市'),
 'R-B14-009':('栃木犬舎','老犬ホーム トップ 栃木犬舎 矢板市'),
}
hold={'R-B14-003','R-B14-004'}
out=[]
for h in d['homes']:
    if h['id'] in hold: continue
    if h['id'] in rv:
        h['review_name'],h['review_query']=rv[h['id']]
    out.append(h)
print('homes',len(d['homes']),'->',len(out))
d['homes']=out
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
