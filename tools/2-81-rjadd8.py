import json
p='tools/rojin.json'
d=json.load(open(p,encoding='utf-8'))
assert not any('fullest412' in h['url'] or 'フルエスト' in h['name'] for h in d['homes'])
src="https://fullest412.com/old_dog/lp5/"
d['homes'].append({"id":"R-B14-008","name":"老犬介護ハイム フルエスト","prefs":["広島県"],"city":"呉市","url":"https://fullest412.com/","animals":"犬",
 "review_name":"フルエスト","review_query":"老犬介護ハイム フルエスト 呉市",
 "facts":[{"k":"受け入れ条件","v":"一時入居のプラン（1か月・1年）と、終生飼養のプランがある。体重と年齢の目安で区分","src":src,"by":"site","checked":"2026-11-25"}]})
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('added 008')
