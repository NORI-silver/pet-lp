import json,re,sys
P='tools/vet_clinics.json'
D=json.load(open(sys.argv[1],encoding='utf-8'))
d=json.load(open(P,encoding='utf-8'))
cl=d['clinics']
CODE={'東京都':'13','大阪府':'27','神奈川県':'14','滋賀県':'25','愛媛県':'38','長崎県':'42','宮崎県':'45','千葉県':'12','栃木県':'09','埼玉県':'11','愛知県':'23','香川県':'37'}
EXTRA={ # 公式サイトの本文が動物の名前をはっきり書いている病院だけ（それ以外は犬・猫だけ）
 'おどりば動物病院':'犬・猫・ハムスター・うさぎ','トキ動物病院':'犬・猫・エキゾチックアニマル','バーズ動物病院':'犬・猫・鳥・小動物',
 'ふう動物病院':'犬・猫・うさぎ・小動物・小鳥','アニマルフレンド':'犬・猫・うさぎ','岩上動物病院':'犬・猫・エキゾチックアニマル（火曜午前を除く）',
 '富士見台どうぶつ病院':'犬・猫・うさぎ・ハムスター・フェレット',
 '小儀動物病院':'犬・猫・ハムスター・うさぎ・モルモット','向陽台動物病院':'犬・猫・ハムスター','クリハラペットクリニック':'犬・猫・フェレット・うさぎ・ハムスター',
 'えんどう動物病院':'犬・猫・うさぎ・ハムスター・フェレット・その他小動物','ニュートン動物病院':'犬・猫・うさぎ・フェレット・ハムスター'}
TAIL='・その他は公式サイトで確認'
have_url={re.sub(r'^https?://(www\.)?|/$','',c['url']) for c in cl}
have_name={(c['pref'],c['name']) for c in cl}
have_addr={re.sub(r'[\s　\-−ー]','',c['addr']) for c in cl}
n=0
for x in D:
    u=re.sub(r'^https?://(www\.)?|/$','',x['url']); ad=x['addr'].replace('−','-').replace('－','-')
    assert u not in have_url and (x['pref'],x['name']) not in have_name and re.sub(r'[\s　\-−ー]','',ad) not in have_addr, ('dup',x['name'])
    pc=CODE[x['pref']]
    seq=max([int(c['id'][3:]) for c in cl if c['id'].startswith('G'+pc)]+[0])+1
    an=EXTRA.get(x['name'],'犬・猫'); an=an if 'その他' in an else an+TAIL
    cl.append({'id':f'G{pc}{seq:03d}','name':x['name'],'pref':x['pref'],'city':x['city'],'addr':ad,'hours':'','closed':'','animals':an,'services':'','pay':'','url':x['url'],'src':x['url'],'checked':'2026-11-25','src_name':'病院の公式サイト'})
    n+=1
json.dump(d,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('added',n,'total',len(cl))
