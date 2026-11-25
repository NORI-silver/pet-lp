import json
p='tools/rojin.json'
d=json.load(open(p,encoding='utf-8'))
base=[h for h in d['homes'] if not h['id'].startswith('R-B14-')]
D='2026-11-25'
def f(k,v,src): return {"k":k,"v":v,"src":src,"by":"site","checked":D}
new=[
 {"id":"R-B14-002","name":"さかがみ家 老犬老猫ホーム terra-pa","prefs":["千葉県"],"city":"君津市","url":"https://sakagamike-terrapa.com/","animals":"犬・猫",
  "review_name":"terra-pa","review_query":"さかがみ家 老犬老猫ホーム terra-pa 君津市",
  "facts":[f("受け入れ条件","終身預かりのプランがある（原則13歳以上）","https://sakagamike-terrapa.com/price/"),
           f("1泊・日帰り","3か月・6か月のプランがある。日中のお預かり（デイサービス）とペットホテルは別のメニュー","https://sakagamike-terrapa.com/price/")]},
 {"id":"R-B14-003","name":"わんデイサービス ラブ","prefs":["大阪府"],"city":"寝屋川市","url":"https://1day-love.amebaownd.com/","animals":"犬",
  "review_name":"わんデイサービス ラブ","review_query":"わんデイサービス ラブ 寝屋川市",
  "facts":[f("受け入れ条件","老犬ホームは月極のお預かり（1か月単位）","https://1day-love.amebaownd.com/pages/940817/page_201704091516"),
           f("1泊・日帰り","ペットホテル・半日預かり・ナイトモードもある","https://1day-love.amebaownd.com/pages/940817/page_201704091516"),
           f("部屋","小規模の介護ホーム。一軒家で、ドッグランが併設されている","https://1day-love.amebaownd.com/pages/938112/page_201603171850")]},
 {"id":"R-B14-005","name":"老犬介護ホーム Azul（アスル）","prefs":["福岡県"],"city":"宗像市","url":"http://roukenkaigo-azul.com/","animals":"犬",
  "review_name":"Azul","review_query":"老犬介護ホーム Azul 宗像市",
  "facts":[f("1泊・日帰り","日中一時お預り・一時お預り（1泊から）・1か月お預り・半年お預りがある。終生のお預りは要相談","http://roukenkaigo-azul.com/info.html"),
           f("お世話","介護なしと要介護で料金の区分がある。重症の老犬も受け入れる介護ホームとQ&Aに書いてある","http://roukenkaigo-azul.com/QA.html")]},
 {"id":"R-B14-006","name":"保護猫カフェ＆老犬老猫ホーム Kaipooh","prefs":["福岡県"],"city":"福岡市早良区","url":"https://www.kaipooh.jp/","animals":"犬・猫",
  "review_name":"Kaipooh","review_query":"保護猫カフェ＆老犬老猫ホーム Kaipooh 福岡市早良区",
  "facts":[f("料金","料金表がある（ショートタイム・デイ・一泊二日・1か月・3か月・6か月・1年）","https://www.kaipooh.jp/price"),
           f("別料金","料金はお預かりのみで、お世話の内容により別料金","https://www.kaipooh.jp/price"),
           f("受け入れ条件","猫と小型犬から大型犬が対象（超大型犬は要相談）","https://www.kaipooh.jp/senior")]},
 {"id":"R-B14-007","name":"老犬ホーム ani TERRACE","prefs":["三重県"],"city":"多気郡多気町","url":"https://www.ani-terrace.com/","animals":"犬",
  "review_name":"ani TERRACE","review_query":"老犬ホーム ani TERRACE 多気町",
  "facts":[f("受け入れ条件","高齢で自宅での飼育が難しくなった犬を、長期的に預かると書いてある","https://www.ani-terrace.com/")]},
 {"id":"R-B14-009","name":"老犬ホーム トップ 栃木犬舎","prefs":["栃木県"],"city":"矢板市","url":"https://roukentop.co.jp/nyuukyo/","animals":"犬",
  "review_name":"栃木犬舎","review_query":"老犬ホーム トップ 栃木犬舎 矢板市",
  "facts":[f("受け入れ条件","短期から長期まで預かる","https://roukentop.co.jp/nyuukyo/")]},
]
d['homes']=base+new
print('homes',len(base),'+',len(new))
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
