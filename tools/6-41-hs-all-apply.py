import json,re
P='tools/vet_clinics.json'
D=[]
for g in ('tools/*20-vets64.json','tools/*26-vets12.json','tools/*28-vets-unknown.json','tools/*34-vets4.json','tools/*37-vets-chunk4-20.json','tools/*39-vets-chunk5-9.json','tools/*40-vets-chunk7-6.json','tools/*41-vets-chunk6-1.json'):
    for x in json.load(open(__import__('glob').glob(g)[0],encoding='utf-8')):
        if 'animals_confirmed' not in x: x['animals_confirmed']=x.get('animals','')
        D.append(x)
d=json.load(open(P,encoding='utf-8')); cl=d['clinics']
CODE={'東京都':'13','大阪府':'27','神奈川県':'14','滋賀県':'25','愛媛県':'38','長崎県':'42','宮崎県':'45','千葉県':'12','栃木県':'09','埼玉県':'11','愛知県':'23','香川県':'37','兵庫県':'28','青森県':'02','秋田県':'05','鳥取県':'31','大分県':'44','山形県':'06','島根県':'32','高知県':'39','奈良県':'29','佐賀県':'41'}
HOLD={'木場パークサイド動物病院','益田ペットクリニック','こざわ犬猫病院','しもつけVETセンター'}  # 後ろ2つは夜間救急の病院カード（H069/H015）と同じ施設なので足さない  # 江東区の薄いページを作ってしまうため、今回は入れない（保留）
TAIL='・その他は要確認'
NOTE={}
def animals(x):
    r=animals0(x)
    nm=x['name']
    g=x.get('animals_confirmed','')
    if not g: return ''
    if nm in ('トキ動物病院','後藤アニマルホスピタル','もみじが丘動物病院','はなやまペットクリニック'):
        w='エキゾチックアニマル' if 'エキゾ' in g else '小動物'
        NOTE[nm]=f'公式サイトに「{w}」の記載あり（診る種類は要確認）'
        return '犬・猫'+TAIL
    if nm=='さくら動物病院' and x['pref']=='埼玉県':
        NOTE[nm]='隔週木曜はエキゾチックの診察あり（種類は要確認）'
        return '犬・猫'+TAIL
    if nm=='ふう動物病院':
        return '犬・猫・うさぎ・小鳥'+TAIL
    if nm=='バーズ動物病院':
        NOTE[nm]='公式サイトに「小動物（げっ歯類・ウサギ・フェレット）」の記載あり（げっ歯類の種類は要確認）'
        return '犬・猫・小鳥・ウサギ・フェレット'+TAIL
    if nm=='岩上動物病院':
        return '犬・猫・小鳥・ハムスター・うさぎ・フェレット（火曜午前を除く）'+TAIL
    if nm=='えんどう動物病院' and x['pref']=='神奈川県':
        NOTE[nm]='公式サイトに「その他小動物」の記載あり（診る種類は要確認）'
        return '犬・猫・うさぎ・ハムスター・フェレット'+TAIL
    if nm=='動物病院川上':
        NOTE[nm]='犬・猫以外は来院前に連絡が必要（公式サイトの記載）'
        return '犬・猫・うさぎ・ハムスター'+TAIL
    if nm=='おおるりペットクリニック':
        NOTE[nm]='公式サイトに「ハムスターなどの小動物」の記載あり（そのほかの種類は要確認）'
        return '犬・猫・うさぎ・小鳥・ハムスター'+TAIL
    if nm=='ぴーす白川動物病院':
        NOTE[nm]='公式サイトは「犬、猫を中心とした全科診療」とあり、ほかの動物は要確認'
        return '犬・猫'+TAIL
    if nm=='やまさきペットクリニック':
        NOTE[nm]='公式サイトに「ハムスターなどの齧歯類」「鳥類（セキセイインコなどの小型）」の記載あり（そのほかの種類は要確認）。エキゾチックは専門診療ではないと書いてある'
        return '犬・猫・ウサギ・ハムスター・フェレット・小鳥'+TAIL
    if nm=='ハナペチャアニマルクリニック':
        NOTE[nm]='公式サイトに「診療動物は犬と猫になります」と書いてある（ほかの動物の扱いは要確認）'
        return '犬・猫'+TAIL
    if nm=='金重動物病院':
        NOTE[nm]='公式サイトに「犬、猫専門」とあり、犬・猫以外の小動物（ウサギやフェレットなど）は専門ではないため、できる処置に限りがある'
        return '犬・猫'+TAIL
    if nm=='みなみ動物病院' and x['pref']=='神奈川県':
        NOTE[nm]='公式サイトに「2022年10月12日以降犬猫のみの診療」と書いてある'
        return '犬・猫のみ'
    if nm=='井土ケ谷しっぽ動物病院':
        NOTE[nm]='公式サイトに「その他の動物は問い合わせ」とある'
        return '犬・猫・ウサギ・ハムスター'+TAIL
    return r
def animals0(x):
    a=x.get('animals_confirmed','').replace('(','（').replace(')','）').replace('兎','うさぎ')
    a=a.replace('犬・猫（のみ）','犬・猫')
    a=re.sub(r'（待合室[^）]*）','',a)
    a=a.replace('犬・猫（隔週木曜はエキゾチック）','犬・猫・エキゾチックアニマル（隔週木曜）')
    if re.search(r'その他|など',a): return a
    return a+TAIL
def city(x):
    m0=re.match(r'^(?:横浜市|川崎市|名古屋市)([^\d０-９]{1,4}?区)$',x['city'])
    if m0: return m0.group(1)
    m=re.match(r'(?:神奈川県|愛知県)(?:横浜市|川崎市|名古屋市)([^\d０-９]{1,4}?区)',x['addr'])
    if x['city'] in('横浜市','川崎市','名古屋市'):
        assert m,x['name']; return m.group(1)
    return x['city']
have_url={re.sub(r'^https?://(www\.)?|/$','',c['url']) for c in cl}
have_name={(c['pref'],c['name'],c['city']) for c in cl}
have_addr={re.sub(r'[\s　\-−ー－]','',c['addr']) for c in cl}
n=0;held=[]
for x in D:
    if x['name'] in HOLD: held.append(x['name']); continue
    u=re.sub(r'^https?://(www\.)?|/$','',x['url']); ad=x['addr'].replace('−','-').replace('－','-')
    assert u not in have_url and (x['pref'],x['name'],city(x)) not in have_name and re.sub(r'[\s　\-−ー－]','',ad) not in have_addr,('dup',x['name'])
    pc=CODE[x['pref']]
    seq=max([int(c['id'][3:]) for c in cl if c['id'].startswith('G'+pc)]+[0])+1
    an=animals(x)
    nm2=x['name']; src2=x['url']
    if nm2=='金重動物病院': nm2='金重動物病院 能見台院'; src2='https://kaneshigeah.b.la9.jp/policy.html'
    cl.append({'id':f'G{pc}{seq:03d}','name':nm2,'pref':x['pref'],'city':city(x),'addr':ad,'hours':'','closed':'','animals':an,'services':NOTE.get(x['name'],''),'pay':'','url':x['url'],'src':src2,'checked':'2026-11-26','src_name':'病院の公式サイト'})
    n+=1
json.dump(d,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('added',n,'held',held,'total',len(cl))
assert n==189,n
